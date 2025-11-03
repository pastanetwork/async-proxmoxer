"""
Example: Firewall Management for LXC Containers

Shows how to use FirewallManager with LXC containers and access specific resources.
"""

import asyncio
import sys

sys.path.insert(0, "..")

from proxmoxer import ProxmoxAPI, FirewallManager, FirewallRule, FirewallRuleAction, FirewallRuleType

# Configuration
PROXMOX_HOST = "10.0.0.1"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_password"
NODE = "pve"
CT_ID = 100  # Container ID


async def example_lxc_firewall():
    """Configure firewall for an LXC container."""
    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        # Create firewall manager for LXC container
        fw = FirewallManager(proxmox, NODE, CT_ID, vm_type="lxc")

        print(f"=== Firewall Management for LXC Container {CT_ID} ===\n")

        # Enable firewall
        print("Enabling firewall...")
        await fw.enable()

        # Set basic options
        await fw.set_options(
            dhcp=True,
            policy_in="DROP",
            policy_out="ACCEPT",
        )

        # Add some rules
        print("Adding firewall rules...")
        await fw.allow_ssh(source="192.168.1.0/24")
        await fw.allow_http()
        await fw.allow_https()

        # Add alias
        print("\nAdding alias 'admin_ip'...")
        await fw.add_alias("admin_ip", "192.168.1.100", comment="Admin workstation")

        # Get specific alias by name (uses /firewall/aliases/{name})
        print("Retrieving specific alias...")
        alias = await fw.get_alias("admin_ip")
        print(f"  Name: {alias.name}")
        print(f"  CIDR: {alias.cidr}")
        print(f"  Comment: {alias.comment}")

        # Get all aliases
        print("\nAll aliases:")
        aliases = await fw.get_aliases()
        for alias in aliases:
            print(f"  - {alias.name}: {alias.cidr}")

        # Get options (returns FirewallOptions model)
        print("\nFirewall configuration:")
        options = await fw.get_options()
        print(f"  Enabled: {options.enable}")
        print(f"  Policy IN: {options.policy_in}")
        print(f"  Policy OUT: {options.policy_out}")
        print(f"  DHCP: {options.dhcp}")

        print("\nLXC firewall configured successfully!")


async def example_qemu_vs_lxc():
    """Show the difference between QEMU and LXC firewall management."""
    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        print("=== QEMU vs LXC Firewall ===\n")

        # QEMU VM (default)
        fw_vm = FirewallManager(proxmox, NODE, 100)
        print(f"VM Firewall type: {fw_vm.vm_type}")
        print(f"VM Path: /nodes/{NODE}/qemu/100/firewall\n")

        # LXC Container
        fw_ct = FirewallManager(proxmox, NODE, 100, vm_type="lxc")
        print(f"Container Firewall type: {fw_ct.vm_type}")
        print(f"Container Path: /nodes/{NODE}/lxc/100/firewall\n")

        # Both use the same methods!
        print("Both support the same firewall operations:")
        print("  - get_options(), enable(), disable()")
        print("  - get_rules(), add_rule(), delete_rule()")
        print("  - get_aliases(), get_alias(name), add_alias()")
        print("  - get_ipsets(), create_ipset(), delete_ipset()")


async def main():
    """Run examples."""
    print("=" * 60)
    print("LXC Firewall Management Examples")
    print("=" * 60)

    examples = [
        ("LXC Firewall Configuration", example_lxc_firewall),
        ("QEMU vs LXC Comparison", example_qemu_vs_lxc),
    ]

    for name, example_func in examples:
        try:
            await example_func()
            print()
        except Exception as e:
            print(f"\nExample '{name}' failed: {e}")
            import traceback
            traceback.print_exc()

        await asyncio.sleep(1)

    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
