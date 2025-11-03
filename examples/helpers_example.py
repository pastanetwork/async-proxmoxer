"""
Comprehensive examples for using Proxmoxer helpers.

This file demonstrates how to use all the high-level helpers for managing
Proxmox VE infrastructure, including access control, cluster operations,
VMs, storage, and more.
"""
import asyncio

from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import (
    AccessManager,
    ClusterManager,
    NodeManager,
    PoolManager,
    StorageManager,
    VMType,
    HAState,
    BackupMode,
    BackupCompression,
    StorageType,
    ContentType,
)


async def access_examples(proxmox: ProxmoxAPI):
    """Examples for AccessManager."""
    print("\n=== Access Management Examples ===\n")

    access = AccessManager(proxmox)

    # List all users
    users = await access.list_users()
    print(f"Found {len(users)} users")
    for user in users[:3]:
        print(f"  - {user.userid} ({user.email})")

    # Create a new user
    await access.create_user(
        userid="testuser@pve",
        password="SecurePassword123!",
        email="testuser@example.com",
        firstname="Test",
        lastname="User",
        groups=["Administrators"],
        comment="Test user for demonstration",
    )
    print("Created user: testuser@pve")

    # Update user
    await access.update_user(
        userid="testuser@pve",
        email="newemail@example.com",
        comment="Updated test user",
    )
    print("Updated user email")

    # Change password
    await access.set_password("testuser@pve", "NewSecurePassword456!")
    print("Changed user password")

    # Create a group
    await access.create_group(
        groupid="developers",
        comment="Development team",
    )
    print("Created group: developers")

    # Create a role
    await access.create_role(
        roleid="CustomRole",
        privs=["VM.Audit", "VM.Console", "Datastore.Audit"],
    )
    print("Created role: CustomRole")

    # Set ACL
    await access.update_acl(
        path="/vms/100",
        roles=["CustomRole"],
        users=["testuser@pve"],
        propagate=True,
    )
    print("Set ACL for VM 100")

    # List API tokens for user
    tokens = await access.list_tokens("testuser@pve")
    print(f"User has {len(tokens)} API tokens")

    # Create API token
    token_info = await access.create_token(
        userid="testuser@pve",
        tokenid="automation",
        comment="Token for automation scripts",
        privsep=True,
    )
    print(f"Created API token: {token_info.get('value', 'N/A')}")

    # Get permissions
    perms = await access.get_permissions(userid="testuser@pve")
    print(f"User permissions: {len(perms)} entries")


async def cluster_examples(proxmox: ProxmoxAPI):
    """Examples for ClusterManager."""
    print("\n=== Cluster Management Examples ===\n")

    cluster = ClusterManager(proxmox)

    # Get cluster status
    status = await cluster.get_status()
    print(f"Cluster status: {status}")

    # List all resources
    resources = await cluster.list_resources()
    print(f"Total resources: {len(resources)}")

    vms = await cluster.list_resources(type="vm")
    print(f"VMs in cluster: {len(vms)}")

    nodes = await cluster.list_resources(type="node")
    print(f"Nodes in cluster: {len(nodes)}")

    # Get next free VMID
    next_vmid = await cluster.get_next_vmid()
    print(f"Next available VMID: {next_vmid}")

    # HA Management
    ha_resources = await cluster.list_ha_resources()
    print(f"HA resources: {len(ha_resources)}")

    # Create HA resource
    await cluster.create_ha_resource(
        sid="vm:100",
        state=HAState.STARTED,
        group="production",
        max_restart=3,
        max_relocate=2,
        comment="Production VM with HA",
    )
    print("Created HA resource for VM 100")

    # Create HA group
    await cluster.create_ha_group(
        group="production",
        nodes="node1:2,node2:1",
        comment="Production nodes with priorities",
        restricted=True,
    )
    print("Created HA group: production")

    # Get HA status
    ha_status = await cluster.get_ha_status()
    print(f"HA manager status: {ha_status}")

    # Backup Jobs
    backup_jobs = await cluster.list_backup_jobs()
    print(f"Backup jobs: {len(backup_jobs)}")

    # Create backup job
    await cluster.create_backup_job(
        id="backup-daily",
        schedule="02:00",
        storage="backup-storage",
        all=True,
        mode=BackupMode.SNAPSHOT,
        compress=BackupCompression.ZSTD,
        mailnotification="failure",
        mailto="admin@example.com",
        comment="Daily full backup",
    )
    print("Created backup job: backup-daily")

    # Replication Jobs
    replication_jobs = await cluster.list_replication_jobs()
    print(f"Replication jobs: {len(replication_jobs)}")

    # Create replication job
    await cluster.create_replication_job(
        id="100-0",
        target="node2",
        schedule="*/15",
        comment="Replicate VM 100 to node2 every 15 minutes",
    )
    print("Created replication job for VM 100")

    # ACME Management
    acme_accounts = await cluster.list_acme_accounts()
    print(f"ACME accounts: {len(acme_accounts)}")

    # Create ACME account
    await cluster.create_acme_account(
        name="letsencrypt",
        email="admin@example.com",
        directory="https://acme-v02.api.letsencrypt.org/directory",
    )
    print("Created ACME account: letsencrypt")

    # Get cluster options
    options = await cluster.get_options()
    print(f"Cluster options: {options}")


async def node_examples(proxmox: ProxmoxAPI):
    """Examples for NodeManager."""
    print("\n=== Node Management Examples ===\n")

    # Initialize node manager for specific node
    node = NodeManager(proxmox, "pve-node1")

    # Get node status
    status = await node.get_status()
    print(f"Node: {status.node}")
    print(f"  Status: {status.status}")
    print(f"  Uptime: {status.uptime}s")
    print(f"  CPU: {status.cpu:.1%} of {status.maxcpu} cores")
    print(f"  Memory: {status.mem}/{status.maxmem} bytes")

    # List all VMs
    all_vms = await node.list_vms()
    print(f"\nTotal VMs/Containers: {len(all_vms)}")

    # List only QEMU VMs
    qemu_vms = await node.list_vms(vm_type=VMType.QEMU)
    print(f"QEMU VMs: {len(qemu_vms)}")

    # List only LXC containers
    lxc_containers = await node.list_vms(vm_type=VMType.LXC)
    print(f"LXC Containers: {len(lxc_containers)}")

    # Get specific VM
    vm = await node.get_vm(100, vm_type=VMType.QEMU)
    print(f"\nVM {vm.vmid}: {vm.name}")
    print(f"  Status: {vm.status}")
    print(f"  CPU: {vm.cpu:.1%}")
    print(f"  Memory: {vm.mem}/{vm.maxmem} bytes")

    # Get VM config
    config = await node.get_vm_config(100, VMType.QEMU)
    print(f"  Config: {list(config.keys())[:5]}...")

    # Create a new VM
    task = await node.create_vm(
        vmid=999,
        vm_type=VMType.QEMU,
        name="test-vm",
        memory=2048,
        cores=2,
        sockets=1,
        net0="virtio,bridge=vmbr0",
        scsi0="local-lvm:32",
    )
    print(f"\nCreating VM 999... Task: {task}")

    # VM Operations
    await node.start_vm(100, VMType.QEMU)
    print("Started VM 100")

    await node.shutdown_vm(100, VMType.QEMU, timeout=60)
    print("Shutting down VM 100...")

    # Clone VM
    task = await node.clone_vm(
        vmid=100,
        newid=101,
        vm_type=VMType.QEMU,
        name="cloned-vm",
        full=True,
    )
    print(f"Cloning VM 100 to 101... Task: {task}")

    # Migrate VM
    task = await node.migrate_vm(
        vmid=100,
        vm_type=VMType.QEMU,
        target="node2",
        online=True,
    )
    print(f"Migrating VM 100 to node2... Task: {task}")

    # Snapshot Management
    snapshots = await node.list_snapshots(100, VMType.QEMU)
    print(f"\nVM 100 snapshots: {len(snapshots)}")

    task = await node.create_snapshot(
        vmid=100,
        vm_type=VMType.QEMU,
        snapname="before-upgrade",
        description="Snapshot before system upgrade",
        vmstate=True,
    )
    print(f"Creating snapshot... Task: {task}")

    # QEMU Guest Agent
    try:
        agent_info = await node.agent_get_osinfo(100)
        print(f"\nGuest OS: {agent_info}")

        fsinfo = await node.agent_get_fsinfo(100)
        print(f"Filesystems: {len(fsinfo)}")

        # Execute command via guest agent
        exec_result = await node.agent_exec(100, ["ls", "-la", "/tmp"])
        pid = exec_result.get("pid")
        print(f"Executed command, PID: {pid}")

        # Check execution status
        await asyncio.sleep(1)
        status = await node.agent_exec_status(100, pid)
        print(f"Command status: {status}")
    except Exception as e:
        print(f"Guest agent not available: {e}")

    # Storage Management
    storages = await node.list_storage()
    print(f"\nNode storage: {len(storages)}")

    storage_status = await node.get_storage_status("local")
    print(f"Local storage: {storage_status}")

    content = await node.list_storage_content("local", content="iso")
    print(f"ISO images: {len(content)}")

    # Service Management
    services = await node.list_services()
    print(f"\nServices: {len(services)}")

    pveproxy = await node.get_service_state("pveproxy")
    print(f"pveproxy: {pveproxy.state}")

    # Restart a service
    await node.restart_service("pveproxy")
    print("Restarted pveproxy")

    # Tasks
    tasks = await node.list_tasks(limit=10)
    print(f"\nRecent tasks: {len(tasks)}")

    if tasks:
        task_upid = tasks[0].get("upid")
        task_status = await node.get_task_status(task_upid)
        print(f"Task status: {task_status}")

    # Backup
    task = await node.backup_vm(
        vmid=100,
        storage="backup-storage",
        mode="snapshot",
        compress="zstd",
        notes="Manual backup before maintenance",
    )
    print(f"\nBackup started... Task: {task}")

    # Network interfaces
    interfaces = await node.list_network_interfaces()
    print(f"Network interfaces: {len(interfaces)}")


async def pool_examples(proxmox: ProxmoxAPI):
    """Examples for PoolManager."""
    print("\n=== Pool Management Examples ===\n")

    pool_mgr = PoolManager(proxmox)

    # List all pools
    pools = await pool_mgr.list_pools()
    print(f"Pools: {len(pools)}")
    for p in pools:
        print(f"  - {p.poolid}: {p.comment}")

    # Create a pool
    await pool_mgr.create_pool(
        poolid="production",
        comment="Production VMs and storage",
    )
    print("\nCreated pool: production")

    # Add VMs to pool
    await pool_mgr.add_vm_to_pool("production", 100)
    await pool_mgr.add_vm_to_pool("production", 101)
    print("Added VMs 100, 101 to production pool")

    # Add storage to pool
    await pool_mgr.add_storage_to_pool("production", "local-lvm")
    print("Added storage to production pool")

    # Get pool details
    pool = await pool_mgr.get_pool("production")
    print(f"\nPool: {pool.poolid}")
    print(f"  Comment: {pool.comment}")
    print(f"  Members: {len(pool.members or [])}")

    # Get organized members
    members = await pool_mgr.get_pool_members("production")
    print(f"  VMs: {len(members['vms'])}")
    print(f"  Storage: {len(members['storage'])}")

    # Update pool
    await pool_mgr.update_pool(
        poolid="production",
        comment="Production environment (updated)",
    )
    print("\nUpdated pool comment")

    # Remove VM from pool
    await pool_mgr.remove_vm_from_pool("production", 101)
    print("Removed VM 101 from pool")


async def storage_examples(proxmox: ProxmoxAPI):
    """Examples for StorageManager."""
    print("\n=== Storage Management Examples ===\n")

    storage_mgr = StorageManager(proxmox)

    # List all storage
    storages = await storage_mgr.list_storage()
    print(f"Total storage: {len(storages)}")
    for s in storages[:5]:
        print(f"  - {s.storage} ({s.type}): {s.content}")

    # List specific type
    nfs_storages = await storage_mgr.list_storage(type=StorageType.NFS)
    print(f"\nNFS storage: {len(nfs_storages)}")

    # Create NFS storage
    await storage_mgr.create_nfs_storage(
        storage="nfs-backup",
        server="192.168.1.100",
        export="/mnt/backup",
        content=[ContentType.BACKUP, ContentType.ISO],
        maxfiles=10,
        prune_backups="keep-last=7,keep-weekly=4,keep-monthly=3",
    )
    print("\nCreated NFS storage: nfs-backup")

    # Create CIFS storage
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

    # Create directory storage
    await storage_mgr.create_dir_storage(
        storage="local-backup",
        path="/mnt/local-backup",
        content=[ContentType.BACKUP],
        maxfiles=5,
        shared=False,
    )
    print("Created directory storage: local-backup")

    # Create LVM storage
    await storage_mgr.create_lvm_storage(
        storage="lvm-vms",
        vgname="vg_vms",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
        shared=False,
    )
    print("Created LVM storage: lvm-vms")

    # Create LVM-thin storage
    await storage_mgr.create_lvmthin_storage(
        storage="lvmthin-vms",
        vgname="vg_vms",
        thinpool="data",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
    )
    print("Created LVM-thin storage: lvmthin-vms")

    # Create ZFS storage
    await storage_mgr.create_zfs_storage(
        storage="zfs-vms",
        pool="rpool/vms",
        content=[ContentType.IMAGES, ContentType.ROOTDIR],
        sparse=True,
        blocksize="16k",
    )
    print("Created ZFS storage: zfs-vms")

    # Create Ceph RBD storage
    await storage_mgr.create_ceph_rbd_storage(
        storage="ceph-vms",
        pool="rbd",
        monhost="192.168.1.10,192.168.1.11,192.168.1.12",
        username="admin",
        content=[ContentType.IMAGES],
        krbd=True,
    )
    print("Created Ceph RBD storage: ceph-vms")

    # Create PBS storage
    await storage_mgr.create_pbs_storage(
        storage="pbs-backup",
        server="pbs.example.com",
        datastore="backup",
        username="backup@pbs",
        password="SecurePassword",
        fingerprint="AA:BB:CC:DD:...",
        content=[ContentType.BACKUP],
        maxfiles=10,
    )
    print("Created PBS storage: pbs-backup")

    # Update storage
    await storage_mgr.update_storage(
        storage="nfs-backup",
        maxfiles=15,
        prune_backups="keep-last=10,keep-weekly=5",
    )
    print("\nUpdated NFS storage settings")

    # Disable storage
    await storage_mgr.disable_storage("nfs-backup")
    print("Disabled NFS storage")

    # Enable storage
    await storage_mgr.enable_storage("nfs-backup")
    print("Enabled NFS storage")

    # Get storage details
    storage = await storage_mgr.get_storage("local")
    print(f"\nStorage: {storage.storage}")
    print(f"  Type: {storage.type}")
    print(f"  Content: {storage.content}")
    print(f"  Path: {storage.path}")
    print(f"  Enabled: {storage.enabled}")
    print(f"  Shared: {storage.shared}")


async def main():
    """Main example runner."""
    # Initialize Proxmox API connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    try:
        # Run examples
        print("=" * 60)
        print("Proxmoxer Helpers - Comprehensive Examples")
        print("=" * 60)

        await access_examples(proxmox)
        await cluster_examples(proxmox)
        await node_examples(proxmox)
        await pool_examples(proxmox)
        await storage_examples(proxmox)

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run async main
    asyncio.run(main())
