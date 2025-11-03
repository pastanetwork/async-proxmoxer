"""
JSON serializers for Proxmoxer.

Provides high-performance JSON parsing with orjson and fallback to
standard library json.
"""
from __future__ import annotations

import logging
from typing import Any

from .exceptions import SerializationError

# Try to import orjson for performance, fallback to standard json
try:
    import orjson

    HAS_ORJSON = True
except ImportError:
    import json

    HAS_ORJSON = False


logger = logging.getLogger(__name__)


class JsonSerializer:
    """
    JSON serializer with orjson support and standard json fallback.

    Uses orjson when available for 3-5x faster parsing, falls back to
    standard library json otherwise.
    """

    def __init__(
        self,
        *,
        extract_data_key: bool = True,
        content_types: tuple[str, ...] | None = None,
    ) -> None:
        """
        Initialize JSON serializer.

        Args:
            extract_data_key: Whether to extract ["data"] key from responses
            content_types: Accepted content types (defaults to common JSON types)
        """
        self.extract_data_key = extract_data_key
        self._content_types = content_types or (
            "application/json",
            "application/json; charset=utf-8",
            "application/json;charset=utf-8",
            "application/json;charset=UTF-8",
        )

        if HAS_ORJSON:
            logger.debug("Using orjson for JSON parsing")
        else:
            logger.debug("orjson not available, using standard json")

    @property
    def content_types(self) -> tuple[str, ...]:
        """Return supported content types."""
        return self._content_types

    def loads(self, response: Any) -> Any:
        """
        Deserialize JSON response to Python objects.

        Args:
            response: Response object with content attribute

        Returns:
            Deserialized Python object

        Raises:
            SerializationError: If JSON parsing fails
        """
        try:
            content = self._get_content(response)

            if not content:
                return None

            # Parse JSON
            if HAS_ORJSON:
                data = orjson.loads(content)
            else:
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                data = json.loads(content)

            # Extract data key if requested
            if self.extract_data_key and isinstance(data, dict):
                return data.get("data", data)

            return data

        except (orjson.JSONDecodeError if HAS_ORJSON else json.JSONDecodeError) as e:
            raise SerializationError(
                f"Failed to parse JSON response: {e}",
                data=content if "content" in locals() else None,
            ) from e
        except Exception as e:
            raise SerializationError(
                f"Unexpected error during deserialization: {e}",
                data=getattr(response, "content", None),
            ) from e

    def dumps(self, data: Any) -> bytes:
        """
        Serialize Python object to JSON bytes.

        Args:
            data: Python object to serialize

        Returns:
            JSON bytes

        Raises:
            SerializationError: If serialization fails
        """
        try:
            if HAS_ORJSON:
                # orjson returns bytes directly
                return orjson.dumps(data)
            else:
                # Standard json returns str, encode to bytes
                return json.dumps(data).encode("utf-8")

        except (TypeError, ValueError) as e:
            raise SerializationError(
                f"Failed to serialize data: {e}",
                data=data,
            ) from e

    def _get_content(self, response: Any) -> bytes | str:
        """
        Extract content from response object.

        Handles different response types (aiohttp, requests, custom).

        Args:
            response: Response object

        Returns:
            Response content as bytes or string
        """
        # Try common response attributes
        if hasattr(response, "content"):
            return response.content
        elif hasattr(response, "text"):
            return response.text
        elif hasattr(response, "read"):
            # File-like object
            return response.read()
        elif isinstance(response, (bytes, str)):
            # Raw content
            return response
        else:
            raise SerializationError(
                f"Unsupported response type: {type(response)}",
                data=response,
            )


class CommandJsonSerializer(JsonSerializer):
    """
    JSON serializer for command-based backends (SSH, local).

    Handles malformed Proxmox CLI output that may contain non-JSON
    text before the actual JSON response.
    """

    def loads(self, response: Any) -> Any:
        """
        Deserialize JSON with workaround for broken pvesh output.

        The Proxmox pvesh command sometimes outputs text before JSON
        (e.g., "trying to acquire lock...OK"). This method strips
        non-JSON lines until valid JSON is found.

        Args:
            response: Response object with content

        Returns:
            Deserialized Python object

        Raises:
            SerializationError: If no valid JSON found
        """
        try:
            content = self._get_content(response)

            if not content:
                return None

            if isinstance(content, bytes):
                content = content.decode("utf-8")

            # Try parsing as-is first
            try:
                if HAS_ORJSON:
                    data = orjson.loads(content)
                else:
                    data = json.loads(content)

                if self.extract_data_key and isinstance(data, dict):
                    return data.get("data", data)
                return data

            except (orjson.JSONDecodeError if HAS_ORJSON else json.JSONDecodeError):
                # Fall through to line-by-line parsing
                pass

            # Strip lines until we find valid JSON
            lines = content.strip().split("\n")

            for i in range(len(lines)):
                attempt = "\n".join(lines[i:])
                try:
                    if HAS_ORJSON:
                        data = orjson.loads(attempt)
                    else:
                        data = json.loads(attempt)

                    if self.extract_data_key and isinstance(data, dict):
                        return data.get("data", data)
                    return data

                except (
                    orjson.JSONDecodeError if HAS_ORJSON else json.JSONDecodeError
                ):
                    continue

            # No valid JSON found
            raise SerializationError(
                "No valid JSON found in command output",
                data=content,
            )

        except SerializationError:
            raise
        except Exception as e:
            raise SerializationError(
                f"Unexpected error during command JSON parsing: {e}",
                data=content if "content" in locals() else None,
            ) from e


class ErrorSerializer(JsonSerializer):
    """
    JSON serializer specialized for error responses.

    Extracts error information from Proxmox API error responses.
    """

    def loads(self, response: Any) -> Any:
        """
        Parse error response and extract error details.

        Args:
            response: Error response object

        Returns:
            Error data with structured information
        """
        try:
            content = self._get_content(response)

            if not content:
                return None

            # Parse JSON
            if HAS_ORJSON:
                data = orjson.loads(content)
            else:
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                data = json.loads(content)

            # Extract error information
            if isinstance(data, dict):
                # Proxmox error format: {"errors": {...}, "data": null}
                if "errors" in data:
                    return data["errors"]
                # Some endpoints return error in data key
                elif "data" in data and data.get("data") is None:
                    return data
                else:
                    return data

            return data

        except Exception:
            # If we can't parse the error as JSON, return raw content
            return {"message": content if "content" in locals() else str(response)}


def get_serializer(
    backend_type: str = "https",
    *,
    extract_data_key: bool = True,
) -> JsonSerializer:
    """
    Factory function to get appropriate serializer for backend type.

    Args:
        backend_type: Type of backend (https, ssh, local)
        extract_data_key: Whether to extract ["data"] key from responses

    Returns:
        Appropriate JsonSerializer instance
    """
    if backend_type in ("ssh", "local"):
        return CommandJsonSerializer(extract_data_key=extract_data_key)
    else:
        return JsonSerializer(extract_data_key=extract_data_key)


__all__ = [
    "JsonSerializer",
    "CommandJsonSerializer",
    "ErrorSerializer",
    "get_serializer",
    "HAS_ORJSON",
]
