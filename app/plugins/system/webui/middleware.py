"""Authentication and authorization middleware for WebUI plugin."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import MutableHeaders

from app.auth.models import verify_token, User
from .rbac.models import get_rbac_manager, PermissionScope, PermissionAction

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage user sessions with enhanced security."""

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize session manager."""
        self.session_dir = session_dir or Path("data/sessions")
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

    def create_session(self, user_id: str, user_data: Dict[str, Any]) -> str:
        """Create a new session for user."""
        import secrets
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + self.session_timeout

        self.sessions[session_id] = {
            'user_id': user_id,
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': datetime.now().isoformat(),
            'ip_address': user_data.get('ip_address'),
            'user_agent': user_data.get('user_agent'),
        }

        self._save_sessions()
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
            del self.sessions[session_id]
            self._save_sessions()

    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.now().isoformat()
        expired = [sid for sid, session in self.sessions.items()
                  if session.get('expires_at', '') < now]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired)} expired sessions")


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Enhanced authentication middleware with RBAC support."""

    def __init__(self, app, **kwargs):
        """Initialize authentication middleware."""
        super().__init__(app)
        self.session_manager = SessionManager()
        self.rbac_manager = get_rbac_manager()
        self.public_paths = {
            "/", "/login", "/api/auth/login", "/api/auth/register",
            "/static", "/favicon.ico", "/health", "/api/health"
        }
        self.api_prefix = "/api"

        # Path to permission mappings
        self.path_permissions = {
            "/dashboard": (PermissionScope.DASHBOARD, PermissionAction.VIEW),
            "/firewall": (PermissionScope.FIREWALL, PermissionAction.VIEW),
            "/network": (PermissionScope.NETWORK, PermissionAction.VIEW),
            "/monitoring": (PermissionScope.MONITORING, PermissionAction.VIEW),
            "/plugins": (PermissionScope.PLUGINS, PermissionAction.VIEW),
            "/logs": (PermissionScope.LOGS, PermissionAction.VIEW),
            "/settings": (PermissionScope.SETTINGS, PermissionAction.VIEW),
            "/users": (PermissionScope.USERS, PermissionAction.VIEW),
        }

        # API endpoint permissions
        self.api_permissions = {
            "GET": PermissionAction.VIEW,
            "POST": PermissionAction.CREATE,
            "PUT": PermissionAction.UPDATE,
            "PATCH": PermissionAction.UPDATE,
            "DELETE": PermissionAction.DELETE,
        }

    async def dispatch(self, request: Request, call_next):
        """Process authentication for each request."""
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Clean up expired sessions periodically
        if hasattr(request.app.state, 'last_cleanup'):
            if datetime.now() - request.app.state.last_cleanup > timedelta(hours=1):
                self.session_manager.cleanup_expired()
                request.app.state.last_cleanup = datetime.now()
        else:
            request.app.state.last_cleanup = datetime.now()

        try:
            # Try to authenticate the request
            user = await self._authenticate_request(request)

            if user:
                # Check permissions
                if not await self._check_permissions(request, user):
                    if request.url.path.startswith(self.api_prefix):
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Permission denied"}
                        )
                    else:
                        return RedirectResponse(url="/login", status_code=302)

                # Attach user to request state
                request.state.user = user
                request.state.authenticated = True

                # Log access
                await self._log_access(request, user)
            else:
                # No authentication found
                if request.url.path.startswith(self.api_prefix):
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Authentication required"}
                    )
                else:
                    return RedirectResponse(url="/login", status_code=302)

            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response)

            return response

        except HTTPException as e:
            if request.url.path.startswith(self.api_prefix):
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
            else:
                return RedirectResponse(url="/login", status_code=302)

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no authentication required)."""
        # Exact matches
        if path in self.public_paths:
            return True

        # Prefix matches
        for public_path in self.public_paths:
            if path.startswith(public_path + "/"):
                return True

        return False

    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """Authenticate request using various methods."""
        user = None

        # 1. Try session cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            session = self.session_manager.get_session(session_id)
            if session:
                user = User(session['user_data'])
                request.state.session = session
                return user

        # 2. Try Bearer token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = verify_token(token)
                username = payload.get("sub")
                if username:
                    # Get user from database
                    from app.core.startup import CoreUserRepository
                    user_repo = CoreUserRepository()
                    user_data = user_repo.get_user_by_username(username)
                    if user_data:
                        user = User(user_data)
                        return user
            except Exception as e:
                logger.debug(f"Token verification failed: {e}")

        # 3. Try access_token cookie (for web UI)
        access_token = request.cookies.get("access_token")
        if access_token:
            try:
                payload = verify_token(access_token)
                username = payload.get("sub")
                if username:
                    from app.core.startup import CoreUserRepository
                    user_repo = CoreUserRepository()
                    user_data = user_repo.get_user_by_username(username)
                    if user_data:
                        user = User(user_data)
                        return user
            except Exception as e:
                logger.debug(f"Cookie token verification failed: {e}")

        return None

    async def _check_permissions(self, request: Request, user: User) -> bool:
        """Check if user has required permissions for the request."""
        path = request.url.path
        method = request.method

        # Super admin always has access
        if user.is_superuser:
            return True

        # Check web UI path permissions
        for pattern, (scope, action) in self.path_permissions.items():
            if path.startswith(pattern):
                has_permission = self.rbac_manager.check_permission(
                    user.username, scope.value, action.value
                )
                if not has_permission:
                    logger.warning(
                        f"Permission denied for {user.username}: {scope.value}.{action.value} on {path}"
                    )
                    return False

        # Check API permissions
        if path.startswith(self.api_prefix):
            # Extract API scope from path
            parts = path.split("/")
            if len(parts) >= 3:
                scope = parts[2]  # e.g., /api/firewall/... -> firewall
                action = self.api_permissions.get(method, PermissionAction.VIEW)

                # Map to permission scope
                scope_map = {
                    "firewall": PermissionScope.FIREWALL,
                    "network": PermissionScope.NETWORK,
                    "monitoring": PermissionScope.MONITORING,
                    "plugins": PermissionScope.PLUGINS,
                    "logs": PermissionScope.LOGS,
                    "users": PermissionScope.USERS,
                    "settings": PermissionScope.SETTINGS,
                    "system": PermissionScope.SYSTEM,
                }

                if scope in scope_map:
                    perm_scope = scope_map[scope]
                    has_permission = self.rbac_manager.check_permission(
                        user.username, perm_scope.value, action.value
                    )
                    if not has_permission:
                        logger.warning(
                            f"API permission denied for {user.username}: {perm_scope.value}.{action.value} on {path}"
                        )
                        return False

        return True

    async def _log_access(self, request: Request, user: User):
        """Log user access for auditing."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user': user.username,
            'method': request.method,
            'path': request.url.path,
            'ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown')
        }

        # Log to file or database
        logger.info(f"Access log: {json.dumps(log_entry)}")

    def _add_security_headers(self, response: Response):
        """Add security headers to response."""
        headers = MutableHeaders(response.headers)

        # Security headers
        headers['X-Content-Type-Options'] = 'nosniff'
        headers['X-Frame-Options'] = 'DENY'
        headers['X-XSS-Protection'] = '1; mode=block'
        headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:;"
        )
        headers['Content-Security-Policy'] = csp


def login_required(f: Callable) -> Callable:
    """Decorator to require login for a route."""
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        if not hasattr(request.state, 'authenticated') or not request.state.authenticated:
            if request.url.path.startswith('/api'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            else:
                return RedirectResponse(url="/login", status_code=302)
        return await f(request, *args, **kwargs)
    return decorated_function


def require_permission(scope: PermissionScope, action: PermissionAction):
    """Decorator to require specific permission for a route."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        async def decorated_function(request: Request, *args, **kwargs):
            if not hasattr(request.state, 'user'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user = request.state.user
            rbac = get_rbac_manager()

            if not user.is_superuser:
                has_permission = rbac.check_permission(
                    user.username, scope.value, action.value
                )
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied: {scope.value}.{action.value}"
                    )

            return await f(request, *args, **kwargs)
        return decorated_function
    return decorator


def get_current_user(request: Request) -> Optional[User]:
    """Get the current authenticated user from request."""
    if hasattr(request.state, 'user'):
        return request.state.user
    return None


def get_session_data(request: Request) -> Optional[Dict[str, Any]]:
    """Get session data for the current request."""
    if hasattr(request.state, 'session'):
        return request.state.session
    return None
