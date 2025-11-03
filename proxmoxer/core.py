"""
Async core module for Proxmoxer.

Provides async versions of ProxmoxResource and ProxmoxAPI with full
asyncio support, connection pooling, and modern Python features.
"""

from __future__ import annotations

__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2024"
__license__ = "MIT"

import importlib
import logging
import posixpath
from http import client as httplib
from typing import Any, Literal
from urllib import parse as urlparse

from .exceptions import (
    ConfigurationError,
    ResourceException as NewResourceException,
)
from .serializers import ErrorSerializer
from .types import PathSegment, RequestParams, ResponseData, ServiceType

logger = logging.getLogger(__name__)

# https://metacpan.org/pod/AnyEvent::HTTP
ANYEVENT_HTTP_STATUS_CODES = {
    595: "Errors during connection establishment, proxy handshake",
    596: "Errors during TLS negotiation, request sending and header processing",
    597: "Errors during body receiving or processing",
    598: "User aborted request via on_header or on_body",
    599: "Other, usually nonretryable, errors (garbled URL etc.)",
}

SERVICES = {
    "PVE": {
        "supported_backends": ["local", "https", "ssh"],
        "supported_https_auths": ["password", "token"],
        "default_port": 8006,
        "token_separator": "=",
        "cli_additional_options": ["--output-format", "json"],
    },
    "PMG": {
        "supported_backends": ["local", "https", "ssh"],
        "supported_https_auths": ["password"],
        "default_port": 8006,
    },
    "PBS": {
        "supported_backends": ["https"],
        "supported_https_auths": ["password", "token"],
        "default_port": 8007,
        "token_separator": ":",
    },
}


class ProxmoxResource:
    """
    Async Proxmox resource for dynamic API path building.

    Supports attribute-based path construction and async HTTP methods.

    Example:
        resource = ProxmoxResource(...)
        nodes = resource.nodes
        node1 = nodes.node1
        vms = await node1.qemu.get()
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize ProxmoxResource.

        Args:
            **kwargs: Resource configuration (base_url, session, serializer, etc.)
        """
        self._store = kwargs

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ProxmoxResource ({self._store.get('base_url')})"

    def __getattr__(self, item: str) -> "ProxmoxResource":
        """
        Build resource path dynamically via attribute access.

        Args:
            item: Path segment

        Returns:
            New ProxmoxResource with extended path

        Raises:
            AttributeError: If attribute starts with underscore
        """
        if item.startswith("_"):
            raise AttributeError(item)

        kwargs = self._store.copy()
        kwargs["base_url"] = self.url_join(self._store["base_url"], item)

        return ProxmoxResource(**kwargs)

    def url_join(self, base: str, *args: PathSegment) -> Literal[b""]:
        """
        Join URL path segments.

        Args:
            base: Base URL
            *args: Path segments to append

        Returns:
            Joined URL
        """
        scheme, netloc, path, query, fragment = urlparse.urlsplit(base)
        path = path if len(path) else "/"
        path = posixpath.join(path, *[str(x) for x in args])
        return urlparse.urlunsplit([scheme, netloc, path, query, fragment])

    def __call__(
        self,
        resource_id: PathSegment | list[PathSegment] | tuple[PathSegment, ...] | None = None,
    ) -> "ProxmoxResource":
        """
        Extend resource path with ID(s).

        Args:
            resource_id: Resource ID (string, int, or list/tuple of segments)

        Returns:
            New ProxmoxResource with extended path

        Example:
            resource.qemu(100)  # -> /qemu/100
            resource.qemu("100/status")  # -> /qemu/100/status
        """
        if resource_id in (None, ""):
            return self

        if isinstance(resource_id, (bytes, str)):
            resource_id = resource_id.split("/")
        elif not isinstance(resource_id, (tuple, list)):
            resource_id = [str(resource_id)]

        kwargs = self._store.copy()
        if resource_id is not None:
            kwargs["base_url"] = self.url_join(self._store["base_url"], *resource_id)

        return ProxmoxResource(**kwargs)

    async def _request(
        self,
        method: str,
        data: RequestParams | None = None,
        params: RequestParams | None = None,
    ) -> ResponseData:
        """
        Make an async HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            data: Request body data
            params: Query parameters

        Returns:
            Deserialized response data

        Raises:
            NewResourceException: If request fails (status >= 400)
        """
        url = self._store["base_url"]

        if data:
            logger.info(f"{method} {url} {data}")
        else:
            logger.info(f"{method} {url}")

        # Remove None values (pvesh doesn't handle them well)
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        if data:
            data = {k: v for k, v in data.items() if v is not None}

        # Make async request
        resp = await self._store["session"].request(method, url, data=data, params=params)

        logger.debug(f"Status code: {resp.status_code}, output: {resp.content!r}")

        # Handle errors
        if resp.status_code >= 400:
            error_serializer = ErrorSerializer()

            if hasattr(resp, "reason"):
                raise NewResourceException(
                    f"{httplib.responses.get(resp.status_code, ANYEVENT_HTTP_STATUS_CODES.get(resp.status_code))}: {resp.reason}",
                    status_code=resp.status_code,
                    content=resp.reason,
                    errors=error_serializer.loads(resp),
                )
            else:
                raise NewResourceException(
                    f"{httplib.responses.get(resp.status_code, ANYEVENT_HTTP_STATUS_CODES.get(resp.status_code))}: {resp.text}",
                    status_code=resp.status_code,
                    content=resp.text,
                )

        # Success response
        elif 200 <= resp.status_code <= 299:
            return self._store["serializer"].loads(resp)

        return None

    async def get(
        self,
        *args: PathSegment,
        **params: Any,
    ) -> ResponseData:
        """
        GET request.

        Args:
            *args: Path segments
            **params: Query parameters

        Returns:
            Response data
        """
        return await self(args)._request("GET", params=params)

    async def post(
        self,
        *args: PathSegment,
        **data: Any,
    ) -> ResponseData:
        """
        POST request.

        Args:
            *args: Path segments
            **data: Request body data

        Returns:
            Response data
        """
        return await self(args)._request("POST", data=data)

    async def put(
        self,
        *args: PathSegment,
        **data: Any,
    ) -> ResponseData:
        """
        PUT request.

        Args:
            *args: Path segments
            **data: Request body data

        Returns:
            Response data
        """
        return await self(args)._request("PUT", data=data)

    async def delete(
        self,
        *args: PathSegment,
        **params: Any,
    ) -> ResponseData:
        """
        DELETE request.

        Args:
            *args: Path segments
            **params: Query parameters

        Returns:
            Response data
        """
        return await self(args)._request("DELETE", params=params)

    async def create(
        self,
        *args: PathSegment,
        **data: Any,
    ) -> ResponseData:
        """
        Alias for POST.

        Args:
            *args: Path segments
            **data: Request body data

        Returns:
            Response data
        """
        return await self.post(*args, **data)

    async def set(
        self,
        *args: PathSegment,
        **data: Any,
    ) -> ResponseData:
        """
        Alias for PUT.

        Args:
            *args: Path segments
            **data: Request body data

        Returns:
            Response data
        """
        return await self.put(*args, **data)


class ProxmoxAPI(ProxmoxResource):
    """
    Async Proxmox API client.

    Main entry point for interacting with Proxmox services (PVE, PMG, PBS).

    Example:
        async with ProxmoxAPI.create(
            host="proxmox.example.com",
            user="root@pam",
            password="secret",
        ) as proxmox:
            nodes = await proxmox.nodes.get()
            print(nodes)
    """

    def __init__(
        self,
        backend: Any,
        backend_name: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ProxmoxAPI (internal use, prefer create() class method).

        Args:
            backend: Backend instance
            backend_name: Backend type name
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        self._backend = backend
        self._backend_name = backend_name
        self._closed = False

        self._store = {
            "base_url": self._backend.get_base_url(),
            "session": self._backend.get_session(),
            "serializer": self._backend.get_serializer(),
        }

    @classmethod
    async def create(
        cls,
        host: str | None = None,
        *,
        backend: str = "https",
        service: ServiceType = "PVE",
        **kwargs: Any,
    ) -> "ProxmoxAPI":
        """
        Create and initialize ProxmoxAPI instance.

        Args:
            host: Proxmox server hostname/IP
            backend: Backend type (https, ssh, local)
            service: Service type (PVE, PMG, PBS)
            **kwargs: Backend-specific configuration

        Returns:
            Initialized ProxmoxAPI instance

        Raises:
            ConfigurationError: If service or backend is unsupported

        Example:
            proxmox = await ProxmoxAPI.create(
                host="10.0.0.1",
                user="root@pam",
                password="secret",
            )
        """
        service = service.upper()  # type: ignore
        backend = backend.lower()

        # Validate service
        if service not in SERVICES.keys():
            raise ConfigurationError(
                f"{service} service is not supported",
                option="service",
                value=service,
            )

        # Validate backend for service
        if backend not in SERVICES[service]["supported_backends"]:
            raise ConfigurationError(
                f"{service} service does not support {backend} backend",
                option="backend",
                value=backend,
            )

        # Validate host requirement
        if host is not None:
            if backend == "local":
                raise ConfigurationError(
                    f"{backend} backend does not support host keyword",
                    option="host",
                    value=host,
                )
            else:
                kwargs["host"] = host

        kwargs["service"] = service

        # Load backend module
        backend_module = importlib.import_module(
            f".backends.{backend}", "proxmoxer"
        )
        backend_instance = backend_module.Backend(**kwargs)

        # Initialize backend if needed
        if hasattr(backend_instance, "initialize"):
            await backend_instance.initialize()

        return cls(
            backend=backend_instance,
            backend_name=backend,
            **kwargs,
        )

    def __repr__(self) -> str:
        """Return string representation."""
        dest = getattr(self._backend, "target", self._store.get("base_url"))
        return f"ProxmoxAPI ({self._backend_name} backend for {dest})"

    async def __aenter__(self) -> "ProxmoxAPI":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit with cleanup."""
        await self.close()

    async def close(self) -> None:
        """Close API connection and cleanup resources."""
        if self._closed:
            return

        self._closed = True

        # Close backend
        if hasattr(self._backend, "close"):
            await self._backend.close()

        logger.info(f"ProxmoxAPI closed ({self._backend_name} backend)")

    async def get_tokens(self) -> tuple[str | None, str | None]:
        """
        Get auth and CSRF tokens (HTTPS backend only).

        Returns:
            Tuple of (auth_token, csrf_token) or (None, None)
        """
        if self._backend_name != "https":
            return None, None

        if hasattr(self._backend, "get_tokens"):
            return await self._backend.get_tokens()

        return None, None


__all__ = [
    "ProxmoxResource",
    "ProxmoxAPI",
    "SERVICES",
    "ANYEVENT_HTTP_STATUS_CODES",
]
