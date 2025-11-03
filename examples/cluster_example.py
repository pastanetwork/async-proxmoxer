"""
ClusterManager Example - Cluster Operations, HA, Backup, and Replication

This example demonstrates cluster-wide operations including high availability,
backup jobs, replication, and ACME certificate management.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import (
    ClusterManager,
    HAState,
    BackupMode,
    BackupCompression,
)


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    cluster = ClusterManager(proxmox)

    print("=" * 60)
    print("ClusterManager Examples - Cluster Operations")
    print("=" * 60)

    # ========================================
    # 1. CLUSTER STATUS & RESOURCES
    # ========================================
    print("\n[1] CLUSTER STATUS & RESOURCES")
    print("-" * 60)

    # Get cluster status
    status = await cluster.get_status()
    print("Cluster nodes:")
    for node_info in status:
        if node_info.get("type") == "node":
            print(f"  - {node_info['name']}: {node_info.get('online', 'unknown')}")
            print(f"    IP: {node_info.get('ip', 'N/A')}")
            print(f"    Level: {node_info.get('level', 'N/A')}")

    # List all resources
    print("\n[All Resources]")
    resources = await cluster.list_resources()
    print(f"Total resources: {len(resources)}")

    # Filter by type
    vms = await cluster.list_resources(type="vm")
    print(f"\nVMs in cluster: {len(vms)}")
    for vm in vms[:3]:
        print(f"  - VM {vm.id}: {vm.name or 'N/A'}")
        print(f"    Node: {vm.node}")
        print(f"    Status: {vm.status}")
        if vm.cpu:
            print(f"    CPU: {vm.cpu:.1%}")

    nodes = await cluster.list_resources(type="node")
    print(f"\nNodes: {len(nodes)}")
    for node in nodes:
        print(f"  - {node.id}: {node.status}")
        if node.cpu:
            print(f"    CPU: {node.cpu:.1%} of {node.maxcpu} cores")
            print(f"    Memory: {node.mem}/{node.maxmem} bytes")

    # Get next free VMID
    print("\n[Next Free VMID]")
    next_vmid = await cluster.get_next_vmid()
    print(f"Next available VMID: {next_vmid}")

    # Verify specific VMID is free
    try:
        specific_vmid = await cluster.get_next_vmid(vmid=999)
        print(f"VMID 999 is available: {specific_vmid}")
    except Exception as e:
        print(f"VMID 999 is not available: {e}")

    # ========================================
    # 2. HIGH AVAILABILITY (HA)
    # ========================================
    print("\n[2] HIGH AVAILABILITY MANAGEMENT")
    print("-" * 60)

    # Create HA group first
    print("\n[Create HA Group]")
    await cluster.create_ha_group(
        group="production",
        nodes="node1:2,node2:1",  # node1 has priority 2, node2 has priority 1
        nofailback=False,
        restricted=True,
        comment="Production nodes with failover",
    )
    print("Created HA group: production")

    # List HA groups
    ha_groups = await cluster.list_ha_groups()
    print(f"\nHA Groups: {len(ha_groups)}")
    for group in ha_groups:
        print(f"  - {group.group}")
        print(f"    Nodes: {group.nodes}")
        print(f"    Restricted: {group.restricted}")

    # Create HA resource
    print("\n[Create HA Resource]")
    await cluster.create_ha_resource(
        sid="vm:100",
        state=HAState.STARTED,
        group="production",
        max_restart=3,
        max_relocate=2,
        comment="Production database server",
    )
    print("Created HA resource: vm:100")

    await cluster.create_ha_resource(
        sid="vm:101",
        state=HAState.STARTED,
        group="production",
        max_restart=5,
        max_relocate=1,
        comment="Production web server",
    )
    print("Created HA resource: vm:101")

    # List HA resources
    ha_resources = await cluster.list_ha_resources()
    print(f"\nHA Resources: {len(ha_resources)}")
    for res in ha_resources:
        print(f"  - {res.sid}")
        print(f"    State: {res.state}")
        print(f"    Group: {res.group}")
        print(f"    Max restart: {res.max_restart}")

    # Update HA resource
    print("\n[Update HA Resource]")
    await cluster.update_ha_resource(
        sid="vm:100",
        max_restart=5,
        comment="Production database - Updated",
    )
    print("Updated HA resource settings")

    # Get HA status
    print("\n[HA Manager Status]")
    ha_status = await cluster.get_ha_status()
    print(f"HA Status: {ha_status}")

    # Migrate HA resource
    # await cluster.migrate_ha_resource("vm:100", node="node2")
    # print("Migrated vm:100 to node2")

    # ========================================
    # 3. BACKUP JOBS
    # ========================================
    print("\n[3] BACKUP JOB MANAGEMENT")
    print("-" * 60)

    # Create backup job
    print("\n[Create Backup Job]")
    await cluster.create_backup_job(
        id="backup-daily",
        schedule="02:00",
        storage="backup-storage",
        all=True,  # Backup all VMs
        mode=BackupMode.SNAPSHOT,
        compress=BackupCompression.ZSTD,
        mailnotification="failure",
        mailto="admin@example.com",
        prune_backups="keep-last=7,keep-weekly=4,keep-monthly=3",
        comment="Daily full backup of all VMs",
    )
    print("Created backup job: backup-daily")

    # Create selective backup job
    await cluster.create_backup_job(
        id="backup-critical",
        schedule="*/6",  # Every 6 hours
        storage="backup-storage",
        vmid="100,101,102",
        mode=BackupMode.SNAPSHOT,
        compress=BackupCompression.ZSTD,
        mailnotification="always",
        mailto="ops@example.com",
        comment="Critical VMs - frequent backup",
    )
    print("Created backup job: backup-critical")

    # List backup jobs
    backup_jobs = await cluster.list_backup_jobs()
    print(f"\nBackup Jobs: {len(backup_jobs)}")
    for job in backup_jobs:
        print(f"  - {job.id}")
        print(f"    Schedule: {job.schedule}")
        print(f"    Storage: {job.storage}")
        print(f"    Mode: {job.mode}")
        print(f"    Enabled: {job.enabled}")

    # Update backup job
    print("\n[Update Backup Job]")
    await cluster.update_backup_job(
        id="backup-daily",
        schedule="03:00",  # Change time
        prune_backups="keep-last=10,keep-weekly=5,keep-monthly=6",
    )
    print("Updated backup schedule and retention")

    # ========================================
    # 4. REPLICATION JOBS
    # ========================================
    print("\n[4] REPLICATION JOB MANAGEMENT")
    print("-" * 60)

    # Create replication job
    print("\n[Create Replication Job]")
    await cluster.create_replication_job(
        id="100-0",  # Format: <VMID>-<JOBNUM>
        target="node2",
        schedule="*/15",  # Every 15 minutes
        rate=100.0,  # 100 mbps rate limit
        comment="Replicate VM 100 to node2",
    )
    print("Created replication job: 100-0")

    # Create another replication job
    await cluster.create_replication_job(
        id="101-0",
        target="node2",
        schedule="*/30",
        comment="Replicate VM 101 to node2",
    )
    print("Created replication job: 101-0")

    # List replication jobs
    repl_jobs = await cluster.list_replication_jobs()
    print(f"\nReplication Jobs: {len(repl_jobs)}")
    for job in repl_jobs:
        print(f"  - {job.id}")
        print(f"    Target: {job.target}")
        print(f"    Schedule: {job.schedule}")
        if job.rate:
            print(f"    Rate limit: {job.rate} mbps")

    # Update replication job
    print("\n[Update Replication Job]")
    await cluster.update_replication_job(
        id="100-0",
        schedule="*/20",
        rate=50.0,
    )
    print("Updated replication schedule and rate")

    # ========================================
    # 5. ACME (Let's Encrypt) MANAGEMENT
    # ========================================
    print("\n[5] ACME CERTIFICATE MANAGEMENT")
    print("-" * 60)

    # List ACME directories
    print("\n[ACME Directories]")
    directories = await cluster.list_acme_directories()
    print(f"Available ACME directories: {len(directories)}")
    for dir_info in directories:
        print(f"  - {dir_info.get('name', 'N/A')}: {dir_info.get('url', 'N/A')}")

    # Get Terms of Service
    print("\n[ACME Terms of Service]")
    tos = await cluster.get_acme_tos()
    if tos.get("url"):
        print(f"TOS URL: {tos['url']}")

    # Create ACME account
    print("\n[Create ACME Account]")
    await cluster.create_acme_account(
        name="letsencrypt",
        email="admin@example.com",
        directory="https://acme-v02.api.letsencrypt.org/directory",
    )
    print("Created ACME account: letsencrypt")

    # List ACME accounts
    acme_accounts = await cluster.list_acme_accounts()
    print(f"\nACME Accounts: {len(acme_accounts)}")
    for account in acme_accounts:
        print(f"  - {account.name}")
        print(f"    Email: {account.email}")
        print(f"    Directory: {account.directory}")

    # List ACME plugins
    print("\n[ACME Plugins]")
    plugins = await cluster.list_acme_plugins()
    print(f"ACME plugins configured: {len(plugins)}")

    # ========================================
    # 6. CLUSTER OPTIONS
    # ========================================
    print("\n[6] CLUSTER OPTIONS")
    print("-" * 60)

    # Get cluster options
    options = await cluster.get_options()
    print("Current cluster options:")
    for key, value in list(options.items())[:5]:
        print(f"  {key}: {value}")

    # Set cluster options
    print("\n[Set Cluster Options]")
    await cluster.set_options(
        email_from="noreply@example.com",
        keyboard="en-us",
        language="en",
        max_workers=4,
        migration="secure,network=10.0.0.0/8",
    )
    print("Updated cluster options")

    # ========================================
    # 7. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[7] CLEANUP")
    print("-" * 60)

    # Delete replication job
    print("\n[Delete Replication Job]")
    await cluster.delete_replication_job("101-0", keep=False)
    print("Deleted replication job: 101-0")

    # Delete backup job
    print("\n[Delete Backup Job]")
    await cluster.delete_backup_job("backup-critical")
    print("Deleted backup job: backup-critical")

    # Delete HA resource
    print("\n[Delete HA Resource]")
    await cluster.delete_ha_resource("vm:101")
    print("Deleted HA resource: vm:101")

    # Delete HA group
    # await cluster.delete_ha_group("production")
    # print("Deleted HA group: production")

    # Delete ACME account
    # await cluster.delete_acme_account("letsencrypt")
    # print("Deleted ACME account: letsencrypt")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("CLUSTER MANAGEMENT SUMMARY")
    print("=" * 60)
    print("Cluster status and resource monitoring")
    print("Next VMID allocation")
    print("High Availability (HA) groups and resources")
    print("HA migration and relocation")
    print("Backup job scheduling with retention")
    print("VM replication between nodes")
    print("ACME/Let's Encrypt certificate management")
    print("Cluster-wide options configuration")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
