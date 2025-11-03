"""
DiskManager Example - Disk Management and Storage Initialization

This example demonstrates disk operations including listing disks,
SMART monitoring, and creating LVM, ZFS, and directory storage.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import DiskManager, DiskType


async def main():
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )
    disks = DiskManager(proxmox, "pve-node1")

    print("=" * 60)
    print("DiskManager Examples - Disk Management")
    print("=" * 60)

    # LIST DISKS
    print("\n[1] LIST ALL DISKS")
    print("-" * 60)
    all_disks = await disks.list_disks()
    print(f"Total disks: {len(all_disks)}")
    for disk in all_disks[:5]:
        print(f"  - {disk.devpath}")
        print(f"    Model: {disk.model}")
        print(f"    Size: {disk.size:,} bytes ({disk.size / (1024**3):.1f} GB)")
        print(f"    Type: {disk.type}")
        if disk.serial:
            print(f"    Serial: {disk.serial}")
        if disk.health:
            print(f"    Health: {disk.health}")

    # LIST ONLY SSDs
    print("\n[2] LIST SSDs")
    print("-" * 60)
    ssds = await disks.list_disks(disk_type=DiskType.SSD)
    print(f"SSDs: {len(ssds)}")
    for ssd in ssds:
        print(f"  - {ssd.devpath}: {ssd.model}")

    # LIST ONLY HDDs
    print("\n[3] LIST HDDs")
    print("-" * 60)
    hdds = await disks.list_disks(disk_type=DiskType.HDD)
    print(f"HDDs: {len(hdds)}")
    for hdd in hdds:
        print(f"  - {hdd.devpath}: {hdd.model}")

    # GET UNUSED DISKS
    print("\n[4] GET UNUSED DISKS")
    print("-" * 60)
    unused = await disks.get_unused_disks()
    print(f"Unused disks: {len(unused)}")
    for disk in unused:
        print(f"  - {disk.devpath}: {disk.model} ({disk.size / (1024**3):.1f} GB)")

    # GET SMART INFO
    print("\n[5] GET SMART INFORMATION")
    print("-" * 60)
    try:
        smart = await disks.get_smart_info("/dev/sda")
        print(f"SMART Health: {smart.health}")
        print(f"Type: {smart.type}")
        if smart.attributes:
            print(f"Attributes: {len(smart.attributes)}")
            for attr in smart.attributes[:3]:
                print(f"  - {attr}")
    except Exception as e:
        print(f"Could not get SMART info: {e}")

    # CHECK DISK HEALTH
    print("\n[6] CHECK DISK HEALTH")
    print("-" * 60)
    try:
        health = await disks.check_disk_health("/dev/sda")
        print(f"Disk /dev/sda health: {health}")
    except Exception as e:
        print(f"Could not check health: {e}")

    # FIND DISK BY SERIAL
    print("\n[7] FIND DISK BY SERIAL")
    print("-" * 60)
    disk = await disks.get_disk_by_serial("WD-SERIAL123")
    if disk:
        print(f"Found disk: {disk.devpath} - {disk.model}")
    else:
        print("Disk not found")

    # CREATE LVM
    print("\n[8] CREATE LVM VOLUME GROUP")
    print("-" * 60)
    # result = await disks.create_lvm("vg_data", "/dev/sdb", add_storage=True)
    # print(f"Created LVM: {result}")

    # LIST LVM
    print("\n[9] LIST LVM VOLUME GROUPS")
    print("-" * 60)
    lvms = await disks.list_lvm()
    print(f"LVM Volume Groups: {len(lvms)}")
    for lvm in lvms:
        print(f"  - {lvm.vg}")
        print(f"    Size: {lvm.size:,} bytes")
        print(f"    Free: {lvm.free:,} bytes")

    # CREATE LVM-THIN
    print("\n[10] CREATE LVM-THIN POOL")
    print("-" * 60)
    # result = await disks.create_lvmthin("data", "/dev/sdc", add_storage=True)
    # print(f"Created LVM-thin: {result}")

    # LIST LVM-THIN
    thin_pools = await disks.list_lvmthin()
    print(f"LVM-thin pools: {len(thin_pools)}")

    # CREATE ZFS POOL
    print("\n[11] CREATE ZFS POOL")
    print("-" * 60)
    # Single disk
    # result = await disks.create_zfs(
    #     name="tank",
    #     devices="/dev/sdd",
    #     raidlevel="single",
    #     ashift=12,
    #     compression="lz4",
    #     add_storage=True,
    # )
    # print(f"Created ZFS pool: {result}")

    # Mirror
    # result = await disks.create_zfs(
    #     name="mirror-pool",
    #     devices="/dev/sde,/dev/sdf",
    #     raidlevel="mirror",
    #     ashift=12,
    #     add_storage=True,
    # )
    # print(f"Created ZFS mirror: {result}")

    # LIST ZFS POOLS
    print("\n[12] LIST ZFS POOLS")
    print("-" * 60)
    zfs_pools = await disks.list_zfs()
    print(f"ZFS pools: {len(zfs_pools)}")
    for pool in zfs_pools:
        print(f"  - {pool.name}")
        print(f"    Size: {pool.size:,} bytes")
        print(f"    Free: {pool.free:,} bytes")
        print(f"    Health: {pool.health}")

    # CREATE DIRECTORY STORAGE
    print("\n[13] CREATE DIRECTORY STORAGE")
    print("-" * 60)
    # result = await disks.create_directory(
    #     name="local-data",
    #     device="/dev/sdg",
    #     filesystem="ext4",
    #     add_storage=True,
    # )
    # print(f"Created directory storage: {result}")

    # LIST DIRECTORIES
    print("\n[14] LIST DIRECTORY MOUNTS")
    print("-" * 60)
    directories = await disks.list_directories()
    print(f"Mounted directories: {len(directories)}")
    for directory in directories:
        print(f"  - {directory.path}")
        if directory.device:
            print(f"    Device: {directory.device}")
        if directory.type:
            print(f"    Type: {directory.type}")

    # WIPE DISK (USE WITH CAUTION!)
    print("\n[15] WIPE DISK")
    print("-" * 60)
    # WARNING: This will erase all data on the disk!
    # task = await disks.wipe_disk("/dev/sdh")
    # print(f"Wiping disk... Task: {task}")

    # DISK TYPE EXAMPLES
    print("\n[16] DISK TYPE EXAMPLES")
    print("-" * 60)
    print("Disk types:")
    print(f"  - HDD: {DiskType.HDD.value}")
    print(f"  - SSD: {DiskType.SSD.value}")
    print(f"  - Unknown: {DiskType.UNKNOWN.value}")

    # PRACTICAL USE CASES
    print("\n[17] PRACTICAL USE CASES")
    print("-" * 60)

    print("\n[Use Case 1: Find best disks for VM storage]")
    ssd_disks = await disks.get_disks_by_type(DiskType.SSD)
    unused_ssds = [d for d in ssd_disks if not d.used]
    print(f"Available SSDs for VMs: {len(unused_ssds)}")

    print("\n[Use Case 2: Health monitoring]")
    all_disks = await disks.list_disks(skipsmart=False)
    unhealthy = [d for d in all_disks if d.health and d.health != "PASSED"]
    print(f"Unhealthy disks: {len(unhealthy)}")
    for disk in unhealthy:
        print(f"  WARNING:{disk.devpath}: {disk.health}")

    print("\n[Use Case 3: Check wearout (SSDs)]")
    ssds = await disks.get_disks_by_type(DiskType.SSD)
    for ssd in ssds[:3]:
        if ssd.wearout is not None:
            print(f"  {ssd.devpath}: {ssd.wearout}% wearout")

    # DELETE STORAGE (CLEANUP)
    print("\n[18] DELETE STORAGE")
    print("-" * 60)
    # Delete ZFS pool
    # await disks.delete_zfs("tank", cleanup_disks=True)
    # print("Deleted ZFS pool")

    # Delete LVM
    # await disks.delete_lvm("vg_data", cleanup_disks=True)
    # print("Deleted LVM volume group")

    print("\n" + "=" * 60)
    print("DISK MANAGEMENT SUMMARY")
    print("=" * 60)
    print("List all disks (with/without partitions)")
    print("Filter by disk type (HDD/SSD)")
    print("Get unused disks")
    print("SMART health monitoring")
    print("Find disks by serial number")
    print("Create LVM volume groups")
    print("Create LVM-thin pools")
    print("Create ZFS pools (single, mirror, raidz)")
    print("Create directory storage (format & mount)")
    print("List existing storage")
    print("Wipe disks")
    print("Delete storage (with cleanup)")
    print("\nUse Cases:")
    print("  - Disk health monitoring")
    print("  - SSD wearout tracking")
    print("  - Automated storage provisioning")
    print("  - Disk inventory management")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
