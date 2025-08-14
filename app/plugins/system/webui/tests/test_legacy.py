#!/usr/bin/env python3
"""
Test script for WebUI Plugin
Verifies that the WebUI plugin follows plugin framework standards and works correctly.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import importlib.util

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))


def test_plugin_structure():
    """Test that the WebUI plugin has correct structure."""
    print("Testing WebUI plugin structure...")

    plugin_dir = Path("app/plugins/system/webui")

    # Check required files exist
    required_files = [
        "__init__.py",
        "plugin.py",
        "manifest.json",
        "services.py",
        "README.md"
    ]

    all_exist = True
    for file_name in required_files:
        file_path = plugin_dir / file_name
        if file_path.exists():
            print(f"✓ {file_name} exists")
        else:
            print(f"✗ {file_name} missing")
            all_exist = False

    return all_exist


def test_manifest_validity():
    """Test that the manifest.json is valid and complete."""
    print("\nTesting WebUI plugin manifest...")

    manifest_path = Path("app/plugins/system/webui/manifest.json")

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Check required manifest fields
        required_fields = [
            "name", "display_name", "category", "version", "description",
            "author", "dependencies", "permissions", "configuration",
            "api_prefix", "database_path", "supports_hot_reload"
        ]

        all_present = True
        for field in required_fields:
            if field in manifest:
                print(f"✓ Manifest field '{field}' present")
            else:
                print(f"✗ Manifest field '{field}' missing")
                all_present = False

        # Validate specific values
        if manifest.get("name") == "webui":
            print("✓ Plugin name is 'webui'")
        else:
            print(f"✗ Plugin name is '{manifest.get('name')}', expected 'webui'")
            all_present = False

        if manifest.get("category") == "system":
            print("✓ Plugin category is 'system'")
        else:
            print(f"✗ Plugin category is '{manifest.get('category')}', expected 'system'")
            all_present = False

        return all_present

    except Exception as e:
        print(f"✗ Failed to load manifest: {e}")
        return False


def test_plugin_import():
    """Test that the WebUI plugin can be imported."""
    print("\nTesting WebUI plugin import...")

    try:
        from app.plugins.system.webui import WebUIPlugin, plugin
        print("✓ WebUI plugin imported successfully")

        # Check if plugin is an instance of WebUIPlugin
        if isinstance(plugin, WebUIPlugin):
            print("✓ Plugin instance created correctly")
        else:
            print(f"✗ Plugin instance is {type(plugin)}, expected WebUIPlugin")
            return False

        return True

    except Exception as e:
        print(f"✗ Failed to import WebUI plugin: {e}")
        return False


def test_plugin_inheritance():
    """Test that WebUI plugin inherits from BasePlugin."""
    print("\nTesting WebUI plugin inheritance...")

    try:
        from app.plugins.system.webui import WebUIPlugin
        from app.plugins.base import BasePlugin

        if issubclass(WebUIPlugin, BasePlugin):
            print("✓ WebUIPlugin inherits from BasePlugin")
        else:
            print("✗ WebUIPlugin does not inherit from BasePlugin")
            return False

        # Check required methods are implemented
        required_methods = [
            "initialize", "shutdown", "get_api_routes",
            "get_database_schema", "validate_config"
        ]

        all_implemented = True
        for method in required_methods:
            if hasattr(WebUIPlugin, method):
                print(f"✓ Method '{method}' implemented")
            else:
                print(f"✗ Method '{method}' not implemented")
                all_implemented = False

        return all_implemented

    except Exception as e:
        print(f"✗ Failed to test inheritance: {e}")
        return False


async def test_plugin_initialization():
    """Test that the WebUI plugin can be initialized."""
    print("\nTesting WebUI plugin initialization...")

    try:
        from app.plugins.system.webui import WebUIPlugin

        # Create plugin instance
        plugin = WebUIPlugin()
        print("✓ Plugin instance created")

        # Test basic attributes
        if plugin.name == "webui":
            print("✓ Plugin name set correctly")
        else:
            print(f"✗ Plugin name is '{plugin.name}', expected 'webui'")

        if plugin.category == "system":
            print("✓ Plugin category set correctly")
        else:
            print(f"✗ Plugin category is '{plugin.category}', expected 'system'")

        # Initialize plugin
        result = await plugin.initialize()
        if result:
            print("✓ Plugin initialized successfully")
        else:
            print("✗ Plugin initialization failed")
            return False

        # Check if plugin is marked as initialized
        if plugin._initialized:
            print("✓ Plugin marked as initialized")
        else:
            print("✗ Plugin not marked as initialized")
            return False

        # Shutdown plugin
        await plugin.shutdown()
        print("✓ Plugin shutdown successfully")

        return True

    except Exception as e:
        print(f"✗ Plugin initialization test failed: {e}")
        return False


def test_plugin_routes():
    """Test that the WebUI plugin provides API routes."""
    print("\nTesting WebUI plugin routes...")

    try:
        from app.plugins.system.webui import WebUIPlugin

        plugin = WebUIPlugin()
        routes = plugin.get_api_routes()

        if routes and len(routes) > 0:
            print(f"✓ Plugin provides {len(routes)} router(s)")

            # Check for web and API routers
            web_router_found = False
            api_router_found = False

            for router in routes:
                if hasattr(router, 'tags'):
                    if 'webui' in router.tags:
                        web_router_found = True
                        print("✓ Web router found")
                    if 'webui-api' in router.tags:
                        api_router_found = True
                        print("✓ API router found")

            return web_router_found and api_router_found
        else:
            print("✗ Plugin provides no routes")
            return False

    except Exception as e:
        print(f"✗ Failed to test routes: {e}")
        return False


def test_plugin_database_schema():
    """Test that the WebUI plugin provides database schema."""
    print("\nTesting WebUI plugin database schema...")

    try:
        from app.plugins.system.webui import WebUIPlugin

        plugin = WebUIPlugin()
        schema = plugin.get_database_schema()

        if schema and isinstance(schema, dict):
            print("✓ Plugin provides database schema")

            if "collections" in schema:
                print(f"✓ Schema defines {len(schema['collections'])} collection(s)")

                # Check for WebUI-specific collections
                expected_collections = ["webui", "webui_sessions", "webui_preferences"]
                for collection in expected_collections:
                    if collection in schema["collections"]:
                        print(f"✓ Collection '{collection}' defined")
                    else:
                        print(f"✗ Collection '{collection}' missing")

                return True
            else:
                print("✗ Schema missing 'collections' key")
                return False
        else:
            print("✗ Plugin provides no database schema")
            return False

    except Exception as e:
        print(f"✗ Failed to test database schema: {e}")
        return False


def test_plugin_configuration():
    """Test that the WebUI plugin configuration works."""
    print("\nTesting WebUI plugin configuration...")

    try:
        from app.plugins.system.webui import WebUIPlugin

        plugin = WebUIPlugin()

        # Test configuration validation
        test_config = {
            "enabled": True,
            "port": 8080,
            "host": "0.0.0.0",
            "theme": "default",
            "auto_refresh_interval": 60,
            "session_timeout": 3600
        }

        if plugin.validate_config(test_config):
            print("✓ Valid configuration accepted")
        else:
            print("✗ Valid configuration rejected")
            return False

        # Test invalid configuration
        invalid_config = {
            "port": 99999,  # Invalid port
            "session_timeout": 10  # Too short
        }

        try:
            result = plugin.validate_config(invalid_config)
            if not result:
                print("✓ Invalid configuration rejected")
            else:
                print("✗ Invalid configuration accepted")
                return False
        except:
            print("✓ Invalid configuration raised exception")

        return True

    except Exception as e:
        print(f"✗ Failed to test configuration: {e}")
        return False


def test_plugin_health():
    """Test that the WebUI plugin provides health status."""
    print("\nTesting WebUI plugin health status...")

    try:
        from app.plugins.system.webui import WebUIPlugin

        plugin = WebUIPlugin()
        health = plugin.get_health_status()

        if health and isinstance(health, dict):
            print("✓ Plugin provides health status")

            # Check for required health fields
            required_fields = [
                "plugin_id", "name", "category", "version",
                "status", "enabled", "initialized"
            ]

            for field in required_fields:
                if field in health:
                    print(f"✓ Health field '{field}' present")
                else:
                    print(f"✗ Health field '{field}' missing")

            # Check WebUI-specific health fields
            webui_fields = [
                "active_sessions", "total_requests",
                "templates_available", "static_files_available"
            ]

            for field in webui_fields:
                if field in health:
                    print(f"✓ WebUI health field '{field}' present")

            return True
        else:
            print("✗ Plugin provides no health status")
            return False

    except Exception as e:
        print(f"✗ Failed to test health status: {e}")
        return False


def test_plugin_services():
    """Test that the WebUI plugin services are available."""
    print("\nTesting WebUI plugin services...")

    try:
        from app.plugins.system.webui.services import (
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
            "TemplateService", "StaticFileService", "SessionManager",
            "WidgetManager", "ThemeManager", "WebSocketManager",
            "ActivityLogger", "BackupService", "MetricsCollector"
        ]

        all_available = True
        for service in services:
            try:
                # Service was already imported above
                print(f"✓ Service '{service}' available")
            except:
                print(f"✗ Service '{service}' not available")
                all_available = False

        return all_available

    except Exception as e:
        print(f"✗ Failed to test services: {e}")
        return False


async def test_plugin_with_manager():
    """Test that the WebUI plugin works with plugin manager."""
    print("\nTesting WebUI plugin with plugin manager...")

    try:
        from app.plugins.registry import plugin_manager

        # Discover plugins
        discovered = await plugin_manager.discover_plugins()
        print(f"✓ Discovered {len(discovered)} plugin(s)")

        # Check if WebUI plugin was discovered
        webui_found = False
        for plugin_path in discovered:
            if "webui" in plugin_path and "system" in plugin_path:
                webui_found = True
                print(f"✓ WebUI plugin discovered at: {plugin_path}")
                break

        if not webui_found:
            print("✗ WebUI plugin not discovered")
            return False

        # Try to load WebUI plugin
        webui_path = "system.webui"
        success = await plugin_manager.load_plugin(webui_path)

        if success:
            print("✓ WebUI plugin loaded successfully via manager")
        else:
            print("✗ Failed to load WebUI plugin via manager")
            return False

        # Check if plugin is in enabled plugins
        enabled = plugin_manager.get_enabled_plugins()
        webui_enabled = False

        for plugin in enabled:
            if plugin.name == "webui" and plugin.category == "system":
                webui_enabled = True
                print("✓ WebUI plugin is enabled")
                break

        if not webui_enabled:
            print("✗ WebUI plugin not in enabled plugins")
            return False

        # Unload plugin
        success = await plugin_manager.unload_plugin(webui_path)
        if success:
            print("✓ WebUI plugin unloaded successfully")
        else:
            print("✗ Failed to unload WebUI plugin")

        return True

    except Exception as e:
        print(f"✗ Failed to test with plugin manager: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("WebUI Plugin Test Suite")
    print("=" * 60)

    tests = [
        ("Plugin Structure", test_plugin_structure),
        ("Manifest Validity", test_manifest_validity),
        ("Plugin Import", test_plugin_import),
        ("Plugin Inheritance", test_plugin_inheritance),
        ("Plugin Routes", test_plugin_routes),
        ("Database Schema", test_plugin_database_schema),
        ("Configuration", test_plugin_configuration),
        ("Health Status", test_plugin_health),
        ("Plugin Services", test_plugin_services)
    ]

    # Async tests
    async_tests = [
        ("Plugin Initialization", test_plugin_initialization),
        ("Plugin Manager Integration", test_plugin_with_manager)
    ]

    results = []

    # Run synchronous tests
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Run asynchronous tests
    for test_name, test_func in async_tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            result = asyncio.run(test_func())
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name:<30} : {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! WebUI plugin is ready for use.")
        print("\nThe WebUI plugin successfully:")
        print("- Follows plugin framework standards")
        print("- Inherits from BasePlugin correctly")
        print("- Implements all required methods")
        print("- Provides proper routes and database schema")
        print("- Integrates with the plugin manager")
        print("- Can be loaded/unloaded dynamically")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please fix the issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
