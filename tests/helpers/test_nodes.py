"""
Comprehensive tests for NodeManager helper.
Tests all 90+ methods of the NodeManager class.
"""

import pytest
from proxmoxer.helpers.nodes import (
    NodeManager,
    VMType,
    VMStatus,
    NodeStatus,
    VM,
    Service,
    NetworkInterface,
    Certificate,
    APTUpdate,
    Subscription,
    StorageContent,
    Snapshot,
    NodeVersion,
    NodeTime,
    DNSConfig,
    QemuAgentInfo,
    QemuAgentOSInfo,
    QemuAgentFSInfo,
    QemuAgentExecResult,
    TermProxy,
    VNCInfo,
)


@pytest.fixture
def node_manager(mock_proxmox):
    """Create NodeManager instance with mocked API."""
    return NodeManager(mock_proxmox, "pve1")


# ==================== Node Status Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestNodeStatus:
    async def test_get_status(self, node_manager, sample_node_status_full):
        """Test getting node status."""
        node_manager._node_api.status.get.return_value = sample_node_status_full

        result = await node_manager.get_status()

        assert isinstance(result, NodeStatus)
        assert result.cpu == 0.15
        assert result.pveversion == "pve-manager/8.0.4/d258a813cfa6b390"
        assert result.boot_info.mode == "efi"
        assert result.cpuinfo.cores == 8
        node_manager._node_api.status.get.assert_called_once()

    async def test_get_version(self, node_manager):
        """Test getting node version."""
        version_data = {
            "release": "8.0",
            "repoid": "d258a813",
            "version": "8.0.4",
        }
        node_manager._node_api.version.get.return_value = version_data

        result = await node_manager.get_version()

        assert isinstance(result, NodeVersion)
        assert result.release == "8.0"
        assert result.version == "8.0.4"

    async def test_get_time(self, node_manager):
        """Test getting node time."""
        time_data = {
            "localtime": 1603912756,
            "timezone": "Europe/Berlin",
        }
        node_manager._node_api.time.get.return_value = time_data

        result = await node_manager.get_time()

        assert isinstance(result, NodeTime)
        assert result.localtime == 1603912756
        assert result.timezone == "Europe/Berlin"

    async def test_set_time(self, node_manager):
        """Test setting node timezone."""
        await node_manager.set_time("Europe/Paris")

        node_manager._node_api.time.put.assert_called_once_with(timezone="Europe/Paris")


# ==================== VM Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestVMManagement:
    async def test_list_vms_all(self, node_manager, sample_vm_data):
        """Test listing all VMs and containers."""
        qemu_data = [sample_vm_data.copy()]
        lxc_data = [{**sample_vm_data, "vmid": 101, "type": "lxc"}]

        node_manager._node_api.qemu.get.return_value = qemu_data
        node_manager._node_api.lxc.get.return_value = lxc_data

        result = await node_manager.list_vms()

        assert len(result) == 2
        assert all(isinstance(vm, VM) for vm in result)
        assert result[0].type == "qemu"
        assert result[1].type == "lxc"

    async def test_list_vms_qemu_only(self, node_manager, sample_vm_data):
        """Test listing only QEMU VMs."""
        node_manager._node_api.qemu.get.return_value = [sample_vm_data]

        result = await node_manager.list_vms(vm_type=VMType.QEMU)

        assert len(result) == 1
        assert result[0].type == "qemu"
        node_manager._node_api.lxc.get.assert_not_called()

    async def test_list_vms_lxc_only(self, node_manager, sample_vm_data):
        """Test listing only LXC containers."""
        lxc_data = {**sample_vm_data, "type": "lxc"}
        node_manager._node_api.lxc.get.return_value = [lxc_data]

        result = await node_manager.list_vms(vm_type=VMType.LXC)

        assert len(result) == 1
        assert result[0].type == "lxc"
        node_manager._node_api.qemu.get.assert_not_called()

    async def test_get_vm_qemu(self, node_manager, sample_vm_data):
        """Test getting QEMU VM details."""
        node_manager._node_api.qemu(100).status.current.get.return_value = sample_vm_data

        result = await node_manager.get_vm(100, VMType.QEMU)

        assert isinstance(result, VM)
        assert result.vmid == 100
        assert result.type == "qemu"

    async def test_get_vm_lxc(self, node_manager, sample_vm_data):
        """Test getting LXC container details."""
        node_manager._node_api.lxc(101).status.current.get.return_value = sample_vm_data

        result = await node_manager.get_vm(101, VMType.LXC)

        assert isinstance(result, VM)
        assert result.type == "lxc"

    async def test_get_vm_config_qemu(self, node_manager):
        """Test getting QEMU VM configuration."""
        config = {"cores": 4, "memory": 4096}
        node_manager._node_api.qemu(100).config.get.return_value = config

        result = await node_manager.get_vm_config(100, VMType.QEMU)

        assert result == config

    async def test_update_vm_config(self, node_manager):
        """Test updating VM configuration."""
        await node_manager.update_vm_config(100, VMType.QEMU, cores=4, memory=4096)

        node_manager._node_api.qemu(100).config.put.assert_called_once_with(cores=4, memory=4096)

    async def test_create_vm_qemu(self, node_manager):
        """Test creating QEMU VM."""
        node_manager._node_api.qemu.post.return_value = "UPID:test"

        result = await node_manager.create_vm(100, VMType.QEMU, memory=2048)

        assert result == "UPID:test"
        node_manager._node_api.qemu.post.assert_called_once()

    async def test_create_vm_lxc(self, node_manager):
        """Test creating LXC container."""
        node_manager._node_api.lxc.post.return_value = "UPID:test"

        result = await node_manager.create_vm(101, VMType.LXC, memory=512)

        assert result == "UPID:test"
        node_manager._node_api.lxc.post.assert_called_once()

    async def test_delete_vm(self, node_manager):
        """Test deleting VM."""
        node_manager._node_api.qemu(100).delete.return_value = "UPID:test"

        result = await node_manager.delete_vm(100, VMType.QEMU, purge=True)

        assert result == "UPID:test"
        node_manager._node_api.qemu(100).delete.assert_called_once()


# ==================== VM Status Control Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestVMStatusControl:
    async def test_start_vm(self, node_manager):
        """Test starting VM."""
        node_manager._node_api.qemu(100).status.start.post.return_value = "UPID:test"

        result = await node_manager.start_vm(100, VMType.QEMU)

        assert result == "UPID:test"
        node_manager._node_api.qemu(100).status.start.post.assert_called_once()

    async def test_stop_vm(self, node_manager):
        """Test stopping VM."""
        node_manager._node_api.qemu(100).status.stop.post.return_value = "UPID:test"

        result = await node_manager.stop_vm(100, VMType.QEMU)

        assert result == "UPID:test"

    async def test_shutdown_vm(self, node_manager):
        """Test graceful shutdown."""
        node_manager._node_api.qemu(100).status.shutdown.post.return_value = "UPID:test"

        result = await node_manager.shutdown_vm(100, VMType.QEMU, timeout=120)

        assert result == "UPID:test"
        node_manager._node_api.qemu(100).status.shutdown.post.assert_called_once_with(timeout=120)

    async def test_reboot_vm(self, node_manager):
        """Test rebooting VM."""
        node_manager._node_api.qemu(100).status.reboot.post.return_value = "UPID:test"

        result = await node_manager.reboot_vm(100, VMType.QEMU)

        assert result == "UPID:test"

    async def test_reset_vm(self, node_manager):
        """Test hard reset VM."""
        node_manager._node_api.qemu(100).status.reset.post.return_value = "UPID:test"

        result = await node_manager.reset_vm(100)

        assert result == "UPID:test"

    async def test_suspend_vm(self, node_manager):
        """Test suspending VM."""
        node_manager._node_api.qemu(100).status.suspend.post.return_value = "UPID:test"

        result = await node_manager.suspend_vm(100)

        assert result == "UPID:test"

    async def test_resume_vm(self, node_manager):
        """Test resuming VM."""
        node_manager._node_api.qemu(100).status.resume.post.return_value = "UPID:test"

        result = await node_manager.resume_vm(100)

        assert result == "UPID:test"


# ==================== VM Operations Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestVMOperations:
    async def test_clone_vm(self, node_manager):
        """Test cloning VM."""
        node_manager._node_api.qemu(100).clone.post.return_value = "UPID:test"

        result = await node_manager.clone_vm(
            100, 200, VMType.QEMU, name="cloned-vm", full=True
        )

        assert result == "UPID:test"
        call_args = node_manager._node_api.qemu(100).clone.post.call_args
        assert call_args[1]["newid"] == 200
        assert call_args[1]["full"] == 1

    async def test_migrate_vm(self, node_manager):
        """Test migrating VM."""
        node_manager._node_api.qemu(100).migrate.post.return_value = "UPID:test"

        result = await node_manager.migrate_vm(100, VMType.QEMU, "pve2", online=True)

        assert result == "UPID:test"
        call_args = node_manager._node_api.qemu(100).migrate.post.call_args
        assert call_args[1]["target"] == "pve2"
        assert call_args[1]["online"] == 1

    async def test_convert_to_template(self, node_manager):
        """Test converting VM to template."""
        await node_manager.convert_to_template(100, VMType.QEMU)

        node_manager._node_api.qemu(100).template.post.assert_called_once()


# ==================== Snapshot Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestSnapshots:
    async def test_list_snapshots(self, node_manager):
        """Test listing snapshots."""
        snap_data = [
            {"name": "snap1", "snaptime": 1603912756, "description": "Test snapshot"}
        ]
        node_manager._node_api.qemu(100).snapshot.get.return_value = snap_data

        result = await node_manager.list_snapshots(100, VMType.QEMU)

        assert len(result) == 1
        assert isinstance(result[0], Snapshot)
        assert result[0].name == "snap1"

    async def test_create_snapshot(self, node_manager):
        """Test creating snapshot."""
        node_manager._node_api.qemu(100).snapshot.post.return_value = "UPID:test"

        result = await node_manager.create_snapshot(
            100, VMType.QEMU, "snap1", description="Test", vmstate=True
        )

        assert result == "UPID:test"

    async def test_delete_snapshot(self, node_manager):
        """Test deleting snapshot."""
        node_manager._node_api.qemu(100).snapshot("snap1").delete.return_value = "UPID:test"

        result = await node_manager.delete_snapshot(100, VMType.QEMU, "snap1")

        assert result == "UPID:test"

    async def test_rollback_snapshot(self, node_manager):
        """Test rolling back to snapshot."""
        node_manager._node_api.qemu(100).snapshot("snap1").rollback.post.return_value = "UPID:test"

        result = await node_manager.rollback_snapshot(100, VMType.QEMU, "snap1")

        assert result == "UPID:test"


# ==================== QEMU Guest Agent Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestQemuAgent:
    async def test_agent_ping(self, node_manager):
        """Test pinging guest agent."""
        node_manager._node_api.qemu(100).agent.ping.post.return_value = {"return": {}}

        result = await node_manager.agent_ping(100)

        assert result == {"return": {}}

    async def test_agent_get_info(self, node_manager):
        """Test getting agent info."""
        agent_data = {"version": "5.2.0", "supported-commands": []}
        node_manager._node_api.qemu(100).agent("get-info").get.return_value = agent_data

        result = await node_manager.agent_get_info(100)

        assert isinstance(result, QemuAgentInfo)
        assert result.version == "5.2.0"

    async def test_agent_get_osinfo(self, node_manager):
        """Test getting OS info via agent."""
        os_data = {
            "id": "ubuntu",
            "name": "Ubuntu",
            "version": "22.04",
            "kernel-release": "5.15.0",
        }
        node_manager._node_api.qemu(100).agent("get-osinfo").get.return_value = os_data

        result = await node_manager.agent_get_osinfo(100)

        assert isinstance(result, QemuAgentOSInfo)
        assert result.name == "Ubuntu"

    async def test_agent_exec(self, node_manager):
        """Test executing command via agent."""
        exec_data = {"pid": 1234}
        node_manager._node_api.qemu(100).agent.exec.post.return_value = exec_data

        result = await node_manager.agent_exec(100, ["ls", "-la"])

        assert isinstance(result, QemuAgentExecResult)
        assert result.pid == 1234

    async def test_agent_shutdown(self, node_manager):
        """Test shutting down guest via agent."""
        await node_manager.agent_shutdown(100)

        node_manager._node_api.qemu(100).agent.shutdown.post.assert_called_once()


# ==================== Storage Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestStorage:
    async def test_list_storage(self, node_manager):
        """Test listing storage."""
        storage_data = [{"storage": "local", "type": "dir"}]
        node_manager._node_api.storage.get.return_value = storage_data

        result = await node_manager.list_storage()

        assert result == storage_data

    async def test_get_storage_status(self, node_manager):
        """Test getting storage status."""
        status_data = {"total": 1000, "used": 500, "avail": 500}
        node_manager._node_api.storage("local").status.get.return_value = status_data

        result = await node_manager.get_storage_status("local")

        assert result == status_data

    async def test_list_storage_content(self, node_manager):
        """Test listing storage content."""
        content_data = [
            {
                "volid": "local:iso/ubuntu-22.04.iso",
                "format": "iso",
                "size": 1073741824,
            }
        ]
        node_manager._node_api.storage("local").content.get.return_value = content_data

        result = await node_manager.list_storage_content("local")

        assert len(result) == 1
        assert isinstance(result[0], StorageContent)
        assert result[0].format == "iso"

    async def test_delete_storage_content(self, node_manager):
        """Test deleting storage content."""
        node_manager._node_api.storage("local").content("local:iso/test.iso").delete.return_value = "UPID:test"

        result = await node_manager.delete_storage_content("local", "local:iso/test.iso")

        assert result == "UPID:test"


# ==================== Services Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestServices:
    async def test_list_services(self, node_manager, sample_service_data):
        """Test listing services."""
        node_manager._node_api.services.get.return_value = [sample_service_data]

        result = await node_manager.list_services()

        assert len(result) == 1
        assert isinstance(result[0], Service)
        assert result[0].name == "pveproxy"

    async def test_get_service_state(self, node_manager, sample_service_data):
        """Test getting service state."""
        node_manager._node_api.services("pveproxy").state.get.return_value = sample_service_data

        result = await node_manager.get_service_state("pveproxy")

        assert isinstance(result, Service)
        assert result.state == "running"

    async def test_start_service(self, node_manager):
        """Test starting service."""
        await node_manager.start_service("pveproxy")

        node_manager._node_api.services("pveproxy").start.post.assert_called_once()

    async def test_stop_service(self, node_manager):
        """Test stopping service."""
        await node_manager.stop_service("pveproxy")

        node_manager._node_api.services("pveproxy").stop.post.assert_called_once()

    async def test_restart_service(self, node_manager):
        """Test restarting service."""
        await node_manager.restart_service("pveproxy")

        node_manager._node_api.services("pveproxy").restart.post.assert_called_once()

    async def test_reload_service(self, node_manager):
        """Test reloading service."""
        await node_manager.reload_service("pveproxy")

        node_manager._node_api.services("pveproxy").reload.post.assert_called_once()


# ==================== Tasks Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestTasks:
    async def test_list_tasks(self, node_manager):
        """Test listing tasks."""
        task_data = [{"upid": "UPID:test", "status": "running"}]
        node_manager._node_api.tasks.get.return_value = task_data

        result = await node_manager.list_tasks()

        assert result == task_data

    async def test_list_tasks_with_filters(self, node_manager):
        """Test listing tasks with filters."""
        task_data = [{"upid": "UPID:test", "status": "stopped"}]
        node_manager._node_api.tasks.get.return_value = task_data

        result = await node_manager.list_tasks(vmid=100, errors=True, limit=50)

        assert result == task_data
        call_args = node_manager._node_api.tasks.get.call_args[1]
        assert call_args["vmid"] == 100
        assert call_args["errors"] == 1
        assert call_args["limit"] == 50

    async def test_get_task_status(self, node_manager):
        """Test getting task status."""
        status_data = {"status": "stopped", "exitstatus": "OK"}
        node_manager._node_api.tasks("UPID:test").status.get.return_value = status_data

        result = await node_manager.get_task_status("UPID:test")

        assert result == status_data

    async def test_get_task_log(self, node_manager):
        """Test getting task log."""
        log_data = [{"n": 1, "t": "Log line 1"}]
        node_manager._node_api.tasks("UPID:test").log.get.return_value = log_data

        result = await node_manager.get_task_log("UPID:test", start=0, limit=50)

        assert result == log_data

    async def test_stop_task(self, node_manager):
        """Test stopping task."""
        await node_manager.stop_task("UPID:test")

        node_manager._node_api.tasks("UPID:test").delete.assert_called_once()


# ==================== Backup Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestBackup:
    async def test_backup_vm(self, node_manager):
        """Test backing up VM."""
        node_manager._node_api.vzdump.post.return_value = "UPID:test"

        result = await node_manager.backup_vm(
            100,
            "backup-storage",
            mode="snapshot",
            compress="zstd",
            notes="Test backup"
        )

        assert result == "UPID:test"
        call_args = node_manager._node_api.vzdump.post.call_args[1]
        assert call_args["vmid"] == 100
        assert call_args["storage"] == "backup-storage"


# Continue with remaining tests in next file due to length...
