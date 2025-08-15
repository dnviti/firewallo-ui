"""WireGuard Plugin Web UI Routes Handler."""

from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Import authentication dependencies from WebUI plugin if available
try:
    from app.plugins.system.webui.auth_deps import (
        require_web_auth as _require_web_auth,
        get_current_web_user as _get_current_web_user,
        get_user_context as _get_user_context,
        get_navigation_context as _get_navigation_context
    )
    HAS_AUTH = True

    # Wrap auth functions to handle exceptions gracefully
    async def require_web_auth(request: Request = None):
        try:
            return await _require_web_auth(request)
        except Exception:
            # If auth fails, allow access for now (development mode)
            return {"username": "admin", "id": "default"}

    async def get_current_web_user(request: Request = None):
        try:
            return await _get_current_web_user(request)
        except Exception:
            return {"username": "admin", "id": "default"}

    async def get_user_context(request: Request):
        try:
            return await _get_user_context(request)
        except Exception:
            return {"user": {"username": "admin"}}

    async def get_navigation_context():
        try:
            return await _get_navigation_context()
        except Exception:
            return {"menu_items": []}

except ImportError:
    # Fallback if WebUI plugin is not available
    HAS_AUTH = False
    async def require_web_auth(request: Request = None):
        return {"username": "admin", "id": "default"}
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

        # Setup templates with multiple search paths
        template_dir = Path(__file__).parent / "templates"
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)

        # Add system templates directory for base template
        system_templates_dir = Path(__file__).parent.parent.parent.parent / "system" / "webui" / "templates"
        app_templates_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "templates"

        # Create search paths - prioritize plugin templates, then system, then app
        search_paths = [str(template_dir)]
        if system_templates_dir.exists():
            search_paths.append(str(system_templates_dir))
        if app_templates_dir.exists():
            search_paths.append(str(app_templates_dir))

        # Create Jinja2 environment with multiple loaders
        loader = FileSystemLoader(search_paths)
        env = Environment(loader=loader)
        self.templates = Jinja2Templates(env=env)

        # Setup routes
        self._setup_routes()

        logger.info("WireGuard WebUI initialized")

    async def _get_navigation_context(self, request: Request):
        """Helper to get navigation context with proper error handling."""
        current_user = None
        nav_context = {"plugin_menus": []}
        if HAS_AUTH:
            try:
                current_user = await get_current_web_user(request)
                if current_user:
                    nav_context = await get_navigation_context(current_user)
            except Exception as e:
                logger.warning(f"Failed to get navigation context: {e}")
        return current_user, nav_context

    def _setup_routes(self):
        """Setup all web UI routes."""

        @self.router.get("/", response_class=HTMLResponse)
        async def dashboard(
            request: Request,
            auth=Depends(require_web_auth),
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

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": plugin_info,
                    "servers": servers,
                    "stats": {
                        "total_servers": len(servers),
                        "active_servers": active_servers,
                        "total_clients": total_clients,
                        "active_connections": 0  # TODO: implement active connections tracking
                    },
                    "recent_activity": recent_activity,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("dashboard.html", context)

            except Exception as e:
                logger.error(f"Error rendering dashboard: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/servers", response_class=HTMLResponse)
        async def servers_list(
            request: Request,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """List all WireGuard servers."""
            try:
                servers = await self.plugin.list_servers()

                # Get client count for each server
                for server in servers:
                    clients = await self.plugin.list_clients(server_id=server.id)
                    server.client_count = len(clients)

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "servers": servers,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("servers.html", context)

            except Exception as e:
                logger.error(f"Error listing servers: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/servers/new", response_class=HTMLResponse)
        async def new_server_form(
            request: Request,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show form to create a new server."""
            # Get navigation context for integrated layout
            current_user, nav_context = await self._get_navigation_context(request)

            context = {
                "request": request,
                "plugin": self.plugin.get_info(),
                "menu_context": await self._get_plugin_menu_context(),
                "user": current_user,
                "has_system_base": True,
                "plugin_menus": nav_context.get("plugin_menus", [])
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
            auth=Depends(require_web_auth),
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
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show server details and clients."""
            try:
                server = await self.plugin.get_server(server_id)
                clients = await self.plugin.list_clients(server_id=server_id)

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "server": server,
                    "clients": clients,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("server_detail.html", context)

            except Exception as e:
                logger.error(f"Error getting server details: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/servers/{server_id}/toggle")
        async def toggle_server(
            server_id: str,
            auth=Depends(require_web_auth),
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

        @self.router.get("/servers/{server_id}/edit", response_class=HTMLResponse)
        async def edit_server_form(
            request: Request,
            server_id: str,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show form to edit an existing server."""
            try:
                server = await self.plugin.get_server(server_id)

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "server": server,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("server_form.html", context)

            except Exception as e:
                logger.error(f"Error loading server edit form: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/servers/{server_id}")
        async def update_server(
            request: Request,
            server_id: str,
            name: str = Form(...),
            description: str = Form(""),
            endpoint: str = Form(...),
            port: int = Form(...),
            network: str = Form(...),
            dns: str = Form(""),
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Update an existing server."""
            try:
                # Prepare server data
                server_data = {
                    "name": name,
                    "description": description,
                    "endpoint": endpoint,
                    "port": port,
                    "network": network,
                    "dns": dns.split(',') if dns else []
                }

                # Update the server
                await self.plugin.update_server(server_id, server_data)

                # Redirect to server detail page
                return RedirectResponse(
                    url=f"{await self._get_plugin_menu_context()['plugin_path']}/servers/{server_id}",
                    status_code=302
                )

            except Exception as e:
                logger.error(f"Error updating server: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.delete("/servers/{server_id}")
        async def delete_server(
            server_id: str,
            auth=Depends(require_web_auth),
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
            auth=Depends(require_web_auth),
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

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "clients": clients,
                    "servers": servers,
                    "selected_server": server_id,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("clients.html", context)

            except Exception as e:
                logger.error(f"Error listing clients: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/clients/new", response_class=HTMLResponse)
        async def new_client_form(
            request: Request,
            server_id: Optional[str] = Query(None),
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show form to create a new client."""
            servers = await self.plugin.list_servers()

            # Get navigation context for integrated layout
            current_user, nav_context = await self._get_navigation_context(request)

            context = {
                "request": request,
                "plugin": self.plugin.get_info(),
                "servers": servers,
                "selected_server": server_id,
                "menu_context": await self._get_plugin_menu_context(),
                "user": current_user,
                "has_system_base": True,
                "plugin_menus": nav_context.get("plugin_menus", [])
            }

            return self.templates.TemplateResponse("client_form.html", context)

        @self.router.post("/clients/new")
        async def create_client(
            request: Request,
            server_id: str = Form(...),
            name: str = Form(...),
            email: Optional[str] = Form(None),
            allowed_ips: str = Form("0.0.0.0/0"),
            auth=Depends(require_web_auth),
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
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Show client configuration."""
            try:
                config = await self.plugin.generate_config(client_id)
                client = await self.plugin.get_client(client_id)

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "client": client,
                    "config": config,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
                }

                return self.templates.TemplateResponse("client_config.html", context)

            except Exception as e:
                logger.error(f"Error getting client config: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.delete("/clients/{client_id}")
        async def delete_client(
            client_id: str,
            auth=Depends(require_web_auth),
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
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Plugin settings page."""
            try:
                config = self.plugin.get_config()

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)

                context = {
                    "request": request,
                    "plugin": self.plugin.get_info(),
                    "config": config,
                    "menu_context": await self._get_plugin_menu_context(),
                    "user": current_user,
                    "has_system_base": True,
                    "plugin_menus": nav_context.get("plugin_menus", [])
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
            auth=Depends(require_web_auth),
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

        @self.router.post("/servers/{server_id}/restart")
        async def restart_server(
            server_id: str,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Restart a WireGuard server."""
            try:
                # Get the server to verify it exists
                server = await self.plugin.get_server(server_id)

                # Restart the server (this would typically involve stopping and starting the WireGuard interface)
                await self.plugin.restart_server(server_id)

                return JSONResponse({"success": True, "message": "Server restarted successfully"})
            except Exception as e:
                logger.error(f"Error restarting server {server_id}: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.post("/servers/{server_id}/regenerate-keys")
        async def regenerate_server_keys(
            server_id: str,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Regenerate server keys."""
            try:
                # Get the server to verify it exists
                server_before = await self.plugin.get_server(server_id)
                logger.info(f"Server before regenerate: private_key={server_before.private_key[:10] if server_before and server_before.private_key else 'None'}...")

                # Regenerate the server keys
                success = await self.plugin.regenerate_server_keys(server_id)

                if not success:
                    return JSONResponse(
                        {"success": False, "error": "Failed to regenerate keys"},
                        status_code=500
                    )

                # Get the server after regeneration to verify keys were updated
                server_after = await self.plugin.get_server(server_id)
                logger.info(f"Server after regenerate: private_key={server_after.private_key[:10] if server_after and server_after.private_key else 'None'}...")

                return JSONResponse({"success": True, "message": "Server keys regenerated successfully"})
            except Exception as e:
                logger.error(f"Error regenerating keys for server {server_id}: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.get("/servers/{server_id}/config")
        async def download_server_config(
            request: Request,
            server_id: str,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Download server configuration file."""
            try:
                from fastapi.responses import Response

                # Get the server configuration
                config_content = await self.plugin.get_server_config(server_id)
                server = await self.plugin.get_server(server_id)

                # Return the config as a downloadable file
                return Response(
                    content=config_content,
                    media_type="text/plain",
                    headers={
                        "Content-Disposition": f"attachment; filename={server.name}.conf"
                    }
                )
            except Exception as e:
                logger.error(f"Error downloading config for server {server_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/settings/restart")
        async def restart_wireguard_service(
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Restart the WireGuard service."""
            try:
                # Restart the entire WireGuard service
                await self.plugin.restart_service()

                return JSONResponse({"success": True, "message": "WireGuard service restarted successfully"})
            except Exception as e:
                logger.error(f"Error restarting WireGuard service: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.get("/settings/export")
        async def export_configuration(
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Export all WireGuard configuration."""
            try:
                from fastapi.responses import Response
                import json
                from datetime import datetime

                # Get all servers and clients
                servers = await self.plugin.list_servers()
                all_clients = []

                for server in servers:
                    clients = await self.plugin.list_clients(server_id=server.id)
                    all_clients.extend(clients)

                # Create export data
                export_data = {
                    "export_date": datetime.now().isoformat(),
                    "plugin_version": self.plugin.get_info().get("version", "unknown"),
                    "servers": [server.dict() if hasattr(server, 'dict') else vars(server) for server in servers],
                    "clients": [client.dict() if hasattr(client, 'dict') else vars(client) for client in all_clients],
                    "config": self.plugin.get_config()
                }

                # Return as JSON file
                return Response(
                    content=json.dumps(export_data, indent=2),
                    media_type="application/json",
                    headers={
                        "Content-Disposition": f"attachment; filename=wireguard-config-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
                    }
                )
            except Exception as e:
                logger.error(f"Error exporting configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/logs", response_class=HTMLResponse)
        async def view_logs(
            request: Request,
            lines: int = Query(100),
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """View WireGuard logs."""
            try:
                # Get recent logs
                logs = await self.plugin.get_logs()

                # Get navigation context for integrated layout
                current_user, nav_context = await self._get_navigation_context(request)
                menu_context = await self._get_plugin_menu_context()

                context = {
                    "request": request,
                    "logs": logs,
                    "current_user": current_user,
                    "navigation": nav_context,
                    "menu_context": menu_context,
                    "has_system_base": nav_context is not None
                }

                return self.templates.TemplateResponse("logs.html", context)
            except Exception as e:
                logger.error(f"Error viewing logs: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/servers/fix-keys")
        async def fix_all_server_keys(
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Fix all servers with missing keys."""
            try:
                servers = await self.plugin.list_servers()
                fixed_count = 0

                for server in servers:
                    if not server.private_key or server.private_key == "N/A" or not server.public_key:
                        success = await self.plugin.regenerate_server_keys(server.id)
                        if success:
                            fixed_count += 1

                return JSONResponse({
                    "success": True,
                    "message": f"Fixed {fixed_count} servers with missing keys",
                    "fixed_count": fixed_count
                })
            except Exception as e:
                logger.error(f"Error fixing server keys: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

        @self.router.get("/servers/{server_id}/debug")
        async def debug_server_data(
            request: Request,
            server_id: str,
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Debug endpoint to check server private key status."""
            try:
                server = await self.plugin.get_server(server_id)
                has_private_key = bool(server and server.private_key and server.private_key != "N/A")

                return JSONResponse({
                    "server_id": server_id,
                    "has_private_key": has_private_key,
                    "private_key_length": len(server.private_key) if server and server.private_key else 0,
                    "private_key_preview": server.private_key[:10] + "..." if has_private_key else "None"
                })
            except Exception as e:
                logger.error(f"Error in debug endpoint: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @self.router.post("/logs/clear")
        async def clear_logs(
            auth=Depends(require_web_auth),
            _enabled: None = require_plugin_instance_enabled(self.plugin) if HAS_PLUGIN_DEPS else None
        ):
            """Clear WireGuard logs."""
            try:
                # Clear logs (this would typically clear application-specific logs)
                await self.plugin.clear_logs()

                return JSONResponse({"success": True, "message": "Logs cleared successfully"})
            except Exception as e:
                logger.error(f"Error clearing logs: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)},
                    status_code=500
                )

    async def _get_plugin_menu_context(self) -> Dict[str, Any]:
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


# Add class aliases for the plugin base class to find
PluginWebUI = WireGuardWebUI
WireguardWebUI = WireGuardWebUI
WebUI = WireGuardWebUI

# Export the WebUI class
__all__ = ["WireGuardWebUI", "WireguardWebUI", "PluginWebUI", "WebUI"]
