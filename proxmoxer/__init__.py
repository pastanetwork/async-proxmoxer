"""
Proxmoxer - Async Python wrapper for Proxmox REST API.

Modern async/await API for Proxmox Virtual Environment, Proxmox Mail Gateway,
and Proxmox Backup Server.
"""

__author__ = "Oleg Butovich"
__copyright__ = "(c) Oleg Butovich 2013-2025"
__version__ = "3.0.0"
__license__ = "MIT"

# Core API
from .core import ProxmoxAPI, ProxmoxResource, SERVICES

# Exceptions
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    FileOperationError,
    ProxmoxError,
    ResourceException,
    RetryExhaustedError,
    SerializationError,
    SSHError,
    TaskError,
    TimeoutError,
    ValidationError,
)

# Helpers
from .helpers import (
    FirewallManager,
    FirewallRule,
    FirewallRuleAction,
    FirewallRuleType,
    FirewallProtocol,
    FirewallLogLevel,
    FirewallOptions,
    FirewallAlias,
    FirewallIPSet,
    FirewallIPSetEntry,
    FirewallRef,
    FirewallLogEntry,
)

# Retry utilities
from .retry import RetryContext, RetryStrategy, retry_async

# Serializers
from .serializers import JsonSerializer, HAS_ORJSON

__all__ = [
    # Main API
    "ProxmoxAPI",
    "ProxmoxResource",
    "SERVICES",
    # Exceptions
    "ProxmoxError",
    "ResourceException",
    "AuthenticationError",
    "ConnectionError",
    "TimeoutError",
    "RetryExhaustedError",
    "ValidationError",
    "ConfigurationError",
    "SerializationError",
    "SSHError",
    "FileOperationError",
    "TaskError",
    # Helpers
    "FirewallManager",
    "FirewallRule",
    "FirewallRuleAction",
    "FirewallRuleType",
    "FirewallProtocol",
    "FirewallLogLevel",
    "FirewallOptions",
    "FirewallAlias",
    "FirewallIPSet",
    "FirewallIPSetEntry",
    "FirewallRef",
    "FirewallLogEntry",
    # Retry
    "retry_async",
    "RetryStrategy",
    "RetryContext",
    # Serializers
    "JsonSerializer",
    "HAS_ORJSON",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
