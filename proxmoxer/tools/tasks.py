"""
Async task monitoring for Proxmoxer.

Provides utilities for waiting on and monitoring Proxmox async tasks (UPIDs).
"""

from __future__ import annotations

__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2022-2025"
__license__ = "MIT"

import asyncio
import logging
from typing import Any

from ..exceptions import TaskError, TimeoutError as ProxmoxTimeoutError
from ..retry import retry_async
from ..types import TaskStatus, UPIDInfo

logger = logging.getLogger(__name__)


class Tasks:
    """
    Async task monitoring utilities for Proxmox.

    Provides methods for waiting on task completion and parsing UPIDs.
    """

    @staticmethod
    @retry_async(max_attempts=5, initial_delay=1.0)
    async def wait_for_task(
        prox: Any,
        task_id: str,
        *,
        timeout: float = 300.0,
        polling_interval: float = 1.0,
    ) -> TaskStatus:
        """
        Wait for Proxmox task to complete.

        Polls the task status endpoint until task completes or timeout occurs.

        Args:
            prox: ProxmoxAPI instance
            task_id: UPID of the task
            timeout: Maximum time to wait in seconds
            polling_interval: Time between status checks

        Returns:
            Final task status

        Raises:
            ProxmoxTimeoutError: If task doesn't complete within timeout
            TaskError: If task fails

        Example:
            async with await ProxmoxAPI.create(...) as proxmox:
                upid = await proxmox.nodes("node1").qemu(100).status.start.post()
                result = await Tasks.wait_for_task(proxmox, upid)
                print(f"Task completed: {result['exitstatus']}")
        """
        # Decode UPID to get node
        upid_info = Tasks.decode_upid(task_id)
        node = upid_info["node"]

        logger.info(f"Waiting for task {task_id} on node {node}")

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise ProxmoxTimeoutError(
                    f"Task {task_id} did not complete within {timeout}s",
                    timeout=timeout,
                    operation="wait_for_task",
                )

            # Get task status
            status = await prox.nodes(node).tasks(task_id).status.get()

            # Check if task completed
            if status.get("status") == "stopped":
                exit_status = status.get("exitstatus", "unknown")

                if exit_status == "OK":
                    logger.info(f"Task {task_id} completed successfully")
                    return status
                else:
                    # Task failed
                    logger.error(f"Task {task_id} failed: {exit_status}")

                    raise TaskError(
                        f"Task failed with status: {exit_status}",
                        upid=task_id,
                        task_status=exit_status,
                    )

            # Wait before next poll
            await asyncio.sleep(polling_interval)

    @staticmethod
    async def get_task_log(
        prox: Any,
        task_id: str,
        *,
        start: int = 0,
        limit: int | None = None,
    ) -> str:
        """
        Get task log.

        Args:
            prox: ProxmoxAPI instance
            task_id: UPID of the task
            start: Start line number
            limit: Max number of lines

        Returns:
            Log as multiline string

        Example:
            log = await Tasks.get_task_log(proxmox, upid)
            print(log)
        """
        upid_info = Tasks.decode_upid(task_id)
        node = upid_info["node"]

        # Get log
        params: dict[str, Any] = {"start": start}
        if limit is not None:
            params["limit"] = limit

        log_data = await prox.nodes(node).tasks(task_id).log.get(**params)

        # Decode log
        return Tasks.decode_log(log_data)

    @staticmethod
    def decode_upid(upid: str) -> UPIDInfo:
        """
        Decode UPID string into structured information.

        Args:
            upid: UPID string (format: UPID:node:pid:pstart:starttime:type:id:user:comment)

        Returns:
            Decoded UPID information

        Raises:
            TaskError: If UPID format is invalid

        Example:
            info = Tasks.decode_upid("UPID:pve:00001234:00005678:5A1B2C3D:qmstart:100:root@pam:")
            print(f"Node: {info['node']}, Type: {info['type']}")
        """
        segments = upid.split(":")

        if segments[0] != "UPID" or len(segments) != 9:
            raise TaskError(
                "Invalid UPID format (expected: UPID:node:pid:pstart:starttime:type:id:user:comment)",
                upid=upid,
            )

        try:
            upid_info: UPIDInfo = {
                "node": segments[1],
                "pid": int(segments[2], 16),  # Hex
                "pstart": int(segments[3], 16),  # Hex
                "starttime": int(segments[4], 16),  # Hex
                "type": segments[5],
                "id": segments[6],
                "user": segments[7].split("!")[0],  # Remove token part
                "comment": segments[8] if segments[8] else None,
            }

            return upid_info

        except (ValueError, IndexError) as e:
            raise TaskError(
                f"Failed to parse UPID: {e}",
                upid=upid,
            ) from e

    @staticmethod
    def decode_log(log_list: list[dict[str, Any]]) -> str:
        """
        Decode task log from API format to multiline string.

        Args:
            log_list: Log data from API (list of dicts with 'n' and 't' keys)

        Returns:
            Formatted log string

        Example:
            log_data = await proxmox.nodes("node1").tasks(upid).log.get()
            log_text = Tasks.decode_log(log_data)
            print(log_text)
        """
        if not log_list:
            return ""

        # Find max line number
        max_line = max(line.get("n", 0) for line in log_list)

        # Create array for lines
        str_list = [""] * max_line

        # Fill in lines
        for line in log_list:
            line_num = line.get("n", 0)
            if line_num > 0:
                str_list[line_num - 1] = line.get("t", "")

        return "\n".join(str_list)

    @staticmethod
    async def wait_for_multiple_tasks(
        prox: Any,
        task_ids: list[str],
        *,
        timeout: float = 300.0,
        polling_interval: float = 1.0,
        fail_fast: bool = False,
    ) -> dict[str, TaskStatus | Exception]:
        """
        Wait for multiple tasks concurrently.

        Args:
            prox: ProxmoxAPI instance
            task_ids: List of UPIDs
            timeout: Timeout per task
            polling_interval: Polling interval
            fail_fast: If True, cancel remaining tasks if one fails

        Returns:
            Dictionary mapping UPID to result (TaskStatus or Exception)

        Example:
            upids = [
                await proxmox.nodes("node1").qemu(100).status.start.post(),
                await proxmox.nodes("node1").qemu(101).status.start.post(),
            ]

            results = await Tasks.wait_for_multiple_tasks(proxmox, upids)

            for upid, result in results.items():
                if isinstance(result, Exception):
                    print(f"Task {upid} failed: {result}")
                else:
                    print(f"Task {upid} completed: {result['exitstatus']}")
        """
        logger.info(f"Waiting for {len(task_ids)} tasks")

        # Create tasks
        tasks = [
            Tasks.wait_for_task(
                prox,
                task_id,
                timeout=timeout,
                polling_interval=polling_interval,
            )
            for task_id in task_ids
        ]

        # Gather results
        if fail_fast:
            # Use asyncio.gather without return_exceptions
            # Will raise first exception
            results_list = await asyncio.gather(*tasks)
            return dict(zip(task_ids, results_list))
        else:
            # Gather all results, including exceptions
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            return dict(zip(task_ids, results_list))

    @staticmethod
    async def get_task_status(
        prox: Any,
        task_id: str,
    ) -> TaskStatus:
        """
        Get current task status (non-blocking).

        Args:
            prox: ProxmoxAPI instance
            task_id: UPID of the task

        Returns:
            Current task status

        Example:
            status = await Tasks.get_task_status(proxmox, upid)
            print(f"Status: {status['status']}")
        """
        upid_info = Tasks.decode_upid(task_id)
        node = upid_info["node"]

        return await prox.nodes(node).tasks(task_id).status.get()


__all__ = ["Tasks"]
