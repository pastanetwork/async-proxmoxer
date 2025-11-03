"""
FirewallManager Example - Firewall Rules and Configuration

This example demonstrates firewall management including rules, IP sets,
aliases, and logging.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import (
    FirewallManager,
    FirewallRule,
    FirewallRuleAction,
    FirewallRuleType,
    FirewallProtocol,
    FirewallLogLevel,
)


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    # Firewall manager for specific VM
    fw = FirewallManager(proxmox, node="pve-node1", vmid=100)

    print("=" * 60)
    print("FirewallManager Examples - Firewall Configuration")
    print("=" * 60)

    # ========================================
    # 1. ENABLE FIREWALL
    # ========================================
    print("\n[1] ENABLE FIREWALL")
    print("-" * 60)

    await fw.enable()
    print("Firewall enabled for VM 100")

    # Get current options
    options = await fw.get_options()
    print(f"Firewall enabled: {options.enable}")
    print(f"Policy IN: {options.policy_in}")
    print(f"Policy OUT: {options.policy_out}")

    # ========================================
    # 2. SET FIREWALL OPTIONS
    # ========================================
    print("\n[2] SET FIREWALL OPTIONS")
    print("-" * 60)

    await fw.set_options(
        enable=True,
        dhcp=True,
        ipfilter=True,
        policy_in="DROP",
        policy_out="ACCEPT",
        log_level_in=FirewallLogLevel.INFO,
        log_level_out=FirewallLogLevel.NOTICE,
    )
    print("Firewall options configured")

    # ========================================
    # 3. ADD FIREWALL RULES
    # ========================================
    print("\n[3] ADD FIREWALL RULES")
    print("-" * 60)

    # Allow SSH
    rule_ssh = FirewallRule(
        action=FirewallRuleAction.ACCEPT,
        type=FirewallRuleType.IN,
        proto=FirewallProtocol.TCP,
        dport=22,
        comment="Allow SSH",
    )
    await fw.add_rule(rule_ssh)
    print("Added rule: Allow SSH (port 22)")

    # Allow HTTP
    rule_http = FirewallRule(
        action=FirewallRuleAction.ACCEPT,
        type=FirewallRuleType.IN,
        proto=FirewallProtocol.TCP,
        dport=80,
        comment="Allow HTTP",
    )
    await fw.add_rule(rule_http)
    print("Added rule: Allow HTTP (port 80)")

    # Allow HTTPS
    rule_https = FirewallRule(
        action=FirewallRuleAction.ACCEPT,
        type=FirewallRuleType.IN,
        proto=FirewallProtocol.TCP,
        dport=443,
        comment="Allow HTTPS",
    )
    await fw.add_rule(rule_https)
    print("Added rule: Allow HTTPS (port 443)")

    # Allow from specific IP
    rule_mysql = FirewallRule(
        action=FirewallRuleAction.ACCEPT,
        type=FirewallRuleType.IN,
        proto=FirewallProtocol.TCP,
        source="192.168.1.100/32",
        dport=3306,
        comment="Allow MySQL from admin server",
    )
    await fw.add_rule(rule_mysql)
    print("Added rule: Allow MySQL from 192.168.1.100")

    # Block outgoing SMTP
    rule_smtp = FirewallRule(
        action=FirewallRuleAction.REJECT,
        type=FirewallRuleType.OUT,
        proto=FirewallProtocol.TCP,
        dport=25,
        comment="Block outgoing SMTP",
    )
    await fw.add_rule(rule_smtp)
    print("Added rule: Block outgoing SMTP")

    # ========================================
    # 4. LIST FIREWALL RULES
    # ========================================
    print("\n[4] LIST FIREWALL RULES")
    print("-" * 60)

    rules = await fw.get_rules()
    print(f"Total rules: {len(rules)}")
    for rule in rules:
        print(f"\n  Rule {rule.pos}:")
        print(f"    Type: {rule.type}")
        print(f"    Action: {rule.action}")
        print(f"    Protocol: {rule.proto}")
        if rule.dport:
            print(f"    Port: {rule.dport}")
        if rule.source:
            print(f"    Source: {rule.source}")
        if rule.comment:
            print(f"    Comment: {rule.comment}")
        print(f"    Enabled: {rule.enable}")

    # ========================================
    # 5. UPDATE FIREWALL RULE
    # ========================================
    print("\n[5] UPDATE FIREWALL RULE")
    print("-" * 60)

    # Get the SSH rule and update it to enable logging
    ssh_rule = await fw.get_rule(0)
    ssh_rule.log = FirewallLogLevel.INFO
    ssh_rule.comment = "Allow SSH (with logging)"
    await fw.update_rule(0, ssh_rule)
    print("Updated SSH rule to enable logging")

    # ========================================
    # 6. IP ALIASES
    # ========================================
    print("\n[6] IP ALIASES")
    print("-" * 60)

    # Add IP alias
    await fw.add_alias(
        name="admin_server",
        cidr="192.168.1.100/32",
        comment="Administrator server",
    )
    print("Added IP alias: admin_server")

    await fw.add_alias(
        name="office_network",
        cidr="192.168.1.0/24",
        comment="Office network",
    )
    print("Added IP alias: office_network")

    # List aliases
    aliases = await fw.get_aliases()
    print(f"\nIP Aliases: {len(aliases)}")
    for alias in aliases:
        print(f"  - {alias.name}: {alias.cidr}")
        if alias.comment:
            print(f"    {alias.comment}")

    # ========================================
    # 7. IP SETS
    # ========================================
    print("\n[7] IP SETS")
    print("-" * 60)

    # Create IP set
    await fw.create_ipset(
        name="whitelist",
        comment="Whitelisted IPs",
    )
    print("Created IP set: whitelist")

    # Add entries to IP set
    await fw.add_ipset_entry(
        ipset_name="whitelist",
        cidr="10.0.1.0/24",
        comment="Internal network",
    )
    print("Added 10.0.1.0/24 to whitelist")

    await fw.add_ipset_entry(
        ipset_name="whitelist",
        cidr="10.0.2.0/24",
        comment="Partner network",
    )
    print("Added 10.0.2.0/24 to whitelist")

    # List IP sets
    ipsets = await fw.get_ipsets()
    print(f"\nIP Sets: {len(ipsets)}")
    for ipset in ipsets:
        print(f"  - {ipset.name}")
        if ipset.comment:
            print(f"    {ipset.comment}")

    # List IP set entries
    entries = await fw.get_ipset_entries("whitelist")
    print(f"\nWhitelist entries: {len(entries)}")
    for entry in entries:
        print(f"  - {entry.cidr}: {entry.comment}")

    # ========================================
    # 8. USE IP SET IN RULE
    # ========================================
    print("\n[8] USE IP SET IN FIREWALL RULE")
    print("-" * 60)

    # Add rule using IP set
    rule_whitelist = FirewallRule(
        action=FirewallRuleAction.ACCEPT,
        type=FirewallRuleType.IN,
        source="+whitelist",  # + prefix for IP set
        comment="Allow from whitelist",
    )
    await fw.add_rule(rule_whitelist)
    print("Added rule using whitelist IP set")

    # ========================================
    # 9. CONVENIENCE METHODS
    # ========================================
    print("\n[9] CONVENIENCE METHODS")
    print("-" * 60)

    # Use built-in convenience methods
    # Note: These are just examples, don't actually run if rules already exist
    # await fw.allow_ssh()
    # await fw.allow_http()
    # await fw.allow_https()
    print("Convenience methods available: allow_ssh(), allow_http(), allow_https()")

    # ========================================
    # 10. FIREWALL LOGS
    # ========================================
    print("\n[10] FIREWALL LOGS")
    print("-" * 60)

    # Get firewall logs
    try:
        logs = await fw.get_log(limit=10)
        print(f"Recent firewall logs: {len(logs)}")
        for log in logs[:5]:
            print(f"  Line {log.n}: {log.t}")
    except Exception as e:
        print(f"Could not retrieve logs: {e}")

    # ========================================
    # 11. FIREWALL REFS (Rule Analysis)
    # ========================================
    print("\n[11] FIREWALL REFS")
    print("-" * 60)

    try:
        refs = await fw.get_refs()
        print(f"Firewall references: {len(refs)}")
        for ref in refs[:5]:
            print(f"  - {ref.type}: {ref.name}")
    except Exception as e:
        print(f"Could not retrieve refs: {e}")

    # ========================================
    # 12. DISABLE SPECIFIC RULE
    # ========================================
    print("\n[12] DISABLE SPECIFIC RULE")
    print("-" * 60)

    # Disable the outgoing SMTP block temporarily
    smtp_rule = await fw.get_rule(4)
    smtp_rule.enable = False
    await fw.update_rule(4, smtp_rule)
    print("Disabled outgoing SMTP block rule")

    # ========================================
    # 13. MOVE RULE
    # ========================================
    print("\n[13] MOVE RULE POSITION")
    print("-" * 60)

    # Move rule to different position
    await fw.move_rule(pos=4, new_pos=2)
    print("Moved rule from position 4 to position 2")

    # ========================================
    # 14. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[14] CLEANUP")
    print("-" * 60)

    # Delete IP set entry
    await fw.delete_ipset_entry("whitelist", "10.0.2.0/24")
    print("Deleted IP set entry")

    # Delete IP alias
    await fw.delete_alias("admin_server")
    print("Deleted IP alias")

    # Delete rule
    await fw.delete_rule(pos=5)
    print("Deleted rule at position 5")

    # Disable firewall
    # await fw.disable()
    # print("Firewall disabled")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("FIREWALL MANAGEMENT SUMMARY")
    print("=" * 60)
    print("Enable/disable firewall")
    print("Configure firewall options (policies, logging)")
    print("Add rules (ACCEPT, REJECT, DROP)")
    print("Update rules (enable/disable, logging)")
    print("Move rules to different positions")
    print("Delete rules")
    print("Create IP aliases for readability")
    print("Create IP sets for grouped IPs")
    print("Use IP sets in rules")
    print("View firewall logs")
    print("Analyze rule references")
    print("\nUse Cases:")
    print("  - Secure VM access (SSH, HTTP/HTTPS)")
    print("  - IP whitelisting/blacklisting")
    print("  - Network segmentation")
    print("  - Traffic logging and monitoring")
    print("  - DDoS protection")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
