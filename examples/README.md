# Proxmoxer Helpers - Examples

This directory contains comprehensive examples for all Proxmoxer helpers. Each example file demonstrates the complete functionality of a specific helper manager.

## Available Examples

### 1. **access_example.py** - AccessManager
Complete user, group, role, and permission management.

**Topics covered:**
- User management (create, update, delete, password changes)
- Group management
- Role creation with privileges
- ACL (Access Control List) management
- API token generation and management
- Permission queries
- Authentication domains
- Two-Factor Authentication (TFA)

**Run:**
```bash
python examples/access_example.py
```

---

### 2. **cluster_example.py** - ClusterManager
Cluster-wide operations and configurations.

**Topics covered:**
- Cluster status and resource monitoring
- High Availability (HA) groups and resources
- HA migration and relocation
- Backup job scheduling with retention policies
- VM replication between nodes
- ACME/Let's Encrypt certificate management
- Cluster options configuration

**Run:**
```bash
python examples/cluster_example.py
```

---

### 3. **nodes_example.py** - NodeManager
Node-specific operations and VM/container management.

**Topics covered:**
- Node status and information
- List VMs and containers (QEMU/LXC)
- VM lifecycle (create, start, stop, shutdown, reboot)
- VM operations (clone, migrate, convert to template)
- Snapshot management (create, list, rollback, delete)
- QEMU guest agent operations (25+ operations)
- Storage operations and content management
- Service management (start, stop, restart)
- Task monitoring
- Backup operations
- Network interface management

**Run:**
```bash
python examples/nodes_example.py
```

---

### 4. **pools_example.py** - PoolManager
Resource pool management for organizing VMs and storage.

**Topics covered:**
- List and create pools
- Add/remove VMs to pools
- Add/remove storage to pools
- Get pool details and organized members
- Update pool configuration
- Practical use cases (environment, customer, department organization)

**Run:**
```bash
python examples/pools_example.py
```

---

### 5. **storage_example.py** - StorageManager
Storage backend configuration for all supported types.

**Topics covered:**
- List storage (all or by type)
- Create NFS storage
- Create CIFS/SMB storage with authentication
- Create Directory storage
- Create LVM and LVM-thin storage
- Create ZFS storage with RAID options
- Create Ceph RBD storage
- Create Proxmox Backup Server (PBS) storage
- Update storage configuration
- Enable/disable storage
- Delete storage

**Run:**
```bash
python examples/storage_example.py
```

---

### 6. **sdn_example.py** - SDNManager
Software-Defined Networking configuration.

**Topics covered:**
- Create SDN zones (VXLAN, VLAN, EVPN, QinQ)
- Create virtual networks (VNets)
- Create subnets with DHCP
- Configure SDN controllers (BGP, EVPN)
- IPAM (IP Address Management) integration
- DNS configuration
- Apply SDN changes

**Run:**
```bash
python examples/sdn_example.py
```

---

### 7. **ceph_example.py** - CephManager
Ceph storage cluster management.

**Topics covered:**
- Initialize Ceph cluster
- Get Ceph status (health, OSDs, monitors, pools)
- Create monitors (MON)
- Create managers (MGR)
- Create OSDs with DB/WAL devices
- Create storage pools with replication
- Create CephFS filesystems
- CRUSH map and rules
- Ceph flags management

**Run:**
```bash
python examples/ceph_example.py
```

---

### 8. **tasks_example.py** - TasksHelper
Asynchronous task tracking and monitoring.

**Topics covered:**
- Parse UPID (task identifier)
- Get task status
- Wait for task completion with timeout
- Progress callbacks during task execution
- Get task logs
- Stream task logs in real-time
- Wait for multiple tasks concurrently
- List node/cluster tasks
- Get active and failed tasks
- Stop running tasks

**Run:**
```bash
python examples/tasks_example.py
```

---

### 9. **notifications_example.py** - NotificationManager
Notification system configuration.

**Topics covered:**
- Create SMTP endpoints with authentication
- Create Sendmail endpoints
- Create Gotify endpoints for push notifications
- Create Webhook endpoints (Slack, Teams, etc.)
- Create notification matchers with severity filters
- Update endpoints and matchers
- Test endpoints
- List endpoints, matchers, and targets

**Run:**
```bash
python examples/notifications_example.py
```

---

### 10. **disks_example.py** - DiskManager
Disk management and storage initialization.

**Topics covered:**
- List all disks with details
- Filter disks by type (HDD/SSD)
- Get unused disks
- SMART health monitoring
- Find disks by serial number
- Create LVM volume groups
- Create LVM-thin pools
- Create ZFS pools (single, mirror, raidz)
- Create directory storage (format and mount)
- List existing storage
- Wipe disks
- Delete storage with cleanup

**Run:**
```bash
python examples/disks_example.py
```

---

### 11. **firewall_example.py** - FirewallManager
Firewall rule management (existing example).

**Topics covered:**
- Firewall rules (add, update, delete)
- Firewall options
- IP aliases and IP sets
- Security groups
- Firewall logs and references

**Run:**
```bash
python examples/firewall_example.py
```

---

## Quick Start

### Prerequisites

1. Install async-proxmoxer:
```bash
pip install proxmoxer
```

2. Update connection details in each example:
```python
proxmox = await ProxmoxAPI.create(
    host="pve.example.com",  # Your Proxmox host
    user="root@pam",         # Your username
    password="password",     # Your password
    verify_ssl=False,
)
```

### Running Examples

Each example is standalone and can be run independently:

```bash
# Run specific example
python examples/access_example.py

# Or with python3
python3 examples/nodes_example.py
```

### Example Structure

Each example follows this structure:

1. **Import helpers and types**
2. **Initialize connection**
3. **Create manager instance**
4. **Demonstrate features** (numbered sections)
5. **Cleanup** (optional)
6. **Summary** of what was covered

## Learning Path

Recommended order for learning:

1. **access_example.py** - Start with users and permissions
2. **pools_example.py** - Learn resource organization
3. **storage_example.py** - Configure storage backends
4. **nodes_example.py** - Create and manage VMs
5. **cluster_example.py** - Cluster operations and HA
6. **tasks_example.py** - Monitor asynchronous operations
7. **sdn_example.py** - Advanced networking
8. **ceph_example.py** - Ceph storage (if using Ceph)
9. **notifications_example.py** - Set up alerting
10. **disks_example.py** - Low-level disk management
11. **firewall_example.py** - Security configuration

## Contributing

To add new examples:

1. Follow the existing structure
2. Include comprehensive comments
3. Add to this README
4. Test thoroughly
