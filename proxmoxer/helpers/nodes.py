"""
Node management helpers for Proxmoxer.

Provides high-level async API for managing Proxmox nodes,
VMs, containers, storage, and services.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class VMStatus(str, Enum):
    """VM/Container status."""

    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"


class VMType(str, Enum):
    """VM type."""

    QEMU = "qemu"
    LXC = "lxc"


@dataclass
class BootInfo:
    """Boot information."""

    mode: str
    secureboot: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BootInfo:
        """Create BootInfo from API response."""
        return cls(
            mode=data["mode"],
            secureboot=bool(data.get("secureboot", 0)),
        )


@dataclass
class CPUInfo:
    """CPU information."""

    cores: int
    cpus: int
    model: str
    sockets: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CPUInfo:
        """Create CPUInfo from API response."""
        return cls(
            cores=data["cores"],
            cpus=data["cpus"],
            model=data["model"],
            sockets=data["sockets"],
        )


@dataclass
class KernelInfo:
    """Kernel information."""

    machine: str
    release: str
    sysname: str
    version: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KernelInfo:
        """Create KernelInfo from API response."""
        return cls(
            machine=data["machine"],
            release=data["release"],
            sysname=data["sysname"],
            version=data["version"],
        )


@dataclass
class MemoryInfo:
    """Memory information."""

    available: int
    free: int
    total: int
    used: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryInfo:
        """Create MemoryInfo from API response."""
        return cls(
            available=data["available"],
            free=data["free"],
            total=data["total"],
            used=data["used"],
        )


@dataclass
class RootFSInfo:
    """Root filesystem information."""

    avail: int
    free: int
    total: int
    used: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RootFSInfo:
        """Create RootFSInfo from API response."""
        return cls(
            avail=data["avail"],
            free=data["free"],
            total=data["total"],
            used=data["used"],
        )


@dataclass
class NodeStatus:
    """Node status information."""

    cpu: float
    loadavg: list[str]
    pveversion: str
    boot_info: BootInfo
    cpuinfo: CPUInfo
    current_kernel: KernelInfo
    memory: MemoryInfo
    rootfs: RootFSInfo

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeStatus:
        """Create NodeStatus from API response."""
        return cls(
            cpu=data["cpu"],
            loadavg=data["loadavg"],
            pveversion=data["pveversion"],
            boot_info=BootInfo.from_dict(data["boot-info"]),
            cpuinfo=CPUInfo.from_dict(data["cpuinfo"]),
            current_kernel=KernelInfo.from_dict(data["current-kernel"]),
            memory=MemoryInfo.from_dict(data["memory"]),
            rootfs=RootFSInfo.from_dict(data["rootfs"]),
        )


@dataclass
class VM:
    """Virtual machine or container."""

    vmid: int
    name: str
    status: str
    type: str
    node: str | None = None
    uptime: int | None = None
    cpu: float | None = None
    cpus: int | None = None
    mem: int | None = None
    maxmem: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    netin: int | None = None
    netout: int | None = None
    diskread: int | None = None
    diskwrite: int | None = None
    template: bool = False
    # Additional fields
    lock: str | None = None
    tags: str | None = None
    # QEMU-specific fields
    memhost: int | None = None
    pid: int | None = None
    qmpstatus: str | None = None
    running_machine: str | None = None
    running_qemu: str | None = None
    serial: bool | None = None
    # LXC-specific fields
    maxswap: int | None = None
    # Pressure metrics (available for both QEMU and LXC)
    pressurecpufull: float | None = None
    pressurecpusome: float | None = None
    pressureiofull: float | None = None
    pressureiosome: float | None = None
    pressurememoryfull: float | None = None
    pressurememorysome: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VM:
        """Create VM from API response."""
        return cls(
            vmid=data["vmid"],
            name=data.get("name", ""),
            status=data.get("status", ""),
            type=data.get("type", "qemu"),
            node=data.get("node"),
            uptime=data.get("uptime"),
            cpu=data.get("cpu"),
            cpus=data.get("cpus"),
            mem=data.get("mem"),
            maxmem=data.get("maxmem"),
            disk=data.get("disk"),
            maxdisk=data.get("maxdisk"),
            netin=data.get("netin"),
            netout=data.get("netout"),
            diskread=data.get("diskread"),
            diskwrite=data.get("diskwrite"),
            template=bool(data.get("template", 0)),
            lock=data.get("lock"),
            tags=data.get("tags"),
            memhost=data.get("memhost"),
            pid=data.get("pid"),
            qmpstatus=data.get("qmpstatus"),
            running_machine=data.get("running-machine"),
            running_qemu=data.get("running-qemu"),
            serial=bool(data.get("serial", 0)) if "serial" in data else None,
            maxswap=data.get("maxswap"),
            pressurecpufull=data.get("pressurecpufull"),
            pressurecpusome=data.get("pressurecpusome"),
            pressureiofull=data.get("pressureiofull"),
            pressureiosome=data.get("pressureiosome"),
            pressurememoryfull=data.get("pressurememoryfull"),
            pressurememorysome=data.get("pressurememorysome"),
        )


@dataclass
class Service:
    """System service."""

    name: str
    state: str
    desc: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Service:
        """Create Service from API response."""
        return cls(
            name=data["name"],
            state=data.get("state", ""),
            desc=data.get("desc"),
        )


@dataclass
class StorageContent:
    """Storage content entry."""

    volid: str
    format: str
    size: int
    content: str | None = None
    vmid: int | None = None
    ctime: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StorageContent:
        """Create StorageContent from API response."""
        return cls(
            volid=data["volid"],
            format=data.get("format", ""),
            size=data.get("size", 0),
            content=data.get("content"),
            vmid=data.get("vmid"),
            ctime=data.get("ctime"),
        )


@dataclass
class Snapshot:
    """VM/Container snapshot."""

    name: str
    snaptime: int | None = None
    description: str | None = None
    vmstate: bool = False
    parent: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Snapshot:
        """Create Snapshot from API response."""
        return cls(
            name=data["name"],
            snaptime=data.get("snaptime"),
            description=data.get("description"),
            vmstate=bool(data.get("vmstate", 0)),
            parent=data.get("parent"),
        )


@dataclass
class NodeVersion:
    """Node version information."""

    release: str
    repoid: str
    version: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeVersion:
        """Create NodeVersion from API response."""
        return cls(
            release=data["release"],
            repoid=data["repoid"],
            version=data["version"],
        )


@dataclass
class NodeTime:
    """Node time information."""

    localtime: int
    timezone: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NodeTime:
        """Create NodeTime from API response."""
        return cls(
            localtime=data["localtime"],
            timezone=data["timezone"],
        )


@dataclass
class NetworkInterface:
    """Network interface configuration."""

    iface: str
    type: str
    active: bool | None = None
    address: str | None = None
    address6: str | None = None
    autostart: bool | None = None
    bridge_ports: str | None = None
    bridge_stp: str | None = None
    bridge_vlan_aware: bool | None = None
    cidr: str | None = None
    cidr6: str | None = None
    comments: str | None = None
    comments6: str | None = None
    exists: bool | None = None
    families: list[str] | None = None
    gateway: str | None = None
    gateway6: str | None = None
    method: str | None = None
    method6: str | None = None
    netmask: str | None = None
    options: list[str] | None = None
    priority: int | None = None
    slaves: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkInterface:
        """Create NetworkInterface from API response."""
        return cls(
            iface=data["iface"],
            type=data["type"],
            active=bool(data.get("active", 0)) if data.get("active") is not None else None,
            address=data.get("address"),
            address6=data.get("address6"),
            autostart=bool(data.get("autostart", 0)) if data.get("autostart") is not None else None,
            bridge_ports=data.get("bridge_ports"),
            bridge_stp=data.get("bridge_stp"),
            bridge_vlan_aware=bool(data.get("bridge_vlan_aware", 0)) if data.get("bridge_vlan_aware") is not None else None,
            cidr=data.get("cidr"),
            cidr6=data.get("cidr6"),
            comments=data.get("comments"),
            comments6=data.get("comments6"),
            exists=bool(data.get("exists", 0)) if data.get("exists") is not None else None,
            families=data.get("families"),
            gateway=data.get("gateway"),
            gateway6=data.get("gateway6"),
            method=data.get("method"),
            method6=data.get("method6"),
            netmask=data.get("netmask"),
            options=data.get("options"),
            priority=data.get("priority"),
            slaves=data.get("slaves"),
        )


@dataclass
class QemuAgentInfo:
    """QEMU Guest Agent information."""

    version: str
    supported_commands: list[dict[str, Any]] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QemuAgentInfo:
        """Create QemuAgentInfo from API response."""
        return cls(
            version=data["version"],
            supported_commands=data.get("supported-commands"),
        )


@dataclass
class QemuAgentOSInfo:
    """QEMU Guest Agent OS information."""

    id: str | None = None
    kernel_release: str | None = None
    kernel_version: str | None = None
    machine: str | None = None
    name: str | None = None
    pretty_name: str | None = None
    version: str | None = None
    version_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QemuAgentOSInfo:
        """Create QemuAgentOSInfo from API response."""
        return cls(
            id=data.get("id"),
            kernel_release=data.get("kernel-release"),
            kernel_version=data.get("kernel-version"),
            machine=data.get("machine"),
            name=data.get("name"),
            pretty_name=data.get("pretty-name"),
            version=data.get("version"),
            version_id=data.get("version-id"),
        )


@dataclass
class QemuAgentFSInfo:
    """QEMU Guest Agent filesystem information."""

    name: str
    mountpoint: str
    disk: list[dict[str, Any]] | None = None
    total_bytes: int | None = None
    used_bytes: int | None = None
    type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QemuAgentFSInfo:
        """Create QemuAgentFSInfo from API response."""
        return cls(
            name=data["name"],
            mountpoint=data["mountpoint"],
            disk=data.get("disk"),
            total_bytes=data.get("total-bytes"),
            used_bytes=data.get("used-bytes"),
            type=data.get("type"),
        )


@dataclass
class QemuAgentExecResult:
    """QEMU Guest Agent command execution result."""

    pid: int
    exited: bool | None = None
    exitcode: int | None = None
    signal: int | None = None
    out_data: str | None = None
    err_data: str | None = None
    out_truncated: bool | None = None
    err_truncated: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QemuAgentExecResult:
        """Create QemuAgentExecResult from API response."""
        return cls(
            pid=data["pid"],
            exited=bool(data.get("exited", 0)) if data.get("exited") is not None else None,
            exitcode=data.get("exitcode"),
            signal=data.get("signal"),
            out_data=data.get("out-data"),
            err_data=data.get("err-data"),
            out_truncated=bool(data.get("out-truncated", 0)) if data.get("out-truncated") is not None else None,
            err_truncated=bool(data.get("err-truncated", 0)) if data.get("err-truncated") is not None else None,
        )


@dataclass
class DNSConfig:
    """DNS configuration."""

    dns1: str | None = None
    dns2: str | None = None
    dns3: str | None = None
    search: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DNSConfig:
        """Create DNSConfig from API response."""
        return cls(
            dns1=data.get("dns1"),
            dns2=data.get("dns2"),
            dns3=data.get("dns3"),
            search=data.get("search"),
        )


@dataclass
class HostsConfig:
    """Hosts file configuration."""

    data: str
    digest: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HostsConfig:
        """Create HostsConfig from API response."""
        return cls(
            data=data["data"],
            digest=data["digest"],
        )


@dataclass
class Subscription:
    """Node subscription information."""

    status: str
    checktime: int | None = None
    key: str | None = None
    level: str | None = None
    nextduedate: str | None = None
    productname: str | None = None
    regdate: str | None = None
    url: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Subscription:
        """Create Subscription from API response."""
        return cls(
            status=data["status"],
            checktime=data.get("checktime"),
            key=data.get("key"),
            level=data.get("level"),
            nextduedate=data.get("nextduedate"),
            productname=data.get("productname"),
            regdate=data.get("regdate"),
            url=data.get("url"),
        )


@dataclass
class APTUpdate:
    """APT package update information."""

    Package: str
    Title: str
    Arch: str
    Description: str
    Version: str
    OldVersion: str | None = None
    Priority: str | None = None
    Section: str | None = None
    ChangeLogUrl: str | None = None
    Origin: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> APTUpdate:
        """Create APTUpdate from API response."""
        return cls(
            Package=data["Package"],
            Title=data["Title"],
            Arch=data["Arch"],
            Description=data["Description"],
            Version=data["Version"],
            OldVersion=data.get("OldVersion"),
            Priority=data.get("Priority"),
            Section=data.get("Section"),
            ChangeLogUrl=data.get("ChangeLogUrl"),
            Origin=data.get("Origin"),
        )


@dataclass
class Certificate:
    """SSL certificate information."""

    filename: str
    fingerprint: str | None = None
    issuer: str | None = None
    notafter: int | None = None
    notbefore: int | None = None
    pem: str | None = None
    public_key_bits: int | None = None
    public_key_type: str | None = None
    san: list[str] | None = None
    subject: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Certificate:
        """Create Certificate from API response."""
        return cls(
            filename=data["filename"],
            fingerprint=data.get("fingerprint"),
            issuer=data.get("issuer"),
            notafter=data.get("notafter"),
            notbefore=data.get("notbefore"),
            pem=data.get("pem"),
            public_key_bits=data.get("public-key-bits"),
            public_key_type=data.get("public-key-type"),
            san=data.get("san"),
            subject=data.get("subject"),
        )


@dataclass
class SyslogEntry:
    """Syslog entry."""

    n: int
    t: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SyslogEntry:
        """Create SyslogEntry from API response."""
        return cls(
            n=data["n"],
            t=data["t"],
        )


@dataclass
class VNCInfo:
    """VNC connection information."""

    cert: str | None = None
    port: int | None = None
    ticket: str | None = None
    upid: str | None = None
    user: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VNCInfo:
        """Create VNCInfo from API response."""
        return cls(
            cert=data.get("cert"),
            port=data.get("port"),
            ticket=data.get("ticket"),
            upid=data.get("upid"),
            user=data.get("user"),
        )


@dataclass
class VNCWebSocket:
    """VNC WebSocket connection information."""

    port: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VNCWebSocket:
        """Create VNCWebSocket from API response."""
        return cls(
            port=data["port"],
        )


@dataclass
class TermProxy:
    """Terminal proxy connection information."""

    port: int
    ticket: str
    upid: str
    user: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TermProxy:
        """Create TermProxy from API response."""
        return cls(
            port=data["port"],
            ticket=data["ticket"],
            upid=data["upid"],
            user=data["user"],
        )


class NodeManager:
    """
    High-level manager for Proxmox node operations.

    Provides methods for managing nodes, VMs, containers,
    storage, and services.

    Example:
        >>> node_mgr = NodeManager(proxmox, "pve-node1")
        >>> status = await node_mgr.get_status()
        >>> vms = await node_mgr.list_vms()
        >>> await node_mgr.start_vm(100)
    """

    def __init__(self, proxmox: Any, node: str):
        """
        Initialize NodeManager.

        Args:
            proxmox: Proxmoxer instance
            node: Node name
        """
        self.proxmox = proxmox
        self.node = node
        self._node_api = proxmox.nodes(node)

    # Node Status
    async def get_status(self) -> NodeStatus:
        """
        Get node status.

        Returns:
            NodeStatus object
        """
        data: ResponseData = await self._node_api.status.get()
        data["node"] = self.node
        return NodeStatus.from_dict(data)

    async def get_version(self) -> NodeVersion:
        """
        Get node version information.

        Returns:
            NodeVersion object
        """
        data = await self._node_api.version.get()
        return NodeVersion.from_dict(data)

    async def get_time(self) -> NodeTime:
        """
        Get node time.

        Returns:
            NodeTime object
        """
        data = await self._node_api.time.get()
        return NodeTime.from_dict(data)

    async def set_time(self, timezone: str) -> None:
        """
        Set node timezone.

        Args:
            timezone: Timezone (e.g., "Europe/Berlin")
        """
        await self._node_api.time.put(timezone=timezone)

    # VM Management
    async def list_vms(self, vm_type: VMType | None = None) -> list[VM]:
        """
        List all VMs and containers on this node.

        Args:
            vm_type: Filter by type (qemu or lxc)

        Returns:
            List of VM objects
        """
        vms = []

        if vm_type is None or vm_type == VMType.QEMU:
            qemu_data: ResponseData = await self._node_api.qemu.get()
            for vm in qemu_data:
                vm["type"] = "qemu"
                vm["node"] = self.node
                vms.append(VM.from_dict(vm))

        if vm_type is None or vm_type == VMType.LXC:
            lxc_data: ResponseData = await self._node_api.lxc.get()
            for ct in lxc_data:
                ct["type"] = "lxc"
                ct["node"] = self.node
                vms.append(VM.from_dict(ct))

        return vms

    async def get_vm(self, vmid: int, vm_type: VMType | None = None) -> VM:
        """
        Get VM/container details.

        Args:
            vmid: VM ID
            vm_type: VM type (auto-detect if not specified)

        Returns:
            VM object
        """
        if vm_type is None:
            # Try to detect type
            try:
                data: ResponseData = await self._node_api.qemu(vmid).status.current.get()
                data["vmid"] = vmid
                data["type"] = "qemu"
                data["node"] = self.node
                return VM.from_dict(data)
            except Exception:
                data: ResponseData = await self._node_api.lxc(vmid).status.current.get()
                data["vmid"] = vmid
                data["type"] = "lxc"
                data["node"] = self.node
                return VM.from_dict(data)
        elif vm_type == VMType.QEMU:
            data: ResponseData = await self._node_api.qemu(vmid).status.current.get()
            data["vmid"] = vmid
            data["type"] = "qemu"
            data["node"] = self.node
            return VM.from_dict(data)
        else:
            data: ResponseData = await self._node_api.lxc(vmid).status.current.get()
            data["vmid"] = vmid
            data["type"] = "lxc"
            data["node"] = self.node
            return VM.from_dict(data)

    async def get_vm_config(self, vmid: int, vm_type: VMType) -> dict[str, Any]:
        """
        Get VM/container configuration.

        Args:
            vmid: VM ID
            vm_type: VM type

        Returns:
            Configuration dict
        """
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).config.get()
        else:
            return await self._node_api.lxc(vmid).config.get()

    async def update_vm_config(
        self, vmid: int, vm_type: VMType, **config: Any
    ) -> None:
        """
        Update VM/container configuration.

        Args:
            vmid: VM ID
            vm_type: VM type
            **config: Configuration parameters
        """
        if vm_type == VMType.QEMU:
            await self._node_api.qemu(vmid).config.put(**config)
        else:
            await self._node_api.lxc(vmid).config.put(**config)

    async def create_vm(
        self, vmid: int, vm_type: VMType = VMType.QEMU, **config: Any
    ) -> str:
        """
        Create a new VM or container.

        Args:
            vmid: VM ID
            vm_type: VM type
            **config: VM configuration parameters

        Returns:
            Task ID (UPID)
        """
        config["vmid"] = vmid
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu.post(**config)
        else:
            return await self._node_api.lxc.post(**config)

    async def delete_vm(
        self,
        vmid: int,
        vm_type: VMType,
        purge: bool = False,
        destroy_unreferenced_disks: bool = False,
    ) -> str:
        """
        Delete a VM or container.

        Args:
            vmid: VM ID
            vm_type: VM type
            purge: Remove VM from all pools and backup jobs
            destroy_unreferenced_disks: Destroy disks not referenced in config

        Returns:
            Task ID (UPID)
        """
        params = {}
        if purge:
            params["purge"] = 1
        if destroy_unreferenced_disks:
            params["destroy-unreferenced-disks"] = 1

        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).delete(**params)
        else:
            return await self._node_api.lxc(vmid).delete(**params)

    # VM Status Control
    async def start_vm(self, vmid: int, vm_type: VMType) -> str:
        """
        Start a VM or container.

        Args:
            vmid: VM ID
            vm_type: VM type

        Returns:
            Task ID (UPID)
        """
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).status.start.post()
        else:
            return await self._node_api.lxc(vmid).status.start.post()

    async def stop_vm(self, vmid: int, vm_type: VMType) -> str:
        """
        Stop a VM or container (hard stop).

        Args:
            vmid: VM ID
            vm_type: VM type

        Returns:
            Task ID (UPID)
        """
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).status.stop.post()
        else:
            return await self._node_api.lxc(vmid).status.stop.post()

    async def shutdown_vm(self, vmid: int, vm_type: VMType, timeout: int = 60) -> str:
        """
        Shutdown a VM or container (graceful shutdown).

        Args:
            vmid: VM ID
            vm_type: VM type
            timeout: Timeout in seconds

        Returns:
            Task ID (UPID)
        """
        params = {"timeout": timeout}
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).status.shutdown.post(**params)
        else:
            return await self._node_api.lxc(vmid).status.shutdown.post(**params)

    async def reboot_vm(self, vmid: int, vm_type: VMType, timeout: int = 60) -> str:
        """
        Reboot a VM or container.

        Args:
            vmid: VM ID
            vm_type: VM type
            timeout: Timeout in seconds

        Returns:
            Task ID (UPID)
        """
        params = {"timeout": timeout}
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).status.reboot.post(**params)
        else:
            return await self._node_api.lxc(vmid).status.reboot.post(**params)

    async def reset_vm(self, vmid: int) -> str:
        """
        Reset a QEMU VM (hard reset).

        Args:
            vmid: VM ID

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.qemu(vmid).status.reset.post()

    async def suspend_vm(self, vmid: int) -> str:
        """
        Suspend a QEMU VM.

        Args:
            vmid: VM ID

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.qemu(vmid).status.suspend.post()

    async def resume_vm(self, vmid: int) -> str:
        """
        Resume a suspended QEMU VM.

        Args:
            vmid: VM ID

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.qemu(vmid).status.resume.post()

    # VM Operations
    async def clone_vm(
        self,
        vmid: int,
        newid: int,
        vm_type: VMType,
        name: str | None = None,
        full: bool = True,
        target: str | None = None,
        pool: str | None = None,
    ) -> str:
        """
        Clone a VM or container.

        Args:
            vmid: Source VM ID
            newid: New VM ID
            vm_type: VM type
            name: New VM name
            full: Create a full copy (not linked)
            target: Target node
            pool: Add to this pool

        Returns:
            Task ID (UPID)
        """
        params = {"newid": newid}
        if name:
            params["name"] = name
        if full:
            params["full"] = 1
        if target:
            params["target"] = target
        if pool:
            params["pool"] = pool

        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).clone.post(**params)
        else:
            return await self._node_api.lxc(vmid).clone.post(**params)

    async def migrate_vm(
        self,
        vmid: int,
        vm_type: VMType,
        target: str,
        online: bool = False,
        with_local_disks: bool = False,
    ) -> str:
        """
        Migrate a VM or container to another node.

        Args:
            vmid: VM ID
            vm_type: VM type
            target: Target node
            online: Online migration (live migration)
            with_local_disks: Migrate local disks

        Returns:
            Task ID (UPID)
        """
        params = {"target": target}
        if online:
            params["online"] = 1
        if with_local_disks:
            params["with-local-disks"] = 1

        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).migrate.post(**params)
        else:
            return await self._node_api.lxc(vmid).migrate.post(**params)

    async def convert_to_template(self, vmid: int, vm_type: VMType) -> None:
        """
        Convert a VM or container to a template.

        Args:
            vmid: VM ID
            vm_type: VM type
        """
        if vm_type == VMType.QEMU:
            await self._node_api.qemu(vmid).template.post()
        else:
            await self._node_api.lxc(vmid).template.post()

    # Snapshot Management
    async def list_snapshots(self, vmid: int, vm_type: VMType) -> list[Snapshot]:
        """
        List VM/container snapshots.

        Args:
            vmid: VM ID
            vm_type: VM type

        Returns:
            List of Snapshot objects
        """
        if vm_type == VMType.QEMU:
            data: ResponseData = await self._node_api.qemu(vmid).snapshot.get()
        else:
            data: ResponseData = await self._node_api.lxc(vmid).snapshot.get()

        return [Snapshot.from_dict(s) for s in data]

    async def create_snapshot(
        self,
        vmid: int,
        vm_type: VMType,
        snapname: str,
        description: str | None = None,
        vmstate: bool = False,
    ) -> str:
        """
        Create a VM/container snapshot.

        Args:
            vmid: VM ID
            vm_type: VM type
            snapname: Snapshot name
            description: Snapshot description
            vmstate: Include VM state (memory)

        Returns:
            Task ID (UPID)
        """
        params = {"snapname": snapname}
        if description:
            params["description"] = description
        if vmstate:
            params["vmstate"] = 1

        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).snapshot.post(**params)
        else:
            return await self._node_api.lxc(vmid).snapshot.post(**params)

    async def delete_snapshot(
        self, vmid: int, vm_type: VMType, snapname: str, force: bool = False
    ) -> str:
        """
        Delete a VM/container snapshot.

        Args:
            vmid: VM ID
            vm_type: VM type
            snapname: Snapshot name
            force: Force deletion

        Returns:
            Task ID (UPID)
        """
        params = {}
        if force:
            params["force"] = 1

        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).snapshot(snapname).delete(**params)
        else:
            return await self._node_api.lxc(vmid).snapshot(snapname).delete(**params)

    async def rollback_snapshot(
        self, vmid: int, vm_type: VMType, snapname: str
    ) -> str:
        """
        Rollback to a snapshot.

        Args:
            vmid: VM ID
            vm_type: VM type
            snapname: Snapshot name

        Returns:
            Task ID (UPID)
        """
        if vm_type == VMType.QEMU:
            return await self._node_api.qemu(vmid).snapshot(snapname).rollback.post()
        else:
            return await self._node_api.lxc(vmid).snapshot(snapname).rollback.post()

    # QEMU Guest Agent
    async def agent_ping(self, vmid: int) -> dict[str, Any]:
        """
        Ping QEMU guest agent.

        Args:
            vmid: VM ID

        Returns:
            Ping response
        """
        return await self._node_api.qemu(vmid).agent.ping.post()

    async def agent_get_info(self, vmid: int) -> QemuAgentInfo:
        """
        Get guest agent info.

        Args:
            vmid: VM ID

        Returns:
            QemuAgentInfo object
        """
        data = await self._node_api.qemu(vmid).agent("get-info").get()
        return QemuAgentInfo.from_dict(data)

    async def agent_get_osinfo(self, vmid: int) -> QemuAgentOSInfo:
        """
        Get OS information via guest agent.

        Args:
            vmid: VM ID

        Returns:
            QemuAgentOSInfo object
        """
        data = await self._node_api.qemu(vmid).agent("get-osinfo").get()
        return QemuAgentOSInfo.from_dict(data)

    async def agent_get_fsinfo(self, vmid: int) -> list[QemuAgentFSInfo]:
        """
        Get filesystem information via guest agent.

        Args:
            vmid: VM ID

        Returns:
            List of QemuAgentFSInfo objects
        """
        result = await self._node_api.qemu(vmid).agent("get-fsinfo").get()
        fs_list = result.get("result", [])
        return [QemuAgentFSInfo.from_dict(fs) for fs in fs_list]

    async def agent_exec(
        self, vmid: int, command: str | list[str], input_data: str | None = None
    ) -> QemuAgentExecResult:
        """
        Execute command via guest agent.

        Args:
            vmid: VM ID
            command: Command to execute (string or list of args)
            input_data: Input data to pass to command

        Returns:
            QemuAgentExecResult object with PID
        """
        params = {}
        if isinstance(command, str):
            params["command"] = command
        else:
            params["command"] = command
        if input_data:
            params["input-data"] = input_data

        data = await self._node_api.qemu(vmid).agent.exec.post(**params)
        return QemuAgentExecResult.from_dict(data)

    async def agent_exec_status(self, vmid: int, pid: int) -> QemuAgentExecResult:
        """
        Get command execution status via guest agent.

        Args:
            vmid: VM ID
            pid: Process ID from agent_exec

        Returns:
            QemuAgentExecResult object with execution status
        """
        data = await self._node_api.qemu(vmid).agent("exec-status").get(pid=pid)
        return QemuAgentExecResult.from_dict(data)

    async def agent_shutdown(self, vmid: int) -> None:
        """
        Shutdown guest via agent.

        Args:
            vmid: VM ID
        """
        await self._node_api.qemu(vmid).agent.shutdown.post()

    # Storage
    async def list_storage(self) -> list[dict[str, Any]]:
        """
        List storage on this node.

        Returns:
            List of storage entries
        """
        return await self._node_api.storage.get()

    async def get_storage_status(self, storage: str) -> dict[str, Any]:
        """
        Get storage status.

        Args:
            storage: Storage ID

        Returns:
            Storage status
        """
        return await self._node_api.storage(storage).status.get()

    async def list_storage_content(
        self, storage: str, content: str | None = None, vmid: int | None = None
    ) -> list[StorageContent]:
        """
        List storage content.

        Args:
            storage: Storage ID
            content: Content type filter (images, iso, vztmpl, backup, rootdir)
            vmid: Filter by VM ID

        Returns:
            List of StorageContent objects
        """
        params = {}
        if content:
            params["content"] = content
        if vmid:
            params["vmid"] = vmid

        data: ResponseData = await self._node_api.storage(storage).content.get(**params)
        return [StorageContent.from_dict(c) for c in data]

    async def delete_storage_content(self, storage: str, volid: str) -> str:
        """
        Delete storage content.

        Args:
            storage: Storage ID
            volid: Volume ID

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.storage(storage).content(volid).delete()

    async def upload_to_storage(
        self,
        storage: str,
        content: str,
        filename: str,
        file_data: bytes,
    ) -> str:
        """
        Upload file to storage.

        Args:
            storage: Storage ID
            content: Content type (iso, vztmpl)
            filename: Filename
            file_data: File data

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.storage(storage).upload.post(
            content=content, filename=filename, file=file_data
        )

    # Services
    async def list_services(self) -> list[Service]:
        """
        List system services.

        Returns:
            List of Service objects
        """
        data: ResponseData = await self._node_api.services.get()
        return [Service.from_dict(s) for s in data]

    async def get_service_state(self, service: str) -> Service:
        """
        Get service state.

        Args:
            service: Service name

        Returns:
            Service object
        """
        data: ResponseData = await self._node_api.services(service).state.get()
        return Service.from_dict(data)

    async def start_service(self, service: str) -> None:
        """
        Start a service.

        Args:
            service: Service name
        """
        await self._node_api.services(service).start.post()

    async def stop_service(self, service: str) -> None:
        """
        Stop a service.

        Args:
            service: Service name
        """
        await self._node_api.services(service).stop.post()

    async def restart_service(self, service: str) -> None:
        """
        Restart a service.

        Args:
            service: Service name
        """
        await self._node_api.services(service).restart.post()

    async def reload_service(self, service: str) -> None:
        """
        Reload a service.

        Args:
            service: Service name
        """
        await self._node_api.services(service).reload.post()

    # Tasks
    async def list_tasks(
        self,
        vmid: int | None = None,
        errors: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        List node tasks.

        Args:
            vmid: Filter by VM ID
            errors: Only show errors
            limit: Limit results

        Returns:
            List of task entries
        """
        params = {}
        if vmid:
            params["vmid"] = vmid
        if errors:
            params["errors"] = 1
        if limit:
            params["limit"] = limit

        return await self._node_api.tasks.get(**params)

    async def get_task_status(self, upid: str) -> dict[str, Any]:
        """
        Get task status.

        Args:
            upid: Task ID (UPID)

        Returns:
            Task status
        """
        return await self._node_api.tasks(upid).status.get()

    async def get_task_log(
        self, upid: str, start: int = 0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get task log.

        Args:
            upid: Task ID (UPID)
            start: Start line
            limit: Number of lines

        Returns:
            List of log entries
        """
        return await self._node_api.tasks(upid).log.get(start=start, limit=limit)

    async def stop_task(self, upid: str) -> None:
        """
        Stop a task.

        Args:
            upid: Task ID (UPID)
        """
        await self._node_api.tasks(upid).delete()

    # Backup
    async def backup_vm(
        self,
        vmid: int,
        storage: str,
        mode: str = "snapshot",
        compress: str = "zstd",
        remove: bool = False,
        notes: str | None = None,
    ) -> str:
        """
        Backup a VM or container.

        Args:
            vmid: VM ID
            storage: Target storage
            mode: Backup mode (snapshot, suspend, stop)
            compress: Compression (0, lzo, gzip, zstd)
            remove: Remove old backups
            notes: Backup notes

        Returns:
            Task ID (UPID)
        """
        params = {
            "vmid": vmid,
            "storage": storage,
            "mode": mode,
            "compress": compress,
        }
        if remove:
            params["remove"] = 1
        if notes:
            params["notes"] = notes

        return await self._node_api.vzdump.post(**params)

    # Network
    async def list_network_interfaces(self) -> list[NetworkInterface]:
        """
        List network interfaces.

        Returns:
            List of NetworkInterface objects
        """
        data: ResponseData = await self._node_api.network.get()
        return [NetworkInterface.from_dict(iface) for iface in data]

    async def get_network_interface(self, iface: str) -> NetworkInterface:
        """
        Get network interface config.

        Args:
            iface: Interface name

        Returns:
            NetworkInterface object
        """
        data = await self._node_api.network(iface).get()
        return NetworkInterface.from_dict(data)

    async def create_network_interface(
        self,
        iface: str,
        type: str,
        autostart: bool | None = None,
        address: str | None = None,
        netmask: str | None = None,
        gateway: str | None = None,
        bridge_ports: str | None = None,
        bridge_vlan_aware: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Create network device configuration.

        Args:
            iface: Interface name
            type: Network interface type (bridge, bond, eth, alias, vlan, OVSBridge, etc.)
            autostart: Automatically start interface on boot
            address: IP address
            netmask: Network mask
            gateway: Default gateway
            bridge_ports: Bridge ports (for bridge type)
            bridge_vlan_aware: Enable VLAN aware bridge
            **kwargs: Additional interface-specific parameters
        """
        params = {"iface": iface, "type": type}
        if autostart is not None:
            params["autostart"] = 1 if autostart else 0
        if address:
            params["address"] = address
        if netmask:
            params["netmask"] = netmask
        if gateway:
            params["gateway"] = gateway
        if bridge_ports:
            params["bridge_ports"] = bridge_ports
        if bridge_vlan_aware is not None:
            params["bridge_vlan_aware"] = 1 if bridge_vlan_aware else 0

        params.update(kwargs)
        await self._node_api.network.post(**params)

    async def update_network_interface(
        self,
        iface: str,
        autostart: bool | None = None,
        address: str | None = None,
        netmask: str | None = None,
        gateway: str | None = None,
        bridge_ports: str | None = None,
        comments: str | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Update network device configuration.

        Args:
            iface: Interface name
            autostart: Automatically start interface on boot
            address: IP address
            netmask: Network mask
            gateway: Default gateway
            bridge_ports: Bridge ports
            comments: Comments
            **kwargs: Additional parameters
        """
        params = {}
        if autostart is not None:
            params["autostart"] = 1 if autostart else 0
        if address:
            params["address"] = address
        if netmask:
            params["netmask"] = netmask
        if gateway:
            params["gateway"] = gateway
        if bridge_ports:
            params["bridge_ports"] = bridge_ports
        if comments:
            params["comments"] = comments

        params.update(kwargs)
        await self._node_api.network(iface).put(**params)

    async def delete_network_interface(self, iface: str) -> None:
        """
        Delete network device configuration.

        Args:
            iface: Interface name
        """
        await self._node_api.network(iface).delete()

    async def reload_network_configuration(self) -> str:
        """
        Reload network configuration.

        Returns:
            Task ID (UPID)
        """
        return await self._node_api.network.put()

    async def revert_network_configuration(self) -> None:
        """
        Revert network configuration changes.
        """
        await self._node_api.network.delete()

    # Certificates
    async def get_certificates_info(self) -> list[Certificate]:
        """
        Get information about node's certificates.

        Returns:
            List of Certificate objects
        """
        data: ResponseData = await self._node_api.certificates.info.get()
        return [Certificate.from_dict(cert) for cert in data]

    async def order_acme_certificate(
        self,
        force: bool = False,
    ) -> str:
        """
        Order a new certificate from ACME-compatible CA.

        Args:
            force: Force renewal even if certificate is not due

        Returns:
            Task ID (UPID)
        """
        params = {}
        if force:
            params["force"] = 1

        return await self._node_api.certificates.acme.certificate.post(**params)

    async def renew_acme_certificate(
        self,
        force: bool = False,
    ) -> str:
        """
        Renew existing certificate from CA.

        Args:
            force: Force renewal even if certificate is not due

        Returns:
            Task ID (UPID)
        """
        params = {}
        if force:
            params["force"] = 1

        return await self._node_api.certificates.acme.certificate.put(**params)

    async def revoke_acme_certificate(self) -> str:
        """
        Revoke existing certificate from CA.

        Returns:
            Success message
        """
        return await self._node_api.certificates.acme.certificate.delete()

    async def upload_custom_certificate(
        self,
        certificates: str,
        key: str | None = None,
        force: bool = False,
        restart: bool = False,
    ) -> list[Certificate]:
        """
        Upload or update custom certificate chain and key.

        Args:
            certificates: PEM encoded certificate (chain)
            key: PEM encoded private key
            force: Overwrite existing custom certificate
            restart: Restart pveproxy service

        Returns:
            List of Certificate objects
        """
        params = {"certificates": certificates}
        if key:
            params["key"] = key
        if force:
            params["force"] = 1
        if restart:
            params["restart"] = 1

        data: ResponseData = await self._node_api.certificates.custom.post(**params)
        return [Certificate.from_dict(cert) for cert in data]

    async def delete_custom_certificate(self, restart: bool = False) -> None:
        """
        DELETE custom certificate chain and key.

        Args:
            restart: Restart pveproxy service
        """
        params = {}
        if restart:
            params["restart"] = 1

        await self._node_api.certificates.custom.delete(**params)

    # APT Package Management
    async def list_apt_updates(self) -> list[APTUpdate]:
        """
        List available APT updates.

        Returns:
            List of APTUpdate objects
        """
        data: ResponseData = await self._node_api.apt.update.get()
        return [APTUpdate.from_dict(pkg) for pkg in data]

    async def update_apt_database(
        self,
        notify: bool = False,
        quiet: bool = False,
    ) -> str:
        """
        Resynchronize package index files from sources (apt-get update).

        Args:
            notify: Send notification mail about new packages
            quiet: Only print errors

        Returns:
            Task ID (UPID)
        """
        params = {}
        if notify:
            params["notify"] = 1
        if quiet:
            params["quiet"] = 1

        return await self._node_api.apt.update.post(**params)

    async def get_package_changelog(
        self,
        name: str,
        version: str | None = None,
    ) -> str:
        """
        Get package changelogs.

        Args:
            name: Package name
            version: Package version

        Returns:
            Changelog text
        """
        params = {"name": name}
        if version:
            params["version"] = version

        return await self._node_api.apt.changelog.get(**params)

    async def get_package_versions(self) -> list[dict[str, Any]]:
        """
        Get package information for important Proxmox packages.

        Returns:
            List of package info dicts
        """
        return await self._node_api.apt.versions.get()

    async def get_apt_repositories(self) -> dict[str, Any]:
        """
        Get APT repository information.

        Returns:
            Repository configuration
        """
        return await self._node_api.apt.repositories.get()

    async def add_apt_repository(
        self,
        handle: str,
        digest: str | None = None,
    ) -> None:
        """
        Add a standard repository to the configuration.

        Args:
            handle: Handle to identify the repository
            digest: Digest to detect modifications
        """
        params = {"handle": handle}
        if digest:
            params["digest"] = digest

        await self._node_api.apt.repositories.put(**params)

    async def change_apt_repository(
        self,
        index: int,
        digest: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        """
        Change the properties of a repository.

        Args:
            index: Index of the repository
            digest: Digest to detect modifications
            enabled: Enable/disable the repository
        """
        params = {"index": index}
        if digest:
            params["digest"] = digest
        if enabled is not None:
            params["enabled"] = 1 if enabled else 0

        await self._node_api.apt.repositories.post(**params)

    # Subscription Management
    async def get_subscription(self) -> Subscription:
        """
        Read subscription info.

        Returns:
            Subscription object
        """
        data = await self._node_api.subscription.get()
        return Subscription.from_dict(data)

    async def set_subscription_key(self, key: str) -> None:
        """
        Set subscription key.

        Args:
            key: Subscription key
        """
        await self._node_api.subscription.put(key=key)

    async def update_subscription(self, force: bool = False) -> None:
        """
        Update subscription info.

        Args:
            force: Force update even if subscription is not valid
        """
        params = {}
        if force:
            params["force"] = 1

        await self._node_api.subscription.post(**params)

    async def delete_subscription_key(self) -> None:
        """
        Delete subscription key of this node.
        """
        await self._node_api.subscription.delete()

    # System
    async def reboot_node(self) -> str:
        """
        Reboot the node.

        Returns:
            Success message
        """
        return await self._node_api.status.post(command="reboot")

    async def shutdown_node(self) -> str:
        """
        Shutdown the node.

        Returns:
            Success message
        """
        return await self._node_api.status.post(command="shutdown")
