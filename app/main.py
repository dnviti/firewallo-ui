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

# Function to configure WebUI plugin if loaded
async def configure_webui_plugin():
    """Configure WebUI plugin if it's loaded."""
    global webui_plugin_loaded, webui_plugin_instance

    try:
        # Initialize MenuService if WebUI plugin will be loaded
        from app.plugins.system.webui.services import MenuService
        await MenuService.initialize()

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
                        # Register all WebUI plugin routes to ensure authentication works
                        app.include_router(router)
                        logger.info(f"Registered WebUI routes: {router}")

                        # Also register API routes if they have specific tags
                        if hasattr(router, 'prefix') and router.prefix and '/api/' in router.prefix:
                            api_router.include_router(router)
                            logger.info("Registered WebUI API routes")

                logger.info("WebUI plugin configured successfully")
                break

    except Exception as e:
        logger.error(f"Failed to configure WebUI plugin: {e}")

# Function to register plugin routes dynamically
async def register_plugin_routes():
    """Register routes from all enabled plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()
        registered_count = 0
        webui_registered_count = 0

        for plugin in enabled_plugins:
            try:
                # Skip WebUI plugin as it's handled separately
                if plugin.name == "webui" and plugin.category == "system":
                    continue

                # Get plugin API routes
                plugin_routes = plugin.get_api_routes()
                if plugin_routes:
                    for router in plugin_routes:
                        # Include each router with plugin-specific prefix
                        api_prefix = getattr(plugin, 'manifest', {}).get('api_prefix')
                        if not api_prefix:
                            api_prefix = f"/{plugin.category}/{plugin.name}"

                        api_router.include_router(router, prefix=api_prefix, tags=[plugin.name])
                        registered_count += 1
                        logger.info(f"Registered API routes for plugin {plugin.name} at {api_prefix}")

                # Check if plugin has WebUI routes
                if hasattr(plugin, 'webui_enabled') and plugin.webui_enabled:
                    # Initialize plugin WebUI
                    if asyncio.iscoroutinefunction(plugin.initialize_webui):
                        await plugin.initialize_webui()
                    else:
                        plugin.initialize_webui()

                    # Get WebUI routes
                    webui_routes = plugin.get_webui_routes()
                    if webui_routes:
                        # Register WebUI routes at plugin-specific path
                        webui_path = plugin.webui_base_path or f"/plugins/{plugin.category}/{plugin.name}"
                        app.include_router(webui_routes, prefix=webui_path)
                        webui_registered_count += 1
                        logger.info(f"Registered WebUI routes for plugin {plugin.name} at {webui_path}")

                        # Mount static files if available
                        if hasattr(plugin, 'webui_static_path') and plugin.webui_static_path and plugin.webui_static_path.exists():
                            static_mount_path = f"{webui_path}/static"
                            app.mount(
                                static_mount_path,
                                StaticFiles(directory=str(plugin.webui_static_path)),
                                name=f"{plugin.name}_static"
                            )
                            plugin.webui_static_mounted = True
                            logger.info(f"Mounted static files for {plugin.name} at {static_mount_path}")

            except Exception as e:
                logger.error(f"Failed to register routes for plugin {plugin.name}: {e}")

        logger.info(f"Successfully registered API routes from {registered_count} plugins")
        if webui_registered_count > 0:
            logger.info(f"Successfully registered WebUI routes from {webui_registered_count} plugins")
        return registered_count + webui_registered_count
    except Exception as e:
        logger.error(f"Failed to register plugin routes: {e}")
        return 0

# Include API router first (higher priority)
app.include_router(api_router)

# Include GUI routes with session-based authentication (lower priority)
# Note: Plugin routes will be registered during startup to take precedence
if not webui_plugin_loaded:
    app.include_router(gui.router)

# Test endpoint to verify our changes are loaded
@app.get("/test-plugin-webui")
async def test_plugin_webui():
    """Test endpoint to verify plugin WebUI framework is loaded."""
    return {
        "status": "Plugin WebUI framework loaded",
        "webui_plugin_loaded": webui_plugin_loaded,
        "has_webui_instance": webui_plugin_instance is not None,
        "timestamp": "2025-08-15T01:37:00Z"
    }

# Manual menu registration endpoint
@app.get("/trigger-menu-registration")
async def trigger_menu_registration():
    """Manually trigger menu registration for all plugins."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()
        registration_results = []

        for plugin in enabled_plugins:
            if getattr(plugin, 'webui_enabled', False):
                try:
                    result = await plugin.register_menu_entry()
                    registration_results.append({
                        "plugin": f"{plugin.category}.{plugin.name}",
                        "success": result,
                        "menu_registered": getattr(plugin, 'menu_entry_registered', False)
                    })
                except Exception as e:
                    registration_results.append({
                        "plugin": f"{plugin.category}.{plugin.name}",
                        "success": False,
                        "error": str(e)
                    })

        return {
            "status": "Menu registration triggered",
            "results": registration_results,
            "total_plugins": len(enabled_plugins)
        }
    except Exception as e:
        return {
            "status": "Error triggering menu registration",
            "error": str(e)
        }

# Endpoint to check current menu entries
@app.get("/check-menu-entries")
async def check_menu_entries():
    """Check current menu entries registered in MenuService."""
    try:
        from app.plugins.system.webui.services import MenuService

        # Initialize if needed
        if not getattr(MenuService, '_initialized', False):
            await MenuService.initialize()

        menu_entries = await MenuService.get_menu_entries()

        return {
            "status": "Menu entries retrieved",
            "total_entries": len(menu_entries),
            "entries": menu_entries,
            "raw_entries": MenuService._menu_entries,
            "menu_order": MenuService._menu_order
        }
    except Exception as e:
        return {
            "status": "Error retrieving menu entries",
            "error": str(e)
        }

# Test navigation context endpoint
@app.get("/test-navigation-context")
async def test_navigation_context():
    """Test endpoint to check navigation context generation."""
    try:
        from app.plugins.system.webui.auth_deps import get_navigation_context
        from app.auth.models import User

        # Create a test user
        test_user = User({
            "username": "admin",
            "email": "admin@test.com",
            "is_active": True,
            "is_superuser": True,
            "role": "admin"
        })

        # Get navigation context
        nav_context = await get_navigation_context(test_user)

        return {
            "status": "Navigation context retrieved",
            "context": nav_context,
            "plugin_menus_count": len(nav_context.get("plugin_menus", [])),
            "navigation_count": len(nav_context.get("navigation", []))
        }
    except Exception as e:
        return {
            "status": "Error getting navigation context",
            "error": str(e)
        }

# Debug MenuService step by step
@app.get("/debug-menu-service")
async def debug_menu_service():
    """Debug MenuService step by step."""
    debug_info = {}

    try:
        # Step 1: Import MenuService
        from app.plugins.system.webui.services import MenuService
        debug_info["step1_import"] = "✅ MenuService imported successfully"

        # Step 2: Check initialization
        debug_info["step2_initialized"] = getattr(MenuService, '_initialized', False)

        # Step 3: Initialize if needed
        if not debug_info["step2_initialized"]:
            await MenuService.initialize()
            debug_info["step3_init_result"] = "✅ MenuService initialized"
        else:
            debug_info["step3_init_result"] = "✅ Already initialized"

        # Step 4: Check raw entries
        debug_info["step4_raw_entries"] = MenuService._menu_entries
        debug_info["step4_menu_order"] = MenuService._menu_order

        # Step 5: Get menu entries without permissions
        entries_no_perms = await MenuService.get_menu_entries(None)
        debug_info["step5_entries_no_perms"] = entries_no_perms

        # Step 6: Get menu entries with admin permissions
        admin_perms = ["vpn.wireguard.view", "admin.all", "*"]
        entries_with_perms = await MenuService.get_menu_entries(admin_perms)
        debug_info["step6_entries_with_perms"] = entries_with_perms

        return {
            "status": "MenuService debug completed",
            "debug_info": debug_info
        }

    except Exception as e:
        debug_info["error"] = str(e)
        import traceback
        debug_info["traceback"] = traceback.format_exc()
        return {
            "status": "MenuService debug failed",
            "debug_info": debug_info
        }

# Test navigation context with permission scenarios
@app.get("/debug-nav-context-permissions")
async def debug_nav_context_permissions():
    """Test navigation context with different permission scenarios."""
    try:
        from app.plugins.system.webui.auth_deps import get_navigation_context
        from app.auth.models import User

        results = {}

        # Test 1: User with no permissions
        user_no_perms = User({
            "username": "testuser",
            "email": "test@test.com",
            "is_active": True,
            "is_superuser": False,
            "role": "user"
        })
        nav_context_no_perms = await get_navigation_context(user_no_perms)
        results["test1_no_perms"] = {
            "plugin_menus_count": len(nav_context_no_perms.get("plugin_menus", [])),
            "plugin_menus": nav_context_no_perms.get("plugin_menus", [])
        }

        # Test 2: User with vpn.wireguard.view permission
        user_with_perms = User({
            "username": "vipuser",
            "email": "vip@test.com",
            "is_active": True,
            "is_superuser": False,
            "role": "user",
            "permissions": ["vpn.wireguard.view"]
        })
        nav_context_with_perms = await get_navigation_context(user_with_perms)
        results["test2_with_perms"] = {
            "plugin_menus_count": len(nav_context_with_perms.get("plugin_menus", [])),
            "plugin_menus": nav_context_with_perms.get("plugin_menus", [])
        }

        # Test 3: Super user
        super_user = User({
            "username": "admin",
            "email": "admin@test.com",
            "is_active": True,
            "is_superuser": True,
            "role": "admin"
        })
        nav_context_super = await get_navigation_context(super_user)
        results["test3_super_user"] = {
            "plugin_menus_count": len(nav_context_super.get("plugin_menus", [])),
            "plugin_menus": nav_context_super.get("plugin_menus", [])
        }

        return {
            "status": "Navigation context permission tests completed",
            "results": results
        }

    except Exception as e:
        import traceback
        return {
            "status": "Error testing navigation context permissions",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Test MenuService with empty list vs None
@app.get("/debug-menu-permissions")
async def debug_menu_permissions():
    """Test MenuService with different permission scenarios."""
    try:
        from app.plugins.system.webui.services import MenuService

        # Ensure MenuService is initialized
        if not getattr(MenuService, '_initialized', False):
            await MenuService.initialize()

        results = {}

        # Test 1: Call with None (should return all entries)
        entries_none = await MenuService.get_menu_entries(None)
        results["test1_none_permissions"] = {
            "count": len(entries_none),
            "entries": entries_none
        }

        # Test 2: Call with empty list (should filter out entries with permissions)
        entries_empty = await MenuService.get_menu_entries([])
        results["test2_empty_list"] = {
            "count": len(entries_empty),
            "entries": entries_empty
        }

        # Test 3: Call with correct permission
        entries_correct = await MenuService.get_menu_entries(["vpn.wireguard.view"])
        results["test3_correct_permission"] = {
            "count": len(entries_correct),
            "entries": entries_correct
        }

        # Test 4: Call with admin permissions
        entries_admin = await MenuService.get_menu_entries(["admin.*", "*"])
        results["test4_admin_permissions"] = {
            "count": len(entries_admin),
            "entries": entries_admin
        }

        return {
            "status": "MenuService permission tests completed",
            "results": results
        }

    except Exception as e:
        import traceback
        return {
            "status": "Error testing MenuService permissions",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Debug endpoint to check plugin WebUI status
@app.get("/debug-plugin-webui")
async def debug_plugin_webui():
    """Debug endpoint to check plugin WebUI registration status."""
    try:
        enabled_plugins = plugin_manager.get_enabled_plugins()
        plugin_info = []

        for plugin in enabled_plugins:
            info = {
                "name": plugin.name,
                "category": plugin.category,
                "webui_enabled": getattr(plugin, 'webui_enabled', False),
                "has_webui_router": getattr(plugin, 'webui_router', None) is not None,
                "webui_base_path": getattr(plugin, 'webui_base_path', None),
                "menu_registered": getattr(plugin, 'menu_entry_registered', False),
                "static_mounted": getattr(plugin, 'webui_static_mounted', False)
            }

            # Get manifest webui config if available
            if hasattr(plugin, 'manifest') and plugin.manifest:
                webui_config = plugin.manifest.get('webui', {})
                info['manifest_webui_enabled'] = webui_config.get('enabled', False)
                info['manifest_menu_title'] = webui_config.get('menu_entry', {}).get('title', 'N/A')

            plugin_info.append(info)

        return {
            "status": "Debug info collected",
            "total_plugins": len(enabled_plugins),
            "plugins": plugin_info,
            "app_routes": [str(route.path) for route in app.routes if hasattr(route, 'path')]
        }
    except Exception as e:
        return {
            "status": "Error collecting debug info",
            "error": str(e)
        }

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
        else:
            logger.warning("WebUI plugin not loaded - web interface may not have authentication!")

        registered_count = await register_plugin_routes()
        if registered_count > 0:
            logger.info(f"Plugin route registration completed: {registered_count} plugins")
        else:
            logger.warning("No plugin routes were registered (excluding WebUI)")
    except Exception as e:
        logger.error(f"Plugin route registration failed: {e}")
