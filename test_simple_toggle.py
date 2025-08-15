#!/usr/bin/env python3
"""Simple test for WireGuard server toggle functionality via WebUI."""

import sys
import requests
import time
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

def test_simple_toggle():
    """Test WireGuard server toggle functionality."""
    print("🧪 Simple WireGuard Server Toggle Test")
    print("=" * 45)

    base_url = "http://localhost:8000"
    wireguard_path = "/plugins/vpn/wireguard"
    server_id = "e5d8597d-531d-4cd0-b26e-f035f91376c4"

    session = requests.Session()

    # Step 1: Authenticate
    print("🔐 Authenticating...")
    try:
        login_data = {"username": "admin", "password": "admin"}
        response = session.post(f"{base_url}/api/auth/login", data=login_data, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
                print("✅ Authentication successful")
            else:
                print("❌ No access token received")
                return False
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

    # Step 2: Test server detail page access
    print("\n🌐 Testing server detail page access...")
    try:
        detail_url = f"{base_url}{wireguard_path}/servers/{server_id}"
        response = session.get(detail_url, timeout=10)

        if response.status_code == 200:
            content = response.text
            if "WireGuard" in content and ("Stop Server" in content or "Start Server" in content):
                print("✅ Server detail page accessible with toggle button")
            else:
                print("⚠️  Server detail page accessible but toggle button not found")
                return False
        else:
            print(f"❌ Server detail page not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing server detail page: {e}")
        return False

    # Step 3: Test toggle endpoint
    print("\n🔄 Testing toggle endpoint...")
    try:
        toggle_url = f"{base_url}{wireguard_path}/servers/{server_id}/toggle"

        print(f"   Making POST request to: {toggle_url}")
        response = session.post(toggle_url, timeout=15)

        print(f"   Response status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response data: {data}")

                if data.get("success"):
                    new_state = "enabled" if data.get("enabled") else "disabled"
                    print(f"✅ Toggle successful - Server is now: {new_state}")
                    return True
                else:
                    error_msg = data.get("error", "Unknown error")
                    print(f"❌ Toggle failed: {error_msg}")
                    return False
            except Exception as json_error:
                print(f"❌ Failed to parse JSON response: {json_error}")
                print(f"   Raw response: {response.text[:200]}")
                return False
        else:
            print(f"❌ Toggle request failed with status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Error testing toggle endpoint: {e}")
        return False

def main():
    """Main function."""
    success = test_simple_toggle()

    print("\n" + "=" * 45)
    if success:
        print("🎉 SERVER TOGGLE TEST PASSED!")
        print("\n✨ The server toggle functionality is working correctly.")
        print("   You can now use the Start/Stop button in the WireGuard WebUI.")
        print("\n🌐 Access your server at:")
        print("   http://localhost:8000/plugins/vpn/wireguard/servers/e5d8597d-531d-4cd0-b26e-f035f91376c4")
        return 0
    else:
        print("❌ SERVER TOGGLE TEST FAILED!")
        print("\n🔧 Possible issues:")
        print("   - Server may not exist")
        print("   - Authentication problems")
        print("   - Network connectivity issues")
        print("   - WireGuard service not running")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
