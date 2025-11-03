"""
Tests for proxmoxer.helpers.nodes module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from proxmoxer.helpers.nodes import (
    NodeManager,
    NodeStatus,
    NodeTime,
    DNSConfig,
    NetworkInterface,
    Certificate,
    APTUpdate,
    Subscription,
    VMType,
)


@pytest.fixture
def nodes_helper(mock_proxmox_api):
    """Create a NodeManager instance with mocked API."""
    helper = NodeManager(mock_proxmox_api, "test-node")
    # Store reference to node_api for easy access in tests
    helper._test_node_api = helper._node_api
    return helper


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperBasic:
    """Test basic node operations."""

    async def test_init(self, mock_proxmox_api):
        """Test NodeManager initialization."""
        helper = NodeManager(mock_proxmox_api, "test-node")
        assert helper.node == "test-node"
        assert helper.proxmox == mock_proxmox_api

    async def test_get_status(self, nodes_helper, sample_node_status):
        """Test getting node status."""
        nodes_helper._test_node_api.status.get.return_value = sample_node_status

        status = await nodes_helper.get_status()

        assert isinstance(status, NodeStatus)
        assert status.uptime == 123456
        assert status.cpu == 0.15
        assert status.maxcpu == 8
        assert status.mem == 4294967296
        nodes_helper._test_node_api.status.get.assert_called_once()

    async def test_get_time(self, nodes_helper):
        """Test getting node time."""
        time_data = {
            "time": 1603912756,
            "timezone": "Europe/Paris",
            "localtime": 1603916356,
        }
        nodes_helper._test_node_api.time.get.return_value = time_data

        node_time = await nodes_helper.get_time()

        assert isinstance(node_time, NodeTime)
        assert node_time.time == 1603912756
        assert node_time.timezone == "Europe/Paris"
        nodes_helper._test_node_api.time.get.assert_called_once()

    async def test_set_time(self, nodes_helper):
        """Test setting node timezone."""
        await nodes_helper.set_time(timezone="America/New_York")

        nodes_helper._test_node_api.time.put.assert_called_once_with(
            timezone="America/New_York"
        )


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperVMOperations:
    """Test VM/Container operations."""

    async def test_list_vms_all(self, nodes_helper):
        """Test listing all VMs and containers."""
        vm_data = {"vmid": 100, "name": "test-vm", "status": "running", "type": "qemu"}
        nodes_helper._test_node_api.qemu.get.return_value = [vm_data]
        nodes_helper._test_node_api.lxc.get.return_value = []

        vms = await nodes_helper.list_vms()

        assert len(vms) >= 1
        nodes_helper._test_node_api.qemu.get.assert_called_once()
        nodes_helper._test_node_api.lxc.get.assert_called_once()

    async def test_list_vms_qemu_only(self, nodes_helper):
        """Test listing only QEMU VMs."""
        vm_data = {"vmid": 100, "name": "test-vm", "status": "running", "type": "qemu"}
        nodes_helper._test_node_api.qemu.get.return_value = [vm_data]

        vms = await nodes_helper.list_vms(vm_type=VMType.QEMU)

        assert len(vms) >= 1
        nodes_helper._test_node_api.qemu.get.assert_called_once()

    async def test_create_snapshot(self, nodes_helper):
        """Test creating VM snapshot."""
        mock_vm_api = AsyncMock()
        mock_vm_api.snapshot.post.return_value = "UPID:test:snapshot"
        nodes_helper._test_node_api.qemu.return_value = mock_vm_api

        task = await nodes_helper.create_snapshot(
            vmid=100,
            vm_type=VMType.QEMU,
            snapname="test-snap",
            description="Test snapshot",
            vmstate=True,
        )

        assert task == "UPID:test:snapshot"
        nodes_helper._test_node_api.qemu.assert_called_with(100)
        mock_vm_api.snapshot.post.assert_called_once()

    async def test_start_vm(self, nodes_helper):
        """Test starting a VM."""
        mock_vm_api = AsyncMock()
        mock_status_api = AsyncMock()
        mock_status_api.start.post.return_value = "UPID:test:start"
        mock_vm_api.status = mock_status_api
        nodes_helper._test_node_api.qemu.return_value = mock_vm_api

        task = await nodes_helper.start_vm(100, VMType.QEMU)

        assert task == "UPID:test:start"
        mock_status_api.start.post.assert_called_once()

    async def test_stop_vm(self, nodes_helper):
        """Test stopping a VM."""
        mock_vm_api = AsyncMock()
        mock_status_api = AsyncMock()
        mock_status_api.stop.post.return_value = "UPID:test:stop"
        mock_vm_api.status = mock_status_api
        nodes_helper._test_node_api.qemu.return_value = mock_vm_api

        task = await nodes_helper.stop_vm(100, VMType.QEMU)

        assert task == "UPID:test:stop"
        mock_status_api.stop.post.assert_called_once()


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperNetworking:
    """Test network interface management."""

    async def test_list_network_interfaces(self, nodes_helper, sample_network_interface):
        """Test listing network interfaces."""
        nodes_helper._test_node_api.network.get.return_value = [sample_network_interface]

        interfaces = await nodes_helper.list_network_interfaces()

        assert len(interfaces) == 1
        assert isinstance(interfaces[0], NetworkInterface)
        assert interfaces[0].iface == "vmbr0"
        assert interfaces[0].type == "bridge"
        assert interfaces[0].address == "192.168.1.100"
        nodes_helper._test_node_api.network.get.assert_called_once()

    async def test_get_network_interface(self, nodes_helper, sample_network_interface):
        """Test getting specific network interface."""
        mock_iface_api = AsyncMock()
        mock_iface_api.get.return_value = sample_network_interface
        nodes_helper._test_node_api.network.return_value = mock_iface_api

        interface = await nodes_helper.get_network_interface("vmbr0")

        assert isinstance(interface, NetworkInterface)
        assert interface.iface == "vmbr0"
        assert interface.bridge_ports == "eno1"
        mock_iface_api.get.assert_called_once()

    async def test_create_network_interface(self, nodes_helper):
        """Test creating network interface."""
        await nodes_helper.create_network_interface(
            iface="vmbr1",
            type="bridge",
            address="192.168.2.1",
            netmask="255.255.255.0",
            autostart=True,
            bridge_ports="eno2",
            bridge_vlan_aware=True,
        )

        nodes_helper._test_node_api.network.post.assert_called_once()
        call_kwargs = nodes_helper._test_node_api.network.post.call_args[1]
        assert call_kwargs["iface"] == "vmbr1"
        assert call_kwargs["type"] == "bridge"
        assert call_kwargs["address"] == "192.168.2.1"
        assert call_kwargs["autostart"] == 1
        assert call_kwargs["bridge_vlan_aware"] == 1

    async def test_delete_network_interface(self, nodes_helper):
        """Test deleting network interface."""
        mock_iface_api = AsyncMock()
        nodes_helper._test_node_api.network.return_value = mock_iface_api

        await nodes_helper.delete_network_interface("vmbr1")

        mock_iface_api.delete.assert_called_once()

    async def test_reload_network_configuration(self, nodes_helper):
        """Test reloading network configuration."""
        nodes_helper._test_node_api.network.put.return_value = "UPID:test:netreload"

        task = await nodes_helper.reload_network_configuration()

        assert task == "UPID:test:netreload"
        nodes_helper._test_node_api.network.put.assert_called_once()

    async def test_revert_network_configuration(self, nodes_helper):
        """Test reverting network configuration."""
        await nodes_helper.revert_network_configuration()

        nodes_helper._test_node_api.network.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperCertificates:
    """Test certificate management."""

    async def test_get_certificates_info(self, nodes_helper, sample_certificate):
        """Test getting certificates information."""
        nodes_helper._test_node_api.certificates.info.get.return_value = [sample_certificate]

        certs = await nodes_helper.get_certificates_info()

        assert len(certs) == 1
        assert isinstance(certs[0], Certificate)
        assert certs[0].filename == "pveproxy-ssl.pem"
        assert certs[0].subject == "CN=proxmox.example.com"
        nodes_helper._test_node_api.certificates.info.get.assert_called_once()

    async def test_order_acme_certificate(self, nodes_helper):
        """Test ordering ACME certificate."""
        nodes_helper._test_node_api.certificates.acme.certificate.post.return_value = "UPID:test:acme"

        task = await nodes_helper.order_acme_certificate(force=True)

        assert task == "UPID:test:acme"
        nodes_helper._test_node_api.certificates.acme.certificate.post.assert_called_once()

    async def test_upload_custom_certificate(self, nodes_helper, sample_certificate):
        """Test uploading custom certificate."""
        nodes_helper._test_node_api.certificates.custom.post.return_value = [sample_certificate]

        cert_data = "-----BEGIN CERTIFICATE-----\nMIIC..."
        key_data = "-----BEGIN PRIVATE KEY-----\nMIIE..."

        certs = await nodes_helper.upload_custom_certificate(
            certificates=cert_data,
            key=key_data,
            restart=True,
        )

        assert len(certs) == 1
        assert isinstance(certs[0], Certificate)
        nodes_helper._test_node_api.certificates.custom.post.assert_called_once()

    async def test_delete_custom_certificate(self, nodes_helper):
        """Test deleting custom certificate."""
        await nodes_helper.delete_custom_certificate(restart=False)

        nodes_helper._test_node_api.certificates.custom.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperAPT:
    """Test APT package management."""

    async def test_list_apt_updates(self, nodes_helper, sample_apt_update):
        """Test listing APT updates."""
        nodes_helper._test_node_api.apt.update.get.return_value = [sample_apt_update]

        updates = await nodes_helper.list_apt_updates()

        assert len(updates) == 1
        assert isinstance(updates[0], APTUpdate)
        assert updates[0].Package == "proxmox-ve"
        assert updates[0].Version == "8.0.4"
        assert updates[0].OldVersion == "8.0.3"
        nodes_helper._test_node_api.apt.update.get.assert_called_once()

    async def test_update_apt_database(self, nodes_helper):
        """Test updating APT database."""
        nodes_helper._test_node_api.apt.update.post.return_value = "UPID:test:aptupdate"

        task = await nodes_helper.update_apt_database(notify=True, quiet=False)

        assert task == "UPID:test:aptupdate"
        nodes_helper._test_node_api.apt.update.post.assert_called_once()

    async def test_get_apt_repositories(self, nodes_helper):
        """Test getting APT repositories."""
        repos = {
            "files": [{"path": "/etc/apt/sources.list"}],
            "errors": [],
        }
        nodes_helper._test_node_api.apt.repositories.get.return_value = repos

        result = await nodes_helper.get_apt_repositories()

        assert result == repos
        nodes_helper._test_node_api.apt.repositories.get.assert_called_once()

    async def test_add_apt_repository(self, nodes_helper):
        """Test adding APT repository."""
        await nodes_helper.add_apt_repository("pve-no-subscription", "abc123")

        nodes_helper._test_node_api.apt.repositories.post.assert_called_once()

    async def test_change_apt_repository(self, nodes_helper):
        """Test changing APT repository."""
        await nodes_helper.change_apt_repository(
            index=0,
            enabled=True,
            digest="abc123",
        )

        nodes_helper._test_node_api.apt.repositories.put.assert_called_once()


@pytest.mark.unit
@pytest.mark.helpers
class TestNodesHelperSubscription:
    """Test subscription management."""

    async def test_get_subscription(self, nodes_helper, sample_subscription):
        """Test getting subscription info."""
        nodes_helper._test_node_api.subscription.get.return_value = sample_subscription

        sub = await nodes_helper.get_subscription()

        assert isinstance(sub, Subscription)
        assert sub.status == "active"
        assert sub.key == "pve1c-1234567890"
        assert sub.level == "c"
        nodes_helper._test_node_api.subscription.get.assert_called_once()

    async def test_set_subscription_key(self, nodes_helper):
        """Test setting subscription key."""
        await nodes_helper.set_subscription_key("pve1c-1234567890")

        nodes_helper._test_node_api.subscription.post.assert_called_once()

    async def test_update_subscription(self, nodes_helper):
        """Test updating subscription."""
        await nodes_helper.update_subscription(force=True)

        nodes_helper._test_node_api.subscription.put.assert_called_once()

    async def test_delete_subscription_key(self, nodes_helper):
        """Test deleting subscription key."""
        await nodes_helper.delete_subscription_key()

        nodes_helper._test_node_api.subscription.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.helpers
class TestDataclasses:
    """Test dataclass from_dict methods."""

    def test_node_status_from_dict(self, sample_node_status):
        """Test NodeStatus.from_dict()."""
        status = NodeStatus.from_dict(sample_node_status)

        assert status.uptime == 123456
        assert status.cpu == 0.15
        assert status.maxcpu == 8
        assert status.mem == 4294967296
        assert status.loadavg == [0.5, 0.6, 0.7]

    def test_network_interface_from_dict(self, sample_network_interface):
        """Test NetworkInterface.from_dict()."""
        iface = NetworkInterface.from_dict(sample_network_interface)

        assert iface.iface == "vmbr0"
        assert iface.type == "bridge"
        assert iface.address == "192.168.1.100"
        assert iface.autostart == 1

    def test_certificate_from_dict(self, sample_certificate):
        """Test Certificate.from_dict()."""
        cert = Certificate.from_dict(sample_certificate)

        assert cert.filename == "pveproxy-ssl.pem"
        assert cert.subject == "CN=proxmox.example.com"
        assert cert.notafter == 1735534356

    def test_apt_update_from_dict(self, sample_apt_update):
        """Test APTUpdate.from_dict()."""
        update = APTUpdate.from_dict(sample_apt_update)

        assert update.Package == "proxmox-ve"
        assert update.Version == "8.0.4"
        assert update.OldVersion == "8.0.3"

    def test_subscription_from_dict(self, sample_subscription):
        """Test Subscription.from_dict()."""
        sub = Subscription.from_dict(sample_subscription)

        assert sub.status == "active"
        assert sub.key == "pve1c-1234567890"
        assert sub.level == "c"
