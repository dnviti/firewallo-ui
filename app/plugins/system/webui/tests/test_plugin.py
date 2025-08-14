#!/usr/bin/env python3
"""
Test module for WebUI Plugin core functionality.
Tests plugin structure, inheritance, initialization, and basic operations.
"""

import sys
import os
import json
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


class TestWebUIPluginStructure:
    """Test WebUI plugin file structure and basic requirements."""

    def test_plugin_files_exist(self):
        """Test that all required plugin files exist."""
        plugin_dir = Path(__file__).parent.parent

        required_files = [
            "__init__.py",
            "plugin.py",
            "manifest.json",
            "services.py",
            "README.md"
        ]

        for file_name in required_files:
            file_path = plugin_dir / file_name
            assert file_path.exists(), f"Required file {file_name} is missing"

    def test_tests_directory_exists(self):
        """Test that tests directory exists and has proper structure."""
        tests_dir = Path(__file__).parent
        assert tests_dir.exists(), "Tests directory should exist"
        assert tests_dir.name == "tests", "Tests directory should be named 'tests'"

        # Check for __init__.py in tests directory
        init_file = tests_dir / "__init__.py"
        assert init_file.exists(), "Tests directory should have __init__.py"


class TestWebUIPluginManifest:
    """Test WebUI plugin manifest.json validity and completeness."""

    def setup_method(self):
        """Setup test data."""
        manifest_path = Path(__file__).parent.parent / "manifest.json"
        with open(manifest_path, 'r') as f:
            self.manifest = json.load(f)

    def test_manifest_required_fields(self):
        """Test that manifest contains all required fields."""
        required_fields = [
            "name", "display_name", "category", "version", "description",
            "author", "dependencies", "permissions", "configuration",
            "api_prefix", "database_path", "supports_hot_reload"
        ]

        for field in required_fields:
            assert field in self.manifest, f"Manifest missing required field: {field}"

    def test_manifest_values(self):
        """Test that manifest has correct values."""
        assert self.manifest["name"] == "webui", "Plugin name should be 'webui'"
        assert self.manifest["category"] == "system", "Plugin category should be 'system'"
        assert self.manifest["version"] == "2.0.0", "Plugin version should be '2.0.0'"
        assert self.manifest["api_prefix"] == "/api/webui", "API prefix should be '/api/webui'"
        assert self.manifest["database_path"] == "plugins.system.webui", "Database path should be 'plugins.system.webui'"
        assert self.manifest["supports_hot_reload"] is True, "Should support hot reload"

    def test_configuration_structure(self):
        """Test that configuration section is properly structured."""
        config = self.manifest.get("configuration", {})

        assert "required" in config, "Configuration should have 'required' section"
        assert "optional" in config, "Configuration should have 'optional' section"
        assert "defaults" in config, "Configuration should have 'defaults' section"

        # Check required fields
        required_fields = config["required"]
        assert "enabled" in required_fields, "Should require 'enabled' field"
        assert "port" in required_fields, "Should require 'port' field"
        assert "host" in required_fields, "Should require 'host' field"

    def test_dependencies_structure(self):
        """Test that dependencies are properly defined."""
        deps = self.manifest.get("dependencies", {})

        assert "python" in deps, "Should specify Python version requirement"
        assert "packages" in deps, "Should list required packages"

        packages = deps["packages"]
        required_packages = ["fastapi", "jinja2", "psutil", "aiofiles"]

        for package in required_packages:
            found = any(package in pkg for pkg in packages)
            assert found, f"Should include {package} in dependencies"


class TestWebUIPluginImport:
    """Test WebUI plugin import and basic class structure."""

    def test_plugin_import(self):
        """Test that WebUI plugin can be imported successfully."""
        try:
            from plugin import WebUIPlugin, plugin
            assert WebUIPlugin is not None, "WebUIPlugin class should be importable"
            assert plugin is not None, "Plugin instance should be available"
        except ImportError as e:
            pytest.fail(f"Failed to import WebUI plugin: {e}")

    def test_plugin_inheritance(self):
        """Test that WebUI plugin inherits from BasePlugin."""
        from plugin import WebUIPlugin
        from app.plugins.base import BasePlugin

        assert issubclass(WebUIPlugin, BasePlugin), "WebUIPlugin should inherit from BasePlugin"

    def test_plugin_instance_type(self):
        """Test that plugin instance is of correct type."""
        from plugin import WebUIPlugin, plugin

        assert isinstance(plugin, WebUIPlugin), "Plugin instance should be WebUIPlugin type"


class TestWebUIPluginMethods:
    """Test WebUI plugin required method implementations."""

    def setup_method(self):
        """Setup test plugin instance."""
        from plugin import WebUIPlugin
        self.plugin = WebUIPlugin()

    def test_required_methods_exist(self):
        """Test that all required BasePlugin methods are implemented."""
        required_methods = [
            "initialize", "shutdown", "get_api_routes",
            "get_database_schema", "validate_config"
        ]

        for method in required_methods:
            assert hasattr(self.plugin, method), f"Plugin should implement {method} method"
            assert callable(getattr(self.plugin, method)), f"{method} should be callable"

    def test_plugin_attributes(self):
        """Test that plugin has correct basic attributes."""
        assert self.plugin.name == "webui", "Plugin name should be 'webui'"
        assert self.plugin.category == "system", "Plugin category should be 'system'"
        assert self.plugin.version == "2.0.0", "Plugin version should be '2.0.0'"
        assert self.plugin.description is not None, "Plugin should have description"
        assert self.plugin.author is not None, "Plugin should have author"

    def test_get_api_routes(self):
        """Test that plugin provides API routes."""
        routes = self.plugin.get_api_routes()

        assert isinstance(routes, list), "get_api_routes should return a list"
        assert len(routes) > 0, "Plugin should provide at least one router"

        # Check for web and API routers
        web_router_found = False
        api_router_found = False

        for router in routes:
            if hasattr(router, 'tags'):
                if 'webui' in router.tags:
                    web_router_found = True
                if 'webui-api' in router.tags:
                    api_router_found = True

        assert web_router_found, "Should provide web router"
        assert api_router_found, "Should provide API router"

    def test_get_database_schema(self):
        """Test that plugin provides database schema."""
        schema = self.plugin.get_database_schema()

        assert isinstance(schema, dict), "get_database_schema should return a dict"
        assert "collections" in schema, "Schema should define collections"

        collections = schema["collections"]
        expected_collections = ["webui", "webui_sessions", "webui_preferences"]

        for collection in expected_collections:
            assert collection in collections, f"Schema should define {collection} collection"


class TestWebUIPluginConfiguration:
    """Test WebUI plugin configuration validation."""

    def setup_method(self):
        """Setup test plugin instance."""
        from plugin import WebUIPlugin
        self.plugin = WebUIPlugin()

    def test_valid_configuration(self):
        """Test that valid configuration is accepted."""
        valid_config = {
            "enabled": True,
            "port": 8080,
            "host": "0.0.0.0",
            "theme": "default",
            "auto_refresh_interval": 60,
            "session_timeout": 3600
        }

        result = self.plugin.validate_config(valid_config)
        assert result is True, "Valid configuration should be accepted"

    def test_invalid_port_configuration(self):
        """Test that invalid port configuration is rejected."""
        invalid_configs = [
            {"port": 0},           # Port too low
            {"port": 99999},       # Port too high
            {"port": -1},          # Negative port
        ]

        for config in invalid_configs:
            result = self.plugin.validate_config(config)
            assert result is False, f"Invalid port configuration should be rejected: {config}"

    def test_invalid_timeout_configuration(self):
        """Test that invalid timeout configuration is rejected."""
        invalid_config = {
            "session_timeout": 30  # Too short (minimum is 60)
        }

        result = self.plugin.validate_config(invalid_config)
        assert result is False, "Too short session timeout should be rejected"

    def test_configuration_type_validation(self):
        """Test that configuration with wrong types is handled."""
        invalid_config = {
            "port": "not_a_number",
            "enabled": "not_a_boolean"
        }

        # Should either reject or handle gracefully
        try:
            result = self.plugin.validate_config(invalid_config)
            # If it doesn't raise an exception, it should return False
            assert result is False, "Invalid types should be rejected"
        except (ValueError, TypeError):
            # It's also acceptable to raise an exception for type errors
            pass


class TestWebUIPluginHealth:
    """Test WebUI plugin health status reporting."""

    def setup_method(self):
        """Setup test plugin instance."""
        from plugin import WebUIPlugin
        self.plugin = WebUIPlugin()

    def test_health_status_structure(self):
        """Test that health status has required structure."""
        health = self.plugin.get_health_status()

        assert isinstance(health, dict), "Health status should be a dictionary"

        # Check for required base fields
        required_fields = [
            "plugin_id", "name", "category", "version",
            "status", "enabled", "initialized"
        ]

        for field in required_fields:
            assert field in health, f"Health status should include {field}"

    def test_webui_specific_health_fields(self):
        """Test that WebUI-specific health fields are present."""
        health = self.plugin.get_health_status()

        webui_fields = [
            "active_sessions", "total_requests",
            "templates_available", "static_files_available"
        ]

        for field in webui_fields:
            assert field in health, f"WebUI health should include {field}"

    def test_health_status_values(self):
        """Test that health status contains reasonable values."""
        health = self.plugin.get_health_status()

        assert health["name"] == "webui", "Health should report correct plugin name"
        assert health["category"] == "system", "Health should report correct category"
        assert health["version"] == "2.0.0", "Health should report correct version"
        assert isinstance(health["active_sessions"], int), "Active sessions should be integer"
        assert isinstance(health["total_requests"], int), "Total requests should be integer"


@pytest.mark.asyncio
class TestWebUIPluginLifecycle:
    """Test WebUI plugin initialization and shutdown lifecycle."""

    def setup_method(self):
        """Setup test plugin instance."""
        from plugin import WebUIPlugin
        self.plugin = WebUIPlugin()

    async def test_plugin_initialization(self):
        """Test that plugin can be initialized successfully."""
        result = await self.plugin.initialize()

        assert result is True, "Plugin initialization should succeed"
        assert self.plugin._initialized is True, "Plugin should be marked as initialized"
        assert self.plugin._startup_time is not None, "Startup time should be recorded"

    async def test_plugin_shutdown(self):
        """Test that plugin can be shut down successfully."""
        # First initialize
        await self.plugin.initialize()

        # Then shutdown
        await self.plugin.shutdown()

        assert self.plugin._initialized is False, "Plugin should be marked as not initialized after shutdown"
        assert self.plugin._shutdown_time is not None, "Shutdown time should be recorded"

    async def test_plugin_reinitialization(self):
        """Test that plugin can be reinitialized after shutdown."""
        # Initialize, shutdown, then initialize again
        await self.plugin.initialize()
        await self.plugin.shutdown()

        result = await self.plugin.initialize()

        assert result is True, "Plugin should be able to reinitialize"
        assert self.plugin._initialized is True, "Plugin should be initialized after restart"

    async def test_plugin_metrics_initialization(self):
        """Test that plugin metrics are properly initialized."""
        await self.plugin.initialize()

        assert hasattr(self.plugin, 'metrics'), "Plugin should have metrics attribute"
        assert self.plugin.start_time is not None, "Start time should be set"
        assert isinstance(self.plugin.request_count, int), "Request count should be integer"


class TestWebUIPluginServices:
    """Test WebUI plugin service imports and availability."""

    def test_service_imports(self):
        """Test that all WebUI services can be imported."""
        try:
            from services import (
                TemplateService,
                StaticFileService,
                SessionManager,
                WidgetManager,
                ThemeManager,
                WebSocketManager,
                ActivityLogger,
                BackupService,
                MetricsCollector
            )

            # Just importing successfully is the test
            assert True, "All services should be importable"

        except ImportError as e:
            pytest.fail(f"Failed to import WebUI services: {e}")

    def test_service_classes_exist(self):
        """Test that service classes are properly defined."""
        from services import (
            TemplateService,
            StaticFileService,
            SessionManager,
            WidgetManager,
            ThemeManager,
            WebSocketManager,
            ActivityLogger,
            BackupService,
            MetricsCollector
        )

        services = [
            TemplateService, StaticFileService, SessionManager,
            WidgetManager, ThemeManager, WebSocketManager,
            ActivityLogger, BackupService, MetricsCollector
        ]

        for service_class in services:
            assert callable(service_class), f"{service_class.__name__} should be a callable class"
            assert hasattr(service_class, '__init__'), f"{service_class.__name__} should have __init__ method"


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
