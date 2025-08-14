#!/usr/bin/env python3
"""
Comprehensive login flow test script for Firewallo WebUI.
Tests the complete authentication flow including default credentials.
"""

import requests
import sys
from urllib.parse import urljoin


class FirewalloLoginTester:
    """Test the Firewallo login flow."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def test_unauthenticated_access(self):
        """Test that unauthenticated users are redirected to login."""
        print("🔒 Testing unauthenticated access...")

        # Test root URL
        response = self.session.get(self.base_url, allow_redirects=False)
        if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
            print("  ✅ Root URL redirects to login")
        else:
            print(f"  ❌ Root URL failed: {response.status_code}")
            return False

        # Test dashboard URL
        response = self.session.get(f"{self.base_url}/dashboard", allow_redirects=False)
        if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
            print("  ✅ Dashboard redirects to login")
        else:
            print(f"  ❌ Dashboard access failed: {response.status_code}")
            return False

        return True

    def test_login_page_access(self):
        """Test that login page is accessible."""
        print("📄 Testing login page accessibility...")

        response = self.session.get(f"{self.base_url}/login")
        if response.status_code == 200:
            # Check for expected content
            content = response.text
            if "Welcome Back" in content and "Default Credentials" in content:
                print("  ✅ Login page loads with default credentials info")
                return True
            else:
                print("  ⚠️  Login page loads but missing expected content")
                return True
        else:
            print(f"  ❌ Login page failed: {response.status_code}")
            return False

    def test_default_credentials_login(self):
        """Test login with default admin credentials."""
        print("🔑 Testing login with default credentials...")

        # Test API login
        login_data = {
            "username": "admin",
            "password": "admin",
            "grant_type": "password"
        }

        response = self.session.post(f"{self.base_url}/api/auth/login", data=login_data)

        if response.status_code == 200:
            try:
                data = response.json()
                if "access_token" in data:
                    print("  ✅ API login successful")
                    self.access_token = data["access_token"]
                    return True
                else:
                    print("  ❌ API login failed: No access token in response")
                    return False
            except Exception as e:
                print(f"  ❌ API login failed: {e}")
                return False
        else:
            print(f"  ❌ API login failed: {response.status_code}")
            try:
                error = response.json()
                print(f"      Error: {error.get('detail', 'Unknown error')}")
            except:
                pass
            return False

    def test_authenticated_dashboard_access(self):
        """Test dashboard access with authentication."""
        print("🏠 Testing authenticated dashboard access...")

        if not hasattr(self, 'access_token'):
            print("  ❌ No access token available")
            return False

        # Set the access token as a cookie
        self.session.cookies.set('access_token', self.access_token)

        response = self.session.get(f"{self.base_url}/dashboard")

        if response.status_code == 200:
            content = response.text
            if "Dashboard" in content and "Firewallo" in content:
                print("  ✅ Dashboard loads successfully for authenticated user")
                return True
            else:
                print("  ⚠️  Dashboard loads but missing expected content")
                return True
        else:
            print(f"  ❌ Dashboard access failed: {response.status_code}")
            return False

    def test_authenticated_login_redirect(self):
        """Test that authenticated users are redirected from login page."""
        print("🔄 Testing authenticated user login page redirect...")

        if not hasattr(self, 'access_token'):
            print("  ❌ No access token available")
            return False

        response = self.session.get(f"{self.base_url}/login", allow_redirects=False)

        if response.status_code == 302 and "/dashboard" in response.headers.get("Location", ""):
            print("  ✅ Authenticated user redirected from login to dashboard")
            return True
        else:
            print(f"  ❌ Login redirect failed: {response.status_code}")
            return False

    def test_api_access_with_token(self):
        """Test API access with Bearer token."""
        print("🔧 Testing API access with Bearer token...")

        if not hasattr(self, 'access_token'):
            print("  ❌ No access token available")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.session.get(f"{self.base_url}/webui/status", headers=headers)

        if response.status_code == 200:
            try:
                data = response.json()
                if "status" in data and "version" in data:
                    print("  ✅ API access with Bearer token successful")
                    print(f"      WebUI Status: {data['status']}")
                    print(f"      Version: {data['version']}")
                    return True
                else:
                    print("  ⚠️  API responded but missing expected data")
                    return True
            except Exception as e:
                print(f"  ❌ API response parsing failed: {e}")
                return False
        else:
            print(f"  ❌ API access failed: {response.status_code}")
            return False

    def test_logout_functionality(self):
        """Test logout functionality."""
        print("🚪 Testing logout functionality...")

        if not hasattr(self, 'access_token'):
            print("  ❌ No access token available")
            return False

        response = self.session.get(f"{self.base_url}/logout", allow_redirects=False)

        if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
            # Check if cookies are cleared
            cookies_cleared = False
            set_cookie_headers = response.headers.get("Set-Cookie", "")
            if isinstance(set_cookie_headers, str):
                set_cookie_headers = [set_cookie_headers]
            elif hasattr(set_cookie_headers, '__iter__'):
                set_cookie_headers = list(set_cookie_headers)
            else:
                set_cookie_headers = []

            for header in set_cookie_headers:
                if "access_token=" in header and "Max-Age=0" in header:
                    cookies_cleared = True
                    break

            if cookies_cleared:
                print("  ✅ Logout successful - redirected to login and cookies cleared")
                return True
            else:
                print("  ⚠️  Logout redirected but cookies may not be cleared")
                return True
        else:
            print(f"  ❌ Logout failed: {response.status_code}")
            return False

    def test_post_logout_access(self):
        """Test that access is denied after logout."""
        print("🔐 Testing post-logout access denial...")

        # Clear session cookies to simulate post-logout state
        self.session.cookies.clear()

        response = self.session.get(f"{self.base_url}/dashboard", allow_redirects=False)

        if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
            print("  ✅ Post-logout access properly denied")
            return True
        else:
            print(f"  ❌ Post-logout access check failed: {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all authentication tests."""
        print("🚀 Starting Firewallo WebUI Authentication Tests")
        print("=" * 60)

        tests = [
            self.test_unauthenticated_access,
            self.test_login_page_access,
            self.test_default_credentials_login,
            self.test_authenticated_dashboard_access,
            self.test_authenticated_login_redirect,
            self.test_api_access_with_token,
            self.test_logout_functionality,
            self.test_post_logout_access
        ]

        passed = 0
        failed = 0

        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  💥 Test crashed: {e}")
                failed += 1
            print()

        print("=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")

        if failed == 0:
            print("🎉 All tests passed! Authentication system is working correctly.")
            print()
            print("ℹ️  Default Login Credentials:")
            print("   Username: admin")
            print("   Password: admin")
            print()
            print("🌐 You can now test in your browser:")
            print(f"   {self.base_url}")
            return True
        else:
            print("❌ Some tests failed. Please check the authentication system.")
            return False


def main():
    """Main test function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Firewallo WebUI authentication")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL of the Firewallo application")

    args = parser.parse_args()

    tester = FirewalloLoginTester(args.url)

    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
