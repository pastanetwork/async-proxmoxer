"""
Disk management helpers for Proxmoxer.

Provides high-level async API for managing disks on Proxmox nodes,
including LVM, LVM-thin, ZFS, and directory storage initialization.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class DiskType(str, Enum):
    """Disk types."""

    HDD = "hdd"
    SSD = "ssd"
    UNKNOWN = "unknown"


@dataclass
class Disk:
    """Physical disk information."""

    devpath: str
    model: str | None = None
    size: int = 0
    serial: str | None = None
    vendor: str | None = None
    wwn: str | None = None
    health: str | None = None
    type: str | None = None
    rpm: int | None = None
    wearout: int | None = None
    used: str | None = None
    # Ceph OSD fields
    osdid: int | None = None
    osdid_list: list[int] | None = None
    # Mounting and partitioning
    mounted: bool | None = None
    parent: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Disk:
        """Create Disk from API response."""
        return cls(
            devpath=data.get("devpath", ""),
            model=data.get("model"),
            size=data.get("size", 0),
            serial=data.get("serial"),
            vendor=data.get("vendor"),
            wwn=data.get("wwn"),
            health=data.get("health"),
            type=data.get("type"),
            rpm=data.get("rpm"),
            wearout=data.get("wearout"),
            used=data.get("used"),
            osdid=data.get("osdid"),
            osdid_list=data.get("osdid-list") if isinstance(data.get("osdid-list"), list) else None,
            mounted=bool(data.get("mounted", 0)) if data.get("mounted") is not None else None,
            parent=data.get("parent"),
        )


@dataclass
class SMARTInfo:
    """SMART disk information."""

    health: str
    type: str | None = None
    attributes: list[dict[str, Any]] | None = None
    text: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SMARTInfo:
        """Create SMARTInfo from API response."""
        return cls(
            health=data.get("health", "UNKNOWN"),
            type=data.get("type"),
            attributes=data.get("attributes"),
            text=data.get("text"),
        )


@dataclass
class LVMInfo:
    """LVM volume group information."""

    vg: str
    size: int
    free: int
    children: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LVMInfo:
        """Create LVMInfo from API response."""
        return cls(
            vg=data.get("vg", data.get("name", "")),
            size=data.get("size", 0),
            free=data.get("free", 0),
            children=data.get("children"),
        )


@dataclass
class ZFSInfo:
    """ZFS pool information."""

    name: str
    size: int
    free: int
    alloc: int
    frag: int | None = None
    dedup: float | None = None
    health: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ZFSInfo:
        """Create ZFSInfo from API response."""
        return cls(
            name=data.get("name", ""),
            size=data.get("size", 0),
            free=data.get("free", 0),
            alloc=data.get("alloc", 0),
            frag=data.get("frag"),
            dedup=data.get("dedup"),
            health=data.get("health"),
        )


@dataclass
class DirectoryInfo:
    """Directory storage information."""

    path: str
    device: str | None = None
    options: str | None = None
    type: str | None = None
    unitfile: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DirectoryInfo:
        """Create DirectoryInfo from API response."""
        return cls(
            path=data.get("path", ""),
            device=data.get("device"),
            options=data.get("options"),
            type=data.get("type"),
            unitfile=data.get("unitfile"),
        )


class DiskManager:
    """
    High-level manager for disk operations on a Proxmox node.

    Provides methods for listing disks, checking SMART status,
    and creating LVM, LVM-thin, ZFS, and directory storage.

    Example:
        >>> disks = DiskManager(proxmox, "pve-node1")
        >>> available = await disks.list_disks(include_partitions=False)
        >>> smart = await disks.get_smart_info("/dev/sda")
        >>> await disks.create_lvm("vg_data", "/dev/sdb")
        >>> await disks.create_zfs("rpool", "/dev/sdc", raidlevel="single")
    """

    def __init__(self, proxmox: Any, node: str):
        """
        Initialize DiskManager.

        Args:
            proxmox: Proxmoxer instance
            node: Node name
        """
        self.proxmox = proxmox
        self.node = node
        self._disks_api = proxmox.nodes(node).disks

    # Disk Listing
    async def list_disks(
        self,
        include_partitions: bool = False,
        skipsmart: bool = False,
        disk_type: DiskType | str | None = None,
    ) -> list[Disk]:
        """
        List physical disks.

        Args:
            include_partitions: Include partitions
            skipsmart: Skip SMART detection
            disk_type: Filter by disk type (hdd, ssd)

        Returns:
            List of Disk objects
        """
        params = {}
        if include_partitions:
            params["include-partitions"] = 1
        if skipsmart:
            params["skipsmart"] = 1
        if disk_type:
            if isinstance(disk_type, DiskType):
                params["type"] = disk_type.value
            else:
                params["type"] = disk_type

        data: ResponseData = await self._disks_api.list.get(**params)
        return [Disk.from_dict(d) for d in data]

    async def get_smart_info(self, disk: str, healthonly: bool = False) -> SMARTInfo:
        """
        Get SMART information for a disk.

        Args:
            disk: Disk path (e.g., "/dev/sda")
            healthonly: Only return health status

        Returns:
            SMARTInfo object
        """
        params = {"disk": disk}
        if healthonly:
            params["healthonly"] = 1

        data: ResponseData = await self._disks_api.smart.get(**params)
        return SMARTInfo.from_dict(data)

    async def wipe_disk(self, disk: str) -> str:
        """
        Wipe a disk.

        Args:
            disk: Disk path

        Returns:
            Task ID (UPID)
        """
        return await self._disks_api.wipedisk.put(disk=disk)

    # LVM Management
    async def list_lvm(self) -> list[LVMInfo]:
        """
        List LVM volume groups.

        Returns:
            List of LVMInfo objects
        """
        data: ResponseData = await self._disks_api.lvm.get()
        return [LVMInfo.from_dict(vg) for vg in data]

    async def create_lvm(
        self,
        name: str,
        device: str,
        add_storage: bool = True,
    ) -> str:
        """
        Create LVM volume group.

        Args:
            name: Volume group name
            device: Device path
            add_storage: Automatically add as Proxmox storage

        Returns:
            Success message
        """
        params = {"name": name, "device": device}
        if add_storage:
            params["add_storage"] = 1

        return await self._disks_api.lvm.post(**params)

    async def delete_lvm(self, name: str, cleanup_disks: bool = False) -> None:
        """
        Delete LVM volume group.

        Args:
            name: Volume group name
            cleanup_disks: Cleanup disks
        """
        params = {"name": name}
        if cleanup_disks:
            params["cleanup-disks"] = 1

        await self._disks_api.lvm(name).delete(**params)

    # LVM-Thin Management
    async def list_lvmthin(self) -> list[dict[str, Any]]:
        """
        List LVM thin pools.

        Returns:
            List of LVM thin pool dicts
        """
        return await self._disks_api.lvmthin.get()

    async def create_lvmthin(
        self,
        name: str,
        device: str,
        add_storage: bool = True,
    ) -> str:
        """
        Create LVM-thin pool.

        Args:
            name: Pool name
            device: Device path
            add_storage: Automatically add as Proxmox storage

        Returns:
            Success message
        """
        params = {"name": name, "device": device}
        if add_storage:
            params["add_storage"] = 1

        return await self._disks_api.lvmthin.post(**params)

    async def delete_lvmthin(
        self, name: str, volume_group: str, cleanup_disks: bool = False
    ) -> None:
        """
        Delete LVM-thin pool.

        Args:
            name: Pool name
            volume_group: Volume group name
            cleanup_disks: Cleanup disks
        """
        params = {"volume-group": volume_group}
        if cleanup_disks:
            params["cleanup-disks"] = 1

        await self._disks_api.lvmthin(name).delete(**params)

    # ZFS Management
    async def list_zfs(self) -> list[ZFSInfo]:
        """
        List ZFS pools.

        Returns:
            List of ZFSInfo objects
        """
        data: ResponseData = await self._disks_api.zfs.get()
        return [ZFSInfo.from_dict(pool) for pool in data]

    async def get_zfs(self, name: str) -> ZFSInfo:
        """
        Get ZFS pool details.

        Args:
            name: Pool name

        Returns:
            ZFSInfo object
        """
        data: ResponseData = await self._disks_api.zfs(name).get()
        return ZFSInfo.from_dict(data)

    async def create_zfs(
        self,
        name: str,
        devices: str,
        raidlevel: str = "single",
        ashift: int = 12,
        compression: str | None = None,
        add_storage: bool = True,
    ) -> str:
        """
        Create ZFS pool.

        Args:
            name: Pool name
            devices: Comma-separated device paths
            raidlevel: RAID level (single, mirror, raidz, raidz2, raidz3)
            ashift: Pool sector size exponent (12 = 4KB sectors)
            compression: Compression algorithm (on, off, lzjb, lz4, zle, gzip)
            add_storage: Automatically add as Proxmox storage

        Returns:
            Success message
        """
        params = {
            "name": name,
            "devices": devices,
            "raidlevel": raidlevel,
            "ashift": ashift,
        }
        if compression:
            params["compression"] = compression
        if add_storage:
            params["add_storage"] = 1

        return await self._disks_api.zfs.post(**params)

    async def delete_zfs(self, name: str, cleanup_disks: bool = False) -> None:
        """
        Delete ZFS pool.

        Args:
            name: Pool name
            cleanup_disks: Cleanup disks
        """
        params = {}
        if cleanup_disks:
            params["cleanup-disks"] = 1

        await self._disks_api.zfs(name).delete(**params)

    # Directory Management
    async def list_directories(self) -> list[DirectoryInfo]:
        """
        List mounted directories usable for storage.

        Returns:
            List of DirectoryInfo objects
        """
        data: ResponseData = await self._disks_api.directory.get()
        return [DirectoryInfo.from_dict(d) for d in data]

    async def create_directory(
        self,
        name: str,
        device: str,
        filesystem: str = "ext4",
        add_storage: bool = True,
    ) -> str:
        """
        Create directory storage by mounting a device.

        Args:
            name: Directory name/path
            device: Block device to format and mount
            filesystem: Filesystem type (ext4, xfs)
            add_storage: Automatically add as Proxmox storage

        Returns:
            Success message
        """
        params = {"name": name, "device": device, "filesystem": filesystem}
        if add_storage:
            params["add_storage"] = 1

        return await self._disks_api.directory.post(**params)

    async def delete_directory(self, name: str, cleanup_disks: bool = False) -> None:
        """
        Delete directory storage.

        Args:
            name: Directory name
            cleanup_disks: Cleanup disks
        """
        params = {}
        if cleanup_disks:
            params["cleanup-disks"] = 1

        await self._disks_api.directory(name).delete(**params)

    # Helper Methods
    async def get_unused_disks(
        self,
        include_partitions: bool = False,
        disk_type: DiskType | str | None = None,
    ) -> list[Disk]:
        """
        Get list of unused (unpartitioned) disks.

        Args:
            include_partitions: Include partitions
            disk_type: Filter by disk type

        Returns:
            List of unused Disk objects
        """
        all_disks = await self.list_disks(
            include_partitions=include_partitions, disk_type=disk_type
        )
        return [d for d in all_disks if not d.used or d.used == ""]

    async def get_disk_by_serial(self, serial: str) -> Disk | None:
        """
        Find disk by serial number.

        Args:
            serial: Serial number

        Returns:
            Disk object or None if not found
        """
        disks = await self.list_disks()
        for disk in disks:
            if disk.serial == serial:
                return disk
        return None

    async def get_disks_by_type(self, disk_type: DiskType | str) -> list[Disk]:
        """
        Get disks by type.

        Args:
            disk_type: Disk type (hdd, ssd)

        Returns:
            List of Disk objects
        """
        return await self.list_disks(disk_type=disk_type)

    async def check_disk_health(self, disk: str) -> str:
        """
        Quick health check for a disk.

        Args:
            disk: Disk path

        Returns:
            Health status string (PASSED, FAILED, etc.)
        """
        smart = await self.get_smart_info(disk, healthonly=True)
        return smart.health
