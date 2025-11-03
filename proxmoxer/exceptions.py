"""
Exception hierarchy for Proxmoxer.

Provides a comprehensive set of exceptions for error handling
with rich context and improved debugging experience.
"""

from typing import Any, Optional


class ProxmoxError(Exception):
    """Base exception for all Proxmoxer errors."""

    def __init__(
        self,
        message: str,
        *,
        context: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        """
        Initialize ProxmoxError.

        Args:
            message: Human-readable error message
            context: Additional context for debugging (optional)
            cause: Original exception that caused this error (optional)
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause

    def __str__(self) -> str:
        """Return formatted error message with context."""
        parts = [self.message]

        if self.context:
            context_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.cause:
            parts.append(f"Caused by: {self.cause}")

        return " | ".join(parts)

    def __repr__(self) -> str:
        """Return detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"context={self.context!r}, "
            f"cause={self.cause!r})"
        )


class ResourceException(ProxmoxError):
    """
    Exception raised when an API resource operation fails.

    Typically indicates HTTP errors or invalid API responses.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        content: Optional[str] = None,
        errors: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ResourceException.

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            content: Response content
            errors: Structured error data from API
            **kwargs: Additional context
        """
        context = {
            "status_code": status_code,
            "content": content,
            "errors": errors,
            **kwargs,
        }
        # Remove None values
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.status_code = status_code
        self.content = content
        self.errors = errors


class AuthenticationError(ProxmoxError):
    """
    Exception raised when authentication fails.

    This can happen during initial login or token refresh.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        auth_method: Optional[str] = None,
        username: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize AuthenticationError.

        Args:
            message: Error message
            auth_method: Authentication method used (e.g., 'password', 'token')
            username: Username that failed authentication
            **kwargs: Additional context
        """
        context = {
            "auth_method": auth_method,
            "username": username,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.auth_method = auth_method
        self.username = username


class ConnectionError(ProxmoxError):
    """
    Exception raised when connection to Proxmox server fails.

    This includes network errors, DNS resolution failures, etc.
    """

    def __init__(
        self,
        message: str = "Connection failed",
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ConnectionError.

        Args:
            message: Error message
            host: Target host
            port: Target port
            **kwargs: Additional context
        """
        context = {
            "host": host,
            "port": port,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.host = host
        self.port = port


class TimeoutError(ProxmoxError):
    """
    Exception raised when an operation times out.

    This can be a connection timeout, read timeout, or operation timeout.
    """

    def __init__(
        self,
        message: str = "Operation timed out",
        *,
        timeout: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize TimeoutError.

        Args:
            message: Error message
            timeout: Timeout value in seconds
            operation: Operation that timed out
            **kwargs: Additional context
        """
        context = {
            "timeout": timeout,
            "operation": operation,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.timeout = timeout
        self.operation = operation


class RetryExhaustedError(ProxmoxError):
    """
    Exception raised when retry attempts are exhausted.

    Wraps the last exception that caused the retry to fail.
    """

    def __init__(
        self,
        message: str = "Maximum retry attempts exhausted",
        *,
        attempts: Optional[int] = None,
        last_error: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize RetryExhaustedError.

        Args:
            message: Error message
            attempts: Number of attempts made
            last_error: Last exception before giving up
            **kwargs: Additional context
        """
        context = {
            "attempts": attempts,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context, cause=last_error)
        self.attempts = attempts
        self.last_error = last_error


class ValidationError(ProxmoxError):
    """
    Exception raised when input validation fails.

    Used for parameter validation, schema validation, etc.
    """

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ValidationError.

        Args:
            message: Error message
            field: Field that failed validation
            value: Invalid value
            **kwargs: Additional context
        """
        context = {
            "field": field,
            "value": value,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.field = field
        self.value = value


class ConfigurationError(ProxmoxError):
    """
    Exception raised when configuration is invalid.

    This includes invalid backend selection, incompatible options, etc.
    """

    def __init__(
        self,
        message: str,
        *,
        option: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize ConfigurationError.

        Args:
            message: Error message
            option: Configuration option that is invalid
            value: Invalid value
            **kwargs: Additional context
        """
        context = {
            "option": option,
            "value": value,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.option = option
        self.value = value


class SerializationError(ProxmoxError):
    """
    Exception raised when JSON serialization/deserialization fails.

    Wraps errors from orjson or json libraries.
    """

    def __init__(
        self,
        message: str,
        *,
        data: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SerializationError.

        Args:
            message: Error message
            data: Data that failed serialization
            **kwargs: Additional context
        """
        context = {
            "data_type": type(data).__name__ if data is not None else None,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.data = data


class SSHError(ProxmoxError):
    """
    Exception raised when SSH operations fail.

    This includes connection failures, command execution errors, etc.
    """

    def __init__(
        self,
        message: str,
        *,
        host: Optional[str] = None,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize SSHError.

        Args:
            message: Error message
            host: SSH host
            exit_code: Command exit code
            stderr: Standard error output
            **kwargs: Additional context
        """
        context = {
            "host": host,
            "exit_code": exit_code,
            "stderr": stderr,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.host = host
        self.exit_code = exit_code
        self.stderr = stderr


class FileOperationError(ProxmoxError):
    """
    Exception raised when file operations fail.

    This includes upload failures, checksum mismatches, etc.
    """

    def __init__(
        self,
        message: str,
        *,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize FileOperationError.

        Args:
            message: Error message
            file_path: Path to file that caused the error
            operation: Operation that failed (upload, download, checksum, etc.)
            **kwargs: Additional context
        """
        context = {
            "file_path": file_path,
            "operation": operation,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.file_path = file_path
        self.operation = operation


class TaskError(ProxmoxError):
    """
    Exception raised when task operations fail.

    This includes task timeout, task failure, invalid UPID, etc.
    """

    def __init__(
        self,
        message: str,
        *,
        upid: Optional[str] = None,
        task_status: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize TaskError.

        Args:
            message: Error message
            upid: Task UPID
            task_status: Final task status
            **kwargs: Additional context
        """
        context = {
            "upid": upid,
            "task_status": task_status,
            **kwargs,
        }
        context = {k: v for k, v in context.items() if v is not None}

        super().__init__(message, context=context)
        self.upid = upid
        self.task_status = task_status


# Export all exceptions
__all__ = [
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
]
