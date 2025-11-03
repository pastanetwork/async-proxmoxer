"""
Ceph storage helpers for Proxmoxer.

Provides high-level async API for managing Ceph storage on Proxmox nodes,
including OSDs, monitors, managers, MDS, pools, and CephFS.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class CephServiceType(str, Enum):
    """Ceph service types."""

    OSD = "osd"
    MON = "mon"
    MGR = "mgr"
    MDS = "mds"


@dataclass
class CephOSD:
    """Ceph OSD (Object Storage Daemon)."""

    id: int
    status: str
    weight: float
    reweight: float
    host: str
    device_class: str | None = None
    in_service: bool = True
    up: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephOSD:
        """Create CephOSD from API response."""
        return cls(
            id=data.get("id", data.get("osdid", 0)),
            status=data.get("status", ""),
            weight=data.get("weight", 0.0),
            reweight=data.get("reweight", 1.0),
            host=data.get("host", ""),
            device_class=data.get("device_class"),
            in_service=bool(data.get("in", 1)),
            up=bool(data.get("up", 1)),
        )


@dataclass
class CephMon:
    """Ceph Monitor."""

    name: str
    addr: str
    rank: int | None = None
    in_quorum: bool = True
    ceph_version: str | None = None
    ceph_version_short: str | None = None
    direxists: str | None = None
    quorum: bool | None = None
    service: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephMon:
        """Create CephMon from API response."""
        return cls(
            name=data.get("name", ""),
            addr=data.get("addr", data.get("host", "")),
            rank=data.get("rank"),
            in_quorum=bool(data.get("in_quorum", 1)),
            ceph_version=data.get("ceph_version"),
            ceph_version_short=data.get("ceph_version_short"),
            direxists=data.get("direxists"),
            quorum=bool(data.get("quorum", 0)) if data.get("quorum") is not None else None,
            service=data.get("service"),
        )


@dataclass
class CephMgr:
    """Ceph Manager."""

    name: str
    addr: str | None = None
    active: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephMgr:
        """Create CephMgr from API response."""
        return cls(
            name=data.get("name", ""),
            addr=data.get("addr"),
            active=bool(data.get("active", 0)),
        )


@dataclass
class CephMDS:
    """Ceph Metadata Server."""

    name: str
    addr: str | None = None
    rank: int | None = None
    state: str | None = None
    standby_replay: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephMDS:
        """Create CephMDS from API response."""
        return cls(
            name=data.get("name", ""),
            addr=data.get("addr"),
            rank=data.get("rank"),
            state=data.get("state"),
            standby_replay=bool(data.get("standby_replay", 0)) if data.get("standby_replay") is not None else None,
        )


@dataclass
class CephPool:
    """Ceph Storage Pool."""

    pool: int
    pool_name: str
    size: int
    min_size: int
    pg_num: int
    type: str
    bytes_used: int | None = None
    percent_used: float | None = None
    pg_autoscale_mode: str | None = None
    pg_num_final: int | None = None
    pg_num_min: int | None = None
    target_size: int | None = None
    target_size_ratio: float | None = None
    crush_rule: str | None = None
    crush_rule_name: str | None = None
    application: str | None = None
    application_metadata: dict[str, Any] | None = None
    autoscale_status: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephPool:
        """Create CephPool from API response."""
        return cls(
            pool=int(data.get("pool", data.get("poolid", 0))),
            pool_name=data.get("pool_name", data.get("name", "")),
            size=data.get("size", 3),
            min_size=data.get("min_size", 2),
            pg_num=data.get("pg_num", 128),
            type=data.get("type", "unknown"),
            bytes_used=data.get("bytes_used"),
            percent_used=data.get("percent_used"),
            pg_autoscale_mode=data.get("pg_autoscale_mode"),
            pg_num_final=data.get("pg_num_final"),
            pg_num_min=data.get("pg_num_min"),
            target_size=data.get("target_size"),
            target_size_ratio=data.get("target_size_ratio"),
            crush_rule=data.get("crush_rule"),
            crush_rule_name=data.get("crush_rule_name"),
            application=data.get("application"),
            application_metadata=data.get("application_metadata"),
            autoscale_status=data.get("autoscale_status"),
        )


@dataclass
class CephFS:
    """Ceph Filesystem."""

    name: str
    data_pool: str
    metadata_pool: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephFS:
        """Create CephFS from API response."""
        return cls(
            name=data.get("name", ""),
            data_pool=data.get("data_pool", ""),
            metadata_pool=data.get("metadata_pool", ""),
        )


@dataclass
class CephStatus:
    """Ceph cluster status."""

    health: str
    monitors: int
    osds: int
    osds_up: int
    osds_in: int
    pgs: int
    pools: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CephStatus:
        """Create CephStatus from API response."""
        health_data = data.get("health", {})
        osd_data = data.get("osdmap", {}).get("osdmap", {})
        pg_data = data.get("pgmap", {})

        return cls(
            health=health_data.get("status", "HEALTH_UNKNOWN"),
            monitors=len(data.get("monmap", {}).get("mons", [])),
            osds=osd_data.get("num_osds", 0),
            osds_up=osd_data.get("num_up_osds", 0),
            osds_in=osd_data.get("num_in_osds", 0),
            pgs=pg_data.get("num_pgs", 0),
            pools=len(data.get("osdmap", {}).get("pools", [])),
        )


class CephManager:
    """
    High-level manager for Ceph operations on a Proxmox node.

    Provides methods for managing Ceph OSDs, monitors, managers,
    metadata servers, pools, and filesystems.

    Example:
        >>> ceph = CephManager(proxmox, "pve-node1")
        >>> status = await ceph.get_status()
        >>> osds = await ceph.list_osds()
        >>> await ceph.create_osd(device="/dev/sdb", db_device="/dev/nvme0n1")
        >>> await ceph.create_pool("vm-pool", size=3, pg_num=128)
    """

    def __init__(self, proxmox: Any, node: str):
        """
        Initialize CephManager.

        Args:
            proxmox: Proxmoxer instance
            node: Node name
        """
        self.proxmox = proxmox
        self.node = node
        self._ceph_api = proxmox.nodes(node).ceph

    # Ceph Status
    async def get_status(self) -> dict[str, Any]:
        """
        Get Ceph cluster status.

        Returns:
            Ceph status dict
        """
        return await self._ceph_api.status.get()

    async def get_status_parsed(self) -> CephStatus:
        """
        Get parsed Ceph cluster status.

        Returns:
            CephStatus object
        """
        data = await self.get_status()
        return CephStatus.from_dict(data)

    # Ceph Initialization
    async def init_ceph(
        self,
        network: str,
        cluster_network: str | None = None,
        size: int = 3,
        min_size: int = 2,
    ) -> str:
        """
        Initialize Ceph on this node.

        Args:
            network: Ceph public network CIDR
            cluster_network: Ceph cluster network CIDR (optional)
            size: Default pool size
            min_size: Default pool min_size

        Returns:
            Success message
        """
        params = {"network": network, "size": size, "min_size": min_size}
        if cluster_network:
            params["cluster-network"] = cluster_network

        return await self._ceph_api.init.post(**params)

    async def stop_ceph(self, service: str | None = None) -> str:
        """
        Stop Ceph services.

        Args:
            service: Specific service to stop (e.g., "osd.0")

        Returns:
            Success message
        """
        params = {}
        if service:
            params["service"] = service

        return await self._ceph_api.stop.post(**params)

    async def start_ceph(self, service: str | None = None) -> str:
        """
        Start Ceph services.

        Args:
            service: Specific service to start (e.g., "osd.0")

        Returns:
            Success message
        """
        params = {}
        if service:
            params["service"] = service

        return await self._ceph_api.start.post(**params)

    # OSD Management
    async def list_osds(self) -> list[CephOSD]:
        """
        List Ceph OSDs on this node.

        Returns:
            List of CephOSD objects
        """
        data: ResponseData = await self._ceph_api.osd.get()
        return [CephOSD.from_dict(osd) for osd in data]

    async def create_osd(
        self,
        device: str,
        db_device: str | None = None,
        wal_device: str | None = None,
        encrypted: bool = False,
        crush_device_class: str | None = None,
    ) -> str:
        """
        Create a Ceph OSD.

        Args:
            device: Block device path (e.g., "/dev/sdb")
            db_device: Block device for DB (optional, for BlueStore)
            wal_device: Block device for WAL (optional, for BlueStore)
            encrypted: Encrypt OSD
            crush_device_class: CRUSH device class (e.g., "ssd", "nvme", "hdd")

        Returns:
            Task ID (UPID)
        """
        params = {"dev": device}
        if db_device:
            params["db_dev"] = db_device
        if wal_device:
            params["wal_dev"] = wal_device
        if encrypted:
            params["encrypted"] = 1
        if crush_device_class:
            params["crush-device-class"] = crush_device_class

        return await self._ceph_api.osd.post(**params)

    async def destroy_osd(self, osdid: int, cleanup: bool = False) -> str:
        """
        Destroy a Ceph OSD.

        Args:
            osdid: OSD ID
            cleanup: Cleanup device

        Returns:
            Task ID (UPID)
        """
        params = {}
        if cleanup:
            params["cleanup"] = 1

        return await self._ceph_api.osd(osdid).delete(**params)

    async def osd_in(self, osdid: int) -> None:
        """
        Mark OSD as in.

        Args:
            osdid: OSD ID
        """
        await self._ceph_api.osd(osdid)("in").post()

    async def osd_out(self, osdid: int) -> None:
        """
        Mark OSD as out.

        Args:
            osdid: OSD ID
        """
        await self._ceph_api.osd(osdid).out.post()

    # Monitor Management
    async def list_monitors(self) -> list[CephMon]:
        """
        List Ceph monitors.

        Returns:
            List of CephMon objects
        """
        data: ResponseData = await self._ceph_api.mon.get()
        return [CephMon.from_dict(mon) for mon in data]

    async def create_monitor(self, mon_address: str | None = None) -> str:
        """
        Create a Ceph monitor on this node.

        Args:
            mon_address: Monitor address (optional, auto-detected)

        Returns:
            Success message
        """
        params = {}
        if mon_address:
            params["mon-address"] = mon_address

        return await self._ceph_api.mon(self.node).post(**params)

    async def destroy_monitor(self, monid: str) -> str:
        """
        Destroy a Ceph monitor.

        Args:
            monid: Monitor ID (node name)

        Returns:
            Success message
        """
        return await self._ceph_api.mon(monid).delete()

    # Manager Management
    async def list_managers(self) -> list[CephMgr]:
        """
        List Ceph managers.

        Returns:
            List of CephMgr objects
        """
        data: ResponseData = await self._ceph_api.mgr.get()
        return [CephMgr.from_dict(mgr) for mgr in data]

    async def create_manager(self) -> str:
        """
        Create a Ceph manager on this node.

        Returns:
            Success message
        """
        return await self._ceph_api.mgr(self.node).post()

    async def destroy_manager(self, mgrid: str) -> str:
        """
        Destroy a Ceph manager.

        Args:
            mgrid: Manager ID (node name)

        Returns:
            Success message
        """
        return await self._ceph_api.mgr(mgrid).delete()

    # MDS Management
    async def list_mds(self) -> list[CephMDS]:
        """
        List Ceph metadata servers.

        Returns:
            List of CephMDS objects
        """
        data: ResponseData = await self._ceph_api.mds.get()
        return [CephMDS.from_dict(mds) for mds in data]

    async def create_mds(self, hotstandby: bool = False) -> str:
        """
        Create a Ceph MDS on this node.

        Args:
            hotstandby: Start as hotstandby

        Returns:
            Success message
        """
        params = {}
        if hotstandby:
            params["hotstandby"] = 1

        return await self._ceph_api.mds(self.node).post(**params)

    async def destroy_mds(self, name: str) -> str:
        """
        Destroy a Ceph MDS.

        Args:
            name: MDS name

        Returns:
            Success message
        """
        return await self._ceph_api.mds(name).delete()

    # Pool Management
    async def list_pools(self) -> list[CephPool]:
        """
        List Ceph pools.

        Returns:
            List of CephPool objects
        """
        data: ResponseData = await self._ceph_api.pool.get()
        return [CephPool.from_dict(pool) for pool in data]

    async def get_pool(self, name: str) -> CephPool:
        """
        Get pool details.

        Args:
            name: Pool name

        Returns:
            CephPool object
        """
        data: ResponseData = await self._ceph_api.pool(name).get()
        return CephPool.from_dict(data)

    async def create_pool(
        self,
        name: str,
        size: int = 3,
        min_size: int = 2,
        pg_num: int = 128,
        pg_autoscale_mode: str = "warn",
        crush_rule: str | None = None,
        application: str = "rbd",
        add_storages: bool = False,
    ) -> str:
        """
        Create a Ceph pool.

        Args:
            name: Pool name
            size: Replication size
            min_size: Minimum replication size
            pg_num: Number of placement groups
            pg_autoscale_mode: PG autoscale mode (on, off, warn)
            crush_rule: CRUSH rule name
            application: Pool application (rbd, cephfs, rgw)
            add_storages: Automatically create Proxmox storages

        Returns:
            Success message
        """
        params = {
            "name": name,
            "size": size,
            "min_size": min_size,
            "pg_num": pg_num,
            "pg_autoscale_mode": pg_autoscale_mode,
            "application": application,
        }
        if crush_rule:
            params["crush_rule"] = crush_rule
        if add_storages:
            params["add_storages"] = 1

        return await self._ceph_api.pool.post(**params)

    async def update_pool(
        self,
        name: str,
        size: int | None = None,
        min_size: int | None = None,
        pg_num: int | None = None,
        pg_autoscale_mode: str | None = None,
        crush_rule: str | None = None,
    ) -> str:
        """
        Update pool configuration.

        Args:
            name: Pool name
            size: Replication size
            min_size: Minimum replication size
            pg_num: Number of placement groups
            pg_autoscale_mode: PG autoscale mode
            crush_rule: CRUSH rule name

        Returns:
            Success message
        """
        params = {}
        if size is not None:
            params["size"] = size
        if min_size is not None:
            params["min_size"] = min_size
        if pg_num is not None:
            params["pg_num"] = pg_num
        if pg_autoscale_mode is not None:
            params["pg_autoscale_mode"] = pg_autoscale_mode
        if crush_rule is not None:
            params["crush_rule"] = crush_rule

        return await self._ceph_api.pool(name).put(**params)

    async def destroy_pool(self, name: str, force: bool = False) -> str:
        """
        Destroy a Ceph pool.

        Args:
            name: Pool name
            force: Force destruction

        Returns:
            Success message
        """
        params = {}
        if force:
            params["force"] = 1

        return await self._ceph_api.pool(name).delete(**params)

    # CephFS Management
    async def list_cephfs(self) -> list[CephFS]:
        """
        List CephFS filesystems.

        Returns:
            List of CephFS objects
        """
        data: ResponseData = await self._ceph_api.fs.get()
        return [CephFS.from_dict(fs) for fs in data]

    async def create_cephfs(
        self,
        name: str,
        pg_num: int = 128,
        add_storage: bool = False,
    ) -> str:
        """
        Create a CephFS filesystem.

        Args:
            name: Filesystem name
            pg_num: Number of placement groups for pools
            add_storage: Automatically create Proxmox storage

        Returns:
            Success message
        """
        params = {"name": name, "pg_num": pg_num}
        if add_storage:
            params["add-storage"] = 1

        return await self._ceph_api.fs(name).post(**params)

    # Ceph Configuration
    async def get_config(self) -> dict[str, Any]:
        """
        Get Ceph configuration.

        Returns:
            Configuration dict
        """
        return await self._ceph_api.config.get()

    async def get_config_db(self) -> list[dict[str, Any]]:
        """
        Get Ceph configuration database.

        Returns:
            List of configuration entries
        """
        return await self._ceph_api.configdb.get()

    # Ceph Flags
    async def get_flags(self) -> dict[str, Any]:
        """
        Get Ceph flags.

        Returns:
            Flags dict
        """
        return await self._ceph_api.flags.get()

    async def set_flag(self, flag: str) -> None:
        """
        Set a Ceph flag.

        Args:
            flag: Flag name (e.g., "noout", "nodown", "norecover")
        """
        await self._ceph_api.flags(flag).post()

    async def unset_flag(self, flag: str) -> None:
        """
        Unset a Ceph flag.

        Args:
            flag: Flag name
        """
        await self._ceph_api.flags(flag).delete()

    # CRUSH
    async def get_crush(self) -> str:
        """
        Get CRUSH map.

        Returns:
            CRUSH map as text
        """
        return await self._ceph_api.crush.get()

    # Ceph Logs
    async def get_log(
        self, start: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get Ceph cluster log.

        Args:
            start: Start line
            limit: Number of lines

        Returns:
            List of log entries
        """
        return await self._ceph_api.log.get(start=start, limit=limit)

    # Ceph Rules
    async def get_rules(self) -> list[dict[str, Any]]:
        """
        Get CRUSH rules.

        Returns:
            List of CRUSH rules
        """
        return await self._ceph_api.rules.get()
