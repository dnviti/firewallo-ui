#!/usr/bin/env python3
"""
Integration tests for WebUI Plugin with the Firewallo plugin framework.
Tests plugin manager integration, loading/unloading, and system-wide functionality.
"""

import sys
import os
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, List
import importlib.util

# Add paths for testing
plugin_dir = Path(__file__).parent.parent
app_dir = plugin_dir.parent.parent.parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plugin_dir))


@pytest.mark.asyncio
class TestWebUIPluginManagerIntegration:
    """Test WebUI plugin integration with the plugin manager."""

    def setup_method(self):
        """Setup test environment."""
        from app.plugins.registry import plugin_manager
        self.plugin_manager = plugin_manager
        self.webui_plugin_path = "system.webui"

    async def test_plugin_discovery(self):
        """Test that WebUI plugin is discovered by plugin manager."""
        discovered = await self.plugin_manager.discover_plugins()

        assert isinstance(discovered, list), "Discovery should return a list"
        assert len(discovered) > 0, "Should discover at least one plugin"

        # Check if WebUI plugin was discovered
        webui_found = False
        for plugin_path in discovered:
            if "webui" in plugin_path and "system" in plugin_path:
                webui_found = True
                break

        assert webui_found, "WebUI plugin should be discovered by plugin manager"

    async def test_plugin_loading(self):
        """Test that WebUI plugin can be loaded via plugin manager."""
        # First ensure it's discovered
        await self.plugin_manager.discover_plugins()

        # Load the plugin
        success = await self.plugin_manager.load_plugin(self.webui_plugin_path)

        assert success is True, "WebUI plugin should load successfully"

        # Verify it's in enabled plugins
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be in enabled plugins"
        assert webui_plugin._initialized is True, "WebUI plugin should be initialized"

    async def test_plugin_unloading(self):
        """Test that WebUI plugin can be unloaded via plugin manager."""
        # First load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin(self.webui_plugin_path)

        # Now unload it
        success = await self.plugin_manager.unload_plugin(self.webui_plugin_path)

        assert success is True, "WebUI plugin should unload successfully"

        # Verify it's no longer in enabled plugins
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_found = False

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_found = True
                break

        assert webui_found is False, "WebUI plugin should not be in enabled plugins after unload"

    async def test_plugin_reload(self):
        """Test that WebUI plugin can be reloaded via plugin manager."""
        # Load, unload, then load again
        await self.plugin_manager.discover_plugins()

        # First load
        success1 = await self.plugin_manager.load_plugin(self.webui_plugin_path)
        assert success1 is True, "First load should succeed"

        # Unload
        success2 = await self.plugin_manager.unload_plugin(self.webui_plugin_path)
        assert success2 is True, "Unload should succeed"

        # Reload
        success3 = await self.plugin_manager.load_plugin(self.webui_plugin_path)
        assert success3 is True, "Reload should succeed"

        # Verify it's working after reload
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be available after reload"
        assert webui_plugin._initialized is True, "WebUI plugin should be initialized after reload"

    async def test_plugin_auto_loading(self):
        """Test WebUI plugin auto-loading functionality."""
        # Test loading all plugins (which should include WebUI)
        load_results = await self.plugin_manager.load_all_plugins(auto_enable=True)

        assert isinstance(load_results, dict), "Load results should be a dictionary"

        # Check if WebUI was loaded
        webui_loaded = False
        for plugin_path, success in load_results.items():
            if "webui" in plugin_path and "system" in plugin_path:
                webui_loaded = success
                break

        assert webui_loaded is True, "WebUI plugin should be loaded automatically"

    async def test_plugin_manifest_validation(self):
        """Test that WebUI plugin manifest passes validation."""
        # This is implicitly tested during loading, but let's be explicit
        await self.plugin_manager.discover_plugins()

        try:
            success = await self.plugin_manager.load_plugin(self.webui_plugin_path)
            assert success is True, "Plugin should load if manifest is valid"
        except Exception as e:
            pytest.fail(f"Plugin manifest validation failed: {e}")

    async def test_plugin_dependencies(self):
        """Test WebUI plugin dependency handling."""
        # Load the plugin and check if dependencies are satisfied
        await self.plugin_manager.discover_plugins()
        success = await self.plugin_manager.load_plugin(self.webui_plugin_path)

        assert success is True, "Plugin should load if dependencies are satisfied"

        # Get the loaded plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Check that required imports work (dependencies are available)
        try:
            # These should all be available if dependencies are met
            import fastapi
            import jinja2
            import psutil
            import aiofiles
            assert True, "All required dependencies should be available"
        except ImportError as e:
            pytest.fail(f"Required dependency not available: {e}")


@pytest.mark.asyncio
class TestWebUIPluginSystemIntegration:
    """Test WebUI plugin integration with the broader system."""

    def setup_method(self):
        """Setup test environment."""
        from app.plugins.registry import plugin_manager
        self.plugin_manager = plugin_manager

    async def test_plugin_routes_integration(self):
        """Test that WebUI plugin routes integrate properly."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test route retrieval
        routes = webui_plugin.get_api_routes()
        assert len(routes) > 0, "Plugin should provide routes"

        # Check route structure
        for router in routes:
            assert hasattr(router, 'routes'), "Router should have routes"
            assert len(router.routes) > 0, "Router should have at least one route"

    async def test_plugin_database_integration(self):
        """Test that WebUI plugin database schema integrates properly."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test database schema
        schema = webui_plugin.get_database_schema()
        assert isinstance(schema, dict), "Schema should be a dictionary"
        assert "collections" in schema, "Schema should define collections"

        # Verify collections are properly namespaced
        collections = schema["collections"]
        for collection_name in collections.keys():
            assert "webui" in collection_name, "Collections should be namespaced to webui"

    async def test_plugin_configuration_integration(self):
        """Test WebUI plugin configuration integration."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test configuration handling
        current_config = webui_plugin.get_config()
        assert isinstance(current_config, dict), "Config should be a dictionary"

        # Test configuration update
        test_config = current_config.copy()
        test_config["auto_refresh_interval"] = 120

        webui_plugin.update_config({"auto_refresh_interval": 120})
        updated_config = webui_plugin.get_config()

        assert updated_config["auto_refresh_interval"] == 120, "Configuration should be updated"

    async def test_plugin_health_monitoring_integration(self):
        """Test WebUI plugin health monitoring integration."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test health status
        health = webui_plugin.get_health_status()
        assert health["status"] == "healthy", "Plugin should be healthy after loading"

        # Test metrics
        metrics = webui_plugin.get_metrics()
        assert isinstance(metrics, dict), "Metrics should be a dictionary"
        assert "uptime_seconds" in metrics, "Metrics should include uptime"

    async def test_plugin_error_handling(self):
        """Test WebUI plugin error handling and recovery."""
        # Test loading with invalid configuration
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test error logging
        initial_error_count = webui_plugin._error_count

        # Trigger an error by setting invalid config
        webui_plugin.log_error("Test error", Exception("Test exception"))

        assert webui_plugin._error_count > initial_error_count, "Error count should increase"
        assert webui_plugin._last_error is not None, "Last error should be recorded"

    async def test_plugin_concurrent_operations(self):
        """Test WebUI plugin handling of concurrent operations."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Test concurrent health checks
        async def get_health():
            return webui_plugin.get_health_status()

        # Run multiple concurrent health checks
        tasks = [get_health() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10, "All concurrent operations should complete"
        for result in results:
            assert isinstance(result, dict), "Each result should be a valid health status"

    async def test_plugin_resource_cleanup(self):
        """Test WebUI plugin resource cleanup on shutdown."""
        # Load the plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Get the plugin
        enabled = self.plugin_manager.get_enabled_plugins()
        webui_plugin = None

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_plugin = plugin
                break

        assert webui_plugin is not None, "WebUI plugin should be loaded"

        # Check initial state
        assert webui_plugin._initialized is True, "Plugin should be initialized"

        # Record initial metrics
        initial_metrics = webui_plugin.get_metrics()

        # Shutdown the plugin
        await webui_plugin.shutdown()

        # Verify cleanup
        assert webui_plugin._initialized is False, "Plugin should be marked as not initialized"
        assert webui_plugin._shutdown_time is not None, "Shutdown time should be recorded"


@pytest.mark.asyncio
class TestWebUIPluginPerformance:
    """Test WebUI plugin performance characteristics."""

    def setup_method(self):
        """Setup test environment."""
        from app.plugins.registry import plugin_manager
        self.plugin_manager = plugin_manager

    async def test_plugin_load_time(self):
        """Test WebUI plugin loading performance."""
        import time

        await self.plugin_manager.discover_plugins()

        start_time = time.time()
        success = await self.plugin_manager.load_plugin("system.webui")
        load_time = time.time() - start_time

        assert success is True, "Plugin should load successfully"
        assert load_time < 5.0, "Plugin should load within 5 seconds"

    async def test_plugin_initialization_time(self):
        """Test WebUI plugin initialization performance."""
        import time
        from plugin import WebUIPlugin

        plugin = WebUIPlugin()

        start_time = time.time()
        result = await plugin.initialize()
        init_time = time.time() - start_time

        assert result is True, "Plugin should initialize successfully"
        assert init_time < 3.0, "Plugin should initialize within 3 seconds"

        await plugin.shutdown()

    async def test_plugin_route_generation_time(self):
        """Test WebUI plugin route generation performance."""
        import time
        from plugin import WebUIPlugin

        plugin = WebUIPlugin()
        await plugin.initialize()

        start_time = time.time()
        routes = plugin.get_api_routes()
        route_time = time.time() - start_time

        assert len(routes) > 0, "Plugin should provide routes"
        assert route_time < 1.0, "Route generation should complete within 1 second"

        await plugin.shutdown()

    async def test_plugin_memory_usage(self):
        """Test WebUI plugin memory usage characteristics."""
        import psutil
        import gc

        # Get baseline memory
        gc.collect()
        process = psutil.Process()
        baseline_memory = process.memory_info().rss

        # Load plugin
        await self.plugin_manager.discover_plugins()
        await self.plugin_manager.load_plugin("system.webui")

        # Check memory after loading
        gc.collect()
        loaded_memory = process.memory_info().rss
        memory_increase = (loaded_memory - baseline_memory) / 1024 / 1024  # MB

        # Plugin should not use excessive memory
        assert memory_increase < 50.0, f"Plugin should use less than 50MB, used {memory_increase:.2f}MB"

        # Unload and check memory cleanup
        await self.plugin_manager.unload_plugin("system.webui")
        gc.collect()

        unloaded_memory = process.memory_info().rss
        memory_after_unload = (unloaded_memory - baseline_memory) / 1024 / 1024

        # Should free most memory (allow some overhead)
        assert memory_after_unload < memory_increase * 0.5, "Plugin should free most memory on unload"


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
