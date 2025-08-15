# Plugin Development Guide

This guide provides step-by-step instructions for developing plugins for the Firewallo platform. Whether you're creating a new VPN implementation, monitoring solution, or network tool, this guide will help you build robust, secure plugins.

## Quick Start

### 1. Setup Development Environment

```bash
# Clone Firewallo repository
git clone <firewallo-repo-url>
cd firewallo-ui

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio black isort mypy
```

### 2. Create Plugin Structure

```bash
# Create plugin directory structure
mkdir -p app/plugins/vpn/myvpn
cd app/plugins/vpn/myvpn

# Create required files
touch __init__.py
touch plugin.py
touch manifest.json
touch schemas.py
touch repository.py
touch routes.py
touch services.py
```

### 3. Implement Basic Plugin

```python
# app/plugins/vpn/myvpn/plugin.py
from app.plugins.base.plugin import BasePlugin
from app.plugins.categories.vpn import VPNPluginInterface
from fastapi import APIRouter
from typing import Dict, List, Any

class MyVPNPlugin(BasePlugin, VPNPluginInterface):
    """Example VPN plugin implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "myvpn"
        self.category = "vpn"
        self.version = "1.0.0"
        self.description = "My Custom VPN Plugin"
        self.author = "Developer Name"
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        # Initialize plugin resources
        self.logger.info(f"Initializing {self.name} plugin")
        return True
    
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""
        self.logger.info(f"Shutting down {self.name} plugin")
    
    def get_api_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this plugin."""
        from .routes import router
        return [router]
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema for this plugin."""
        return {
            "servers": [],
            "clients": [],
            "config": {
                "encryption": "aes256",
                "protocol": "udp",
                "port": 1194
            }
        }
    
    # VPN Interface Implementation
    async def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN server."""
        # Implementation here
        return {"server_id": "srv_001", "status": "created"}
    
    async def delete_server(self, server_id: str) -> bool:
        """Delete a VPN server."""
        # Implementation here
        return True
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all VPN servers."""
        # Implementation here
        return []
    
    async def create_client(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN client."""
        # Implementation here
        return {"client_id": "cli_001", "status": "created"}
    
    async def generate_config(self, client_id: str) -> str:
        """Generate client configuration file."""
        # Implementation here
        return "# VPN Configuration\n"
    
    async def get_connection_status(self, client_id: str) -> Dict[str, Any]:
        """Get client connection status."""
        # Implementation here
        return {"status": "connected", "uptime": "1h 23m"}
```

### 4. Create Plugin Manifest

```json
{
  "name": "myvpn",
  "display_name": "My Custom VPN",
  "category": "vpn",
  "version": "1.0.0",
  "description": "A custom VPN implementation for Firewallo",
  "author": "Developer Name",
  "email": "developer@example.com",
  "license": "MIT",
  "repository": "https://github.com/developer/myvpn-plugin",
  "homepage": "https://myvpn.example.com",
  "documentation": "https://docs.myvpn.example.com",
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
    "network.read",
    "file.write",
    "system.execute"
  ],
  "configuration": {
    "required": [
      "server_endpoint",
      "encryption_method"
    ],
    "optional": [
      "custom_port",
      "log_level",
      "max_clients"
    ]
  },
  "api_prefix": "/api/vpn/myvpn",
  "database_path": "plugins.vpn.myvpn",
  "supports_hot_reload": true,
  "min_firewallo_version": "1.0.0",
  "max_firewallo_version": "2.0.0",
  "tags": ["vpn", "custom", "encryption"],
  "icon": "data:image/svg+xml;base64,PHN2Zy4uLg==",
  "screenshots": [
    "https://example.com/screenshot1.png",
    "https://example.com/screenshot2.png"
  ]
}
```

## Plugin Categories in Detail

### VPN Plugins

VPN plugins implement the `VPNPluginInterface` and provide:

```python
# app/plugins/categories/vpn.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VPNPluginInterface(ABC):
    """Interface for VPN plugins."""
    
    @abstractmethod
    async def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN server with the given configuration."""
        pass
    
    @abstractmethod
    async def delete_server(self, server_id: str) -> bool:
        """Delete the specified VPN server."""
        pass
    
    @abstractmethod
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all VPN servers managed by this plugin."""
        pass
    
    @abstractmethod
    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific server."""
        pass
    
    @abstractmethod
    async def update_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update server configuration."""
        pass
    
    @abstractmethod
    async def create_client(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a VPN client for the specified server."""
        pass
    
    @abstractmethod
    async def delete_client(self, client_id: str) -> bool:
        """Delete the specified VPN client."""
        pass
    
    @abstractmethod
    async def list_clients(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List VPN clients, optionally filtered by server."""
        pass
    
    @abstractmethod
    async def generate_config(self, client_id: str) -> str:
        """Generate client configuration file."""
        pass
    
    @abstractmethod
    async def get_connection_status(self, client_id: str) -> Dict[str, Any]:
        """Get client connection status and statistics."""
        pass
    
    @abstractmethod
    async def revoke_client(self, client_id: str) -> bool:
        """Revoke client access."""
        pass
```

### Firewall Plugins

```python
# app/plugins/categories/firewall.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class FirewallPluginInterface(ABC):
    """Interface for firewall plugins."""
    
    @abstractmethod
    async def create_rule(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a firewall rule."""
        pass
    
    @abstractmethod
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a firewall rule."""
        pass
    
    @abstractmethod
    async def list_rules(self, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List firewall rules."""
        pass
    
    @abstractmethod
    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a firewall rule."""
        pass
    
    @abstractmethod
    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a firewall rule."""
        pass
    
    @abstractmethod
    async def backup_config(self) -> str:
        """Backup current firewall configuration."""
        pass
    
    @abstractmethod
    async def restore_config(self, backup_data: str) -> bool:
        """Restore firewall configuration from backup."""
        pass
```

### Monitoring Plugins

```python
# app/plugins/categories/monitoring.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MonitoringPluginInterface(ABC):
    """Interface for monitoring plugins."""
    
    @abstractmethod
    async def create_monitor(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new monitor."""
        pass
    
    @abstractmethod
    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        pass
    
    @abstractmethod
    async def list_monitors(self) -> List[Dict[str, Any]]:
        """List all monitors."""
        pass
    
    @abstractmethod
    async def get_metrics(self, monitor_id: str, time_range: str) -> Dict[str, Any]:
        """Get metrics for a specific monitor."""
        pass
    
    @abstractmethod
    async def create_alert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule."""
        pass
    
    @abstractmethod
    async def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by status."""
        pass
```

## Data Management

### Repository Pattern

```python
# app/plugins/vpn/myvpn/repository.py
from typing import List, Dict, Any, Optional
from app.plugins.base.repository import BaseRepository

class MyVPNRepository(BaseRepository):
    """Repository for MyVPN plugin data."""
    
    def __init__(self):
        super().__init__()
        self.plugin_name = "myvpn"
        self.db_path = "plugins.vpn.myvpn"
    
    async def create_server(self, server_data: Dict[str, Any]) -> str:
        """Create a new VPN server."""
        servers = await self.get_data("servers")
        server_id = self.generate_id()
        
        server_record = {
            "id": server_id,
            "created_at": self.get_timestamp(),
            **server_data
        }
        
        servers.append(server_record)
        await self.set_data("servers", servers)
        return server_id
    
    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server by ID."""
        servers = await self.get_data("servers")
        for server in servers:
            if server["id"] == server_id:
                return server
        return None
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all servers."""
        return await self.get_data("servers")
    
    async def update_server(self, server_id: str, updates: Dict[str, Any]) -> bool:
        """Update server configuration."""
        servers = await self.get_data("servers")
        for i, server in enumerate(servers):
            if server["id"] == server_id:
                servers[i].update(updates)
                servers[i]["updated_at"] = self.get_timestamp()
                await self.set_data("servers", servers)
                return True
        return False
    
    async def delete_server(self, server_id: str) -> bool:
        """Delete server."""
        servers = await self.get_data("servers")
        original_length = len(servers)
        servers = [s for s in servers if s["id"] != server_id]
        
        if len(servers) < original_length:
            await self.set_data("servers", servers)
            return True
        return False
```

### Base Repository

```python
# app/plugins/base/repository.py
import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.db.connection import get_database

class BaseRepository:
    """Base repository class for plugin data access."""
    
    def __init__(self):
        self.plugin_name = ""
        self.db_path = ""
    
    async def get_data(self, key: str) -> Any:
        """Get data from plugin storage."""
        db = get_database()
        path = f"{self.db_path}.{key}"
        return await db.get(path, [])
    
    async def set_data(self, key: str, value: Any) -> None:
        """Set data in plugin storage."""
        db = get_database()
        path = f"{self.db_path}.{key}"
        await db.set(path, value)
    
    async def get_config(self, key: str, default=None) -> Any:
        """Get plugin configuration value."""
        config = await self.get_data("config")
        return config.get(key, default)
    
    async def set_config(self, key: str, value: Any) -> None:
        """Set plugin configuration value."""
        config = await self.get_data("config")
        config[key] = value
        await self.set_data("config", config)
    
    def generate_id(self) -> str:
        """Generate unique ID."""
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()
```

## API Routes

### FastAPI Integration

```python
# app/plugins/vpn/myvpn/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.auth.models import current_active_user
from app.plugins.wireguard.repository import UserDoc
from .repository import MyVPNRepository
from .schemas import ServerCreate, ServerResponse, ClientCreate, ClientResponse

router = APIRouter(prefix="/vpn/myvpn", tags=["MyVPN"])
repo = MyVPNRepository()

@router.post("/servers", response_model=ServerResponse)
async def create_server(
    server_data: ServerCreate,
    user: UserDoc = Depends(current_active_user)
):
    """Create a new VPN server."""
    try:
        server_id = await repo.create_server(server_data.dict())
        server = await repo.get_server(server_id)
        return ServerResponse(**server)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/servers", response_model=List[ServerResponse])
async def list_servers(user: UserDoc = Depends(current_active_user)):
    """List all VPN servers."""
    servers = await repo.list_servers()
    return [ServerResponse(**server) for server in servers]

@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: str,
    user: UserDoc = Depends(current_active_user)
):
    """Get server details."""
    server = await repo.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    return ServerResponse(**server)

@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: str,
    updates: ServerCreate,
    user: UserDoc = Depends(current_active_user)
):
    """Update server configuration."""
    success = await repo.update_server(server_id, updates.dict(exclude_unset=True))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    server = await repo.get_server(server_id)
    return ServerResponse(**server)

@router.delete("/servers/{server_id}")
async def delete_server(
    server_id: str,
    user: UserDoc = Depends(current_active_user)
):
    """Delete a VPN server."""
    success = await repo.delete_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    return {"message": "Server deleted successfully"}

@router.post("/servers/{server_id}/clients", response_model=ClientResponse)
async def create_client(
    server_id: str,
    client_data: ClientCreate,
    user: UserDoc = Depends(current_active_user)
):
    """Create a VPN client."""
    # Verify server exists
    server = await repo.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    try:
        client_id = await repo.create_client(server_id, client_data.dict())
        client = await repo.get_client(client_id)
        return ClientResponse(**client)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

## Web UI Management

### Overview

The Firewallo Plugin Framework provides comprehensive web UI management capabilities, allowing plugins to create their own web interfaces that integrate seamlessly with the main application. Each plugin can manage its own UI pages, navigation entries, and themes while maintaining consistency with the overall system design.

### Web UI Architecture

#### Plugin UI Structure

```
<plugin_directory>/
├── plugin.py                  # Main plugin implementation
├── manifest.json              # Plugin metadata
├── webui/                     # Web UI resources
│   ├── routes.py             # Web route handlers
│   ├── templates/            # HTML templates
│   │   ├── base.html        # Plugin base template
│   │   ├── index.html       # Plugin main page
│   │   └── settings.html    # Plugin settings page
│   ├── static/              # Static resources
│   │   ├── css/            # Plugin-specific CSS
│   │   ├── js/             # Plugin-specific JavaScript
│   │   └── img/            # Plugin images
│   └── menu.json           # Menu configuration
└── api/                      # API endpoints
    └── routes.py            # API route handlers
```

### Implementing Plugin Web UI

#### 1. Define Web UI Configuration in Manifest

```json
{
  "name": "wireguard",
  "category": "vpn",
  "version": "1.0.0",
  "webui": {
    "enabled": true,
    "menu_entry": {
      "title": "WireGuard VPN",
      "icon": "bi-shield-lock",
      "category": "vpn",
      "position": 10,
      "permissions": ["vpn.wireguard.view"]
    },
    "routes": {
      "base_path": "/plugins/vpn/wireguard",
      "use_system_theme": true,
      "custom_theme": null
    },
    "static_path": "webui/static",
    "template_path": "webui/templates"
  }
}
```

#### 2. Create Web Routes Handler

```python
# webui/routes.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

class PluginWebUI:
    """Web UI handler for the plugin."""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.router = APIRouter()
        
        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        self.templates = Jinja2Templates(directory=str(template_dir))
        
        # Register routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup web UI routes."""
        
        @self.router.get("/", response_class=HTMLResponse)
        async def plugin_index(request: Request):
            """Plugin main page."""
            return self.templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "servers": await self.plugin.list_servers()
                }
            )
        
        @self.router.get("/settings", response_class=HTMLResponse)
        async def plugin_settings(request: Request):
            """Plugin settings page."""
            return self.templates.TemplateResponse(
                "settings.html",
                {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "config": self.plugin.get_config()
                }
            )
```

#### 3. Implement Plugin Templates

##### Base Template (Extending System Theme)

```html
<!-- webui/templates/base.html -->
{% extends "system/base.html" %}

{% block plugin_name %}{{ plugin.display_name }}{% endblock %}

{% block plugin_nav %}
<ul class="nav nav-tabs mb-3">
    <li class="nav-item">
        <a class="nav-link {% if request.url.path.endswith('/') %}active{% endif %}" 
           href="{{ plugin.webui.base_path }}/">
            <i class="bi bi-house"></i> Overview
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if 'servers' in request.url.path %}active{% endif %}" 
           href="{{ plugin.webui.base_path }}/servers">
            <i class="bi bi-server"></i> Servers
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if 'clients' in request.url.path %}active{% endif %}" 
           href="{{ plugin.webui.base_path }}/clients">
            <i class="bi bi-people"></i> Clients
        </a>
    </li>
    <li class="nav-item">
        <a class="nav-link {% if 'settings' in request.url.path %}active{% endif %}" 
           href="{{ plugin.webui.base_path }}/settings">
            <i class="bi bi-gear"></i> Settings
        </a>
    </li>
</ul>
{% endblock %}

{% block content %}
<!-- Plugin content goes here -->
{% endblock %}
```

##### Plugin Main Page

```html
<!-- webui/templates/index.html -->
{% extends "base.html" %}

{% block title %}{{ plugin.display_name }} - Dashboard{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h1>{{ plugin.display_name }}</h1>
            <p class="text-muted">{{ plugin.description }}</p>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">Active Servers</h5>
                    <h2 class="text-primary">{{ servers|length }}</h2>
                </div>
            </div>
        </div>
        <!-- More dashboard widgets -->
    </div>
    
    <div class="row mt-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Server List</h5>
                </div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Endpoint</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for server in servers %}
                            <tr>
                                <td>{{ server.name }}</td>
                                <td>{{ server.endpoint }}:{{ server.port }}</td>
                                <td>
                                    <span class="badge bg-{{ 'success' if server.enabled else 'secondary' }}">
                                        {{ 'Active' if server.enabled else 'Inactive' }}
                                    </span>
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-primary" 
                                            onclick="editServer('{{ server.id }}')">
                                        Edit
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function editServer(serverId) {
    window.location.href = `{{ plugin.webui.base_path }}/servers/${serverId}/edit`;
}
</script>
{% endblock %}
```

### Menu Integration

#### Automatic Menu Registration

When a plugin with web UI is enabled, it automatically registers its menu entry in the main navigation:

```python
# In BasePlugin class
def register_menu_entry(self):
    """Register plugin menu entry in the main navigation."""
    if not self.manifest.get('webui', {}).get('enabled'):
        return
    
    menu_config = self.manifest['webui']['menu_entry']
    menu_entry = {
        'id': f"{self.category}_{self.name}",
        'title': menu_config.get('title', self.name),
        'icon': menu_config.get('icon', 'bi-puzzle'),
        'url': self.manifest['webui']['routes']['base_path'],
        'category': self.category,
        'position': menu_config.get('position', 999),
        'permissions': menu_config.get('permissions', []),
        'badge': None,  # Can be updated dynamically
        'active': self.enabled
    }
    
    # Register with menu service
    from app.plugins.system.webui.services import MenuService
    MenuService.register_plugin_menu(menu_entry)
```

#### Dynamic Menu Updates

Plugins can update their menu entries dynamically:

```python
# Update badge count
await self.update_menu_badge(count=5, style="danger")

# Update menu visibility
await self.set_menu_visibility(visible=False)

# Update menu title
await self.update_menu_title("WireGuard (3 active)")
```

### Theme Management

#### Using System Theme

By default, plugins use the system theme for consistency:

```python
class PluginWebUI:
    def __init__(self, plugin):
        # Inherit system theme
        self.use_system_theme = plugin.manifest['webui']['routes'].get('use_system_theme', True)
        
        if self.use_system_theme:
            # Use system templates as base
            self.base_template_path = "system/base.html"
        else:
            # Use custom theme
            self.base_template_path = "custom_base.html"
```

#### Custom Theme Support

Plugins can implement their own themes:

```python
# webui/theme.py
class CustomTheme:
    """Custom theme for the plugin."""
    
    def __init__(self):
        self.name = "wireguard-dark"
        self.primary_color = "#00b4d8"
        self.secondary_color = "#0077b6"
        self.styles = {
            "navbar": "bg-dark navbar-dark",
            "sidebar": "bg-dark text-light",
            "card": "bg-dark text-light"
        }
    
    def get_css(self):
        """Return custom CSS."""
        return """
        .plugin-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        /* Custom styles */
        """
```

### Standalone Access

Plugins remain accessible even when the main WebUI is disabled:

```python
# Plugin routes are registered independently
@app.on_event("startup")
async def register_plugin_webui():
    """Register plugin web UI routes."""
    for plugin in plugin_manager.get_enabled_plugins():
        if hasattr(plugin, 'webui_router'):
            # Register at plugin-specific path
            app.include_router(
                plugin.webui_router,
                prefix=f"/plugins/{plugin.category}/{plugin.name}"
            )
```

### WebUI Lifecycle Management

#### Plugin WebUI Initialization

```python
class BasePlugin:
    async def initialize_webui(self):
        """Initialize plugin web UI components."""
        if not self.manifest.get('webui', {}).get('enabled'):
            return
        
        try:
            # Import and initialize WebUI handler
            from .webui.routes import PluginWebUI
            self.webui_handler = PluginWebUI(self)
            self.webui_router = self.webui_handler.router
            
            # Register menu entry
            self.register_menu_entry()
            
            # Mount static files
            self.mount_static_files()
            
            self.logger.info(f"WebUI initialized for {self.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebUI: {e}")
            return False
```

#### Static File Handling

```python
def mount_static_files(self):
    """Mount plugin static files."""
    static_path = Path(__file__).parent / self.manifest['webui']['static_path']
    if static_path.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount(
            f"/plugins/{self.category}/{self.name}/static",
            StaticFiles(directory=str(static_path)),
            name=f"{self.name}_static"
        )
```

### WebUI API Integration

#### Frontend-Backend Communication

```javascript
// Plugin frontend API client
class PluginAPI {
    constructor(pluginPath) {
        this.basePath = `/api${pluginPath}`;
    }
    
    async getServers() {
        const response = await fetch(`${this.basePath}/servers`);
        return response.json();
    }
    
    async createServer(data) {
        const response = await fetch(`${this.basePath}/servers`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        return response.json();
    }
    
    // Real-time updates via WebSocket
    connectWebSocket() {
        const ws = new WebSocket(`ws://${window.location.host}${this.basePath}/ws`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleUpdate(data);
        };
        return ws;
    }
}
```

### Security and Permissions

#### WebUI Access Control

```python
from app.plugins.system.webui.auth_deps import require_web_auth, check_permission

@router.get("/admin", dependencies=[Depends(require_web_auth)])
async def admin_page(
    request: Request,
    user: User = Depends(check_permission("vpn.wireguard.admin"))
):
    """Admin page with permission check."""
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "user": user
    })
```

#### CSRF Protection

```python
from fastapi_csrf_protect import CsrfProtect

@router.post("/settings")
async def update_settings(
    request: Request,
    csrf_protect: CsrfProtect = Depends()
):
    """Update settings with CSRF protection."""
    await csrf_protect.validate_csrf(request)
    # Process settings update
```

### Best Practices for Plugin WebUI

1. **Responsive Design**: Ensure UI works on all device sizes
2. **Lazy Loading**: Load resources only when needed
3. **Error Handling**: Provide clear error messages and recovery options
4. **Accessibility**: Follow WCAG guidelines for accessibility
5. **Performance**: Optimize assets and minimize HTTP requests
6. **Internationalization**: Support multiple languages
7. **Theme Consistency**: Match the main application's look and feel
8. **Progressive Enhancement**: Ensure basic functionality without JavaScript

### Example: Complete WireGuard Plugin WebUI

```python
# app/plugins/vpn/wireguard/webui/routes.py
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

class WireGuardWebUI:
    """WireGuard plugin web UI implementation."""
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.router = APIRouter()
        self.templates = Jinja2Templates(
            directory=str(Path(__file__).parent / "templates")
        )
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            servers = await self.plugin.list_servers()
            stats = await self.plugin.get_statistics()
            
            return self.templates.TemplateResponse("dashboard.html", {
                "request": request,
                "plugin": self.plugin.get_info(),
                "servers": servers,
                "stats": stats,
                "menu_context": await self._get_menu_context()
            })
        
        @self.router.get("/servers/{server_id}", response_class=HTMLResponse)
        async def server_detail(request: Request, server_id: str):
            server = await self.plugin.get_server(server_id)
            clients = await self.plugin.list_clients(server_id=server_id)
            
            return self.templates.TemplateResponse("server_detail.html", {
                "request": request,
                "server": server,
                "clients": clients,
                "plugin": self.plugin.get_info()
            })
        
        @self.router.post("/servers/{server_id}/toggle")
        async def toggle_server(server_id: str):
            server = await self.plugin.get_server(server_id)
            if server.enabled:
                await self.plugin.disable_server(server_id)
            else:
                await self.plugin.enable_server(server_id)
            return JSONResponse({"success": True})
    
    async def _get_menu_context(self):
        """Get menu context for navigation."""
        return {
            "plugin_path": f"/plugins/{self.plugin.category}/{self.plugin.name}",
            "category": self.plugin.category,
            "items": [
                {"title": "Dashboard", "url": "/", "icon": "bi-speedometer2"},
                {"title": "Servers", "url": "/servers", "icon": "bi-server"},
                {"title": "Clients", "url": "/clients", "icon": "bi-people"},
                {"title": "Settings", "url": "/settings", "icon": "bi-gear"}
            ]
        }
```

## Data Schemas

### Pydantic Models

```python
# app/plugins/vpn/myvpn/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ServerCreate(BaseModel):
    """Schema for creating a VPN server."""
    name: str = Field(..., min_length=1, max_length=100)
    endpoint: str = Field(..., description="Server endpoint address")
    port: int = Field(default=1194, ge=1, le=65535)
    protocol: str = Field(default="udp", regex="^(tcp|udp)$")
    encryption: str = Field(default="aes256", description="Encryption method")
    max_clients: int = Field(default=100, ge=1, le=1000)
    description: Optional[str] = Field(None, max_length=500)
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint format."""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            # Could be hostname, validate basic format
            if not v or '.' not in v:
                raise ValueError("Invalid endpoint format")
            return v

class ServerResponse(BaseModel):
    """Schema for server response."""
    id: str
    name: str
    endpoint: str
    port: int
    protocol: str
    encryption: str
    max_clients: int
    active_clients: int = 0
    status: str = "inactive"
    description: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ClientCreate(BaseModel):
    """Schema for creating a VPN client."""
    username: str = Field(..., min_length=1, max_length=50)
    email: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    description: Optional[str] = Field(None, max_length=200)
    allowed_ips: str = Field(default="0.0.0.0/0")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return v

class ClientResponse(BaseModel):
    """Schema for client response."""
    id: str
    username: str
    email: Optional[str] = None
    server_id: str
    status: str = "inactive"
    ip_address: Optional[str] = None
    connected_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    bytes_sent: int = 0
    bytes_received: int = 0
    description: Optional[str] = None
    created_at: datetime

class ConfigResponse(BaseModel):
    """Schema for configuration file response."""
    config: str
    filename: str
    qr_code: Optional[str] = None
```

## Testing Your Plugin

### Unit Tests

```python
# tests/plugins/vpn/test_myvpn.py
import pytest
from app.plugins.vpn.myvpn.plugin import MyVPNPlugin
from app.plugins.vpn.myvpn.repository import MyVPNRepository
from app.plugins.testing.base import PluginTestCase

class TestMyVPNPlugin(PluginTestCase):
    """Test MyVPN plugin."""
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin loads and initializes correctly."""
        plugin = MyVPNPlugin()
        
        # Test basic properties
        assert plugin.name == "myvpn"
        assert plugin.category == "vpn"
        assert plugin.version == "1.0.0"
        
        # Test initialization
        result = await plugin.initialize()
        assert result is True
        
        # Test shutdown
        await plugin.shutdown()
    
    @pytest.mark.asyncio
    async def test_server_creation(self):
        """Test VPN server creation."""
        plugin = MyVPNPlugin()
        await plugin.initialize()
        
        config = {
            "name": "test-server",
            "endpoint": "192.168.1.100",
            "port": 1194,
            "protocol": "udp"
        }
        
        result = await plugin.create_server(config)
        assert "server_id" in result
        assert result.get("status") == "created"
        
        await plugin.shutdown()
    
    @pytest.mark.asyncio
    async def test_repository_operations(self):
        """Test repository operations."""
        repo = MyVPNRepository()
        
        # Test server creation
        server_data = {
            "name": "test-server",
            "endpoint": "192.168.1.100",
            "port": 1194
        }
        
        server_id = await repo.create_server(server_data)
        assert server_id is not None
        
        # Test server retrieval
        server = await repo.get_server(server_id)
        assert server is not None
        assert server["name"] == "test-server"
        
        # Test server listing
        servers = await repo.list_servers()
        assert len(servers) >= 1
        
        # Test server deletion
        success = await repo.delete_server(server_id)
        assert success is True

@pytest.mark.asyncio
async def test_api_routes():
    """Test API routes."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Test server creation (would need authentication)
    # This is a simplified example
    response = client.post("/api/vpn/myvpn/servers", json={
        "name": "test-server",
        "endpoint": "192.168.1.100"
    })
    
    # Add proper authentication and assertions
    # assert response.status_code == 201
```

### Integration Tests

```python
# tests/plugins/vpn/test_myvpn_integration.py
import pytest
from app.plugins.registry.manager import PluginManager

@pytest.mark.asyncio
async def test_plugin_loading():
    """Test plugin loading through plugin manager."""
    manager = PluginManager()
    
    # Load plugin
    success = await manager.load_plugin("vpn.myvpn")
    assert success is True
    
    # Verify plugin is loaded
    assert "vpn.myvpn" in manager.plugins
    
    # Test plugin enable/disable
    await manager.enable_plugin("vpn.myvpn")
    assert "vpn.myvpn" in manager.enabled_plugins
    
    await manager.disable_plugin("vpn.myvpn")
    assert "vpn.myvpn" not in manager.enabled_plugins
    
    # Unload plugin
    await manager.unload_plugin("vpn.myvpn")
    assert "vpn.myvpn" not in manager.plugins
```

## Deployment

### Plugin Package Structure

```
myvpn-plugin-1.0.0/
├── manifest.json
├── README.md
├── LICENSE
├── setup.py
├── requirements.txt
├── app/
│   └── plugins/
│       └── vpn/
│           └── myvpn/
│               ├── __init__.py
│               ├── plugin.py
│               ├── schemas.py
│               ├── repository.py
│               ├── routes.py
│               └── services.py
├── tests/
│   └── test_myvpn.py
└── docs/
    ├── installation.md
    ├── configuration.md
    └── api.md
```

### Setup Script

```python
# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="firewallo-myvpn-plugin",
    version="1.0.0",
    author="Developer Name",
    author_email="developer@example.com",
    description="Custom VPN plugin for Firewallo",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/developer/myvpn-plugin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt"],
    },
    entry_points={
        "firewallo.plugins": [
            "myvpn = app.plugins.vpn.myvpn.plugin:MyVPNPlugin",
        ],
    },
)
```

### Distribution

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI (optional)
pip install twine
twine upload dist/*

# Create release archive
tar -czf myvpn-plugin-1.0.0.tar.gz myvpn-plugin-1.0.0/
```

## Best Practices

### 1. Code Quality

- Use type hints throughout your code
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Use meaningful variable and function names
- Implement proper error handling

### 2. Security

- Validate all inputs using Pydantic models
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Store sensitive data securely (encrypted)
- Follow the principle of least privilege

### 3. Performance

- Use async/await for I/O operations
- Implement connection pooling for external services
- Cache frequently accessed data
- Use pagination for large datasets
- Monitor resource usage

### 4. Documentation

- Write clear installation instructions
- Document all configuration options
- Provide API documentation
- Include usage examples
- Create troubleshooting guides

### 5. Testing

- Write unit tests for all functions
- Create integration tests for workflows
- Test error conditions and edge cases
- Use test fixtures for consistent test data
- Aim for high test coverage (>90%)

## Debugging

### Logging

```python
# Use plugin logger
self.logger.info("Server created successfully")
self.logger.warning("Client limit reached")
self.logger.error("Failed to connect to external service")

# Add contextual information
self.logger.info("Creating server", extra={
    "server_name": server_name,
    "endpoint": endpoint,
    "port": port
})
```

### Error Handling

```python
from app.plugins.base.exceptions import PluginError, PluginConfigError

class MyVPNError(PluginError):
    """Base exception for MyVPN plugin."""
    pass

class ServerNotFoundError(MyVPNError):
    """Raised when server is not found."""
    pass

# Usage
try:
    server = await self.get_server(server_id)
    if not server:
        raise ServerNotFoundError(f"Server {server_id} not found")
except MyVPNError as e:
    self.logger.error(f"MyVPN error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### Development Tools

```bash
# Run tests
pytest tests/plugins/vpn/test_myvpn.py -v

# Check code style
black app/plugins/vpn/myvpn/
isort app/plugins/vpn/myvpn/

# Type checking
mypy app/plugins/vpn/myvpn/

# Run with debug logging
FIREWALLO_LOG_LEVEL=DEBUG python -m uvicorn app.main:app --reload
```

This comprehensive development guide provides everything needed to create professional, production-ready plugins for the Firewallo platform. Follow these patterns and best practices to ensure your plugin integrates seamlessly with the platform and provides a great user experience.
