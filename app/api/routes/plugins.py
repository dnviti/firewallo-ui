"""Plugin management API routes."""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.plugins import plugin_manager


router = APIRouter()


class PluginActionResponse(BaseModel):
    """Response model for plugin actions."""
    success: bool
    message: str
    plugin_path: Optional[str] = None


class PluginDiscoveryResponse(BaseModel):
    """Response model for plugin discovery."""
    discovered_plugins: List[str]
    count: int


class PluginLoadResults(BaseModel):
    """Response model for plugin loading results."""
    results: Dict[str, bool]
    successful_count: int
    total_count: int
    failed_plugins: List[str]


@router.get("/", summary="List all loaded plugins")
async def list_plugins(
    category: Optional[str] = Query(None, description="Filter by plugin category"),
    enabled_only: bool = Query(False, description="Show only enabled plugins")
) -> Dict[str, Any]:
    """List all loaded plugins with optional filtering."""
    try:
        if enabled_only:
            plugins = plugin_manager.get_enabled_plugins(category=category)
            plugin_info = {plugin.name: plugin.get_info() for plugin in plugins}
        else:
            all_plugins = plugin_manager.get_plugin_info()
            if category:
                plugin_info = {
                    path: info for path, info in all_plugins.items()
                    if info.get('category') == category
                }
            else:
                plugin_info = all_plugins

        return {
            "plugins": plugin_info,
            "count": len(plugin_info),
            "stats": plugin_manager.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")


@router.get("/discover", response_model=PluginDiscoveryResponse, summary="Discover available plugins")
async def discover_plugins() -> PluginDiscoveryResponse:
    """Discover all available plugins in the plugin directory."""
    try:
        discovered = await plugin_manager.discover_plugins()
        return PluginDiscoveryResponse(
            discovered_plugins=discovered,
            count=len(discovered)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin discovery failed: {str(e)}")


@router.post("/load-all", response_model=PluginLoadResults, summary="Load all discovered plugins")
async def load_all_plugins(
    auto_enable: bool = Query(True, description="Automatically enable plugins after loading")
) -> PluginLoadResults:
    """Load all discovered plugins."""
    try:
        results = await plugin_manager.load_all_plugins(auto_enable=auto_enable)
        successful = [path for path, success in results.items() if success]
        failed = [path for path, success in results.items() if not success]

        return PluginLoadResults(
            results=results,
            successful_count=len(successful),
            total_count=len(results),
            failed_plugins=failed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load plugins: {str(e)}")


@router.post("/unload-all", response_model=PluginLoadResults, summary="Unload all loaded plugins")
async def unload_all_plugins() -> PluginLoadResults:
    """Unload all loaded plugins."""
    try:
        results = await plugin_manager.unload_all_plugins()
        successful = [path for path, success in results.items() if success]
        failed = [path for path, success in results.items() if not success]

        return PluginLoadResults(
            results=results,
            successful_count=len(successful),
            total_count=len(results),
            failed_plugins=failed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unload plugins: {str(e)}")


@router.get("/stats", summary="Get plugin manager statistics")
async def get_plugin_stats() -> Dict[str, Any]:
    """Get comprehensive plugin manager statistics."""
    try:
        return plugin_manager.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin stats: {str(e)}")


@router.get("/{plugin_path}", summary="Get plugin information")
async def get_plugin_info(plugin_path: str) -> Dict[str, Any]:
    """Get detailed information about a specific plugin."""
    try:
        info = plugin_manager.get_plugin_info(plugin_path)
        if not info:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_path}' not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin info: {str(e)}")


@router.get("/{plugin_path}/health", summary="Get plugin health status")
async def get_plugin_health(plugin_path: str) -> Dict[str, Any]:
    """Get health status of a specific plugin."""
    try:
        health = plugin_manager.get_plugin_health(plugin_path)
        if not health:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_path}' not found")
        return health
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin health: {str(e)}")


@router.post("/{plugin_path}/load", response_model=PluginActionResponse, summary="Load a specific plugin")
async def load_plugin(
    plugin_path: str,
    enable: bool = Query(True, description="Enable the plugin after loading")
) -> PluginActionResponse:
    """Load a specific plugin."""
    try:
        if plugin_manager.is_plugin_loaded(plugin_path):
            return PluginActionResponse(
                success=False,
                message=f"Plugin '{plugin_path}' is already loaded",
                plugin_path=plugin_path
            )

        success = await plugin_manager.load_plugin(plugin_path, enable=enable)
        return PluginActionResponse(
            success=success,
            message=f"Plugin '{plugin_path}' {'loaded successfully' if success else 'failed to load'}",
            plugin_path=plugin_path
        )
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to load plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )


@router.post("/{plugin_path}/unload", response_model=PluginActionResponse, summary="Unload a specific plugin")
async def unload_plugin(plugin_path: str) -> PluginActionResponse:
    """Unload a specific plugin."""
    try:
        if not plugin_manager.is_plugin_loaded(plugin_path):
            return PluginActionResponse(
                success=False,
                message=f"Plugin '{plugin_path}' is not loaded",
                plugin_path=plugin_path
            )

        success = await plugin_manager.unload_plugin(plugin_path)
        return PluginActionResponse(
            success=success,
            message=f"Plugin '{plugin_path}' {'unloaded successfully' if success else 'failed to unload'}",
            plugin_path=plugin_path
        )
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to unload plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )


@router.post("/{plugin_path}/enable", response_model=PluginActionResponse, summary="Enable a plugin")
async def enable_plugin(plugin_path: str) -> PluginActionResponse:
    """Enable a loaded plugin."""
    try:
        if not plugin_manager.is_plugin_loaded(plugin_path):
            return PluginActionResponse(
                success=False,
                message=f"Plugin '{plugin_path}' is not loaded",
                plugin_path=plugin_path
            )

        if plugin_manager.is_plugin_enabled(plugin_path):
            return PluginActionResponse(
                success=True,
                message=f"Plugin '{plugin_path}' is already enabled",
                plugin_path=plugin_path
            )

        success = await plugin_manager.enable_plugin(plugin_path)
        return PluginActionResponse(
            success=success,
            message=f"Plugin '{plugin_path}' {'enabled successfully' if success else 'failed to enable'}",
            plugin_path=plugin_path
        )
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to enable plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )


@router.post("/{plugin_path}/disable", response_model=PluginActionResponse, summary="Disable a plugin")
async def disable_plugin(plugin_path: str) -> PluginActionResponse:
    """Disable a loaded plugin."""
    try:
        if not plugin_manager.is_plugin_loaded(plugin_path):
            return PluginActionResponse(
                success=False,
                message=f"Plugin '{plugin_path}' is not loaded",
                plugin_path=plugin_path
            )

        if not plugin_manager.is_plugin_enabled(plugin_path):
            return PluginActionResponse(
                success=True,
                message=f"Plugin '{plugin_path}' is already disabled",
                plugin_path=plugin_path
            )

        success = await plugin_manager.disable_plugin(plugin_path)
        return PluginActionResponse(
            success=success,
            message=f"Plugin '{plugin_path}' {'disabled successfully' if success else 'failed to disable'}",
            plugin_path=plugin_path
        )
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to disable plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )


@router.post("/{plugin_path}/reload", response_model=PluginActionResponse, summary="Reload a plugin")
async def reload_plugin(plugin_path: str) -> PluginActionResponse:
    """Reload a plugin (unload and load again)."""
    try:
        if not plugin_manager.is_plugin_loaded(plugin_path):
            return PluginActionResponse(
                success=False,
                message=f"Plugin '{plugin_path}' is not loaded",
                plugin_path=plugin_path
            )

        success = await plugin_manager.reload_plugin(plugin_path)
        return PluginActionResponse(
            success=success,
            message=f"Plugin '{plugin_path}' {'reloaded successfully' if success else 'failed to reload'}",
            plugin_path=plugin_path
        )
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to reload plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )


@router.get("/{plugin_path}/routes", summary="Get plugin API routes")
async def get_plugin_routes(plugin_path: str) -> Dict[str, Any]:
    """Get API routes provided by a specific plugin."""
    try:
        plugin = plugin_manager.get_plugin(plugin_path)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_path}' not found")

        routes = plugin.get_api_routes()
        route_info = []

        for router in routes:
            for route in router.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    route_info.append({
                        "path": route.path,
                        "methods": list(route.methods),
                        "name": getattr(route, 'name', None),
                        "summary": getattr(route, 'summary', None)
                    })

        return {
            "plugin_path": plugin_path,
            "route_count": len(route_info),
            "routes": route_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin routes: {str(e)}")


@router.get("/{plugin_path}/config", summary="Get plugin configuration")
async def get_plugin_config(plugin_path: str) -> Dict[str, Any]:
    """Get configuration for a specific plugin."""
    try:
        plugin = plugin_manager.get_plugin(plugin_path)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_path}' not found")

        return {
            "plugin_path": plugin_path,
            "config": plugin.get_config(),
            "manifest_config": plugin.manifest.get('configuration', {}),
            "updated_at": plugin.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plugin config: {str(e)}")


@router.put("/{plugin_path}/config", response_model=PluginActionResponse, summary="Update plugin configuration")
async def update_plugin_config(plugin_path: str, config: Dict[str, Any]) -> PluginActionResponse:
    """Update configuration for a specific plugin."""
    try:
        plugin = plugin_manager.get_plugin(plugin_path)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{plugin_path}' not found")

        # Validate and set config
        plugin.set_config(config)

        return PluginActionResponse(
            success=True,
            message=f"Configuration updated for plugin '{plugin_path}'",
            plugin_path=plugin_path
        )
    except HTTPException:
        raise
    except Exception as e:
        return PluginActionResponse(
            success=False,
            message=f"Failed to update config for plugin '{plugin_path}': {str(e)}",
            plugin_path=plugin_path
        )
