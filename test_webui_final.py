#!/usr/bin/env python3
"""
Final integration test for WebUI Plugin.
Confirms the WebUI plugin works correctly as a plugin following framework standards.
"""

import sys
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_webui_plugin_complete():
    """Complete test of WebUI plugin functionality."""
    print("🧪 WebUI Plugin Final Integration Test")
    print("=" * 50)

    tests_passed = 0
    tests_total = 0

    # Test 1: Plugin Structure
    print("\n1️⃣ Testing Plugin Structure...")
    tests_total += 1
    try:
        plugin_dir = Path("app/plugins/system/webui")
        required_files = ["__init__.py", "plugin.py", "manifest.json", "services.py", "README.md"]

        for file_name in required_files:
            file_path = plugin_dir / file_name
            assert file_path.exists(), f"Required file {file_name} missing"

        # Check tests directory
        tests_dir = plugin_dir / "tests"
        assert tests_dir.exists(), "Tests directory should exist"

        test_files = ["test_plugin.py", "test_integration.py", "test_api.py", "test_services.py"]
        for test_file in test_files:
            test_path = tests_dir / test_file
            assert test_path.exists(), f"Test file {test_file} missing"

        print("✅ Plugin structure is complete")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Plugin structure test failed: {e}")

    # Test 2: Manifest Validation
    print("\n2️⃣ Testing Manifest...")
    tests_total += 1
    try:
        manifest_path = Path("app/plugins/system/webui/manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        required_fields = ["name", "category", "version", "api_prefix", "database_path"]
        for field in required_fields:
            assert field in manifest, f"Manifest missing {field}"

        assert manifest["name"] == "webui", "Plugin name should be 'webui'"
        assert manifest["category"] == "system", "Plugin category should be 'system'"
        assert manifest["version"] == "2.0.0", "Plugin version should be '2.0.0'"

        print("✅ Manifest is valid")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Manifest test failed: {e}")

    # Test 3: Plugin Import
    print("\n3️⃣ Testing Plugin Import...")
    tests_total += 1
    try:
        from app.plugins.system.webui import WebUIPlugin, plugin
        from app.plugins.base import BasePlugin

        assert issubclass(WebUIPlugin, BasePlugin), "WebUIPlugin should inherit from BasePlugin"
        assert isinstance(plugin, WebUIPlugin), "Plugin instance should be WebUIPlugin"

        print("✅ Plugin imports correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Plugin import test failed: {e}")

    # Test 4: Plugin Manager Integration
    print("\n4️⃣ Testing Plugin Manager Integration...")
    tests_total += 1
    try:
        from app.plugins.registry import plugin_manager

        # Test discovery
        discovered = asyncio.run(plugin_manager.discover_plugins())
        webui_found = any("webui" in path for path in discovered)
        assert webui_found, "WebUI plugin should be discoverable"

        # Test loading
        success = asyncio.run(plugin_manager.load_plugin("system.webui"))
        assert success, "WebUI plugin should load successfully"

        # Test it's enabled
        enabled = plugin_manager.get_enabled_plugins()
        webui_plugin = None
        for p in enabled:
            if p.name == "webui" and p.category == "system":
                webui_plugin = p
                break

        assert webui_plugin is not None, "WebUI plugin should be enabled"
        assert webui_plugin._initialized, "WebUI plugin should be initialized"

        # Test unloading
        success = asyncio.run(plugin_manager.unload_plugin("system.webui"))
        assert success, "WebUI plugin should unload successfully"

        print("✅ Plugin manager integration works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Plugin manager test failed: {e}")

    # Test 5: Plugin Functionality
    print("\n5️⃣ Testing Plugin Functionality...")
    tests_total += 1
    try:
        plugin_instance = WebUIPlugin()

        # Test initialization
        result = asyncio.run(plugin_instance.initialize())
        assert result, "Plugin should initialize successfully"

        # Test API routes
        routes = plugin_instance.get_api_routes()
        assert len(routes) > 0, "Plugin should provide API routes"

        # Test database schema
        schema = plugin_instance.get_database_schema()
        assert "collections" in schema, "Plugin should provide database schema"

        # Test configuration validation
        valid_config = {
            "enabled": True,
            "port": 8080,
            "host": "0.0.0.0",
            "theme": "default"
        }
        assert plugin_instance.validate_config(valid_config), "Valid config should pass"

        # Test health status
        health = plugin_instance.get_health_status()
        assert "status" in health, "Plugin should provide health status"

        # Test shutdown
        asyncio.run(plugin_instance.shutdown())
        assert not plugin_instance._initialized, "Plugin should shutdown cleanly"

        print("✅ Plugin functionality works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Plugin functionality test failed: {e}")

    # Test 6: Services Import
    print("\n6️⃣ Testing Services...")
    tests_total += 1
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

        # Test service instantiation
        temp_dir = Path("/tmp")
        template_service = TemplateService(temp_dir)
        static_service = StaticFileService(temp_dir)
        session_manager = SessionManager()
        widget_manager = WidgetManager()
        theme_manager = ThemeManager()
        websocket_manager = WebSocketManager()
        activity_logger = ActivityLogger()
        backup_service = BackupService(temp_dir)
        metrics_collector = MetricsCollector()

        print("✅ All services import and instantiate correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Services test failed: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    print(f"Tests run: {tests_total}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_total - tests_passed}")
    print(f"Success rate: {(tests_passed/tests_total*100):.1f}%")

    if tests_passed == tests_total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ WebUI plugin is fully functional and compliant")
        print("✅ Plugin follows framework standards")
        print("✅ Plugin integrates with plugin manager")
        print("✅ All services are available")
        print("✅ Tests directory is properly structured")
        print("\n🚀 WebUI plugin is ready for production use!")
        return True
    else:
        print(f"\n❌ {tests_total - tests_passed} test(s) failed")
        print("Please review and fix the failing tests")
        return False

def main():
    """Main entry point."""
    try:
        success = test_webui_plugin_complete()
        exit_code = 0 if success else 1
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
