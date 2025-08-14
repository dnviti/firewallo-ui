"""Standalone authentication service for WebUI plugin."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

from app.auth.models import verify_token, User
from app.core.startup import CoreUserRepository

logger = logging.getLogger(__name__)


class WebUIAuthService:
    """Authentication service for WebUI plugin."""

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize authentication service."""
        self.session_dir = session_dir or Path("data/webui_sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)
        self._load_sessions()

    def _load_sessions(self):
        """Load existing sessions from storage."""
        session_file = self.session_dir / "sessions.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    # Filter out expired sessions
                    now = datetime.now().isoformat()
                    self.sessions = {
                        sid: session for sid, session in data.items()
                        if session.get('expires_at', '') > now
                    }
                logger.info(f"Loaded {len(self.sessions)} active sessions")
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.sessions = {}

    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            session_file = self.session_dir / "sessions.json"
            with open(session_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def create_session(self, user_id: str, user_data: Dict[str, Any], remember_me: bool = False) -> str:
        """Create a new session for user."""
        import secrets
        session_id = secrets.token_urlsafe(32)

        # Set expiration based on remember me option
        if remember_me:
            expires_at = datetime.now() + timedelta(days=30)
        else:
            expires_at = datetime.now() + self.session_timeout

        self.sessions[session_id] = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': datetime.now().isoformat(),
            'ip_address': user_data.get('ip_address'),
            'user_agent': user_data.get('user_agent'),
            'remember_me': remember_me
        }

        self._save_sessions()
        logger.info(f"Created session for user {user_id} (remember_me: {remember_me})")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if valid."""
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check expiration
        if datetime.fromisoformat(session['expires_at']) < datetime.now():
            self.destroy_session(session_id)
            return None

        # Update last activity
        session['last_activity'] = datetime.now().isoformat()
        self._save_sessions()

        return session

    def destroy_session(self, session_id: str):
        """Destroy a session."""
        if session_id in self.sessions:
            user_id = self.sessions[session_id].get('user_id', 'unknown')
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Destroyed session for user {user_id}")

    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now().isoformat()
        expired = [sid for sid, session in self.sessions.items()
                  if session.get('expires_at', '') < now]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def extend_session(self, session_id: str) -> bool:
        """Extend session expiration."""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Extend by original timeout period
        if session.get('remember_me', False):
            new_expiry = datetime.now() + timedelta(days=30)
        else:
            new_expiry = datetime.now() + self.session_timeout

        session['expires_at'] = new_expiry.isoformat()
        session['last_activity'] = datetime.now().isoformat()
        self._save_sessions()
        return True

    async def check_authentication(self, request: Request) -> Optional[User]:
        """Check if request is authenticated and return user object."""
        try:
            # 1. Try session cookie first
            session_id = request.cookies.get("session_id")
            if session_id:
                session = self.get_session(session_id)
                if session:
                    # Create User object from session data
                    user_data = session['user_data']
                    return User(user_data)

            # 2. Try access token cookie
            access_token = request.cookies.get("access_token")
            if access_token:
                try:
                    payload = verify_token(access_token)
                    username = payload.get("sub")
                    if username:
                        user_repo = CoreUserRepository()
                        user_data = user_repo.get_user_by_username(username)
                        if user_data and user_data.get("is_active", False):
                            return User(user_data)
                except Exception as e:
                    logger.debug(f"Token verification failed: {e}")

            # 3. Try Authorization header (for API access)
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = verify_token(token)
                    username = payload.get("sub")
                    if username:
                        user_repo = CoreUserRepository()
                        user_data = user_repo.get_user_by_username(username)
                        if user_data and user_data.get("is_active", False):
                            return User(user_data)
                except Exception as e:
                    logger.debug(f"Bearer token verification failed: {e}")

            return None

        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return None

    def require_authentication(self, for_api: bool = False):
        """Decorator to require authentication for routes."""
        def decorator(func):
            async def wrapper(request: Request, *args, **kwargs):
                user = await self.check_authentication(request)
                if not user:
                    if for_api:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication required"
                        )
                    else:
                        return RedirectResponse(url="/login", status_code=302)

                # Add user to request state
                request.state.user = user
                request.state.authenticated = True

                return await func(request, *args, **kwargs)
            return wrapper
        return decorator

    def is_public_path(self, path: str) -> bool:
        """Check if path should be accessible without authentication."""
        public_paths = {
            "/login",
            "/api/auth/login",
            "/api/auth/register",
            "/static",
            "/favicon.ico",
            "/health",
            "/api/health"
        }

        # Exact matches
        if path in public_paths:
            return True

        # Prefix matches for static assets
        for public_path in ["/static/"]:
            if path.startswith(public_path):
                return True

        return False

    def log_access(self, request: Request, user: User):
        """Log user access for auditing."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user': user.username,
                'method': request.method,
                'path': str(request.url.path),
                'ip': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }

            logger.info(f"Access: {user.username} {request.method} {request.url.path}")
        except Exception as e:
            logger.error(f"Failed to log access: {e}")

    def get_session_count(self) -> int:
        """Get current active session count."""
        return len(self.sessions)

    def get_user_sessions(self, user_id: str) -> list:
        """Get all sessions for a specific user."""
        user_sessions = []
        for session_id, session in self.sessions.items():
            if session.get('user_id') == user_id:
                user_sessions.append({
                    'session_id': session_id,
                    'created_at': session.get('created_at'),
                    'last_activity': session.get('last_activity'),
                    'ip_address': session.get('ip_address'),
                    'user_agent': session.get('user_agent'),
                    'expires_at': session.get('expires_at')
                })
        return user_sessions

    def revoke_user_sessions(self, user_id: str, except_session: Optional[str] = None):
        """Revoke all sessions for a user except the specified one."""
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.get('user_id') == user_id and session_id != except_session:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            self.destroy_session(session_id)

        logger.info(f"Revoked {len(sessions_to_remove)} sessions for user {user_id}")
        return len(sessions_to_remove)

    async def validate_session_security(self, request: Request, session: Dict[str, Any]) -> bool:
        """Validate session security (IP, user agent, etc.)."""
        try:
            # Check if IP address matches (optional security measure)
            current_ip = request.client.host if request.client else None
            session_ip = session.get('ip_address')

            # For now, we'll be lenient with IP checking due to NAT/proxy scenarios
            # In production, you might want to make this configurable

            # Check user agent for basic consistency
            current_ua = request.headers.get('User-Agent', '')
            session_ua = session.get('user_agent', '')

            # Basic user agent validation (allow some variation)
            if session_ua and current_ua:
                # Extract browser/version for comparison
                import re
                def extract_browser_info(ua):
                    # Simple browser detection
                    patterns = [
                        r'Chrome/[\d.]+',
                        r'Firefox/[\d.]+',
                        r'Safari/[\d.]+',
                        r'Edge/[\d.]+'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, ua)
                        if match:
                            return match.group(0)
                    return None

                session_browser = extract_browser_info(session_ua)
                current_browser = extract_browser_info(current_ua)

                # If we can't detect browsers or they don't match, log but don't block
                if session_browser and current_browser and session_browser != current_browser:
                    logger.warning(f"User agent mismatch for session: {session_browser} vs {current_browser}")
                    # Could return False here for stricter security

            return True

        except Exception as e:
            logger.error(f"Session security validation failed: {e}")
            return True  # Default to allowing on error


# Global auth service instance
_auth_service: Optional[WebUIAuthService] = None


def get_auth_service() -> WebUIAuthService:
    """Get global authentication service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = WebUIAuthService()
    return _auth_service


def require_auth(for_api: bool = False):
    """Convenience decorator for requiring authentication."""
    auth_service = get_auth_service()
    return auth_service.require_authentication(for_api=for_api)


async def get_current_user(request: Request) -> Optional[User]:
    """Get current authenticated user from request."""
    auth_service = get_auth_service()
    return await auth_service.check_authentication(request)
