# Firewallo Plugin Framework

The Firewallo Plugin Framework provides a robust, extensible architecture that allows developers to create and integrate custom plugins seamlessly. This framework supports multiple plugin categories including VPN technologies, network tools, monitoring solutions, and security features.

## Overview

Firewallo's plugin system is designed around a modular architecture that promotes:

- **Standardized Interfaces** - Common base classes and protocols for consistency
- **Isolation** - Plugins operate in isolated namespaces with controlled interactions
- **Hot-loading** - Dynamic plugin loading without application restarts
- **Dependency Management** - Automatic handling of plugin dependencies
- **Validation** - Schema validation and security checks for all plugins
- **Extensibility** - Support for multiple plugin categories and types

## Plugin Architecture

### Core Components

```
app/plugins/
├── __init__.py                 # Plugin registry and loader
├── base/                       # Base classes and interfaces
│   ├── __init__.py
│   ├── plugin.py              # Base plugin class
│   ├── interfaces.py          # Common interfaces
│   └── exceptions.py          # Plugin-specific exceptions
├── registry/                   # Plugin management
│   ├── __init__.py
│   ├── manager.py             # Plugin manager
│   ├── loader.py              # Dynamic plugin loader
│   └── validator.py           # Plugin validation
├── categories/                 # Plugin category definitions
│   ├── __init__.py
│   ├── vpn.py                 # VPN plugin interface
│   ├── firewall.py            # Firewall plugin interface
│   ├── monitoring.py          # Monitoring plugin interface
│   └── network.py             # Network tools interface
└── <plugin_category>/          # Individual plugin implementations
    └── <plugin_name>/
        ├── __init__.py
        ├── plugin.py          # Main plugin implementation
        ├── schemas.py         # Data schemas
        ├── repository.py      # Data access layer
        ├── services.py        # Business logic
        └── manifest.json      # Plugin metadata
```

### Database Integration

Plugins integrate with Firewallo's modular database structure:

```json
{
  "plugins": {
    "<category>": {
      "<plugin_name>": {
        "config": {},
        "data": {},
        "state": {}
      }
    }
  }
}
```

## Plugin Categories

### VPN Plugins (`plugins.vpn.*`)
- **Purpose**: VPN server and client management
- **Examples**: WireGuard, OpenVPN, IPSec, SSTP
- **Data Structure**: Servers, peers, tunnels, certificates

### Firewall Plugins (`plugins.firewall.*`)
- **Purpose**: Firewall rule management and configuration
- **Examples**: iptables, nftables, ufw, pfSense
- **Data Structure**: Rules, chains, policies, zones

### Monitoring Plugins (`plugins.monitoring.*`)
- **Purpose**: System and network monitoring
- **Examples**: Prometheus, Grafana, Zabbix, SNMP
- **Data Structure**: Metrics, alerts, dashboards, targets

### Network Tools (`plugins.network.*`)
- **Purpose**: Network utilities and management
- **Examples**: DNS, DHCP, Load Balancer, Proxy
- **Data Structure**: Configurations, pools, rules, endpoints

### Security Plugins (`plugins.security.*`)
- **Purpose**: Security tools and intrusion detection
- **Examples**: IDS/IPS, Certificate Management, 2FA
- **Data Structure**: Policies, certificates, tokens, logs

## Plugin Development Guide

### 1. Plugin Structure

Every plugin must follow this structure:

```python
# app/plugins/<category>/<plugin_name>/plugin.py
from app.plugins.base import BasePlugin
from app.plugins.categories.vpn import VPNPluginInterface

class MyVPNPlugin(BasePlugin, VPNPluginInterface):
    """Example VPN plugin implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "myvpn"
        self.category = "vpn"
        self.version = "1.0.0"
        self.description = "Custom VPN implementation"
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        # Setup plugin-specific resources
        return True
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def get_api_routes(self) -> list:
        """Return FastAPI router for this plugin."""
        from .routes import router
        return [router]
    
    def get_database_schema(self) -> dict:
        """Return database schema for this plugin."""
        return {
            "servers": [],
            "clients": [],
            "config": {}
        }
```

### 2. Plugin Manifest

Each plugin requires a `manifest.json` file:

```json
{
  "name": "myvpn",
  "display_name": "My Custom VPN",
  "category": "vpn",
  "version": "1.0.0",
  "description": "A custom VPN implementation",
  "author": "Developer Name",
  "email": "developer@example.com",
  "license": "MIT",
  "repository": "https://github.com/developer/myvpn-plugin",
  "dependencies": {
    "python": ">=3.11",
    "packages": [
      "cryptography>=3.0.0",
      "pynacl>=1.4.0"
    ],
    "system": [
      "openssl"
    ]
  },
  "permissions": [
    "network.create",
    "network.modify",
    "system.execute"
  ],
  "configuration": {
    "required": [
      "server_endpoint",
      "encryption_method"
    ],
    "optional": [
      "custom_port",
      "log_level"
    ]
  },
  "api_prefix": "/api/vpn/myvpn",
  "database_path": "plugins.vpn.myvpn",
  "supports_hot_reload": true,
  "min_firewallo_version": "1.0.0"
}
```

### 3. Base Plugin Class

```python
# app/plugins/base/plugin.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from fastapi import APIRouter

class BasePlugin(ABC):
    """Base class for all Firewallo plugins."""
    
    def __init__(self):
        self.name: str = ""
        self.category: str = ""
        self.version: str = ""
        self.description: str = ""
        self.enabled: bool = True
        self.config: Dict[str, Any] = {}
        self.logger = None
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    @abstractmethod
    def get_api_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this plugin."""
        pass
    
    @abstractmethod
    def get_database_schema(self) -> Dict[str, Any]:
        """Return the database schema for this plugin."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return plugin health information."""
        return {
            "name": self.name,
            "status": "healthy" if self.enabled else "disabled",
            "version": self.version
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return plugin metrics."""
        return {}
```

### 4. Category Interfaces

```python
# app/plugins/categories/vpn.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VPNPluginInterface(ABC):
    """Interface for VPN plugins."""
    
    @abstractmethod
    async def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN server."""
        pass
    
    @abstractmethod
    async def delete_server(self, server_id: str) -> bool:
        """Delete a VPN server."""
        pass
    
    @abstractmethod
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all VPN servers."""
        pass
    
    @abstractmethod
    async def create_client(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN client."""
        pass
    
    @abstractmethod
    async def generate_config(self, client_id: str) -> str:
        """Generate client configuration file."""
        pass
    
    @abstractmethod
    async def get_connection_status(self, client_id: str) -> Dict[str, Any]:
        """Get client connection status."""
        pass
```

## Plugin Manager

### Core Functionality

```python
# app/plugins/registry/manager.py
import importlib
import json
import os
from typing import Dict, List, Optional, Type
from app.plugins.base import BasePlugin

class PluginManager:
    """Manages plugin lifecycle and registration."""
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, dict] = {}
        self.enabled_plugins: set = set()
    
    async def discover_plugins(self, plugin_dir: str = "app/plugins") -> List[str]:
        """Discover available plugins in the plugin directory."""
        discovered = []
        
        for category in os.listdir(plugin_dir):
            category_path = os.path.join(plugin_dir, category)
            if not os.path.isdir(category_path) or category.startswith('_'):
                continue
                
            for plugin_name in os.listdir(category_path):
                plugin_path = os.path.join(category_path, plugin_name)
                manifest_path = os.path.join(plugin_path, "manifest.json")
                
                if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                    discovered.append(f"{category}.{plugin_name}")
        
        return discovered
    
    async def load_plugin(self, plugin_path: str) -> bool:
        """Load a specific plugin."""
        try:
            # Load manifest
            manifest = self._load_manifest(plugin_path)
            if not manifest:
                return False
            
            # Import plugin module
            module_path = f"app.plugins.{plugin_path}.plugin"
            module = importlib.import_module(module_path)
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                return False
            
            # Instantiate plugin
            plugin = plugin_class()
            
            # Validate and initialize
            if await self._validate_plugin(plugin, manifest):
                await plugin.initialize()
                self.plugins[plugin_path] = plugin
                self.plugin_configs[plugin_path] = manifest
                return True
                
        except Exception as e:
            print(f"Failed to load plugin {plugin_path}: {e}")
            
        return False
    
    async def unload_plugin(self, plugin_path: str) -> bool:
        """Unload a specific plugin."""
        if plugin_path in self.plugins:
            try:
                await self.plugins[plugin_path].shutdown()
                del self.plugins[plugin_path]
                del self.plugin_configs[plugin_path]
                self.enabled_plugins.discard(plugin_path)
                return True
            except Exception as e:
                print(f"Failed to unload plugin {plugin_path}: {e}")
        return False
    
    async def enable_plugin(self, plugin_path: str) -> bool:
        """Enable a loaded plugin."""
        if plugin_path in self.plugins:
            self.plugins[plugin_path].enabled = True
            self.enabled_plugins.add(plugin_path)
            return True
        return False
    
    async def disable_plugin(self, plugin_path: str) -> bool:
        """Disable a loaded plugin."""
        if plugin_path in self.plugins:
            self.plugins[plugin_path].enabled = False
            self.enabled_plugins.discard(plugin_path)
            return True
        return False
    
    def get_enabled_plugins(self, category: Optional[str] = None) -> List[BasePlugin]:
        """Get all enabled plugins, optionally filtered by category."""
        enabled = []
        for path, plugin in self.plugins.items():
            if plugin.enabled and path in self.enabled_plugins:
                if not category or plugin.category == category:
                    enabled.append(plugin)
        return enabled
    
    def get_plugin_routes(self) -> List:
        """Get API routes from all enabled plugins."""
        routes = []
        for plugin in self.get_enabled_plugins():
            routes.extend(plugin.get_api_routes())
        return routes
    
    def _load_manifest(self, plugin_path: str) -> Optional[dict]:
        """Load plugin manifest file."""
        try:
            manifest_file = f"app/plugins/{plugin_path.replace('.', '/')}/manifest.json"
            with open(manifest_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """Find the plugin class in the module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, BasePlugin) and 
                attr != BasePlugin):
                return attr
        return None
    
    async def _validate_plugin(self, plugin: BasePlugin, manifest: dict) -> bool:
        """Validate plugin against its manifest."""
        # Validate required fields
        required_fields = ['name', 'category', 'version']
        for field in required_fields:
            if not hasattr(plugin, field) or not getattr(plugin, field):
                return False
        
        # Validate manifest consistency
        if plugin.name != manifest.get('name'):
            return False
        
        if plugin.category != manifest.get('category'):
            return False
        
        # Additional validation logic
        return True

# Global plugin manager instance
plugin_manager = PluginManager()
```

## Plugin Installation

### From Git Repository

```bash
# Install plugin from Git repository
firewallo plugin install https://github.com/developer/myvpn-plugin.git

# Install specific version
firewallo plugin install https://github.com/developer/myvpn-plugin.git@v1.2.0

# Install from local directory
firewallo plugin install ./local-plugin/
```

### From Plugin Package

```bash
# Install from .tar.gz package
firewallo plugin install myvpn-plugin-1.0.0.tar.gz

# Install from URL
firewallo plugin install https://releases.example.com/myvpn-plugin-1.0.0.tar.gz
```

### Plugin CLI Commands

```bash
# List available plugins
firewallo plugin list

# Show plugin information
firewallo plugin info wireguard

# Enable/disable plugin
firewallo plugin enable myvpn
firewallo plugin disable myvpn

# Update plugin
firewallo plugin update myvpn

# Remove plugin
firewallo plugin remove myvpn

# Validate plugin
firewallo plugin validate ./my-plugin/
```

## Configuration Management

### Plugin Configuration

```python
# app/plugins/registry/config.py
class PluginConfig:
    """Plugin configuration management."""
    
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.config_path = f"plugins.{plugin_name}.config"
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        from app.plugins.wireguard.repository import repo
        config = repo.get_plugin_config(self.plugin_name)
        return config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value."""
        from app.plugins.wireguard.repository import repo
        repo.set_plugin_config(self.plugin_name, key, value)
    
    def update(self, config_dict: dict):
        """Update multiple configuration values."""
        from app.plugins.wireguard.repository import repo
        repo.update_plugin_config(self.plugin_name, config_dict)
```

### Environment Variables

Plugins can access environment variables with the `FIREWALLO_PLUGIN_` prefix:

```bash
# Plugin-specific configuration
export FIREWALLO_PLUGIN_MYVPN_SERVER_PORT=8080
export FIREWALLO_PLUGIN_MYVPN_DEBUG=true
export FIREWALLO_PLUGIN_MYVPN_API_KEY=secret123
```

## Security Considerations

### Plugin Validation

```python
# app/plugins/registry/validator.py
class PluginValidator:
    """Security validation for plugins."""
    
    def validate_manifest(self, manifest: dict) -> bool:
        """Validate plugin manifest for security issues."""
        # Check required fields
        required = ['name', 'category', 'version', 'author']
        if not all(field in manifest for field in required):
            return False
        
        # Validate permissions
        permissions = manifest.get('permissions', [])
        if not self._validate_permissions(permissions):
            return False
        
        # Check dependencies
        dependencies = manifest.get('dependencies', {})
        if not self._validate_dependencies(dependencies):
            return False
        
        return True
    
    def _validate_permissions(self, permissions: list) -> bool:
        """Validate requested permissions."""
        allowed_permissions = {
            'network.create', 'network.modify', 'network.read',
            'file.read', 'file.write',
            'system.execute', 'system.read',
            'database.read', 'database.write'
        }
        
        return all(perm in allowed_permissions for perm in permissions)
    
    def _validate_dependencies(self, dependencies: dict) -> bool:
        """Validate plugin dependencies."""
        # Check Python version
        python_version = dependencies.get('python', '>=3.11')
        # Validate version format
        
        # Check package dependencies
        packages = dependencies.get('packages', [])
        for package in packages:
            if not self._is_safe_package(package):
                return False
        
        return True
    
    def _is_safe_package(self, package: str) -> bool:
        """Check if package is safe to install."""
        # Implement package safety checks
        # Check against known malicious packages
        # Validate package names and versions
        return True
```

### Permission System

```python
# app/plugins/base/permissions.py
class PluginPermissions:
    """Plugin permission management."""
    
    NETWORK_CREATE = "network.create"
    NETWORK_MODIFY = "network.modify"
    NETWORK_READ = "network.read"
    
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    
    SYSTEM_EXECUTE = "system.execute"
    SYSTEM_READ = "system.read"
    
    DATABASE_READ = "database.read"
    DATABASE_WRITE = "database.write"
    
    def __init__(self, plugin_name: str, granted_permissions: list):
        self.plugin_name = plugin_name
        self.granted_permissions = set(granted_permissions)
    
    def has_permission(self, permission: str) -> bool:
        """Check if plugin has specific permission."""
        return permission in self.granted_permissions
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.has_permission(permission):
                    raise PermissionError(f"Plugin {self.plugin_name} lacks permission: {permission}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

## Testing Framework

### Plugin Testing

```python
# app/plugins/testing/base.py
import pytest
from app.plugins.base import BasePlugin
from app.plugins.registry.manager import PluginManager

class PluginTestCase:
    """Base class for plugin testing."""
    
    def setup_method(self):
        """Setup test environment."""
        self.plugin_manager = PluginManager()
        self.plugin = None
    
    def teardown_method(self):
        """Cleanup after test."""
        if self.plugin:
            self.plugin.shutdown()
    
    async def load_test_plugin(self, plugin_path: str):
        """Load plugin for testing."""
        success = await self.plugin_manager.load_plugin(plugin_path)
        assert success, f"Failed to load plugin: {plugin_path}"
        self.plugin = self.plugin_manager.plugins[plugin_path]
        return self.plugin
    
    def assert_plugin_valid(self, plugin: BasePlugin):
        """Assert plugin meets basic requirements."""
        assert plugin.name, "Plugin must have a name"
        assert plugin.category, "Plugin must have a category"
        assert plugin.version, "Plugin must have a version"
        assert hasattr(plugin, 'initialize'), "Plugin must implement initialize()"
        assert hasattr(plugin, 'shutdown'), "Plugin must implement shutdown()"
```

### Example Test

```python
# tests/plugins/test_myvpn.py
import pytest
from app.plugins.testing.base import PluginTestCase

class TestMyVPNPlugin(PluginTestCase):
    """Test MyVPN plugin."""
    
    @pytest.mark.asyncio
    async def test_plugin_loads(self):
        """Test plugin loads successfully."""
        plugin = await self.load_test_plugin("vpn.myvpn")
        self.assert_plugin_valid(plugin)
        assert plugin.category == "vpn"
    
    @pytest.mark.asyncio
    async def test_create_server(self):
        """Test server creation."""
        plugin = await self.load_test_plugin("vpn.myvpn")
        
        config = {
            "name": "test-server",
            "port": 8080,
            "protocol": "tcp"
        }
        
        result = await plugin.create_server(config)
        assert result['success'] == True
        assert 'server_id' in result
```

## Best Practices

### 1. Plugin Development

- **Follow naming conventions**: Use lowercase with underscores
- **Implement proper error handling**: Use try-catch blocks and meaningful error messages
- **Document your plugin**: Include comprehensive docstrings and README
- **Test thoroughly**: Write unit tests and integration tests
- **Handle dependencies gracefully**: Check for required system tools and packages

### 2. Database Integration

- **Use the repository pattern**: Abstract database operations
- **Maintain schema consistency**: Follow the established database structure
- **Handle migrations**: Provide upgrade/downgrade scripts
- **Validate data**: Use Pydantic schemas for data validation

### 3. API Design

- **Follow REST principles**: Use appropriate HTTP methods and status codes
- **Implement proper authentication**: Use the existing auth system
- **Document endpoints**: Use FastAPI's automatic documentation features
- **Handle rate limiting**: Implement appropriate rate limiting for API endpoints

### 4. Security

- **Validate all inputs**: Never trust user input
- **Use parameterized queries**: Prevent SQL injection
- **Implement proper permissions**: Request only necessary permissions
- **Secure sensitive data**: Use encryption for passwords and keys

## Plugin Examples

For complete examples and templates, see:

- [WireGuard Plugin](PLUGIN_EXAMPLES.md#wireguard) - Complete VPN plugin implementation
- [Monitoring Plugin](PLUGIN_EXAMPLES.md#monitoring) - System monitoring plugin
- [Firewall Plugin](PLUGIN_EXAMPLES.md#firewall) - iptables management plugin

## Migration Guide

### From Legacy System

If you have an existing system that you want to convert to a Firewallo plugin:

1. **Analyze your current architecture**
2. **Identify the appropriate plugin category**
3. **Create the plugin structure**
4. **Implement the required interfaces**
5. **Migrate your data to the plugin database schema**
6. **Test thoroughly**

For detailed migration instructions, see [PLUGIN_MIGRATION.md](PLUGIN_MIGRATION.md).

---

The Firewallo Plugin Framework provides a powerful foundation for extending the platform's capabilities. By following this guide, developers can create robust, secure, and maintainable plugins that integrate seamlessly with the Firewallo ecosystem.
