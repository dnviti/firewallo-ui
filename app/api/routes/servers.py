"""Generic server management API routes.

This module provides generic server management functionality that can work with
any VPN plugin through the plugin framework. Plugin-specific functionality
should be implemented within the plugins themselves.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from app.auth.models import current_active_user
from app.plugins import plugin_manager

router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("/")
async def list_all_servers(
    plugin_category: str = Query("vpn", description="Plugin category to filter by"),
    user = Depends(current_active_user)
):
    """List all servers across all enabled plugins of the specified category."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins(category=plugin_category)

        all_servers = []
        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_servers'):
                    servers = await plugin.list_servers()
                    # Add plugin info to each server
                    for server in servers:
                        server_dict = server.__dict__ if hasattr(server, '__dict__') else dict(server)
                        server_dict['plugin_name'] = plugin.name
                        server_dict['plugin_category'] = plugin.category
                        all_servers.append(server_dict)
            except Exception as e:
                # Log error but continue with other plugins
                print(f"Error getting servers from plugin {plugin.name}: {e}")

        return {
            "servers": all_servers,
            "total": len(all_servers),
            "plugins_checked": len(enabled_plugins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")


@router.get("/plugins")
async def get_available_server_plugins(user = Depends(current_active_user)):
    """Get all available plugins that provide server functionality."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        server_plugins = []
        for plugin in enabled_plugins:
            if hasattr(plugin, 'list_servers') or hasattr(plugin, 'create_server'):
                plugin_info = plugin.get_info()
                plugin_info['has_servers'] = hasattr(plugin, 'list_servers')
                plugin_info['can_create_servers'] = hasattr(plugin, 'create_server')
                server_plugins.append(plugin_info)

        return {
            "plugins": server_plugins,
            "total": len(server_plugins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server plugins: {str(e)}")


@router.get("/stats")
async def get_server_statistics(user = Depends(current_active_user)):
    """Get aggregated server statistics across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        total_servers = 0
        active_servers = 0
        plugin_stats = {}

        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_servers'):
                    servers = await plugin.list_servers()
                    plugin_server_count = len(servers)
                    plugin_active_count = len([s for s in servers if getattr(s, 'enabled', False)])

                    total_servers += plugin_server_count
                    active_servers += plugin_active_count

                    plugin_stats[plugin.name] = {
                        "total_servers": plugin_server_count,
                        "active_servers": plugin_active_count,
                        "category": plugin.category
                    }
            except Exception as e:
                plugin_stats[plugin.name] = {
                    "error": str(e),
                    "total_servers": 0,
                    "active_servers": 0
                }

        return {
            "total_servers": total_servers,
            "active_servers": active_servers,
            "inactive_servers": total_servers - active_servers,
            "plugin_stats": plugin_stats,
            "plugins_checked": len(enabled_plugins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server statistics: {str(e)}")


@router.get("/health")
async def check_all_server_health(user = Depends(current_active_user)):
    """Check health status of all servers across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        health_report = {
            "overall_status": "healthy",
            "plugins": {},
            "total_servers": 0,
            "healthy_servers": 0,
            "unhealthy_servers": 0
        }

        for plugin in enabled_plugins:
            try:
                plugin_health = {
                    "plugin_status": "healthy",
                    "servers": [],
                    "server_count": 0
                }

                if hasattr(plugin, 'list_servers'):
                    servers = await plugin.list_servers()
                    plugin_health["server_count"] = len(servers)
                    health_report["total_servers"] += len(servers)

                    for server in servers:
                        server_health = {
                            "id": getattr(server, 'id', 'unknown'),
                            "name": getattr(server, 'name', 'unknown'),
                            "status": "healthy" if getattr(server, 'enabled', False) else "inactive"
                        }

                        # Try to get detailed health if plugin supports it
                        if hasattr(plugin, 'get_connection_status'):
                            try:
                                status = await plugin.get_connection_status(server.id)
                                server_health["status"] = status.status
                                server_health["details"] = status.__dict__
                            except:
                                pass  # Use basic status

                        plugin_health["servers"].append(server_health)

                        if server_health["status"] in ["healthy", "active", "connected"]:
                            health_report["healthy_servers"] += 1
                        else:
                            health_report["unhealthy_servers"] += 1

                health_report["plugins"][plugin.name] = plugin_health

            except Exception as e:
                health_report["plugins"][plugin.name] = {
                    "plugin_status": "error",
                    "error": str(e),
                    "servers": [],
                    "server_count": 0
                }
                health_report["overall_status"] = "degraded"

        # Determine overall status
        if health_report["unhealthy_servers"] > 0:
            health_report["overall_status"] = "degraded"
        if health_report["total_servers"] == 0:
            health_report["overall_status"] = "no_servers"

        return health_report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check server health: {str(e)}")


@router.post("/discover")
async def discover_new_servers(user = Depends(current_active_user)):
    """Trigger discovery of new servers across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        discovery_results = {}

        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'discover_servers'):
                    # Plugin has discovery capability
                    discovered = await plugin.discover_servers()
                    discovery_results[plugin.name] = {
                        "status": "success",
                        "discovered": discovered,
                        "count": len(discovered) if isinstance(discovered, list) else 0
                    }
                else:
                    # Plugin doesn't support discovery
                    discovery_results[plugin.name] = {
                        "status": "not_supported",
                        "message": "Plugin does not support server discovery"
                    }
            except Exception as e:
                discovery_results[plugin.name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "discovery_results": discovery_results,
            "plugins_checked": len(enabled_plugins)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover servers: {str(e)}")


# Redirect endpoints - these redirect to the appropriate plugin endpoints
@router.get("/redirect/{plugin_name}")
async def redirect_to_plugin(plugin_name: str, user = Depends(current_active_user)):
    """Get information about how to access a specific plugin's server endpoints."""
    try:
        # Find plugin by name in any category
        all_plugins = plugin_manager.get_all_plugins()
        target_plugin = None

        for path, plugin in all_plugins.items():
            if plugin.name == plugin_name:
                target_plugin = plugin
                break

        if not target_plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found")

        if not target_plugin.enabled:
            raise HTTPException(status_code=503, detail=f"Plugin '{plugin_name}' is disabled")

        # Get plugin's API information
        plugin_info = target_plugin.get_info()
        api_prefix = plugin_info.get('api_prefix', f'/api/{target_plugin.category}/{target_plugin.name}')

        return {
            "plugin_name": plugin_name,
            "plugin_category": target_plugin.category,
            "api_prefix": api_prefix,
            "available_endpoints": {
                "servers": f"{api_prefix}/servers",
                "clients": f"{api_prefix}/clients",
                "status": f"{api_prefix}/status",
                "config": f"{api_prefix}/config"
            },
            "plugin_info": plugin_info
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin redirect info: {str(e)}")
