"""Generic peer/client management API routes.

This module provides generic peer/client management functionality that can work with
any plugin through the plugin framework. Plugin-specific functionality
should be implemented within the plugins themselves.
"""

from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from app.auth.models import current_active_user
from app.plugins import plugin_manager

router = APIRouter(tags=["peers"])


@router.get("/peers")
async def list_all_peers(
    plugin_category: str = Query("vpn", description="Plugin category to filter by"),
    server_id: Optional[str] = Query(None, description="Filter by server ID"),
    user = Depends(current_active_user)
):
    """List all peers/clients across all enabled plugins of the specified category."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins(category=plugin_category)

        all_peers = []
        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_clients'):
                    peers = await plugin.list_clients(server_id=server_id)
                    # Add plugin info to each peer
                    for peer in peers:
                        peer_dict = peer.__dict__ if hasattr(peer, '__dict__') else dict(peer)
                        peer_dict['plugin_name'] = plugin.name
                        peer_dict['plugin_category'] = plugin.category
                        all_peers.append(peer_dict)
            except Exception as e:
                # Log error but continue with other plugins
                print(f"Error getting peers from plugin {plugin.name}: {e}")

        return {
            "peers": all_peers,
            "total": len(all_peers),
            "plugins_checked": len(enabled_plugins),
            "server_filter": server_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list peers: {str(e)}")


@router.get("/peers/plugins")
async def get_available_peer_plugins(user = Depends(current_active_user)):
    """Get all available plugins that provide peer/client functionality."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        peer_plugins = []
        for plugin in enabled_plugins:
            if hasattr(plugin, 'list_clients') or hasattr(plugin, 'create_client'):
                plugin_info = plugin.get_info()
                plugin_info['has_clients'] = hasattr(plugin, 'list_clients')
                plugin_info['can_create_clients'] = hasattr(plugin, 'create_client')
                plugin_info['supports_config_generation'] = hasattr(plugin, 'generate_config')
                peer_plugins.append(plugin_info)

        return {
            "plugins": peer_plugins,
            "total": len(peer_plugins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get peer plugins: {str(e)}")


@router.get("/peers/stats")
async def get_peer_statistics(user = Depends(current_active_user)):
    """Get aggregated peer statistics across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        total_peers = 0
        active_peers = 0
        plugin_stats = {}

        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_clients'):
                    peers = await plugin.list_clients()
                    plugin_peer_count = len(peers)
                    plugin_active_count = len([p for p in peers if getattr(p, 'enabled', False)])

                    total_peers += plugin_peer_count
                    active_peers += plugin_active_count

                    plugin_stats[plugin.name] = {
                        "total_peers": plugin_peer_count,
                        "active_peers": plugin_active_count,
                        "inactive_peers": plugin_peer_count - plugin_active_count,
                        "category": plugin.category
                    }
            except Exception as e:
                plugin_stats[plugin.name] = {
                    "error": str(e),
                    "total_peers": 0,
                    "active_peers": 0
                }

        return {
            "total_peers": total_peers,
            "active_peers": active_peers,
            "inactive_peers": total_peers - active_peers,
            "plugin_stats": plugin_stats,
            "plugins_checked": len(enabled_plugins)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get peer statistics: {str(e)}")


@router.get("/peers/health")
async def check_all_peer_health(user = Depends(current_active_user)):
    """Check health status of all peers across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        health_report = {
            "overall_status": "healthy",
            "plugins": {},
            "total_peers": 0,
            "healthy_peers": 0,
            "unhealthy_peers": 0
        }

        for plugin in enabled_plugins:
            try:
                plugin_health = {
                    "plugin_status": "healthy",
                    "peers": [],
                    "peer_count": 0
                }

                if hasattr(plugin, 'list_clients'):
                    peers = await plugin.list_clients()
                    plugin_health["peer_count"] = len(peers)
                    health_report["total_peers"] += len(peers)

                    for peer in peers:
                        peer_health = {
                            "id": getattr(peer, 'id', 'unknown'),
                            "name": getattr(peer, 'name', 'unknown'),
                            "server_id": getattr(peer, 'server_id', 'unknown'),
                            "status": "healthy" if getattr(peer, 'enabled', False) else "inactive"
                        }

                        # Try to get detailed health if plugin supports it
                        if hasattr(plugin, 'get_connection_status'):
                            try:
                                status = await plugin.get_connection_status(peer.server_id, peer.id)
                                peer_health["status"] = status.status
                                peer_health["details"] = status.__dict__
                            except:
                                pass  # Use basic status

                        plugin_health["peers"].append(peer_health)

                        if peer_health["status"] in ["healthy", "active", "connected"]:
                            health_report["healthy_peers"] += 1
                        else:
                            health_report["unhealthy_peers"] += 1

                health_report["plugins"][plugin.name] = plugin_health

            except Exception as e:
                health_report["plugins"][plugin.name] = {
                    "plugin_status": "error",
                    "error": str(e),
                    "peers": [],
                    "peer_count": 0
                }
                health_report["overall_status"] = "degraded"

        # Determine overall status
        if health_report["unhealthy_peers"] > 0:
            health_report["overall_status"] = "degraded"
        if health_report["total_peers"] == 0:
            health_report["overall_status"] = "no_peers"

        return health_report

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check peer health: {str(e)}")


@router.get("/peers/by-server/{server_id}")
async def get_peers_by_server(server_id: str, user = Depends(current_active_user)):
    """Get all peers for a specific server across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        server_peers = []
        server_found = False

        for plugin in enabled_plugins:
            try:
                # First check if the server exists in this plugin
                if hasattr(plugin, 'get_server'):
                    server = await plugin.get_server(server_id)
                    if server:
                        server_found = True
                        # Get peers for this server
                        if hasattr(plugin, 'list_clients'):
                            peers = await plugin.list_clients(server_id=server_id)
                            for peer in peers:
                                peer_dict = peer.__dict__ if hasattr(peer, '__dict__') else dict(peer)
                                peer_dict['plugin_name'] = plugin.name
                                peer_dict['plugin_category'] = plugin.category
                                server_peers.append(peer_dict)
                        break  # Found the server, no need to check other plugins
            except Exception as e:
                # Continue checking other plugins
                print(f"Error checking server {server_id} in plugin {plugin.name}: {e}")

        if not server_found:
            raise HTTPException(status_code=404, detail=f"Server {server_id} not found in any plugin")

        return {
            "server_id": server_id,
            "peers": server_peers,
            "peer_count": len(server_peers)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get peers for server: {str(e)}")


@router.get("/peers/search")
async def search_peers(
    query: str = Query(..., description="Search query (name, email, etc.)"),
    user = Depends(current_active_user)
):
    """Search for peers across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        search_results = []
        query_lower = query.lower()

        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_clients'):
                    peers = await plugin.list_clients()
                    for peer in peers:
                        # Search in peer name, email, and description
                        peer_name = getattr(peer, 'name', '').lower()
                        peer_email = getattr(peer, 'email', '').lower()
                        peer_desc = getattr(peer, 'description', '').lower()

                        if (query_lower in peer_name or
                            query_lower in peer_email or
                            query_lower in peer_desc):

                            peer_dict = peer.__dict__ if hasattr(peer, '__dict__') else dict(peer)
                            peer_dict['plugin_name'] = plugin.name
                            peer_dict['plugin_category'] = plugin.category
                            search_results.append(peer_dict)
            except Exception as e:
                print(f"Error searching peers in plugin {plugin.name}: {e}")

        return {
            "query": query,
            "results": search_results,
            "result_count": len(search_results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search peers: {str(e)}")


@router.post("/peers/bulk-action")
async def bulk_peer_action(
    action: str = Query(..., description="Action to perform: enable, disable, delete"),
    peer_ids: List[str] = Query(..., description="List of peer IDs"),
    user = Depends(current_active_user)
):
    """Perform bulk actions on multiple peers across plugins."""
    try:
        if action not in ["enable", "disable", "delete"]:
            raise HTTPException(status_code=400, detail="Invalid action. Must be: enable, disable, or delete")

        enabled_plugins = plugin_manager.get_enabled_plugins()
        results = {}

        for peer_id in peer_ids:
            results[peer_id] = {"success": False, "error": "Peer not found in any plugin"}

            # Find the peer in any plugin
            for plugin in enabled_plugins:
                try:
                    if hasattr(plugin, 'get_client'):
                        peer = await plugin.get_client(peer_id)
                        if peer:
                            # Found the peer, perform the action
                            if action == "enable" and hasattr(plugin, 'update_client'):
                                from app.plugins.categories.vpn import VPNClientUpdate
                                update_data = VPNClientUpdate(enabled=True)
                                await plugin.update_client(peer_id, update_data)
                                results[peer_id] = {"success": True, "action": "enabled"}
                            elif action == "disable" and hasattr(plugin, 'update_client'):
                                from app.plugins.categories.vpn import VPNClientUpdate
                                update_data = VPNClientUpdate(enabled=False)
                                await plugin.update_client(peer_id, update_data)
                                results[peer_id] = {"success": True, "action": "disabled"}
                            elif action == "delete" and hasattr(plugin, 'delete_client'):
                                success = await plugin.delete_client(peer_id)
                                results[peer_id] = {"success": success, "action": "deleted"}
                            else:
                                results[peer_id] = {"success": False, "error": f"Plugin does not support {action}"}
                            break  # Found and processed, no need to check other plugins
                except Exception as e:
                    results[peer_id] = {"success": False, "error": str(e)}

        successful = sum(1 for result in results.values() if result["success"])
        return {
            "action": action,
            "peer_ids": peer_ids,
            "results": results,
            "successful": successful,
            "failed": len(peer_ids) - successful
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk action: {str(e)}")


@router.get("/peers/configurations")
async def get_all_peer_configurations(
    format: str = Query("json", description="Configuration format: json, configs"),
    user = Depends(current_active_user)
):
    """Get configuration information for all peers across all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()

        configurations = []

        for plugin in enabled_plugins:
            try:
                if hasattr(plugin, 'list_clients'):
                    peers = await plugin.list_clients()
                    for peer in peers:
                        config_info = {
                            "peer_id": getattr(peer, 'id', 'unknown'),
                            "peer_name": getattr(peer, 'name', 'unknown'),
                            "server_id": getattr(peer, 'server_id', 'unknown'),
                            "plugin_name": plugin.name,
                            "plugin_category": plugin.category,
                            "has_config_generation": hasattr(plugin, 'generate_config')
                        }

                        if format == "configs" and hasattr(plugin, 'generate_config'):
                            try:
                                config = await plugin.generate_config(peer.id)
                                config_info["config_content"] = config.config_content
                                config_info["has_qr_code"] = config.qr_code is not None
                            except Exception as e:
                                config_info["config_error"] = str(e)

                        configurations.append(config_info)
            except Exception as e:
                print(f"Error getting configurations from plugin {plugin.name}: {e}")

        return {
            "format": format,
            "configurations": configurations,
            "total": len(configurations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get peer configurations: {str(e)}")


# Redirect endpoints - these redirect to the appropriate plugin endpoints
@router.get("/peers/redirect/{plugin_name}")
async def redirect_to_plugin_peers(plugin_name: str, user = Depends(current_active_user)):
    """Get information about how to access a specific plugin's peer endpoints."""
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
                "clients": f"{api_prefix}/clients",
                "create_client": f"{api_prefix}/clients",
                "client_config": f"{api_prefix}/clients/{{client_id}}/config",
                "client_status": f"{api_prefix}/clients/{{client_id}}/status"
            },
            "plugin_info": plugin_info,
            "supports_clients": hasattr(target_plugin, 'list_clients'),
            "supports_config_generation": hasattr(target_plugin, 'generate_config')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin peer redirect info: {str(e)}")
