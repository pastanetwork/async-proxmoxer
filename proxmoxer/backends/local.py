"""
Async local backend for Proxmoxer using asyncio.subprocess.

Executes pvesh commands locally on the Proxmox host using subprocess.
Includes retry logic and proper error handling.
"""

from __future__ import annotations

__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2025"
__license__ = "MIT"

import asyncio
import logging
from typing import Any

from ..core import SERVICES
from ..exceptions import ConfigurationError, SSHError
from ..retry import retry_async
from ..serializers import get_serializer

logger = logging.getLogger(__name__)


class AsyncResponse:
    """Response wrapper for subprocess execution."""

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
            status_code: HTTP-like status code (200 for success, 500 for error)
            content: Response content as bytes
            text: Response content as text
            exit_code: Subprocess exit code
        """
        self.status_code = status_code
        self.content = content
        self.text = text
        self.exit_code = exit_code
        self.reason = "OK" if status_code == 200 else "Command Failed"


class LocalSession:
    """
    Async session for local command execution.

    Executes pvesh commands using asyncio.subprocess with retry logic.
    """

    def __init__(
        self,
        service: str = "PVE",
        *,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize local session.

        Args:
            service: Service type (PVE, PMG, PBS)
            timeout: Command timeout in seconds
        """
        self.service = service
        self.timeout = timeout
        self._closed = False

        # Get service-specific CLI options
        self.cli_additional_options = SERVICES[service].get("cli_additional_options", [])

    @retry_async(max_attempts=3, initial_delay=0.5)
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
        Execute pvesh command.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: API path
            params: Query parameters
            data: Request body data
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
        cmd = [service_cmd, cmd_name, url]

        # Add CLI options
        cmd.extend(self.cli_additional_options)

        # Add parameters/data
        request_data = data or params or {}
        for key, value in request_data.items():
            if value is not None:
                cmd.extend([f"-{key}", str(value)])

        logger.debug(f"Executing local command: {' '.join(cmd)}")

        try:
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise SSHError(
                    f"Command timeout after {self.timeout}s",
                    exit_code=-1,
                    stderr="Timeout",
                )

            exit_code = process.returncode or 0

            # Determine status code
            if exit_code == 0:
                status_code = 200
            else:
                status_code = 500

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            if exit_code != 0:
                logger.warning(
                    f"Command failed (exit {exit_code}): {stderr_text}"
                )

                raise SSHError(
                    f"Command failed: {stderr_text or 'Unknown error'}",
                    exit_code=exit_code,
                    stderr=stderr_text,
                )

            return AsyncResponse(
                status_code=status_code,
                content=stdout,
                text=stdout_text,
                exit_code=exit_code,
            )

        except SSHError:
            raise
        except Exception as e:
            raise SSHError(
                f"Failed to execute command: {e}",
                exit_code=-1,
            ) from e

    async def close(self) -> None:
        """Close session."""
        self._closed = True
        logger.debug("Local session closed")


class Backend:
    """
    Async local backend for Proxmox API.

    Executes commands directly on the Proxmox host using pvesh.
    """

    def __init__(
        self,
        *,
        service: str = "PVE",
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> None:
        """
        Initialize local backend.

        Args:
            service: Service type (PVE, PMG, PBS)
            timeout: Command timeout in seconds
            **kwargs: Additional options (ignored)
        """
        # Validate service
        if service not in SERVICES:
            raise ConfigurationError(
                f"Unknown service: {service}",
                option="service",
                value=service,
            )

        # Check backend support
        if "local" not in SERVICES[service]["supported_backends"]:
            raise ConfigurationError(
                f"{service} does not support local backend",
                option="backend",
                value="local",
            )

        self.service = service
        self.timeout = timeout
        self.target = "localhost"

        # Create session
        self._session = LocalSession(
            service=service,
            timeout=timeout,
        )

        # Create serializer
        self._serializer = get_serializer("local")

        # Base URL (local path)
        self.base_url = f"/api2/json"

        logger.info(f"Initialized local backend for {service}")

    async def initialize(self) -> None:
        """Initialize backend (no-op for local)."""
        pass

    def get_session(self) -> LocalSession:
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
        logger.info("Local backend closed")


__all__ = ["Backend", "LocalSession"]
