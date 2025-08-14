# Database Architecture Documentation

## Overview

The Firewallo application uses a modular database structure designed to be the backbone of the application. This structure provides clear separation between different functional areas and allows for extensible plugin architecture.

## Database Structure

The database follows a hierarchical modular structure with three main sections:

### 1. Plugins Section (`plugins.*`)

The plugins section contains all plugin-related data, organized by plugin type and specific plugin implementations.

#### Structure:
```json
{
  "plugins": {
    "vpn": {
      "wireguard": {
        "servers": [
          {
            "interface": "wg0",
            "private_key": "...",
            "public_key": "...",
            "listen_port": 51820,
            "address": "10.0.0.1/24",
            "mtu": 1420,
            "peers": [...]
          }
        ]
      }
    }
  }
}
```

#### VPN Plugins (`plugins.vpn.*`)

##### WireGuard Plugin (`plugins.vpn.wireguard`)

- **Path**: `plugins.vpn.wireguard`
- **Purpose**: Stores WireGuard VPN server and peer configurations
- **Sub-sections**:
  - `servers`: Array of WireGuard server configurations, each containing their associated peers

**Server Document Schema**:
```json
{
  "interface": "string",
  "private_key": "string", 
  "public_key": "string",
  "listen_port": "number",
  "address": "string",
  "mtu": "number",
  "peers": [...]
}
```

**Peer Document Schema** (nested within server):
```json
{
  "username": "string",
  "server_interface": "string",
  "private_ip": "string",
  "private_key": "string",
  "public_key": "string", 
  "allowed_ips": "string",
  "endpoint": "string|null",
  "group": "string|null",
  "persistent_keepalive": "number|null",
  "preshared_key": "string|null"
}
```

### 2. Core Section (`core.*`)

The core section contains application-level functionality and configuration.

#### Structure:
```json
{
  "core": {
    "system": {},
    "config": {},
    "logs": []
  }
}
```

#### Core Sub-sections:

- **`core.system`**: System-level configuration and status
- **`core.config`**: Application configuration settings
- **`core.logs`**: Application logs and audit trail

### 3. Authentication & Authorization Section (`auth.*`)

The auth section handles user authentication and role-based access control.

#### Structure:
```json
{
  "auth": {
    "users": [...],
    "rbac": {
      "roles": [],
      "permissions": [],
      "assignments": []
    }
  }
}
```

#### Auth Sub-sections:

##### Users (`auth.users`)
- **Path**: `auth.users`
- **Purpose**: Store user accounts and authentication data
- **Schema**:
```json
{
  "email": "string",
  "username": "string", 
  "hashed_password": "string",
  "is_active": "boolean",
  "is_superuser": "boolean",
  "created_at": "string|null"
}
```

##### RBAC (`auth.rbac`)
- **Path**: `auth.rbac`
- **Purpose**: Role-based access control system
- **Sub-sections**:
  - `roles`: Available roles in the system
  - `permissions`: Available permissions
  - `assignments`: User-role assignments

## Backend Implementations

### LiteDB Backend

- **Type**: Local JSON file storage
- **Location**: `app/db/metadata.json`
- **Use Case**: Development, small deployments, single-node setups
- **Features**: Simple file-based storage with atomic read/write operations

### MongoDB Backend

- **Type**: Document database (MongoDB)
- **Use Case**: Production deployments, multi-node setups, high availability
- **Features**: Distributed storage, transactions, indexing, replication

## Migration

### Database Migration

The application includes a migration system to convert from old flat structure to the new modular structure.

**Migration Script**: `app/db/migration.py`

**Usage**:
```bash
python -m app.db.migration app/db/metadata.json
```

**Migration Process**:
1. Creates backup of existing database
2. Converts flat structure to modular structure
3. Validates new structure
4. Reports migration status

### Old vs New Structure

**Old Structure (Legacy)**:
```json
{
  "servers": [...],
  "peers": [...],
  "users": [...]
}
```

**New Structure (Modular)**:
```json
{
  "plugins": {
    "vpn": {
      "wireguard": {
        "servers": [
          {
            "interface": "wg0",
            "private_key": "...",
            "public_key": "...",
            "listen_port": 51820,
            "address": "10.0.0.1/24",
            "mtu": 1420,
            "peers": [...]
          }
        ]
      }
    }
  },
  "core": {
    "system": {},
    "config": {},
    "logs": []
  },
  "auth": {
    "users": [...],
    "rbac": {
      "roles": [],
      "permissions": [],
      "assignments": []
    }
  }
}
```

## Repository Layer

The repository layer provides a unified interface for accessing data regardless of the backend implementation.

### Key Components:

1. **Repository Interface**: `app/wireguard_manager/repository.py`
2. **LiteDB Backend**: `app/wireguard_manager/backends/litedb.py`
3. **Database Configuration**: `app/wireguard_manager/database.py`

### Usage Examples:

```python
from app.wireguard_manager.repository import repo

# Access WireGuard servers (plugins.vpn.wireguard.servers)
servers = repo.list_servers()

# Access WireGuard peers for a specific server
for server in servers:
    peers = server.get('peers', [])

# Access users (auth.users)
users = repo.list_users()
```

## Configuration

### Environment Variables:

- `DATABASE_TYPE`: Backend type (`litedb` or `mongodb`)
- `MONGO_URI`: MongoDB connection URI (if using MongoDB)
- `MONGO_DB_NAME`: MongoDB database name (if using MongoDB)

### Default Configuration:

- **Backend**: LiteDB (local JSON file)
- **Database File**: `app/db/metadata.json`
- **Auto-create**: Database file created with proper structure if missing

## Best Practices

### 1. Section Naming Convention
- Use dot notation for hierarchical paths
- Plugins: `plugins.<category>.<plugin_name>`
- Core: `core.<function>`
- Auth: `auth.<component>`

### 2. Data Organization
- Keep related data in appropriate sections
- Use consistent document schemas within sections
- Maintain referential integrity (e.g., peer.server_interface → server.interface)

### 3. Extension Points
- Add new plugins under `plugins.<category>.<new_plugin>`
- Add core functions under `core.<new_function>`
- Extend RBAC with additional roles/permissions under `auth.rbac`

### 4. Validation
- Use the migration script to validate database structure
- Check for required sections and proper schemas
- Monitor for missing or malformed data

## Future Extensions

The modular structure supports easy extension:

### New VPN Plugins
```json
{
  "plugins": {
    "vpn": {
      "wireguard": {...},
      "openvpn": {...},
      "ipsec": {...}
    }
  }
}
```

### Additional Plugin Categories
```json
{
  "plugins": {
    "vpn": {...},
    "firewall": {
      "iptables": {...},
      "nftables": {...}
    },
    "monitoring": {
      "prometheus": {...},
      "grafana": {...}
    }
  }
}
```

### Extended Core Functions
```json
{
  "core": {
    "system": {...},
    "config": {...},
    "logs": [...],
    "metrics": {...},
    "backup": {...},
    "scheduler": {...}
  }
}
```

This modular database structure provides a solid foundation for the application's growth and extensibility while maintaining clear separation of concerns and data organization.
