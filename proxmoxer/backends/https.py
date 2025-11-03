"""
Async HTTPS backend for Proxmoxer using aiohttp.

Provides high-performance async HTTP communication with Proxmox services
including authentication, file uploads, and connection pooling.
"""

__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2024"
__license__ = "MIT"

import asyncio
import io
import logging
import os
import platform
import time
from shlex import split as shell_split
from typing import Any

import aiohttp

from ..core import SERVICES
from ..exceptions import AuthenticationError, ConfigurationError
from ..retry import retry_async
from ..serializers import JsonSerializer, get_serializer

logger = logging.getLogger(__name__)

STREAMING_SIZE_THRESHOLD = 10 * 1024 * 1024  # 10 MiB
SSL_OVERFLOW_THRESHOLD = 2147483135  # 2^31 - 1 - 512


class ProxmoxHTTPAuthBase:
    """Base class for authentication handlers."""

    def __init__(
        self,
        *,
        timeout: float = 5.0,
        service: str = "PVE",
        verify_ssl: bool = True,
        cert: Any | None = None,
    ) -> None:
        """
        Initialize auth base.

        Args:
            timeout: Request timeout in seconds
            service: Service type (PVE, PMG, PBS)
            verify_ssl: Whether to verify SSL certificates
            cert: Client certificate for mutual TLS
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.service = service
        self.verify_ssl = verify_ssl
        self.cert = cert

    async def get_cookies(self) -> dict[str, str]:
        """Get cookies for authentication."""
        return {}

    async def get_tokens(self) -> tuple[str | None, str | None]:
        """Get auth and CSRF tokens."""
        return None, None

    async def prepare_request(self, session: aiohttp.ClientSession, method: str) -> None:
        """
        Prepare request with authentication.

        Args:
            session: aiohttp session
            method: HTTP method
        """
        pass


class ProxmoxHTTPAuth(ProxmoxHTTPAuthBase):
    """
    Password-based authentication with automatic ticket renewal.

    Proxmox uses ticket-based authentication with a 2-hour expiration.
    This handler automatically renews tickets before they expire.
    """

    renew_age = 3600  # Renew after 1 hour (before 2-hour expiration)

    def __init__(
        self,
        username: str,
        password: str,
        *,
        otp: str | None = None,
        base_url: str = "",
        **kwargs: Any,
    ) -> None:
        """
        Initialize password authentication.

        Args:
            username: Username (e.g., "root@pam")
            password: Password
            otp: One-Time Password for 2FA
            base_url: Base URL for API
            **kwargs: Additional auth options
        """
        super().__init__(**kwargs)
        self.base_url = base_url
        self.username = username
        self.password = password
        self.otp = otp

        self.pve_auth_ticket: str = ""
        self.csrf_prevention_token: str = ""
        self.birth_time: float = 0.0
        self._lock = asyncio.Lock()

    async def _get_new_tokens(self, password: str | None = None, otp: str | None = None) -> None:
        """
        Acquire new authentication tokens from Proxmox.

        Args:
            password: Password (or ticket for renewal)
            otp: One-Time Password
        """
        if password is None:
            # Refresh from existing ticket
            password = self.pve_auth_ticket

        data = {"username": self.username, "password": password}
        if otp:
            data["otp"] = otp

        # Create SSL context
        ssl_context = (
            aiohttp.TCPConnector(ssl=True if self.verify_ssl else False).ssl
            if self.verify_ssl
            else False
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/access/ticket",
                data=data,
                ssl=ssl_context,
                timeout=self.timeout,
            ) as resp:
                response_data = (await resp.json())["data"]

                if response_data is None:
                    raise AuthenticationError(
                        f"Couldn't authenticate user: {self.username}",
                        auth_method="password",
                        username=self.username,
                    )

                if response_data.get("NeedTFA") is not None:
                    raise AuthenticationError(
                        "Couldn't authenticate user: missing Two Factor Authentication (TFA)",
                        auth_method="password",
                        username=self.username,
                    )

                self.birth_time = time.monotonic()
                self.pve_auth_ticket = response_data["ticket"]
                self.csrf_prevention_token = response_data["CSRFPreventionToken"]

                logger.debug(f"Acquired new auth ticket for {self.username}")

    async def initialize(self) -> None:
        """Initialize authentication by acquiring initial token."""
        await self._get_new_tokens(password=self.password, otp=self.otp)

    async def get_cookies(self) -> dict[str, str]:
        """Get authentication cookies."""
        return {f"{self.service}AuthCookie": self.pve_auth_ticket}

    async def get_tokens(self) -> tuple[str, str]:
        """Get auth and CSRF tokens."""
        return self.pve_auth_ticket, self.csrf_prevention_token

    async def prepare_request(self, session: aiohttp.ClientSession, method: str) -> None:
        """
        Prepare request with auth, refreshing token if needed.

        Args:
            session: aiohttp session
            method: HTTP method
        """
        # Refresh ticket if older than renew_age
        async with self._lock:
            time_diff = time.monotonic() - self.birth_time

            if time_diff >= self.renew_age:
                logger.debug(f"Refreshing ticket (age {time_diff:.1f}s)")
                await self._get_new_tokens()

        # Add cookies
        session.cookie_jar.update_cookies(await self.get_cookies())

        # Add CSRF token for non-GET requests
        if method != "GET":
            session.headers["CSRFPreventionToken"] = self.csrf_prevention_token


class ProxmoxHTTPApiTokenAuth(ProxmoxHTTPAuthBase):
    """
    API Token authentication.

    More secure and recommended for automation. No session management needed.
    """

    def __init__(
        self,
        username: str,
        token_name: str,
        token_value: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize API token authentication.

        Args:
            username: Username (e.g., "root@pam")
            token_name: Token name
            token_value: Token secret value
            **kwargs: Additional auth options
        """
        super().__init__(**kwargs)
        self.username = username
        self.token_name = token_name
        self.token_value = token_value

    async def initialize(self) -> None:
        """No initialization needed for token auth."""
        pass

    async def prepare_request(self, session: aiohttp.ClientSession, method: str) -> None:
        """
        Add API token to request headers.

        Args:
            session: aiohttp session
            method: HTTP method
        """
        token_separator = SERVICES[self.service]["token_separator"]
        session.headers["Authorization"] = (
            f"{self.service}APIToken={self.username}!{self.token_name}"
            f"{token_separator}{self.token_value}"
        )


class AsyncResponse:
    """
    Wrapper for aiohttp response to match expected interface.

    Provides compatibility with serializers expecting status_code,
    content, text, and reason attributes.
    """

    def __init__(
        self,
        status_code: int,
        content: bytes,
        text: str,
        reason: str | None = None,
    ) -> None:
        """
        Initialize response wrapper.

        Args:
            status_code: HTTP status code
            content: Response body as bytes
            text: Response body as text
            reason: HTTP reason phrase
        """
        self.status_code = status_code
        self.content = content
        self.text = text
        self.reason = reason


class ProxmoxHttpSession:
    """
    Async HTTP session for Proxmox API with file upload support.

    Handles:
    - Authentication
    - Large file uploads with streaming
    - Command splitting for QEMU exec
    - Connection pooling
    """

    def __init__(
        self,
        auth: ProxmoxHTTPAuthBase,
        *,
        verify_ssl: bool = True,
        timeout: float = 5.0,
        connector: aiohttp.BaseConnector | None = None,
    ) -> None:
        """
        Initialize async HTTP session.

        Args:
            auth: Authentication handler
            verify_ssl: Whether to verify SSL certificates
            timeout: Default timeout in seconds
            connector: Optional custom aiohttp connector
        """
        self.auth = auth
        self.verify_ssl = verify_ssl
        self.default_timeout = aiohttp.ClientTimeout(total=timeout)

        # Create SSL context
        if connector is None:
            ssl_context = True if verify_ssl else False
            connector = aiohttp.TCPConnector(ssl=ssl_context, limit=100)

        self._session: aiohttp.ClientSession | None = None
        self._connector = connector
        self._closed = False

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=self.default_timeout,
                headers={
                    "Connection": "keep-alive",
                    "Accept": ", ".join(JsonSerializer().content_types),
                },
            )
        return self._session

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
        Make async HTTP request with automatic retry.

        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body data
            **kwargs: Additional options

        Returns:
            AsyncResponse object
        """
        session = await self._get_session()

        # Prepare authentication
        await self.auth.prepare_request(session, method)

        # Handle file uploads and command splitting
        files = {}
        data = data or {}
        total_file_size = 0

        for k, v in list(data.items()):
            # Split QEMU exec commands for proper parsing (issue #89)
            if k == "command" and url.endswith("agent/exec"):
                if isinstance(v, list):
                    data[k] = v
                elif "Windows" not in platform.platform():
                    data[k] = shell_split(v)

            # Handle file uploads
            if isinstance(v, io.IOBase):
                total_file_size += get_file_size(v)
                files[k] = v
                del data[k]

        # Prepare request body
        if files:
            # Use multipart for file uploads
            form_data = aiohttp.FormData()

            # Add regular data fields
            for k, v in data.items():
                form_data.add_field(k, str(v))

            # Add file fields
            for k, file_obj in files.items():
                filename = getattr(file_obj, "name", "upload")
                form_data.add_field(
                    k,
                    file_obj,
                    filename=filename,
                    content_type="application/octet-stream",
                )

            request_data = form_data
        else:
            request_data = data if data else None

        # Make request
        async with session.request(
            method,
            url,
            params=params,
            data=request_data,
            **kwargs,
        ) as resp:
            content = await resp.read()
            text = await resp.text()

            return AsyncResponse(
                status_code=resp.status,
                content=content,
                text=text,
                reason=resp.reason,
            )

    async def close(self) -> None:
        """Close session and cleanup."""
        if self._closed:
            return

        self._closed = True

        if self._session and not self._session.closed:
            await self._session.close()

        if self._connector and not self._connector.closed:
            await self._connector.close()


class Backend:
    """
    Async HTTPS backend for Proxmox API.

    Provides async HTTP communication with automatic authentication,
    connection pooling, and file upload support.
    """

    def __init__(
        self,
        host: str,
        *,
        user: str | None = None,
        password: str | None = None,
        otp: str | None = None,
        port: int | None = None,
        verify_ssl: bool = True,
        mode: str = "json",
        timeout: float = 5.0,
        token_name: str | None = None,
        token_value: str | None = None,
        path_prefix: str | None = None,
        service: str = "PVE",
        cert: Any | None = None,
    ) -> None:
        """
        Initialize HTTPS backend.

        Args:
            host: Proxmox server hostname/IP
            user: Username
            password: Password
            otp: One-Time Password for 2FA
            port: Port (default: service-specific)
            verify_ssl: Whether to verify SSL certificates
            mode: Response mode (json)
            timeout: Request timeout in seconds
            token_name: API token name
            token_value: API token value
            path_prefix: URL path prefix for reverse proxy
            service: Service type (PVE, PMG, PBS)
            cert: Client certificate for mutual TLS
        """
        self.cert = cert
        self.mode = mode

        # Parse host and port
        host_port = ""
        if len(host.split(":")) > 2:  # IPv6
            if host.startswith("["):
                if "]:" in host:
                    host, host_port = host.rsplit(":", 1)
            else:
                host = f"[{host}]"
        elif ":" in host:
            host, host_port = host.split(":")

        port = int(host_port) if host_port.isdigit() else port

        # Use default port if not specified
        if not port:
            port = SERVICES[service]["default_port"]

        # Build base URL
        if path_prefix is not None:
            self.base_url = f"https://{host}:{port}/{path_prefix}/api2/{mode}"
        else:
            self.base_url = f"https://{host}:{port}/api2/{mode}"

        # Setup authentication
        if token_name is not None:
            if "token" not in SERVICES[service]["supported_https_auths"]:
                raise ConfigurationError(
                    f"{service} does not support API Token authentication",
                    option="token_name",
                    value=token_name,
                )

            self.auth: ProxmoxHTTPAuthBase = ProxmoxHTTPApiTokenAuth(
                user or "",
                token_name,
                token_value or "",
                verify_ssl=verify_ssl,
                timeout=timeout,
                service=service,
                cert=cert,
            )
        elif password is not None:
            if "password" not in SERVICES[service]["supported_https_auths"]:
                raise ConfigurationError(
                    f"{service} does not support password authentication",
                    option="password",
                )

            self.auth = ProxmoxHTTPAuth(
                user or "",
                password,
                otp=otp,
                base_url=self.base_url,
                verify_ssl=verify_ssl,
                timeout=timeout,
                service=service,
                cert=cert,
            )
        else:
            raise ConfigurationError(
                "No valid authentication credentials were supplied",
                option="auth",
            )

        self._session: ProxmoxHttpSession | None = None
        self._serializer = get_serializer("https")

    async def initialize(self) -> None:
        """Initialize backend and authentication."""
        await self.auth.initialize()

    def get_session(self) -> ProxmoxHttpSession:
        """Get or create HTTP session."""
        if self._session is None:
            self._session = ProxmoxHttpSession(
                self.auth,
                verify_ssl=self.auth.verify_ssl,
                timeout=self.auth.timeout.total if hasattr(self.auth.timeout, "total") else 5.0,
            )
        return self._session

    def get_base_url(self) -> str:
        """Get base URL for API requests."""
        return self.base_url

    def get_serializer(self) -> JsonSerializer:
        """Get JSON serializer."""
        return self._serializer

    async def get_tokens(self) -> tuple[str | None, str | None]:
        """Get auth and CSRF tokens."""
        return await self.auth.get_tokens()

    async def close(self) -> None:
        """Close backend and cleanup resources."""
        if self._session:
            await self._session.close()


def get_file_size(file_obj: io.IOBase) -> int:
    """
    Get total size of file object without changing cursor position.

    Args:
        file_obj: File object

    Returns:
        File size in bytes
    """
    starting_cursor = file_obj.tell()
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(starting_cursor)
    return size


__all__ = [
    "Backend",
    "ProxmoxHTTPAuth",
    "ProxmoxHTTPApiTokenAuth",
    "ProxmoxHttpSession",
]
