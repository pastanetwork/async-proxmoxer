"""
Task management helpers for Proxmoxer.

Provides high-level async API for tracking and waiting for Proxmox tasks
(asynchronous operations identified by UPID).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from ..types import ResponseData

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status."""

    RUNNING = "running"
    STOPPED = "stopped"
    OK = "OK"
    ERROR = "error"


@dataclass
class Task:
    """Proxmox task information."""

    upid: str
    node: str
    pid: int
    pstart: int
    starttime: int
    type: str
    status: str | None = None
    exitstatus: str | None = None
    user: str | None = None
    id: str | None = None
    endtime: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create Task from API response."""
        return cls(
            upid=data.get("upid", ""),
            node=data.get("node", ""),
            pid=data.get("pid", 0),
            pstart=data.get("pstart", 0),
            starttime=data.get("starttime", 0),
            type=data.get("type", ""),
            status=data.get("status"),
            exitstatus=data.get("exitstatus"),
            user=data.get("user"),
            id=data.get("id"),
            endtime=data.get("endtime"),
        )

    @property
    def is_running(self) -> bool:
        """Check if task is still running."""
        return self.status == TaskStatus.RUNNING.value or self.status is None

    @property
    def is_successful(self) -> bool:
        """Check if task completed successfully."""
        return self.exitstatus == TaskStatus.OK.value

    @property
    def is_error(self) -> bool:
        """Check if task ended with error."""
        return self.exitstatus and self.exitstatus != TaskStatus.OK.value


class TasksHelper:
    """
    High-level helper for managing Proxmox tasks.

    Provides methods for tracking, waiting, and monitoring asynchronous
    operations (tasks) in Proxmox, identified by UPID.

    Example:
        >>> tasks = TasksHelper(proxmox)
        >>> upid = await proxmox.nodes("node1").qemu(100).status.start.post()
        >>> task = await tasks.wait_for_task(upid)
        >>> if task.is_successful:
        ...     print("VM started successfully")
        ...
        >>> # Or with callback for progress
        >>> await tasks.wait_for_task(upid, on_progress=lambda task: print(task.status))
    """

    def __init__(self, proxmox: Any):
        """
        Initialize TasksHelper.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    def parse_upid(self, upid: str) -> dict[str, str]:
        """
        Parse UPID into components.

        UPID format: UPID:node:pid:pstart:starttime:type:id:user@realm

        Args:
            upid: Task UPID string

        Returns:
            Dict with parsed components
        """
        parts = upid.split(":")
        if len(parts) < 8 or parts[0] != "UPID":
            raise ValueError(f"Invalid UPID format: {upid}")

        return {
            "node": parts[1],
            "pid": parts[2],
            "pstart": parts[3],
            "starttime": parts[4],
            "type": parts[5],
            "id": parts[6] if len(parts) > 6 else "",
            "user": parts[7] if len(parts) > 7 else "",
        }

    async def get_task_status(self, upid: str, node: str | None = None) -> Task:
        """
        Get task status.

        Args:
            upid: Task UPID
            node: Node name (auto-detected from UPID if not provided)

        Returns:
            Task object
        """
        if not node:
            parsed = self.parse_upid(upid)
            node = parsed["node"]

        data: ResponseData = await self.proxmox.nodes(node).tasks(upid).status.get()
        data["upid"] = upid
        data["node"] = node
        return Task.from_dict(data)

    async def get_task_log(
        self,
        upid: str,
        node: str | None = None,
        start: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get task log.

        Args:
            upid: Task UPID
            node: Node name (auto-detected if not provided)
            start: Start line
            limit: Number of lines

        Returns:
            List of log entries
        """
        if not node:
            parsed = self.parse_upid(upid)
            node = parsed["node"]

        return await self.proxmox.nodes(node).tasks(upid).log.get(
            start=start, limit=limit
        )

    async def stop_task(self, upid: str, node: str | None = None) -> None:
        """
        Stop a running task.

        Args:
            upid: Task UPID
            node: Node name (auto-detected if not provided)
        """
        if not node:
            parsed = self.parse_upid(upid)
            node = parsed["node"]

        await self.proxmox.nodes(node).tasks(upid).delete()

    async def wait_for_task(
        self,
        upid: str,
        node: str | None = None,
        timeout: float | None = None,
        poll_interval: float = 1.0,
        on_progress: Callable[[Task], None] | None = None,
    ) -> Task:
        """
        Wait for a task to complete.

        Args:
            upid: Task UPID
            node: Node name (auto-detected if not provided)
            timeout: Timeout in seconds (None for no timeout)
            poll_interval: Polling interval in seconds
            on_progress: Optional callback called on each poll with Task object

        Returns:
            Completed Task object

        Raises:
            asyncio.TimeoutError: If timeout is reached
            RuntimeError: If task fails
        """
        if not node:
            parsed = self.parse_upid(upid)
            node = parsed["node"]

        start_time = asyncio.get_event_loop().time()

        while True:
            task = await self.get_task_status(upid, node)

            if on_progress:
                on_progress(task)

            if not task.is_running:
                if task.is_error:
                    # Get last few log lines for error context
                    try:
                        log = await self.get_task_log(upid, node, start=0, limit=10)
                        error_msg = "\n".join(
                            [entry.get("t", "") for entry in log[-5:]]
                        )
                        raise RuntimeError(
                            f"Task {upid} failed with status '{task.exitstatus}': {error_msg}"
                        )
                    except Exception as e:
                        raise RuntimeError(
                            f"Task {upid} failed with status '{task.exitstatus}'"
                        ) from e
                return task

            if timeout is not None:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= timeout:
                    raise asyncio.TimeoutError(
                        f"Task {upid} did not complete within {timeout} seconds"
                    )

            await asyncio.sleep(poll_interval)

    async def wait_for_tasks(
        self,
        upids: list[str],
        timeout: float | None = None,
        poll_interval: float = 1.0,
        raise_on_error: bool = True,
    ) -> list[Task]:
        """
        Wait for multiple tasks to complete.

        Args:
            upids: List of task UPIDs
            timeout: Timeout in seconds (None for no timeout)
            poll_interval: Polling interval in seconds
            raise_on_error: Raise exception if any task fails

        Returns:
            List of completed Task objects

        Raises:
            asyncio.TimeoutError: If timeout is reached
            RuntimeError: If any task fails and raise_on_error is True
        """
        tasks = await asyncio.gather(
            *[
                self.wait_for_task(
                    upid, timeout=timeout, poll_interval=poll_interval
                )
                for upid in upids
            ],
            return_exceptions=not raise_on_error,
        )

        if not raise_on_error:
            # Filter out exceptions
            return [t for t in tasks if isinstance(t, Task)]

        return tasks

    async def get_task_result(
        self,
        upid: str,
        node: str | None = None,
        timeout: float | None = None,
        poll_interval: float = 1.0,
    ) -> Any:
        """
        Wait for task and return its result.

        This is a convenience method that waits for completion
        and returns the task object if successful.

        Args:
            upid: Task UPID
            node: Node name
            timeout: Timeout in seconds
            poll_interval: Polling interval

        Returns:
            Task object if successful

        Raises:
            asyncio.TimeoutError: If timeout is reached
            RuntimeError: If task fails
        """
        task = await self.wait_for_task(
            upid, node=node, timeout=timeout, poll_interval=poll_interval
        )
        return task

    async def stream_task_log(
        self,
        upid: str,
        node: str | None = None,
        callback: Callable[[str], None] | None = None,
        poll_interval: float = 0.5,
    ) -> None:
        """
        Stream task log in real-time until task completes.

        Args:
            upid: Task UPID
            node: Node name
            callback: Callback function for each new log line
            poll_interval: Polling interval in seconds
        """
        if not node:
            parsed = self.parse_upid(upid)
            node = parsed["node"]

        start = 0
        while True:
            task = await self.get_task_status(upid, node)

            # Get new log lines
            log_entries = await self.get_task_log(
                upid, node, start=start, limit=1000
            )

            for entry in log_entries:
                line = entry.get("t", "")
                if callback:
                    callback(line)
                else:
                    print(line)
                start += 1

            if not task.is_running:
                break

            await asyncio.sleep(poll_interval)

    async def list_node_tasks(
        self,
        node: str,
        vmid: int | None = None,
        errors: bool = False,
        limit: int | None = None,
        start: int | None = None,
    ) -> list[Task]:
        """
        List tasks on a node.

        Args:
            node: Node name
            vmid: Filter by VM ID
            errors: Only show tasks with errors
            limit: Limit number of results
            start: Start at specific offset

        Returns:
            List of Task objects
        """
        params = {}
        if vmid:
            params["vmid"] = vmid
        if errors:
            params["errors"] = 1
        if limit:
            params["limit"] = limit
        if start:
            params["start"] = start

        data: ResponseData = await self.proxmox.nodes(node).tasks.get(**params)
        return [Task.from_dict(t) for t in data]

    async def list_cluster_tasks(
        self,
        errors: bool = False,
        limit: int | None = None,
    ) -> list[Task]:
        """
        List tasks across entire cluster.

        Args:
            errors: Only show tasks with errors
            limit: Limit number of results

        Returns:
            List of Task objects
        """
        params = {}
        if errors:
            params["errors"] = 1
        if limit:
            params["limit"] = limit

        data: ResponseData = await self.proxmox.cluster.tasks.get(**params)
        return [Task.from_dict(t) for t in data]

    async def get_active_tasks(self, node: str | None = None) -> list[Task]:
        """
        Get currently running tasks.

        Args:
            node: Node name (None for cluster-wide)

        Returns:
            List of running Task objects
        """
        if node:
            tasks = await self.list_node_tasks(node)
        else:
            tasks = await self.list_cluster_tasks()

        return [t for t in tasks if t.is_running]

    async def get_failed_tasks(
        self, node: str | None = None, limit: int = 50
    ) -> list[Task]:
        """
        Get recently failed tasks.

        Args:
            node: Node name (None for cluster-wide)
            limit: Maximum number of tasks to return

        Returns:
            List of failed Task objects
        """
        if node:
            tasks = await self.list_node_tasks(node, errors=True, limit=limit)
        else:
            tasks = await self.list_cluster_tasks(errors=True, limit=limit)

        return tasks
