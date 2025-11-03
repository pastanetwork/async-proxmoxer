"""
Comprehensive tests for AccessManager helper.
Tests all user, group, role, ACL, domain, and TFA management methods.
"""

import pytest
from proxmoxer.helpers.access import (
    AccessManager,
    User,
    Group,
    Role,
    ACL,
    Domain,
    APIToken,
)


@pytest.fixture
def access_manager(mock_proxmox):
    """Create AccessManager instance with mocked API."""
    return AccessManager(mock_proxmox)


# ==================== User Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestUserManagement:
    async def test_list_users(self, access_manager, sample_user_data):
        """Test listing all users."""
        access_manager.proxmox.access.users.get.return_value = [sample_user_data]

        result = await access_manager.list_users()

        assert len(result) == 1
        assert isinstance(result[0], User)
        assert result[0].userid == "user@pve"

    async def test_list_users_filtered(self, access_manager, sample_user_data):
        """Test listing users with filters."""
        access_manager.proxmox.access.users.get.return_value = [sample_user_data]

        result = await access_manager.list_users(enabled=True)

        access_manager.proxmox.access.users.get.assert_called_once_with(enabled=1)

    async def test_get_user(self, access_manager, sample_user_data):
        """Test getting user details."""
        access_manager.proxmox.access.users("user@pve").get.return_value = sample_user_data

        result = await access_manager.get_user("user@pve")

        assert isinstance(result, User)
        assert result.email == "user@example.com"

    async def test_create_user(self, access_manager):
        """Test creating user."""
        await access_manager.create_user(
            "newuser@pve",
            password="secret123",
            email="new@example.com",
            groups=["admin", "ops"]
        )

        call_args = access_manager.proxmox.access.users.post.call_args[1]
        assert call_args["userid"] == "newuser@pve"
        assert call_args["groups"] == "admin,ops"

    async def test_update_user(self, access_manager):
        """Test updating user."""
        await access_manager.update_user(
            "user@pve",
            email="updated@example.com",
            enable=False
        )

        call_args = access_manager.proxmox.access.users("user@pve").put.call_args[1]
        assert call_args["email"] == "updated@example.com"
        assert call_args["enable"] == 0

    async def test_delete_user(self, access_manager):
        """Test deleting user."""
        await access_manager.delete_user("user@pve")

        access_manager.proxmox.access.users("user@pve").delete.assert_called_once()

    async def test_set_password(self, access_manager):
        """Test setting user password."""
        await access_manager.set_password("user@pve", "newpassword")

        access_manager.proxmox.access.password.put.assert_called_once_with(
            userid="user@pve",
            password="newpassword"
        )


# ==================== Group Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestGroupManagement:
    async def test_list_groups(self, access_manager, sample_group_data):
        """Test listing groups."""
        access_manager.proxmox.access.groups.get.return_value = [sample_group_data]

        result = await access_manager.list_groups()

        assert len(result) == 1
        assert isinstance(result[0], Group)
        assert result[0].groupid == "admin"

    async def test_get_group(self, access_manager, sample_group_data):
        """Test getting group details."""
        access_manager.proxmox.access.groups("admin").get.return_value = sample_group_data

        result = await access_manager.get_group("admin")

        assert isinstance(result, Group)
        assert result.comment == "Administrators"

    async def test_create_group(self, access_manager):
        """Test creating group."""
        await access_manager.create_group("developers", comment="Dev team")

        call_args = access_manager.proxmox.access.groups.post.call_args[1]
        assert call_args["groupid"] == "developers"
        assert call_args["comment"] == "Dev team"

    async def test_update_group(self, access_manager):
        """Test updating group."""
        await access_manager.update_group("admin", comment="Updated comment")

        access_manager.proxmox.access.groups("admin").put.assert_called_once()

    async def test_delete_group(self, access_manager):
        """Test deleting group."""
        await access_manager.delete_group("admin")

        access_manager.proxmox.access.groups("admin").delete.assert_called_once()


# ==================== Role Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestRoleManagement:
    async def test_list_roles(self, access_manager, sample_role_data):
        """Test listing roles."""
        access_manager.proxmox.access.roles.get.return_value = [sample_role_data]

        result = await access_manager.list_roles()

        assert len(result) == 1
        assert isinstance(result[0], Role)

    async def test_get_role(self, access_manager, sample_role_data):
        """Test getting role details."""
        access_manager.proxmox.access.roles("Administrator").get.return_value = sample_role_data

        result = await access_manager.get_role("Administrator")

        assert isinstance(result, Role)
        assert result.special is True

    async def test_create_role(self, access_manager):
        """Test creating role."""
        await access_manager.create_role(
            "CustomRole",
            privs=["VM.Allocate", "Datastore.Allocate"]
        )

        call_args = access_manager.proxmox.access.roles.post.call_args[1]
        assert "VM.Allocate" in call_args["privs"]

    async def test_update_role(self, access_manager):
        """Test updating role."""
        await access_manager.update_role(
            "CustomRole",
            privs=["VM.Config.Disk"],
            append=True
        )

        call_args = access_manager.proxmox.access.roles("CustomRole").put.call_args[1]
        assert call_args["append"] == 1

    async def test_delete_role(self, access_manager):
        """Test deleting role."""
        await access_manager.delete_role("CustomRole")

        access_manager.proxmox.access.roles("CustomRole").delete.assert_called_once()


# ==================== ACL Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestACLManagement:
    async def test_list_acls(self, access_manager):
        """Test listing ACLs."""
        acl_data = [{
            "path": "/vms/100",
            "roleid": "Administrator",
            "type": "user",
            "ugid": "user@pve",
            "propagate": 1,
        }]
        access_manager.proxmox.access.acl.get.return_value = acl_data

        result = await access_manager.list_acls()

        assert len(result) == 1
        assert isinstance(result[0], ACL)

    async def test_update_acl(self, access_manager):
        """Test updating ACL."""
        await access_manager.update_acl(
            path="/vms/100",
            roles=["Administrator"],
            users=["user@pve"],
            propagate=False
        )

        call_args = access_manager.proxmox.access.acl.put.call_args[1]
        assert call_args["path"] == "/vms/100"
        assert call_args["propagate"] == 0


# ==================== Domain Management Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestDomainManagement:
    async def test_list_domains(self, access_manager):
        """Test listing domains."""
        domain_data = [{
            "realm": "pve",
            "type": "pve",
            "comment": "Proxmox VE authentication server",
            "default": 1,
        }]
        access_manager.proxmox.access.domains.get.return_value = domain_data

        result = await access_manager.list_domains()

        assert len(result) == 1
        assert isinstance(result[0], Domain)

    async def test_get_domain(self, access_manager):
        """Test getting domain details."""
        domain_data = {
            "realm": "pve",
            "type": "pve",
            "default": 1,
        }
        access_manager.proxmox.access.domains("pve").get.return_value = domain_data

        result = await access_manager.get_domain("pve")

        assert isinstance(result, Domain)
        assert result.default is True


# ==================== API Token Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestAPITokens:
    async def test_list_tokens(self, access_manager):
        """Test listing API tokens."""
        token_data = [{
            "tokenid": "test",
            "userid": "user@pve",
            "expire": 0,
            "privsep": 1,
        }]
        access_manager.proxmox.access.users("user@pve").token.get.return_value = token_data

        result = await access_manager.list_tokens("user@pve")

        assert len(result) == 1
        assert isinstance(result[0], APIToken)

    async def test_create_token(self, access_manager):
        """Test creating API token."""
        token_response = {
            "value": "secret-token-value",
            "info": {"tokenid": "test"}
        }
        access_manager.proxmox.access.users("user@pve").token.post.return_value = token_response

        result = await access_manager.create_token(
            "user@pve",
            "test",
            comment="Test token",
            privsep=False
        )

        assert "value" in result or result == token_response

    async def test_update_token(self, access_manager):
        """Test updating API token."""
        await access_manager.update_token(
            "user@pve",
            "test",
            comment="Updated token"
        )

        access_manager.proxmox.access.users("user@pve").token("test").put.assert_called_once()

    async def test_delete_token(self, access_manager):
        """Test deleting API token."""
        await access_manager.delete_token("user@pve", "test")

        access_manager.proxmox.access.users("user@pve").token("test").delete.assert_called_once()


# ==================== Permissions Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestPermissions:
    async def test_get_permissions(self, access_manager):
        """Test getting permissions."""
        perms = {"/vms": {"VM.Allocate": 1}}
        access_manager.proxmox.access.permissions.get.return_value = perms

        result = await access_manager.get_permissions(userid="user@pve")

        assert result == perms

    async def test_get_permissions_for_path(self, access_manager):
        """Test getting permissions for specific path."""
        perms = {"VM.Allocate": 1}
        access_manager.proxmox.access.permissions.get.return_value = perms

        result = await access_manager.get_permissions(path="/vms/100")

        assert result == perms


# ==================== TFA Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
@pytest.mark.asyncio
class TestTFA:
    async def test_list_tfa(self, access_manager):
        """Test listing TFA devices."""
        tfa_data = [{"type": "totp", "id": "device1"}]
        access_manager.proxmox.access.tfa("user@pve").get.return_value = tfa_data

        result = await access_manager.list_tfa("user@pve")

        assert result == tfa_data

    async def test_unlock_tfa(self, access_manager):
        """Test unlocking TFA."""
        await access_manager.unlock_tfa("user@pve")

        access_manager.proxmox.access.users("user@pve")("unlock-tfa").put.assert_called_once()


# ==================== Dataclass Tests ====================

@pytest.mark.unit
@pytest.mark.helpers
class TestAccessDataclasses:
    """Test all dataclass from_dict methods."""

    def test_user_from_dict(self, sample_user_data):
        """Test User.from_dict."""
        result = User.from_dict(sample_user_data)

        assert result.userid == "user@pve"
        assert result.groups == ["admin", "ops"]

    def test_group_from_dict(self, sample_group_data):
        """Test Group.from_dict."""
        result = Group.from_dict(sample_group_data)

        assert result.groupid == "admin"
        assert "user1@pve" in result.users

    def test_role_from_dict(self, sample_role_data):
        """Test Role.from_dict."""
        result = Role.from_dict(sample_role_data)

        assert result.roleid == "Administrator"
        assert result.special is True

    def test_acl_from_dict(self):
        """Test ACL.from_dict."""
        data = {
            "path": "/vms",
            "roleid": "Administrator",
            "type": "user",
            "ugid": "user@pve",
            "propagate": 1,
        }

        result = ACL.from_dict(data)

        assert result.path == "/vms"
        assert result.propagate is True

    def test_domain_from_dict(self):
        """Test Domain.from_dict."""
        data = {
            "realm": "pve",
            "type": "pve",
            "default": 1,
        }

        result = Domain.from_dict(data)

        assert result.realm == "pve"
        assert result.default is True

    def test_api_token_from_dict(self):
        """Test APIToken.from_dict."""
        data = {
            "tokenid": "test",
            "userid": "user@pve",
            "privsep": 1,
        }

        result = APIToken.from_dict(data)

        assert result.tokenid == "test"
        assert result.privsep is True
