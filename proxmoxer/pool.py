"""
Connection pooling for Proxmoxer.

Manages reusable connections with health checking, limits, and automatic cleanup.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Generic, TypeVar

from .exceptions import ConnectionError as ProxmoxConnectionError
from .types import PoolConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class PooledConnection(Generic[T]):
    """
    Wrapper for a pooled connection with metadata.

    Tracks creation time, last use, and health status.
    """

    def __init__(self, connection: T, key: str) -> None:
        """
        Initialize pooled connection.

        Args:
            connection: The actual connection object
            key: Unique key identifying this connection
        """
        self.connection = connection
        self.key = key
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.use_count = 0
        self.is_healthy = True

    def mark_used(self) -> None:
        """Mark connection as recently used."""
        self.last_used_at = time.time()
        self.use_count += 1

    def mark_unhealthy(self) -> None:
        """Mark connection as unhealthy."""
        self.is_healthy = False

    @property
    def age(self) -> float:
        """Get connection age in seconds."""
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        """Get time since last use in seconds."""
        return time.time() - self.last_used_at


class ConnectionPool(Generic[T]):
    """
    Generic connection pool with health checking and auto-cleanup.

    Features:
    - Maximum connections limit (with semaphore)
    - Connection reuse with keep-alive
    - Automatic cleanup of stale connections
    - Health checking
    - Per-key (host/user) pooling
    """

    def __init__(
        self,
        *,
        max_connections: int = 100,
        max_keepalive: int = 10,
        keepalive_timeout: float = 300.0,
        ttl_dns_cache: int = 300,
        cleanup_interval: float = 60.0,
    ) -> None:
        """
        Initialize connection pool.

        Args:
            max_connections: Maximum total connections
            max_keepalive: Maximum connections to keep alive per key
            keepalive_timeout: Timeout for idle connections (seconds)
            ttl_dns_cache: DNS cache TTL (seconds)
            cleanup_interval: Interval for cleanup task (seconds)
        """
        self.max_connections = max_connections
        self.max_keepalive = max_keepalive
        self.keepalive_timeout = keepalive_timeout
        self.ttl_dns_cache = ttl_dns_cache
        self.cleanup_interval = cleanup_interval

        # Connection storage: key -> list of PooledConnection
        self._connections: dict[str, list[PooledConnection[T]]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_connections)

        # Stats
        self._stats = {
            "total_created": 0,
            "total_reused": 0,
            "total_closed": 0,
            "total_evicted": 0,
        }

        # Cleanup task
        self._cleanup_task: asyncio.Task[None] | None = None
        self._closed = False

    async def start(self) -> None:
        """Start the connection pool and cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Connection pool started")

    async def close(self) -> None:
        """Close all connections and stop cleanup task."""
        if self._closed:
            return

        self._closed = True

        # Stop cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        async with self._lock:
            for key, conns in self._connections.items():
                for pooled_conn in conns:
                    await self._close_connection(pooled_conn.connection)
                    self._stats["total_closed"] += 1
            self._connections.clear()

        logger.info(
            f"Connection pool closed. Stats: {self._stats}"
        )

    async def acquire(
        self,
        key: str,
        factory: Any,  # Callable[[], Awaitable[T]]
    ) -> T:
        """
        Acquire a connection from the pool or create a new one.

        Args:
            key: Unique key for connection grouping (e.g., "host:port:user")
            factory: Async factory function to create new connections

        Returns:
            Connection object

        Raises:
            ProxmoxConnectionError: If pool is closed or factory fails
        """
        if self._closed:
            raise ProxmoxConnectionError("Connection pool is closed")

        # Try to get existing connection
        async with self._lock:
            connections = self._connections[key]

            # Find healthy idle connection
            for i, pooled_conn in enumerate(connections):
                if pooled_conn.is_healthy and pooled_conn.idle_time < self.keepalive_timeout:
                    # Reuse this connection
                    connections.pop(i)
                    pooled_conn.mark_used()
                    self._stats["total_reused"] += 1

                    logger.debug(
                        f"Reusing connection {pooled_conn.key} "
                        f"(age: {pooled_conn.age:.1f}s, uses: {pooled_conn.use_count})"
                    )
                    return pooled_conn.connection

        # No healthy connection available, create new one
        await self._semaphore.acquire()

        try:
            connection = await factory()
            self._stats["total_created"] += 1

            logger.debug(f"Created new connection for {key}")
            return connection

        except Exception as e:
            self._semaphore.release()
            raise ProxmoxConnectionError(
                f"Failed to create connection for {key}: {e}",
            ) from e

    async def release(self, key: str, connection: T) -> None:
        """
        Release a connection back to the pool.

        Args:
            key: Connection key
            connection: Connection to release
        """
        if self._closed:
            await self._close_connection(connection)
            self._semaphore.release()
            return

        async with self._lock:
            connections = self._connections[key]

            # Check if we have room in keep-alive pool
            if len(connections) < self.max_keepalive:
                pooled_conn = PooledConnection(connection, key)
                connections.append(pooled_conn)
                logger.debug(f"Released connection {key} to pool")
            else:
                # Pool full, close connection
                await self._close_connection(connection)
                self._stats["total_evicted"] += 1
                logger.debug(f"Connection pool full for {key}, closed connection")

        self._semaphore.release()

    async def mark_unhealthy(self, key: str, connection: T) -> None:
        """
        Mark a connection as unhealthy (will be cleaned up).

        Args:
            key: Connection key
            connection: Connection to mark
        """
        async with self._lock:
            connections = self._connections[key]

            for pooled_conn in connections:
                if pooled_conn.connection is connection:
                    pooled_conn.mark_unhealthy()
                    logger.debug(f"Marked connection {key} as unhealthy")
                    break

    def get_stats(self) -> dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Statistics dictionary
        """
        active_count = sum(len(conns) for conns in self._connections.values())

        return {
            **self._stats,
            "active_connections": active_count,
            "keys_count": len(self._connections),
            "max_connections": self.max_connections,
            "max_keepalive": self.max_keepalive,
        }

    async def _cleanup_loop(self) -> None:
        """Background task to cleanup stale connections."""
        while not self._closed:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def _cleanup_stale_connections(self) -> None:
        """Remove stale or unhealthy connections."""
        now = time.time()
        removed = 0

        async with self._lock:
            for key, connections in list(self._connections.items()):
                # Filter out stale/unhealthy connections
                stale = []
                keep = []

                for pooled_conn in connections:
                    is_stale = (
                        not pooled_conn.is_healthy
                        or pooled_conn.idle_time > self.keepalive_timeout
                    )

                    if is_stale:
                        stale.append(pooled_conn)
                    else:
                        keep.append(pooled_conn)

                # Close stale connections
                for pooled_conn in stale:
                    await self._close_connection(pooled_conn.connection)
                    removed += 1

                # Update pool
                if keep:
                    self._connections[key] = keep
                else:
                    del self._connections[key]

        if removed > 0:
            logger.debug(f"Cleaned up {removed} stale connections")
            self._stats["total_closed"] += removed

    async def _close_connection(self, connection: T) -> None:
        """
        Close a connection safely.

        Args:
            connection: Connection to close
        """
        try:
            if hasattr(connection, "close"):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    def __repr__(self) -> str:
        """Return string representation."""
        stats = self.get_stats()
        return (
            f"ConnectionPool("
            f"active={stats['active_connections']}, "
            f"max={self.max_connections}, "
            f"created={stats['total_created']}, "
            f"reused={stats['total_reused']})"
        )


def create_pool_from_config(config: PoolConfig) -> ConnectionPool[Any]:
    """
    Create connection pool from configuration.

    Args:
        config: Pool configuration

    Returns:
        ConnectionPool instance
    """
    return ConnectionPool(
        max_connections=config.get("max_connections", 100),
        max_keepalive=config.get("max_keepalive", 10),
        keepalive_timeout=config.get("keepalive_timeout", 300.0),
        ttl_dns_cache=config.get("ttl_dns_cache", 300),
    )


__all__ = [
    "PooledConnection",
    "ConnectionPool",
    "create_pool_from_config",
]
