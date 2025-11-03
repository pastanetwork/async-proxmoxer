"""
Storage management helpers for Proxmoxer.

Provides high-level async API for managing Proxmox storage configuration.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class StorageType(str, Enum):
    """Storage backend types."""

    DIR = "dir"
    NFS = "nfs"
    CIFS = "cifs"
    LVM = "lvm"
    LVMTHIN = "lvmthin"
    ZFS = "zfspool"
    CEPH_RBD = "rbd"
    CEPH_FS = "cephfs"
    ISCSI = "iscsi"
    ISCSIDIRECT = "iscsidirect"
    GLUSTERFS = "glusterfs"
    PBS = "pbs"
    BTRFS = "btrfs"


class ContentType(str, Enum):
    """Storage content types."""

    IMAGES = "images"
    ROOTDIR = "rootdir"
    ISO = "iso"
    VZTMPL = "vztmpl"
    BACKUP = "backup"
    SNIPPETS = "snippets"


@dataclass
class Storage:
    """Storage configuration."""

    storage: str
    type: str
    content: str | None = None
    enabled: bool = True
    shared: bool = False
    nodes: str | None = None
    path: str | None = None
    server: str | None = None
    export: str | None = None
    pool: str | None = None
    username: str | None = None
    maxfiles: int | None = None
    prune_backups: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Storage:
        """Create Storage from API response."""
        return cls(
            storage=data["storage"],
            type=data["type"],
            content=data.get("content"),
            enabled=bool(data.get("disable", 0) == 0),
            shared=bool(data.get("shared", 0)),
            nodes=data.get("nodes"),
            path=data.get("path"),
            server=data.get("server"),
            export=data.get("export"),
            pool=data.get("pool"),
            username=data.get("username"),
            maxfiles=data.get("maxfiles"),
            prune_backups=data.get("prune-backups"),
        )


class StorageManager:
    """
    High-level manager for Proxmox storage configuration.

    Provides methods for managing storage backends like NFS, CIFS,
    LVM, ZFS, Ceph, and more.

    Example:
        >>> storage_mgr = StorageManager(proxmox)
        >>> storages = await storage_mgr.list_storage()
        >>> await storage_mgr.create_nfs_storage(
        ...     storage="nfs-backup",
        ...     server="192.168.1.100",
        ...     export="/mnt/backup",
        ...     content=["backup", "iso"]
        ... )
        >>> await storage_mgr.update_storage("nfs-backup", enabled=False)
    """

    def __init__(self, proxmox: Any):
        """
        Initialize StorageManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    async def list_storage(self, type: StorageType | str | None = None) -> list[Storage]:
        """
        List all storage configurations.

        Args:
            type: Filter by storage type

        Returns:
            List of Storage objects
        """
        params = {}
        if type:
            if isinstance(type, StorageType):
                params["type"] = type.value
            else:
                params["type"] = type

        data: ResponseData = await self.proxmox.storage.get(**params)
        return [Storage.from_dict(s) for s in data]

    async def get_storage(self, storage: str) -> Storage:
        """
        Get storage configuration.

        Args:
            storage: Storage ID

        Returns:
            Storage object
        """
        data: ResponseData = await self.proxmox.storage(storage).get()
        data["storage"] = storage
        return Storage.from_dict(data)

    async def create_storage(
        self,
        storage: str,
        type: StorageType | str,
        **config: Any,
    ) -> None:
        """
        Create storage configuration (generic).

        Args:
            storage: Storage ID
            type: Storage type
            **config: Storage-specific configuration parameters
        """
        params = {"storage": storage}
        if isinstance(type, StorageType):
            params["type"] = type.value
        else:
            params["type"] = type

        params.update(config)
        await self.proxmox.storage.post(**params)

    async def create_nfs_storage(
        self,
        storage: str,
        server: str,
        export: str,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        maxfiles: int | None = None,
        prune_backups: str | None = None,
        options: str | None = None,
    ) -> None:
        """
        Create NFS storage.

        Args:
            storage: Storage ID
            server: NFS server hostname or IP
            export: NFS export path
            content: Content types (backup, iso, vztmpl, etc.)
            nodes: Comma-separated list of nodes
            maxfiles: Maximum backup files
            prune_backups: Prune settings
            options: NFS mount options
        """
        params = {
            "storage": storage,
            "type": "nfs",
            "server": server,
            "export": export,
        }
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if maxfiles:
            params["maxfiles"] = maxfiles
        if prune_backups:
            params["prune-backups"] = prune_backups
        if options:
            params["options"] = options

        await self.proxmox.storage.post(**params)

    async def create_cifs_storage(
        self,
        storage: str,
        server: str,
        share: str,
        username: str | None = None,
        password: str | None = None,
        domain: str | None = None,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        maxfiles: int | None = None,
        prune_backups: str | None = None,
    ) -> None:
        """
        Create CIFS/SMB storage.

        Args:
            storage: Storage ID
            server: CIFS server hostname or IP
            share: Share name
            username: Username
            password: Password
            domain: Domain
            content: Content types
            nodes: Comma-separated list of nodes
            maxfiles: Maximum backup files
            prune_backups: Prune settings
        """
        params = {
            "storage": storage,
            "type": "cifs",
            "server": server,
            "share": share,
        }
        if username:
            params["username"] = username
        if password:
            params["password"] = password
        if domain:
            params["domain"] = domain
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if maxfiles:
            params["maxfiles"] = maxfiles
        if prune_backups:
            params["prune-backups"] = prune_backups

        await self.proxmox.storage.post(**params)

    async def create_dir_storage(
        self,
        storage: str,
        path: str,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        maxfiles: int | None = None,
        prune_backups: str | None = None,
        shared: bool = False,
    ) -> None:
        """
        Create directory storage.

        Args:
            storage: Storage ID
            path: Directory path
            content: Content types
            nodes: Comma-separated list of nodes
            maxfiles: Maximum backup files
            prune_backups: Prune settings
            shared: Shared storage
        """
        params = {"storage": storage, "type": "dir", "path": path}
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if maxfiles:
            params["maxfiles"] = maxfiles
        if prune_backups:
            params["prune-backups"] = prune_backups
        if shared:
            params["shared"] = 1

        await self.proxmox.storage.post(**params)

    async def create_lvm_storage(
        self,
        storage: str,
        vgname: str,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        shared: bool = False,
    ) -> None:
        """
        Create LVM storage.

        Args:
            storage: Storage ID
            vgname: LVM volume group name
            content: Content types (typically "images" and "rootdir")
            nodes: Comma-separated list of nodes
            shared: Shared storage
        """
        params = {"storage": storage, "type": "lvm", "vgname": vgname}
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if shared:
            params["shared"] = 1

        await self.proxmox.storage.post(**params)

    async def create_lvmthin_storage(
        self,
        storage: str,
        vgname: str,
        thinpool: str,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
    ) -> None:
        """
        Create LVM-thin storage.

        Args:
            storage: Storage ID
            vgname: LVM volume group name
            thinpool: LVM thin pool name
            content: Content types
            nodes: Comma-separated list of nodes
        """
        params = {
            "storage": storage,
            "type": "lvmthin",
            "vgname": vgname,
            "thinpool": thinpool,
        }
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes

        await self.proxmox.storage.post(**params)

    async def create_zfs_storage(
        self,
        storage: str,
        pool: str,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        sparse: bool = False,
        blocksize: str | None = None,
    ) -> None:
        """
        Create ZFS storage.

        Args:
            storage: Storage ID
            pool: ZFS pool name
            content: Content types
            nodes: Comma-separated list of nodes
            sparse: Use sparse volumes
            blocksize: Block size (4k, 8k, 16k, etc.)
        """
        params = {"storage": storage, "type": "zfspool", "pool": pool}
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if sparse:
            params["sparse"] = 1
        if blocksize:
            params["blocksize"] = blocksize

        await self.proxmox.storage.post(**params)

    async def create_ceph_rbd_storage(
        self,
        storage: str,
        pool: str,
        monhost: str,
        username: str | None = None,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        krbd: bool = False,
    ) -> None:
        """
        Create Ceph RBD storage.

        Args:
            storage: Storage ID
            pool: Ceph pool name
            monhost: Monitor hosts (comma-separated)
            username: Ceph username
            content: Content types
            nodes: Comma-separated list of nodes
            krbd: Use krbd (kernel RBD)
        """
        params = {
            "storage": storage,
            "type": "rbd",
            "pool": pool,
            "monhost": monhost,
        }
        if username:
            params["username"] = username
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if krbd:
            params["krbd"] = 1

        await self.proxmox.storage.post(**params)

    async def create_pbs_storage(
        self,
        storage: str,
        server: str,
        datastore: str,
        username: str,
        password: str | None = None,
        fingerprint: str | None = None,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        maxfiles: int | None = None,
        prune_backups: str | None = None,
    ) -> None:
        """
        Create Proxmox Backup Server storage.

        Args:
            storage: Storage ID
            server: PBS server hostname or IP
            datastore: PBS datastore name
            username: PBS username
            password: PBS password
            fingerprint: PBS server fingerprint
            content: Content types (typically "backup")
            nodes: Comma-separated list of nodes
            maxfiles: Maximum backup files
            prune_backups: Prune settings
        """
        params = {
            "storage": storage,
            "type": "pbs",
            "server": server,
            "datastore": datastore,
            "username": username,
        }
        if password:
            params["password"] = password
        if fingerprint:
            params["fingerprint"] = fingerprint
        if content:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes:
            params["nodes"] = nodes
        if maxfiles:
            params["maxfiles"] = maxfiles
        if prune_backups:
            params["prune-backups"] = prune_backups

        await self.proxmox.storage.post(**params)

    async def update_storage(
        self,
        storage: str,
        enabled: bool | None = None,
        content: list[str | ContentType] | None = None,
        nodes: str | None = None,
        maxfiles: int | None = None,
        prune_backups: str | None = None,
        delete: str | None = None,
        **other_config: Any,
    ) -> None:
        """
        Update storage configuration.

        Args:
            storage: Storage ID
            enabled: Enable/disable storage
            content: Content types
            nodes: Node list
            maxfiles: Maximum backup files
            prune_backups: Prune settings
            delete: List of settings to delete
            **other_config: Other storage-specific parameters
        """
        params = {}
        if enabled is not None:
            params["disable"] = 0 if enabled else 1
        if content is not None:
            content_str = ",".join(
                [c.value if isinstance(c, ContentType) else c for c in content]
            )
            params["content"] = content_str
        if nodes is not None:
            params["nodes"] = nodes
        if maxfiles is not None:
            params["maxfiles"] = maxfiles
        if prune_backups is not None:
            params["prune-backups"] = prune_backups
        if delete:
            params["delete"] = delete

        params.update(other_config)
        await self.proxmox.storage(storage).put(**params)

    async def delete_storage(self, storage: str) -> None:
        """
        Delete storage configuration.

        Args:
            storage: Storage ID to delete
        """
        await self.proxmox.storage(storage).delete()

    async def enable_storage(self, storage: str) -> None:
        """
        Enable storage.

        Args:
            storage: Storage ID
        """
        await self.update_storage(storage, enabled=True)

    async def disable_storage(self, storage: str) -> None:
        """
        Disable storage.

        Args:
            storage: Storage ID
        """
        await self.update_storage(storage, enabled=False)
