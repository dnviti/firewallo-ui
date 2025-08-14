#!/usr/bin/env python3
"""Test script to verify WebUI authentication functionality."""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.plugins.system.webui.auth_service import WebUIAuthService
from app.auth.models import hash_password, verify_password, create_access_token, verify_token
from app.core.startup import CoreUserRepository


async def test_authentication():
    """Test the authentication service functionality."""
    print("🔐 Testing Firewallo WebUI Authentication")
    print("=" * 50)

    # Test 1: Initialize auth service
    print("\n1. Initializing authentication service...")
    auth_service = WebUIAuthService(Path("/tmp/test_sessions"))
    print("✅ Authentication service initialized")

    # Test 2: Create test user
    print("\n2. Creating test user...")
    user_repo = CoreUserRepository()

    test_user = {
        "username": "testuser",
        "email": "test@firewallo.local",
        "hashed_password": hash_password("testpass123"),
        "is_active": True,
        "is_superuser": False,
        "role": "user",
        "first_name": "Test",
        "last_name": "User"
    }

    try:
        # Try to create the user (will fail if already exists)
        user_repo.create_user(test_user)
        print("✅ Test user created successfully")
    except Exception as e:
        print(f"ℹ️  Test user might already exist: {e}")

    # Test 3: Verify password hashing
    print("\n3. Testing password verification...")
    stored_hash = test_user["hashed_password"]

    if verify_password("testpass123", stored_hash):
        print("✅ Password verification successful")
    else:
        print("❌ Password verification failed")
        return False

    if not verify_password("wrongpassword", stored_hash):
        print("✅ Wrong password correctly rejected")
    else:
        print("❌ Wrong password incorrectly accepted")
        return False

    # Test 4: JWT Token creation and verification
    print("\n4. Testing JWT tokens...")
    token_data = {"sub": "testuser"}
    token = create_access_token(token_data)
    print(f"✅ JWT token created: {token[:50]}...")

    try:
        payload = verify_token(token)
        if payload.get("sub") == "testuser":
            print("✅ JWT token verification successful")
        else:
            print("❌ JWT token payload incorrect")
            return False
    except Exception as e:
        print(f"❌ JWT token verification failed: {e}")
        return False

    # Test 5: Session management
    print("\n5. Testing session management...")

    session_data = {
        "username": "testuser",
        "email": "test@firewallo.local",
        "role": "user",
        "ip_address": "127.0.0.1",
        "user_agent": "Test Browser"
    }

    session_id = auth_service.create_session("testuser", session_data)
    print(f"✅ Session created: {session_id[:16]}...")

    # Retrieve session
    retrieved_session = auth_service.get_session(session_id)
    if retrieved_session and retrieved_session["user_id"] == "testuser":
        print("✅ Session retrieval successful")
    else:
        print("❌ Session retrieval failed")
        return False

    # Test session count
    session_count = auth_service.get_session_count()
    print(f"✅ Active sessions: {session_count}")

    # Test 6: Mock request authentication
    print("\n6. Testing request authentication simulation...")

    class MockClient:
        def __init__(self, host):
            self.host = host

    class MockHeaders:
        def __init__(self, headers):
            self._headers = headers

        def get(self, key, default=None):
            return self._headers.get(key, default)

    class MockCookies:
        def __init__(self, cookies):
            self._cookies = cookies

        def get(self, key, default=None):
            return self._cookies.get(key, default)

    class MockRequest:
        def __init__(self, cookies=None, headers=None, client_host="127.0.0.1"):
            self.cookies = MockCookies(cookies or {})
            self.headers = MockHeaders(headers or {})
            self.client = MockClient(client_host)

    # Test with session cookie
    mock_request = MockRequest(cookies={"session_id": session_id})
    user = await auth_service.check_authentication(mock_request)

    if user and user.username == "testuser":
        print("✅ Session-based authentication successful")
    else:
        print("❌ Session-based authentication failed")
        return False

    # Test with access token
    mock_request_token = MockRequest(cookies={"access_token": token})
    user_token = await auth_service.check_authentication(mock_request_token)

    if user_token and user_token.username == "testuser":
        print("✅ Token-based authentication successful")
    else:
        print("❌ Token-based authentication failed")
        return False

    # Test with invalid session
    mock_request_invalid = MockRequest(cookies={"session_id": "invalid_session"})
    user_invalid = await auth_service.check_authentication(mock_request_invalid)

    if user_invalid is None:
        print("✅ Invalid session correctly rejected")
    else:
        print("❌ Invalid session incorrectly accepted")
        return False

    # Test 7: Session cleanup
    print("\n7. Testing session cleanup...")
    initial_count = auth_service.get_session_count()

    # Destroy the test session
    auth_service.destroy_session(session_id)

    final_count = auth_service.get_session_count()
    if final_count == initial_count - 1:
        print("✅ Session cleanup successful")
    else:
        print(f"❌ Session cleanup failed: {initial_count} -> {final_count}")
        return False

    # Test 8: Public path checking
    print("\n8. Testing public path checking...")

    public_paths = ["/login", "/static/css/style.css", "/favicon.ico"]
    private_paths = ["/dashboard", "/firewall", "/api/system"]

    for path in public_paths:
        if auth_service.is_public_path(path):
            print(f"✅ Public path correctly identified: {path}")
        else:
            print(f"❌ Public path incorrectly rejected: {path}")
            return False

    for path in private_paths:
        if not auth_service.is_public_path(path):
            print(f"✅ Private path correctly identified: {path}")
        else:
            print(f"❌ Private path incorrectly accepted as public: {path}")
            return False

    print("\n" + "=" * 50)
    print("🎉 All authentication tests passed!")
    print("✅ The WebUI authentication system is working correctly")

    return True


async def test_user_creation():
    """Test user creation and retrieval."""
    print("\n📝 Testing user database operations...")

    user_repo = CoreUserRepository()

    # Test admin user exists
    admin_user = user_repo.get_user_by_username("admin")
    if admin_user:
        print("✅ Admin user exists in database")
        print(f"   Username: {admin_user.get('username')}")
        print(f"   Email: {admin_user.get('email', 'N/A')}")
        print(f"   Role: {admin_user.get('role', 'N/A')}")
        print(f"   Is Superuser: {admin_user.get('is_superuser', False)}")
        print(f"   Is Active: {admin_user.get('is_active', False)}")
    else:
        print("❌ Admin user not found in database")
        return False

    # List all users
    all_users = user_repo.list_users()
    print(f"✅ Total users in database: {len(all_users)}")

    for user in all_users[:5]:  # Show first 5 users
        print(f"   - {user.get('username')} ({user.get('role', 'user')})")

    return True


def print_login_instructions():
    """Print instructions for testing login via web interface."""
    print("\n" + "=" * 50)
    print("🌐 Web Interface Testing Instructions")
    print("=" * 50)

    print("\n1. Start the Firewallo application:")
    print("   cd firewallo-ui")
    print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

    print("\n2. Open your web browser and go to:")
    print("   http://localhost:8000")

    print("\n3. You should be automatically redirected to the login page")
    print("   URL should be: http://localhost:8000/login")

    print("\n4. Test login with default admin credentials:")
    print("   Username: admin")
    print("   Password: admin")

    print("\n5. Or test with the test user created above:")
    print("   Username: testuser")
    print("   Password: testpass123")

    print("\n6. After successful login, you should be redirected to:")
    print("   http://localhost:8000/dashboard")

    print("\n7. Test logout by visiting:")
    print("   http://localhost:8000/logout")

    print("\n8. Try accessing protected pages without login:")
    print("   http://localhost:8000/dashboard")
    print("   http://localhost:8000/firewall")
    print("   (Should redirect to login page)")

    print("\nIf authentication is working correctly:")
    print("✅ Unauthenticated users will be redirected to /login")
    print("✅ Login page will authenticate and create sessions")
    print("✅ Authenticated users can access protected pages")
    print("✅ Logout will clear sessions and redirect to login")


async def main():
    """Main test function."""
    try:
        print("🚀 Starting Firewallo WebUI Authentication Tests")

        # Test user database operations
        if not await test_user_creation():
            print("❌ User database tests failed")
            return 1

        # Test authentication functionality
        if not await test_authentication():
            print("❌ Authentication tests failed")
            return 1

        # Print web testing instructions
        print_login_instructions()

        return 0

    except Exception as e:
        print(f"💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
