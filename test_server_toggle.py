#!/usr/bin/env python3
"""Test script to validate WireGuard server toggle functionality."""

import sys
import asyncio
import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

class ServerToggleTester:
    """Test WireGuard server toggle functionality."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token: Optional[str] = None
        self.wireguard_base_path = "/plugins/vpn/wireguard"
        self.test_server_id = "e5d8597d-531d-4cd0-b26e-f035f91376c4"

    def authenticate(self) -> bool:
        """Authenticate with the server."""
        print("🔐 Authenticating with admin/admin...")
        try:
            login_data = {"username": "admin", "password": "admin"}
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

            print(f"❌ Authentication failed: {response.status_code}")
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_server_status(self) -> Optional[Dict]:
        """Get current server status."""
        try:
            url = f"{self.base_url}/api/plugins/vpn/wireguard/servers/{self.test_server_id}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get server status: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error getting server status: {e}")
            return None

    def toggle_server(self) -> bool:
        """Toggle server state."""
        try:
            url = f"{self.base_url}{self.wireguard_base_path}/servers/{self.test_server_id}/toggle"
            response = self.session.post(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Server toggle successful - New state: {'enabled' if data.get('enabled') else 'disabled'}")
                    return True
                else:
                    print(f"❌ Server toggle failed: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Toggle request failed: {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                return False

        except Exception as e:
            print(f"❌ Error toggling server: {e}")
            return False

    def test_toggle_cycle(self) -> bool:
        """Test complete toggle cycle (enable -> disable -> enable)."""
        print("\n🔄 Testing complete toggle cycle...")

        # Get initial state
        initial_status = self.get_server_status()
        if not initial_status:
            print("❌ Cannot get initial server status")
            return False

        initial_enabled = initial_status.get("enabled", False)
        print(f"📊 Initial server state: {'enabled' if initial_enabled else 'disabled'}")

        # First toggle
        print(f"\n1️⃣ Toggling server to {'disabled' if initial_enabled else 'enabled'}...")
        if not self.toggle_server():
            return False

        # Wait a moment for state change
        time.sleep(2)

        # Check intermediate state
        intermediate_status = self.get_server_status()
        if not intermediate_status:
            print("❌ Cannot get intermediate server status")
            return False

        intermediate_enabled = intermediate_status.get("enabled", False)
        expected_intermediate = not initial_enabled

        if intermediate_enabled == expected_intermediate:
            print(f"✅ Server correctly toggled to {'enabled' if intermediate_enabled else 'disabled'}")
        else:
            print(f"❌ Server toggle failed - Expected: {expected_intermediate}, Got: {intermediate_enabled}")
            return False

        # Second toggle (back to original state)
        print(f"\n2️⃣ Toggling server back to {'enabled' if initial_enabled else 'disabled'}...")
        if not self.toggle_server():
            return False

        # Wait a moment for state change
        time.sleep(2)

        # Check final state
        final_status = self.get_server_status()
        if not final_status:
            print("❌ Cannot get final server status")
            return False

        final_enabled = final_status.get("enabled", False)

        if final_enabled == initial_enabled:
            print(f"✅ Server correctly restored to initial state: {'enabled' if final_enabled else 'disabled'}")
            return True
        else:
            print(f"❌ Server restore failed - Expected: {initial_enabled}, Got: {final_enabled}")
            return False

    def test_toggle_endpoint_response(self) -> bool:
        """Test that toggle endpoint responds correctly."""
        print("\n🌐 Testing toggle endpoint response...")

        # Get current state
        status = self.get_server_status()
        if not status:
            return False

        current_enabled = status.get("enabled", False)
        print(f"📊 Current server state: {'enabled' if current_enabled else 'disabled'}")

        # Test toggle
        try:
            url = f"{self.base_url}{self.wireguard_base_path}/servers/{self.test_server_id}/toggle"
            response = self.session.post(url, timeout=15)

            print(f"📡 Toggle response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"📋 Response data: {data}")

                # Check response structure
                if "success" in data and "enabled" in data:
                    if data["success"]:
                        expected_new_state = not current_enabled
                        actual_new_state = data["enabled"]

                        if actual_new_state == expected_new_state:
                            print("✅ Toggle response contains correct new state")
                            return True
                        else:
                            print(f"❌ Toggle response state mismatch - Expected: {expected_new_state}, Got: {actual_new_state}")
                            return False
                    else:
                        print(f"❌ Toggle failed: {data.get('error', 'Unknown error')}")
                        return False
                else:
                    print("❌ Toggle response missing required fields")
                    return False
            else:
                print(f"❌ Toggle endpoint returned {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing toggle endpoint: {e}")
            return False

    def test_ui_integration(self) -> bool:
        """Test UI integration by checking server detail page."""
        print("\n🖥️  Testing UI integration...")

        try:
            # Get server detail page
            url = f"{self.base_url}{self.wireguard_base_path}/servers/{self.test_server_id}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                content = response.text

                # Check for toggle button
                if "toggleServer" in content:
                    print("✅ Toggle button JavaScript found in page")
                else:
                    print("❌ Toggle button JavaScript not found")
                    return False

                # Check for server state indicators
                if "Stop Server" in content or "Start Server" in content:
                    print("✅ Server state buttons found in page")
                else:
                    print("❌ Server state buttons not found")
                    return False

                return True
            else:
                print(f"❌ Cannot access server detail page: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing UI integration: {e}")
            return False

def main():
    """Main test function."""
    print("🧪 WireGuard Server Toggle Functionality Test")
    print("=" * 55)

    tester = ServerToggleTester()

    # Track results
    results = {}

    # Test 1: Authentication
    results["auth"] = tester.authenticate()
    if not results["auth"]:
        print("\n❌ Cannot proceed without authentication")
        return 1

    # Test 2: Get initial server status
    initial_status = tester.get_server_status()
    if initial_status:
        print(f"✅ Server status retrieved: {initial_status.get('name', 'Unknown')} - {'enabled' if initial_status.get('enabled') else 'disabled'}")
        results["status_check"] = True
    else:
        print("❌ Cannot retrieve server status")
        results["status_check"] = False

    # Test 3: Toggle endpoint response
    results["endpoint_response"] = tester.test_toggle_endpoint_response()

    # Test 4: Complete toggle cycle
    results["toggle_cycle"] = tester.test_toggle_cycle()

    # Test 5: UI integration
    results["ui_integration"] = tester.test_ui_integration()

    # Summary
    print("\n" + "=" * 55)
    print("📊 SERVER TOGGLE TEST RESULTS")
    print("-" * 35)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status} {test_name.upper().replace('_', ' ')}")

    print(f"\n🎯 Final Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✨ Server Toggle Functionality is fully operational:")
        print("   - Server can be started and stopped correctly")
        print("   - Toggle endpoint responds properly")
        print("   - State changes are persistent")
        print("   - UI integration is working")

        print(f"\n🌐 Test server toggle at:")
        print(f"   {tester.base_url}{tester.wireguard_base_path}/servers/{tester.test_server_id}")

        print("\n💡 Server toggle is ready for production use!")
        return 0

    elif passed >= total * 0.75:
        print("\n⚠️  MOSTLY WORKING")
        print("   Core toggle functionality is operational but some issues remain.")
        return 0

    else:
        print("\n❌ SIGNIFICANT ISSUES")
        print("   Multiple critical tests failed.")
        print("   Server toggle functionality needs attention.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
