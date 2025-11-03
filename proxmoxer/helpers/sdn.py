"""
Software-Defined Networking (SDN) helpers for Proxmoxer.

Provides high-level async API for managing Proxmox SDN including
virtual networks (VNets), zones, controllers, IPAM, and DNS.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


class ZoneType(str, Enum):
    """SDN zone types."""

    VLAN = "vlan"
    VXLAN = "vxlan"
    QinQ = "qinq"
    EVPN = "evpn"
    SIMPLE = "simple"


class ControllerType(str, Enum):
    """SDN controller types."""

    EVPN = "evpn"
    BGP = "bgp"
    ISIS = "isis"


class IPAMType(str, Enum):
    """IPAM types."""

    PVE = "pve"
    NETBOX = "netbox"
    PHPIPAM = "phpipam"


@dataclass
class VNet:
    """Virtual Network."""

    vnet: str
    zone: str
    alias: str | None = None
    tag: int | None = None
    vlanaware: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VNet:
        """Create VNet from API response."""
        return cls(
            vnet=data["vnet"],
            zone=data["zone"],
            alias=data.get("alias"),
            tag=data.get("tag"),
            vlanaware=bool(data.get("vlanaware", 0)),
        )


@dataclass
class Zone:
    """SDN Zone."""

    zone: str
    type: str
    bridge: str | None = None
    nodes: str | None = None
    mtu: int | None = None
    ipam: str | None = None
    dns: str | None = None
    dnszone: str | None = None
    reversedns: str | None = None
    pending: bool | None = None
    state: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Zone:
        """Create Zone from API response."""
        return cls(
            zone=data["zone"],
            type=data["type"],
            bridge=data.get("bridge"),
            nodes=data.get("nodes"),
            mtu=data.get("mtu"),
            ipam=data.get("ipam"),
            dns=data.get("dns"),
            dnszone=data.get("dnszone"),
            reversedns=data.get("reversedns"),
            pending=bool(data.get("pending", 0)) if data.get("pending") is not None else None,
            state=data.get("state"),
        )


@dataclass
class Controller:
    """SDN Controller."""

    controller: str
    type: str
    asn: int | None = None
    peers: str | None = None
    bgp_multipath_as_path_relax: bool = False
    pending: bool | None = None
    state: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Controller:
        """Create Controller from API response."""
        return cls(
            controller=data["controller"],
            type=data["type"],
            asn=data.get("asn"),
            peers=data.get("peers"),
            bgp_multipath_as_path_relax=bool(data.get("bgp-multipath-as-path-relax", 0)),
            pending=bool(data.get("pending", 0)) if data.get("pending") is not None else None,
            state=data.get("state"),
        )


@dataclass
class IPAM:
    """IP Address Management configuration."""

    ipam: str
    type: str
    url: str | None = None
    token: str | None = None
    section: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> IPAM:
        """Create IPAM from API response."""
        return cls(
            ipam=data["ipam"],
            type=data["type"],
            url=data.get("url"),
            token=data.get("token"),
            section=data.get("section"),
        )


@dataclass
class DNS:
    """DNS configuration for SDN."""

    dns: str
    url: str
    key: str | None = None
    reversemaskv6: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DNS:
        """Create DNS from API response."""
        return cls(
            dns=data["dns"],
            url=data["url"],
            key=data.get("key"),
            reversemaskv6=data.get("reversemaskv6"),
        )


@dataclass
class Subnet:
    """SDN Subnet."""

    subnet: str
    type: str
    gateway: str | None = None
    snat: bool = False
    dhcp_range: str | None = None
    dhcp_dns_server: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Subnet:
        """Create Subnet from API response."""
        return cls(
            subnet=data.get("subnet", ""),
            type=data.get("type", "subnet"),
            gateway=data.get("gateway"),
            snat=bool(data.get("snat", 0)),
            dhcp_range=data.get("dhcp-range"),
            dhcp_dns_server=data.get("dhcp-dns-server"),
        )


class SDNManager:
    """
    High-level manager for Proxmox Software-Defined Networking.

    Provides methods for managing virtual networks, zones, controllers,
    IPAM, and DNS configuration.

    Example:
        >>> sdn = SDNManager(proxmox)
        >>> zones = await sdn.list_zones()
        >>> await sdn.create_zone("zone1", ZoneType.VXLAN, bridge="vmbr0")
        >>> await sdn.create_vnet("vnet100", "zone1", tag=100)
    """

    def __init__(self, proxmox: Any):
        """
        Initialize SDNManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    # VNets Management
    async def list_vnets(self) -> list[VNet]:
        """
        List all virtual networks.

        Returns:
            List of VNet objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.vnets.get()
        return [VNet.from_dict(v) for v in data]

    async def get_vnet(self, vnet: str) -> VNet:
        """
        Get virtual network details.

        Args:
            vnet: VNet ID

        Returns:
            VNet object
        """
        data: ResponseData = await self.proxmox.cluster.sdn.vnets(vnet).get()
        data["vnet"] = vnet
        return VNet.from_dict(data)

    async def create_vnet(
        self,
        vnet: str,
        zone: str,
        alias: str | None = None,
        tag: int | None = None,
        vlanaware: bool = False,
    ) -> None:
        """
        Create a virtual network.

        Args:
            vnet: VNet ID
            zone: Zone ID
            alias: Alias name
            tag: VLAN/VXLAN tag
            vlanaware: Enable VLAN awareness
        """
        params = {"vnet": vnet, "zone": zone}
        if alias:
            params["alias"] = alias
        if tag is not None:
            params["tag"] = tag
        if vlanaware:
            params["vlanaware"] = 1

        await self.proxmox.cluster.sdn.vnets.post(**params)

    async def update_vnet(
        self,
        vnet: str,
        alias: str | None = None,
        tag: int | None = None,
        zone: str | None = None,
        vlanaware: bool | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update virtual network.

        Args:
            vnet: VNet ID
            alias: Alias name
            tag: VLAN/VXLAN tag
            zone: Zone ID
            vlanaware: Enable VLAN awareness
            delete: List of properties to delete
        """
        params = {}
        if alias is not None:
            params["alias"] = alias
        if tag is not None:
            params["tag"] = tag
        if zone is not None:
            params["zone"] = zone
        if vlanaware is not None:
            params["vlanaware"] = 1 if vlanaware else 0
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.sdn.vnets(vnet).put(**params)

    async def delete_vnet(self, vnet: str) -> None:
        """
        Delete a virtual network.

        Args:
            vnet: VNet ID
        """
        await self.proxmox.cluster.sdn.vnets(vnet).delete()

    # Subnets
    async def list_subnets(self, vnet: str) -> list[Subnet]:
        """
        List subnets for a VNet.

        Args:
            vnet: VNet ID

        Returns:
            List of Subnet objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.vnets(vnet).subnets.get()
        return [Subnet.from_dict(s) for s in data]

    async def create_subnet(
        self,
        vnet: str,
        subnet: str,
        type: str = "subnet",
        gateway: str | None = None,
        snat: bool = False,
        dhcp_range: str | None = None,
        dhcp_dns_server: str | None = None,
    ) -> None:
        """
        Create a subnet in a VNet.

        Args:
            vnet: VNet ID
            subnet: Subnet CIDR (e.g., "10.0.0.0/24")
            type: Subnet type
            gateway: Gateway IP
            snat: Enable SNAT
            dhcp_range: DHCP range (e.g., "start-address=10.0.0.10,end-address=10.0.0.100")
            dhcp_dns_server: DHCP DNS server
        """
        params = {"subnet": subnet, "type": type}
        if gateway:
            params["gateway"] = gateway
        if snat:
            params["snat"] = 1
        if dhcp_range:
            params["dhcp-range"] = dhcp_range
        if dhcp_dns_server:
            params["dhcp-dns-server"] = dhcp_dns_server

        await self.proxmox.cluster.sdn.vnets(vnet).subnets.post(**params)

    async def delete_subnet(self, vnet: str, subnet: str) -> None:
        """
        Delete a subnet.

        Args:
            vnet: VNet ID
            subnet: Subnet CIDR
        """
        await self.proxmox.cluster.sdn.vnets(vnet).subnets(subnet).delete()

    # Zones Management
    async def list_zones(self) -> list[Zone]:
        """
        List all SDN zones.

        Returns:
            List of Zone objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.zones.get()
        return [Zone.from_dict(z) for z in data]

    async def get_zone(self, zone: str) -> Zone:
        """
        Get zone details.

        Args:
            zone: Zone ID

        Returns:
            Zone object
        """
        data: ResponseData = await self.proxmox.cluster.sdn.zones(zone).get()
        data["zone"] = zone
        return Zone.from_dict(data)

    async def create_zone(
        self,
        zone: str,
        type: ZoneType | str,
        bridge: str | None = None,
        nodes: str | None = None,
        mtu: int | None = None,
        ipam: str | None = None,
        dns: str | None = None,
        **options: Any,
    ) -> None:
        """
        Create an SDN zone.

        Args:
            zone: Zone ID
            type: Zone type
            bridge: Bridge name
            nodes: Comma-separated node list
            mtu: MTU
            ipam: IPAM ID
            dns: DNS ID
            **options: Additional zone-specific options
        """
        params = {"zone": zone}
        if isinstance(type, ZoneType):
            params["type"] = type.value
        else:
            params["type"] = type

        if bridge:
            params["bridge"] = bridge
        if nodes:
            params["nodes"] = nodes
        if mtu:
            params["mtu"] = mtu
        if ipam:
            params["ipam"] = ipam
        if dns:
            params["dns"] = dns

        params.update(options)
        await self.proxmox.cluster.sdn.zones.post(**params)

    async def update_zone(
        self,
        zone: str,
        bridge: str | None = None,
        nodes: str | None = None,
        mtu: int | None = None,
        ipam: str | None = None,
        dns: str | None = None,
        delete: str | None = None,
        **options: Any,
    ) -> None:
        """
        Update zone configuration.

        Args:
            zone: Zone ID
            bridge: Bridge name
            nodes: Node list
            mtu: MTU
            ipam: IPAM ID
            dns: DNS ID
            delete: List of properties to delete
            **options: Additional options
        """
        params = {}
        if bridge is not None:
            params["bridge"] = bridge
        if nodes is not None:
            params["nodes"] = nodes
        if mtu is not None:
            params["mtu"] = mtu
        if ipam is not None:
            params["ipam"] = ipam
        if dns is not None:
            params["dns"] = dns
        if delete:
            params["delete"] = delete

        params.update(options)
        await self.proxmox.cluster.sdn.zones(zone).put(**params)

    async def delete_zone(self, zone: str) -> None:
        """
        Delete a zone.

        Args:
            zone: Zone ID
        """
        await self.proxmox.cluster.sdn.zones(zone).delete()

    # Controllers Management
    async def list_controllers(self) -> list[Controller]:
        """
        List all SDN controllers.

        Returns:
            List of Controller objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.controllers.get()
        return [Controller.from_dict(c) for c in data]

    async def get_controller(self, controller: str) -> Controller:
        """
        Get controller details.

        Args:
            controller: Controller ID

        Returns:
            Controller object
        """
        data: ResponseData = await self.proxmox.cluster.sdn.controllers(controller).get()
        data["controller"] = controller
        return Controller.from_dict(data)

    async def create_controller(
        self,
        controller: str,
        type: ControllerType | str,
        asn: int | None = None,
        peers: str | None = None,
        **options: Any,
    ) -> None:
        """
        Create an SDN controller.

        Args:
            controller: Controller ID
            type: Controller type
            asn: BGP ASN
            peers: BGP peers
            **options: Additional controller-specific options
        """
        params = {"controller": controller}
        if isinstance(type, ControllerType):
            params["type"] = type.value
        else:
            params["type"] = type

        if asn is not None:
            params["asn"] = asn
        if peers:
            params["peers"] = peers

        params.update(options)
        await self.proxmox.cluster.sdn.controllers.post(**params)

    async def update_controller(
        self,
        controller: str,
        asn: int | None = None,
        peers: str | None = None,
        delete: str | None = None,
        **options: Any,
    ) -> None:
        """
        Update controller configuration.

        Args:
            controller: Controller ID
            asn: BGP ASN
            peers: BGP peers
            delete: List of properties to delete
            **options: Additional options
        """
        params = {}
        if asn is not None:
            params["asn"] = asn
        if peers is not None:
            params["peers"] = peers
        if delete:
            params["delete"] = delete

        params.update(options)
        await self.proxmox.cluster.sdn.controllers(controller).put(**params)

    async def delete_controller(self, controller: str) -> None:
        """
        Delete a controller.

        Args:
            controller: Controller ID
        """
        await self.proxmox.cluster.sdn.controllers(controller).delete()

    # IPAM Management
    async def list_ipams(self) -> list[IPAM]:
        """
        List all IPAM configurations.

        Returns:
            List of IPAM objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.ipams.get()
        return [IPAM.from_dict(i) for i in data]

    async def get_ipam(self, ipam: str) -> IPAM:
        """
        Get IPAM configuration.

        Args:
            ipam: IPAM ID

        Returns:
            IPAM object
        """
        data: ResponseData = await self.proxmox.cluster.sdn.ipams(ipam).get()
        data["ipam"] = ipam
        return IPAM.from_dict(data)

    async def create_ipam(
        self,
        ipam: str,
        type: IPAMType | str,
        url: str | None = None,
        token: str | None = None,
        section: str | None = None,
    ) -> None:
        """
        Create IPAM configuration.

        Args:
            ipam: IPAM ID
            type: IPAM type
            url: IPAM URL
            token: API token
            section: Section/namespace
        """
        params = {"ipam": ipam}
        if isinstance(type, IPAMType):
            params["type"] = type.value
        else:
            params["type"] = type

        if url:
            params["url"] = url
        if token:
            params["token"] = token
        if section:
            params["section"] = section

        await self.proxmox.cluster.sdn.ipams.post(**params)

    async def update_ipam(
        self,
        ipam: str,
        url: str | None = None,
        token: str | None = None,
        section: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update IPAM configuration.

        Args:
            ipam: IPAM ID
            url: IPAM URL
            token: API token
            section: Section/namespace
            delete: List of properties to delete
        """
        params = {}
        if url is not None:
            params["url"] = url
        if token is not None:
            params["token"] = token
        if section is not None:
            params["section"] = section
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.sdn.ipams(ipam).put(**params)

    async def delete_ipam(self, ipam: str) -> None:
        """
        Delete IPAM configuration.

        Args:
            ipam: IPAM ID
        """
        await self.proxmox.cluster.sdn.ipams(ipam).delete()

    # DNS Management
    async def list_dns(self) -> list[DNS]:
        """
        List all DNS configurations.

        Returns:
            List of DNS objects
        """
        data: ResponseData = await self.proxmox.cluster.sdn.dns.get()
        return [DNS.from_dict(d) for d in data]

    async def get_dns(self, dns: str) -> DNS:
        """
        Get DNS configuration.

        Args:
            dns: DNS ID

        Returns:
            DNS object
        """
        data: ResponseData = await self.proxmox.cluster.sdn.dns(dns).get()
        data["dns"] = dns
        return DNS.from_dict(data)

    async def create_dns(
        self,
        dns: str,
        url: str,
        key: str | None = None,
        reversemaskv6: int | None = None,
    ) -> None:
        """
        Create DNS configuration.

        Args:
            dns: DNS ID
            url: DNS server URL
            key: API key
            reversemaskv6: Reverse DNS IPv6 prefix length
        """
        params = {"dns": dns, "url": url}
        if key:
            params["key"] = key
        if reversemaskv6 is not None:
            params["reversemaskv6"] = reversemaskv6

        await self.proxmox.cluster.sdn.dns.post(**params)

    async def update_dns(
        self,
        dns: str,
        url: str | None = None,
        key: str | None = None,
        reversemaskv6: int | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update DNS configuration.

        Args:
            dns: DNS ID
            url: DNS server URL
            key: API key
            reversemaskv6: Reverse DNS IPv6 prefix length
            delete: List of properties to delete
        """
        params = {}
        if url is not None:
            params["url"] = url
        if key is not None:
            params["key"] = key
        if reversemaskv6 is not None:
            params["reversemaskv6"] = reversemaskv6
        if delete:
            params["delete"] = delete

        await self.proxmox.cluster.sdn.dns(dns).put(**params)

    async def delete_dns(self, dns: str) -> None:
        """
        Delete DNS configuration.

        Args:
            dns: DNS ID
        """
        await self.proxmox.cluster.sdn.dns(dns).delete()

    # SDN Operations
    async def reload_sdn(self) -> str:
        """
        Apply pending SDN changes.

        Returns:
            Task ID (UPID)
        """
        return await self.proxmox.cluster.sdn.put()
