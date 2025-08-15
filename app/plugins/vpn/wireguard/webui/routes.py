"""WireGuard Plugin Web UI Routes Handler."""

from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from datetime import datetime

# Import authentication dependencies from WebUI plugin if available
try:
    from app.plugins.system.webui.auth_deps import (
        require_web_auth,
        get_current_web_user,
        get_user_context,
        get_navigation_context
    )
    HAS_AUTH = True
except ImportError:
    # Fallback if WebUI plugin is not available
    HAS_AUTH = False
    async def require_web_auth(request: Request = None):
        return True
    async def get_current_web_user(request: Request = None):
        return {"username": "admin", "id": "default"}
    async def get_user_context(request: Request):
        return {"user": {"username": "admin"}}
    async def get_navigation_context():
        return {"menu_items": []}


logger = logging.getLogger("firewallo.plugins.vpn.wireguard.webui")

# Import plugin dependency functions
try:
    from app.plugins.base.dependencies import require_plugin_instance_enabled
    HAS_PLUGIN_DEPS = True
except ImportError:
    HAS_PLUGIN_DEPS = False
    def require_plugin_instance_enabled(plugin_instance):
        """Fallback dependency that always allows access."""
        def _dummy():
            pass
        return Depends(_dummy)


class WireGuardWebUI:
    """WireGuard Plugin Web UI Implementation."""

    def __init__(self, plugin):
        """Initialize WireGuard Web UI.

        Args:
            plugin: The WireGuard plugin instance
        """
        self.plugin = plugin
        self.router = APIRouter()

        # Setup templates
        template_dir = Path(__file__).parent / "templates"
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)

        self.templates = Jinja2Templates(directory=str(template_dir))

        # Setup routes
        self._setup_routes()

        logger.info("WireGuard WebUI initialized")

    def _setup_routes(self):
        """Setup all web UI routes."""

        @self.router.get("/", response_class=HTMLResponse)
        async def dashboard(
            request: Request,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """WireGuard dashboard page."""
            try:
                # Get plugin information
                plugin_info = self.plugin.get_info()

                # Get servers and statistics
                servers = await self.plugin.list_servers()

                # Count active servers and total clients
                active_servers = sum(1 for s in servers if s.enabled)
                total_clients = 0
                for server in servers:
                    clients = await self.plugin.list_clients(server_id=server.id)
                    total_clients += len(clients)

                # Get recent activity
                recent_activity = []

                context = {
                    "request": request,
                    "plugin": plugin_info,
                    "servers": servers,
                    "stats": {
                        "total_servers": len(servers),
                        "active_servers": active_servers,
                        "total_clients": total_clients,
                        "active_connections": 0  # TODO: Implement active connection tracking
                    },
                    "recent_activity": recent_activity,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("simple.html", context)

            except Exception as e:
                logger.error(f"Error rendering dashboard: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/servers", response_class=HTMLResponse)
        async def servers_list(
            request: Request,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """List all WireGuard servers."""
            try:
                servers = await self.plugin.list_servers()

                # Get client count for each server
                for server in servers:
                    clients = await self.plugin.list_clients(server_id=server.id)
                    server.client_count = len(clients)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "servers": servers,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("servers.html", context)

            except Exception as e:
                logger.error(f"Error listing servers: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/servers/new", response_class=HTMLResponse)
        async def new_server_form(
            request: Request,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show form to create a new server."""
            context = {
                "request": request,
                "plugin": self.plugin.get_info(),
                "menu_context": await self._get_menu_context(),
                "user": await get_current_web_user(request) if HAS_AUTH else None
            }

            return self.templates.TemplateResponse("server_form.html", context)

        @self.router.post("/servers/new")
        async def create_server(
            request: Request,
            name: str = Form(...),
            endpoint: str = Form(...),
            port: int = Form(51820),
            network: str = Form("10.0.0.0/24"),
            dns_servers: str = Form("8.8.8.8,8.8.4.4"),
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Create a new WireGuard server."""
            try:
                from app.plugins.categories.vpn import VPNServerCreate

                server_data = VPNServerCreate(
                    name=name,
                    endpoint=endpoint,
                    port=port,
                    network=network,
                    dns_servers=dns_servers.split(","),
                    enabled=True
                )

                await self.plugin.create_server(server_data)

                return RedirectResponse(
                    url=f"{self.plugin.webui_base_path}/servers",
                    status_code=status.HTTP_303_SEE_OTHER
                )

            except Exception as e:
                logger.error(f"Error creating server: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/servers/{server_id}", response_class=HTMLResponse)
        async def server_detail(
            request: Request,
            server_id: str,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show server details and clients."""
            try:
                server = await self.plugin.get_server(server_id)
                clients = await self.plugin.list_clients(server_id=server_id)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "server": server,
                    "clients": clients,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("server_detail.html", context)

            except Exception as e:
                logger.error(f"Error getting server details: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/servers/{server_id}/toggle")
        async def toggle_server(
            server_id: str,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Toggle server enabled state."""
            try:
                server = await self.plugin.get_server(server_id)

                from app.plugins.categories.vpn import VPNServerUpdate
                update_data = VPNServerUpdate(enabled=not server.enabled)

                await self.plugin.update_server(server_id, update_data)

                return JSONResponse({
                    "success": True,
                    "enabled": not server.enabled
                })

            except Exception as e:
                logger.error(f"Error toggling server: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.delete("/servers/{server_id}")
        async def delete_server(
            server_id: str,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Delete a server."""
            try:
                await self.plugin.delete_server(server_id)
                return JSONResponse({"success": True})

            except Exception as e:
                logger.error(f"Error deleting server: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.get("/clients", response_class=HTMLResponse)
        async def clients_list(
            request: Request,
            server_id: Optional[str] = Query(None),
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """List all clients."""
            try:
                if server_id:
                    clients = await self.plugin.list_clients(server_id=server_id)
                    servers = [await self.plugin.get_server(server_id)]
                else:
                    # Get all clients from all servers
                    servers = await self.plugin.list_servers()
                    clients = []
                    for server in servers:
                        server_clients = await self.plugin.list_clients(server_id=server.id)
                        clients.extend(server_clients)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "clients": clients,
                    "servers": servers,
                    "selected_server": server_id,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("clients.html", context)

            except Exception as e:
                logger.error(f"Error listing clients: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/clients/new", response_class=HTMLResponse)
        async def new_client_form(
            request: Request,
            server_id: Optional[str] = Query(None),
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show form to create a new client."""
            servers = await self.plugin.list_servers()

            context = {
                "request": request,
                "plugin": self.plugin.get_info(),
                "servers": servers,
                "selected_server": server_id,
                "menu_context": await self._get_menu_context(),
                "user": await get_current_web_user(request) if HAS_AUTH else None
            }

            return self.templates.TemplateResponse("client_form.html", context)

        @self.router.post("/clients/new")
        async def create_client(
            request: Request,
            server_id: str = Form(...),
            name: str = Form(...),
            email: Optional[str] = Form(None),
            allowed_ips: str = Form("0.0.0.0/0"),
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Create a new client."""
            try:
                from app.plugins.categories.vpn import VPNClientCreate

                client_data = VPNClientCreate(
                    name=name,
                    server_id=server_id,
                    email=email,
                    allowed_ips=allowed_ips.split(",") if allowed_ips else ["0.0.0.0/0"]
                )

                await self.plugin.create_client(client_data)

                return RedirectResponse(
                    url=f"{self.plugin.webui_base_path}/clients?server_id={server_id}",
                    status_code=status.HTTP_303_SEE_OTHER
                )

            except Exception as e:
                logger.error(f"Error creating client: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/clients/{client_id}/config", response_class=HTMLResponse)
        async def client_config(
            request: Request,
            client_id: str,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show client configuration."""
            try:
                config = await self.plugin.generate_config(client_id)
                client = await self.plugin.get_client(client_id)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "client": client,
                    "config": config,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("client_config.html", context)

            except Exception as e:
                logger.error(f"Error getting client config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.delete("/clients/{client_id}")
        async def delete_client(
            client_id: str,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Delete a client."""
            try:
                await self.plugin.delete_client(client_id)
                return JSONResponse({"success": True})

            except Exception as e:
                logger.error(f"Error deleting client: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.get("/settings", response_class=HTMLResponse)
        async def settings_page(
            request: Request,
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Plugin settings page."""
            try:
                config = self.plugin.get_config()

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "config": config,
                    "menu_context": await self._get_menu_context(),
                    "user": await get_current_web_user(request) if HAS_AUTH else None
                }

                return self.templates.TemplateResponse("settings.html", context)

            except Exception as e:
                logger.error(f"Error rendering settings: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/settings")
        async def update_settings(
            request: Request,
            interface_name: str = Form("wg0"),
            listen_port: int = Form(51820),
            network_range: str = Form("10.0.0.0/24"),
            dns_servers: str = Form("8.8.8.8,8.8.4.4"),
            mtu: int = Form(1420),
            keep_alive: int = Form(25),
            auth=Depends(require_web_auth) if HAS_AUTH else None,
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Update plugin settings."""
            try:
                config_updates = {
                    "interface_name": interface_name,
                    "listen_port": listen_port,
                    "network_range": network_range,
                    "dns_servers": dns_servers.split(","),
                    "mtu": mtu,
                    "keep_alive": keep_alive
                }

                self.plugin.update_config(config_updates)

                return RedirectResponse(
                    url=f"{self.plugin.webui_base_path}/settings",
                    status_code=status.HTTP_303_SEE_OTHER
                )

            except Exception as e:
                logger.error(f"Error updating settings: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _get_menu_context(self) -> Dict[str, Any]:
        """Get menu context for navigation."""
        return {
            "plugin_path": self.plugin.webui_base_path or f"/plugins/{self.plugin.category}/{self.plugin.name}",
            "category": self.plugin.category,
            "plugin_name": self.plugin.name,
            "items": [
                {
                    "title": "Dashboard",
                    "url": "/",
                    "icon": "bi-speedometer2",
                    "active_pattern": r"/$"
                },
                {
                    "title": "Servers",
                    "url": "/servers",
                    "icon": "bi-server",
                    "active_pattern": r"/servers"
                },
                {
                    "title": "Clients",
                    "url": "/clients",
                    "icon": "bi-people",
                    "active_pattern": r"/clients"
                },
                {
                    "title": "Settings",
                    "url": "/settings",
                    "icon": "bi-gear",
                    "active_pattern": r"/settings"
                }
            ]
        }

        @self.router.get("/test")
        async def test_route(_enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None):
            """Simple test route to verify plugin is working."""
            return {"status": "WireGuard WebUI is working", "plugin": self.plugin.name}


# Export the WebUI class
__all__ = ["WireGuardWebUI"]
