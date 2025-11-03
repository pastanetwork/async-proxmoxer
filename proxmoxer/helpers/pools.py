"""
Pool management helpers for Proxmoxer.

Provides high-level async API for managing Proxmox resource pools.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..types import ResponseData

logger = logging.getLogger(__name__)


@dataclass
class PoolMember:
    """Resource pool member."""

    id: str
    type: str
    node: str
    storage: str | None = None
    vmid: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolMember:
        """Create PoolMember from API response."""
        return cls(
            id=data["id"],
            type=data["type"],
            node=data["node"],
            storage=data.get("storage"),
            vmid=data.get("vmid"),
        )


@dataclass
class Pool:
    """Resource pool."""

    poolid: str
    comment: str | None = None
    members: list[PoolMember] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pool:
        """Create Pool from API response."""
        members = None
        if data.get("members"):
            members = [PoolMember.from_dict(m) for m in data["members"]]

        return cls(
            poolid=data["poolid"],
            comment=data.get("comment"),
            members=members,
        )


class PoolManager:
    """
    High-level manager for Proxmox resource pools.

    Provides methods for managing resource pools, which are used
    to organize VMs, containers, and storage resources.

    Example:
        >>> pool_mgr = PoolManager(proxmox)
        >>> pools = await pool_mgr.list_pools()
        >>> await pool_mgr.create_pool("production", comment="Production VMs")
        >>> await pool_mgr.add_vm_to_pool("production", 100)
        >>> await pool_mgr.remove_vm_from_pool("production", 100)
    """

    def __init__(self, proxmox: Any):
        """
        Initialize PoolManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    async def list_pools(self) -> list[Pool]:
        """
        List all resource pools.

        Returns:
            List of Pool objects
        """
        data: ResponseData = await self.proxmox.pools.get()
        return [Pool.from_dict(p) for p in data]

    async def get_pool(self, poolid: str) -> Pool:
        """
        Get pool details.

        Args:
            poolid: Pool ID

        Returns:
            Pool object with members
        """
        data: ResponseData = await self.proxmox.pools(poolid).get()
        data["poolid"] = poolid
        return Pool.from_dict(data)

    async def create_pool(self, poolid: str, comment: str | None = None) -> None:
        """
        Create a new resource pool.

        Args:
            poolid: Pool ID
            comment: Pool description
        """
        params = {"poolid": poolid}
        if comment:
            params["comment"] = comment

        await self.proxmox.pools.post(**params)

    async def update_pool(
        self,
        poolid: str,
        comment: str | None = None,
        storage: str | None = None,
        vms: str | None = None,
        delete_storage: str | None = None,
        delete_vms: str | None = None,
        delete: str | None = None,
    ) -> None:
        """
        Update pool configuration.

        Args:
            poolid: Pool ID
            comment: New comment
            storage: Comma-separated list of storage IDs to add
            vms: Comma-separated list of VM IDs to add
            delete_storage: Comma-separated list of storage IDs to remove
            delete_vms: Comma-separated list of VM IDs to remove
            delete: Delete comment or other properties
        """
        params = {}
        if comment is not None:
            params["comment"] = comment
        if storage is not None:
            params["storage"] = storage
        if vms is not None:
            params["vms"] = vms
        if delete_storage is not None:
            params["delete-storage"] = delete_storage
        if delete_vms is not None:
            params["delete-vms"] = delete_vms
        if delete is not None:
            params["delete"] = delete

        await self.proxmox.pools(poolid).put(**params)

    async def delete_pool(self, poolid: str) -> None:
        """
        Delete a resource pool.

        Args:
            poolid: Pool ID to delete
        """
        await self.proxmox.pools(poolid).delete()

    async def add_vm_to_pool(self, poolid: str, vmid: int) -> None:
        """
        Add a VM or container to a pool.

        Args:
            poolid: Pool ID
            vmid: VM/Container ID
        """
        await self.proxmox.pools(poolid).put(vms=str(vmid))

    async def remove_vm_from_pool(self, poolid: str, vmid: int) -> None:
        """
        Remove a VM or container from a pool.

        Args:
            poolid: Pool ID
            vmid: VM/Container ID
        """
        await self.proxmox.pools(poolid).put(**{"delete-vms": str(vmid)})

    async def add_storage_to_pool(self, poolid: str, storage: str) -> None:
        """
        Add storage to a pool.

        Args:
            poolid: Pool ID
            storage: Storage ID
        """
        await self.proxmox.pools(poolid).put(storage=storage)

    async def remove_storage_from_pool(self, poolid: str, storage: str) -> None:
        """
        Remove storage from a pool.

        Args:
            poolid: Pool ID
            storage: Storage ID
        """
        await self.proxmox.pools(poolid).put(**{"delete-storage": storage})

    async def get_pool_members(self, poolid: str) -> dict[str, list[Any]]:
        """
        Get pool members organized by type.

        Args:
            poolid: Pool ID

        Returns:
            Dict with 'vms', 'storage', etc. as keys
        """
        pool = await self.get_pool(poolid)
        members: dict[str, list[Any]] = {"vms": [], "storage": []}

        if pool.members:
            for member in pool.members:
                member_type = member.get("type", "")
                if member_type in ("qemu", "lxc"):
                    members["vms"].append(member)
                elif member_type == "storage":
                    members["storage"].append(member)

        return members
