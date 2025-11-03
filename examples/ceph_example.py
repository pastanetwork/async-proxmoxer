"""
CephManager Example - Ceph Storage Operations

This example demonstrates Ceph cluster initialization and management
including OSDs, monitors, managers, pools, and CephFS.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import CephManager


async def main():
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )
    ceph = CephManager(proxmox, "pve-node1")

    print("=" * 60)
    print("CephManager Examples - Ceph Storage")
    print("=" * 60)

    # INITIALIZE CEPH
    print("\n[1] INITIALIZE CEPH")
    print("-" * 60)
    result = await ceph.init_ceph(
        network="10.0.0.0/24",
        cluster_network="10.0.1.0/24",
        size=3,
        min_size=2,
    )
    print(f"Initialized Ceph: {result}")

    # GET STATUS
    print("\n[2] GET CEPH STATUS")
    print("-" * 60)
    status = await ceph.get_status()
    print(f"Ceph Status: {status}")

    status_parsed = await ceph.get_status_parsed()
    print(f"\nHealth: {status_parsed.health}")
    print(f"Monitors: {status_parsed.monitors}")
    print(f"OSDs: {status_parsed.osds} (up: {status_parsed.osds_up}, in: {status_parsed.osds_in})")
    print(f"Pools: {status_parsed.pools}")

    # CREATE MONITOR
    print("\n[3] CREATE MONITOR")
    print("-" * 60)
    result = await ceph.create_monitor()
    print(f"Created monitor: {result}")

    # LIST MONITORS
    monitors = await ceph.list_monitors()
    print(f"\nMonitors: {len(monitors)}")
    for mon in monitors:
        print(f"  - {mon.name} ({mon.addr})")

    # CREATE MANAGER
    print("\n[4] CREATE MANAGER")
    print("-" * 60)
    result = await ceph.create_manager()
    print(f"Created manager: {result}")

    # CREATE OSD
    print("\n[5] CREATE OSD")
    print("-" * 60)
    task = await ceph.create_osd(
        device="/dev/sdb",
        db_device="/dev/nvme0n1",  # Optional: separate DB/WAL
        crush_device_class="ssd",
    )
    print(f"Creating OSD on /dev/sdb... Task: {task}")

    # LIST OSDS
    osds = await ceph.list_osds()
    print(f"\nOSDs: {len(osds)}")
    for osd in osds:
        print(f"  - OSD.{osd.id}: {osd.status}")
        print(f"    Weight: {osd.weight}, Host: {osd.host}")

    # CREATE POOL
    print("\n[6] CREATE CEPH POOL")
    print("-" * 60)
    result = await ceph.create_pool(
        name="vm-pool",
        size=3,
        min_size=2,
        pg_num=128,
        pg_autoscale_mode="on",
        application="rbd",
        add_storages=True,
    )
    print(f"Created pool: {result}")

    # LIST POOLS
    pools = await ceph.list_pools()
    print(f"\nPools: {len(pools)}")
    for pool in pools:
        print(f"  - {pool.pool_name}")
        print(f"    Size: {pool.size}, PGs: {pool.pg_num}")

    # CREATE CEPHFS
    print("\n[7] CREATE CEPHFS")
    print("-" * 60)
    result = await ceph.create_cephfs("cephfs", pg_num=128, add_storage=True)
    print(f"Created CephFS: {result}")

    # GET CRUSH MAP
    print("\n[8] GET CRUSH MAP")
    print("-" * 60)
    crush = await ceph.get_crush()
    print(f"CRUSH map length: {len(crush)} bytes")

    # GET FLAGS
    print("\n[9] GET/SET CEPH FLAGS")
    print("-" * 60)
    flags = await ceph.get_flags()
    print(f"Current flags: {flags}")

    # Set noout flag (useful for maintenance)
    # await ceph.set_flag("noout")
    # print("Set noout flag")

    # Unset noout flag
    # await ceph.unset_flag("noout")
    # print("Unset noout flag")

    print("\n" + "=" * 60)
    print("CEPH CONFIGURATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
