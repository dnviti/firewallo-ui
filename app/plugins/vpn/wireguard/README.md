# WireGuard VPN Plugin

A complete, self-contained WireGuard VPN plugin for the Firewallo Plugin Framework. This plugin provides modern, fast, and secure VPN functionality using the WireGuard protocol.

## Overview

This plugin is **completely isolated and self-contained** - it includes all necessary services, utilities, validation, and API endpoints within itself. The main application automatically discovers and integrates this plugin without requiring any modifications to the core codebase.

## Features

### 🔐 **Core VPN Functionality**
- **Server Management**: Create, configure, and manage WireGuard servers
- **Client Management**: Generate and manage VPN clients with automatic key generation
- **IP Allocation**: Intelligent IP address allocation within server networks
- **Configuration Generation**: Automatic WireGuard configuration file generation
- **QR Code Support**: Generate QR codes for easy mobile client setup

### 🛡️ **Security & Validation**
- **Cryptographic Key Management**: Secure X25519 key generation and validation
- **Input Validation**: Comprehensive validation of IP addresses, networks, and configurations
- **Access Control**: Integration with Firewallo's authentication system
- **Configuration Security**: Validates all WireGuard parameters

### 📊 **Monitoring & Management**
- **Real-time Status**: Monitor connection status and statistics
- **Health Checks**: Plugin and server health monitoring
- **Traffic Statistics**: Track data transfer and connection metrics
- **System Integration**: Native WireGuard tools integration

### 🔄 **Advanced Features**
- **Hot Reloading**: Update plugin without application restart
- **Backup/Restore**: Configuration backup and restore capabilities
- **Bulk Operations**: Manage multiple clients simultaneously
- **Legacy Compatibility**: Support for existing WireGuard configurations

## Plugin Architecture

```
app/plugins/vpn/wireguard/
├── __init__.py          # Plugin exports and metadata
├── plugin.py            # Main plugin implementation
├── services.py          # All WireGuard services and utilities
├── manifest.json        # Plugin metadata and dependencies
├── README.md           # This documentation
└── [future files]       # Screenshots, additional docs, etc.
```

### Self-Contained Services

All functionality is contained within the plugin:

- **KeyGenerationService**: Cryptographic key generation and validation
- **IPAllocationService**: IP address allocation and network management
- **ValidationService**: Input validation and security checks
- **WireGuardConfigRenderer**: Configuration file generation
- **QRCodeService**: QR code generation for mobile clients
- **WireGuardSystemService**: System integration and WireGuard tools interface
- **WireGuardRepository**: Data access and persistence

## Installation & Setup

### Prerequisites

1. **System Dependencies**:
   ```bash
   # Ubuntu/Debian
   sudo apt install wireguard-tools iptables
   
   # CentOS/RHEL
   sudo dnf install wireguard-tools iptables
   ```

2. **Python Dependencies** (automatically installed):
   - `cryptography>=3.0.0`
   - `qrcode>=7.0.0`
   - `pillow>=8.0.0`

### Automatic Discovery

The plugin is automatically discovered and loaded by the Firewallo Plugin Framework:

1. **Discovery**: Framework scans `app/plugins/vpn/wireguard/`
2. **Validation**: Security and dependency validation
3. **Loading**: Plugin class instantiation and initialization
4. **Registration**: API routes automatically registered
5. **Integration**: Available via `/api/vpn/wireguard/` endpoints

## API Endpoints

The plugin provides a comprehensive REST API:

### Server Management

```http
GET    /api/vpn/wireguard/servers              # List all servers
POST   /api/vpn/wireguard/servers              # Create new server
GET    /api/vpn/wireguard/servers/{id}         # Get specific server
PUT    /api/vpn/wireguard/servers/{id}         # Update server
DELETE /api/vpn/wireguard/servers/{id}         # Delete server

POST   /api/vpn/wireguard/servers/{id}/start   # Start server
POST   /api/vpn/wireguard/servers/{id}/stop    # Stop server
POST   /api/vpn/wireguard/servers/{id}/restart # Restart server
GET    /api/vpn/wireguard/servers/{id}/status  # Get server status
GET    /api/vpn/wireguard/servers/{id}/statistics # Get server stats
```

### Client Management

```http
GET    /api/vpn/wireguard/clients              # List all clients
POST   /api/vpn/wireguard/clients              # Create new client
GET    /api/vpn/wireguard/clients/{id}         # Get specific client
PUT    /api/vpn/wireguard/clients/{id}         # Update client
DELETE /api/vpn/wireguard/clients/{id}         # Delete client

POST   /api/vpn/wireguard/clients/{id}/enable  # Enable client
POST   /api/vpn/wireguard/clients/{id}/disable # Disable client
POST   /api/vpn/wireguard/clients/{id}/revoke  # Revoke client access
GET    /api/vpn/wireguard/clients/{id}/status  # Get client status
```

### Configuration & Files

```http
GET    /api/vpn/wireguard/clients/{id}/config  # Get client config + QR code
POST   /api/vpn/wireguard/clients/{id}/persist # Download client config file
POST   /api/vpn/wireguard/servers/{id}/persist # Download server config file
```

### Utilities

```http
GET    /api/vpn/wireguard/next_ip             # Get next available IP
GET    /api/vpn/wireguard/info                # Plugin information
GET    /api/vpn/wireguard/health              # Plugin health status
GET    /api/vpn/wireguard/routes              # List all plugin routes
```

## Usage Examples

### Creating a Server

```bash
curl -X POST http://localhost:8000/api/vpn/wireguard/servers \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "main-server",
    "endpoint": "vpn.example.com",
    "port": 51820,
    "network": "10.0.0.0/24",
    "dns_servers": ["8.8.8.8", "8.8.4.4"],
    "mtu": 1420,
    "enabled": true,
    "description": "Main VPN server"
  }'
```

### Creating a Client

```bash
curl -X POST http://localhost:8000/api/vpn/wireguard/clients \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "john-laptop",
    "server_id": "<server-uuid>",
    "email": "john@example.com",
    "allowed_ips": ["0.0.0.0/0"],
    "persistent_keepalive": 25,
    "enabled": true,
    "description": "John'\''s laptop"
  }'
```

### Getting Client Configuration

```bash
# Get config with QR code (JSON)
curl http://localhost:8000/api/vpn/wireguard/clients/<client-id>/config \
  -H "Authorization: Bearer <token>"

# Download config file
curl http://localhost:8000/api/vpn/wireguard/clients/<client-id>/persist \
  -H "Authorization: Bearer <token>" \
  -o client.conf
```

## Configuration

### Plugin Configuration

The plugin can be configured via its configuration system:

```python
# Default configuration
{
  "interface_name": "wg0",
  "listen_port": 51820,
  "network_range": "10.0.0.0/24",
  "dns_servers": ["8.8.8.8", "8.8.4.4"],
  "mtu": 1420,
  "keep_alive": 25,
  "save_config": True,
  "table": "auto"
}
```

### Server Configuration

```json
{
  "name": "wg0",                    // Interface name
  "endpoint": "vpn.example.com",    // Public endpoint
  "port": 51820,                   // Listen port
  "network": "10.0.0.0/24",        // VPN network
  "dns_servers": ["8.8.8.8"],      // DNS servers
  "mtu": 1420,                     // MTU size
  "keep_alive": 25,                // Keep alive interval
  "enabled": true,                 // Server enabled
  "description": "Main server"      // Description
}
```

### Client Configuration

```json
{
  "name": "client1",               // Client name
  "server_id": "uuid",             // Server UUID
  "email": "user@example.com",     // User email
  "allowed_ips": ["0.0.0.0/0"],    // Allowed IP ranges
  "dns_servers": ["8.8.8.8"],      // DNS servers (optional)
  "persistent_keepalive": 25,      // Keep alive
  "enabled": true,                 // Client enabled
  "description": "User device"     // Description
}
```

## Integration with Main Application

### Automatic Integration

The plugin integrates seamlessly with the main application:

1. **Route Registration**: All plugin routes are automatically registered under `/api/vpn/wireguard/`
2. **Authentication**: Uses existing Firewallo authentication system
3. **Database**: Stores data in plugin-specific namespace
4. **Logging**: Integrated with application logging system
5. **Health Monitoring**: Plugin health tracked by framework

### Plugin Management

```bash
# Check plugin status
curl http://localhost:8000/api/plugins/vpn.wireguard

# Plugin health
curl http://localhost:8000/api/plugins/vpn.wireguard/health

# Disable plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/disable

# Enable plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/enable

# Reload plugin
curl -X POST http://localhost:8000/api/plugins/vpn.wireguard/reload
```

## Security

### Key Management

- **X25519 Keys**: Modern elliptic curve cryptography
- **Automatic Generation**: Secure random key generation
- **Key Validation**: Cryptographic key format validation
- **Preshared Keys**: Additional layer of security

### Network Security

- **IP Validation**: Comprehensive IP address and network validation
- **Access Control**: Integration with authentication system
- **Configuration Validation**: All parameters validated before use
- **System Integration**: Secure WireGuard tools integration

### Plugin Security

- **Code Analysis**: Plugin code analyzed for security issues
- **Permission System**: Granular permission controls
- **Input Sanitization**: All inputs validated and sanitized
- **Error Handling**: Secure error handling without information leakage

## Monitoring & Troubleshooting

### Health Checks

```bash
# Plugin health
GET /api/vpn/wireguard/health

# Server status
GET /api/vpn/wireguard/servers/{id}/status

# Client status
GET /api/vpn/wireguard/clients/{id}/status
```

### Logs

Plugin logs are integrated with the main application logging:

```bash
# View plugin logs
docker logs firewallo-ui | grep "wireguard"

# Debug mode
# Set log level to DEBUG in application configuration
```

### Common Issues

1. **WireGuard Tools Not Found**
   ```bash
   # Install WireGuard tools
   sudo apt install wireguard-tools  # Ubuntu/Debian
   sudo dnf install wireguard-tools  # CentOS/RHEL
   ```

2. **Permission Denied**
   - Ensure application has permission to manage network interfaces
   - Check iptables permissions for firewall rules

3. **Port Already in Use**
   - Change the listen port in server configuration
   - Check for conflicting services on the same port

4. **Client Connection Issues**
   - Verify endpoint is accessible from client
   - Check firewall rules allow WireGuard port
   - Validate client configuration format

## Development

### Extending the Plugin

The plugin is designed to be easily extensible:

1. **Add New Services**: Create new services in `services.py`
2. **Add New Routes**: Extend the `_setup_routes()` method
3. **Add New Validation**: Extend `ValidationService`
4. **Add New Features**: Implement in main plugin class

### Testing

```bash
# Run plugin tests
python test_plugins.py

# Test specific functionality
curl http://localhost:8000/api/vpn/wireguard/info
```

### Custom Configuration

Modify the plugin configuration via the API:

```bash
curl -X PUT http://localhost:8000/api/plugins/vpn.wireguard/config \
  -H "Content-Type: application/json" \
  -d '{"interface_name": "wg1", "listen_port": 51821}'
```

## License

This plugin is part of the Firewallo project and is licensed under the MIT License.

## Support

- **Documentation**: See `/documentation/PLUGIN_DEVELOPMENT.md`
- **API Docs**: Available at `http://localhost:8000/docs`
- **Issues**: Submit to the main Firewallo repository
- **Community**: Join the Firewallo community Discord

---

**Note**: This plugin demonstrates the Firewallo Plugin Framework's capability to create completely isolated, self-contained functionality that integrates seamlessly with the main application without requiring any modifications to the core codebase.