#!/usr/bin/env python3
"""
Authentication API endpoint tests for Firewallo UI.

Tests the authentication-related API endpoints including:
- User login/logout
- Token management
- Password operations
- Session handling
- Authorization checks
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import status
import jwt
from datetime import datetime, timedelta

# Test markers
pytestmark = [pytest.mark.api, pytest.mark.auth, pytest.mark.asyncio]


class TestLoginEndpoints:
    """Test user login endpoints."""

    async def test_login_success(self, test_client: AsyncClient, mock_user):
        """Test successful user login."""
        login_data = {
            "username": "testuser",
            "password": "correct_password"
        }

        with patch('app.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = mock_user

            with patch('app.auth.create_access_token') as mock_create_token:
                mock_create_token.return_value = "test-access-token"

                response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testuser"

    async def test_login_invalid_credentials(self, test_client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "testuser",
            "password": "wrong_password"
        }

        with patch('app.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = None

            response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "error" in data
        assert "Invalid credentials" in data["error"]

    async def test_login_missing_username(self, test_client: AsyncClient):
        """Test login with missing username."""
        login_data = {
            "password": "password123"
        }

        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_missing_password(self, test_client: AsyncClient):
        """Test login with missing password."""
        login_data = {
            "username": "testuser"
        }

        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_empty_credentials(self, test_client: AsyncClient):
        """Test login with empty credentials."""
        login_data = {
            "username": "",
            "password": ""
        }

        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_login_user_disabled(self, test_client: AsyncClient):
        """Test login with disabled user account."""
        login_data = {
            "username": "disabled_user",
            "password": "correct_password"
        }

        disabled_user = {
            "id": "disabled-user-id",
            "username": "disabled_user",
            "email": "disabled@example.com",
            "is_active": False,
            "is_admin": False
        }

        with patch('app.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = disabled_user

            response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "Account is disabled" in data["error"]

    @patch('app.auth.rate_limiter.is_rate_limited')
    async def test_login_rate_limiting(self, mock_rate_limiter, test_client: AsyncClient):
        """Test login rate limiting."""
        mock_rate_limiter.return_value = True

        login_data = {
            "username": "testuser",
            "password": "password123"
        }

        response = await test_client.post("/api/auth/login", json=login_data)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert "rate limit" in data["error"].lower()


class TestLogoutEndpoints:
    """Test user logout endpoints."""

    async def test_logout_success(self, test_client: AsyncClient, mock_auth_token):
        """Test successful user logout."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.invalidate_token') as mock_invalidate:
            mock_invalidate.return_value = True

            response = await test_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Successfully logged out"

    async def test_logout_without_token(self, test_client: AsyncClient):
        """Test logout without authentication token."""
        response = await test_client.post("/api/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_logout_invalid_token(self, test_client: AsyncClient):
        """Test logout with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}

        with patch('app.auth.verify_token') as mock_verify:
            mock_verify.side_effect = jwt.InvalidTokenError("Invalid token")

            response = await test_client.post("/api/auth/logout", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_logout_all_sessions(self, test_client: AsyncClient, mock_auth_token):
        """Test logout from all sessions."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.invalidate_all_user_tokens') as mock_invalidate_all:
            mock_invalidate_all.return_value = True

            response = await test_client.post("/api/auth/logout-all", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "all sessions" in data["message"].lower()


class TestTokenManagement:
    """Test token management endpoints."""

    async def test_refresh_token_success(self, test_client: AsyncClient, mock_auth_token):
        """Test successful token refresh."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.refresh_access_token') as mock_refresh:
            new_token_data = {
                "access_token": "new-access-token",
                "token_type": "bearer",
                "expires_in": 3600
            }
            mock_refresh.return_value = new_token_data

            response = await test_client.post("/api/auth/refresh", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        assert data["access_token"] == "new-access-token"

    async def test_refresh_token_expired(self, test_client: AsyncClient):
        """Test token refresh with expired token."""
        headers = {"Authorization": "Bearer expired-token"}

        with patch('app.auth.verify_token') as mock_verify:
            mock_verify.side_effect = jwt.ExpiredSignatureError("Token expired")

            response = await test_client.post("/api/auth/refresh", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "expired" in data["error"].lower()

    async def test_verify_token_valid(self, test_client: AsyncClient, mock_auth_token):
        """Test token verification with valid token."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        response = await test_client.get("/api/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "valid" in data
        assert data["valid"] is True
        assert "user" in data

    async def test_verify_token_invalid(self, test_client: AsyncClient):
        """Test token verification with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}

        with patch('app.auth.verify_token') as mock_verify:
            mock_verify.side_effect = jwt.InvalidTokenError("Invalid token")

            response = await test_client.get("/api/auth/verify", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_token_info(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving token information."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.get_token_info') as mock_get_info:
            token_info = {
                "user_id": "test-user-id",
                "username": "testuser",
                "issued_at": "2023-01-01T12:00:00Z",
                "expires_at": "2023-01-01T13:00:00Z",
                "scopes": ["read", "write"]
            }
            mock_get_info.return_value = token_info

            response = await test_client.get("/api/auth/token-info", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_id" in data
        assert "expires_at" in data
        assert "scopes" in data


class TestPasswordOperations:
    """Test password-related operations."""

    async def test_change_password_success(self, test_client: AsyncClient, mock_auth_token):
        """Test successful password change."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        password_data = {
            "current_password": "old_password",
            "new_password": "new_secure_password123",
            "confirm_password": "new_secure_password123"
        }

        with patch('app.auth.verify_current_password') as mock_verify_current:
            mock_verify_current.return_value = True

            with patch('app.auth.update_password') as mock_update:
                mock_update.return_value = True

                response = await test_client.put("/api/auth/change-password",
                                                json=password_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password changed successfully"

    async def test_change_password_wrong_current(self, test_client: AsyncClient, mock_auth_token):
        """Test password change with wrong current password."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        password_data = {
            "current_password": "wrong_password",
            "new_password": "new_secure_password123",
            "confirm_password": "new_secure_password123"
        }

        with patch('app.auth.verify_current_password') as mock_verify_current:
            mock_verify_current.return_value = False

            response = await test_client.put("/api/auth/change-password",
                                            json=password_data, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "current password" in data["error"].lower()

    async def test_change_password_mismatch(self, test_client: AsyncClient, mock_auth_token):
        """Test password change with mismatched new passwords."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        password_data = {
            "current_password": "old_password",
            "new_password": "new_password123",
            "confirm_password": "different_password123"
        }

        response = await test_client.put("/api/auth/change-password",
                                        json=password_data, headers=headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_change_password_weak(self, test_client: AsyncClient, mock_auth_token):
        """Test password change with weak password."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        password_data = {
            "current_password": "old_password",
            "new_password": "weak",
            "confirm_password": "weak"
        }

        with patch('app.auth.validate_password_strength') as mock_validate:
            mock_validate.return_value = False

            response = await test_client.put("/api/auth/change-password",
                                            json=password_data, headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "password strength" in data["error"].lower()

    async def test_forgot_password_request(self, test_client: AsyncClient):
        """Test password reset request."""
        reset_data = {
            "email": "user@example.com"
        }

        with patch('app.auth.send_password_reset_email') as mock_send_email:
            mock_send_email.return_value = True

            response = await test_client.post("/api/auth/forgot-password", json=reset_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "reset email sent" in data["message"].lower()

    async def test_forgot_password_invalid_email(self, test_client: AsyncClient):
        """Test password reset request with invalid email."""
        reset_data = {
            "email": "nonexistent@example.com"
        }

        with patch('app.auth.find_user_by_email') as mock_find_user:
            mock_find_user.return_value = None

            # Should still return success for security reasons
            response = await test_client.post("/api/auth/forgot-password", json=reset_data)

        assert response.status_code == status.HTTP_200_OK

    async def test_reset_password_success(self, test_client: AsyncClient):
        """Test successful password reset."""
        reset_data = {
            "token": "valid-reset-token",
            "new_password": "new_secure_password123",
            "confirm_password": "new_secure_password123"
        }

        with patch('app.auth.verify_reset_token') as mock_verify_token:
            mock_verify_token.return_value = {"user_id": "test-user-id"}

            with patch('app.auth.reset_user_password') as mock_reset:
                mock_reset.return_value = True

                response = await test_client.post("/api/auth/reset-password", json=reset_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "password reset successfully" in data["message"].lower()

    async def test_reset_password_invalid_token(self, test_client: AsyncClient):
        """Test password reset with invalid token."""
        reset_data = {
            "token": "invalid-reset-token",
            "new_password": "new_secure_password123",
            "confirm_password": "new_secure_password123"
        }

        with patch('app.auth.verify_reset_token') as mock_verify_token:
            mock_verify_token.side_effect = jwt.InvalidTokenError("Invalid token")

            response = await test_client.post("/api/auth/reset-password", json=reset_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "invalid" in data["error"].lower()


class TestSessionManagement:
    """Test session management endpoints."""

    async def test_get_active_sessions(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving active sessions."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.get_user_sessions') as mock_get_sessions:
            mock_sessions = [
                {
                    "session_id": "session-1",
                    "created_at": "2023-01-01T12:00:00Z",
                    "last_activity": "2023-01-01T12:30:00Z",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                    "is_current": True
                },
                {
                    "session_id": "session-2",
                    "created_at": "2023-01-01T10:00:00Z",
                    "last_activity": "2023-01-01T11:00:00Z",
                    "ip_address": "192.168.1.101",
                    "user_agent": "Mobile App",
                    "is_current": False
                }
            ]
            mock_get_sessions.return_value = mock_sessions

            response = await test_client.get("/api/auth/sessions", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        current_session = next(s for s in data if s["is_current"])
        assert current_session["session_id"] == "session-1"

    async def test_revoke_session(self, test_client: AsyncClient, mock_auth_token):
        """Test revoking a specific session."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.revoke_session') as mock_revoke:
            mock_revoke.return_value = True

            response = await test_client.delete("/api/auth/sessions/session-2", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session revoked" in data["message"].lower()

    async def test_revoke_all_other_sessions(self, test_client: AsyncClient, mock_auth_token):
        """Test revoking all other sessions."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.revoke_other_sessions') as mock_revoke_others:
            mock_revoke_others.return_value = 3  # Number of revoked sessions

            response = await test_client.delete("/api/auth/sessions/others", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "3" in data["message"]
        assert "sessions revoked" in data["message"].lower()


class TestAuthorizationChecks:
    """Test authorization and permission checks."""

    async def test_admin_required_endpoint(self, test_client: AsyncClient, mock_admin_user):
        """Test endpoint that requires admin privileges."""
        with patch('app.auth.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_admin_user

            headers = {"Authorization": "Bearer admin-token"}
            response = await test_client.get("/api/auth/admin/users", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    async def test_admin_required_forbidden(self, test_client: AsyncClient, mock_user):
        """Test admin endpoint with non-admin user."""
        with patch('app.auth.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user  # Regular user, not admin

            headers = {"Authorization": "Bearer user-token"}
            response = await test_client.get("/api/auth/admin/users", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_permission_check(self, test_client: AsyncClient, mock_auth_token):
        """Test permission-based access control."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.check_permission') as mock_check_permission:
            mock_check_permission.return_value = True

            response = await test_client.get("/api/auth/protected-resource", headers=headers)

        assert response.status_code == status.HTTP_200_OK

    async def test_permission_denied(self, test_client: AsyncClient, mock_auth_token):
        """Test access denied due to insufficient permissions."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.check_permission') as mock_check_permission:
            mock_check_permission.return_value = False

            response = await test_client.get("/api/auth/protected-resource", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserProfile:
    """Test user profile endpoints."""

    async def test_get_current_user_profile(self, test_client: AsyncClient, mock_auth_token, mock_user):
        """Test retrieving current user profile."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user

            response = await test_client.get("/api/auth/profile", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "username" in data
        assert "email" in data
        assert "is_active" in data
        assert data["username"] == "testuser"

    async def test_update_user_profile(self, test_client: AsyncClient, mock_auth_token):
        """Test updating user profile."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        profile_data = {
            "email": "newemail@example.com",
            "first_name": "John",
            "last_name": "Doe"
        }

        with patch('app.auth.update_user_profile') as mock_update:
            mock_update.return_value = True

            response = await test_client.put("/api/auth/profile",
                                           json=profile_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Profile updated successfully"


class TestTwoFactorAuthentication:
    """Test two-factor authentication endpoints."""

    async def test_enable_2fa_setup(self, test_client: AsyncClient, mock_auth_token):
        """Test setting up 2FA."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.auth.setup_2fa') as mock_setup_2fa:
            mock_setup_2fa.return_value = {
                "secret": "BASE32SECRET",
                "qr_code": "data:image/png;base64,..."
            }

            response = await test_client.post("/api/auth/2fa/setup", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data

    async def test_verify_2fa_setup(self, test_client: AsyncClient, mock_auth_token):
        """Test verifying 2FA setup."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        verify_data = {
            "secret": "BASE32SECRET",
            "code": "123456"
        }

        with patch('app.auth.verify_2fa_setup') as mock_verify:
            mock_verify.return_value = True

            response = await test_client.post("/api/auth/2fa/verify",
                                            json=verify_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "2FA enabled successfully"

    async def test_disable_2fa(self, test_client: AsyncClient, mock_auth_token):
        """Test disabling 2FA."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        disable_data = {
            "password": "current_password",
            "code": "123456"
        }

        with patch('app.auth.disable_2fa') as mock_disable:
            mock_disable.return_value = True

            response = await test_client.post("/api/auth/2fa/disable",
                                            json=disable_data, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "2FA disabled successfully"


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    async def test_complete_auth_flow(self, test_client: AsyncClient, mock_user):
        """Test complete authentication flow."""
        # Login
        login_data = {"username": "testuser", "password": "password123"}

        with patch('app.auth.authenticate_user') as mock_auth:
            mock_auth.return_value = mock_user

            with patch('app.auth.create_access_token') as mock_create_token:
                mock_create_token.return_value = "test-access-token"

                login_response = await test_client.post("/api/auth/login", json=login_data)

        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()
        token = login_data["access_token"]

        # Verify token
        headers = {"Authorization": f"Bearer {token}"}
        verify_response = await test_client.get("/api/auth/verify", headers=headers)
        assert verify_response.status_code == status.HTTP_200_OK

        # Get profile
        profile_response = await test_client.get("/api/auth/profile", headers=headers)
        assert profile_response.status_code == status.HTTP_200_OK

        # Logout
        with patch('app.auth.invalidate_token') as mock_invalidate:
            mock_invalidate.return_value = True

            logout_response = await test_client.post("/api/auth/logout", headers=headers)

        assert logout_response.status_code == status.HTTP_200_OK

    async def test_token_lifecycle(self, test_client: AsyncClient, mock_auth_token):
        """Test token lifecycle management."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        # Verify token is valid
        verify_response = await test_client.get("/api/auth/verify", headers=headers)
        assert verify_response.status_code == status.HTTP_200_OK

        # Refresh token
        with patch('app.auth.refresh_access_token') as mock_refresh:
            new_token_data = {
                "access_token": "new-token",
                "token_type": "bearer",
                "expires_in": 3600
            }
            mock_refresh.return_value = new_token_data

            refresh_response = await test_client.post("/api/auth/refresh", headers=headers)

        assert refresh_response.status_code == status.HTTP_200_OK
        new_token = refresh_response.json()["access_token"]

        # Use new token
        new_headers = {"Authorization": f"Bearer {new_token}"}
        verify_new_response = await test_client.get("/api/auth/verify", headers=new_headers)
        assert verify_new_response.status_code == status.HTTP_200_OK
