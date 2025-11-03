"""
Pytest configuration and fixtures for helper module tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any


class AsyncMockAPI:
    """
    Generic async mock for Proxmox API endpoints.
    Automatically creates async mocks for any attribute access.
    """

    def __init__(self):
        self._mocks = {}

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        if name not in self._mocks:
            # Check if this is a known HTTP method
            if name in ('get', 'post', 'put', 'delete'):
                self._mocks[name] = AsyncMock()
            else:
                # Create a callable that returns another AsyncMockAPI
                def _create_child(*args, **kwargs):
                    return AsyncMockAPI()
                self._mocks[name] = Mock(side_effect=_create_child)

        return self._mocks[name]

    def __call__(self, *args, **kwargs):
        """Allow the mock to be called (for parameterized endpoints)."""
        return AsyncMockAPI()


@pytest.fixture
def mock_proxmox():
    """
    Mock Proxmoxer instance with automatic async API creation.

    Returns a mock that automatically creates nested async mocks
    for any attribute access, supporting chains like:
    proxmox.nodes(node).qemu(vmid).status.start.post()
    """
    return AsyncMockAPI()


@pytest.fixture
def mock_node_api():
    """Mock for node-level API operations."""
    return AsyncMockAPI()


# ========== NodeManager Fixtures ==========

@pytest.fixture
def sample_node_status_full():
    """Complete node status with all nested objects."""
    return {
        "cpu": 0.15,
        "loadavg": ["0.5", "0.6", "0.7"],
        "pveversion": "pve-manager/8.0.4/d258a813cfa6b390",
        "boot-info": {
            "mode": "efi",
            "secureboot": 1,
        },
        "cpuinfo": {
            "cores": 8,
            "cpus": 16,
            "model": "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
            "sockets": 2,
        },
        "current-kernel": {
            "machine": "x86_64",
            "release": "6.2.16-3-pve",
            "sysname": "Linux",
            "version": "#1 SMP PREEMPT_DYNAMIC",
        },
        "memory": {
            "available": 12884901888,
            "free": 8589934592,
            "total": 16777216000,
            "used": 4187282408,
        },
        "rootfs": {
            "avail": 85899345920,
            "free": 96636764160,
            "total": 107374182400,
            "used": 10737418240,
        },
    }


@pytest.fixture
def sample_vm_data():
    """Sample VM data."""
    return {
        "vmid": 100,
        "name": "test-vm",
        "status": "running",
        "type": "qemu",
        "uptime": 12345,
        "cpus": 2,
        "maxmem": 2147483648,
        "mem": 1073741824,
        "maxdisk": 32212254720,
        "disk": 10737418240,
        "netin": 1024000,
        "netout": 2048000,
        "cpu": 0.25,
        "template": 0,
    }


@pytest.fixture
def sample_service_data():
    """Sample service data."""
    return {
        "name": "pveproxy",
        "state": "running",
        "desc": "PVE API Proxy Server",
    }


@pytest.fixture
def sample_network_interface_data():
    """Sample network interface data."""
    return {
        "iface": "vmbr0",
        "type": "bridge",
        "active": 1,
        "autostart": 1,
        "address": "192.168.1.100",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "bridge_ports": "eno1",
    }


# ========== AccessManager Fixtures ==========

@pytest.fixture
def sample_user_data():
    """Sample user data."""
    return {
        "userid": "user@pve",
        "email": "user@example.com",
        "firstname": "Test",
        "lastname": "User",
        "groups": "admin,ops",
        "enable": 1,
        "expire": 0,
    }


@pytest.fixture
def sample_group_data():
    """Sample group data."""
    return {
        "groupid": "admin",
        "comment": "Administrators",
        "users": "user1@pve,user2@pve",
    }


@pytest.fixture
def sample_role_data():
    """Sample role data."""
    return {
        "roleid": "Administrator",
        "privs": "VM.Allocate,Datastore.Allocate,VM.Config.Disk",
        "special": 1,
    }


# ========== ClusterManager Fixtures ==========

@pytest.fixture
def sample_cluster_resource():
    """Sample cluster resource."""
    return {
        "id": "node/pve1",
        "type": "node",
        "status": "online",
        "node": "pve1",
        "cpu": 0.15,
        "maxcpu": 16,
        "mem": 4187282408,
        "maxmem": 16777216000,
    }


@pytest.fixture
def sample_ha_resource():
    """Sample HA resource."""
    return {
        "sid": "vm:100",
        "state": "started",
        "group": "production",
        "max_restart": 1,
        "max_relocate": 1,
    }


@pytest.fixture
def sample_backup_job():
    """Sample backup job."""
    return {
        "id": "backup-daily",
        "enabled": 1,
        "schedule": "02:00",
        "storage": "backup-storage",
        "mode": "snapshot",
        "compress": "zstd",
    }


# ========== DiskManager Fixtures ==========

@pytest.fixture
def sample_disk_data():
    """Sample disk data."""
    return {
        "devpath": "/dev/sda",
        "model": "Samsung SSD 970",
        "size": 1000204886016,
        "serial": "S5GXNX0N123456",
        "vendor": "Samsung",
        "type": "ssd",
        "health": "PASSED",
    }


@pytest.fixture
def sample_smart_info():
    """Sample SMART info."""
    return {
        "health": "PASSED",
        "type": "ssd",
        "attributes": [],
    }


# ========== FirewallManager Fixtures ==========

@pytest.fixture
def sample_firewall_rule():
    """Sample firewall rule."""
    return {
        "action": "ACCEPT",
        "type": "in",
        "enable": 1,
        "proto": "tcp",
        "dport": "22",
        "comment": "Allow SSH",
        "pos": 0,
    }


@pytest.fixture
def sample_firewall_options():
    """Sample firewall options."""
    return {
        "enable": 1,
        "dhcp": 0,
        "ipfilter": 1,
        "policy_in": "DROP",
        "policy_out": "ACCEPT",
    }


# ========== CephManager Fixtures ==========

@pytest.fixture
def sample_ceph_osd():
    """Sample Ceph OSD."""
    return {
        "id": 0,
        "status": "up",
        "weight": 1.0,
        "reweight": 1.0,
        "host": "pve1",
        "in": 1,
        "up": 1,
    }


@pytest.fixture
def sample_ceph_pool():
    """Sample Ceph pool."""
    return {
        "pool": 1,
        "pool_name": "rbd",
        "size": 3,
        "min_size": 2,
        "pg_num": 128,
        "type": "replicated",
    }


# ========== StorageManager Fixtures ==========

@pytest.fixture
def sample_storage_data():
    """Sample storage data."""
    return {
        "storage": "local",
        "type": "dir",
        "content": "vztmpl,iso,backup",
        "path": "/var/lib/vz",
        "shared": 0,
        "disable": 0,
    }


# ========== SDNManager Fixtures ==========

@pytest.fixture
def sample_vnet_data():
    """Sample VNet data."""
    return {
        "vnet": "vnet100",
        "zone": "zone1",
        "tag": 100,
        "alias": "test-network",
    }


@pytest.fixture
def sample_zone_data():
    """Sample zone data."""
    return {
        "zone": "zone1",
        "type": "vxlan",
        "bridge": "vmbr0",
        "mtu": 1500,
    }


# ========== PoolManager Fixtures ==========

@pytest.fixture
def sample_pool_data():
    """Sample pool data."""
    return {
        "poolid": "production",
        "comment": "Production VMs",
        "members": [
            {
                "id": "qemu/100",
                "type": "qemu",
                "node": "pve1",
                "vmid": 100,
            }
        ],
    }


# ========== TasksHelper Fixtures ==========

@pytest.fixture
def sample_task_data():
    """Sample task data."""
    return {
        "upid": "UPID:pve1:00001234:00000000:5F9A1234:vncproxy:100:root@pam:",
        "node": "pve1",
        "pid": 1234,
        "pstart": 0,
        "starttime": 1603912756,
        "type": "vncproxy",
        "id": "100",
        "user": "root@pam",
        "status": "stopped",
        "exitstatus": "OK",
    }


# ========== NotificationManager Fixtures ==========

@pytest.fixture
def sample_smtp_endpoint():
    """Sample SMTP endpoint."""
    return {
        "name": "email",
        "type": "smtp",
        "server": "smtp.example.com",
        "port": 587,
        "mailto": "admin@example.com",
        "disable": 0,
    }


@pytest.fixture
def sample_notification_matcher():
    """Sample notification matcher."""
    return {
        "name": "critical",
        "target": "email",
        "mode": "all",
        "match-severity": "error",
        "disable": 0,
    }
