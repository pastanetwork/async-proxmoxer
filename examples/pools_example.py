"""
PoolManager Example - Resource Pool Management

This example demonstrates resource pool management for organizing
VMs, containers, and storage.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import PoolManager


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    pool_mgr = PoolManager(proxmox)

    print("=" * 60)
    print("PoolManager Examples - Resource Pool Management")
    print("=" * 60)

    # ========================================
    # 1. LIST POOLS
    # ========================================
    print("\n[1] LIST POOLS")
    print("-" * 60)

    pools = await pool_mgr.list_pools()
    print(f"Total pools: {len(pools)}")
    for pool in pools:
        print(f"  - {pool.poolid}")
        if pool.comment:
            print(f"    Comment: {pool.comment}")

    # ========================================
    # 2. CREATE POOLS
    # ========================================
    print("\n[2] CREATE POOLS")
    print("-" * 60)

    # Create production pool
    await pool_mgr.create_pool(
        poolid="production",
        comment="Production environment VMs and storage",
    )
    print("Created pool: production")

    # Create development pool
    await pool_mgr.create_pool(
        poolid="development",
        comment="Development and testing environment",
    )
    print("Created pool: development")

    # Create customer pool
    await pool_mgr.create_pool(
        poolid="customer-acme",
        comment="ACME Corporation resources",
    )
    print("Created pool: customer-acme")

    # ========================================
    # 3. ADD VMs TO POOL
    # ========================================
    print("\n[3] ADD VMs TO POOL")
    print("-" * 60)

    # Add VMs to production pool
    print("\n[Add to Production Pool]")
    await pool_mgr.add_vm_to_pool("production", 100)
    print("Added VM 100 to production")

    await pool_mgr.add_vm_to_pool("production", 101)
    print("Added VM 101 to production")

    await pool_mgr.add_vm_to_pool("production", 102)
    print("Added VM 102 to production")

    # Add VMs to development pool
    print("\n[Add to Development Pool]")
    await pool_mgr.add_vm_to_pool("development", 200)
    print("Added VM 200 to development")

    await pool_mgr.add_vm_to_pool("development", 201)
    print("Added VM 201 to development")

    # ========================================
    # 4. ADD STORAGE TO POOL
    # ========================================
    print("\n[4] ADD STORAGE TO POOL")
    print("-" * 60)

    # Add storage to production pool
    await pool_mgr.add_storage_to_pool("production", "local-lvm")
    print("Added storage 'local-lvm' to production")

    await pool_mgr.add_storage_to_pool("production", "backup-nfs")
    print("Added storage 'backup-nfs' to production")

    # Add storage to development pool
    await pool_mgr.add_storage_to_pool("development", "local")
    print("Added storage 'local' to development")

    # ========================================
    # 5. GET POOL DETAILS
    # ========================================
    print("\n[5] GET POOL DETAILS")
    print("-" * 60)

    # Get production pool
    pool = await pool_mgr.get_pool("production")
    print(f"\nPool: {pool.poolid}")
    print(f"Comment: {pool.comment}")
    if pool.members:
        print(f"Members: {len(pool.members)}")
        for member in pool.members[:5]:
            print(f"  - {member.get('type', 'N/A')}: {member.get('id', 'N/A')}")

    # Get organized members
    print("\n[Organized Members]")
    members = await pool_mgr.get_pool_members("production")
    print(f"VMs: {len(members['vms'])}")
    for vm in members['vms']:
        print(f"  - VM {vm.get('vmid', 'N/A')}: {vm.get('name', 'N/A')}")

    print(f"\nStorage: {len(members['storage'])}")
    for storage in members['storage']:
        print(f"  - {storage.get('storage', 'N/A')}")

    # ========================================
    # 6. UPDATE POOL
    # ========================================
    print("\n[6] UPDATE POOL")
    print("-" * 60)

    # Update pool comment
    await pool_mgr.update_pool(
        poolid="production",
        comment="Production Environment - Critical Services",
    )
    print("Updated production pool comment")

    # Bulk add VMs
    await pool_mgr.update_pool(
        poolid="development",
        vms="202,203,204",  # Add multiple VMs at once
    )
    print("Added VMs 202, 203, 204 to development")

    # ========================================
    # 7. REMOVE FROM POOL
    # ========================================
    print("\n[7] REMOVE FROM POOL")
    print("-" * 60)

    # Remove VM from pool
    await pool_mgr.remove_vm_from_pool("production", 102)
    print("Removed VM 102 from production")

    # Remove storage from pool
    await pool_mgr.remove_storage_from_pool("development", "local")
    print("Removed storage 'local' from development")

    # ========================================
    # 8. PRACTICAL USE CASES
    # ========================================
    print("\n[8] PRACTICAL USE CASES")
    print("-" * 60)

    # Use Case 1: Organize by environment
    print("\n[Use Case 1: Environment Organization]")
    await pool_mgr.create_pool("staging", comment="Staging environment")
    await pool_mgr.add_vm_to_pool("staging", 300)
    await pool_mgr.add_vm_to_pool("staging", 301)
    print("Created staging pool with VMs")

    # Use Case 2: Organize by customer
    print("\n[Use Case 2: Customer Organization]")
    await pool_mgr.create_pool("customer-beta", comment="Beta Corporation")
    await pool_mgr.add_vm_to_pool("customer-beta", 400)
    await pool_mgr.add_storage_to_pool("customer-beta", "customer-beta-storage")
    print("Created customer pool with dedicated resources")

    # Use Case 3: Organize by department
    print("\n[Use Case 3: Department Organization]")
    await pool_mgr.create_pool("dept-it", comment="IT Department")
    await pool_mgr.create_pool("dept-finance", comment="Finance Department")
    print("Created department pools")

    # ========================================
    # 9. LIST ALL POOLS WITH DETAILS
    # ========================================
    print("\n[9] LIST ALL POOLS WITH DETAILS")
    print("-" * 60)

    all_pools = await pool_mgr.list_pools()
    print(f"\nTotal pools: {len(all_pools)}")
    for pool in all_pools:
        print(f"\n  Pool: {pool.poolid}")
        if pool.comment:
            print(f"    Comment: {pool.comment}")

        # Get members for each pool
        try:
            members = await pool_mgr.get_pool_members(pool.poolid)
            print(f"    VMs: {len(members['vms'])}")
            print(f"    Storage: {len(members['storage'])}")
        except:
            pass

    # ========================================
    # 10. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[10] CLEANUP")
    print("-" * 60)

    # Delete pools
    pools_to_delete = [
        "staging",
        "customer-beta",
        "dept-it",
        "dept-finance",
    ]

    for pool_id in pools_to_delete:
        try:
            await pool_mgr.delete_pool(pool_id)
            print(f"Deleted pool: {pool_id}")
        except Exception as e:
            print(f"  Could not delete {pool_id}: {e}")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("POOL MANAGEMENT SUMMARY")
    print("=" * 60)
    print("List pools")
    print("Create pools with descriptions")
    print("Add VMs to pools (single or bulk)")
    print("Add storage to pools")
    print("Remove VMs/storage from pools")
    print("Get pool details and members")
    print("Update pool configuration")
    print("Delete pools")
    print("\nUse Cases:")
    print("  - Environment organization (prod, dev, staging)")
    print("  - Customer segregation")
    print("  - Department-based resource allocation")
    print("  - Project-based VM grouping")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
