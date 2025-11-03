"""
Cluster management helpers for Proxmoxer.

Provides high-level async API for managing Proxmox cluster operations,
including HA, backup, ACME, SDN, and notifications.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class HAState(str, Enum):
    """HA resource state."""

    STARTED = "started"
    STOPPED = "stopped"
    ENABLED = "enabled"
    DISABLED = "disabled"
    IGNORED = "ignored"


class BackupMode(str, Enum):
    """Backup mode."""

    SNAPSHOT = "snapshot"
    SUSPEND = "suspend"
    STOP = "stop"


class BackupCompression(str, Enum):
    """Backup compression type."""

    NONE = "0"
    LZOP = "lzo"
    GZIP = "gzip"
    ZSTD = "zstd"


@dataclass
class ClusterStatus:
    """Cluster status information."""

    name: str
    nodes: int
    quorate: bool
    version: int
    # Node-specific fields (when type='node')
    ip: str | None = None
    level: str | None = None
    local: bool | None = None
    nodeid: int | None = None
    online: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClusterStatus:
        """Create ClusterStatus from API response."""
        return cls(
            name=data.get("name", ""),
            nodes=data.get("nodes", 0),
            quorate=bool(data.get("quorate", 0)),
            version=data.get("version", 0),
            ip=data.get("ip"),
            level=data.get("level"),
            local=bool(data.get("local", 0)) if data.get("local") is not None else None,
            nodeid=data.get("nodeid"),
            online=bool(data.get("online", 0)) if data.get("online") is not None else None,
        )


@dataclass
class ClusterResource:
    """Cluster resource entry."""

    id: str
    type: str
    status: str | None = None
    node: str | None = None
    cpu: float | None = None
    maxcpu: int | None = None
    mem: int | None = None
    maxmem: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    name: str | None = None
    uptime: int | None = None
    # Node-specific fields
    cgroup_mode: int | None = None
    level: str | None = None
    # Storage-specific fields
    content: str | None = None
    plugintype: str | None = None
    storage: str | None = None
    # VM/Container-specific fields
    diskread: int | None = None
    diskwrite: int | None = None
    hastate: str | None = None
    lock: str | None = None
    memhost: int | None = None
    netin: int | None = None
    netout: int | None = None
    pool: str | None = None
    tags: str | None = None
    template: bool | None = None
    vmid: int | None = None
    # Pressure metrics
    pressurecpufull: float | None = None
    pressurecpusome: float | None = None
    pressureiofull: float | None = None
    pressureiosome: float | None = None
    pressurememoryfull: float | None = None
    pressurememorysome: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ClusterResource:
        """Create ClusterResource from API response."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", ""),
            status=data.get("status"),
            node=data.get("node"),
            cpu=data.get("cpu"),
            maxcpu=data.get("maxcpu"),
            mem=data.get("mem"),
            maxmem=data.get("maxmem"),
            disk=data.get("disk"),
            maxdisk=data.get("maxdisk"),
            name=data.get("name"),
            uptime=data.get("uptime"),
            # Node-specific fields
            cgroup_mode=data.get("cgroup-mode"),
            level=data.get("level"),
            # Storage-specific fields
            content=data.get("content"),
            plugintype=data.get("plugintype"),
            storage=data.get("storage"),
            # VM/Container-specific fields
            diskread=data.get("diskread"),
            diskwrite=data.get("diskwrite"),
            hastate=data.get("hastate"),
            lock=data.get("lock"),
            memhost=data.get("memhost"),
            netin=data.get("netin"),
            netout=data.get("netout"),
            pool=data.get("pool"),
            tags=data.get("tags"),
            template=bool(data.get("template", 0)) if data.get("template") is not None else None,
            vmid=data.get("vmid"),
            # Pressure metrics
            pressurecpufull=data.get("pressurecpufull"),
            pressurecpusome=data.get("pressurecpusome"),
            pressureiofull=data.get("pressureiofull"),
            pressureiosome=data.get("pressureiosome"),
            pressurememoryfull=data.get("pressurememoryfull"),
            pressurememorysome=data.get("pressurememorysome"),
        )


@dataclass
class HAResource:
    """High Availability resource."""

    sid: str
    state: str
    group: str | None = None
    max_restart: int = 1
    max_relocate: int = 1
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HAResource:
        """Create HAResource from API response."""
        return cls(
            sid=data["sid"],
            state=data.get("state", "started"),
            group=data.get("group"),
            max_restart=data.get("max_restart", 1),
            max_relocate=data.get("max_relocate", 1),
            comment=data.get("comment"),
        )


@dataclass
class HAGroup:
    """High Availability group."""

    group: str
    nodes: str
    nofailback: bool = False
    restricted: bool = False
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HAGroup:
        """Create HAGroup from API response."""
        return cls(
            group=data["group"],
            nodes=data["nodes"],
            nofailback=bool(data.get("nofailback", 0)),
            restricted=bool(data.get("restricted", 0)),
            comment=data.get("comment"),
        )


@dataclass
class BackupJob:
    """Backup job configuration."""

    id: str
    enabled: bool
    schedule: str
    storage: str
    vmid: str | None = None
    node: str | None = None
    all: bool = False
    mode: str = "snapshot"
    compress: str = "zstd"
    mailnotification: str = "always"
    mailto: str | None = None
    prune_backups: str | None = None
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackupJob:
        """Create BackupJob from API response."""
        return cls(
            id=data["id"],
            enabled=bool(data.get("enabled", 1)),
            schedule=data.get("schedule", ""),
            storage=data.get("storage", ""),
            vmid=data.get("vmid"),
            node=data.get("node"),
            all=bool(data.get("all", 0)),
            mode=data.get("mode", "snapshot"),
            compress=data.get("compress", "zstd"),
            mailnotification=data.get("mailnotification", "always"),
            mailto=data.get("mailto"),
            prune_backups=data.get("prune-backups"),
            comment=data.get("comment"),
        )


@dataclass
class ReplicationJob:
    """Replication job configuration."""

    id: str
    type: str
    target: str
    guest: int
    rate: float | None = None
    schedule: str = "*/15"
    source: str | None = None
    comment: str | None = None
    disable: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReplicationJob:
        """Create ReplicationJob from API response."""
        return cls(
            id=data["id"],
            type=data.get("type", "local"),
            target=data["target"],
            guest=data["guest"],
            rate=data.get("rate"),
            schedule=data.get("schedule", "*/15"),
            source=data.get("source"),
            comment=data.get("comment"),
            disable=bool(data.get("disable", 0)),
        )


@dataclass
class ACMEAccount:
    """ACME account."""

    name: str
    email: str
    directory: str
    tos_url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ACMEAccount:
        """Create ACMEAccount from API response."""
        return cls(
            name=data.get("name", ""),
            email=data.get("email", ""),
            directory=data.get("directory", ""),
            tos_url=data.get("tos_url"),
        )


class ClusterManager:
    """
    High-level manager for Proxmox cluster operations.

    Provides methods for managing cluster status, resources, HA,
    backups, replication, and ACME certificates.

    Example:
        >>> cluster = ClusterManager(proxmox)
        >>> status = await cluster.get_status()
        >>> resources = await cluster.list_resources(type="vm")
        >>> await cluster.create_ha_resource("vm:100", group="production")
    """

    def __init__(self, proxmox: Any):
        """
        Initialize ClusterManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    # Cluster Status
    async def get_status(self) -> list[dict[str, Any]]:
        """
        Get cluster status.

        Returns:
            List of cluster status entries (one per node)
        """
        return await self.proxmox.cluster.status.get()

    async def list_resources(
        self, type: str | None = None
    ) -> list[ClusterResource]:
        """
        Get cluster resources.

        Args:
            type: Resource type filter (node, vm, storage, pool)

        Returns:
            List of ClusterResource objects
        """
        params = {}
        if type:
            params["type"] = type

        data: ResponseData = await self.proxmox.cluster.resources.get(**params)
        return [ClusterResource.from_dict(r) for r in data]

    async def get_next_vmid(self, vmid: int | None = None) -> int:
        """
        Get next free VMID.

        Args:
            vmid: Verify if this VMID is free (optional)

        Returns:
            Next free VMID
        """
        params = {}
        if vmid:
            params["vmid"] = vmid

        result = await self.proxmox.cluster.nextid.get(**params)
        return int(result)

    # High Availability
    async def list_ha_resources(self) -> list[HAResource]:
        """
        List HA resources.

        Returns:
            List of HAResource objects
        """
        data: ResponseData = await self.proxmox.cluster.ha.resources.get()
        return [HAResource.from_dict(r) for r in data]

    async def get_ha_resource(self, sid: str) -> HAResource:
        """
        Get HA resource details.

        Args:
            sid: Resource ID (e.g., "vm:100")

        Returns:
            HAResource object
        """
        data: ResponseData = await self.proxmox.cluster.ha.resources(sid).get()
        return HAResource.from_dict(data)

    async def create_ha_resource(
        self,
        sid: str,
        state: str | HAState = HAState.STARTED,
        group: str | None = None,
        max_restart: int = 1,
        max_relocate: int = 1,
        comment: str | None = None,
    ) -> None:
        """
        Create HA resource.

        Args:
            sid: Resource ID (e.g., "vm:100" or "ct:101")
            state: Initial state
            group: HA group name
            max_restart: Maximum restart attempts
            max_relocate: Maximum relocate attempts
            comment: Comment
        """
        params = {"sid": sid}
        if isinstance(state, HAState):
            params["state"] = state.value
        else:
            params["state"] = state
        if group:
            params["group"] = group
        if max_restart != 1:
            params["max_restart"] = max_restart
        if max_relocate != 1:
            params["max_relocate"] = max_relocate
        if comment:
            params["comment"] = comment

        await self.proxmox.cluster.ha.resources.post(**params)

    async def update_ha_resource(
        self,
        sid: str,
        state: str | HAState | None = None,
        group: str | None = None,
        max_restart: int | None = None,
        max_relocate: int | None = None,
        comment: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update HA resource.

        Args:
            sid: Resource ID
            state: New state
            group: HA group name
            max_restart: Maximum restart attempts
            max_relocate: Maximum relocate attempts
            comment: Comment
            delete: List of settings to delete
        """
        params = {}
        if state is not None:
            if isinstance(state, HAState):
                params["state"] = state.value
            else:
                params["state"] = state
        if group is not None:
            params["group"] = group
        if max_restart is not None:
            params["max_restart"] = max_restart
        if max_relocate is not None:
            params["max_relocate"] = max_relocate
        if comment is not None:
            params["comment"] = comment
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.ha.resources(sid).put(**params)

    async def delete_ha_resource(self, sid: str) -> None:
        """
        Delete HA resource.

        Args:
            sid: Resource ID
        """
        await self.proxmox.cluster.ha.resources(sid).delete()

    async def migrate_ha_resource(self, sid: str, node: str) -> None:
        """
        Migrate HA resource to another node.

        Args:
            sid: Resource ID
            node: Target node
        """
        await self.proxmox.cluster.ha.resources(sid).migrate.post(node=node)

    async def relocate_ha_resource(self, sid: str, node: str) -> None:
        """
        Relocate HA resource to another node.

        Args:
            sid: Resource ID
            node: Target node
        """
        await self.proxmox.cluster.ha.resources(sid).relocate.post(node=node)

    async def list_ha_groups(self) -> list[HAGroup]:
        """
        List HA groups.

        Returns:
            List of HAGroup objects
        """
        data: ResponseData = await self.proxmox.cluster.ha.groups.get()
        return [HAGroup.from_dict(g) for g in data]

    async def get_ha_group(self, group: str) -> HAGroup:
        """
        Get HA group details.

        Args:
            group: Group name

        Returns:
            HAGroup object
        """
        data: ResponseData = await self.proxmox.cluster.ha.groups(group).get()
        return HAGroup.from_dict(data)

    async def create_ha_group(
        self,
        group: str,
        nodes: str,
        nofailback: bool = False,
        restricted: bool = False,
        comment: str | None = None,
    ) -> None:
        """
        Create HA group.

        Args:
            group: Group name
            nodes: Node list (e.g., "node1:2,node2:1")
            nofailback: No failback
            restricted: Resources bound to this group may only run on specified nodes
            comment: Comment
        """
        params = {"group": group, "nodes": nodes}
        if nofailback:
            params["nofailback"] = 1
        if restricted:
            params["restricted"] = 1
        if comment:
            params["comment"] = comment

        await self.proxmox.cluster.ha.groups.post(**params)

    async def update_ha_group(
        self,
        group: str,
        nodes: str | None = None,
        nofailback: bool | None = None,
        restricted: bool | None = None,
        comment: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update HA group.

        Args:
            group: Group name
            nodes: Node list
            nofailback: No failback
            restricted: Restricted to specified nodes
            comment: Comment
            delete: List of settings to delete
        """
        params = {}
        if nodes is not None:
            params["nodes"] = nodes
        if nofailback is not None:
            params["nofailback"] = 1 if nofailback else 0
        if restricted is not None:
            params["restricted"] = 1 if restricted else 0
        if comment is not None:
            params["comment"] = comment
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.ha.groups(group).put(**params)

    async def delete_ha_group(self, group: str) -> None:
        """
        Delete HA group.

        Args:
            group: Group name
        """
        await self.proxmox.cluster.ha.groups(group).delete()

    async def get_ha_status(self) -> dict[str, Any]:
        """
        Get HA manager status.

        Returns:
            HA status information
        """
        return await self.proxmox.cluster.ha.status.current.get()

    # Backup Jobs
    async def list_backup_jobs(self) -> list[BackupJob]:
        """
        List backup jobs.

        Returns:
            List of BackupJob objects
        """
        data: ResponseData = await self.proxmox.cluster.backup.get()
        return [BackupJob.from_dict(j) for j in data]

    async def get_backup_job(self, id: str) -> BackupJob:
        """
        Get backup job details.

        Args:
            id: Job ID

        Returns:
            BackupJob object
        """
        data: ResponseData = await self.proxmox.cluster.backup(id).get()
        return BackupJob.from_dict(data)

    async def create_backup_job(
        self,
        id: str,
        schedule: str,
        storage: str,
        vmid: str | None = None,
        node: str | None = None,
        all: bool = False,
        enabled: bool = True,
        mode: str | BackupMode = BackupMode.SNAPSHOT,
        compress: str | BackupCompression = BackupCompression.ZSTD,
        mailnotification: str = "always",
        mailto: str | None = None,
        prune_backups: str | None = None,
        comment: str | None = None,
    ) -> None:
        """
        Create backup job.

        Args:
            id: Job ID
            schedule: Backup schedule (e.g., "mon,wed,fri 02:00")
            storage: Target storage
            vmid: Comma-separated VMID list (or "all")
            node: Only backup VMs on this node
            all: Backup all VMs
            enabled: Enable the job
            mode: Backup mode
            compress: Compression type
            mailnotification: Mail notification (always, failure, never)
            mailto: Email address
            prune_backups: Prune settings
            comment: Comment
        """
        params = {"id": id, "schedule": schedule, "storage": storage}
        if vmid:
            params["vmid"] = vmid
        if node:
            params["node"] = node
        if all:
            params["all"] = 1
        if not enabled:
            params["enabled"] = 0
        if isinstance(mode, BackupMode):
            params["mode"] = mode.value
        else:
            params["mode"] = mode
        if isinstance(compress, BackupCompression):
            params["compress"] = compress.value
        else:
            params["compress"] = compress
        if mailnotification != "always":
            params["mailnotification"] = mailnotification
        if mailto:
            params["mailto"] = mailto
        if prune_backups:
            params["prune-backups"] = prune_backups
        if comment:
            params["comment"] = comment

        await self.proxmox.cluster.backup.post(**params)

    async def update_backup_job(
        self,
        id: str,
        schedule: str | None = None,
        storage: str | None = None,
        vmid: str | None = None,
        node: str | None = None,
        all: bool | None = None,
        enabled: bool | None = None,
        mode: str | BackupMode | None = None,
        compress: str | BackupCompression | None = None,
        mailnotification: str | None = None,
        mailto: str | None = None,
        prune_backups: str | None = None,
        comment: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update backup job.

        Args:
            id: Job ID
            schedule: Backup schedule
            storage: Target storage
            vmid: VMID list
            node: Node filter
            all: Backup all VMs
            enabled: Enable the job
            mode: Backup mode
            compress: Compression type
            mailnotification: Mail notification
            mailto: Email address
            prune_backups: Prune settings
            comment: Comment
            delete: List of settings to delete
        """
        params = {}
        if schedule is not None:
            params["schedule"] = schedule
        if storage is not None:
            params["storage"] = storage
        if vmid is not None:
            params["vmid"] = vmid
        if node is not None:
            params["node"] = node
        if all is not None:
            params["all"] = 1 if all else 0
        if enabled is not None:
            params["enabled"] = 1 if enabled else 0
        if mode is not None:
            if isinstance(mode, BackupMode):
                params["mode"] = mode.value
            else:
                params["mode"] = mode
        if compress is not None:
            if isinstance(compress, BackupCompression):
                params["compress"] = compress.value
            else:
                params["compress"] = compress
        if mailnotification is not None:
            params["mailnotification"] = mailnotification
        if mailto is not None:
            params["mailto"] = mailto
        if prune_backups is not None:
            params["prune-backups"] = prune_backups
        if comment is not None:
            params["comment"] = comment
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.backup(id).put(**params)

    async def delete_backup_job(self, id: str) -> None:
        """
        Delete backup job.

        Args:
            id: Job ID
        """
        await self.proxmox.cluster.backup(id).delete()

    # Replication
    async def list_replication_jobs(self) -> list[ReplicationJob]:
        """
        List replication jobs.

        Returns:
            List of ReplicationJob objects
        """
        data: ResponseData = await self.proxmox.cluster.replication.get()
        return [ReplicationJob.from_dict(j) for j in data]

    async def get_replication_job(self, id: str) -> ReplicationJob:
        """
        Get replication job details.

        Args:
            id: Job ID

        Returns:
            ReplicationJob object
        """
        data: ResponseData = await self.proxmox.cluster.replication(id).get()
        return ReplicationJob.from_dict(data)

    async def create_replication_job(
        self,
        id: str,
        target: str,
        type: str = "local",
        schedule: str = "*/15",
        rate: float | None = None,
        source: str | None = None,
        comment: str | None = None,
        disable: bool = False,
    ) -> None:
        """
        Create replication job.

        Args:
            id: Job ID (format: <GUEST>-<JOBNUM>)
            target: Target node
            type: Replication type
            schedule: Schedule (systemd calendar event format)
            rate: Rate limit in mbps
            source: Source node
            comment: Comment
            disable: Disable the job
        """
        params = {"id": id, "target": target, "type": type}
        if schedule != "*/15":
            params["schedule"] = schedule
        if rate:
            params["rate"] = rate
        if source:
            params["source"] = source
        if comment:
            params["comment"] = comment
        if disable:
            params["disable"] = 1

        await self.proxmox.cluster.replication.post(**params)

    async def update_replication_job(
        self,
        id: str,
        schedule: str | None = None,
        rate: float | None = None,
        comment: str | None = None,
        disable: bool | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update replication job.

        Args:
            id: Job ID
            schedule: Schedule
            rate: Rate limit in mbps
            comment: Comment
            disable: Disable the job
            delete: List of settings to delete
        """
        params = {}
        if schedule is not None:
            params["schedule"] = schedule
        if rate is not None:
            params["rate"] = rate
        if comment is not None:
            params["comment"] = comment
        if disable is not None:
            params["disable"] = 1 if disable else 0
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.replication(id).put(**params)

    async def delete_replication_job(
        self, id: str, force: bool = False, keep: bool = False
    ) -> None:
        """
        Delete replication job.

        Args:
            id: Job ID
            force: Force removal without cleanup
            keep: Keep replicated data at target
        """
        params = {}
        if force:
            params["force"] = 1
        if keep:
            params["keep"] = 1

        await self.proxmox.cluster.replication(id).delete(**params)

    # ACME
    async def list_acme_accounts(self) -> list[ACMEAccount]:
        """
        List ACME accounts.

        Returns:
            List of ACMEAccount objects
        """
        data: ResponseData = await self.proxmox.cluster.acme.account.get()
        return [ACMEAccount.from_dict(a) for a in data]

    async def get_acme_account(self, name: str) -> ACMEAccount:
        """
        Get ACME account details.

        Args:
            name: Account name

        Returns:
            ACMEAccount object
        """
        data: ResponseData = await self.proxmox.cluster.acme.account(name).get()
        return ACMEAccount.from_dict(data)

    async def create_acme_account(
        self, name: str, email: str, directory: str | None = None
    ) -> dict[str, Any]:
        """
        Create ACME account.

        Args:
            name: Account name
            email: Email address
            directory: ACME directory URL

        Returns:
            Account information
        """
        params = {"name": name, "contact": email}
        if directory:
            params["directory"] = directory

        return await self.proxmox.cluster.acme.account.post(**params)

    async def update_acme_account(self, name: str, email: str) -> None:
        """
        Update ACME account.

        Args:
            name: Account name
            email: New email address
        """
        await self.proxmox.cluster.acme.account(name).put(contact=email)

    async def delete_acme_account(self, name: str) -> None:
        """
        Delete ACME account.

        Args:
            name: Account name
        """
        await self.proxmox.cluster.acme.account(name).delete()

    async def get_acme_tos(self, directory: str | None = None) -> dict[str, Any]:
        """
        Get ACME Terms of Service URL.

        Args:
            directory: ACME directory URL

        Returns:
            TOS information
        """
        params = {}
        if directory:
            params["directory"] = directory

        return await self.proxmox.cluster.acme.tos.get(**params)

    async def list_acme_directories(self) -> list[dict[str, Any]]:
        """
        List known ACME directories.

        Returns:
            List of ACME directories
        """
        return await self.proxmox.cluster.acme.directories.get()

    async def list_acme_plugins(self) -> list[dict[str, Any]]:
        """
        List ACME challenge plugins.

        Returns:
            List of ACME plugins
        """
        return await self.proxmox.cluster.acme.plugins.get()

    # Options
    async def get_options(self) -> dict[str, Any]:
        """
        Get cluster options.

        Returns:
            Cluster options
        """
        return await self.proxmox.cluster.options.get()

    async def set_options(
        self,
        bandwidth_limit: str | None = None,
        console: str | None = None,
        crs: str | None = None,
        description: str | None = None,
        email_from: str | None = None,
        fencing: str | None = None,
        ha: str | None = None,
        http_proxy: str | None = None,
        keyboard: str | None = None,
        language: str | None = None,
        mac_prefix: str | None = None,
        max_workers: int | None = None,
        migration: str | None = None,
        next_id: str | None = None,
        notify: str | None = None,
        tag_style: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Set cluster options.

        Args:
            bandwidth_limit: Default bandwidth limit
            console: Console viewer preference
            crs: Cluster resource scheduler settings
            description: Cluster description
            email_from: Email from address
            fencing: Fencing mode
            ha: HA settings
            http_proxy: HTTP proxy
            keyboard: Default keyboard layout
            language: Default language
            mac_prefix: MAC address prefix
            max_workers: Maximum workers
            migration: Migration settings
            next_id: Next ID settings
            notify: Notification settings
            tag_style: Tag style settings
            delete: List of settings to delete
        """
        params = {}
        if bandwidth_limit is not None:
            params["bwlimit"] = bandwidth_limit
        if console is not None:
            params["console"] = console
        if crs is not None:
            params["crs"] = crs
        if description is not None:
            params["description"] = description
        if email_from is not None:
            params["email_from"] = email_from
        if fencing is not None:
            params["fencing"] = fencing
        if ha is not None:
            params["ha"] = ha
        if http_proxy is not None:
            params["http_proxy"] = http_proxy
        if keyboard is not None:
            params["keyboard"] = keyboard
        if language is not None:
            params["language"] = language
        if mac_prefix is not None:
            params["mac_prefix"] = mac_prefix
        if max_workers is not None:
            params["max_workers"] = max_workers
        if migration is not None:
            params["migration"] = migration
        if next_id is not None:
            params["next_id"] = next_id
        if notify is not None:
            params["notify"] = notify
        if tag_style is not None:
            params["tag-style"] = tag_style
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.options.put(**params)
