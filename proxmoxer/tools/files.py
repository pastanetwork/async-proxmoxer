"""
Async file operations for Proxmoxer.

Provides high-level async API for uploading/downloading files to Proxmox storage
with checksum validation and retry logic.
"""

from __future__ import annotations

__author__ = "John Hollowell"
__copyright__ = "(c) John Hollowell 2023-2025"
__license__ = "MIT"

import hashlib
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import aiofiles
import aiohttp

from ..exceptions import FileOperationError
from ..retry import retry_async
from ..types import ResponseData

CHECKSUM_CHUNK_SIZE = 65536  # 64KB chunks for async reading

logger = logging.getLogger(__name__)


class ChecksumInfo:
    """Checksum algorithm information."""

    def __init__(self, name: str, hex_size: int) -> None:
        """
        Initialize checksum info.

        Args:
            name: Algorithm name
            hex_size: Size of hex digest
        """
        self.name = name
        self.hex_size = hex_size

    def __str__(self) -> str:
        """Return algorithm name."""
        return self.name

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"{self.name} ({self.hex_size} digits)"


class SupportedChecksums(Enum):
    """
    Checksum types supported by Proxmox.

    Ordered by preference (strongest first).
    """

    SHA512 = ChecksumInfo("sha512", 128)
    SHA256 = ChecksumInfo("sha256", 64)
    SHA384 = ChecksumInfo("sha384", 96)
    SHA224 = ChecksumInfo("sha224", 56)
    MD5 = ChecksumInfo("md5", 32)
    SHA1 = ChecksumInfo("sha1", 40)


class Files:
    """
    Async file operations for Proxmox storage.

    Provides methods for uploading/downloading files with checksum validation.
    """

    def __init__(self, prox: Any, node: str, storage: str) -> None:
        """
        Initialize Files helper.

        Args:
            prox: ProxmoxAPI instance
            node: Node name
            storage: Storage name
        """
        self._prox = prox
        self._node = node
        self._storage = storage

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Files ({self._node}/{self._storage} at {self._prox})"

    async def calculate_checksum(
        self,
        file_path: Path,
        algorithm: str = "sha256",
        *,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """
        Calculate file checksum asynchronously.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm name
            progress_callback: Optional callback (bytes_read, total_bytes)

        Returns:
            Hex digest string

        Raises:
            FileOperationError: If calculation fails
        """
        try:
            hasher = hashlib.new(algorithm)
            file_size = file_path.stat().st_size
            bytes_read = 0

            async with aiofiles.open(file_path, "rb") as f:
                while True:
                    chunk = await f.read(CHECKSUM_CHUNK_SIZE)
                    if not chunk:
                        break

                    hasher.update(chunk)
                    bytes_read += len(chunk)

                    if progress_callback:
                        progress_callback(bytes_read, file_size)

            logger.debug(
                f"Calculated {algorithm} checksum for {file_path}: {hasher.hexdigest()}"
            )

            return hasher.hexdigest()

        except Exception as e:
            raise FileOperationError(
                f"Failed to calculate checksum: {e}",
                file_path=str(file_path),
                operation="checksum",
            ) from e

    @retry_async(max_attempts=3, initial_delay=1.0)
    async def upload_local_file_to_storage(
        self,
        filename: str | Path,
        *,
        do_checksum_check: bool = True,
        wait_for_task: bool = True,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ResponseData:
        """
        Upload local file to Proxmox storage.

        Args:
            filename: Path to file
            do_checksum_check: Calculate and verify checksum
            wait_for_task: Wait for upload task to complete
            progress_callback: Optional progress callback

        Returns:
            Task status or UPID

        Raises:
            FileOperationError: If upload fails
        """
        file_path = Path(filename)

        if not file_path.is_file():
            raise FileOperationError(
                f"File does not exist: {file_path}",
                file_path=str(file_path),
                operation="upload",
            )

        checksum = None
        checksum_type = None

        try:
            if do_checksum_check:
                # Find best available checksum algorithm
                for checksum_info in (v.value for v in SupportedChecksums):
                    if checksum_info.name in hashlib.algorithms_available:
                        checksum_type = checksum_info.name
                        break

                if checksum_type is None:
                    logger.warning(
                        "No supported checksum algorithm found, skipping validation"
                    )
                else:
                    # Calculate checksum
                    checksum = await self.calculate_checksum(
                        file_path,
                        checksum_type,
                        progress_callback=progress_callback,
                    )

            # Determine content type
            content_type = "iso" if file_path.suffix.lower() == ".iso" else "vztmpl"

            # Prepare upload parameters
            upload_params: dict[str, Any] = {
                "content": content_type,
            }

            if checksum and checksum_type:
                upload_params["checksum-algorithm"] = checksum_type
                upload_params["checksum"] = checksum

            # Open file for upload
            async with aiofiles.open(file_path, "rb") as f:
                # Read file content
                file_content = await f.read()

                # Upload via API
                logger.info(f"Uploading {file_path.name} to {self._node}/{self._storage}")

                upid = await self._prox.nodes(self._node).storage(self._storage).upload.post(
                    filename=file_content,
                    **upload_params,
                )

            logger.info(f"File uploaded successfully: {upid}")

            # Wait for task completion if requested
            if wait_for_task:
                from .tasks import Tasks

                result = await Tasks.wait_for_task(self._prox, upid)
                return result
            else:
                return await self._prox.nodes(self._node).tasks(upid).status.get()

        except Exception as e:
            raise FileOperationError(
                f"Failed to upload file: {e}",
                file_path=str(file_path),
                operation="upload",
            ) from e

    @retry_async(max_attempts=3, initial_delay=1.0)
    async def download_file_to_storage(
        self,
        url: str,
        *,
        checksum: str | None = None,
        checksum_type: str | None = None,
        wait_for_task: bool = True,
    ) -> ResponseData:
        """
        Download file from URL to Proxmox storage.

        Args:
            url: File URL
            checksum: Optional checksum value
            checksum_type: Optional checksum algorithm
            wait_for_task: Wait for download task completion

        Returns:
            Task status or UPID

        Raises:
            FileOperationError: If download fails
        """
        try:
            # Get file info if available
            file_info = await self.get_file_info(url)
            filename = file_info.get("filename") if file_info else None

            # Auto-discover checksum if not provided
            if checksum is None and checksum_type is None:
                checksum, checksum_info = await self.get_checksums_from_file_url(
                    url, filename
                )
                checksum_type = checksum_info.name if checksum_info else None
            elif checksum is None or checksum_type is None:
                raise FileOperationError(
                    "Must provide both checksum and checksum_type, or neither",
                    file_path=url,
                    operation="download",
                )

            # Prepare download parameters
            download_params: dict[str, Any] = {
                "content": "iso",  # Default to ISO
                "url": url,
            }

            if filename:
                download_params["filename"] = filename

            if checksum and checksum_type:
                download_params["checksum-algorithm"] = checksum_type
                download_params["checksum"] = checksum

            logger.info(f"Downloading {url} to {self._node}/{self._storage}")

            # Trigger download
            upid = await self._prox.nodes(self._node).storage(self._storage).download_url.post(
                **download_params
            )

            logger.info(f"Download started: {upid}")

            # Wait for task if requested
            if wait_for_task:
                from .tasks import Tasks

                result = await Tasks.wait_for_task(self._prox, upid)
                return result
            else:
                return await self._prox.nodes(self._node).tasks(upid).status.get()

        except Exception as e:
            raise FileOperationError(
                f"Failed to download file: {e}",
                file_path=url,
                operation="download",
            ) from e

    async def get_file_info(self, url: str) -> dict[str, Any] | None:
        """
        Get file information from URL (HEAD request).

        Args:
            url: File URL

        Returns:
            File info dictionary or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as resp:
                    if resp.status != 200:
                        return None

                    content_disposition = resp.headers.get("Content-Disposition", "")
                    filename = None

                    # Parse filename from Content-Disposition
                    if "filename=" in content_disposition:
                        filename = content_disposition.split("filename=")[1].strip('"')

                    return {
                        "filename": filename,
                        "content_type": resp.headers.get("Content-Type"),
                        "content_length": resp.headers.get("Content-Length"),
                    }

        except Exception as e:
            logger.warning(f"Failed to get file info for {url}: {e}")
            return None

    async def get_checksums_from_file_url(
        self, url: str, filename: str | None = None
    ) -> tuple[str | None, ChecksumInfo | None]:
        """
        Try to discover checksums from common checksum file URLs.

        Args:
            url: Base file URL
            filename: Optional filename

        Returns:
            Tuple of (checksum, checksum_info) or (None, None)
        """
        # Try common checksum file patterns
        checksum_patterns = [
            ("{base}SHA512SUMS", SupportedChecksums.SHA512.value),
            ("{base}SHA256SUMS", SupportedChecksums.SHA256.value),
            ("{base}.sha512", SupportedChecksums.SHA512.value),
            ("{base}.sha256", SupportedChecksums.SHA256.value),
            ("{base}.md5", SupportedChecksums.MD5.value),
        ]

        base_url = url.rsplit("/", 1)[0] + "/"

        async with aiohttp.ClientSession() as session:
            for pattern, checksum_info in checksum_patterns:
                checksum_url = pattern.format(base=base_url)

                try:
                    async with session.get(checksum_url) as resp:
                        if resp.status == 200:
                            content = await resp.text()

                            # Parse checksum file
                            for line in content.splitlines():
                                if filename and filename in line:
                                    checksum = line.split()[0]
                                    logger.debug(
                                        f"Found {checksum_info.name} checksum: {checksum}"
                                    )
                                    return checksum, checksum_info

                except Exception:
                    continue

        logger.warning(f"Could not find checksum for {url}")
        return None, None


__all__ = [
    "Files",
    "ChecksumInfo",
    "SupportedChecksums",
]
