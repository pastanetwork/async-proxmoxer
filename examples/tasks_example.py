"""
TasksHelper Example - Asynchronous Task Tracking

This example demonstrates how to track, wait for, and monitor
Proxmox asynchronous tasks (UPIDs).
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import TasksHelper, NodeManager, VMType


async def main():
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )
    tasks = TasksHelper(proxmox)
    node = NodeManager(proxmox, "pve-node1")

    print("=" * 60)
    print("TasksHelper Examples - Task Tracking & Monitoring")
    print("=" * 60)

    # START A TASK (Example: Start VM)
    print("\n[1] START A TASK")
    print("-" * 60)
    upid = await node.start_vm(100, VMType.QEMU)
    print(f"Started VM 100, Task UPID: {upid}")

    # PARSE UPID
    print("\n[2] PARSE UPID")
    print("-" * 60)
    parsed = tasks.parse_upid(upid)
    print(f"Parsed UPID:")
    print(f"  Node: {parsed['node']}")
    print(f"  Type: {parsed['type']}")
    print(f"  User: {parsed['user']}")
    print(f"  PID: {parsed['pid']}")

    # GET TASK STATUS
    print("\n[3] GET TASK STATUS")
    print("-" * 60)
    task = await tasks.get_task_status(upid)
    print(f"Task Status:")
    print(f"  UPID: {task.upid}")
    print(f"  Type: {task.type}")
    print(f"  Status: {task.status}")
    print(f"  Running: {task.is_running}")

    # WAIT FOR TASK COMPLETION
    print("\n[4] WAIT FOR TASK (with timeout)")
    print("-" * 60)
    try:
        completed_task = await tasks.wait_for_task(upid, timeout=60)
        print(f"Task completed successfully")
        print(f"  Exit status: {completed_task.exitstatus}")
        print(f"  Successful: {completed_task.is_successful}")
    except asyncio.TimeoutError:
        print("Task timed out")
    except RuntimeError as e:
        print(f"Task failed: {e}")

    # WAIT WITH PROGRESS CALLBACK
    print("\n[5] WAIT WITH PROGRESS CALLBACK")
    print("-" * 60)
    upid2 = await node.shutdown_vm(100, VMType.QEMU)

    def progress_callback(task):
        print(f"  [Progress] Status: {task.status}, Running: {task.is_running}")

    completed_task = await tasks.wait_for_task(
        upid2,
        timeout=120,
        poll_interval=2.0,
        on_progress=progress_callback,
    )
    print("Shutdown completed")

    # GET TASK LOG
    print("\n[6] GET TASK LOG")
    print("-" * 60)
    log_entries = await tasks.get_task_log(upid, start=0, limit=10)
    print(f"Task log ({len(log_entries)} lines):")
    for entry in log_entries[-5:]:
        print(f"  {entry.get('t', '')}")

    # STREAM TASK LOG (Real-time)
    print("\n[7] STREAM TASK LOG (Real-time)")
    print("-" * 60)
    upid3 = await node.backup_vm(100, storage="local", mode="snapshot")
    print(f"Started backup... Streaming log:")

    # Stream log with callback
    def log_callback(line):
        print(f"  [LOG] {line}")

    await tasks.stream_task_log(upid3, callback=log_callback, poll_interval=0.5)
    print("Backup completed")

    # WAIT FOR MULTIPLE TASKS
    print("\n[8] WAIT FOR MULTIPLE TASKS")
    print("-" * 60)
    task1 = await node.create_snapshot(100, VMType.QEMU, "snap1")
    task2 = await node.create_snapshot(101, VMType.QEMU, "snap1")
    task3 = await node.create_snapshot(102, VMType.QEMU, "snap1")

    print(f"Created 3 snapshot tasks, waiting for all...")
    completed_tasks = await tasks.wait_for_tasks(
        [task1, task2, task3],
        timeout=300,
        raise_on_error=True,
    )
    print(f"All {len(completed_tasks)} tasks completed")

    # LIST TASKS
    print("\n[9] LIST TASKS")
    print("-" * 60)

    # List tasks on node
    node_tasks = await tasks.list_node_tasks("pve-node1", limit=5)
    print(f"Recent tasks on node1: {len(node_tasks)}")
    for task in node_tasks:
        print(f"  - {task.type}: {task.status}")
        print(f"    UPID: {task.upid}")

    # List cluster-wide tasks
    cluster_tasks = await tasks.list_cluster_tasks(limit=10)
    print(f"\nRecent cluster tasks: {len(cluster_tasks)}")

    # GET ACTIVE TASKS
    print("\n[10] GET ACTIVE TASKS")
    print("-" * 60)
    active = await tasks.get_active_tasks(node="pve-node1")
    print(f"Active tasks on node1: {len(active)}")
    for task in active:
        print(f"  - {task.type} (PID: {task.pid})")

    # GET FAILED TASKS
    print("\n[11] GET FAILED TASKS")
    print("-" * 60)
    failed = await tasks.get_failed_tasks(limit=5)
    print(f"Recent failed tasks: {len(failed)}")
    for task in failed:
        print(f"  - {task.type}: {task.exitstatus}")

    # STOP TASK (if needed)
    # print("\n[12] STOP TASK")
    # print("-" * 60)
    # await tasks.stop_task(upid)
    # print("Task stopped")

    print("\n" + "=" * 60)
    print("TASK MANAGEMENT SUMMARY")
    print("=" * 60)
    print("Parse UPID")
    print("Get task status")
    print("Wait for task completion (with timeout)")
    print("Progress callbacks")
    print("Get task logs")
    print("Stream logs in real-time")
    print("Wait for multiple tasks")
    print("List node/cluster tasks")
    print("Get active/failed tasks")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
