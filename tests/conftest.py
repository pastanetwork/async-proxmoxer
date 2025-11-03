"""
Pytest configuration and fixtures for async-proxmoxer tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any, Dict


class MockNodeAPI:
    """Custom mock for node API that handles both sync and async calls properly."""

    def __init__(self):
        # Create async mock attributes for all endpoints
        self.status = AsyncMock()
        self.version = AsyncMock()
        self.time = AsyncMock()
        self.dns = AsyncMock()
        self.tasks = AsyncMock()
        self.services = AsyncMock()
        self.storage = AsyncMock()
        self.disks = AsyncMock()
        self.network = AsyncMock()
        self.certificates = AsyncMock()
        self.apt = AsyncMock()
        self.subscription = AsyncMock()
        self.ceph = AsyncMock()
        self.firewall = AsyncMock()
        self.qemu = Mock(return_value=AsyncMock())
        self.lxc = Mock(return_value=AsyncMock())

        # HTTP methods
        self.get = AsyncMock(return_value={"data": "test"})
        self.post = AsyncMock(return_value="UPID:test")
        self.put = AsyncMock(return_value={"data": "updated"})
        self.delete = AsyncMock(return_value=None)


@pytest.fixture
def mock_proxmox_api():
    """
    Mock ProxmoxAPI instance with proper sync/async separation.

    Returns a mock that can be used to test helpers without actual API calls.
    """
    mock = Mock()

    # nodes() is a regular function that returns a MockNodeAPI
    def nodes_factory(node_name):
        return MockNodeAPI()

    mock.nodes = Mock(side_effect=nodes_factory)
    mock.cluster = Mock(return_value=AsyncMock())
    mock.access = Mock(return_value=AsyncMock())
    mock.storage = Mock(return_value=AsyncMock())
    mock.pools = Mock(return_value=AsyncMock())

    return mock


@pytest.fixture
def mock_node_api():
    """
    Mock for a single node API endpoint.

    Structure: proxmox.nodes('node-name')
    """
    return MockNodeAPI()


@pytest.fixture
def sample_node_status() -> Dict[str, Any]:
    """Sample node status response."""
    return {
        "uptime": 123456,
        "cpu": 0.15,
        "maxcpu": 8,
        "mem": 4294967296,
        "maxmem": 16777216000,
        "swap": 0,
        "maxswap": 8589934592,
        "disk": 10737418240,
        "maxdisk": 107374182400,
        "loadavg": [0.5, 0.6, 0.7],
        "kversion": "Linux 6.2.16-3-pve",
        "cpuinfo": "Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz",
        "pveversion": "pve-manager/8.0.4/d258a813cfa6b390",
    }


@pytest.fixture
def sample_vm_status() -> Dict[str, Any]:
    """Sample VM status response."""
    return {
        "vmid": 100,
        "status": "running",
        "name": "test-vm",
        "uptime": 12345,
        "cpus": 2,
        "maxmem": 2147483648,
        "mem": 1073741824,
        "maxdisk": 32212254720,
        "disk": 10737418240,
        "netin": 1024000,
        "netout": 2048000,
        "diskread": 1024000000,
        "diskwrite": 2048000000,
        "cpu": 0.25,
        "template": 0,
        "pid": 12345,
    }


@pytest.fixture
def sample_task_status() -> Dict[str, Any]:
    """Sample task status response."""
    return {
        "upid": "UPID:node1:00001234:00000000:5F9A1234:vncproxy:100:root@pam:",
        "node": "node1",
        "pid": 1234,
        "pstart": 0,
        "starttime": 1603912756,
        "type": "vncproxy",
        "id": "100",
        "user": "root@pam",
        "status": "running",
    }


@pytest.fixture
def sample_network_interface() -> Dict[str, Any]:
    """Sample network interface response."""
    return {
        "iface": "vmbr0",
        "type": "bridge",
        "active": 1,
        "autostart": 1,
        "address": "192.168.1.100",
        "netmask": "255.255.255.0",
        "gateway": "192.168.1.1",
        "bridge_ports": "eno1",
        "bridge_stp": "off",
        "bridge_fd": "0",
    }


@pytest.fixture
def sample_certificate() -> Dict[str, Any]:
    """Sample certificate response."""
    return {
        "filename": "pveproxy-ssl.pem",
        "subject": "CN=proxmox.example.com",
        "issuer": "CN=Proxmox Virtual Environment",
        "notbefore": 1603912756,
        "notafter": 1735534356,
        "san": ["DNS:proxmox.example.com", "IP:192.168.1.100"],
        "fingerprint": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD",
        "pem": "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----",
    }


@pytest.fixture
def sample_apt_update() -> Dict[str, Any]:
    """Sample APT update package response."""
    return {
        "Package": "proxmox-ve",
        "Title": "Proxmox Virtual Environment",
        "Version": "8.0.4",
        "OldVersion": "8.0.3",
        "Priority": "optional",
        "Section": "admin",
        "Origin": "Proxmox",
        "Description": "The Proxmox Virtual Environment",
    }


@pytest.fixture
def sample_subscription() -> Dict[str, Any]:
    """Sample subscription response."""
    return {
        "status": "active",
        "key": "pve1c-1234567890",
        "level": "c",
        "productname": "Proxmox VE Community Subscription",
        "regdate": "2023-01-01 00:00:00",
        "nextduedate": "2024-01-01",
        "url": "https://www.proxmox.com/products/proxmox-ve/subscription-service-plans",
    }


@pytest.fixture
def mock_async_response():
    """
    Factory fixture for creating mock async responses.

    Usage:
        response = mock_async_response({"key": "value"}, status=200)
    """
    def _create_response(data: Any = None, status: int = 200, error: str | None = None):
        mock = AsyncMock()
        mock.status = status

        if error:
            mock.json = AsyncMock(side_effect=Exception(error))
            mock.text = AsyncMock(return_value=error)
        else:
            mock.json = AsyncMock(return_value={"data": data} if data else {})
            mock.text = AsyncMock(return_value=str(data) if data else "")

        return mock

    return _create_response


# Pytest-asyncio configuration markers
def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "helpers: Tests for helper modules"
    )
