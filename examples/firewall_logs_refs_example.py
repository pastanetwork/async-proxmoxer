"""
Example: Firewall Logs and References

Demonstrates how to use the complete firewall API including logs and references.
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, "..")

from proxmoxer import ProxmoxAPI, FirewallManager

# Configuration
PROXMOX_HOST = "10.0.0.1"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_password"
NODE = "pve"
VMID = 100


async def example_firewall_logs():
    """Read firewall logs."""
    print("\n=== Example 1: Firewall Logs ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Get last 50 log entries
        print("Getting last 50 firewall log entries...")
        logs = await fw.get_log(limit=50)

        print(f"Found {len(logs)} log entries:\n")
        for log in logs[-10:]:  # Show last 10
            print(f"[{log.n}] {log.t}")

        # Get logs since a specific time
        print("\n\nGetting logs from last hour...")
        one_hour_ago = int((datetime.now() - timedelta(hours=1)).timestamp())
        recent_logs = await fw.get_log(since=one_hour_ago)

        print(f"Found {len(recent_logs)} log entries in the last hour")

        # Get logs in a time range
        print("\n\nGetting logs from specific time range...")
        now = int(datetime.now().timestamp())
        two_hours_ago = int((datetime.now() - timedelta(hours=2)).timestamp())

        range_logs = await fw.get_log(since=two_hours_ago, until=now, limit=100)
        print(f"Found {len(range_logs)} log entries in the last 2 hours")


async def example_firewall_refs():
    """Get firewall references (available aliases and IP sets)."""
    print("\n=== Example 2: Firewall References ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Get all references (aliases and IP sets available for use in rules)
        print("Getting all available references...")
        all_refs = await fw.get_refs()

        print(f"\nFound {len(all_refs)} references available:\n")
        for ref in all_refs:
            comment = f" - {ref.comment}" if ref.comment else ""
            print(f"[{ref.type}] {ref.name} ({ref.scope}): {ref.ref}{comment}")

        # Get only aliases
        print("\n\nGetting only alias references...")
        alias_refs = await fw.get_refs(ref_type="alias")

        print(f"Found {len(alias_refs)} aliases:")
        for ref in alias_refs:
            print(f"  - {ref.name}: {ref.ref}")

        # Get only IP sets
        print("\n\nGetting only IP set references...")
        ipset_refs = await fw.get_refs(ref_type="ipset")

        print(f"Found {len(ipset_refs)} IP sets:")
        for ref in ipset_refs:
            print(f"  - {ref.name}: {ref.ref}")


async def example_complete_firewall_info():
    """Get complete firewall information including logs and refs."""
    print("\n=== Example 3: Complete Firewall Information ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        print(f"Firewall information for VM {VMID}:\n")

        # Options
        print("1. Options:")
        options = await fw.get_options()
        print(f"   - Enabled: {options.enable}")
        print(f"   - Policy IN: {options.policy_in}")
        print(f"   - Policy OUT: {options.policy_out}")
        print(f"   - DHCP: {options.dhcp}")
        print(f"   - IP Filter: {options.ipfilter}")

        # Rules
        print("\n2. Rules:")
        rules = await fw.get_rules()
        print(f"   - Total rules: {len(rules)}")
        if rules:
            print(f"   - First rule: {rules[0]}")

        # Aliases
        print("\n3. Aliases:")
        aliases = await fw.get_aliases()
        print(f"   - Total aliases: {len(aliases)}")
        for alias in aliases[:3]:  # Show first 3
            print(f"     - {alias.name}: {alias.cidr}")

        # IP Sets
        print("\n4. IP Sets:")
        ipsets = await fw.get_ipsets()
        print(f"   - Total IP sets: {len(ipsets)}")
        for ipset in ipsets[:3]:  # Show first 3
            print(f"     - {ipset.name}")

        # References (what can be used in rules)
        print("\n5. Available References:")
        refs = await fw.get_refs()
        print(f"   - Total references: {len(refs)}")
        print(f"   - Aliases: {len([r for r in refs if r.type == 'alias'])}")
        print(f"   - IP Sets: {len([r for r in refs if r.type == 'ipset'])}")

        # Recent logs
        print("\n6. Recent Logs:")
        logs = await fw.get_log(limit=5)
        print(f"   - Last {len(logs)} log entries:")
        for log in logs:
            print(f"     [{log.n}] {log.t[:80]}...")  # Truncate long lines


async def example_using_refs_in_rules():
    """Show how to use refs to see what's available before creating rules."""
    print("\n=== Example 4: Using Refs to Build Rules ===\n")

    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Get available references
        refs = await fw.get_refs()

        print("Available references you can use in firewall rules:\n")

        # Show aliases that can be used as source/dest
        alias_refs = [r for r in refs if r.type == "alias"]
        if alias_refs:
            print("Aliases (use in source/dest):")
            for ref in alias_refs:
                print(f"  - {ref.name} → {ref.ref}")
                print(f"    Usage: source=\"{ref.name}\" or dest=\"{ref.name}\"")

        print()

        # Show IP sets that can be used with + prefix
        ipset_refs = [r for r in refs if r.type == "ipset"]
        if ipset_refs:
            print("IP Sets (use with + prefix):")
            for ref in ipset_refs:
                print(f"  - {ref.name} → {ref.ref}")
                print(f"    Usage: source=\"+{ref.name}\" or dest=\"+{ref.name}\"")

        print("\n\nExample rule using a reference:")
        print("""
from proxmoxer import FirewallRule, FirewallRuleAction, FirewallRuleType

rule = FirewallRule(
    action=FirewallRuleAction.ACCEPT,
    type=FirewallRuleType.IN,
    source="+trusted_ips",  # Reference to IP set
    comment="Allow from trusted IPs"
)
await fw.add_rule(rule)
""")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("Firewall Logs and References Examples")
    print("=" * 70)

    examples = [
        ("Firewall Logs", example_firewall_logs),
        ("Firewall References", example_firewall_refs),
        ("Complete Firewall Info", example_complete_firewall_info),
        ("Using Refs in Rules", example_using_refs_in_rules),
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

    print("=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
