"""
NodeManager Example - VM/Container Management and Node Operations

This example demonstrates node-specific operations including VM/container
lifecycle, snapshots, QEMU guest agent, storage, and services.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import NodeManager, VMType


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    node = NodeManager(proxmox, "pve-node1")

    print("=" * 60)
    print("NodeManager Examples - VM & Container Management")
    print("=" * 60)

    # ========================================
    # 1. NODE STATUS
    # ========================================
    print("\n[1] NODE STATUS & INFORMATION")
    print("-" * 60)

    # Get node status
    status = await node.get_status()
    print(f"Node: {status.node}")
    print(f"Status: {status.status}")
    print(f"Uptime: {status.uptime} seconds")
    print(f"CPU Usage: {status.cpu:.1%} of {status.maxcpu} cores")
    print(f"Memory: {status.mem:,} / {status.maxmem:,} bytes")
    print(f"Disk: {status.disk:,} / {status.maxdisk:,} bytes")

    # Get version
    version = await node.get_version()
    print(f"\nProxmox Version: {version.get('version', 'N/A')}")
    print(f"Release: {version.get('release', 'N/A')}")

    # Get time
    time_info = await node.get_time()
    print(f"\nNode time: {time_info.get('localtime', 'N/A')}")
    print(f"Timezone: {time_info.get('timezone', 'N/A')}")

    # ========================================
    # 2. LIST VMs AND CONTAINERS
    # ========================================
    print("\n[2] LIST VMs AND CONTAINERS")
    print("-" * 60)

    # List all VMs and containers
    all_vms = await node.list_vms()
    print(f"Total VMs/Containers: {len(all_vms)}")

    # List only QEMU VMs
    qemu_vms = await node.list_vms(vm_type=VMType.QEMU)
    print(f"\nQEMU VMs: {len(qemu_vms)}")
    for vm in qemu_vms[:3]:
        print(f"  - VM {vm.vmid}: {vm.name}")
        print(f"    Status: {vm.status}")
        if vm.cpu:
            print(f"    CPU: {vm.cpu:.1%}")
        if vm.mem and vm.maxmem:
            print(f"    Memory: {vm.mem:,} / {vm.maxmem:,}")

    # List only LXC containers
    lxc_containers = await node.list_vms(vm_type=VMType.LXC)
    print(f"\nLXC Containers: {len(lxc_containers)}")
    for ct in lxc_containers[:3]:
        print(f"  - CT {ct.vmid}: {ct.name}")
        print(f"    Status: {ct.status}")

    # ========================================
    # 3. CREATE AND MANAGE VM
    # ========================================
    print("\n[3] CREATE AND MANAGE VM")
    print("-" * 60)

    # Create QEMU VM
    print("\n[Create QEMU VM]")
    task = await node.create_vm(
        vmid=999,
        vm_type=VMType.QEMU,
        name="test-vm",
        memory=2048,
        cores=2,
        sockets=1,
        net0="virtio,bridge=vmbr0",
        scsi0="local-lvm:32",
        ostype="l26",  # Linux 2.6+
        description="Test VM created by async-proxmoxer",
    )
    print(f"Creating VM 999... Task: {task}")

    # Get VM details
    print("\n[Get VM Details]")
    vm = await node.get_vm(999, vm_type=VMType.QEMU)
    print(f"VM {vm.vmid}: {vm.name}")
    print(f"  Status: {vm.status}")
    print(f"  Type: {vm.type}")

    # Get VM config
    config = await node.get_vm_config(999, VMType.QEMU)
    print(f"  Config keys: {list(config.keys())[:5]}...")

    # Update VM config
    print("\n[Update VM Config]")
    await node.update_vm_config(
        vmid=999,
        vm_type=VMType.QEMU,
        memory=4096,
        cores=4,
        description="Updated VM configuration",
    )
    print("Updated VM configuration")

    # ========================================
    # 4. VM LIFECYCLE OPERATIONS
    # ========================================
    print("\n[4] VM LIFECYCLE OPERATIONS")
    print("-" * 60)

    # Start VM
    print("\n[Start VM]")
    task = await node.start_vm(999, VMType.QEMU)
    print(f"Started VM 999... Task: {task}")

    # Wait a bit
    await asyncio.sleep(2)

    # Get current status
    vm = await node.get_vm(999)
    print(f"VM Status: {vm.status}")

    # Shutdown VM (graceful)
    print("\n[Shutdown VM]")
    task = await node.shutdown_vm(999, VMType.QEMU, timeout=60)
    print(f"Shutting down VM 999... Task: {task}")

    # Stop VM (hard stop)
    # task = await node.stop_vm(999, VMType.QEMU)
    # print(f"Stopped VM 999... Task: {task}")

    # Reboot VM
    # task = await node.reboot_vm(999, VMType.QEMU, timeout=60)
    # print(f"Rebooting VM 999... Task: {task}")

    # Reset VM (hard reset - QEMU only)
    # task = await node.reset_vm(999)
    # print(f"Reset VM 999... Task: {task}")

    # Suspend VM (QEMU only)
    # task = await node.suspend_vm(999)
    # print(f"Suspended VM 999... Task: {task}")

    # Resume VM (QEMU only)
    # task = await node.resume_vm(999)
    # print(f"Resumed VM 999... Task: {task}")

    # ========================================
    # 5. VM OPERATIONS (CLONE, MIGRATE, TEMPLATE)
    # ========================================
    print("\n[5] VM OPERATIONS")
    print("-" * 60)

    # Clone VM
    print("\n[Clone VM]")
    task = await node.clone_vm(
        vmid=999,
        newid=1000,
        vm_type=VMType.QEMU,
        name="cloned-vm",
        full=True,  # Full clone (not linked)
        # target="node2",  # Optional: clone to another node
        # pool="production",  # Optional: add to pool
    )
    print(f"Cloning VM 999 to 1000... Task: {task}")

    # Migrate VM
    print("\n[Migrate VM]")
    # task = await node.migrate_vm(
    #     vmid=999,
    #     vm_type=VMType.QEMU,
    #     target="node2",
    #     online=True,  # Live migration
    #     with_local_disks=False,
    # )
    # print(f"Migrating VM 999 to node2... Task: {task}")

    # Convert to template
    # await node.convert_to_template(999, VMType.QEMU)
    # print("Converted VM 999 to template")

    # ========================================
    # 6. SNAPSHOT MANAGEMENT
    # ========================================
    print("\n[6] SNAPSHOT MANAGEMENT")
    print("-" * 60)

    # Create snapshot
    print("\n[Create Snapshot]")
    task = await node.create_snapshot(
        vmid=999,
        vm_type=VMType.QEMU,
        snapname="before-upgrade",
        description="Snapshot before system upgrade",
        vmstate=True,  # Include RAM state
    )
    print(f"Creating snapshot... Task: {task}")

    # List snapshots
    print("\n[List Snapshots]")
    snapshots = await node.list_snapshots(999, VMType.QEMU)
    print(f"Snapshots for VM 999: {len(snapshots)}")
    for snap in snapshots:
        print(f"  - {snap.name}")
        if snap.description:
            print(f"    Description: {snap.description}")
        if snap.snaptime:
            print(f"    Time: {snap.snaptime}")

    # Rollback to snapshot
    # task = await node.rollback_snapshot(999, VMType.QEMU, "before-upgrade")
    # print(f"Rolling back... Task: {task}")

    # Delete snapshot
    # task = await node.delete_snapshot(999, VMType.QEMU, "before-upgrade")
    # print(f"Deleting snapshot... Task: {task}")

    # ========================================
    # 7. QEMU GUEST AGENT
    # ========================================
    print("\n[7] QEMU GUEST AGENT")
    print("-" * 60)

    # Note: Guest agent must be installed and running in the VM
    try:
        # Ping agent
        print("\n[Ping Guest Agent]")
        await node.agent_ping(999)
        print("Guest agent is responsive")

        # Get OS info
        print("\n[Get OS Information]")
        os_info = await node.agent_get_osinfo(999)
        print(f"OS: {os_info}")

        # Get filesystem info
        print("\n[Get Filesystem Information]")
        fsinfo = await node.agent_get_fsinfo(999)
        print(f"Filesystems: {len(fsinfo)}")
        for fs in fsinfo[:3]:
            print(f"  - {fs}")

        # Execute command
        print("\n[Execute Command via Agent]")
        exec_result = await node.agent_exec(999, ["ls", "-la", "/tmp"])
        pid = exec_result.get("pid")
        print(f"Command executed, PID: {pid}")

        # Check execution status
        await asyncio.sleep(1)
        status = await node.agent_exec_status(999, pid)
        print(f"Command status: {status}")

    except Exception as e:
        print(f"Guest agent not available or error: {e}")
        print("Make sure qemu-guest-agent is installed and running in the VM")

    # ========================================
    # 8. STORAGE OPERATIONS
    # ========================================
    print("\n[8] STORAGE OPERATIONS")
    print("-" * 60)

    # List storage
    storages = await node.list_storage()
    print(f"Storage on node: {len(storages)}")
    for storage in storages[:3]:
        print(f"  - {storage.get('storage', 'N/A')}")
        print(f"    Type: {storage.get('type', 'N/A')}")

    # Get storage status
    print("\n[Storage Status]")
    status = await node.get_storage_status("local")
    print(f"Local storage:")
    print(f"  Active: {status.get('active', 'N/A')}")
    print(f"  Type: {status.get('type', 'N/A')}")

    # List storage content
    print("\n[Storage Content]")
    content = await node.list_storage_content("local", content="iso")
    print(f"ISO images: {len(content)}")
    for item in content[:3]:
        print(f"  - {item.volid}")
        print(f"    Size: {item.size:,} bytes")

    # ========================================
    # 9. SERVICE MANAGEMENT
    # ========================================
    print("\n[9] SERVICE MANAGEMENT")
    print("-" * 60)

    # List services
    services = await node.list_services()
    print(f"Services: {len(services)}")
    for service in services[:5]:
        print(f"  - {service.name}: {service.state}")

    # Get specific service
    print("\n[Get Service State]")
    pveproxy = await node.get_service_state("pveproxy")
    print(f"pveproxy: {pveproxy.state}")
    print(f"  Description: {pveproxy.desc}")

    # Restart service
    # await node.restart_service("pveproxy")
    # print("Restarted pveproxy")

    # ========================================
    # 10. TASK MANAGEMENT
    # ========================================
    print("\n[10] TASK MANAGEMENT")
    print("-" * 60)

    # List recent tasks
    tasks = await node.list_tasks(limit=10)
    print(f"Recent tasks: {len(tasks)}")
    for task_info in tasks[:3]:
        print(f"  - {task_info.get('type', 'N/A')}")
        print(f"    UPID: {task_info.get('upid', 'N/A')}")
        print(f"    Status: {task_info.get('status', 'N/A')}")

    # ========================================
    # 11. BACKUP
    # ========================================
    print("\n[11] BACKUP VM")
    print("-" * 60)

    # Backup VM
    print("\n[Create Backup]")
    task = await node.backup_vm(
        vmid=999,
        storage="local",
        mode="snapshot",
        compress="zstd",
        notes="Manual backup created by async-proxmoxer",
    )
    print(f"Backup started... Task: {task}")

    # ========================================
    # 12. NETWORK INTERFACES
    # ========================================
    print("\n[12] NETWORK INTERFACES")
    print("-" * 60)

    # List interfaces
    print("\n[List Network Interfaces]")
    interfaces = await node.list_network_interfaces()
    print(f"Network interfaces: {len(interfaces)}")
    for iface in interfaces[:3]:
        print(f"  - {iface.iface} ({iface.type})")
        if iface.address:
            print(f"    Address: {iface.address}/{iface.netmask or 'N/A'}")
        if iface.gateway:
            print(f"    Gateway: {iface.gateway}")
        print(f"    Autostart: {iface.autostart}")

    # Get specific interface
    print("\n[Get Interface Details]")
    try:
        vmbr0 = await node.get_network_interface("vmbr0")
        print(f"Interface: {vmbr0.iface}")
        print(f"  Type: {vmbr0.type}")
        print(f"  Address: {vmbr0.address or 'DHCP'}")
        if vmbr0.bridge_ports:
            print(f"  Bridge ports: {vmbr0.bridge_ports}")
    except Exception as e:
        print(f"  Error: {e}")

    # Create network interface (example - commented for safety)
    # print("\n[Create Bridge Interface]")
    # await node.create_network_interface(
    #     iface="vmbr10",
    #     type="bridge",
    #     address="192.168.10.1",
    #     netmask="255.255.255.0",
    #     autostart=True,
    #     bridge_ports="none",
    #     bridge_vlan_aware=True,
    #     comments="Test bridge created by async-proxmoxer",
    # )
    # print("Created bridge vmbr10")

    # Update interface (example)
    # print("\n[Update Interface]")
    # await node.update_network_interface(
    #     iface="vmbr10",
    #     comments="Updated via API",
    # )
    # print("Updated interface")

    # Reload network configuration
    # print("\n[Reload Network]")
    # task = await node.reload_network_configuration()
    # print(f"Reloading network... Task: {task}")

    # Delete interface (example)
    # await node.delete_network_interface("vmbr10")
    # print("Deleted interface")

    # ========================================
    # 13. CERTIFICATE MANAGEMENT
    # ========================================
    print("\n[13] CERTIFICATE MANAGEMENT")
    print("-" * 60)

    # Get certificate information
    print("\n[Get Certificate Information]")
    try:
        certs = await node.get_certificates_info()
        print(f"Certificates: {len(certs)}")
        for cert in certs:
            print(f"  - {cert.filename}")
            if cert.subject:
                print(f"    Subject: {cert.subject}")
            if cert.issuer:
                print(f"    Issuer: {cert.issuer}")
            if cert.notafter:
                from datetime import datetime
                expiry = datetime.fromtimestamp(cert.notafter)
                print(f"    Expires: {expiry.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"  Error: {e}")

    # Order ACME certificate (example - requires ACME configuration)
    # print("\n[Order ACME Certificate]")
    # task = await node.order_acme_certificate()
    # print(f"Ordering ACME certificate... Task: {task}")

    # Renew ACME certificate (example)
    # print("\n[Renew ACME Certificate]")
    # task = await node.renew_acme_certificate(force=True)
    # print(f"Renewing certificate... Task: {task}")

    # Upload custom certificate (example)
    # print("\n[Upload Custom Certificate]")
    # with open("/path/to/cert.pem") as f:
    #     cert_data = f.read()
    # with open("/path/to/key.pem") as f:
    #     key_data = f.read()
    # certs = await node.upload_custom_certificate(
    #     certificates=cert_data,
    #     key=key_data,
    #     restart=True,  # Restart pveproxy
    # )
    # print(f"Uploaded {len(certs)} certificates")

    # ========================================
    # 14. APT PACKAGE MANAGEMENT
    # ========================================
    print("\n[14] APT PACKAGE MANAGEMENT")
    print("-" * 60)

    # List available updates
    print("\n[List Available Updates]")
    try:
        updates = await node.list_apt_updates()
        print(f"Available updates: {len(updates)}")
        for pkg in updates[:5]:  # Show first 5
            print(f"  - {pkg.Package}")
            print(f"    {pkg.OldVersion} -> {pkg.Version}")
            if pkg.Origin:
                print(f"    Origin: {pkg.Origin}")
        if len(updates) > 5:
            print(f"  ... and {len(updates) - 5} more")
    except Exception as e:
        print(f"  Error: {e}")

    # Update APT database (example - can take time)
    # print("\n[Update APT Database]")
    # task = await node.update_apt_database(
    #     notify=True,  # Send notification
    #     quiet=False,
    # )
    # print(f"Updating APT database... Task: {task}")

    # Get package changelog
    # print("\n[Get Package Changelog]")
    # changelog = await node.get_package_changelog(name="pve-manager")
    # print(changelog[:500])  # First 500 characters

    # Get package versions
    print("\n[Get Proxmox Package Versions]")
    try:
        versions = await node.get_package_versions()
        print("Important packages:")
        for pkg_info in versions[:5]:  # Show first 5
            print(f"  - {pkg_info}")
    except Exception as e:
        print(f"  Error: {e}")

    # Get APT repositories
    print("\n[Get APT Repositories]")
    try:
        repos = await node.get_apt_repositories()
        if isinstance(repos, dict):
            print(f"  Files: {len(repos.get('files', []))}")
            print(f"  Errors: {len(repos.get('errors', []))}")
    except Exception as e:
        print(f"  Error: {e}")

    # Add/change repository (example)
    # print("\n[Add Repository]")
    # await node.add_apt_repository(
    #     handle="pve-no-subscription",
    # )
    # print("Added repository")

    # ========================================
    # 15. SUBSCRIPTION MANAGEMENT
    # ========================================
    print("\n[15] SUBSCRIPTION MANAGEMENT")
    print("-" * 60)

    # Get subscription information
    print("\n[Get Subscription Info]")
    try:
        sub = await node.get_subscription()
        print(f"Status: {sub.status}")
        if sub.key:
            print(f"Key: {sub.key[:20]}... (truncated)")
        if sub.level:
            print(f"Level: {sub.level}")
        if sub.productname:
            print(f"Product: {sub.productname}")
        if sub.nextduedate:
            print(f"Next due date: {sub.nextduedate}")
    except Exception as e:
        print(f"  Error: {e}")

    # Set subscription key (example)
    # print("\n[Set Subscription Key]")
    # await node.set_subscription_key("pve1c-xxxxxxxxxxxxxx")
    # print("Subscription key set")

    # Update subscription info (example)
    # print("\n[Update Subscription]")
    # await node.update_subscription(force=False)
    # print("Subscription updated")

    # Delete subscription key (example)
    # await node.delete_subscription_key()
    # print("Subscription key deleted")

    # ========================================
    # 16. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[16] CLEANUP")
    print("-" * 60)

    # Delete cloned VM
    print("\n[Delete Cloned VM]")
    task = await node.delete_vm(1000, VMType.QEMU, purge=True)
    print(f"Deleting VM 1000... Task: {task}")

    # Delete original VM
    print("\n[Delete Original VM]")
    task = await node.delete_vm(
        vmid=999,
        vm_type=VMType.QEMU,
        purge=True,
        destroy_unreferenced_disks=True,
    )
    print(f"Deleting VM 999... Task: {task}")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("NODE MANAGEMENT SUMMARY")
    print("=" * 60)
    print("Node status and information")
    print("List VMs and containers (QEMU/LXC)")
    print("Create, configure, and delete VMs")
    print("VM lifecycle (start, stop, shutdown, reboot, reset)")
    print("Clone VMs (full or linked)")
    print("Migrate VMs between nodes")
    print("Snapshot management (create, list, rollback, delete)")
    print("QEMU guest agent operations (25+ operations)")
    print("Storage management and content listing")
    print("Service management (list, start, stop, restart)")
    print("Task monitoring")
    print("VM backup operations")
    print("Network interface management")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
