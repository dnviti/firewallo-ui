# Firewallo Plugin Framework Migration Guide

This document describes the migration of the WireGuard implementation from the legacy system to the new Firewallo Plugin Framework.

## Overview

The WireGuard VPN functionality has been completely migrated from a tightly-coupled implementation to a plugin-based architecture that provides better modularity, security, and extensibility.

## What Changed

### Before (Legacy System)
- **Monolithic Structure**: WireGuard code was directly integrated into the main application
- **Direct Database Access**: Used custom repository patterns with direct database coupling
- **Fixed Architecture**: Hard to extend or modify without touching core code
- **Limited Validation**: Basic validation with minimal security checks
- **Manual Route Management**: API routes manually defined in main router

### After (Plugin Framework)
- **Modular Architecture**: WireGuard is now a self-contained plugin
- **Standardized Interfaces**: Implements `VPNPluginInterface` for consistency
- **Plugin Management**: Load, unload, enable, disable at runtime
- **Enhanced Security**: Comprehensive validation and permission system
- **Automatic Integration**: Routes automatically registered when plugin is enabled
- **Hot Reloading**: Update plugins without restarting the application

## Migration Details

### File Structure Changes

**Old Structure:**
```
app/plugins/wireguard/
├── database.py          # Database bootstrap
├── repository.py        # Data access layer
├── schemas.py          # Pydantic models
└── backends/           # Database backends
```

**New Structure:**
```
app/plugins/vpn/wireguard/
├── __init__.py         # Plugin exports
├── plugin.py           # Main plugin implementation
├── manifest.json       # Plugin metadata
└── [additional files]  # Configuration, docs, etc.
```

### API Endpoint Changes

| Legacy Endpoint | New Endpoint | Notes |
|----------------|--------------|-------|
| `GET /api/servers/` | `GET /api/vpn/wireguard/servers` | Now under plugin namespace |
| `POST /api/servers/` | `POST /api/vpn/wireguard/servers` | Enhanced validation |
| `PUT /api/servers/{interface}` | `PUT /api/vpn/wireguard/servers/{id}` | Uses ID instead of interface |
| `GET /api/peers` | `GET /api/vpn/wireguard/clients` | Renamed for clarity |
| `POST /api/servers/{interface}/peers/` | `POST /api/vpn/wireguard/servers/{id}/clients` | Consistent naming |

### Data Model Changes

**Legacy Models (`schemas.py`):**
- `ServerBase`, `ServerCreate`, `ServerUpdate`, `Server`
- `PeerBase`, `PeerCreate`, `PeerUpdate`, `Peer`

**New Models (Plugin Framework):**
- `VPNServerCreate`, `VPNServerResponse`, `VPNServerUpdate`
- `VPNClientCreate`, `VPNClientResponse`, `VPNClientUpdate`
- `VPNConfigResponse`, `VPNConnectionStatus`, `VPNStatistics`

### Database Changes

**Legacy Database Structure:**
```json
{
  "plugins": {
    "vpn": {
      "wireguard": {
        "servers": [],
        "peers": []
      }
    }
  }
}
```

**New Database Structure:**
```json
{
  "plugins": {
    "vpn": {
      "wireguard": {
        "servers": [],
        "clients": [],  // Renamed from "peers"
        "config": {}
      }
    }
  }
}
```

## Key Improvements

### 1. **Enhanced Security**
- **Plugin Validation**: Comprehensive security scanning before loading
- **Permission System**: Granular permissions for different operations
- **Code Analysis**: AST-based analysis to detect unsafe patterns
- **Input Validation**: Stronger validation of all inputs

### 2. **Better Architecture**
- **Interface Compliance**: All VPN plugins implement the same interface
- **Dependency Injection**: Clean separation of concerns
- **Error Handling**: Standardized error handling across all plugins
- **Logging**: Structured logging with plugin-specific loggers

### 3. **Improved Developer Experience**
- **Hot Reloading**: Update plugins without application restart
- **Plugin Management API**: Control plugins via REST API
- **Standardized Configuration**: Consistent configuration patterns
- **Comprehensive Documentation**: Auto-generated API docs

### 4. **Enhanced Functionality**
- **QR Code Generation**: Built-in QR code support for mobile clients
- **Statistics**: Real-time connection and usage statistics
- **Health Monitoring**: Plugin health checks and status reporting
- **Backup/Restore**: Configuration backup and restore capabilities

## Migration Steps for Existing Data

### 1. **Backup Existing Data**
```bash
# Backup current database
cp app/db/metadata.json app/db/metadata.json.backup
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Run Migration Script**
The application will automatically handle data migration when started with the new plugin system.

### 4. **Verify Migration**
```bash
# Test the plugin system
python test_plugins.py

# Start the application
uvicorn app.main:app --reload

# Check plugin status
curl http://localhost:8000/api/plugins/vpn.wireguard
```

## API Usage Examples

### Creating a Server (New Plugin API)

```python
import httpx

# Create server using new plugin API
server_data = {
    "name": "wg0",
    "endpoint": "192.168.1.100",
    "port": 51820,
    "network": "10.0.0.0/24",
    "dns_servers": ["8.8.8.8", "8.8.4.4"],
    "mtu": 1420,
    "enabled": True,
    "description": "Main VPN server"
}

response = httpx.post(
    "http://localhost:8000/api/vpn/wireguard/servers",
    json=server_data,
    headers={"Authorization": "Bearer <token>"}
)
```

### Creating a Client

```python
client_data = {
    "name": "user1",
    "server_id": "server-uuid-here",
    "email": "user1@example.com",
    "allowed_ips": ["0.0.0.0/0"],
    "persistent_keepalive": 25,
    "enabled": True
}

response = httpx.post(
    "http://localhost:8000/api/vpn/wireguard/clients",
    json=client_data,
    headers={"Authorization": "Bearer <token>"}
)
```

### Getting Configuration with QR Code

```python
response = httpx.get(
    "http://localhost:8000/api/vpn/wireguard/clients/{client_id}/config",
    headers={"Authorization": "Bearer <token>"}
)

config_data = response.json()
print(config_data["config_content"])  # WireGuard config
print(config_data["qr_code"])         # Base64 QR code image
```

## Plugin Management

### Managing Plugins via API

```bash
# List all plugins
curl http://localhost:8000/api/plugins/

# Get plugin info
curl http://localhost:8000/api/plugins/vpn.wireguard

# Check plugin health
curl http://localhost:8000/api/plugins/vpn.wireguard/health

# Disable plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/disable

# Enable plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/enable

# Reload plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/reload
```

### Plugin Configuration

```bash
# Get plugin configuration
curl http://localhost:8000/api/plugins/vpn.wireguard/config

# Update plugin configuration
curl -X PUT http://localhost:8000/api/plugins/vpn.wireguard/config \
  -H "Content-Type: application/json" \
  -d '{"interface_name": "wg1", "listen_port": 51821}'
```

## Developing New Plugins

### 1. **Create Plugin Structure**
```
app/plugins/{category}/{plugin_name}/
├── __init__.py
├── plugin.py
├── manifest.json
└── [additional files]
```

### 2. **Implement Plugin Class**
```python
from app.plugins.base import BasePlugin
from app.plugins.categories.vpn import VPNPluginInterface

class MyVPNPlugin(BasePlugin, VPNPluginInterface):
    def __init__(self):
        super().__init__()
        self.name = "myvpn"
        self.category = "vpn"
        # ... implement required methods
```

### 3. **Create Manifest**
```json
{
  "name": "myvpn",
  "category": "vpn",
  "version": "1.0.0",
  "description": "My custom VPN plugin",
  "dependencies": {
    "python": ">=3.11"
  },
  "permissions": ["network.create"]
}
```

### 4. **Register and Test**
The plugin system will automatically discover and load your plugin.

## Troubleshooting

### Common Issues

1. **Plugin Not Loading**
   - Check manifest.json syntax
   - Verify dependencies are installed
   - Check plugin class inherits from BasePlugin
   - Review logs: `docker logs firewallo-ui`

2. **Permission Errors**
   - Ensure required permissions are declared in manifest
   - Check system dependencies (wireguard-tools, iptables)
   - Verify file permissions for /etc/wireguard/

3. **API Endpoints Not Working**
   - Confirm plugin is enabled: `GET /api/plugins/vpn.wireguard`
   - Check plugin routes: `GET /api/plugins/vpn.wireguard/routes`
   - Verify authentication headers

4. **Configuration Issues**
   - Validate IP address formats
   - Check network range conflicts
   - Ensure unique interface names

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("firewallo.plugins").setLevel(logging.DEBUG)
```

### Plugin Health Check

```bash
# Check overall plugin health
curl http://localhost:8000/api/plugins/vpn.wireguard/health

# Get detailed plugin metrics
curl http://localhost:8000/api/plugins/stats
```

## Benefits of the New System

1. **🔒 Enhanced Security**: Comprehensive validation and sandboxing
2. **🚀 Better Performance**: Optimized data access and caching
3. **🔧 Easier Maintenance**: Modular architecture and clear interfaces
4. **📈 Scalability**: Support for multiple VPN technologies
5. **🎯 Developer Friendly**: Rich APIs and development tools
6. **🔄 Hot Reloading**: Update plugins without downtime
7. **📊 Monitoring**: Built-in health checks and metrics
8. **🛡️ Robustness**: Better error handling and recovery

## Future Roadmap

- **Additional VPN Plugins**: OpenVPN, IPSec, SSTP
- **Advanced Monitoring**: Real-time traffic analysis
- **Load Balancing**: Multi-server configurations
- **Mobile Apps**: Native mobile clients
- **Enterprise Features**: LDAP integration, advanced RBAC
- **API Gateway**: Plugin-based API routing and middleware

## Support

For issues or questions regarding the plugin framework:

1. Check the [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)
2. Review the [API Documentation](http://localhost:8000/docs)
3. Submit issues to the GitHub repository
4. Join the community Discord for real-time support

---

**Note**: This migration maintains backward compatibility for existing configurations while providing a path to migrate to the new plugin-based system. The legacy API endpoints will continue to work through compatibility shims until the next major version.