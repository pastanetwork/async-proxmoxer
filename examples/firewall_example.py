"""
Comprehensive Firewall Management Example

Demonstrates all firewall management capabilities with the async Proxmoxer library.
"""

import asyncio
import sys

sys.path.insert(0, "..")

from proxmoxer import (
    ProxmoxAPI,
    FirewallManager,
    FirewallRule,
    FirewallRuleAction,
    FirewallRuleType,
    FirewallProtocol,
    FirewallLogLevel,
)


# Configuration
PROXMOX_HOST = "10.0.0.1"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_password"
NODE = "pve"
VMID = 100


async def example_basic_firewall():
    """Example 1: Basic firewall configuration."""
    print("\n=== Example 1: Basic Firewall Setup ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        # Create firewall manager
        fw = FirewallManager(proxmox, NODE, VMID)

        # Enable firewall
        print("Enabling firewall...")
        await fw.enable()

        # Set basic options
        print("Configuring firewall options...")
        await fw.set_options(
            dhcp=True,  # Allow DHCP
            ipfilter=True,  # Enable IP filtering
            policy_in="DROP",  # Drop all incoming by default
            policy_out="ACCEPT",  # Allow all outgoing
            log_level_in=FirewallLogLevel.INFO,
        )

        print("✓ Basic firewall configured")


async def example_rules_management():
    """Example 2: Managing firewall rules."""
    print("\n=== Example 2: Firewall Rules Management ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Add rule to allow SSH from specific IP
        print("Adding SSH rule...")
        await fw.allow_ssh(source="192.168.1.0/24")

        # Add rule to allow HTTP from anywhere
        print("Adding HTTP rule...")
        await fw.allow_http()

        # Add rule to allow HTTPS from anywhere
        print("Adding HTTPS rule...")
        await fw.allow_https()

        # Add custom rule for MySQL
        print("Adding MySQL rule...")
        mysql_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=3306,
            source="10.0.1.0/24",
            comment="Allow MySQL from internal network",
        )
        await fw.add_rule(mysql_rule)

        # Add rule to block specific IP
        print("Blocking malicious IP...")
        await fw.block_ip("1.2.3.4", comment="Blocked - suspicious activity")

        # List all rules
        print("\nCurrent firewall rules:")
        rules = await fw.get_rules()
        for i, rule in enumerate(rules):
            enabled = "✓" if rule.enable else "✗"
            print(f"  [{i}] {enabled} {rule}")

        print(f"\n✓ {len(rules)} rules configured")


async def example_advanced_rules():
    """Example 3: Advanced firewall rules."""
    print("\n=== Example 3: Advanced Rules ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Allow port range
        print("Allowing port range 8000-8100...")
        port_range_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport="8000:8100",  # Port range
            comment="Allow application ports",
        )
        await fw.add_rule(port_range_rule)

        # Allow UDP for VPN
        print("Allowing OpenVPN...")
        openvpn_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.UDP,
            dport=1194,
            comment="Allow OpenVPN",
        )
        await fw.add_rule(openvpn_rule)

        # Allow ICMP (ping)
        print("Allowing ICMP ping...")
        icmp_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.ICMP,
            comment="Allow ping",
        )
        await fw.add_rule(icmp_rule)

        # Reject with log
        print("Adding reject rule with logging...")
        reject_rule = FirewallRule(
            action=FirewallRuleAction.REJECT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=23,  # Telnet
            log=FirewallLogLevel.WARNING,
            comment="Reject Telnet (insecure)",
        )
        await fw.add_rule(reject_rule)

        print("✓ Advanced rules configured")


async def example_aliases():
    """Example 4: Using firewall aliases."""
    print("\n=== Example 4: Firewall Aliases ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Create aliases for common IPs
        print("Creating IP aliases...")

        await fw.add_alias(
            "admin_workstation", "192.168.1.100", comment="Admin workstation"
        )

        await fw.add_alias("office_network", "192.168.1.0/24", comment="Office network")

        await fw.add_alias("vpn_gateway", "10.0.10.1", comment="VPN gateway")

        # Use aliases in rules
        print("Creating rules with aliases...")

        # Allow SSH from admin workstation
        admin_ssh_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=22,
            source="admin_workstation",  # Use alias
            comment="Allow SSH from admin",
        )
        await fw.add_rule(admin_ssh_rule)

        # List all aliases
        print("\nConfigured aliases:")
        aliases = await fw.get_aliases()
        for alias in aliases:
            comment = alias.comment or 'N/A'
            print(f"  - {alias.name}: {alias.cidr} ({comment})")

        print(f"\n✓ {len(aliases)} aliases configured")


async def example_ipsets():
    """Example 5: Using IP sets."""
    print("\n=== Example 5: IP Sets ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Create IP set for allowed IPs
        print("Creating 'allowed_ips' IP set...")
        await fw.create_ipset("allowed_ips", comment="Trusted IPs")

        # Add IPs to the set
        print("Adding IPs to set...")
        await fw.add_ipset_entry("allowed_ips", "192.168.1.100", comment="Admin PC")
        await fw.add_ipset_entry("allowed_ips", "192.168.1.101", comment="Developer PC")
        await fw.add_ipset_entry("allowed_ips", "10.0.10.0/24", comment="VPN network")

        # Create IP set for blocked IPs
        print("Creating 'blocked_ips' IP set...")
        await fw.create_ipset("blocked_ips", comment="Blocked IPs")

        await fw.add_ipset_entry("blocked_ips", "1.2.3.4", comment="Attacker")
        await fw.add_ipset_entry("blocked_ips", "5.6.7.8", comment="Scanner")

        # Use IP sets in rules
        print("Creating rules with IP sets...")

        # Allow access from allowed_ips
        allowed_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            source="+allowed_ips",  # Reference IP set with +
            comment="Allow from trusted IPs",
        )
        await fw.add_rule(allowed_rule)

        # Block access from blocked_ips
        blocked_rule = FirewallRule(
            action=FirewallRuleAction.DROP,
            type=FirewallRuleType.IN,
            source="+blocked_ips",  # Reference IP set with +
            comment="Block malicious IPs",
        )
        await fw.add_rule(blocked_rule)

        # List all IP sets
        print("\nConfigured IP sets:")
        ipsets = await fw.get_ipsets()
        for ipset in ipsets:
            comment = ipset.comment or 'N/A'
            print(f"\n  {ipset.name} ({comment})")

            entries = await fw.get_ipset_entries(ipset.name)
            for entry in entries:
                entry_comment = entry.comment or 'N/A'
                print(f"    - {entry.cidr}: {entry_comment}")

        print(f"\n✓ {len(ipsets)} IP sets configured")


async def example_complete_setup():
    """Example 6: Complete firewall setup for web server."""
    print("\n=== Example 6: Complete Web Server Firewall ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        print("Setting up web server firewall...\n")

        # 1. Enable firewall with strict policy
        print("1. Enabling firewall with DROP policy...")
        await fw.set_options(
            enable=True,
            policy_in="DROP",  # Drop all by default
            policy_out="ACCEPT",  # Allow outgoing
            dhcp=True,
            ipfilter=True,
            log_level_in=FirewallLogLevel.INFO,
            log_level_out=FirewallLogLevel.NOTICE,
        )

        # 2. Create IP sets
        print("2. Creating IP sets...")
        await fw.create_ipset("admin_ips", comment="Admin IPs")
        await fw.add_ipset_entry("admin_ips", "192.168.1.100")
        await fw.add_ipset_entry("admin_ips", "10.0.10.0/24")

        # 3. Allow SSH from admins only
        print("3. Allowing SSH (admin only)...")
        ssh_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=22,
            source="+admin_ips",
            log=FirewallLogLevel.INFO,
            comment="SSH - admin only",
        )
        await fw.add_rule(ssh_rule)

        # 4. Allow HTTP/HTTPS from anywhere
        print("4. Allowing HTTP/HTTPS (public)...")
        await fw.allow_http()
        await fw.allow_https()

        # 5. Allow database from app servers
        print("5. Allowing MySQL (from app servers)...")
        db_rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=3306,
            source="10.0.20.0/24",
            comment="MySQL from app servers",
        )
        await fw.add_rule(db_rule)

        # 6. Allow ICMP
        print("6. Allowing ICMP (ping)...")
        await fw.add_rule(
            FirewallRule(
                action=FirewallRuleAction.ACCEPT,
                type=FirewallRuleType.IN,
                proto=FirewallProtocol.ICMP,
                comment="Allow ping",
            )
        )

        # 7. Log and reject everything else
        print("7. Setting up logging for rejected traffic...")
        # (This is done by the DROP policy with log_level_in)

        print("\n✓ Web server firewall fully configured!")

        # Show final configuration
        print("\nFinal configuration:")
        options = await fw.get_options()
        print(f"  Firewall: {'Enabled' if options.enable else 'Disabled'}")
        print(f"  Policy IN: {options.policy_in}")
        print(f"  Policy OUT: {options.policy_out}")

        rules = await fw.get_rules()
        print(f"  Rules: {len(rules)}")

        ipsets = await fw.get_ipsets()
        print(f"  IP Sets: {len(ipsets)}")


async def example_rule_management():
    """Example 7: Managing existing rules."""
    print("\n=== Example 7: Rule Management ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # List all rules
        print("Current rules:")
        rules = await fw.get_rules()
        for i, rule in enumerate(rules):
            print(f"  [{i}] {rule}")

        if rules:
            # Update first rule
            print(f"\nUpdating rule 0...")
            updated_rule = rules[0]
            updated_rule.comment = "Updated comment"
            await fw.update_rule(0, updated_rule)

            # Move rule
            if len(rules) > 1:
                print(f"Moving rule 0 to position 1...")
                await fw.move_rule(0, 1)

            # Delete last rule
            print(f"Deleting last rule...")
            await fw.delete_rule(len(rules) - 1)

        print("\n✓ Rules managed successfully")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Proxmoxer Firewall Management Examples")
    print("=" * 60)

    examples = [
        ("Basic Firewall Setup", example_basic_firewall),
        ("Rules Management", example_rules_management),
        ("Advanced Rules", example_advanced_rules),
        ("Firewall Aliases", example_aliases),
        ("IP Sets", example_ipsets),
        ("Complete Web Server Setup", example_complete_setup),
        ("Rule Management", example_rule_management),
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\nExample '{name}' failed: {e}")
            import traceback

            traceback.print_exc()

        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
