"""
Comprehensive tests for NodeManager helper - Part 2.
Tests for Network, Certificates, APT, Subscription, and System operations.
"""

import pytest
from proxmoxer.helpers.nodes import (
    NodeManager,
    NetworkInterface,
    Certificate,
    APTUpdate,
    Subscription,
)


@pytest.fixture
def node_manager(mock_proxmox):
    """Create NodeManager instance with mocked API."""
    return NodeManager(mock_proxmox, "pve1")


# ==================== Network Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestNetwork:
    async def test_list_network_interfaces(self, node_manager, sample_network_interface_data):
        """Test listing network interfaces."""
        node_manager._node_api.network.get.return_value = [sample_network_interface_data]

        result = await node_manager.list_network_interfaces()

        assert len(result) == 1
        assert isinstance(result[0], NetworkInterface)
        assert result[0].iface == "vmbr0"
        assert result[0].type == "bridge"

    async def test_get_network_interface(self, node_manager, sample_network_interface_data):
        """Test getting specific network interface."""
        node_manager._node_api.network("vmbr0").get.return_value = sample_network_interface_data

        result = await node_manager.get_network_interface("vmbr0")

        assert isinstance(result, NetworkInterface)
        assert result.iface == "vmbr0"

    async def test_create_network_interface(self, node_manager):
        """Test creating network interface."""
        await node_manager.create_network_interface(
            iface="vmbr1",
            type="bridge",
            autostart=True,
            address="192.168.2.1",
            netmask="255.255.255.0",
            bridge_ports="eno2"
        )

        node_manager._node_api.network.post.assert_called_once()
        call_args = node_manager._node_api.network.post.call_args[1]
        assert call_args["iface"] == "vmbr1"
        assert call_args["type"] == "bridge"
        assert call_args["autostart"] == 1

    async def test_update_network_interface(self, node_manager):
        """Test updating network interface."""
        await node_manager.update_network_interface(
            iface="vmbr0",
            address="192.168.1.200",
            comments="Updated interface"
        )

        node_manager._node_api.network("vmbr0").put.assert_called_once()

    async def test_delete_network_interface(self, node_manager):
        """Test deleting network interface."""
        await node_manager.delete_network_interface("vmbr1")

        node_manager._node_api.network("vmbr1").delete.assert_called_once()

    async def test_reload_network_configuration(self, node_manager):
        """Test reloading network configuration."""
        node_manager._node_api.network.put.return_value = "UPID:test"

        result = await node_manager.reload_network_configuration()

        assert result == "UPID:test"

    async def test_revert_network_configuration(self, node_manager):
        """Test reverting network configuration."""
        await node_manager.revert_network_configuration()

        node_manager._node_api.network.delete.assert_called_once()


# ==================== Certificates Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestCertificates:
    async def test_get_certificates_info(self, node_manager):
        """Test getting certificates info."""
        cert_data = [
            {
                "filename": "pveproxy-ssl.pem",
                "fingerprint": "AA:BB:CC",
                "subject": "CN=pve",
                "issuer": "CN=Proxmox",
                "notbefore": 1603912756,
                "notafter": 1735534356,
            }
        ]
        node_manager._node_api.certificates.info.get.return_value = cert_data

        result = await node_manager.get_certificates_info()

        assert len(result) == 1
        assert isinstance(result[0], Certificate)
        assert result[0].filename == "pveproxy-ssl.pem"

    async def test_order_acme_certificate(self, node_manager):
        """Test ordering ACME certificate."""
        node_manager._node_api.certificates.acme.certificate.post.return_value = "UPID:test"

        result = await node_manager.order_acme_certificate(force=True)

        assert result == "UPID:test"
        call_args = node_manager._node_api.certificates.acme.certificate.post.call_args[1]
        assert call_args["force"] == 1

    async def test_renew_acme_certificate(self, node_manager):
        """Test renewing ACME certificate."""
        node_manager._node_api.certificates.acme.certificate.put.return_value = "UPID:test"

        result = await node_manager.renew_acme_certificate()

        assert result == "UPID:test"

    async def test_revoke_acme_certificate(self, node_manager):
        """Test revoking ACME certificate."""
        node_manager._node_api.certificates.acme.certificate.delete.return_value = "Success"

        result = await node_manager.revoke_acme_certificate()

        assert result == "Success"

    async def test_upload_custom_certificate(self, node_manager):
        """Test uploading custom certificate."""
        cert_pem = "-----BEGIN CERTIFICATE-----\nMIIC...\n-----END CERTIFICATE-----"
        key_pem = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----"

        cert_data = [
            {"filename": "custom.pem", "fingerprint": "DD:EE:FF"}
        ]
        node_manager._node_api.certificates.custom.post.return_value = cert_data

        result = await node_manager.upload_custom_certificate(
            certificates=cert_pem,
            key=key_pem,
            force=True,
            restart=True
        )

        assert len(result) == 1
        assert isinstance(result[0], Certificate)

    async def test_delete_custom_certificate(self, node_manager):
        """Test deleting custom certificate."""
        await node_manager.delete_custom_certificate(restart=True)

        node_manager._node_api.certificates.custom.delete.assert_called_once()


# ==================== APT Package Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestAPTManagement:
    async def test_list_apt_updates(self, node_manager):
        """Test listing APT updates."""
        updates_data = [
            {
                "Package": "proxmox-ve",
                "Title": "Proxmox VE",
                "Arch": "amd64",
                "Description": "The Proxmox Virtual Environment",
                "Version": "8.0.4",
                "OldVersion": "8.0.3",
            }
        ]
        node_manager._node_api.apt.update.get.return_value = updates_data

        result = await node_manager.list_apt_updates()

        assert len(result) == 1
        assert isinstance(result[0], APTUpdate)
        assert result[0].Package == "proxmox-ve"
        assert result[0].Version == "8.0.4"

    async def test_update_apt_database(self, node_manager):
        """Test updating APT database."""
        node_manager._node_api.apt.update.post.return_value = "UPID:test"

        result = await node_manager.update_apt_database(notify=True, quiet=True)

        assert result == "UPID:test"
        call_args = node_manager._node_api.apt.update.post.call_args[1]
        assert call_args["notify"] == 1
        assert call_args["quiet"] == 1

    async def test_get_package_changelog(self, node_manager):
        """Test getting package changelog."""
        changelog = "proxmox-ve (8.0.4) stable; urgency=medium\n\n  * New features"
        node_manager._node_api.apt.changelog.get.return_value = changelog

        result = await node_manager.get_package_changelog("proxmox-ve", "8.0.4")

        assert result == changelog

    async def test_get_package_versions(self, node_manager):
        """Test getting package versions."""
        versions = [
            {"Package": "proxmox-ve", "Version": "8.0.4", "OldVersion": "8.0.3"}
        ]
        node_manager._node_api.apt.versions.get.return_value = versions

        result = await node_manager.get_package_versions()

        assert result == versions

    async def test_get_apt_repositories(self, node_manager):
        """Test getting APT repositories."""
        repos = {
            "files": [
                {
                    "path": "/etc/apt/sources.list",
                    "file_type": "list",
                }
            ]
        }
        node_manager._node_api.apt.repositories.get.return_value = repos

        result = await node_manager.get_apt_repositories()

        assert result == repos

    async def test_add_apt_repository(self, node_manager):
        """Test adding APT repository."""
        await node_manager.add_apt_repository(
            handle="pve-no-subscription",
            digest="abc123"
        )

        node_manager._node_api.apt.repositories.put.assert_called_once()

    async def test_change_apt_repository(self, node_manager):
        """Test changing APT repository."""
        await node_manager.change_apt_repository(
            index=0,
            enabled=True,
            digest="abc123"
        )

        node_manager._node_api.apt.repositories.post.assert_called_once()
        call_args = node_manager._node_api.apt.repositories.post.call_args[1]
        assert call_args["enabled"] == 1


# ==================== Subscription Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestSubscription:
    async def test_get_subscription(self, node_manager):
        """Test getting subscription info."""
        sub_data = {
            "status": "active",
            "key": "pve1c-1234567890",
            "level": "c",
            "productname": "Proxmox VE Community",
            "nextduedate": "2024-01-01",
        }
        node_manager._node_api.subscription.get.return_value = sub_data

        result = await node_manager.get_subscription()

        assert isinstance(result, Subscription)
        assert result.status == "active"
        assert result.key == "pve1c-1234567890"

    async def test_set_subscription_key(self, node_manager):
        """Test setting subscription key."""
        await node_manager.set_subscription_key("pve1c-0987654321")

        node_manager._node_api.subscription.put.assert_called_once_with(key="pve1c-0987654321")

    async def test_update_subscription(self, node_manager):
        """Test updating subscription."""
        await node_manager.update_subscription(force=True)

        node_manager._node_api.subscription.post.assert_called_once()

    async def test_delete_subscription_key(self, node_manager):
        """Test deleting subscription key."""
        await node_manager.delete_subscription_key()

        node_manager._node_api.subscription.delete.assert_called_once()


# ==================== System Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestSystem:
    async def test_reboot_node(self, node_manager):
        """Test rebooting node."""
        node_manager._node_api.status.post.return_value = "OK"

        result = await node_manager.reboot_node()

        assert result == "OK"
        node_manager._node_api.status.post.assert_called_once_with(command="reboot")

    async def test_shutdown_node(self, node_manager):
        """Test shutting down node."""
        node_manager._node_api.status.post.return_value = "OK"

        result = await node_manager.shutdown_node()

        assert result == "OK"
        node_manager._node_api.status.post.assert_called_once_with(command="shutdown")


# ==================== Dataclass from_dict Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
class TestDataclasses:
    """Test all dataclass from_dict methods."""

    def test_node_status_from_dict(self, sample_node_status_full):
        """Test NodeStatus.from_dict."""
        from proxmoxer.helpers.nodes import NodeStatus

        result = NodeStatus.from_dict(sample_node_status_full)

        assert isinstance(result, NodeStatus)
        assert result.cpu == 0.15
        assert result.boot_info.mode == "efi"

    def test_vm_from_dict(self, sample_vm_data):
        """Test VM.from_dict."""
        from proxmoxer.helpers.nodes import VM

        result = VM.from_dict(sample_vm_data)

        assert isinstance(result, VM)
        assert result.vmid == 100
        assert result.name == "test-vm"

    def test_service_from_dict(self, sample_service_data):
        """Test Service.from_dict."""
        from proxmoxer.helpers.nodes import Service

        result = Service.from_dict(sample_service_data)

        assert isinstance(result, Service)
        assert result.name == "pveproxy"

    def test_network_interface_from_dict(self, sample_network_interface_data):
        """Test NetworkInterface.from_dict."""
        from proxmoxer.helpers.nodes import NetworkInterface

        result = NetworkInterface.from_dict(sample_network_interface_data)

        assert isinstance(result, NetworkInterface)
        assert result.iface == "vmbr0"

    def test_dns_config_from_dict(self):
        """Test DNSConfig.from_dict."""
        from proxmoxer.helpers.nodes import DNSConfig

        data = {
            "dns1": "8.8.8.8",
            "dns2": "8.8.4.4",
            "search": "example.com",
        }

        result = DNSConfig.from_dict(data)

        assert isinstance(result, DNSConfig)
        assert result.dns1 == "8.8.8.8"

    def test_snapshot_from_dict(self):
        """Test Snapshot.from_dict."""
        from proxmoxer.helpers.nodes import Snapshot

        data = {
            "name": "snap1",
            "snaptime": 1603912756,
            "description": "Test snapshot",
            "vmstate": 1,
        }

        result = Snapshot.from_dict(data)

        assert isinstance(result, Snapshot)
        assert result.name == "snap1"
        assert result.vmstate is True

    def test_term_proxy_from_dict(self):
        """Test TermProxy.from_dict."""
        from proxmoxer.helpers.nodes import TermProxy

        data = {
            "port": 3128,
            "ticket": "PVE:ticket",
            "upid": "UPID:test",
            "user": "root@pam",
        }

        result = TermProxy.from_dict(data)

        assert isinstance(result, TermProxy)
        assert result.port == 3128

    def test_vnc_info_from_dict(self):
        """Test VNCInfo.from_dict."""
        from proxmoxer.helpers.nodes import VNCInfo

        data = {
            "port": 5900,
            "ticket": "PVE:ticket",
            "cert": "-----BEGIN CERTIFICATE-----",
        }

        result = VNCInfo.from_dict(data)

        assert isinstance(result, VNCInfo)
        assert result.port == 5900


# ==================== Edge Cases & Error Handling ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error handling."""

    async def test_get_vm_auto_detect_type(self, node_manager, sample_vm_data):
        """Test auto-detecting VM type."""
        # First try fails (not QEMU)
        node_manager._node_api.qemu(100).status.current.get.side_effect = Exception("Not found")
        # Second try succeeds (LXC)
        node_manager._node_api.lxc(100).status.current.get.return_value = sample_vm_data

        result = await node_manager.get_vm(100, vm_type=None)

        assert result.type == "lxc"

    async def test_list_storage_content_with_filters(self, node_manager):
        """Test listing storage content with filters."""
        content_data = [{"volid": "local:100/vm-100-disk-0.qcow2", "format": "qcow2", "size": 10737418240}]
        node_manager._node_api.storage("local").content.get.return_value = content_data

        result = await node_manager.list_storage_content(
            "local",
            content="images",
            vmid=100
        )

        assert len(result) == 1
        call_args = node_manager._node_api.storage("local").content.get.call_args[1]
        assert call_args["content"] == "images"
        assert call_args["vmid"] == 100

    async def test_create_network_interface_with_vlan(self, node_manager):
        """Test creating VLAN interface."""
        await node_manager.create_network_interface(
            iface="vmbr0.100",
            type="vlan",
            vlan_raw_device="vmbr0",
            vlan_id=100
        )

        call_args = node_manager._node_api.network.post.call_args[1]
        assert "vlan_raw_device" in call_args or "vlan-raw-device" in call_args

    async def test_backup_vm_with_all_options(self, node_manager):
        """Test backup with all options."""
        node_manager._node_api.vzdump.post.return_value = "UPID:test"

        result = await node_manager.backup_vm(
            vmid=100,
            storage="backup-storage",
            mode="suspend",
            compress="lzo",
            remove=True,
            notes="Full backup with all options"
        )

        assert result == "UPID:test"
        call_args = node_manager._node_api.vzdump.post.call_args[1]
        assert call_args["mode"] == "suspend"
        assert call_args["compress"] == "lzo"
        assert call_args["remove"] == 1
