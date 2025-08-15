"""Firewallo Web UI Plugin - Modern Bootstrap-based web interface."""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.plugins.base import BasePlugin, BaseRepository, PluginError
from app.auth.models import current_active_user, verify_token, get_current_user, User
from app.api.routes import system as system_routes
from .auth_deps import (
    require_web_auth, get_current_web_user, get_user_context,
    get_navigation_context, require_api_permission, get_api_user_with_rbac
)
from .rbac.models import get_rbac_manager, PermissionScope, PermissionAction


# WebUI specific models
class WebUIConfig(BaseModel):
    """WebUI configuration model."""
    enabled: bool = True
    port: int = 8080
    host: str = "0.0.0.0"
    theme: str = "default"
    auto_refresh_interval: int = 60
    session_timeout: int = 3600
    max_sessions: int = 100
    enable_notifications: bool = True
    enable_sound_alerts: bool = False
    enable_dark_mode: bool = False
    enable_api_docs: bool = True
    dashboard_widgets: List[str] = Field(default_factory=lambda: [
        "system_status", "cpu_usage", "memory_usage", "disk_usage",
        "network_traffic", "active_plugins", "recent_activity", "quick_actions"
    ])
    default_language: str = "en"
    timezone: str = "UTC"
    date_format: str = "YYYY-MM-DD HH:mm:ss"
    enable_metrics: bool = True
    enable_activity_log: bool = True
    max_log_entries: int = 1000


class WidgetConfig(BaseModel):
    """Dashboard widget configuration."""
    id: str
    enabled: bool = True
    position: int = 0
    size: str = "medium"  # small, medium, large
    refresh_interval: int = 30
    settings: Dict[str, Any] = Field(default_factory=dict)


class ThemeConfig(BaseModel):
    """Theme configuration."""
    name: str
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    dark_mode: bool = False
    custom_css: Optional[str] = None


class WebUIMetrics(BaseModel):
    """WebUI usage metrics."""
    active_sessions: int = 0
    total_requests: int = 0
    page_views: Dict[str, int] = Field(default_factory=dict)
    widget_usage: Dict[str, int] = Field(default_factory=dict)
    last_access: Optional[datetime] = None
    uptime_seconds: float = 0


class WebUIRepository(BaseRepository):
    """Repository for WebUI plugin data management."""

    def __init__(self):
        super().__init__(plugin_name="webui", category="system")
        self.sessions = {}
        self.metrics = WebUIMetrics()

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user-specific preferences."""
        doc = await self.get_item(f"user_prefs_{user_id}")
        return doc if doc else {
            "theme": "default",
            "language": "en",
            "dashboard_layout": [],
            "notifications": True
        }

    async def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Save user-specific preferences."""
        return await self.update_item(f"user_prefs_{user_id}", preferences)

    async def get_widget_config(self, user_id: str) -> List[WidgetConfig]:
        """Get user's widget configuration."""
        doc = await self.get_item(f"widgets_{user_id}")
        if doc:
            return [WidgetConfig(**w) for w in doc.get("widgets", [])]
        return []

    async def save_widget_config(self, user_id: str, widgets: List[WidgetConfig]) -> bool:
        """Save user's widget configuration."""
        data = {"widgets": [w.dict() for w in widgets]}
        return await self.update_item(f"widgets_{user_id}", data)

    async def log_activity(self, activity: Dict[str, Any]) -> bool:
        """Log WebUI activity."""
        activity["timestamp"] = datetime.utcnow()
        return await self.create_item(activity)

    async def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent WebUI activity."""
        activities = await self.find_items({})
        # Sort by timestamp and limit
        activities.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        return activities[:limit]

    async def update_metrics(self, metrics: WebUIMetrics) -> bool:
        """Update WebUI metrics."""
        return await self.set_data("metrics", metrics.dict())

    async def get_metrics(self) -> WebUIMetrics:
        """Get WebUI metrics."""
        doc = await self.get_data("metrics")
        return WebUIMetrics(**doc) if doc else WebUIMetrics()


class WebUIPlugin(BasePlugin):
    """Firewallo Web UI Plugin implementation."""

    def __init__(self):
        """Initialize WebUI plugin."""
        super().__init__()
        self.name = "webui"
        self.category = "system"
        self.version = "2.0.0"
        self.description = "Modern Bootstrap-based web interface for Firewallo"
        self.author = "Firewallo Team"
        self.license = "MIT"

        # Plugin paths
        self.plugin_dir = Path(__file__).parent
        self.templates_dir = self.plugin_dir / "templates"
        self.static_dir = self.plugin_dir / "static"

        # Session storage for web interface
        self.active_sessions = {}

        # Fallback to app-level templates/static if plugin dirs don't exist
        if not self.templates_dir.exists():
            self.templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
        if not self.static_dir.exists():
            self.static_dir = Path(__file__).parent.parent.parent.parent / "static"

        # Initialize components
        self.repository = WebUIRepository()
        self.templates = Jinja2Templates(directory=str(self.templates_dir))

        # Create routers
        self.web_router = APIRouter(tags=["webui"])
        self.api_router = APIRouter(prefix="/webui", tags=["webui-api"])

        # Session management
        self.sessions = {}
        self.session_cleanup_task = None

        # Metrics
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.metrics = WebUIMetrics()  # Initialize metrics

        # Setup routes
        self._setup_web_routes()
        self._setup_api_routes()

    async def initialize(self) -> bool:
        """Initialize the WebUI plugin."""
        try:
            self.logger.info("Initializing WebUI plugin...")

            # Load manifest
            manifest_path = self.plugin_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    self.set_manifest(json.load(f))

            # Load configuration
            config = await self.repository.get_data("config")
            if not config:
                # Use default configuration from manifest
                default_config = self.manifest.get("configuration", {}).get("defaults", {})
                await self.repository.set_data("config", default_config)
                self.config = default_config
            else:
                self.config = config

            # Initialize metrics
            self.metrics = await self.repository.get_metrics()
            self.metrics.uptime_seconds = 0
            self.metrics.last_access = datetime.utcnow()

            # Start session cleanup task
            self.session_cleanup_task = asyncio.create_task(self._cleanup_sessions())

            # Mark as initialized
            self.mark_initialized()
            self.logger.info("WebUI plugin initialized successfully")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize WebUI plugin: {str(e)}", e)
            return False

    async def shutdown(self) -> None:
        """Shutdown the WebUI plugin."""
        try:
            self.logger.info("Shutting down WebUI plugin...")

            # Cancel session cleanup task
            if self.session_cleanup_task:
                self.session_cleanup_task.cancel()
                try:
                    await self.session_cleanup_task
                except asyncio.CancelledError:
                    pass

            # Save metrics
            self.metrics.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            await self.repository.update_metrics(self.metrics)

            # Clear sessions
            self.sessions.clear()

            # Mark as shut down
            self.mark_shutdown()
            self.logger.info("WebUI plugin shut down successfully")

        except Exception as e:
            self.log_error(f"Error during WebUI shutdown: {str(e)}", e)

    def get_api_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this plugin."""
        return [self.web_router, self.api_router]

    def get_database_schema(self) -> Dict[str, Any]:
        """Return the database schema for this plugin."""
        return {
            "collections": {
                "webui": {
                    "indexes": [
                        {"keys": [("user_id", 1)]},
                        {"keys": [("timestamp", -1)]},
                        {"keys": [("type", 1)]}
                    ]
                },
                "webui_sessions": {
                    "indexes": [
                        {"keys": [("session_id", 1)], "unique": True},
                        {"keys": [("user_id", 1)]},
                        {"keys": [("expires_at", 1)]}
                    ]
                },
                "webui_preferences": {
                    "indexes": [
                        {"keys": [("user_id", 1)], "unique": True}
                    ]
                }
            }
        }

    def _setup_web_routes(self):
        """Setup web interface routes."""

        @self.web_router.get("/", response_class=HTMLResponse, include_in_schema=False)
        async def root(request: Request):
            """Redirect root to dashboard."""
            # Check authentication using integrated auth system
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)
            return RedirectResponse(url="/dashboard", status_code=302)

        @self.web_router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard(request: Request):
            """Serve the dashboard page."""
            # Use integrated authentication
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            # Check dashboard permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(user.username, PermissionScope.DASHBOARD.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            self._track_request("dashboard")
            self._log_access(request, user)
            context = await self._get_template_context(request, "Dashboard", user)
            return self.templates.TemplateResponse("dashboard.html", context)

        @self.web_router.get("/plugins", response_class=HTMLResponse, include_in_schema=False)
        async def plugins(request: Request):
            """Serve the plugins management page."""
            # Use integrated authentication
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            # Check plugins permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(user.username, PermissionScope.PLUGINS.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            self._track_request("plugins")
            self._log_access(request, user)
            context = await self._get_template_context(request, "Plugin Management", user)
            return self.templates.TemplateResponse("plugins.html", context)

        @self.web_router.get("/login", response_class=HTMLResponse, include_in_schema=False)
        async def login(request: Request):
            """Serve the login page."""
            # Check if user is already authenticated using integrated auth
            user = await get_current_web_user(request)
            if user:
                # User is already logged in, redirect to dashboard
                return RedirectResponse(url="/dashboard", status_code=302)

            self._track_request("login")
            return self.templates.TemplateResponse("login.html", {"request": request})

        @self.web_router.get("/firewall", response_class=HTMLResponse, include_in_schema=False)
        async def firewall(request: Request):
            """Serve the firewall management page."""
            # Use integrated authentication
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            # Check firewall permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(user.username, PermissionScope.FIREWALL.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            self._track_request("firewall")
            self._log_access(request, user)
            context = await self._get_template_context(request, "Firewall Management", user)
            # Use dashboard template as placeholder if firewall.html doesn't exist
            template = "firewall.html" if (self.templates_dir / "firewall.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/monitoring", response_class=HTMLResponse, include_in_schema=False)
        async def monitoring(request: Request):
            """Serve the monitoring page."""
            # Use integrated authentication
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            # Check monitoring permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(user.username, PermissionScope.MONITORING.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            self._track_request("monitoring")
            self._log_access(request, user)
            context = await self._get_template_context(request, "System Monitoring", user)
            template = "monitoring.html" if (self.templates_dir / "monitoring.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
        async def logs(request: Request):
            """Serve the logs viewer page."""
            # Use integrated authentication
            user = await get_current_web_user(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            # Check logs permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(user.username, PermissionScope.LOGS.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            self._track_request("logs")
            self._log_access(request, user)
            context = await self._get_template_context(request, "System Logs", user)
            template = "logs.html" if (self.templates_dir / "logs.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
        async def settings(request: Request):
            """Serve the settings page."""
            # Check authentication
            user = await self._check_web_authentication(request)
            if not user:
                return RedirectResponse(url="/login", status_code=302)

            self._track_request("settings")
            self._log_access(request, user)
            context = await self._get_template_context(request, "Settings", user)
            template = "settings.html" if (self.templates_dir / "settings.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/logout", response_class=HTMLResponse, include_in_schema=False)
        async def logout(request: Request):
            """Handle logout."""
            self._track_request("logout")
            # Clear web session if exists
            session_id = request.cookies.get("web_session_id")
            if session_id and session_id in self.active_sessions:
                del self.active_sessions[session_id]

            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("access_token")
            response.delete_cookie("web_session_id")
            return response

    def _setup_api_routes(self):
        """Setup API routes for WebUI management."""

        @self.api_router.post("/auth/login")
        async def login(request: Request, response: Response):
            """Handle user login and create web session."""
            try:
                # Get form data
                form = await request.form()
                username = form.get("username")
                password = form.get("password")
                remember_me = form.get("remember_me") == "on"

                if not username or not password:
                    raise HTTPException(status_code=400, detail="Username and password required")

                # Use main application auth system
                from app.core.startup import CoreUserRepository
                from app.auth.models import verify_password, create_access_token

                user_repo = CoreUserRepository()
                user_data = user_repo.get_user_by_username(username)

                if not user_data or not verify_password(password, user_data.get("hashed_password", "")):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                if not user_data.get("is_active", False):
                    raise HTTPException(status_code=401, detail="Account is disabled")

                # Create web session for UI navigation
                import secrets
                session_id = secrets.token_urlsafe(32)
                expires_at = datetime.utcnow() + timedelta(days=30 if remember_me else 1)

                self.active_sessions[session_id] = {
                    "user_data": user_data,
                    "created_at": datetime.utcnow(),
                    "expires_at": expires_at,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("User-Agent")
                }

                # Create standard access token for API access
                token_data = {"sub": user_data["username"]}
                expires_delta = timedelta(days=30 if remember_me else 1)
                access_token = create_access_token(token_data, expires_delta)

                # Set cookies
                max_age = int(expires_delta.total_seconds())
                response.set_cookie(
                    key="web_session_id",
                    value=session_id,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=max_age
                )
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=max_age
                )

                return {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "username": user_data["username"],
                        "email": user_data.get("email", ""),
                        "role": user_data.get("role", "user")
                    }
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Login error: {e}")
                raise HTTPException(status_code=500, detail="Login failed")

        @self.api_router.get("/status")
        async def get_status(current_user: User = Depends(get_api_user_with_rbac)):
            """Get WebUI plugin status."""
            # Check system view permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(current_user.username, PermissionScope.SYSTEM.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            return {
                "status": "running" if self._initialized else "stopped",
                "version": self.version,
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "config": self.config,
                "metrics": {
                    "active_sessions": len(self.active_sessions),
                    "total_requests": self.request_count
                }
            }

        @self.api_router.get("/config")
        async def get_config(current_user: User = Depends(get_api_user_with_rbac)):
            """Get WebUI configuration."""
            # Check settings view permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(current_user.username, PermissionScope.SETTINGS.value, PermissionAction.VIEW.value):
                raise HTTPException(status_code=403, detail="Access denied")

            return WebUIConfig(**self.config)

        @self.api_router.post("/config")
        async def update_config(config: WebUIConfig, current_user: User = Depends(get_api_user_with_rbac)):
            """Update WebUI configuration."""
            # Check settings update permission
            rbac = get_rbac_manager()
            if not rbac.check_permission(current_user.username, PermissionScope.SETTINGS.value, PermissionAction.UPDATE.value):
                raise HTTPException(status_code=403, detail="Access denied")

            try:
                self.config = config.dict()
                await self.repository.set_data("config", self.config)
                return {"status": "success", "message": "Configuration updated"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.api_router.get("/metrics")
        async def get_metrics():
            """Get WebUI metrics."""
            metrics = await self.repository.get_metrics()
            metrics.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            metrics.active_sessions = len(self.sessions)
            metrics.total_requests = self.request_count
            return metrics

        @self.api_router.get("/widgets")
        async def get_widgets(user_id: str = "default"):
            """Get widget configuration."""
            widgets = await self.repository.get_widget_config(user_id)
            if not widgets:
                # Return default widgets
                return self._get_default_widgets()
            return widgets

        @self.api_router.post("/widgets")
        async def save_widgets(widgets: List[WidgetConfig], user_id: str = "default"):
            """Save widget configuration."""
            try:
                await self.repository.save_widget_config(user_id, widgets)
                return {"status": "success", "message": "Widgets saved"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.api_router.get("/preferences/{user_id}")
        async def get_preferences(user_id: str):
            """Get user preferences."""
            return await self.repository.get_user_preferences(user_id)

        @self.api_router.post("/preferences/{user_id}")
        async def save_preferences(user_id: str, preferences: Dict[str, Any]):
            """Save user preferences."""
            try:
                await self.repository.save_user_preferences(user_id, preferences)
                return {"status": "success", "message": "Preferences saved"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.api_router.get("/activity")
        async def get_activity(limit: int = 50):
            """Get recent WebUI activity."""
            return await self.repository.get_recent_activity(limit)

        @self.api_router.post("/theme")
        async def set_theme(theme: ThemeConfig):
            """Set WebUI theme."""
            try:
                self.config["theme"] = theme.name
                self.config["enable_dark_mode"] = theme.dark_mode
                await self.repository.set_data("config", self.config)
                return {"status": "success", "message": f"Theme set to {theme.name}"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    async def _get_template_context(self, request: Request, page_title: str = "", user=None) -> Dict[str, Any]:
        """Get enhanced template context with RBAC integration."""
        # Get user context with permissions and roles
        user_context = get_user_context(user)

        # Get navigation context based on permissions
        navigation_context = {}
        if user:
            navigation_context = await get_navigation_context(user)

        base_context = {
            "request": request,
            "page_title": page_title,
            "config": self.config,
            "version": self.version,
            "theme": self.config.get("theme", "default"),
            "dark_mode": self.config.get("theme", "default") == "dark", # Use configured theme to determine dark mode
            "notifications": self.config.get("enable_notifications", True)
        }

        # Merge all contexts
        base_context.update(user_context)
        base_context.update(navigation_context)

        return base_context

    async def _check_web_authentication(self, request: Request) -> User:
        """Check web authentication using main app auth system with web session fallback."""
        try:
            # First try standard Bearer token authentication
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = verify_token(token)
                    username = payload.get("sub")
                    if username:
                        from app.core.startup import CoreUserRepository
                        user_repo = CoreUserRepository()
                        user_data = user_repo.get_user_by_username(username)
                        if user_data and user_data.get("is_active", False):
                            return User(user_data)
                except Exception:
                    pass

            # Try access token cookie
            access_token = request.cookies.get("access_token")
            if access_token:
                try:
                    payload = verify_token(access_token)
                    username = payload.get("sub")
                    if username:
                        from app.core.startup import CoreUserRepository
                        user_repo = CoreUserRepository()
                        user_data = user_repo.get_user_by_username(username)
                        if user_data and user_data.get("is_active", False):
                            return User(user_data)
                except Exception:
                    pass

            # Fall back to web session for UI navigation
            session_id = request.cookies.get("web_session_id")
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if session["expires_at"] > datetime.utcnow():
                    return User(session["user_data"])
                else:
                    # Clean up expired session
                    del self.active_sessions[session_id]

            return None

        except Exception as e:
            self.logger.error(f"Authentication check failed: {e}")
            return None

    def _log_access(self, request: Request, user: User):
        """Log user access for auditing."""
        try:
            self.logger.info(f"Access: {user.username} {request.method} {request.url.path}")
        except Exception as e:
            self.logger.error(f"Failed to log access: {e}")

    async def _check_authentication(self, request: Request):
        """Check if user is authenticated - DEPRECATED: Use _check_web_authentication."""
        return await self._check_web_authentication(request)

    def _track_request(self, page: str):
        """Track page request for metrics."""
        self.request_count += 1
        if not hasattr(self.metrics, 'page_views'):
            self.metrics.page_views = {}
        self.metrics.page_views[page] = self.metrics.page_views.get(page, 0) + 1
        self.metrics.last_access = datetime.utcnow()

    def _get_default_widgets(self) -> List[WidgetConfig]:
        """Get default widget configuration."""
        default_widgets = [
            WidgetConfig(id="system_status", position=0, size="small"),
            WidgetConfig(id="cpu_usage", position=1, size="small"),
            WidgetConfig(id="memory_usage", position=2, size="small"),
            WidgetConfig(id="disk_usage", position=3, size="small"),
            WidgetConfig(id="network_traffic", position=4, size="medium"),
            WidgetConfig(id="active_plugins", position=5, size="medium"),
            WidgetConfig(id="recent_activity", position=6, size="large"),
            WidgetConfig(id="quick_actions", position=7, size="small")
        ]
        return default_widgets

    async def _cleanup_sessions(self):
        """Periodic task to cleanup expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Clean up expired web sessions
                now = datetime.utcnow()
                expired_sessions = [
                    sid for sid, session in self.active_sessions.items()
                    if session["expires_at"] < now
                ]

                for session_id in expired_sessions:
                    del self.active_sessions[session_id]

                if expired_sessions:
                    self.logger.info(f"Cleaned up {len(expired_sessions)} expired web sessions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {str(e)}")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate WebUI configuration."""
        try:
            # Validate using Pydantic model
            WebUIConfig(**config)

            # Additional validation
            port = config.get("port", 8080)
            if isinstance(port, int) and (port < 1 or port > 65535):
                raise ValueError("Port must be between 1 and 65535")

            if config.get("session_timeout", 3600) < 60:
                raise ValueError("Session timeout must be at least 60 seconds")

            if config.get("max_sessions", 100) < 1:
                raise ValueError("Max sessions must be at least 1")

            return True

        except Exception as e:
            self.log_error(f"Configuration validation failed: {str(e)}", e)
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Return WebUI health information."""
        health = super().get_health_status()

        # Add WebUI-specific health information
        health.update({
            "active_sessions": len(self.sessions),
            "total_requests": self.request_count,
            "templates_available": self.templates_dir.exists(),
            "static_files_available": self.static_dir.exists(),
            "last_access": self.metrics.last_access.isoformat() if self.metrics.last_access else None,
            "config_valid": self.validate_config(self.config)
        })

        return health

    def get_metrics(self) -> Dict[str, Any]:
        """Return WebUI metrics."""
        metrics = super().get_metrics()

        # Add WebUI-specific metrics
        metrics.update({
            "active_sessions": len(self.sessions),
            "total_requests": self.request_count,
            "page_views": dict(self.metrics.page_views) if hasattr(self.metrics, 'page_views') else {},
            "average_session_duration": 0,  # To be implemented
            "peak_concurrent_users": len(self.sessions),  # To be tracked properly
            "browser_stats": {},  # To be implemented
            "response_times": {}  # To be implemented
        })

        return metrics


# Create plugin instance
plugin = WebUIPlugin()


# Export plugin class and instance
__all__ = ["WebUIPlugin", "plugin"]
