"""
SDNManager Example - Software-Defined Networking

This example demonstrates SDN configuration including VNets, zones,
controllers, IPAM, and DNS.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import SDNManager, ZoneType, ControllerType, IPAMType


async def main():
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )
    sdn = SDNManager(proxmox)

    print("=" * 60)
    print("SDNManager Examples - Software-Defined Networking")
    print("=" * 60)

    # CREATE VXLAN ZONE
    print("\n[1] CREATE SDN ZONE")
    print("-" * 60)
    await sdn.create_zone("zone-vxlan", ZoneType.VXLAN, bridge="vmbr0", mtu=1450)
    print("Created VXLAN zone")

    await sdn.create_zone("zone-vlan", ZoneType.VLAN, bridge="vmbr1")
    print("Created VLAN zone")

    # LIST ZONES
    zones = await sdn.list_zones()
    print(f"\nZones: {len(zones)}")
    for zone in zones:
        print(f"  - {zone.zone} ({zone.type})")

    # CREATE VNETS
    print("\n[2] CREATE VIRTUAL NETWORKS")
    print("-" * 60)
    await sdn.create_vnet("vnet100", "zone-vxlan", tag=100, alias="Production")
    print("Created VNet 100")

    await sdn.create_vnet("vnet200", "zone-vlan", tag=200, alias="Development")
    print("Created VNet 200")

    # LIST VNETS
    vnets = await sdn.list_vnets()
    print(f"\nVNets: {len(vnets)}")
    for vnet in vnets:
        print(f"  - {vnet.vnet}: {vnet.alias} (zone: {vnet.zone}, tag: {vnet.tag})")

    # CREATE SUBNETS
    print("\n[3] CREATE SUBNETS")
    print("-" * 60)
    await sdn.create_subnet("vnet100", "10.0.100.0/24", gateway="10.0.100.1", snat=True)
    print("Created subnet 10.0.100.0/24 in vnet100")

    await sdn.create_subnet("vnet200", "10.0.200.0/24", gateway="10.0.200.1")
    print("Created subnet 10.0.200.0/24 in vnet200")

    # CREATE BGP CONTROLLER
    print("\n[4] CREATE SDN CONTROLLER")
    print("-" * 60)
    await sdn.create_controller("bgp1", ControllerType.BGP, asn=65000, peers="192.168.1.1")
    print("Created BGP controller")

    # CREATE IPAM
    print("\n[5] CREATE IPAM")
    print("-" * 60)
    await sdn.create_ipam("ipam-pve", IPAMType.PVE)
    print("Created Proxmox built-in IPAM")

    # APPLY SDN CHANGES
    print("\n[6] APPLY SDN CONFIGURATION")
    print("-" * 60)
    task = await sdn.reload_sdn()
    print(f"Applying SDN changes... Task: {task}")

    print("\n" + "=" * 60)
    print("SDN CONFIGURATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
