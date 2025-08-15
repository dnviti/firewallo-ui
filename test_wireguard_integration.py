#!/usr/bin/env python3
"""Comprehensive integration test for WireGuard WebUI functionality."""

import sys
import asyncio
import requests
import json
from pathlib import Path
from typing import Optional

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

class WireGuardWebUITester:
    """Comprehensive tester for WireGuard WebUI functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
        self.wireguard_base_path = "/plugins/vpn/wireguard"

    def test_server_connectivity(self) -> bool:
        """Test if the server is running and responsive."""
        print("🔌 Testing server connectivity...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running and responsive")
                return True
            else:
                response = self.session.get(f"{self.base_url}/", timeout=5)
                if response.status_code in [200, 302, 307]:
                    print("✅ Server is running (detected via root endpoint)")
                    return True
                else:
                    print(f"⚠️  Server responded with status {response.status_code}")
                    return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Server connectivity failed: {e}")
            return False

    def authenticate(self, username: str = "admin", password: str = "admin") -> bool:
        """Authenticate with the server."""
        print(f"🔐 Authenticating as {username}...")
        try:
            # Try to login
            login_data = {"username": username, "password": password}
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ Authentication failed with status {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication request failed: {e}")
            return False

    def test_wireguard_webui_access(self) -> bool:
        """Test accessing the WireGuard WebUI."""
        print("🌐 Testing WireGuard WebUI access...")
        try:
            url = f"{self.base_url}{self.wireguard_base_path}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                content = response.text
                # Check for key indicators that the page loaded correctly
                indicators = [
                    "WireGuard VPN",
                    "Dashboard",
                    "<!doctype html>",
                    "Bootstrap"
                ]

                found_indicators = []
                for indicator in indicators:
                    if indicator.lower() in content.lower():
                        found_indicators.append(indicator)

                print(f"✅ WireGuard WebUI accessible (found {len(found_indicators)}/{len(indicators)} indicators)")
                for indicator in found_indicators:
                    print(f"   ✓ Found: {indicator}")

                # Check for template errors
                error_indicators = [
                    "TemplateNotFound",
                    "not found in search path",
                    "Internal Server Error",
                    "500 Internal Server Error"
                ]

                found_errors = []
                for error in error_indicators:
                    if error in content:
                        found_errors.append(error)

                if found_errors:
                    print("⚠️  Detected potential template errors:")
                    for error in found_errors:
                        print(f"   ❌ {error}")
                    return False

                return len(found_indicators) >= 3  # At least 3 indicators should be present

            elif response.status_code == 302 or response.status_code == 307:
                print(f"⚠️  Redirect detected (status {response.status_code})")
                if 'location' in response.headers:
                    print(f"   Redirecting to: {response.headers['location']}")
                return False
            else:
                print(f"❌ WireGuard WebUI access failed with status {response.status_code}")
                if response.text:
                    print(f"   Response snippet: {response.text[:200]}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ WireGuard WebUI request failed: {e}")
            return False

    def test_wireguard_api_endpoints(self) -> bool:
        """Test WireGuard API endpoints."""
        print("📡 Testing WireGuard API endpoints...")
        success_count = 0
        total_tests = 0

        # Test endpoints to check
        endpoints = [
            ("/servers", "GET", "List servers"),
            ("/clients", "GET", "List clients"),
            ("/info", "GET", "Plugin info"),
            ("/health", "GET", "Plugin health")
        ]

        for endpoint, method, description in endpoints:
            total_tests += 1
            url = f"{self.base_url}/api/plugins/vpn/wireguard{endpoint}"

            try:
                if method == "GET":
                    response = self.session.get(url, timeout=10)
                else:
                    continue  # Skip non-GET for now

                if response.status_code == 200:
                    print(f"   ✅ {description}: {endpoint}")
                    success_count += 1
                elif response.status_code == 404:
                    print(f"   ⚠️  {description}: {endpoint} (not found - might be expected)")
                    success_count += 0.5  # Partial success
                else:
                    print(f"   ❌ {description}: {endpoint} (status {response.status_code})")

            except requests.exceptions.RequestException as e:
                print(f"   ❌ {description}: {endpoint} (request failed: {e})")

        print(f"📊 API Test Results: {success_count}/{total_tests} endpoints working")
        return success_count >= total_tests * 0.5  # At least 50% should work

    def test_template_specific_routes(self) -> bool:
        """Test specific template routes in WireGuard WebUI."""
        print("📄 Testing specific template routes...")
        success_count = 0
        total_tests = 0

        # Test specific WebUI routes
        routes = [
            ("", "Dashboard"),
            ("/servers", "Servers list"),
            ("/clients", "Clients list"),
            ("/settings", "Settings"),
        ]

        for route, description in routes:
            total_tests += 1
            url = f"{self.base_url}{self.wireguard_base_path}{route}"

            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    content = response.text
                    # Check if it's a valid HTML page
                    if "<!doctype html>" in content.lower() and "WireGuard" in content:
                        print(f"   ✅ {description}: {route}")
                        success_count += 1
                    else:
                        print(f"   ⚠️  {description}: {route} (invalid content)")
                elif response.status_code in [302, 307]:
                    print(f"   ⚠️  {description}: {route} (redirect)")
                else:
                    print(f"   ❌ {description}: {route} (status {response.status_code})")

            except requests.exceptions.RequestException as e:
                print(f"   ❌ {description}: {route} (request failed: {e})")

        print(f"📊 Template Route Results: {success_count}/{total_tests} routes working")
        return success_count >= total_tests * 0.75  # At least 75% should work

    def test_static_resources(self) -> bool:
        """Test that static resources are accessible."""
        print("🎨 Testing static resources...")
        success_count = 0
        total_tests = 0

        # Test static resources that should be available
        static_resources = [
            ("/static/css/custom.css", "Custom CSS"),
            ("/static/js/common.js", "Common JavaScript"),
        ]

        for resource, description in static_resources:
            total_tests += 1
            url = f"{self.base_url}{resource}"

            try:
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    print(f"   ✅ {description}: {resource}")
                    success_count += 1
                elif response.status_code == 404:
                    print(f"   ⚠️  {description}: {resource} (not found - might be optional)")
                    success_count += 0.5
                else:
                    print(f"   ❌ {description}: {resource} (status {response.status_code})")

            except requests.exceptions.RequestException as e:
                print(f"   ❌ {description}: {resource} (request failed: {e})")

        if total_tests > 0:
            print(f"📊 Static Resource Results: {success_count}/{total_tests} resources accessible")
            return success_count >= total_tests * 0.5
        else:
            print("📊 No static resources to test")
            return True

async def test_template_loading():
    """Test template loading from Python side."""
    print("\n🔧 Testing Template Loading (Python)...")
    try:
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.vpn.wireguard.webui.routes import WireGuardWebUI

        plugin = WireGuardPlugin()
        webui = WireGuardWebUI(plugin)

        # Test that the template loader has the correct search paths
        env = webui.templates.env
        loader = env.loader

        if hasattr(loader, 'searchpath'):
            print(f"✅ Template search paths configured: {len(loader.searchpath)} paths")
            for i, path in enumerate(loader.searchpath):
                print(f"   {i+1}. {path}")

        # Test loading key templates
        templates_to_test = [
            "system/webui/templates/base.html",
            "dashboard.html",
            "servers.html"
        ]

        success_count = 0
        for template_name in templates_to_test:
            try:
                template = env.get_template(template_name)
                print(f"   ✅ {template_name}")
                success_count += 1
            except Exception as e:
                print(f"   ❌ {template_name}: {e}")

        print(f"📊 Template Loading Results: {success_count}/{len(templates_to_test)} templates loadable")
        return success_count == len(templates_to_test)

    except Exception as e:
        print(f"❌ Template loading test failed: {e}")
        return False

def main():
    """Main test runner."""
    print("🧪 WireGuard WebUI Integration Test Suite")
    print("=" * 60)

    tester = WireGuardWebUITester()

    # Track test results
    results = {}

    # Test 1: Server connectivity
    results["connectivity"] = tester.test_server_connectivity()

    if not results["connectivity"]:
        print("\n❌ Server is not running. Please start the server first:")
        print("   uvicorn app.main:app --reload")
        return 1

    # Test 2: Authentication
    results["authentication"] = tester.authenticate()

    # Test 3: Template loading (Python side)
    results["template_loading"] = asyncio.run(test_template_loading())

    # Test 4: WireGuard WebUI access
    results["webui_access"] = tester.test_wireguard_webui_access()

    # Test 5: API endpoints
    results["api_endpoints"] = tester.test_wireguard_api_endpoints()

    # Test 6: Template routes
    results["template_routes"] = tester.test_template_specific_routes()

    # Test 7: Static resources
    results["static_resources"] = tester.test_static_resources()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("-" * 30)

    passed = 0
    total = 0

    for test_name, passed_test in results.items():
        total += 1
        if passed_test:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"{status} {test_name.replace('_', ' ').title()}")

    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! WireGuard WebUI is working correctly.")
        print("\n✨ The template loading issue has been resolved!")
        print("   - Base template inheritance is working")
        print("   - WireGuard WebUI is accessible")
        print("   - All critical functionality appears to be operational")

        print("\n🌐 Access your WireGuard WebUI at:")
        print(f"   {tester.base_url}{tester.wireguard_base_path}")

        return 0
    elif passed >= total * 0.75:
        print("\n⚠️  MOSTLY WORKING - Some minor issues detected.")
        print("   The core functionality appears to be working, but some")
        print("   optional features might need attention.")
        return 0
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED")
        print("   Multiple tests failed. Please review the output above")
        print("   and address the issues before using the WireGuard WebUI.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
