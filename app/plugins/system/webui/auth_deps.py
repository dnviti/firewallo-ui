"""Authentication dependencies for WebUI plugin using main application auth system."""
from __future__ import annotations

import logging
from typing import Optional, Dict, Any
from functools import wraps

from fastapi import Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.models import User, verify_token, get_current_user, current_active_user
from app.core.startup import CoreUserRepository
from .rbac.models import get_rbac_manager, PermissionScope, PermissionAction

logger = logging.getLogger(__name__)

# Security scheme for API authentication
security = HTTPBearer(auto_error=False)


async def get_current_web_user(request: Request) -> Optional[User]:
    """Get current user for web interface using multiple auth methods."""
    try:
        # Method 1: Check Authorization header (Bearer token)
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
            except Exception:
                pass

        # Method 2: Check access_token cookie
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
            except Exception:
                pass

        # Method 3: Check web_session_id cookie (WebUI specific session)
        web_session_id = request.cookies.get("web_session_id")
        if web_session_id:
            # This would need to be implemented in the WebUI plugin
            # For now, we'll rely on the access_token method
            pass

        return None

    except Exception as e:
        logger.error(f"Authentication check failed: {e}")
        return None


async def require_web_auth(request: Request) -> User:
    """Require authentication for web routes, redirect to login if not authenticated."""
    user = await get_current_web_user(request)
    if not user:
        # For web routes, redirect to login page
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"}
        )
    return user


async def optional_web_auth(request: Request) -> Optional[User]:
    """Optional authentication for web routes."""
    return await get_current_web_user(request)


def require_web_permission(scope: PermissionScope, action: PermissionAction, resource: Optional[str] = None):
    """Decorator to require specific permission for web routes."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get authenticated user
            user = await require_web_auth(request)

            # Check permission using RBAC system
            rbac = get_rbac_manager()
            has_permission = rbac.check_permission(
                user.username, scope.value, action.value, resource
            )

            if not has_permission:
                # For web routes, you might want to show a 403 page or redirect
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {scope.value}.{action.value}"
                )

            # Add user to kwargs for the route handler
            kwargs['current_user'] = user
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_web_permission(user: User, scope: PermissionScope, action: PermissionAction, resource: Optional[str] = None) -> bool:
    """Check if user has specific permission."""
    rbac = get_rbac_manager()
    return rbac.check_permission(user.username, scope.value, action.value, resource)


async def get_api_user_with_rbac(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user for API routes with RBAC information."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Use main app auth system
        user_data = await get_current_user(credentials)
        user = User(user_data)

        # Sync user with RBAC system
        rbac = get_rbac_manager()
        rbac.sync_user_role(user.username)

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_api_permission(scope: PermissionScope, action: PermissionAction, resource: Optional[str] = None):
    """Decorator to require specific permission for API routes."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_api_user_with_rbac), **kwargs):
            # Check permission using RBAC system
            rbac = get_rbac_manager()
            has_permission = rbac.check_permission(
                current_user.username, scope.value, action.value, resource
            )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {scope.value}.{action.value}"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


class WebAuthMiddleware:
    """Middleware to handle web authentication for WebUI routes."""

    def __init__(self):
        self.public_paths = {
            "/login",
            "/static",
            "/favicon.ico",
            "/health"
        }

    def is_public_path(self, path: str) -> bool:
        """Check if path is public (no authentication required)."""
        # Exact matches
        if path in self.public_paths:
            return True

        # Prefix matches for static assets
        for public_path in ["/static/", "/api/"]:
            if path.startswith(public_path):
                return True

        return False

    async def authenticate_request(self, request: Request) -> Optional[User]:
        """Authenticate request and return user if valid."""
        if self.is_public_path(request.url.path):
            return None  # Public path, no auth needed

        return await get_current_web_user(request)


# Utility functions for templates and views
def get_user_context(user: Optional[User]) -> Dict[str, Any]:
    """Get user context for templates."""
    if not user:
        return {
            "user": None,
            "is_authenticated": False,
            "roles": [],
            "permissions": []
        }

    rbac = get_rbac_manager()
    roles = rbac.get_user_roles(user.username)
    permissions = rbac.get_user_permissions(user.username)

    return {
        "user": {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active
        },
        "is_authenticated": True,
        "roles": [r.to_dict() for r in roles],
        "permissions": [p.to_dict() for p in permissions]
    }


def can_access_section(user: User, section: str) -> bool:
    """Check if user can access a specific UI section."""
    section_permissions = {
        "dashboard": (PermissionScope.DASHBOARD, PermissionAction.VIEW),
        "firewall": (PermissionScope.FIREWALL, PermissionAction.VIEW),
        "network": (PermissionScope.NETWORK, PermissionAction.VIEW),
        "monitoring": (PermissionScope.MONITORING, PermissionAction.VIEW),
        "plugins": (PermissionScope.PLUGINS, PermissionAction.VIEW),
        "logs": (PermissionScope.LOGS, PermissionAction.VIEW),
        "settings": (PermissionScope.SETTINGS, PermissionAction.VIEW),
        "users": (PermissionScope.USERS, PermissionAction.VIEW),
        "system": (PermissionScope.SYSTEM, PermissionAction.VIEW)
    }

    if section not in section_permissions:
        return False

    scope, action = section_permissions[section]
    return check_web_permission(user, scope, action)


async def get_navigation_context(user: User) -> Dict[str, Any]:
    """Get navigation context based on user permissions."""
    sections = [
        {"id": "dashboard", "name": "Dashboard", "icon": "speedometer2", "url": "/dashboard"},
        {"id": "firewall", "name": "Firewall", "icon": "shield-lock", "url": "/firewall"},
        {"id": "network", "name": "Network", "icon": "diagram-3", "url": "/network"},
        {"id": "monitoring", "name": "Monitoring", "icon": "graph-up", "url": "/monitoring"},
        {"id": "plugins", "name": "Plugins", "icon": "puzzle", "url": "/plugins"},
        {"id": "logs", "name": "Logs", "icon": "file-text", "url": "/logs"},
        {"id": "settings", "name": "Settings", "icon": "gear", "url": "/settings"},
        {"id": "users", "name": "Users", "icon": "people", "url": "/users"},
        {"id": "system", "name": "System", "icon": "cpu", "url": "/system"}
    ]

    # Filter sections based on user permissions
    accessible_sections = [
        section for section in sections
        if can_access_section(user, section["id"])
    ]

    # Get plugin menu entries
    plugin_menus = []
    try:
        from .services import MenuService
        import logging
        logger = logging.getLogger(__name__)

        # Initialize MenuService if needed
        if not getattr(MenuService, '_initialized', False):
            await MenuService.initialize()
            logger.info("MenuService initialized for navigation context")

        # Get user permissions for filtering
        user_permissions = []

        # If user is superuser, pass None to get all menu entries
        if getattr(user, 'is_superuser', False):
            user_permissions = None
            logger.info("Super user detected - showing all plugin menus")
        else:
            # Get specific permissions for regular users
            if hasattr(user, 'permissions'):
                user_permissions = user.permissions
            elif hasattr(user, 'username'):
                # Get permissions from RBAC if available
                try:
                    rbac = get_rbac_manager()
                    user_permissions = rbac.get_user_permissions(user.username)
                except Exception as rbac_error:
                    logger.debug(f"Could not get RBAC permissions: {rbac_error}")
                    user_permissions = []

            # If no permissions found, try some common admin permissions
            if not user_permissions and getattr(user, 'role', '') == 'admin':
                user_permissions = ['vpn.*', 'firewall.*', 'monitoring.*', 'network.*', 'admin.*']
                logger.info("Admin role detected - using default admin permissions")

        # Get plugin menu entries
        plugin_entries = await MenuService.get_menu_entries(user_permissions)
        logger.info(f"Retrieved {len(plugin_entries)} plugin menu entries")

        # Convert plugin entries to navigation format
        for entry in plugin_entries:
            plugin_menu = {
                "id": entry.get("id", ""),
                "name": entry.get("title", ""),
                "icon": entry.get("icon", "puzzle").replace("bi-", ""),
                "url": entry.get("url", ""),
                "category": entry.get("category", ""),
                "badge": entry.get("badge")
            }
            plugin_menus.append(plugin_menu)
            logger.debug(f"Added plugin menu: {plugin_menu['name']} -> {plugin_menu['url']}")

    except ImportError as e:
        # MenuService not available - WebUI plugin may not be loaded
        import logging
        logging.debug(f"MenuService not available: {e}")
    except Exception as e:
        # Log other errors but don't break navigation
        import logging
        logging.error(f"Error retrieving plugin menus: {e}")

    return {
        "navigation": accessible_sections,
        "plugin_menus": plugin_menus,
        "user_menu": [
            {"name": "Profile", "url": "/profile", "icon": "person"},
            {"name": "Settings", "url": "/settings", "icon": "gear"} if can_access_section(user, "settings") else None,
            {"name": "Logout", "url": "/logout", "icon": "box-arrow-right"}
        ]
    }


# Dependency aliases for convenience
WebUser = Depends(require_web_auth)
OptionalWebUser = Depends(optional_web_auth)
APIUser = Depends(get_api_user_with_rbac)
