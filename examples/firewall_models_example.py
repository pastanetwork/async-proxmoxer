"""
Example: Using Firewall Models for Type-Safe Access

Shows how to use the new dataclass models for clean, type-safe firewall management.
"""

import asyncio
import sys

sys.path.insert(0, "..")

from proxmoxer import ProxmoxAPI, FirewallManager

# Configuration
PROXMOX_HOST = "10.0.0.1"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_password"
NODE = "pve"
VMID = 100


async def main():
    """Demonstrate using firewall models."""
    async with await ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        fw = FirewallManager(proxmox, NODE, VMID)

        # Get firewall options - returns FirewallOptions model
        print("=== Firewall Options (Type-Safe Model) ===\n")
        options = await fw.get_options()

        # Easy attribute access (no more dict['key']!)
        print(f"Enabled: {options.enable}")
        print(f"DHCP: {options.dhcp}")
        print(f"IP Filter: {options.ipfilter}")
        print(f"Policy IN: {options.policy_in}")
        print(f"Policy OUT: {options.policy_out}")
        print(f"Log Level IN: {options.log_level_in or 'none'}")
        print(f"Log Level OUT: {options.log_level_out or 'none'}")
        print(f"MAC Filter: {options.macfilter}")
        print(f"NDP: {options.ndp}")
        print(f"RADV: {options.radv}")

        # Get aliases - returns list[FirewallAlias]
        print("\n=== Firewall Aliases ===\n")
        aliases = await fw.get_aliases()

        if aliases:
            for alias in aliases:
                # Type-safe attribute access
                print(f"Name: {alias.name}")
                print(f"  CIDR: {alias.cidr}")
                if alias.comment:
                    print(f"  Comment: {alias.comment}")
                print()
        else:
            print("No aliases configured\n")

        # Get IP sets - returns list[FirewallIPSet]
        print("=== IP Sets ===\n")
        ipsets = await fw.get_ipsets()

        if ipsets:
            for ipset in ipsets:
                print(f"IP Set: {ipset.name}")
                if ipset.comment:
                    print(f"  Comment: {ipset.comment}")

                # Get entries - returns list[FirewallIPSetEntry]
                entries = await fw.get_ipset_entries(ipset.name)
                if entries:
                    print(f"  Entries:")
                    for entry in entries:
                        nomatch_str = " (nomatch)" if entry.nomatch else ""
                        comment_str = f" - {entry.comment}" if entry.comment else ""
                        print(f"    - {entry.cidr}{nomatch_str}{comment_str}")
                print()
        else:
            print("No IP sets configured\n")

        # Type safety example - these are actual Python objects
        print("=== Type Safety Benefits ===\n")
        print(f"Options type: {type(options).__name__}")
        print(f"Has 'enable' attribute: {hasattr(options, 'enable')}")
        print(f"Enable is bool: {isinstance(options.enable, bool)}")

        if aliases:
            print(f"\nFirst alias type: {type(aliases[0]).__name__}")
            print(f"Has 'cidr' attribute: {hasattr(aliases[0], 'cidr')}")


if __name__ == "__main__":
    asyncio.run(main())
