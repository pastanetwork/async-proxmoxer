"""
Retry logic with exponential backoff for Proxmoxer.

Provides decorators and classes for automatic retry of failed operations
with configurable backoff strategies.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Type, TypeVar

from .exceptions import RetryExhaustedError, TimeoutError
from .types import RetryConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryStrategy:
    """
    Configurable retry strategy with exponential backoff.

    Supports:
    - Exponential backoff with configurable base
    - Maximum delay cap
    - Jitter to prevent thundering herd
    - Retry filtering by exception type
    """

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        initial_delay: float = 0.5,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple[Type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum number of attempts (including initial try)
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter to delays
            retryable_exceptions: Exception types to retry (None = all exceptions)
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if initial_delay < 0:
            raise ValueError("initial_delay must be >= 0")
        if max_delay < initial_delay:
            raise ValueError("max_delay must be >= initial_delay")
        if exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")

        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if the exception should trigger a retry.

        Args:
            exception: The exception that occurred
            attempt: Current attempt number (1-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Check attempt limit
        if attempt >= self.max_attempts:
            return False

        # Check exception type
        if self.retryable_exceptions is not None:
            return isinstance(exception, self.retryable_exceptions)

        # Retry all exceptions by default
        return True

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for the given attempt number.

        Args:
            attempt: Attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            # Add random jitter ±25%
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)

    @classmethod
    def from_config(cls, config: RetryConfig) -> "RetryStrategy":
        """
        Create retry strategy from configuration dict.

        Args:
            config: Retry configuration

        Returns:
            RetryStrategy instance
        """
        return cls(
            max_attempts=config.get("max_attempts", 3),
            initial_delay=config.get("initial_delay", 0.5),
            max_delay=config.get("max_delay", 60.0),
            exponential_base=config.get("exponential_base", 2.0),
            jitter=config.get("jitter", True),
        )


def retry_async(
    *,
    max_attempts: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] | None = None,
    timeout: float | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for automatic retry with exponential backoff.

    Usage:
        @retry_async(max_attempts=5, initial_delay=1.0)
        async def fetch_data():
            ...

    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        retryable_exceptions: Exception types to retry
        timeout: Overall timeout for all attempts (None = no timeout)

    Returns:
        Decorator function
    """
    strategy = RetryStrategy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            last_exception: Exception | None = None
            start_time = asyncio.get_event_loop().time() if timeout else None

            while attempt <= strategy.max_attempts:
                try:
                    # Check timeout
                    if start_time and timeout:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed >= timeout:
                            raise TimeoutError(
                                f"Retry timeout after {elapsed:.2f}s",
                                timeout=timeout,
                                operation=func.__name__,
                            )

                    # Attempt the operation
                    logger.debug(
                        f"Attempting {func.__name__} (attempt {attempt}/{strategy.max_attempts})"
                    )
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not strategy.should_retry(e, attempt):
                        logger.debug(
                            f"{func.__name__} failed, not retrying: {e}",
                            exc_info=True,
                        )
                        raise

                    # Calculate delay
                    delay = strategy.get_delay(attempt)

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{strategy.max_attempts}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    # Wait before retry
                    if delay > 0:
                        await asyncio.sleep(delay)

                    attempt += 1

            # All attempts exhausted
            raise RetryExhaustedError(
                f"Failed after {strategy.max_attempts} attempts",
                attempts=strategy.max_attempts,
                last_error=last_exception,
            )

        return wrapper

    return decorator


class RetryContext:
    """
    Context manager for retry logic with manual control.

    Allows manual retry logic with the same backoff strategy as the decorator.

    Usage:
        async with RetryContext(max_attempts=3) as retry:
            while retry.should_continue():
                try:
                    result = await do_something()
                    retry.success()
                    break
                except Exception as e:
                    if not retry.handle_error(e):
                        raise
                    await retry.wait()
    """

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        initial_delay: float = 0.5,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple[Type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize retry context.

        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
            retryable_exceptions: Exception types to retry
        """
        self.strategy = RetryStrategy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions,
        )
        self.attempt = 0
        self.last_exception: Exception | None = None
        self._success = False

    async def __aenter__(self) -> "RetryContext":
        """Enter context."""
        self.attempt = 1
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Exit context."""
        # Don't suppress exceptions
        return False

    def should_continue(self) -> bool:
        """
        Check if retry should continue.

        Returns:
            True if should continue trying
        """
        return self.attempt <= self.strategy.max_attempts and not self._success

    def handle_error(self, exception: Exception) -> bool:
        """
        Handle an error and determine if retry should occur.

        Args:
            exception: The exception that occurred

        Returns:
            True if should retry, False if should propagate
        """
        self.last_exception = exception
        return self.strategy.should_retry(exception, self.attempt)

    async def wait(self) -> None:
        """Wait before next retry with backoff."""
        delay = self.strategy.get_delay(self.attempt)

        if delay > 0:
            logger.debug(f"Waiting {delay:.2f}s before retry (attempt {self.attempt})")
            await asyncio.sleep(delay)

        self.attempt += 1

    def success(self) -> None:
        """Mark the operation as successful."""
        self._success = True


# Default retry strategies for common scenarios
DEFAULT_STRATEGY = RetryStrategy(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)

AGGRESSIVE_STRATEGY = RetryStrategy(
    max_attempts=5,
    initial_delay=0.1,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

CONSERVATIVE_STRATEGY = RetryStrategy(
    max_attempts=2,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=False,
)


__all__ = [
    "RetryStrategy",
    "retry_async",
    "RetryContext",
    "DEFAULT_STRATEGY",
    "AGGRESSIVE_STRATEGY",
    "CONSERVATIVE_STRATEGY",
]
