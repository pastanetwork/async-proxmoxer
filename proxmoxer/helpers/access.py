"""
Access management helpers for Proxmoxer.

Provides high-level async API for managing Proxmox authentication,
users, groups, roles, ACLs, and TFA (Two-Factor Authentication).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from ..types import ResponseData

logger = logging.getLogger(__name__)


class TFAType(str, Enum):
    """Two-Factor Authentication types."""

    TOTP = "totp"
    U2F = "u2f"
    WEBAUTHN = "webauthn"
    YUBICO = "yubico"
    RECOVERY = "recovery"


@dataclass
class User:
    """Proxmox user."""

    userid: str
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    groups: list[str] | None = None
    expire: int | None = None
    enable: bool = True
    comment: str | None = None
    keys: str | None = None
    tokens: list[str] | None = None
    # Authentication realm
    realm_type: str | None = None
    # Two-Factor Authentication security
    tfa_locked_until: int | None = None
    totp_locked: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Create User from API response."""
        return cls(
            userid=data["userid"],
            email=data.get("email"),
            firstname=data.get("firstname"),
            lastname=data.get("lastname"),
            groups=data.get("groups", "").split(",") if data.get("groups") else None,
            expire=data.get("expire"),
            enable=bool(data.get("enable", 1)),
            comment=data.get("comment"),
            keys=data.get("keys"),
            tokens=data.get("tokens", []) if isinstance(data.get("tokens"), list) else [],
            realm_type=data.get("realm-type"),
            tfa_locked_until=data.get("tfa-locked-until"),
            totp_locked=bool(data.get("totp-locked", 0)) if data.get("totp-locked") is not None else None,
        )


@dataclass
class Group:
    """Proxmox group."""

    groupid: str
    comment: str | None = None
    users: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Group:
        """Create Group from API response."""
        return cls(
            groupid=data["groupid"],
            comment=data.get("comment"),
            users=data.get("users", "").split(",") if data.get("users") else None,
        )


@dataclass
class Role:
    """Proxmox role."""

    roleid: str
    privs: list[str] | None = None
    special: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Role:
        """Create Role from API response."""
        return cls(
            roleid=data["roleid"],
            privs=data.get("privs", "").split(",") if data.get("privs") else None,
            special=bool(data.get("special", 0)),
        )


@dataclass
class ACL:
    """Proxmox Access Control List entry."""

    path: str
    roleid: str
    type: str
    ugid: str
    propagate: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ACL:
        """Create ACL from API response."""
        return cls(
            path=data["path"],
            roleid=data["roleid"],
            type=data["type"],
            ugid=data["ugid"],
            propagate=bool(data.get("propagate", 1)),
        )


@dataclass
class Domain:
    """Authentication domain/realm."""

    realm: str
    type: str
    comment: str | None = None
    default: bool = False
    tfa: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Domain:
        """Create Domain from API response."""
        return cls(
            realm=data["realm"],
            type=data["type"],
            comment=data.get("comment"),
            default=bool(data.get("default", 0)),
            tfa=data.get("tfa"),
        )


@dataclass
class APIToken:
    """API token."""

    tokenid: str
    userid: str
    comment: str | None = None
    expire: int | None = None
    privsep: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> APIToken:
        """Create APIToken from API response."""
        tokenid = data.get("tokenid", "")
        userid = data.get("userid", "")
        return cls(
            tokenid=tokenid,
            userid=userid,
            comment=data.get("comment"),
            expire=data.get("expire"),
            privsep=bool(data.get("privsep", 1)),
        )


class AccessManager:
    """
    High-level manager for Proxmox access control.

    Provides methods for managing users, groups, roles, ACLs, domains,
    and two-factor authentication.

    Example:
        >>> access = AccessManager(proxmox)
        >>> users = await access.list_users()
        >>> await access.create_user("user@pve", password="secret", email="user@example.com")
        >>> await access.set_password("user@pve", "newsecret")
    """

    def __init__(self, proxmox: Any):
        """
        Initialize AccessManager.

        Args:
            proxmox: Proxmoxer instance
        """
        self.proxmox = proxmox

    # User Management
    async def list_users(self, enabled: bool | None = None) -> list[User]:
        """
        List all users.

        Args:
            enabled: Filter by enabled status

        Returns:
            List of User objects
        """
        params = {}
        if enabled is not None:
            params["enabled"] = 1 if enabled else 0

        data: ResponseData = await self.proxmox.access.users.get(**params)
        return [User.from_dict(u) for u in data]

    async def get_user(self, userid: str) -> User:
        """
        Get user details.

        Args:
            userid: User ID (e.g., "user@pve")

        Returns:
            User object
        """
        data: ResponseData = await self.proxmox.access.users(userid).get()
        return User.from_dict(data)

    async def create_user(
        self,
        userid: str,
        password: str | None = None,
        email: str | None = None,
        firstname: str | None = None,
        lastname: str | None = None,
        groups: list[str] | None = None,
        expire: int | None = None,
        enable: bool = True,
        comment: str | None = None,
        keys: str | None = None,
    ) -> None:
        """
        Create a new user.

        Args:
            userid: User ID (e.g., "user@pve")
            password: Password
            email: Email address
            firstname: First name
            lastname: Last name
            groups: List of group IDs
            expire: Account expiration date (UNIX timestamp)
            enable: Enable the account
            comment: Comment
            keys: Keys for ssh-key based authentication
        """
        params = {"userid": userid}
        if password:
            params["password"] = password
        if email:
            params["email"] = email
        if firstname:
            params["firstname"] = firstname
        if lastname:
            params["lastname"] = lastname
        if groups:
            params["groups"] = ",".join(groups)
        if expire:
            params["expire"] = expire
        if not enable:
            params["enable"] = 0
        if comment:
            params["comment"] = comment
        if keys:
            params["keys"] = keys

        await self.proxmox.access.users.post(**params)

    async def update_user(
        self,
        userid: str,
        email: str | None = None,
        firstname: str | None = None,
        lastname: str | None = None,
        groups: list[str] | None = None,
        expire: int | None = None,
        enable: bool | None = None,
        comment: str | None = None,
        keys: str | None = None,
    ) -> None:
        """
        Update user settings.

        Args:
            userid: User ID
            email: Email address
            firstname: First name
            lastname: Last name
            groups: List of group IDs
            expire: Account expiration date (UNIX timestamp)
            enable: Enable the account
            comment: Comment
            keys: Keys for ssh-key based authentication
        """
        params = {}
        if email is not None:
            params["email"] = email
        if firstname is not None:
            params["firstname"] = firstname
        if lastname is not None:
            params["lastname"] = lastname
        if groups is not None:
            params["groups"] = ",".join(groups)
        if expire is not None:
            params["expire"] = expire
        if enable is not None:
            params["enable"] = 1 if enable else 0
        if comment is not None:
            params["comment"] = comment
        if keys is not None:
            params["keys"] = keys

        await self.proxmox.access.users(userid).put(**params)

    async def delete_user(self, userid: str) -> None:
        """
        Delete a user.

        Args:
            userid: User ID to delete
        """
        await self.proxmox.access.users(userid).delete()

    async def set_password(self, userid: str, password: str) -> None:
        """
        Set user password.

        Args:
            userid: User ID
            password: New password
        """
        await self.proxmox.access.password.put(userid=userid, password=password)

    # Group Management
    async def list_groups(self) -> list[Group]:
        """
        List all groups.

        Returns:
            List of Group objects
        """
        data: ResponseData = await self.proxmox.access.groups.get()
        return [Group.from_dict(g) for g in data]

    async def get_group(self, groupid: str) -> Group:
        """
        Get group details.

        Args:
            groupid: Group ID

        Returns:
            Group object
        """
        data: ResponseData = await self.proxmox.access.groups(groupid).get()
        return Group.from_dict(data)

    async def create_group(self, groupid: str, comment: str | None = None) -> None:
        """
        Create a new group.

        Args:
            groupid: Group ID
            comment: Comment
        """
        params = {"groupid": groupid}
        if comment:
            params["comment"] = comment
        await self.proxmox.access.groups.post(**params)

    async def update_group(self, groupid: str, comment: str | None = None) -> None:
        """
        Update group settings.

        Args:
            groupid: Group ID
            comment: Comment
        """
        params = {}
        if comment is not None:
            params["comment"] = comment
        await self.proxmox.access.groups(groupid).put(**params)

    async def delete_group(self, groupid: str) -> None:
        """
        Delete a group.

        Args:
            groupid: Group ID to delete
        """
        await self.proxmox.access.groups(groupid).delete()

    # Role Management
    async def list_roles(self) -> list[Role]:
        """
        List all roles.

        Returns:
            List of Role objects
        """
        data: ResponseData = await self.proxmox.access.roles.get()
        return [Role.from_dict(r) for r in data]

    async def get_role(self, roleid: str) -> Role:
        """
        Get role details.

        Args:
            roleid: Role ID

        Returns:
            Role object
        """
        data: ResponseData = await self.proxmox.access.roles(roleid).get()
        return Role.from_dict(data)

    async def create_role(self, roleid: str, privs: list[str] | None = None) -> None:
        """
        Create a new role.

        Args:
            roleid: Role ID
            privs: List of privileges
        """
        params = {"roleid": roleid}
        if privs:
            params["privs"] = ",".join(privs)
        await self.proxmox.access.roles.post(**params)

    async def update_role(
        self, roleid: str, privs: list[str] | None = None, append: bool = False
    ) -> None:
        """
        Update role privileges.

        Args:
            roleid: Role ID
            privs: List of privileges
            append: Append privileges instead of replacing
        """
        params = {}
        if privs is not None:
            params["privs"] = ",".join(privs)
        if append:
            params["append"] = 1
        await self.proxmox.access.roles(roleid).put(**params)

    async def delete_role(self, roleid: str) -> None:
        """
        Delete a role.

        Args:
            roleid: Role ID to delete
        """
        await self.proxmox.access.roles(roleid).delete()

    # ACL Management
    async def list_acls(self) -> list[ACL]:
        """
        List all ACL entries.

        Returns:
            List of ACL objects
        """
        data: ResponseData = await self.proxmox.access.acl.get()
        return [ACL.from_dict(a) for a in data]

    async def update_acl(
        self,
        path: str,
        roles: list[str],
        users: list[str] | None = None,
        groups: list[str] | None = None,
        propagate: bool = True,
        delete: bool = False,
    ) -> None:
        """
        Update ACL.

        Args:
            path: Access control path
            roles: List of role IDs
            users: List of user IDs
            groups: List of group IDs
            propagate: Allow to propagate (inherit) permissions
            delete: Remove permissions instead of adding
        """
        params = {"path": path, "roles": ",".join(roles)}
        if users:
            params["users"] = ",".join(users)
        if groups:
            params["groups"] = ",".join(groups)
        if not propagate:
            params["propagate"] = 0
        if delete:
            params["delete"] = 1

        await self.proxmox.access.acl.put(**params)

    # Domain Management
    async def list_domains(self) -> list[Domain]:
        """
        List authentication domains/realms.

        Returns:
            List of Domain objects
        """
        data: ResponseData = await self.proxmox.access.domains.get()
        return [Domain.from_dict(d) for d in data]

    async def get_domain(self, realm: str) -> Domain:
        """
        Get domain details.

        Args:
            realm: Realm/domain name

        Returns:
            Domain object
        """
        data: ResponseData = await self.proxmox.access.domains(realm).get()
        return Domain.from_dict(data)

    # API Token Management
    async def list_tokens(self, userid: str) -> list[APIToken]:
        """
        List API tokens for a user.

        Args:
            userid: User ID

        Returns:
            List of APIToken objects
        """
        data: ResponseData = await self.proxmox.access.users(userid).token.get()
        return [APIToken.from_dict(t) for t in data]

    async def create_token(
        self,
        userid: str,
        tokenid: str,
        comment: str | None = None,
        expire: int | None = None,
        privsep: bool = True,
    ) -> dict[str, Any]:
        """
        Create API token for a user.

        Args:
            userid: User ID
            tokenid: Token ID
            comment: Comment
            expire: Expiration date (UNIX timestamp)
            privsep: Privilege separation (restrict to user's permissions)

        Returns:
            Dict containing the token value (only returned on creation!)
        """
        params = {"tokenid": tokenid}
        if comment:
            params["comment"] = comment
        if expire:
            params["expire"] = expire
        if not privsep:
            params["privsep"] = 0

        return await self.proxmox.access.users(userid).token.post(**params)

    async def update_token(
        self,
        userid: str,
        tokenid: str,
        comment: str | None = None,
        expire: int | None = None,
        privsep: bool | None = None,
    ) -> None:
        """
        Update API token.

        Args:
            userid: User ID
            tokenid: Token ID
            comment: Comment
            expire: Expiration date (UNIX timestamp)
            privsep: Privilege separation
        """
        params = {}
        if comment is not None:
            params["comment"] = comment
        if expire is not None:
            params["expire"] = expire
        if privsep is not None:
            params["privsep"] = 1 if privsep else 0

        await self.proxmox.access.users(userid).token(tokenid).put(**params)

    async def delete_token(self, userid: str, tokenid: str) -> None:
        """
        Delete API token.

        Args:
            userid: User ID
            tokenid: Token ID
        """
        await self.proxmox.access.users(userid).token(tokenid).delete()

    async def get_permissions(
        self, userid: str | None = None, path: str | None = None
    ) -> dict[str, Any]:
        """
        Get permission information.

        Args:
            userid: User ID (optional, defaults to current user)
            path: Only return permissions for a specific path

        Returns:
            Dict of permissions
        """
        params = {}
        if userid:
            params["userid"] = userid
        if path:
            params["path"] = path

        return await self.proxmox.access.permissions.get(**params)

    # TFA Management
    async def list_tfa(self, userid: str) -> list[dict[str, Any]]:
        """
        List TFA devices for a user.

        Args:
            userid: User ID

        Returns:
            List of TFA device configs
        """
        return await self.proxmox.access.tfa(userid).get()

    async def unlock_tfa(self, userid: str) -> None:
        """
        Unlock a user's TFA configuration.

        Args:
            userid: User ID
        """
        await self.proxmox.access.users(userid)("unlock-tfa").put()
