"""
StorageManager Example - Storage Configuration

This example demonstrates storage backend configuration for NFS, CIFS,
LVM, ZFS, Ceph, PBS, and more.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import StorageManager, StorageType, ContentType


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    storage_mgr = StorageManager(proxmox)

    print("=" * 60)
    print("StorageManager Examples - Storage Configuration")
    print("=" * 60)

    # ========================================
    # 1. LIST STORAGE
    # ========================================
    print("\n[1] LIST STORAGE")
    print("-" * 60)

    storages = await storage_mgr.list_storage()
    print(f"Total storage: {len(storages)}")
    for storage in storages:
        print(f"  - {storage.storage} ({storage.type})")
        print(f"    Content: {storage.content}")
        print(f"    Enabled: {storage.enabled}")

    # Filter by type
    nfs_storages = await storage_mgr.list_storage(type=StorageType.NFS)
    print(f"\nNFS storage: {len(nfs_storages)}")

    # ========================================
    # 2. NFS STORAGE
    # ========================================
    print("\n[2] NFS STORAGE")
    print("-" * 60)

    await storage_mgr.create_nfs_storage(
        storage="nfs-backup",
        server="192.168.1.100",
        export="/mnt/backup",
        content=[ContentType.BACKUP, ContentType.ISO, ContentType.VZTMPL],
        maxfiles=10,
        prune_backups="keep-last=7,keep-weekly=4,keep-monthly=3",
        options="vers=4",
    )
    print("Created NFS storage: nfs-backup")

    await storage_mgr.create_nfs_storage(
        storage="nfs-iso",
        server="192.168.1.100",
        export="/mnt/iso",
        content=[ContentType.ISO, ContentType.VZTMPL],
    )
    print("Created NFS storage: nfs-iso")

    # ========================================
    # 3. CIFS/SMB STORAGE
    # ========================================
    print("\n[3] CIFS/SMB STORAGE")
    print("-" * 60)

    await storage_mgr.create_cifs_storage(
        storage="cifs-share",
        server="192.168.1.101",
        share="proxmox",
        username="administrator",
        password="SecurePassword",
        domain="COMPANY",
        content=[ContentType.ISO, ContentType.VZTMPL],
    )
    print("Created CIFS storage: cifs-share")

    # ========================================
    # 4. DIRECTORY STORAGE
    # ========================================
    print("\n[4] DIRECTORY STORAGE")
    print("-" * 60)

    await storage_mgr.create_dir_storage(
        storage="local-backup",
        path="/mnt/local-backup",
        content=[ContentType.BACKUP],
        maxfiles=5,
        prune_backups="keep-last=5,keep-weekly=2",
        shared=False,
    )
    print("Created directory storage: local-backup")

    # ========================================
    # 5. LVM STORAGE
    # ========================================
    print("\n[5] LVM STORAGE")
    print("-" * 60)

    await storage_mgr.create_lvm_storage(
        storage="lvm-vms",
        vgname="vg_vms",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
        shared=False,
    )
    print("Created LVM storage: lvm-vms")

    # ========================================
    # 6. LVM-THIN STORAGE
    # ========================================
    print("\n[6] LVM-THIN STORAGE")
    print("-" * 60)

    await storage_mgr.create_lvmthin_storage(
        storage="lvmthin-vms",
        vgname="vg_vms",
        thinpool="data",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
    )
    print("Created LVM-thin storage: lvmthin-vms")

    # ========================================
    # 7. ZFS STORAGE
    # ========================================
    print("\n[7] ZFS STORAGE")
    print("-" * 60)

    await storage_mgr.create_zfs_storage(
        storage="zfs-vms",
        pool="rpool/vms",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
        sparse=True,
        blocksize="16k",
    )
    print("Created ZFS storage: zfs-vms")

    await storage_mgr.create_zfs_storage(
        storage="zfs-data",
        pool="rpool/data",
        content=[ContentType.IMAGES],
        sparse=False,
        blocksize="8k",
    )
    print("Created ZFS storage: zfs-data")

    # ========================================
    # 8. CEPH RBD STORAGE
    # ========================================
    print("\n[8] CEPH RBD STORAGE")
    print("-" * 60)

    await storage_mgr.create_ceph_rbd_storage(
        storage="ceph-vms",
        pool="rbd",
        monhost="192.168.1.10,192.168.1.11,192.168.1.12",
        username="admin",
        content=[ContentType.IMAGES],
        krbd=True,
    )
    print("Created Ceph RBD storage: ceph-vms")

    # ========================================
    # 9. PROXMOX BACKUP SERVER (PBS)
    # ========================================
    print("\n[9] PROXMOX BACKUP SERVER STORAGE")
    print("-" * 60)

    await storage_mgr.create_pbs_storage(
        storage="pbs-backup",
        server="pbs.example.com",
        datastore="backup",
        username="backup@pbs",
        password="SecurePassword",
        fingerprint="AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD",
        content=[ContentType.BACKUP],
        maxfiles=10,
        prune_backups="keep-last=10,keep-weekly=4,keep-monthly=6",
    )
    print("Created PBS storage: pbs-backup")

    # ========================================
    # 10. UPDATE STORAGE
    # ========================================
    print("\n[10] UPDATE STORAGE")
    print("-" * 60)

    await storage_mgr.update_storage(
        storage="nfs-backup",
        maxfiles=15,
        prune_backups="keep-last=10,keep-weekly=5,keep-monthly=6",
    )
    print("Updated NFS storage settings")

    await storage_mgr.update_storage(
        storage="local-backup",
        content=[ContentType.BACKUP, ContentType.SNIPPETS],
    )
    print("Updated directory storage content types")

    # ========================================
    # 11. ENABLE/DISABLE STORAGE
    # ========================================
    print("\n[11] ENABLE/DISABLE STORAGE")
    print("-" * 60)

    await storage_mgr.disable_storage("nfs-iso")
    print("Disabled NFS ISO storage")

    await storage_mgr.enable_storage("nfs-iso")
    print("Enabled NFS ISO storage")

    # ========================================
    # 12. GET STORAGE DETAILS
    # ========================================
    print("\n[12] GET STORAGE DETAILS")
    print("-" * 60)

    storage = await storage_mgr.get_storage("local")
    print(f"\nStorage: {storage.storage}")
    print(f"  Type: {storage.type}")
    print(f"  Content: {storage.content}")
    print(f"  Path: {storage.path}")
    print(f"  Enabled: {storage.enabled}")
    print(f"  Shared: {storage.shared}")

    # ========================================
    # 13. STORAGE TYPE EXAMPLES
    # ========================================
    print("\n[13] STORAGE TYPE EXAMPLES")
    print("-" * 60)

    print("\n[Content Types]")
    print(f"  Images: {ContentType.IMAGES.value}")
    print(f"  Rootdir: {ContentType.ROOTDIR.value}")
    print(f"  ISO: {ContentType.ISO.value}")
    print(f"  VZTmpl: {ContentType.VZTMPL.value}")
    print(f"  Backup: {ContentType.BACKUP.value}")
    print(f"  Snippets: {ContentType.SNIPPETS.value}")

    print("\n[Storage Types]")
    print(f"  NFS: {StorageType.NFS.value}")
    print(f"  CIFS: {StorageType.CIFS.value}")
    print(f"  LVM: {StorageType.LVM.value}")
    print(f"  LVM-Thin: {StorageType.LVMTHIN.value}")
    print(f"  ZFS: {StorageType.ZFS.value}")
    print(f"  Ceph RBD: {StorageType.CEPH_RBD.value}")
    print(f"  PBS: {StorageType.PBS.value}")

    # ========================================
    # 14. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[14] CLEANUP")
    print("-" * 60)

    storages_to_delete = [
        "nfs-iso",
        "cifs-share",
        "zfs-data",
    ]

    for storage_id in storages_to_delete:
        try:
            await storage_mgr.delete_storage(storage_id)
            print(f"Deleted storage: {storage_id}")
        except Exception as e:
            print(f"  Could not delete {storage_id}: {e}")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("STORAGE MANAGEMENT SUMMARY")
    print("=" * 60)
    print("List storage (all or by type)")
    print("Create NFS storage with options")
    print("Create CIFS/SMB storage with authentication")
    print("Create directory storage")
    print("Create LVM and LVM-thin storage")
    print("Create ZFS storage with options")
    print("Create Ceph RBD storage")
    print("Create Proxmox Backup Server storage")
    print("Update storage configuration")
    print("Enable/disable storage")
    print("Get storage details")
    print("Delete storage")
    print("\nSupported Storage Types:")
    print("  - NFS, CIFS, Directory")
    print("  - LVM, LVM-Thin")
    print("  - ZFS")
    print("  - Ceph RBD, CephFS")
    print("  - iSCSI, GlusterFS")
    print("  - Proxmox Backup Server (PBS)")
    print("  - BTRFS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
