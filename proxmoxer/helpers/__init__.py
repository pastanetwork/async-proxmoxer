"""
Proxmoxer Helpers

High-level helpers for common Proxmox operations.
"""

from .firewall import (
    FirewallManager,
    FirewallRule,
    FirewallRuleAction,
    FirewallRuleType,
    FirewallProtocol,
    FirewallLogLevel,
    FirewallOptions,
    FirewallAlias,
    FirewallIPSet,
    FirewallIPSetEntry,
    FirewallRef,
    FirewallLogEntry,
)

from .access import (
    AccessManager,
    User,
    Group,
    Role,
    ACL,
    Domain,
    APIToken,
    TFAType,
)

from .cluster import (
    ClusterManager,
    ClusterStatus,
    ClusterResource,
    HAResource,
    HAGroup,
    HAState,
    BackupJob,
    BackupMode,
    BackupCompression,
    ReplicationJob,
    ACMEAccount,
)

from .nodes import (
    NodeManager,
    NodeStatus,
    VM,
    VMStatus,
    VMType,
    Service,
    StorageContent,
    Snapshot,
)

from .pools import (
    PoolManager,
    Pool,
)

from .storage import (
    StorageManager,
    Storage,
    StorageType,
    ContentType,
)

from .sdn import (
    SDNManager,
    VNet,
    Zone,
    ZoneType,
    Controller,
    ControllerType,
    IPAM,
    IPAMType,
    DNS,
    Subnet,
)

from .ceph import (
    CephManager,
    CephOSD,
    CephMon,
    CephMgr,
    CephMDS,
    CephPool,
    CephFS,
    CephStatus,
    CephServiceType,
)

from .tasks import (
    TasksHelper,
    Task,
    TaskStatus,
)

from .notifications import (
    NotificationManager,
    NotificationEndpoint,
    SMTPEndpoint,
    GotifyEndpoint,
    NotificationMatcher,
    NotificationTarget,
    EndpointType,
    NotificationSeverity,
)

from .disks import (
    DiskManager,
    Disk,
    DiskType,
    SMARTInfo,
    LVMInfo,
    ZFSInfo,
    DirectoryInfo,
)

__all__ = [
    # Firewall
    "FirewallManager",
    "FirewallRule",
    "FirewallRuleAction",
    "FirewallRuleType",
    "FirewallProtocol",
    "FirewallLogLevel",
    "FirewallOptions",
    "FirewallAlias",
    "FirewallIPSet",
    "FirewallIPSetEntry",
    "FirewallRef",
    "FirewallLogEntry",
    # Access
    "AccessManager",
    "User",
    "Group",
    "Role",
    "ACL",
    "Domain",
    "APIToken",
    "TFAType",
    # Cluster
    "ClusterManager",
    "ClusterStatus",
    "ClusterResource",
    "HAResource",
    "HAGroup",
    "HAState",
    "BackupJob",
    "BackupMode",
    "BackupCompression",
    "ReplicationJob",
    "ACMEAccount",
    # Nodes
    "NodeManager",
    "NodeStatus",
    "VM",
    "VMStatus",
    "VMType",
    "Service",
    "StorageContent",
    "Snapshot",
    # Pools
    "PoolManager",
    "Pool",
    # Storage
    "StorageManager",
    "Storage",
    "StorageType",
    "ContentType",
    # SDN
    "SDNManager",
    "VNet",
    "Zone",
    "ZoneType",
    "Controller",
    "ControllerType",
    "IPAM",
    "IPAMType",
    "DNS",
    "Subnet",
    # Ceph
    "CephManager",
    "CephOSD",
    "CephMon",
    "CephMgr",
    "CephMDS",
    "CephPool",
    "CephFS",
    "CephStatus",
    "CephServiceType",
    # Tasks
    "TasksHelper",
    "Task",
    "TaskStatus",
    # Notifications
    "NotificationManager",
    "NotificationEndpoint",
    "SMTPEndpoint",
    "GotifyEndpoint",
    "NotificationMatcher",
    "NotificationTarget",
    "EndpointType",
    "NotificationSeverity",
    # Disks
    "DiskManager",
    "Disk",
    "DiskType",
    "SMARTInfo",
    "LVMInfo",
    "ZFSInfo",
    "DirectoryInfo",
]
