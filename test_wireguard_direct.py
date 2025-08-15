#!/usr/bin/env python3
"""Test script to bypass authentication and test WireGuard WebUI directly."""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

async def test_wireguard_webui_direct():
    """Test WireGuard WebUI directly without authentication."""
    print("🚀 Testing WireGuard WebUI Direct Access")
    print("=" * 50)

    try:
        # Import required modules
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI
        from fastapi import Request
        from fastapi.responses import HTMLResponse

        print("✅ Successfully imported modules")

        # Create plugin instance
        plugin = WireGuardPlugin()
        await plugin.initialize()
        print("✅ Plugin initialized")

        # Create WebUI instance
        webui = WireGuardWebUI(plugin)
        print("✅ WebUI instance created")

        # Create mock request
        class MockRequest:
            def __init__(self):
                self.url = "http://localhost:8000/plugins/vpn/wireguard"
                self.headers = {}
                self.query_params = {}
                self.path_params = {}
                self.method = "GET"

        request = MockRequest()

        # Test dashboard rendering with mocked auth
        print("\n🎨 Testing Dashboard Rendering...")

        try:
            # Mock the authentication functions
            async def mock_require_web_auth():
                return {"username": "admin", "id": "admin"}

            async def mock_get_current_web_user():
                return {"username": "admin", "id": "admin"}

            # Get the dashboard route handler
            dashboard_handler = None
            for route in webui.router.routes:
                if hasattr(route, 'path') and route.path == "" and hasattr(route, 'endpoint'):
                    dashboard_handler = route.endpoint
                    break

            if dashboard_handler:
                print("✅ Found dashboard route handler")

                # Call dashboard with mocked dependencies
                try:
                    # Mock the dependencies
                    auth = await mock_require_web_auth()

                    # Call the dashboard function directly
                    response = await dashboard_handler(request, auth=auth, _enabled=None)

                    if isinstance(response, HTMLResponse):
                        print("✅ Dashboard returned HTMLResponse")
                        print(f"   Content length: {len(response.body)} bytes")

                        # Check if the response contains expected content
                        content = response.body.decode()
                        if "WireGuard VPN" in content:
                            print("✅ Dashboard content contains WireGuard VPN title")
                        if "Dashboard" in content:
                            print("✅ Dashboard content contains Dashboard text")
                        if "Bootstrap" in content:
                            print("✅ Dashboard content includes Bootstrap CSS")

                        return True
                    else:
                        print(f"⚠️  Dashboard returned {type(response)} instead of HTMLResponse")
                        if hasattr(response, 'body'):
                            print(f"   Content: {response.body[:200]}...")
                        return False

                except Exception as e:
                    print(f"❌ Error calling dashboard handler: {e}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                print("❌ Could not find dashboard route handler")
                return False

        except Exception as e:
            print(f"❌ Error during dashboard test: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Error during WebUI test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_template_inheritance():
    """Test template inheritance specifically."""
    print("\n🔍 Testing Template Inheritance...")

    try:
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        webui = WireGuardWebUI(plugin)

        # Test template loading
        env = webui.templates.env

        # Test if we can load the base template
        try:
            base_template = env.get_template("system/webui/templates/base.html")
            print("✅ Base template loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load base template: {e}")
            return False

        # Test if we can load and render dashboard template
        try:
            dashboard_template = env.get_template("dashboard.html")
            print("✅ Dashboard template loaded successfully")

            # Create minimal context for rendering
            context = {
                "request": {"url": "http://localhost:8000"},
                "plugin": {"name": "WireGuard", "description": "WireGuard VPN Plugin"},
                "servers": [],
                "stats": {
                    "total_servers": 0,
                    "active_servers": 0,
                    "total_clients": 0,
                    "active_connections": 0
                },
                "recent_activity": [],
                "menu_context": {"plugin_path": "/plugins/vpn/wireguard"},
                "user": {"username": "admin"},
                "has_system_base": True,
                "plugin_menus": []
            }

            rendered_content = dashboard_template.render(**context)
            print("✅ Dashboard template rendered successfully")
            print(f"   Rendered content length: {len(rendered_content)} characters")

            # Check for key elements
            if "<!doctype html>" in rendered_content.lower():
                print("✅ Rendered content is valid HTML")
            if "WireGuard VPN" in rendered_content:
                print("✅ Rendered content contains WireGuard VPN title")
            if "Bootstrap" in rendered_content:
                print("✅ Rendered content includes Bootstrap CSS")

            return True

        except Exception as e:
            print(f"❌ Failed to render dashboard template: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Error during template inheritance test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_other_templates():
    """Test other WireGuard templates."""
    print("\n📄 Testing Other Templates...")

    try:
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        webui = WireGuardWebUI(plugin)
        env = webui.templates.env

        template_files = ["servers.html", "clients.html", "settings.html", "server_form.html", "client_form.html"]

        success_count = 0
        for template_file in template_files:
            try:
                template = env.get_template(template_file)
                print(f"✅ {template_file} loaded successfully")

                # Try to render with minimal context
                context = {
                    "request": {"url": "http://localhost:8000"},
                    "servers": [],
                    "clients": [],
                    "server": None,
                    "client": None,
                    "menu_context": {"plugin_path": "/plugins/vpn/wireguard"},
                    "user": {"username": "admin"},
                    "has_system_base": True,
                    "plugin_menus": []
                }

                rendered = template.render(**context)
                print(f"   ✅ {template_file} rendered successfully ({len(rendered)} chars)")
                success_count += 1

            except Exception as e:
                print(f"   ❌ {template_file} failed: {e}")

        print(f"\n📊 Template Test Results: {success_count}/{len(template_files)} templates working")
        return success_count == len(template_files)

    except Exception as e:
        print(f"❌ Error during other templates test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    print("🧪 WireGuard WebUI Direct Test Suite")
    print("=" * 60)

    success = True

    # Test 1: Direct WebUI access
    success &= await test_wireguard_webui_direct()

    # Test 2: Template inheritance
    success &= await test_template_inheritance()

    # Test 3: Other templates
    success &= await test_other_templates()

    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! WireGuard WebUI is working correctly.")
        print("\n💡 Template loading and rendering is functioning properly.")
        print("   The original template error should now be resolved.")
        print("\n🌐 Next steps:")
        print("   1. Access the WebUI via browser at: http://localhost:8000/plugins/vpn/wireguard")
        print("   2. Login with admin/admin if prompted")
        print("   3. Test the complete functionality")
    else:
        print("❌ Some tests failed. Check the output above for details.")

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
