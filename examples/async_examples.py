"""
Async Proxmoxer Examples

Demonstrates various usage patterns with the async version of Proxmoxer.
"""

import asyncio
import sys
from typing import Any

# Add parent directory to path for local development
sys.path.insert(0, "..")

from proxmoxer import ProxmoxAPI
from proxmoxer.exceptions import (
    AuthenticationError,
    ConnectionError,
    ResourceException,
)
from proxmoxer.retry import retry_async


# Configuration (update with your Proxmox server details)
PROXMOX_HOST = "10.0.0.1"
PROXMOX_USER = "root@pam"
PROXMOX_PASSWORD = "your_password"

# Or use API token (Method 1 - separate user and token_name):
# PROXMOX_USER = "root@pam"
# PROXMOX_TOKEN_NAME = "my-token"
# PROXMOX_TOKEN_VALUE = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Or use API token (Method 2 - full_token_id, more convenient):
# PROXMOX_FULL_TOKEN_ID = "root@pam!my-token"
# PROXMOX_TOKEN_VALUE = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"


async def example_basic_usage():
    """Example 1: Basic API usage."""
    print("\n=== Example 1: Basic Usage ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,  # Only for testing!
    ) as proxmox:
        # Get Proxmox version
        version = await proxmox.version.get()
        print(f"Proxmox Version: {version['version']}")
        print(f"Release: {version['release']}")

        # Get cluster status
        cluster_status = await proxmox.cluster.status.get()
        print(f"\nCluster Status:")
        for item in cluster_status:
            print(f"  - {item['name']}: {item['type']}")

        # List all nodes
        nodes = await proxmox.nodes.get()
        print(f"\nNodes ({len(nodes)} total):")
        for node in nodes:
            print(f"  - {node['node']}: {node['status']}")


async def example_concurrent_requests():
    """Example 2: Concurrent API requests for better performance."""
    print("\n=== Example 2: Concurrent Requests ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        # Get list of nodes
        nodes = await proxmox.nodes.get()

        # Fetch status of all nodes concurrently (FAST!)
        print("Fetching status for all nodes concurrently...")

        tasks = [proxmox.nodes(node["node"]).status.get() for node in nodes]

        statuses = await asyncio.gather(*tasks)

        # Display results
        for node, status in zip(nodes, statuses):
            print(f"\n{node['node']}:")
            print(f"  CPU: {status.get('cpu', 0) * 100:.1f}%")
            print(f"  Memory: {status['memory']['used'] / status['memory']['total'] * 100:.1f}%")
            print(f"  Uptime: {status.get('uptime', 0) / 86400:.1f} days")


async def example_vm_operations():
    """Example 3: VM management operations."""
    print("\n=== Example 3: VM Operations ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        node = "pve"  # Change to your node name

        # List all VMs on a node
        vms = await proxmox.nodes(node).qemu.get()

        print(f"VMs on {node} ({len(vms)} total):")
        for vm in vms:
            status = vm.get("status", "unknown")
            print(f"  - VM {vm['vmid']}: {vm['name']} ({status})")

        # Get detailed status of first VM (if exists)
        if vms:
            vmid = vms[0]["vmid"]
            vm_status = await proxmox.nodes(node).qemu(vmid).status.current.get()

            print(f"\nDetailed status of VM {vmid}:")
            print(f"  Status: {vm_status['status']}")
            print(f"  CPU: {vm_status.get('cpu', 0) * 100:.1f}%")
            print(f"  Memory: {vm_status.get('mem', 0) / (1024**3):.2f} GB")
            print(f"  Disk: {vm_status.get('disk', 0) / (1024**3):.2f} GB")


async def example_create_vm():
    """Example 4: Create a new VM."""
    print("\n=== Example 4: Create VM ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        node = "pve"  # Change to your node name
        vmid = 999  # Choose an available VMID

        try:
            # Create VM
            print(f"Creating VM {vmid}...")

            result = await proxmox.nodes(node).qemu.create(
                vmid=vmid,
                name="test-vm",
                memory=2048,
                cores=2,
                sockets=1,
                net0="virtio,bridge=vmbr0",
                ide2="local:cloudinit",
                # Add more config as needed
            )

            print(f"VM created successfully: {result}")

            # Start VM
            print(f"Starting VM {vmid}...")
            start_result = await proxmox.nodes(node).qemu(vmid).status.start.post()
            print(f"VM started: {start_result}")

        except ResourceException as e:
            print(f"Failed to create VM: {e.message}")
            print(f"Status: {e.status_code}")
            print(f"Errors: {e.errors}")

        except Exception as e:
            print(f"Unexpected error: {e}")


async def example_storage_operations():
    """Example 5: Storage operations."""
    print("\n=== Example 5: Storage Operations ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        node = "pve"  # Change to your node name

        # List all storage
        storages = await proxmox.nodes(node).storage.get()

        print(f"Storage on {node}:")
        for storage in storages:
            print(f"\n{storage['storage']}:")
            print(f"  Type: {storage['type']}")
            print(f"  Content: {storage.get('content', 'N/A')}")

            # Get storage status
            try:
                status = await proxmox.nodes(node).storage(storage["storage"]).status.get()
                total_gb = status.get("total", 0) / (1024**3)
                used_gb = status.get("used", 0) / (1024**3)
                avail_gb = status.get("avail", 0) / (1024**3)

                print(f"  Total: {total_gb:.2f} GB")
                print(f"  Used: {used_gb:.2f} GB ({used_gb/total_gb*100:.1f}%)")
                print(f"  Available: {avail_gb:.2f} GB")
            except Exception as e:
                print(f"  (Status unavailable: {e})")


async def example_with_retry():
    """Example 6: Using retry decorator for resilience."""
    print("\n=== Example 6: Retry Logic ===\n")

    @retry_async(max_attempts=3, initial_delay=1.0)
    async def get_nodes_with_retry(proxmox):
        """Fetch nodes with automatic retry."""
        print("  Attempting to fetch nodes...")
        return await proxmox.nodes.get()

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        try:
            nodes = await get_nodes_with_retry(proxmox)
            print(f"Successfully fetched {len(nodes)} nodes")
        except Exception as e:
            print(f"Failed after retries: {e}")


async def example_error_handling():
    """Example 7: Comprehensive error handling."""
    print("\n=== Example 7: Error Handling ===\n")

    try:
        async with ProxmoxAPI.create(
            host=PROXMOX_HOST,
            user=PROXMOX_USER,
            password="wrong_password",  # Intentional error
            verify_ssl=False,
        ) as proxmox:
            await proxmox.nodes.get()

    except AuthenticationError as e:
        print(f"Authentication failed:")
        print(f"  Message: {e.message}")
        print(f"  Username: {e.username}")
        print(f"  Method: {e.auth_method}")

    except ConnectionError as e:
        print(f"Connection failed:")
        print(f"  Message: {e.message}")
        print(f"  Host: {e.host}:{e.port}")

    except Exception as e:
        print(f"Unexpected error: {e}")


async def example_batch_operations():
    """Example 8: Batch operations on multiple VMs."""
    print("\n=== Example 8: Batch Operations ===\n")

    async with ProxmoxAPI.create(
        host=PROXMOX_HOST,
        user=PROXMOX_USER,
        password=PROXMOX_PASSWORD,
        verify_ssl=False,
    ) as proxmox:
        node = "pve"

        # Get all VMs
        vms = await proxmox.nodes(node).qemu.get()

        if not vms:
            print("No VMs found")
            return

        print(f"Fetching detailed status for {len(vms)} VMs concurrently...")

        # Fetch status for all VMs in parallel
        tasks = [
            proxmox.nodes(node).qemu(vm["vmid"]).status.current.get()
            for vm in vms
        ]

        statuses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        print("\nVM Status Summary:")
        for vm, status in zip(vms, statuses):
            if isinstance(status, Exception):
                print(f"  VM {vm['vmid']}: Error - {status}")
            else:
                cpu = status.get("cpu", 0) * 100
                mem_pct = (
                    status.get("mem", 0) / status.get("maxmem", 1) * 100
                    if status.get("maxmem")
                    else 0
                )
                print(
                    f"  VM {vm['vmid']} ({vm['name']}): "
                    f"{status['status']} | CPU: {cpu:.1f}% | Mem: {mem_pct:.1f}%"
                )


async def example_api_token_auth():
    """Example 9: Using API token authentication."""
    print("\n=== Example 9: API Token Authentication ===\n")

    # Method 1: Separate user and token_name
    # async with ProxmoxAPI.create(
    #     host=PROXMOX_HOST,
    #     user=PROXMOX_USER,
    #     token_name="my-token",
    #     token_value="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    #     verify_ssl=False,
    # ) as proxmox:
    #     version = await proxmox.version.get()
    #     print(f"Connected with API token: {version['version']}")

    # Method 2: Full token ID (more convenient - recommended)
    # async with ProxmoxAPI.create(
    #     host=PROXMOX_HOST,
    #     full_token_id="root@pam!my-token",
    #     token_value="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    #     verify_ssl=False,
    # ) as proxmox:
    #     version = await proxmox.version.get()
    #     print(f"Connected with full_token_id: {version['version']}")

    print("(Configure full_token_id and token_value to use this example)")


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Async Proxmoxer Examples")
    print("=" * 60)

    examples = [
        ("Basic Usage", example_basic_usage),
        ("Concurrent Requests", example_concurrent_requests),
        ("VM Operations", example_vm_operations),
        ("Storage Operations", example_storage_operations),
        ("Retry Logic", example_with_retry),
        ("Error Handling", example_error_handling),
        ("Batch Operations", example_batch_operations),
        # ("Create VM", example_create_vm),  # Commented out to avoid creating VMs
        # ("API Token Auth", example_api_token_auth),  # Needs token config
    ]

    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\nExample '{name}' failed: {e}")
            import traceback

            traceback.print_exc()

        await asyncio.sleep(1)  # Pause between examples

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(main())
