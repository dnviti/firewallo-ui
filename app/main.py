"""ASGI entrypoint (API-only).

Business logic & routes moved to modular packages under app/.
No SQLite dependencies - using LiteDB or MongoDB for all data.
Frontend completely removed - API only.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from app.core.config import create_app
from app.core.startup import run_startup_tasks
from app.api.routes import auth, plugins, gui, system
from app.plugins import plugin_manager
import logging
import asyncio
from pathlib import Path
from typing import Optional


app = create_app()

# Setup logging for plugins
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("firewallo.main")

# Global flag to track if WebUI plugin is loaded
webui_plugin_loaded = False
webui_plugin_instance: Optional[object] = None

# Mount static files - will be overridden if WebUI plugin is loaded
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def _startup():
    """Application startup tasks."""
    run_startup_tasks()

    # Initialize plugin system
    logger.info("Initializing plugin system...")
    try:
        # Discover available plugins
        discovered = await plugin_manager.discover_plugins()
        logger.info(f"Discovered {len(discovered)} plugins: {discovered}")

        # Load all plugins
        load_results = await plugin_manager.load_all_plugins(auto_enable=True)
        successful_loads = sum(1 for success in load_results.values() if success)
        logger.info(f"Loaded {successful_loads}/{len(load_results)} plugins successfully")

        # Log any failures
        for plugin_path, success in load_results.items():
            if not success:
                logger.error(f"Failed to load plugin: {plugin_path}")

        # Check if WebUI plugin is loaded and configure accordingly
        await configure_webui_plugin()

    except Exception as e:
        logger.error(f"Plugin system initialization failed: {e}")


@app.on_event("shutdown")
async def _shutdown():
    """Application shutdown tasks."""
    logger.info("Shutting down plugin system...")
    try:
        # Unload all plugins gracefully
        unload_results = await plugin_manager.unload_all_plugins()
        successful_unloads = sum(1 for success in unload_results.values() if success)
        logger.info(f"Unloaded {successful_unloads}/{len(unload_results)} plugins successfully")
    except Exception as e:
        logger.error(f"Plugin system shutdown failed: {e}")


# API Router setup - Only manage /api paths
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(system.router, prefix="/system", tags=["system"])

# Include GUI routes only if WebUI plugin is not loaded
# (WebUI plugin will handle these routes if it's active)
if not webui_plugin_loaded:
    app.include_router(gui.router)

# Function to configure WebUI plugin if loaded
async def configure_webui_plugin():
    """Configure WebUI plugin if it's loaded."""
    global webui_plugin_loaded, webui_plugin_instance

    try:
        # Check if WebUI plugin is loaded
        enabled_plugins = plugin_manager.get_enabled_plugins()
        for plugin in enabled_plugins:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin_loaded = True
                webui_plugin_instance = plugin

                logger.info("WebUI plugin detected - configuring web interface...")

                # Mount WebUI static files if they exist
                if hasattr(plugin, 'static_dir') and plugin.static_dir.exists():
                    # Remove default static mount and replace with WebUI's
                    app.mount("/static", StaticFiles(directory=str(plugin.static_dir)), name="static")
                    logger.info(f"Mounted WebUI static files from {plugin.static_dir}")

                # Register WebUI routes
                plugin_routes = plugin.get_api_routes()
                if plugin_routes:
                    for router in plugin_routes:
                        # WebUI web routes go directly to app, API routes go to api_router
                        if hasattr(router, 'tags') and 'webui' in router.tags:
                            app.include_router(router)
                            logger.info("Registered WebUI web routes")
                        elif hasattr(router, 'tags') and 'webui-api' in router.tags:
                            # Already has prefix in the router definition
                            api_router.include_router(router)
                            logger.info("Registered WebUI API routes")

                logger.info("WebUI plugin configured successfully")
                break

    except Exception as e:
        logger.error(f"Failed to configure WebUI plugin: {e}")

# Function to register plugin routes dynamically
def register_plugin_routes():
    """Register routes from all enabled plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()
        registered_count = 0

        for plugin in enabled_plugins:
            try:
                # Skip WebUI plugin as it's handled separately
                if plugin.name == "webui" and plugin.category == "system":
                    continue

                # Get plugin routes
                plugin_routes = plugin.get_api_routes()
                if plugin_routes:
                    for router in plugin_routes:
                        # Include each router with plugin-specific prefix
                        api_prefix = getattr(plugin, 'manifest', {}).get('api_prefix')
                        if not api_prefix:
                            api_prefix = f"/{plugin.category}/{plugin.name}"

                        api_router.include_router(router, prefix=api_prefix, tags=[plugin.name])
                        registered_count += 1
                        logger.info(f"Registered routes for plugin {plugin.name} at {api_prefix}")
            except Exception as e:
                logger.error(f"Failed to register routes for plugin {plugin.name}: {e}")

        logger.info(f"Successfully registered routes from {registered_count} plugins")
        return registered_count
    except Exception as e:
        logger.error(f"Failed to register plugin routes: {e}")
        return 0

# Include only API router
app.include_router(api_router)

# Add route registration on startup (after plugins are loaded)
@app.on_event("startup")
async def register_routes():
    """Register plugin routes after plugins are loaded."""
    # Small delay to ensure plugins are fully loaded
    await asyncio.sleep(0.1)

    try:
        # Re-configure WebUI plugin in case it was loaded late
        await configure_webui_plugin()

        # If WebUI plugin is loaded and we had default GUI routes, remove them
        if webui_plugin_loaded:
            # The WebUI plugin will handle all web routes
            logger.info("WebUI plugin is active - using plugin-provided web interface")

        registered_count = register_plugin_routes()
        if registered_count > 0:
            logger.info(f"Plugin route registration completed: {registered_count} plugins")
        else:
            logger.warning("No plugin routes were registered (excluding WebUI)")
    except Exception as e:
        logger.error(f"Plugin route registration failed: {e}")
