"""
Async SSH backend for Proxmoxer using asyncssh.

Provides SSH connectivity to remote Proxmox hosts with connection pooling
and automatic retry.
"""

from __future__ import annotations

__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2025"
__license__ = "MIT"

import asyncio
import logging
from pathlib import Path
from typing import Any

import asyncssh

from ..core import SERVICES
from ..exceptions import ConfigurationError, ConnectionError as ProxmoxConnectionError, SSHError
from ..pool import ConnectionPool
from ..retry import retry_async
from ..serializers import get_serializer

logger = logging.getLogger(__name__)


class AsyncResponse:
    """Response wrapper for SSH command execution."""

    def __init__(
        self,
        status_code: int,
        content: bytes,
        text: str,
        exit_code: int,
    ) -> None:
        """
        Initialize response.

        Args:
            status_code: HTTP-like status code
            content: Response content as bytes
            text: Response content as text
            exit_code: Command exit code
        """
        self.status_code = status_code
        self.content = content
        self.text = text
        self.exit_code = exit_code
        self.reason = "OK" if status_code == 200 else "Command Failed"


class SSHSession:
    """
    Async SSH session with connection pooling and retry.

    Executes pvesh commands on remote Proxmox hosts via SSH.
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 22,
        user: str = "root",
        password: str | None = None,
        private_key: str | Path | None = None,
        service: str = "PVE",
        timeout: float = 30.0,
        connection_pool: ConnectionPool[asyncssh.SSHClientConnection] | None = None,
    ) -> None:
        """
        Initialize SSH session.

        Args:
            host: SSH host
            port: SSH port
            user: SSH username
            password: SSH password (if not using key)
            private_key: Path to private key file
            service: Service type (PVE, PMG, PBS)
            timeout: Command timeout
            connection_pool: Optional connection pool
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.private_key = Path(private_key) if private_key else None
        self.service = service
        self.timeout = timeout

        # Connection pool (create if not provided)
        self._pool = connection_pool or ConnectionPool(
            max_connections=10,
            max_keepalive=5,
            keepalive_timeout=300.0,
        )
        self._own_pool = connection_pool is None  # Track if we own the pool

        # Service-specific CLI options
        self.cli_additional_options = SERVICES[service].get("cli_additional_options", [])

        self._closed = False

    async def initialize(self) -> None:
        """Initialize session and pool."""
        if self._own_pool:
            await self._pool.start()

    async def _create_connection(self) -> asyncssh.SSHClientConnection:
        """
        Create new SSH connection.

        Returns:
            SSH connection object

        Raises:
            ProxmoxConnectionError: If connection fails
        """
        try:
            # Prepare connection options
            connect_options: dict[str, Any] = {
                "host": self.host,
                "port": self.port,
                "username": self.user,
                "known_hosts": None,  # Don't verify host keys (configurable)
            }

            # Add authentication
            if self.private_key:
                connect_options["client_keys"] = [str(self.private_key)]
            elif self.password:
                connect_options["password"] = self.password
            else:
                # Try agent or default keys
                pass

            logger.debug(f"Connecting to {self.user}@{self.host}:{self.port}")

            conn = await asyncssh.connect(**connect_options)

            logger.info(f"SSH connection established to {self.host}")

            return conn

        except asyncssh.Error as e:
            raise ProxmoxConnectionError(
                f"SSH connection failed: {e}",
                host=self.host,
                port=self.port,
            ) from e
        except Exception as e:
            raise ProxmoxConnectionError(
                f"Unexpected error during SSH connection: {e}",
                host=self.host,
                port=self.port,
            ) from e

    @retry_async(max_attempts=3, initial_delay=1.0)
    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AsyncResponse:
        """
        Execute SSH command with retry.

        Args:
            method: HTTP method
            url: API path
            params: Query parameters
            data: Request data
            **kwargs: Additional options

        Returns:
            AsyncResponse object

        Raises:
            SSHError: If command execution fails
        """
        if self._closed:
            raise SSHError("Session is closed")

        # Map HTTP method to pvesh command
        method_map = {
            "POST": "create",
            "PUT": "set",
            "GET": "get",
            "DELETE": "delete",
        }

        cmd_name = method_map.get(method, "get")

        # Build command
        service_cmd = f"{self.service.lower()}sh"
        cmd_parts = [service_cmd, cmd_name, url]

        # Add CLI options
        cmd_parts.extend(self.cli_additional_options)

        # Add parameters/data
        request_data = data or params or {}
        for key, value in request_data.items():
            if value is not None:
                cmd_parts.extend([f"-{key}", str(value)])

        cmd = " ".join(cmd_parts)

        logger.debug(f"Executing SSH command: {cmd}")

        # Get connection from pool
        pool_key = f"{self.host}:{self.port}:{self.user}"

        conn = await self._pool.acquire(
            pool_key,
            self._create_connection,
        )

        try:
            # Execute command
            result = await asyncio.wait_for(
                conn.run(cmd, check=False),
                timeout=self.timeout,
            )

            exit_code = result.exit_status or 0

            # Determine status code
            if exit_code == 0:
                status_code = 200
            else:
                status_code = 500

            # Get output
            stdout = result.stdout or ""
            stderr = result.stderr or ""

            if exit_code != 0:
                logger.warning(
                    f"SSH command failed (exit {exit_code}): {stderr}"
                )

                # Mark connection as unhealthy if error
                await self._pool.mark_unhealthy(pool_key, conn)

                raise SSHError(
                    f"Command failed: {stderr or 'Unknown error'}",
                    host=self.host,
                    exit_code=exit_code,
                    stderr=stderr,
                )

            # Release connection back to pool
            await self._pool.release(pool_key, conn)

            return AsyncResponse(
                status_code=status_code,
                content=stdout.encode("utf-8"),
                text=stdout,
                exit_code=exit_code,
            )

        except asyncio.TimeoutError:
            # Mark connection as unhealthy on timeout
            await self._pool.mark_unhealthy(pool_key, conn)

            raise SSHError(
                f"Command timeout after {self.timeout}s",
                host=self.host,
                exit_code=-1,
                stderr="Timeout",
            )

        except SSHError:
            raise

        except Exception as e:
            # Mark connection as unhealthy on error
            await self._pool.mark_unhealthy(pool_key, conn)

            raise SSHError(
                f"Failed to execute SSH command: {e}",
                host=self.host,
                exit_code=-1,
            ) from e

    async def close(self) -> None:
        """Close session and pool."""
        if self._closed:
            return

        self._closed = True

        # Close pool if we own it
        if self._own_pool:
            await self._pool.close()

        logger.info(f"SSH session closed for {self.host}")


class Backend:
    """
    Async SSH backend for Proxmox API.

    Provides SSH connectivity to remote Proxmox hosts with connection pooling.
    """

    def __init__(
        self,
        host: str,
        *,
        port: int = 22,
        user: str = "root",
        password: str | None = None,
        private_key: str | None = None,
        service: str = "PVE",
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SSH backend.

        Args:
            host: SSH host
            port: SSH port
            user: SSH username
            password: SSH password
            private_key: Path to private key
            service: Service type (PVE, PMG, PBS)
            timeout: Command timeout
            **kwargs: Additional options
        """
        # Validate service
        if service not in SERVICES:
            raise ConfigurationError(
                f"Unknown service: {service}",
                option="service",
                value=service,
            )

        # Check backend support
        if "ssh" not in SERVICES[service]["supported_backends"]:
            raise ConfigurationError(
                f"{service} does not support SSH backend",
                option="backend",
                value="ssh",
            )

        self.host = host
        self.port = port
        self.user = user
        self.service = service
        self.target = f"{user}@{host}:{port}"

        # Create connection pool
        self._pool = ConnectionPool[asyncssh.SSHClientConnection](
            max_connections=20,
            max_keepalive=10,
            keepalive_timeout=300.0,
        )

        # Create session
        self._session = SSHSession(
            host=host,
            port=port,
            user=user,
            password=password,
            private_key=private_key,
            service=service,
            timeout=timeout,
            connection_pool=self._pool,
        )

        # Create serializer
        self._serializer = get_serializer("ssh")

        # Base URL
        self.base_url = f"/api2/json"

        logger.info(f"Initialized SSH backend for {self.target} ({service})")

    async def initialize(self) -> None:
        """Initialize backend."""
        await self._session.initialize()
        logger.debug(f"SSH backend initialized for {self.target}")

    def get_session(self) -> SSHSession:
        """Get session object."""
        return self._session

    def get_base_url(self) -> str:
        """Get base URL."""
        return self.base_url

    def get_serializer(self) -> Any:
        """Get JSON serializer."""
        return self._serializer

    async def close(self) -> None:
        """Close backend."""
        await self._session.close()
        logger.info(f"SSH backend closed for {self.target}")


__all__ = ["Backend", "SSHSession"]
