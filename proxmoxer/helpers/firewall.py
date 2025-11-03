"""
Firewall helpers for Proxmoxer.

Provides high-level async API for managing Proxmox firewall rules,
especially for VMs, with full type safety.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from ..types import ResponseData

logger = logging.getLogger(__name__)


class FirewallRuleAction(str, Enum):
    """Firewall rule action."""

    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    DROP = "DROP"


class FirewallRuleType(str, Enum):
    """Firewall rule direction type."""

    IN = "in"
    OUT = "out"
    GROUP = "group"


class FirewallLogLevel(str, Enum):
    """Firewall log level."""

    EMERG = "emerg"
    ALERT = "alert"
    CRIT = "crit"
    ERR = "err"
    WARNING = "warning"
    NOTICE = "notice"
    INFO = "info"
    DEBUG = "debug"
    NOLOG = "nolog"


class FirewallProtocol(str, Enum):
    """Network protocols."""

    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ICMPV6 = "icmpv6"
    AH = "ah"
    ESP = "esp"
    GRE = "gre"
    IPIP = "ipip"
    ALL = "all"


@dataclass
class FirewallOptions:
    """Firewall options configuration."""

    enable: bool = False
    dhcp: bool = False
    ipfilter: bool = False
    log_level_in: str | None = None
    log_level_out: str | None = None
    macfilter: bool = False
    ndp: bool = False
    policy_in: str = "DROP"
    policy_out: str = "ACCEPT"
    radv: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallOptions:
        """Create FirewallOptions from API response."""
        return cls(
            enable=bool(data.get("enable", 0)),
            dhcp=bool(data.get("dhcp", 0)),
            ipfilter=bool(data.get("ipfilter", 0)),
            log_level_in=data.get("log_level_in"),
            log_level_out=data.get("log_level_out"),
            macfilter=bool(data.get("macfilter", 0)),
            ndp=bool(data.get("ndp", 0)),
            policy_in=data.get("policy_in", "DROP"),
            policy_out=data.get("policy_out", "ACCEPT"),
            radv=bool(data.get("radv", 0)),
        )


@dataclass
class FirewallAlias:
    """Firewall IP alias."""

    name: str
    cidr: str
    comment: str | None = None
    digest: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallAlias:
        """Create FirewallAlias from API response."""
        return cls(
            name=data["name"],
            cidr=data["cidr"],
            comment=data.get("comment"),
            digest=data.get("digest"),
        )


@dataclass
class FirewallIPSetEntry:
    """IP set entry."""

    cidr: str
    nomatch: bool = False
    comment: str | None = None
    digest: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallIPSetEntry:
        """Create FirewallIPSetEntry from API response."""
        return cls(
            cidr=data["cidr"],
            nomatch=bool(data.get("nomatch", 0)),
            comment=data.get("comment"),
            digest=data.get("digest"),
        )


@dataclass
class FirewallIPSet:
    """IP set configuration."""

    name: str
    comment: str | None = None
    digest: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallIPSet:
        """Create FirewallIPSet from API response."""
        return cls(
            name=data["name"],
            comment=data.get("comment"),
            digest=data.get("digest"),
        )


@dataclass
class FirewallRef:
    """Firewall reference (alias or ipset)."""

    name: str
    type: str  # "alias" or "ipset"
    ref: str
    scope: str
    comment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallRef:
        """Create FirewallRef from API response."""
        return cls(
            name=data["name"],
            type=data["type"],
            ref=data["ref"],
            scope=data["scope"],
            comment=data.get("comment"),
        )


@dataclass
class FirewallLogEntry:
    """Firewall log entry."""

    n: int  # Line number
    t: str  # Line text

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FirewallLogEntry:
        """Create FirewallLogEntry from API response."""
        return cls(
            n=data["n"],
            t=data["t"],
        )


class FirewallRule:
    """
    Represents a Proxmox firewall rule with type safety.

    Provides a convenient interface for creating and managing firewall rules.
    """

    def __init__(
        self,
        action: FirewallRuleAction | str,
        type: FirewallRuleType | str,
        *,
        enable: bool = True,
        comment: str | None = None,
        dest: str | None = None,
        dport: str | int | None = None,
        icmp_type: str | None = None,
        iface: str | None = None,
        ipversion: int | None = None,
        log: FirewallLogLevel | str | None = None,
        macro: str | None = None,
        pos: int | None = None,
        proto: FirewallProtocol | str | None = None,
        source: str | None = None,
        sport: str | int | None = None,
    ) -> None:
        """
        Initialize firewall rule.

        Args:
            action: Rule action (ACCEPT, REJECT, DROP)
            type: Rule type (in, out, group)
            enable: Enable rule (default: True)
            comment: Rule comment/description
            dest: Destination IP/CIDR
            dport: Destination port or port range
            icmp_type: ICMP type specification
            iface: Network interface name
            ipversion: IP version (4 or 6)
            log: Log level
            macro: Use predefined macro
            pos: Rule position (read-only, set by API)
            proto: Protocol (tcp, udp, icmp, etc.)
            source: Source IP/CIDR
            sport: Source port or port range
        """
        self.action = action
        self.type = type
        self.enable = 1 if enable else 0
        self.comment = comment
        self.dest = dest
        self.dport = str(dport) if dport is not None else None
        self.icmp_type = icmp_type
        self.iface = iface
        self.ipversion = ipversion
        self.log = log
        self.macro = macro
        self.pos = pos
        self.proto = proto
        self.source = source
        self.sport = str(sport) if sport is not None else None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert rule to dictionary for API.

        Returns:
            Dictionary representation
        """
        data = {
            "action": str(self.action),
            "type": str(self.type),
            "enable": self.enable,
        }

        # Add optional fields
        if self.comment:
            data["comment"] = self.comment
        if self.dest:
            data["dest"] = self.dest
        if self.dport:
            data["dport"] = self.dport
        if self.icmp_type:
            data["icmp-type"] = self.icmp_type
        if self.iface:
            data["iface"] = self.iface
        if self.ipversion:
            data["ipversion"] = self.ipversion
        if self.log:
            data["log"] = str(self.log)
        if self.macro:
            data["macro"] = self.macro
        if self.proto:
            data["proto"] = str(self.proto)
        if self.source:
            data["source"] = self.source
        if self.sport:
            data["sport"] = self.sport

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FirewallRule":
        """
        Create rule from API response.

        Args:
            data: API response data

        Returns:
            FirewallRule instance
        """
        return cls(
            action=data["action"],
            type=data["type"],
            enable=bool(data.get("enable", 1)),
            comment=data.get("comment"),
            dest=data.get("dest"),
            dport=data.get("dport"),
            icmp_type=data.get("icmp-type"),
            iface=data.get("iface"),
            ipversion=data.get("ipversion"),
            log=data.get("log"),
            macro=data.get("macro"),
            pos=data.get("pos"),
            proto=data.get("proto"),
            source=data.get("source"),
            sport=data.get("sport"),
        )

    def __repr__(self) -> str:
        """String representation."""
        parts = [f"{self.type.upper()}", str(self.action)]

        if self.proto:
            parts.append(str(self.proto).upper())

        if self.source:
            parts.append(f"from {self.source}")

        if self.sport:
            parts.append(f"sport {self.sport}")

        if self.dest:
            parts.append(f"to {self.dest}")

        if self.dport:
            parts.append(f"dport {self.dport}")

        status = "enabled" if self.enable else "disabled"
        parts.append(f"({status})")

        return " ".join(parts)


class FirewallManager:
    """
    High-level async firewall management for Proxmox VMs and Containers.

    Provides convenient methods for managing VM/CT firewall rules, options,
    aliases, and IP sets with full type safety.

    Example:
        async with ProxmoxAPI.create(...) as proxmox:
            # For QEMU VM
            fw = FirewallManager(proxmox, "pve", 100)

            # For LXC Container
            fw = FirewallManager(proxmox, "pve", 100, vm_type="lxc")

            # Add rule to allow SSH
            await fw.add_rule(
                FirewallRule(
                    action=FirewallRuleAction.ACCEPT,
                    type=FirewallRuleType.IN,
                    proto=FirewallProtocol.TCP,
                    dport=22,
                    comment="Allow SSH",
                )
            )

            # Enable firewall
            await fw.enable()
    """

    def __init__(
        self, proxmox: Any, node: str, vmid: int, vm_type: Literal["qemu", "lxc"] = "qemu"
    ) -> None:
        """
        Initialize firewall manager.

        Args:
            proxmox: ProxmoxAPI instance
            node: Node name
            vmid: VM/Container ID
            vm_type: Type of virtualization ("qemu" for VMs, "lxc" for containers)
        """
        self.proxmox = proxmox
        self.node = node
        self.vmid = vmid
        self.vm_type = vm_type

        # Support both QEMU VMs and LXC containers
        if vm_type == "lxc":
            self._fw_resource = proxmox.nodes(node).lxc(vmid).firewall
        else:
            self._fw_resource = proxmox.nodes(node).qemu(vmid).firewall

    # ============= Rules Management =============

    async def get_rules(self) -> list[FirewallRule]:
        """
        Get all firewall rules.

        Returns:
            List of FirewallRule instances
        """
        rules_data = await self._fw_resource.rules.get()

        return [FirewallRule.from_dict(rule) for rule in rules_data]

    async def get_rule(self, pos: int) -> FirewallRule:
        """
        Get specific firewall rule by position.

        Args:
            pos: Rule position (0-indexed)

        Returns:
            FirewallRule instance
        """
        rule_data = await self._fw_resource.rules(pos).get()

        return FirewallRule.from_dict(rule_data)

    async def add_rule(self, rule: FirewallRule) -> str:
        """
        Add new firewall rule.

        Args:
            rule: FirewallRule to add

        Returns:
            Rule position or task ID
        """
        result = await self._fw_resource.rules.post(**rule.to_dict())

        logger.info(f"Added firewall rule for VM {self.vmid}: {rule}")

        return result

    async def update_rule(self, pos: int, rule: FirewallRule) -> None:
        """
        Update existing firewall rule.

        Args:
            pos: Rule position to update
            rule: New rule configuration
        """
        await self._fw_resource.rules(pos).put(**rule.to_dict())

        logger.info(f"Updated firewall rule {pos} for VM {self.vmid}: {rule}")

    async def delete_rule(self, pos: int) -> None:
        """
        Delete firewall rule.

        Args:
            pos: Rule position to delete
        """
        await self._fw_resource.rules(pos).delete()

        logger.info(f"Deleted firewall rule {pos} for VM {self.vmid}")

    async def move_rule(self, pos: int, new_pos: int) -> None:
        """
        Move rule to new position.

        Args:
            pos: Current position
            new_pos: Target position
        """
        await self._fw_resource.rules(pos).put(moveto=new_pos)

        logger.info(f"Moved rule {pos} to {new_pos} for VM {self.vmid}")

    # ============= Options Management =============

    async def get_options(self) -> FirewallOptions:
        """
        Get firewall options.

        Returns:
            Firewall options model with easy attribute access
        """
        data = await self._fw_resource.options.get()
        return FirewallOptions.from_dict(data)

    async def enable(self) -> None:
        """Enable firewall for this VM."""
        await self._fw_resource.options.put(enable=1)

        logger.info(f"Enabled firewall for VM {self.vmid}")

    async def disable(self) -> None:
        """Disable firewall for this VM."""
        await self._fw_resource.options.put(enable=0)

        logger.info(f"Disabled firewall for VM {self.vmid}")

    async def set_options(
        self,
        *,
        enable: bool | None = None,
        dhcp: bool | None = None,
        ipfilter: bool | None = None,
        log_level_in: FirewallLogLevel | str | None = None,
        log_level_out: FirewallLogLevel | str | None = None,
        macfilter: bool | None = None,
        ndp: bool | None = None,
        policy_in: Literal["ACCEPT", "REJECT", "DROP"] | None = None,
        policy_out: Literal["ACCEPT", "REJECT", "DROP"] | None = None,
        radv: bool | None = None,
    ) -> None:
        """
        Set firewall options.

        Args:
            enable: Enable/disable firewall
            dhcp: Enable DHCP
            ipfilter: Enable default IP filters
            log_level_in: Log level for incoming traffic
            log_level_out: Log level for outgoing traffic
            macfilter: Enable MAC address filter
            ndp: Enable NDP (Neighbor Discovery Protocol)
            policy_in: Default policy for incoming traffic
            policy_out: Default policy for outgoing traffic
            radv: Allow sending Router Advertisement
        """
        options: dict[str, Any] = {}

        if enable is not None:
            options["enable"] = 1 if enable else 0
        if dhcp is not None:
            options["dhcp"] = 1 if dhcp else 0
        if ipfilter is not None:
            options["ipfilter"] = 1 if ipfilter else 0
        if log_level_in is not None:
            options["log_level_in"] = str(log_level_in)
        if log_level_out is not None:
            options["log_level_out"] = str(log_level_out)
        if macfilter is not None:
            options["macfilter"] = 1 if macfilter else 0
        if ndp is not None:
            options["ndp"] = 1 if ndp else 0
        if policy_in is not None:
            options["policy_in"] = policy_in
        if policy_out is not None:
            options["policy_out"] = policy_out
        if radv is not None:
            options["radv"] = 1 if radv else 0

        await self._fw_resource.options.put(**options)

        logger.info(f"Updated firewall options for VM {self.vmid}")

    # ============= Aliases Management =============

    async def get_aliases(self) -> list[FirewallAlias]:
        """
        Get all firewall aliases.

        Returns:
            List of FirewallAlias models
        """
        data = await self._fw_resource.aliases.get()
        return [FirewallAlias.from_dict(alias) for alias in data]

    async def get_alias(self, name: str) -> FirewallAlias:
        """
        Get a specific firewall alias by name.

        Args:
            name: Alias name

        Returns:
            FirewallAlias model

        Raises:
            ResourceException: If alias not found
        """
        data = await self._fw_resource.aliases(name).get()
        return FirewallAlias.from_dict(data)

    async def add_alias(self, name: str, cidr: str, comment: str | None = None) -> None:
        """
        Add firewall alias (IP/CIDR with a name).

        Args:
            name: Alias name
            cidr: IP address or CIDR
            comment: Optional comment
        """
        data: dict[str, Any] = {"name": name, "cidr": cidr}
        if comment:
            data["comment"] = comment

        await self._fw_resource.aliases.post(**data)

        logger.info(f"Added firewall alias '{name}' = {cidr} for VM {self.vmid}")

    async def update_alias(self, name: str, cidr: str, comment: str | None = None) -> None:
        """
        Update firewall alias.

        Args:
            name: Alias name
            cidr: New IP address or CIDR
            comment: New comment
        """
        data: dict[str, Any] = {"cidr": cidr}
        if comment:
            data["comment"] = comment

        await self._fw_resource.aliases(name).put(**data)

        logger.info(f"Updated firewall alias '{name}' for VM {self.vmid}")

    async def delete_alias(self, name: str) -> None:
        """
        Delete firewall alias.

        Args:
            name: Alias name to delete
        """
        await self._fw_resource.aliases(name).delete()

        logger.info(f"Deleted firewall alias '{name}' for VM {self.vmid}")

    # ============= IPSet Management =============

    async def get_ipsets(self) -> list[FirewallIPSet]:
        """
        Get all IP sets.

        Returns:
            List of FirewallIPSet models
        """
        data = await self._fw_resource.ipset.get()
        return [FirewallIPSet.from_dict(ipset) for ipset in data]

    async def create_ipset(self, name: str, comment: str | None = None) -> None:
        """
        Create new IP set.

        Args:
            name: IP set name
            comment: Optional comment
        """
        data: dict[str, Any] = {"name": name}
        if comment:
            data["comment"] = comment

        await self._fw_resource.ipset.post(**data)

        logger.info(f"Created IP set '{name}' for VM {self.vmid}")

    async def get_ipset_entries(self, name: str) -> list[FirewallIPSetEntry]:
        """
        Get entries in IP set.

        Args:
            name: IP set name

        Returns:
            List of FirewallIPSetEntry models
        """
        data = await self._fw_resource.ipset(name).get()
        return [FirewallIPSetEntry.from_dict(entry) for entry in data]

    async def add_ipset_entry(
        self, ipset_name: str, cidr: str, comment: str | None = None, nomatch: bool = False
    ) -> None:
        """
        Add entry to IP set.

        Args:
            ipset_name: IP set name
            cidr: IP address or CIDR
            comment: Optional comment
            nomatch: Exclude this IP from the set
        """
        data: dict[str, Any] = {"cidr": cidr}
        if comment:
            data["comment"] = comment
        if nomatch:
            data["nomatch"] = 1

        await self._fw_resource.ipset(ipset_name).post(**data)

        logger.info(f"Added {cidr} to IP set '{ipset_name}' for VM {self.vmid}")

    async def update_ipset_entry(
        self, ipset_name: str, cidr: str, comment: str | None = None, nomatch: bool | None = None
    ) -> None:
        """
        Update IP set entry.

        Args:
            ipset_name: IP set name
            cidr: IP address or CIDR
            comment: New comment
            nomatch: New nomatch value
        """
        data: dict[str, Any] = {}
        if comment is not None:
            data["comment"] = comment
        if nomatch is not None:
            data["nomatch"] = 1 if nomatch else 0

        await self._fw_resource.ipset(ipset_name)(cidr).put(**data)

        logger.info(f"Updated {cidr} in IP set '{ipset_name}' for VM {self.vmid}")

    async def delete_ipset_entry(self, ipset_name: str, cidr: str) -> None:
        """
        Delete entry from IP set.

        Args:
            ipset_name: IP set name
            cidr: IP address or CIDR to remove
        """
        await self._fw_resource.ipset(ipset_name)(cidr).delete()

        logger.info(f"Deleted {cidr} from IP set '{ipset_name}' for VM {self.vmid}")

    async def delete_ipset(self, name: str) -> None:
        """
        Delete entire IP set.

        Args:
            name: IP set name
        """
        await self._fw_resource.ipset(name).delete()

        logger.info(f"Deleted IP set '{name}' for VM {self.vmid}")

    # ============= Logs & References =============

    async def get_log(
        self,
        limit: int | None = None,
        start: int | None = None,
        since: int | None = None,
        until: int | None = None,
    ) -> list[FirewallLogEntry]:
        """
        Read firewall log.

        Args:
            limit: Maximum number of entries to return
            start: Start offset
            since: Display log since this UNIX epoch
            until: Display log until this UNIX epoch

        Returns:
            List of FirewallLogEntry models
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if start is not None:
            params["start"] = start
        if since is not None:
            params["since"] = since
        if until is not None:
            params["until"] = until

        data = await self._fw_resource.log.get(**params)
        return [FirewallLogEntry.from_dict(entry) for entry in data]

    async def get_refs(self, ref_type: Literal["alias", "ipset"] | None = None) -> list[FirewallRef]:
        """
        Get firewall references (aliases and IP sets that can be used in rules).

        Args:
            ref_type: Filter by type ("alias" or "ipset"), None for all

        Returns:
            List of FirewallRef models showing available references
        """
        params: dict[str, Any] = {}
        if ref_type is not None:
            params["type"] = ref_type

        data = await self._fw_resource.refs.get(**params)
        return [FirewallRef.from_dict(ref) for ref in data]

    # ============= Convenience Methods =============

    async def allow_ssh(self, source: str | None = None) -> None:
        """
        Add rule to allow SSH (port 22).

        Args:
            source: Optional source IP/CIDR to restrict access
        """
        rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=22,
            source=source,
            comment="Allow SSH",
        )
        await self.add_rule(rule)

    async def allow_http(self, source: str | None = None) -> None:
        """
        Add rule to allow HTTP (port 80).

        Args:
            source: Optional source IP/CIDR to restrict access
        """
        rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=80,
            source=source,
            comment="Allow HTTP",
        )
        await self.add_rule(rule)

    async def allow_https(self, source: str | None = None) -> None:
        """
        Add rule to allow HTTPS (port 443).

        Args:
            source: Optional source IP/CIDR to restrict access
        """
        rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=FirewallProtocol.TCP,
            dport=443,
            source=source,
            comment="Allow HTTPS",
        )
        await self.add_rule(rule)

    async def allow_port(
        self,
        port: int,
        proto: FirewallProtocol | str = FirewallProtocol.TCP,
        source: str | None = None,
        comment: str | None = None,
    ) -> None:
        """
        Add rule to allow specific port.

        Args:
            port: Port number
            proto: Protocol (tcp, udp, etc.)
            source: Optional source IP/CIDR
            comment: Optional comment
        """
        rule = FirewallRule(
            action=FirewallRuleAction.ACCEPT,
            type=FirewallRuleType.IN,
            proto=proto,
            dport=port,
            source=source,
            comment=comment or f"Allow {proto.upper()} port {port}",
        )
        await self.add_rule(rule)

    async def block_ip(self, ip: str, comment: str | None = None) -> None:
        """
        Add rule to block specific IP.

        Args:
            ip: IP address or CIDR to block
            comment: Optional comment
        """
        rule = FirewallRule(
            action=FirewallRuleAction.DROP,
            type=FirewallRuleType.IN,
            source=ip,
            comment=comment or f"Block {ip}",
        )
        await self.add_rule(rule)

    async def get_log_raw(self) -> ResponseData:
        """
        Get firewall log.

        Returns:
            Firewall log entries
        """
        return await self._fw_resource.log.get()

    async def get_refs_raw(self) -> ResponseData:
        """
        Get firewall references.

        Returns:
            Reference information
        """
        return await self._fw_resource.refs.get()


__all__ = [
    "FirewallManager",
    "FirewallRule",
    "FirewallRuleAction",
    "FirewallRuleType",
    "FirewallLogLevel",
    "FirewallProtocol",
]
