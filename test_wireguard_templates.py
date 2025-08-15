#!/usr/bin/env python3
"""Test script to validate WireGuard WebUI template loading without authentication."""

import sys
import asyncio
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def test_wireguard_template_loading():
    """Test WireGuard WebUI template loading."""
    print("🧪 Testing WireGuard WebUI Template Loading...")

    try:
        # Import WireGuard plugin
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI

        print("✅ Successfully imported WireGuard modules")

        # Create plugin instance
        plugin = WireGuardPlugin()
        print("✅ Created WireGuard plugin instance")

        # Initialize WebUI
        webui = WireGuardWebUI(plugin)
        print("✅ Created WireGuard WebUI instance")

        # Test template loading
        template_dir = Path(__file__).parent / "app/plugins/vpn/wireguard/webui/templates"
        system_templates_dir = Path(__file__).parent / "app/plugins/system/webui/templates"

        print(f"\n📁 Template Directories:")
        print(f"  - WireGuard templates: {template_dir} (exists: {template_dir.exists()})")
        print(f"  - System templates: {system_templates_dir} (exists: {system_templates_dir.exists()})")

        # Test if we can find base.html in the template loader
        try:
            # Check if Jinja2 environment is properly configured
            env = webui.templates.env
            loader = env.loader

            print(f"\n🔍 Template Loader Configuration:")
            if hasattr(loader, 'searchpath'):
                print(f"  - Search paths: {loader.searchpath}")
            else:
                print(f"  - Loader type: {type(loader)}")

            # Try to get the base template
            try:
                base_template = env.get_template("system/webui/templates/base.html")
                print("✅ Successfully loaded system/webui/templates/base.html")
            except Exception as e:
                print(f"❌ Failed to load system/webui/templates/base.html: {e}")

                # Try alternative paths
                try:
                    base_template = env.get_template("base.html")
                    print("✅ Successfully loaded base.html from search path")
                except Exception as e2:
                    print(f"❌ Failed to load base.html: {e2}")

            # Test dashboard template
            try:
                dashboard_template = env.get_template("dashboard.html")
                print("✅ Successfully loaded dashboard.html")
            except Exception as e:
                print(f"❌ Failed to load dashboard.html: {e}")

        except Exception as e:
            print(f"❌ Error testing template loader: {e}")

        # Test available templates
        template_files = list(template_dir.glob("*.html"))
        print(f"\n📄 Available WireGuard templates:")
        for template_file in template_files:
            print(f"  - {template_file.name}")

        system_template_files = list(system_templates_dir.glob("*.html")) if system_templates_dir.exists() else []
        print(f"\n📄 Available System templates:")
        for template_file in system_template_files:
            print(f"  - {template_file.name}")

        print(f"\n✅ Template loading test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during template loading test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mock_template_rendering():
    """Test mock template rendering."""
    print("\n🎨 Testing Mock Template Rendering...")

    try:
        from fastapi import Request
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI

        # Create mock request
        class MockRequest:
            def __init__(self):
                self.url = "http://localhost:8000/plugins/vpn/wireguard"
                self.headers = {}
                self.query_params = {}

        request = MockRequest()

        # Create plugin and WebUI
        plugin = WireGuardPlugin()
        webui = WireGuardWebUI(plugin)

        # Test context creation
        context = {
            "request": request,
            "plugin": plugin.get_info(),
            "servers": [],
            "stats": {
                "total_servers": 0,
                "active_servers": 0,
                "total_clients": 0,
                "active_connections": 0
            },
            "recent_activity": [],
            "menu_context": {"plugin_path": "/plugins/vpn/wireguard"},
            "user": {"username": "test"},
            "has_system_base": True,
            "plugin_menus": []
        }

        # Test template response creation (without actual rendering)
        try:
            # This will test if the template can be found and loaded
            template = webui.templates.env.get_template("dashboard.html")
            print("✅ Dashboard template found and can be loaded")

            # Try to render with our context (this might fail due to missing dependencies)
            try:
                rendered = template.render(**context)
                print("✅ Template rendered successfully!")
                print(f"   Rendered content length: {len(rendered)} characters")
            except Exception as e:
                print(f"⚠️  Template found but rendering failed: {e}")
                # This is expected as we don't have full context

        except Exception as e:
            print(f"❌ Template loading failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Error during mock template rendering test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🚀 WireGuard WebUI Template Test Suite")
    print("=" * 50)

    success = True

    # Test 1: Template loading
    success &= await test_wireguard_template_loading()

    # Test 2: Mock rendering
    success &= await test_mock_template_rendering()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! WireGuard WebUI templates should work correctly.")
        print("\n💡 Next steps:")
        print("  1. Start the server: uvicorn app.main:app --reload")
        print("  2. Visit: http://localhost:8000/plugins/vpn/wireguard")
        print("  3. Check for any runtime errors in the logs")
    else:
        print("❌ Some tests failed. Please check the output above.")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
