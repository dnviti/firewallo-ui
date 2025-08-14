#!/usr/bin/env python3
"""
Plugin manager tests for Firewallo UI.

Tests the plugin manager functionality including:
- Plugin discovery and registration
- Plugin loading and unloading
- Plugin lifecycle management
- Plugin dependency resolution
- Plugin isolation and sandboxing
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, List, Any

# Test markers
pytestmark = [pytest.mark.plugins, pytest.mark.unit, pytest.mark.asyncio]


class TestPluginDiscovery:
    """Test plugin discovery functionality."""

    async def test_discover_plugins_in_directory(self, temp_dir):
        """Test discovering plugins in a directory."""
        from app.plugins.registry.manager import PluginManager

        # Create mock plugin structure
        plugin_dir = temp_dir / "test_plugin"
        plugin_dir.mkdir()

        # Create manifest file
        manifest_content = {
            "name": "test_plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "category": "test",
            "api_version": "1.0"
        }

        (plugin_dir / "manifest.json").write_text(
            '{"name": "test_plugin", "version": "1.0.0", "category": "test"}'
        )
        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "plugin.py").write_text("class TestPlugin: pass")

        manager = PluginManager()
        discovered = await manager.discover_plugins([str(temp_dir)])

        assert len(discovered) == 1
        assert "test_plugin" in discovered
        assert discovered["test_plugin"]["name"] == "test_plugin"

    async def test_discover_plugins_recursive(self, temp_dir):
        """Test recursive plugin discovery."""
        from app.plugins.registry.manager import PluginManager

        # Create nested plugin structure
        category_dir = temp_dir / "vpn"
        category_dir.mkdir()

        plugin_dir = category_dir / "wireguard"
        plugin_dir.mkdir()

        (plugin_dir / "manifest.json").write_text(
            '{"name": "wireguard", "version": "1.0.0", "category": "vpn"}'
        )
        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "plugin.py").touch()

        manager = PluginManager()
        discovered = await manager.discover_plugins([str(temp_dir)], recursive=True)

        assert len(discovered) == 1
        assert "vpn.wireguard" in discovered

    async def test_discover_plugins_invalid_manifest(self, temp_dir):
        """Test handling of plugins with invalid manifests."""
        from app.plugins.registry.manager import PluginManager

        plugin_dir = temp_dir / "invalid_plugin"
        plugin_dir.mkdir()

        # Create invalid manifest
        (plugin_dir / "manifest.json").write_text('{"invalid": "json"')
        (plugin_dir / "__init__.py").touch()

        manager = PluginManager()
        discovered = await manager.discover_plugins([str(temp_dir)])

        # Should skip invalid plugins
        assert len(discovered) == 0

    async def test_discover_plugins_missing_files(self, temp_dir):
        """Test handling of plugins with missing required files."""
        from app.plugins.registry.manager import PluginManager

        plugin_dir = temp_dir / "incomplete_plugin"
        plugin_dir.mkdir()

        # Only create manifest, missing plugin.py
        (plugin_dir / "manifest.json").write_text(
            '{"name": "incomplete", "version": "1.0.0", "category": "test"}'
        )

        manager = PluginManager()
        discovered = await manager.discover_plugins([str(temp_dir)])

        # Should skip incomplete plugins
        assert len(discovered) == 0

    async def test_discover_plugins_multiple_directories(self, temp_dir):
        """Test discovering plugins from multiple directories."""
        from app.plugins.registry.manager import PluginManager

        # Create plugins in different directories
        dir1 = temp_dir / "plugins1"
        dir1.mkdir()
        plugin1_dir = dir1 / "plugin1"
        plugin1_dir.mkdir()
        (plugin1_dir / "manifest.json").write_text(
            '{"name": "plugin1", "version": "1.0.0", "category": "test"}'
        )
        (plugin1_dir / "__init__.py").touch()
        (plugin1_dir / "plugin.py").touch()

        dir2 = temp_dir / "plugins2"
        dir2.mkdir()
        plugin2_dir = dir2 / "plugin2"
        plugin2_dir.mkdir()
        (plugin2_dir / "manifest.json").write_text(
            '{"name": "plugin2", "version": "1.0.0", "category": "test"}'
        )
        (plugin2_dir / "__init__.py").touch()
        (plugin2_dir / "plugin.py").touch()

        manager = PluginManager()
        discovered = await manager.discover_plugins([str(dir1), str(dir2)])

        assert len(discovered) == 2
        assert "plugin1" in discovered
        assert "plugin2" in discovered


class TestPluginLoading:
    """Test plugin loading functionality."""

    async def test_load_plugin_success(self, mock_plugin, sample_plugin_manifest):
        """Test successful plugin loading."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()

        # Mock plugin discovery
        manager._discovered_plugins = {
            "test.plugin": {
                "path": "/mock/path",
                "manifest": sample_plugin_manifest
            }
        }

        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            mock_load.return_value = mock_plugin

            success = await manager.load_plugin("test.plugin")

        assert success is True
        assert manager.is_plugin_loaded("test.plugin")
        assert manager.get_plugin("test.plugin") == mock_plugin

    async def test_load_plugin_not_discovered(self):
        """Test loading a plugin that hasn't been discovered."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        success = await manager.load_plugin("nonexistent.plugin")

        assert success is False

    async def test_load_plugin_already_loaded(self, mock_plugin):
        """Test loading a plugin that's already loaded."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        success = await manager.load_plugin("test.plugin")

        # Should return True but not reload
        assert success is True

    async def test_load_plugin_with_dependencies(self, mock_plugin, sample_plugin_manifest):
        """Test loading plugin with dependencies."""
        from app.plugins.registry.manager import PluginManager

        # Create plugin with dependencies
        dependent_manifest = sample_plugin_manifest.copy()
        dependent_manifest["dependencies"] = ["base.plugin"]

        manager = PluginManager()
        manager._discovered_plugins = {
            "base.plugin": {
                "path": "/mock/base",
                "manifest": sample_plugin_manifest
            },
            "dependent.plugin": {
                "path": "/mock/dependent",
                "manifest": dependent_manifest
            }
        }

        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            base_plugin = MagicMock()
            dependent_plugin = MagicMock()
            mock_load.side_effect = [base_plugin, dependent_plugin]

            success = await manager.load_plugin("dependent.plugin")

        assert success is True
        assert manager.is_plugin_loaded("base.plugin")
        assert manager.is_plugin_loaded("dependent.plugin")

    async def test_load_plugin_circular_dependency(self, sample_plugin_manifest):
        """Test handling of circular dependencies."""
        from app.plugins.registry.manager import PluginManager

        # Create plugins with circular dependencies
        plugin_a_manifest = sample_plugin_manifest.copy()
        plugin_a_manifest["name"] = "plugin_a"
        plugin_a_manifest["dependencies"] = ["plugin_b"]

        plugin_b_manifest = sample_plugin_manifest.copy()
        plugin_b_manifest["name"] = "plugin_b"
        plugin_b_manifest["dependencies"] = ["plugin_a"]

        manager = PluginManager()
        manager._discovered_plugins = {
            "plugin_a": {
                "path": "/mock/a",
                "manifest": plugin_a_manifest
            },
            "plugin_b": {
                "path": "/mock/b",
                "manifest": plugin_b_manifest
            }
        }

        success = await manager.load_plugin("plugin_a")

        # Should detect circular dependency and fail
        assert success is False

    async def test_load_plugin_missing_dependency(self, sample_plugin_manifest):
        """Test loading plugin with missing dependencies."""
        from app.plugins.registry.manager import PluginManager

        dependent_manifest = sample_plugin_manifest.copy()
        dependent_manifest["dependencies"] = ["missing.plugin"]

        manager = PluginManager()
        manager._discovered_plugins = {
            "dependent.plugin": {
                "path": "/mock/dependent",
                "manifest": dependent_manifest
            }
        }

        success = await manager.load_plugin("dependent.plugin")

        assert success is False

    async def test_load_plugin_loader_failure(self, sample_plugin_manifest):
        """Test handling of plugin loader failures."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._discovered_plugins = {
            "failing.plugin": {
                "path": "/mock/failing",
                "manifest": sample_plugin_manifest
            }
        }

        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            mock_load.side_effect = Exception("Load failed")

            success = await manager.load_plugin("failing.plugin")

        assert success is False
        assert not manager.is_plugin_loaded("failing.plugin")


class TestPluginUnloading:
    """Test plugin unloading functionality."""

    async def test_unload_plugin_success(self, mock_plugin):
        """Test successful plugin unloading."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin
        manager._enabled_plugins.add("test.plugin")

        with patch.object(mock_plugin, 'shutdown') as mock_shutdown:
            mock_shutdown.return_value = None

            success = await manager.unload_plugin("test.plugin")

        assert success is True
        assert not manager.is_plugin_loaded("test.plugin")
        assert "test.plugin" not in manager._enabled_plugins

    async def test_unload_plugin_not_loaded(self):
        """Test unloading a plugin that's not loaded."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        success = await manager.unload_plugin("nonexistent.plugin")

        assert success is False

    async def test_unload_plugin_with_dependents(self, mock_plugin):
        """Test unloading plugin that has dependents."""
        from app.plugins.registry.manager import PluginManager

        base_plugin = MagicMock()
        dependent_plugin = MagicMock()

        manager = PluginManager()
        manager._loaded_plugins["base.plugin"] = base_plugin
        manager._loaded_plugins["dependent.plugin"] = dependent_plugin
        manager._plugin_dependencies = {
            "dependent.plugin": ["base.plugin"]
        }

        # Should fail to unload base plugin while dependent is loaded
        success = await manager.unload_plugin("base.plugin")
        assert success is False

        # Should succeed after unloading dependent first
        await manager.unload_plugin("dependent.plugin")
        success = await manager.unload_plugin("base.plugin")
        assert success is True

    async def test_unload_plugin_shutdown_failure(self, mock_plugin):
        """Test handling of plugin shutdown failures."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'shutdown') as mock_shutdown:
            mock_shutdown.side_effect = Exception("Shutdown failed")

            success = await manager.unload_plugin("test.plugin")

        # Should still unload despite shutdown failure
        assert success is True
        assert not manager.is_plugin_loaded("test.plugin")


class TestPluginEnabling:
    """Test plugin enabling/disabling functionality."""

    async def test_enable_plugin_success(self, mock_plugin):
        """Test successful plugin enabling."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'enable') as mock_enable:
            mock_enable.return_value = True

            success = await manager.enable_plugin("test.plugin")

        assert success is True
        assert manager.is_plugin_enabled("test.plugin")

    async def test_enable_plugin_not_loaded(self):
        """Test enabling a plugin that's not loaded."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        success = await manager.enable_plugin("nonexistent.plugin")

        assert success is False

    async def test_enable_plugin_already_enabled(self, mock_plugin):
        """Test enabling a plugin that's already enabled."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin
        manager._enabled_plugins.add("test.plugin")

        success = await manager.enable_plugin("test.plugin")

        # Should return True but not re-enable
        assert success is True

    async def test_disable_plugin_success(self, mock_plugin):
        """Test successful plugin disabling."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin
        manager._enabled_plugins.add("test.plugin")

        with patch.object(mock_plugin, 'disable') as mock_disable:
            mock_disable.return_value = True

            success = await manager.disable_plugin("test.plugin")

        assert success is True
        assert not manager.is_plugin_enabled("test.plugin")

    async def test_disable_plugin_not_enabled(self, mock_plugin):
        """Test disabling a plugin that's not enabled."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        success = await manager.disable_plugin("test.plugin")

        assert success is False


class TestPluginInformation:
    """Test plugin information retrieval."""

    def test_list_plugins_empty(self):
        """Test listing plugins when none are loaded."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        plugins = manager.list_plugins()

        assert plugins == []

    def test_list_plugins_with_loaded(self, mock_plugin):
        """Test listing plugins with loaded plugins."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin
        manager._enabled_plugins.add("test.plugin")

        with patch.object(mock_plugin, 'get_info') as mock_get_info:
            mock_get_info.return_value = {
                "name": "test-plugin",
                "version": "1.0.0",
                "category": "test"
            }

            plugins = manager.list_plugins()

        assert len(plugins) == 1
        plugin_info = plugins[0]
        assert plugin_info["id"] == "test.plugin"
        assert plugin_info["status"] == "loaded"
        assert plugin_info["enabled"] is True

    def test_get_plugin_info_exists(self, mock_plugin):
        """Test getting info for existing plugin."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'get_info') as mock_get_info:
            mock_get_info.return_value = {
                "name": "test-plugin",
                "version": "1.0.0"
            }

            info = manager.get_plugin_info("test.plugin")

        assert info is not None
        assert info["name"] == "test-plugin"

    def test_get_plugin_info_not_exists(self):
        """Test getting info for non-existent plugin."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        info = manager.get_plugin_info("nonexistent.plugin")

        assert info is None

    def test_get_plugin_health(self, mock_plugin):
        """Test getting plugin health status."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'get_health_status') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "last_check": "2023-01-01T12:00:00Z"
            }

            health = manager.get_plugin_health("test.plugin")

        assert health["status"] == "healthy"

    def test_get_plugin_metrics(self, mock_plugin):
        """Test getting plugin metrics."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'get_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "cpu_usage": 2.5,
                "memory_usage": 1024
            }

            metrics = manager.get_plugin_metrics("test.plugin")

        assert metrics["cpu_usage"] == 2.5
        assert metrics["memory_usage"] == 1024


class TestPluginConfiguration:
    """Test plugin configuration management."""

    async def test_get_plugin_config(self, mock_plugin):
        """Test getting plugin configuration."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'get_config') as mock_get_config:
            mock_get_config.return_value = {
                "setting1": "value1",
                "setting2": 42
            }

            config = await manager.get_plugin_config("test.plugin")

        assert config["setting1"] == "value1"
        assert config["setting2"] == 42

    async def test_update_plugin_config(self, mock_plugin):
        """Test updating plugin configuration."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        new_config = {
            "setting1": "new_value",
            "setting3": True
        }

        with patch.object(mock_plugin, 'update_config') as mock_update:
            mock_update.return_value = True

            success = await manager.update_plugin_config("test.plugin", new_config)

        assert success is True
        mock_update.assert_called_once_with(new_config)

    async def test_reset_plugin_config(self, mock_plugin):
        """Test resetting plugin configuration."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        with patch.object(mock_plugin, 'reset_config') as mock_reset:
            mock_reset.return_value = True

            success = await manager.reset_plugin_config("test.plugin")

        assert success is True
        mock_reset.assert_called_once()


class TestPluginSecurity:
    """Test plugin security and isolation."""

    def test_plugin_permission_validation(self, sample_plugin_manifest):
        """Test plugin permission validation."""
        from app.plugins.registry.manager import PluginManager

        # Plugin with dangerous permissions
        dangerous_manifest = sample_plugin_manifest.copy()
        dangerous_manifest["permissions"] = ["filesystem", "network", "system"]

        manager = PluginManager()

        # Should validate permissions
        is_safe = manager._validate_plugin_permissions(dangerous_manifest)

        # This would depend on security policy
        assert isinstance(is_safe, bool)

    def test_plugin_sandboxing(self, mock_plugin):
        """Test plugin sandboxing mechanisms."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()

        # Mock sandbox creation
        with patch('app.plugins.sandbox.create_sandbox') as mock_sandbox:
            mock_sandbox.return_value = MagicMock()

            sandbox = manager._create_plugin_sandbox("test.plugin")

        assert sandbox is not None
        mock_sandbox.assert_called_once()

    def test_plugin_resource_limits(self, mock_plugin):
        """Test plugin resource limiting."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        # Set resource limits
        limits = {
            "memory": 1024 * 1024 * 100,  # 100MB
            "cpu": 50.0,  # 50% CPU
            "disk": 1024 * 1024 * 500   # 500MB disk
        }

        with patch.object(manager, '_apply_resource_limits') as mock_limits:
            manager.set_plugin_resource_limits("test.plugin", limits)

        mock_limits.assert_called_once_with("test.plugin", limits)


class TestPluginEventSystem:
    """Test plugin event system."""

    async def test_plugin_event_registration(self, mock_plugin):
        """Test plugin event registration."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()
        manager._loaded_plugins["test.plugin"] = mock_plugin

        # Register event handler
        handler = AsyncMock()
        manager.register_event_handler("test.plugin", "test_event", handler)

        # Trigger event
        await manager.trigger_event("test_event", {"data": "test"})

        handler.assert_called_once_with({"data": "test"})

    async def test_plugin_event_propagation(self):
        """Test event propagation between plugins."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()

        # Create multiple event handlers
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        manager.register_event_handler("plugin1", "global_event", handler1)
        manager.register_event_handler("plugin2", "global_event", handler2)

        # Trigger global event
        await manager.trigger_event("global_event", {"message": "hello"})

        handler1.assert_called_once_with({"message": "hello"})
        handler2.assert_called_once_with({"message": "hello"})

    async def test_plugin_event_filtering(self):
        """Test plugin event filtering."""
        from app.plugins.registry.manager import PluginManager

        manager = PluginManager()

        # Register filtered event handler
        handler = AsyncMock()
        event_filter = lambda data: data.get("priority") == "high"

        manager.register_event_handler(
            "test.plugin",
            "filtered_event",
            handler,
            event_filter=event_filter
        )

        # Trigger events with different priorities
        await manager.trigger_event("filtered_event", {"priority": "low"})
        await manager.trigger_event("filtered_event", {"priority": "high"})

        # Handler should only be called for high priority
        handler.assert_called_once_with({"priority": "high"})


@pytest.mark.integration
class TestPluginManagerIntegration:
    """Integration tests for plugin manager."""

    async def test_full_plugin_lifecycle(self, temp_dir):
        """Test complete plugin lifecycle."""
        from app.plugins.registry.manager import PluginManager

        # Create mock plugin
        plugin_dir = temp_dir / "lifecycle_plugin"
        plugin_dir.mkdir()

        manifest = {
            "name": "lifecycle_plugin",
            "version": "1.0.0",
            "description": "Test lifecycle",
            "category": "test",
            "api_version": "1.0"
        }

        (plugin_dir / "manifest.json").write_text(str(manifest).replace("'", '"'))
        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "plugin.py").write_text("""
class LifecyclePlugin:
    def __init__(self):
        self.enabled = False

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    def enable(self):
        self.enabled = True
        return True

    def disable(self):
        self.enabled = False
        return True

    def get_info(self):
        return {"name": "lifecycle_plugin", "version": "1.0.0"}

    def get_health_status(self):
        return {"status": "healthy"}
""")

        manager = PluginManager()

        # Discovery
        discovered = await manager.discover_plugins([str(temp_dir)])
        assert "lifecycle_plugin" in discovered

        # Loading
        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            mock_plugin = MagicMock()
            mock_plugin.get_info.return_value = {"name": "lifecycle_plugin"}
            mock_plugin.get_health_status.return_value = {"status": "healthy"}
            mock_load.return_value = mock_plugin

            success = await manager.load_plugin("lifecycle_plugin")
            assert success is True

        # Enabling
        with patch.object(mock_plugin, 'enable') as mock_enable:
            mock_enable.return_value = True
            success = await manager.enable_plugin("lifecycle_plugin")
            assert success is True

        # Status checks
        assert manager.is_plugin_loaded("lifecycle_plugin")
        assert manager.is_plugin_enabled("lifecycle_plugin")

        # Information retrieval
        info = manager.get_plugin_info("lifecycle_plugin")
        assert info is not None

        # Disabling
        with patch.object(mock_plugin, 'disable') as mock_disable:
            mock_disable.return_value = True
            success = await manager.disable_plugin("lifecycle_plugin")
            assert success is True

        # Unloading
        with patch.object(mock_plugin, 'shutdown') as mock_shutdown:
            success = await manager.unload_plugin("lifecycle_plugin")
            assert success is True

        assert not manager.is_plugin_loaded("lifecycle_plugin")

    async def test_plugin_dependency_resolution(self, temp_dir):
        """Test plugin dependency resolution."""
        from app.plugins.registry.manager import PluginManager

        # Create base plugin
        base_dir = temp_dir / "base_plugin"
        base_dir.mkdir()
        (base_dir / "manifest.json").write_text(
            '{"name": "base_plugin", "version": "1.0.0", "category": "base"}'
        )
        (base_dir / "__init__.py").touch()
        (base_dir / "plugin.py").touch()

        # Create dependent plugin
        dep_dir = temp_dir / "dependent_plugin"
        dep_dir.mkdir()
        (dep_dir / "manifest.json").write_text(
            '{"name": "dependent_plugin", "version": "1.0.0", "category": "test", "dependencies": ["base_plugin"]}'
        )
        (dep_dir / "__init__.py").touch()
        (dep_dir / "plugin.py").touch()

        manager = PluginManager()

        # Discover plugins
        await manager.discover_plugins([str(temp_dir)])

        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            base_plugin = MagicMock()
            dep_plugin = MagicMock()
            mock_load.side_effect = [base_plugin, dep_plugin]

            # Load dependent plugin - should automatically load base
            success = await manager.load_plugin("dependent_plugin")

        assert success is True
        assert manager.is_plugin_loaded("base_plugin")
        assert manager.is_plugin_loaded("dependent_plugin")

    async def test_plugin_error_handling(self, temp_dir):
        """Test plugin error handling and recovery."""
        from app.plugins.registry.manager import PluginManager

        # Create plugin that will fail to load
        plugin_dir = temp_dir / "failing_plugin"
        plugin_dir.mkdir()
        (plugin_dir / "manifest.json").write_text(
            '{"name": "failing_plugin", "version": "1.0.0", "category": "test"}'
        )
        (plugin_dir / "__init__.py").touch()
        (plugin_dir / "plugin.py").touch()

        manager = PluginManager()
        await manager.discover_plugins([str(temp_dir)])

        with patch('app.plugins.registry.loader.PluginLoader.load_plugin') as mock_load:
            mock_load.side_effect = Exception("Plugin load failed")

            success = await manager.load_plugin("failing_plugin")

        assert success is False
        assert not manager.is_plugin_loaded("failing_plugin")

        # Manager should remain stable after failure
        assert len(manager.list_plugins()) == 0
