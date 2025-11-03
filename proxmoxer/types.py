"""
Type definitions and protocols for Proxmoxer.

Provides type hints, protocols, and typed dictionaries for
improved type safety and IDE support.
"""
from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict, runtime_checkable


# Service types
ServiceType = Literal["PVE", "PMG", "PBS"]
BackendType = Literal["https", "ssh", "local"]
AuthMethod = Literal["password", "token"]
HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]


class ServiceConfig(TypedDict, total=False):
    """Configuration for a Proxmox service."""

    supported_backends: list[str]
    supported_https_auths: list[str]
    default_port: int
    token_separator: str
    cli_additional_options: list[str]


class BackendConfig(TypedDict, total=False):
    """Configuration for backend initialization."""

    host: str
    port: int
    user: str
    password: str
    token_name: str
    token_value: str
    verify_ssl: bool
    timeout: float
    service: str


class RetryConfig(TypedDict, total=False):
    """Configuration for retry logic."""

    max_attempts: int
    initial_delay: float
    max_delay: float
    exponential_base: float
    jitter: bool


class PoolConfig(TypedDict, total=False):
    """Configuration for connection pooling."""

    max_connections: int
    max_keepalive: int
    keepalive_timeout: float
    ttl_dns_cache: int


class MetricsData(TypedDict, total=False):
    """Metrics data structure."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_retries: int
    latency_p50: float
    latency_p95: float
    latency_p99: float
    active_connections: int


@runtime_checkable
class Serializer(Protocol):
    """Protocol for JSON serializers."""

    def loads(self, response: Any) -> Any:
        """
        Deserialize response content to Python objects.

        Args:
            response: Response object with content

        Returns:
            Deserialized Python object
        """
        ...

    def dumps(self, data: Any) -> bytes:
        """
        Serialize Python object to JSON bytes.

        Args:
            data: Python object to serialize

        Returns:
            JSON bytes
        """
        ...

    @property
    def content_types(self) -> tuple[str, ...]:
        """Return supported content types."""
        ...


@runtime_checkable
class Session(Protocol):
    """Protocol for HTTP/SSH sessions."""

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Make an HTTP/SSH request.

        Args:
            method: HTTP method or SSH command
            url: Target URL or path
            params: Query parameters
            data: Request body data
            **kwargs: Additional options

        Returns:
            Response object
        """
        ...

    async def close(self) -> None:
        """Close the session and cleanup resources."""
        ...


@runtime_checkable
class Backend(Protocol):
    """Protocol for Proxmox backends."""

    def get_session(self) -> Session:
        """
        Get or create the session for making requests.

        Returns:
            Session object
        """
        ...

    def get_serializer(self) -> Serializer:
        """
        Get the JSON serializer for this backend.

        Returns:
            Serializer object
        """
        ...

    def get_base_url(self) -> str:
        """
        Get the base URL for API requests.

        Returns:
            Base URL string
        """
        ...

    async def close(self) -> None:
        """Close backend and cleanup resources."""
        ...


@runtime_checkable
class AuthHandler(Protocol):
    """Protocol for authentication handlers."""

    async def __call__(self, request: Any) -> Any:
        """
        Authenticate a request.

        Args:
            request: Request to authenticate

        Returns:
            Authenticated request
        """
        ...

    async def refresh(self) -> None:
        """Refresh authentication credentials if needed."""
        ...


class TaskStatus(TypedDict):
    """Task status information."""

    status: str
    exitstatus: str | None
    upid: str
    type: str
    id: str
    user: str
    node: str
    pid: int
    pstart: int
    starttime: int


class UPIDInfo(TypedDict):
    """Decoded UPID information."""

    node: str
    pid: int
    pstart: int
    starttime: int
    type: str
    id: str
    user: str
    comment: str | None


class FileInfo(TypedDict, total=False):
    """File metadata information."""

    volid: str
    format: str
    size: int
    used: int
    parent: str
    encrypted: bool
    notes: str


class ChecksumData(TypedDict):
    """Checksum information."""

    algorithm: str
    value: str
    hex_size: int


class UploadProgress(TypedDict):
    """Upload progress callback data."""

    bytes_uploaded: int
    total_bytes: int
    percentage: float
    speed_mbps: float


# Type aliases for common patterns
PathSegment = str | int
PathSegments = tuple[PathSegment, ...]
RequestParams = dict[str, Any]
ResponseData = dict[str, Any] | list[Any] | str | int | float | bool | None


__all__ = [
    # Literals
    "ServiceType",
    "BackendType",
    "AuthMethod",
    "HttpMethod",
    # Configs
    "ServiceConfig",
    "BackendConfig",
    "RetryConfig",
    "PoolConfig",
    "MetricsData",
    # Protocols
    "Serializer",
    "Session",
    "Backend",
    "AuthHandler",
    # Data structures
    "TaskStatus",
    "UPIDInfo",
    "FileInfo",
    "ChecksumData",
    "UploadProgress",
    # Type aliases
    "PathSegment",
    "PathSegments",
    "RequestParams",
    "ResponseData",
]
