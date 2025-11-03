"""
AccessManager Example - User, Group, Role, and ACL Management

This example demonstrates how to manage authentication, users, groups,
roles, ACLs, and API tokens in Proxmox VE.
"""
import asyncio
from proxmoxer import ProxmoxAPI
from proxmoxer.helpers import AccessManager


async def main():
    # Initialize connection
    proxmox = await ProxmoxAPI.create(
        host="pve.example.com",
        user="root@pam",
        password="password",
        verify_ssl=False,
    )

    access = AccessManager(proxmox)

    print("=" * 60)
    print("AccessManager Examples - User & Permission Management")
    print("=" * 60)

    # ========================================
    # 1. USER MANAGEMENT
    # ========================================
    print("\n[1] USER MANAGEMENT")
    print("-" * 60)

    # List all users
    users = await access.list_users()
    print(f"Total users: {len(users)}")
    for user in users[:3]:
        print(f"  - {user.userid}")
        print(f"    Email: {user.email}")
        print(f"    Groups: {user.groups}")
        print(f"    Enabled: {user.enable}")

    # Create a new user
    print("\n[Create User]")
    await access.create_user(
        userid="john.doe@pve",
        password="SecurePassword123!",
        email="john.doe@example.com",
        firstname="John",
        lastname="Doe",
        groups=["Administrators"],
        expire=0,  # Never expires
        enable=True,
        comment="Senior System Administrator",
    )
    print("Created user: john.doe@pve")

    # Get user details
    user = await access.get_user("john.doe@pve")
    print(f"User details: {user.userid} - {user.email}")

    # Update user
    print("\n[Update User]")
    await access.update_user(
        userid="john.doe@pve",
        email="john.d@example.com",
        comment="Senior System Administrator - Updated",
    )
    print("Updated user email and comment")

    # Change password
    print("\n[Change Password]")
    await access.set_password("john.doe@pve", "NewSecurePassword456!")
    print("Changed user password")

    # ========================================
    # 2. GROUP MANAGEMENT
    # ========================================
    print("\n[2] GROUP MANAGEMENT")
    print("-" * 60)

    # List groups
    groups = await access.list_groups()
    print(f"Total groups: {len(groups)}")
    for group in groups:
        print(f"  - {group.groupid}: {group.comment}")

    # Create group
    print("\n[Create Group]")
    await access.create_group(
        groupid="developers",
        comment="Development team members",
    )
    print("Created group: developers")

    await access.create_group(
        groupid="operators",
        comment="System operators",
    )
    print("Created group: operators")

    # Update group
    await access.update_group(
        groupid="developers",
        comment="Development team - Full access to dev VMs",
    )
    print("Updated group comment")

    # ========================================
    # 3. ROLE MANAGEMENT
    # ========================================
    print("\n[3] ROLE MANAGEMENT")
    print("-" * 60)

    # List roles
    roles = await access.list_roles()
    print(f"Total roles: {len(roles)}")
    for role in roles[:5]:
        print(f"  - {role.roleid}")
        if role.privs:
            print(f"    Privileges: {', '.join(role.privs[:3])}...")

    # Create custom role
    print("\n[Create Role]")
    await access.create_role(
        roleid="VMOperator",
        privs=[
            "VM.Audit",        # View VM configuration
            "VM.Console",      # Access VM console
            "VM.PowerMgmt",    # Start/stop/reboot VMs
            "Datastore.Audit", # View storage
        ],
    )
    print("Created role: VMOperator")

    # Create another role
    await access.create_role(
        roleid="BackupOperator",
        privs=[
            "VM.Audit",
            "VM.Backup",
            "Datastore.Allocate",
            "Datastore.AllocateSpace",
        ],
    )
    print("Created role: BackupOperator")

    # Update role (append privileges)
    print("\n[Update Role - Append Privileges]")
    await access.update_role(
        roleid="VMOperator",
        privs=["VM.Config.Network"],  # Add network configuration
        append=True,
    )
    print("Added network config privilege to VMOperator")

    # ========================================
    # 4. ACL MANAGEMENT
    # ========================================
    print("\n[4] ACL (Access Control List) MANAGEMENT")
    print("-" * 60)

    # List all ACLs
    acls = await access.list_acls()
    print(f"Total ACL entries: {len(acls)}")
    for acl in acls[:3]:
        print(f"  - Path: {acl.path}")
        print(f"    Role: {acl.roleid}")
        print(f"    User/Group: {acl.ugid} ({acl.type})")

    # Grant VM permissions to user
    print("\n[Grant Permissions]")
    await access.update_acl(
        path="/vms/100",
        roles=["VMOperator"],
        users=["john.doe@pve"],
        propagate=True,
    )
    print("Granted VMOperator role to john.doe@pve on VM 100")

    # Grant storage permissions to group
    await access.update_acl(
        path="/storage/local-lvm",
        roles=["BackupOperator"],
        groups=["developers"],
        propagate=False,
    )
    print("Granted BackupOperator role to developers group on storage")

    # Grant pool permissions
    await access.update_acl(
        path="/pool/production",
        roles=["VMOperator"],
        groups=["operators"],
        propagate=True,
    )
    print("Granted VMOperator role to operators group on production pool")

    # Revoke permissions
    print("\n[Revoke Permissions]")
    await access.update_acl(
        path="/vms/100",
        roles=["VMOperator"],
        users=["john.doe@pve"],
        delete=True,
    )
    print("Revoked permissions from john.doe@pve on VM 100")

    # ========================================
    # 5. API TOKEN MANAGEMENT
    # ========================================
    print("\n[5] API TOKEN MANAGEMENT")
    print("-" * 60)

    # List tokens for user
    tokens = await access.list_tokens("john.doe@pve")
    print(f"Tokens for john.doe@pve: {len(tokens)}")

    # Create API token
    print("\n[Create API Token]")
    token_info = await access.create_token(
        userid="john.doe@pve",
        tokenid="automation",
        comment="Token for automation scripts",
        expire=0,  # Never expires
        privsep=True,  # Restrict to user's permissions
    )
    print("Created API token: automation")
    print(f"  Token value: {token_info.get('value', 'N/A')}")
    print("  WARNING:Save this token! It won't be shown again!")

    # Create another token without privilege separation
    token_info2 = await access.create_token(
        userid="john.doe@pve",
        tokenid="monitoring",
        comment="Monitoring system token",
        privsep=False,  # Full access like user
    )
    print("Created API token: monitoring (full privileges)")

    # Update token
    print("\n[Update Token]")
    await access.update_token(
        userid="john.doe@pve",
        tokenid="automation",
        comment="Token for automation scripts - Updated",
    )
    print("Updated token comment")

    # ========================================
    # 6. PERMISSION QUERIES
    # ========================================
    print("\n[6] PERMISSION QUERIES")
    print("-" * 60)

    # Get permissions for current user
    print("\n[Current User Permissions]")
    perms = await access.get_permissions()
    print(f"Permission entries: {len(perms)}")

    # Get permissions for specific user
    print("\n[Specific User Permissions]")
    user_perms = await access.get_permissions(userid="john.doe@pve")
    print(f"Permissions for john.doe@pve: {len(user_perms)}")
    for path, roles in list(user_perms.items())[:3]:
        print(f"  {path}: {roles}")

    # Get permissions for specific path
    print("\n[Path Permissions]")
    path_perms = await access.get_permissions(
        userid="john.doe@pve",
        path="/vms",
    )
    print(f"VM permissions for john.doe@pve: {path_perms}")

    # ========================================
    # 7. DOMAIN MANAGEMENT
    # ========================================
    print("\n[7] AUTHENTICATION DOMAINS")
    print("-" * 60)

    # List authentication domains
    domains = await access.list_domains()
    print(f"Total domains: {len(domains)}")
    for domain in domains:
        print(f"  - {domain.realm} ({domain.type})")
        if domain.comment:
            print(f"    Comment: {domain.comment}")
        if domain.tfa:
            print(f"    TFA: {domain.tfa}")

    # ========================================
    # 8. TFA (Two-Factor Authentication)
    # ========================================
    print("\n[8] TWO-FACTOR AUTHENTICATION")
    print("-" * 60)

    # List TFA devices for user
    try:
        tfa_devices = await access.list_tfa("john.doe@pve")
        print(f"TFA devices for john.doe@pve: {len(tfa_devices)}")
        for device in tfa_devices:
            print(f"  - {device}")
    except Exception as e:
        print(f"No TFA devices configured (or error): {e}")

    # Unlock TFA (if locked)
    # await access.unlock_tfa("john.doe@pve")
    # print("Unlocked TFA for user")

    # ========================================
    # 9. CLEANUP (OPTIONAL)
    # ========================================
    print("\n[9] CLEANUP")
    print("-" * 60)

    # Delete token
    print("\n[Delete Token]")
    await access.delete_token("john.doe@pve", "monitoring")
    print("Deleted token: monitoring")

    # Delete role
    print("\n[Delete Role]")
    await access.delete_role("BackupOperator")
    print("Deleted role: BackupOperator")

    # Delete group
    print("\n[Delete Group]")
    await access.delete_group("operators")
    print("Deleted group: operators")

    # Delete user
    print("\n[Delete User]")
    await access.delete_user("john.doe@pve")
    print("Deleted user: john.doe@pve")

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 60)
    print("ACCESS MANAGEMENT SUMMARY")
    print("=" * 60)
    print("User management (create, update, delete, password)")
    print("Group management (create, update, delete)")
    print("Role management (create, update with privileges)")
    print("ACL management (grant/revoke permissions)")
    print("API token management (create, update, delete)")
    print("Permission queries (user, path-specific)")
    print("Authentication domains listing")
    print("TFA device management")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
