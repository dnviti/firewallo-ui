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
from app.auth.models import current_active_user
from app.api.routes import system as system_routes


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
            return RedirectResponse(url="/dashboard", status_code=302)

        @self.web_router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
        async def dashboard(request: Request):
            """Serve the dashboard page."""
            self._track_request("dashboard")
            context = await self._get_template_context(request, "Dashboard")
            return self.templates.TemplateResponse("dashboard.html", context)

        @self.web_router.get("/plugins", response_class=HTMLResponse, include_in_schema=False)
        async def plugins(request: Request):
            """Serve the plugins management page."""
            self._track_request("plugins")
            context = await self._get_template_context(request, "Plugin Management")
            return self.templates.TemplateResponse("plugins.html", context)

        @self.web_router.get("/login", response_class=HTMLResponse, include_in_schema=False)
        async def login(request: Request):
            """Serve the login page."""
            self._track_request("login")
            return self.templates.TemplateResponse("login.html", {"request": request})

        @self.web_router.get("/firewall", response_class=HTMLResponse, include_in_schema=False)
        async def firewall(request: Request):
            """Serve the firewall management page."""
            self._track_request("firewall")
            context = await self._get_template_context(request, "Firewall Management")
            # Use dashboard template as placeholder if firewall.html doesn't exist
            template = "firewall.html" if (self.templates_dir / "firewall.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/monitoring", response_class=HTMLResponse, include_in_schema=False)
        async def monitoring(request: Request):
            """Serve the monitoring page."""
            self._track_request("monitoring")
            context = await self._get_template_context(request, "System Monitoring")
            template = "monitoring.html" if (self.templates_dir / "monitoring.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
        async def logs(request: Request):
            """Serve the logs viewer page."""
            self._track_request("logs")
            context = await self._get_template_context(request, "System Logs")
            template = "logs.html" if (self.templates_dir / "logs.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
        async def settings(request: Request):
            """Serve the settings page."""
            self._track_request("settings")
            context = await self._get_template_context(request, "Settings")
            template = "settings.html" if (self.templates_dir / "settings.html").exists() else "dashboard.html"
            return self.templates.TemplateResponse(template, context)

        @self.web_router.get("/logout", response_class=HTMLResponse, include_in_schema=False)
        async def logout(request: Request):
            """Handle logout."""
            self._track_request("logout")
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("access_token")
            return response

    def _setup_api_routes(self):
        """Setup API routes for WebUI management."""

        @self.api_router.get("/status")
        async def get_status():
            """Get WebUI plugin status."""
            return {
                "status": "running" if self._initialized else "stopped",
                "version": self.version,
                "uptime": (datetime.utcnow() - self.start_time).total_seconds(),
                "config": self.config,
                "metrics": {
                    "active_sessions": len(self.sessions),
                    "total_requests": self.request_count
                }
            }

        @self.api_router.get("/config")
        async def get_config():
            """Get WebUI configuration."""
            return WebUIConfig(**self.config)

        @self.api_router.post("/config")
        async def update_config(config: WebUIConfig):
            """Update WebUI configuration."""
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

    async def _get_template_context(self, request: Request, page_title: str = "") -> Dict[str, Any]:
        """Get common template context."""
        return {
            "request": request,
            "page_title": page_title,
            "user": {"username": "admin", "email": "admin@firewallo.local"},
            "config": self.config,
            "version": self.version,
            "theme": self.config.get("theme", "default"),
            "dark_mode": self.config.get("enable_dark_mode", False),
            "notifications": self.config.get("enable_notifications", True)
        }

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

                now = datetime.utcnow()
                expired = []

                for session_id, session_data in self.sessions.items():
                    if session_data.get("expires_at", now) < now:
                        expired.append(session_id)

                for session_id in expired:
                    del self.sessions[session_id]

                if expired:
                    self.logger.info(f"Cleaned up {len(expired)} expired sessions")

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
