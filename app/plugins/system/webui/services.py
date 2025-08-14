"""WebUI Plugin Services - Handles complex operations for the web interface."""

import os
import json
import hashlib
import asyncio
import mimetypes
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import zipfile
import tempfile
import shutil
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from jinja2 import Environment, FileSystemLoader, select_autoescape
import psutil
from pydantic import BaseModel, Field

import logging

logger = logging.getLogger("firewallo.plugins.system.webui.services")


class TemplateService:
    """Service for managing and rendering templates."""

    def __init__(self, templates_dir: Path):
        """Initialize template service.

        Args:
            templates_dir: Path to templates directory
        """
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            enable_async=True
        )
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a template with context.

        Args:
            template_name: Name of the template file
            context: Template context dictionary

        Returns:
            Rendered HTML string
        """
        try:
            template = self.env.get_template(template_name)
            return await template.render_async(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            raise

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of template filenames
        """
        templates = []
        for file in self.templates_dir.glob("*.html"):
            templates.append(file.name)
        return sorted(templates)

    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and is valid.

        Args:
            template_name: Name of the template to validate

        Returns:
            True if template is valid, False otherwise
        """
        try:
            self.env.get_template(template_name)
            return True
        except Exception:
            return False


class StaticFileService:
    """Service for managing static files."""

    def __init__(self, static_dir: Path):
        """Initialize static file service.

        Args:
            static_dir: Path to static files directory
        """
        self.static_dir = static_dir
        self.cache = {}
        self.etag_cache = {}

    async def serve_file(self, file_path: str) -> FileResponse:
        """Serve a static file.

        Args:
            file_path: Relative path to the file

        Returns:
            FileResponse for the requested file
        """
        full_path = self.static_dir / file_path

        if not full_path.exists() or not full_path.is_file():
            raise FileNotFoundError(f"Static file not found: {file_path}")

        # Security check - ensure file is within static directory
        if not str(full_path.resolve()).startswith(str(self.static_dir.resolve())):
            raise PermissionError(f"Access denied to file: {file_path}")

        # Get mime type
        mime_type, _ = mimetypes.guess_type(str(full_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        # Generate ETag
        etag = await self._generate_etag(full_path)

        return FileResponse(
            str(full_path),
            media_type=mime_type,
            headers={"ETag": etag, "Cache-Control": "public, max-age=3600"}
        )

    async def _generate_etag(self, file_path: Path) -> str:
        """Generate ETag for a file.

        Args:
            file_path: Path to the file

        Returns:
            ETag string
        """
        stat = file_path.stat()
        etag_source = f"{file_path.name}-{stat.st_size}-{stat.st_mtime}"
        return hashlib.md5(etag_source.encode()).hexdigest()

    def list_static_files(self) -> Dict[str, List[str]]:
        """List all static files organized by type.

        Returns:
            Dictionary with file types as keys and file lists as values
        """
        files = defaultdict(list)

        for file_path in self.static_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(self.static_dir)
                file_type = file_path.suffix.lstrip(".") or "other"
                files[file_type].append(str(rel_path))

        return dict(files)


class SessionManager:
    """Service for managing user sessions."""

    def __init__(self, max_sessions: int = 100, timeout: int = 3600):
        """Initialize session manager.

        Args:
            max_sessions: Maximum number of concurrent sessions
            timeout: Session timeout in seconds
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = max_sessions
        self.timeout = timeout
        self.cleanup_interval = 300  # 5 minutes

    async def create_session(self, user_id: str, data: Dict[str, Any] = None) -> str:
        """Create a new session.

        Args:
            user_id: User identifier
            data: Additional session data

        Returns:
            Session ID
        """
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            await self._cleanup_expired_sessions()
            if len(self.sessions) >= self.max_sessions:
                raise RuntimeError("Maximum number of sessions reached")

        # Generate session ID
        session_id = hashlib.sha256(
            f"{user_id}-{datetime.utcnow().isoformat()}-{os.urandom(16).hex()}".encode()
        ).hexdigest()

        # Create session
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=self.timeout),
            "data": data or {}
        }

        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found/expired
        """
        session = self.sessions.get(session_id)

        if not session:
            return None

        # Check expiration
        if session["expires_at"] < datetime.utcnow():
            del self.sessions[session_id]
            return None

        # Update last accessed time
        session["last_accessed"] = datetime.utcnow()
        session["expires_at"] = datetime.utcnow() + timedelta(seconds=self.timeout)

        return session

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was destroyed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self.sessions.items()
            if session["expires_at"] < now
        ]

        for sid in expired:
            del self.sessions[sid]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    def get_active_sessions(self) -> int:
        """Get number of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.sessions)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary with session statistics
        """
        if not self.sessions:
            return {
                "active": 0,
                "average_duration": 0,
                "max_duration": 0,
                "users": []
            }

        now = datetime.utcnow()
        durations = []
        users = set()

        for session in self.sessions.values():
            duration = (now - session["created_at"]).total_seconds()
            durations.append(duration)
            users.add(session["user_id"])

        return {
            "active": len(self.sessions),
            "average_duration": sum(durations) / len(durations),
            "max_duration": max(durations),
            "users": list(users)
        }


class WidgetManager:
    """Service for managing dashboard widgets."""

    def __init__(self):
        """Initialize widget manager."""
        self.widgets = {}
        self.user_layouts = {}

    async def register_widget(self, widget: Dict[str, Any]) -> bool:
        """Register a new widget.

        Args:
            widget: Widget configuration

        Returns:
            True if registered successfully
        """
        widget_id = widget.get("id")
        if not widget_id:
            raise ValueError("Widget must have an ID")

        self.widgets[widget_id] = {
            **widget,
            "registered_at": datetime.utcnow()
        }

        logger.info(f"Registered widget: {widget_id}")
        return True

    async def get_widget(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get widget configuration.

        Args:
            widget_id: Widget identifier

        Returns:
            Widget configuration or None
        """
        return self.widgets.get(widget_id)

    async def get_user_layout(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's widget layout.

        Args:
            user_id: User identifier

        Returns:
            List of widget configurations in user's layout
        """
        layout = self.user_layouts.get(user_id, [])

        if not layout:
            # Return default layout
            return self._get_default_layout()

        return layout

    async def save_user_layout(self, user_id: str, layout: List[Dict[str, Any]]) -> bool:
        """Save user's widget layout.

        Args:
            user_id: User identifier
            layout: Widget layout configuration

        Returns:
            True if saved successfully
        """
        self.user_layouts[user_id] = layout
        logger.info(f"Saved widget layout for user: {user_id}")
        return True

    def _get_default_layout(self) -> List[Dict[str, Any]]:
        """Get default widget layout.

        Returns:
            Default widget layout configuration
        """
        return [
            {"id": "system_status", "position": {"x": 0, "y": 0}, "size": {"w": 3, "h": 2}},
            {"id": "cpu_usage", "position": {"x": 3, "y": 0}, "size": {"w": 3, "h": 2}},
            {"id": "memory_usage", "position": {"x": 6, "y": 0}, "size": {"w": 3, "h": 2}},
            {"id": "disk_usage", "position": {"x": 9, "y": 0}, "size": {"w": 3, "h": 2}},
            {"id": "network_traffic", "position": {"x": 0, "y": 2}, "size": {"w": 6, "h": 3}},
            {"id": "active_plugins", "position": {"x": 6, "y": 2}, "size": {"w": 6, "h": 3}},
            {"id": "recent_activity", "position": {"x": 0, "y": 5}, "size": {"w": 8, "h": 4}},
            {"id": "quick_actions", "position": {"x": 8, "y": 5}, "size": {"w": 4, "h": 4}}
        ]


class ThemeManager:
    """Service for managing UI themes."""

    def __init__(self):
        """Initialize theme manager."""
        self.themes = {
            "default": {
                "name": "Default",
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "background": "#ffffff",
                "text": "#333333"
            },
            "dark": {
                "name": "Dark",
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
                "background": "#1a202c",
                "text": "#e2e8f0"
            },
            "high_contrast": {
                "name": "High Contrast",
                "primary_color": "#000000",
                "secondary_color": "#ffffff",
                "background": "#ffffff",
                "text": "#000000"
            }
        }
        self.user_themes = {}

    async def get_theme(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Get theme configuration.

        Args:
            theme_name: Name of the theme

        Returns:
            Theme configuration or None
        """
        return self.themes.get(theme_name)

    async def get_user_theme(self, user_id: str) -> Dict[str, Any]:
        """Get user's selected theme.

        Args:
            user_id: User identifier

        Returns:
            Theme configuration
        """
        theme_name = self.user_themes.get(user_id, "default")
        return self.themes.get(theme_name, self.themes["default"])

    async def set_user_theme(self, user_id: str, theme_name: str) -> bool:
        """Set user's theme.

        Args:
            user_id: User identifier
            theme_name: Name of the theme

        Returns:
            True if set successfully
        """
        if theme_name not in self.themes:
            raise ValueError(f"Unknown theme: {theme_name}")

        self.user_themes[user_id] = theme_name
        logger.info(f"Set theme '{theme_name}' for user: {user_id}")
        return True

    def list_themes(self) -> List[str]:
        """List available themes.

        Returns:
            List of theme names
        """
        return list(self.themes.keys())


class WebSocketManager:
    """Service for managing WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize WebSocket manager."""
        self.connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.user_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: str = None, channel: str = "default"):
        """Add a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: Optional user identifier
            channel: Channel name for grouping connections
        """
        await websocket.accept()
        self.connections[channel].add(websocket)

        if user_id:
            self.user_connections[user_id].add(websocket)

        logger.info(f"WebSocket connected - Channel: {channel}, User: {user_id}")

    async def disconnect(self, websocket: WebSocket, user_id: str = None, channel: str = "default"):
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: Optional user identifier
            channel: Channel name
        """
        self.connections[channel].discard(websocket)

        if user_id:
            self.user_connections[user_id].discard(websocket)

        logger.info(f"WebSocket disconnected - Channel: {channel}, User: {user_id}")

    async def broadcast(self, message: Dict[str, Any], channel: str = "default"):
        """Broadcast message to all connections in a channel.

        Args:
            message: Message to broadcast
            channel: Channel name
        """
        dead_connections = set()

        for websocket in self.connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {str(e)}")
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            self.connections[channel].discard(websocket)

    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to specific user's connections.

        Args:
            user_id: User identifier
            message: Message to send
        """
        dead_connections = set()

        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {str(e)}")
                dead_connections.add(websocket)

        # Clean up dead connections
        for websocket in dead_connections:
            self.user_connections[user_id].discard(websocket)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics.

        Returns:
            Connection statistics
        """
        total_connections = sum(len(conns) for conns in self.connections.values())
        total_users = len(self.user_connections)

        return {
            "total_connections": total_connections,
            "total_users": total_users,
            "channels": {
                channel: len(conns) for channel, conns in self.connections.items()
            },
            "users_connected": list(self.user_connections.keys())
        }


class ActivityLogger:
    """Service for logging and tracking activity."""

    def __init__(self, max_entries: int = 1000):
        """Initialize activity logger.

        Args:
            max_entries: Maximum number of entries to keep in memory
        """
        self.activities = []
        self.max_entries = max_entries

    async def log_activity(self, activity_type: str, description: str,
                          user_id: str = None, metadata: Dict[str, Any] = None):
        """Log an activity.

        Args:
            activity_type: Type of activity
            description: Activity description
            user_id: Optional user identifier
            metadata: Additional metadata
        """
        activity = {
            "timestamp": datetime.utcnow(),
            "type": activity_type,
            "description": description,
            "user_id": user_id,
            "metadata": metadata or {}
        }

        self.activities.append(activity)

        # Trim to max entries
        if len(self.activities) > self.max_entries:
            self.activities = self.activities[-self.max_entries:]

        logger.debug(f"Activity logged: {activity_type} - {description}")

    async def get_recent_activities(self, limit: int = 50,
                                   activity_type: str = None,
                                   user_id: str = None) -> List[Dict[str, Any]]:
        """Get recent activities.

        Args:
            limit: Maximum number of activities to return
            activity_type: Filter by activity type
            user_id: Filter by user ID

        Returns:
            List of recent activities
        """
        activities = self.activities.copy()
        activities.reverse()  # Most recent first

        # Apply filters
        if activity_type:
            activities = [a for a in activities if a["type"] == activity_type]

        if user_id:
            activities = [a for a in activities if a["user_id"] == user_id]

        return activities[:limit]

    def get_activity_stats(self) -> Dict[str, Any]:
        """Get activity statistics.

        Returns:
            Activity statistics
        """
        if not self.activities:
            return {
                "total": 0,
                "by_type": {},
                "by_user": {},
                "recent_hour": 0
            }

        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        by_type = defaultdict(int)
        by_user = defaultdict(int)
        recent_hour = 0

        for activity in self.activities:
            by_type[activity["type"]] += 1

            if activity["user_id"]:
                by_user[activity["user_id"]] += 1

            if activity["timestamp"] > hour_ago:
                recent_hour += 1

        return {
            "total": len(self.activities),
            "by_type": dict(by_type),
            "by_user": dict(by_user),
            "recent_hour": recent_hour
        }


class BackupService:
    """Service for backup and restore operations."""

    def __init__(self, backup_dir: Path):
        """Initialize backup service.

        Args:
            backup_dir: Directory for storing backups
        """
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self, name: str = None) -> str:
        """Create a backup of WebUI configuration and data.

        Args:
            name: Optional backup name

        Returns:
            Path to the backup file
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"webui_backup_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.zip"

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Collect data to backup
                backup_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "config": {},  # To be filled with actual config
                    "themes": {},  # To be filled with theme data
                    "layouts": {},  # To be filled with layout data
                    "preferences": {}  # To be filled with user preferences
                }

                # Save backup data to JSON
                backup_json = temp_path / "backup.json"
                async with aiofiles.open(backup_json, 'w') as f:
                    await f.write(json.dumps(backup_data, indent=2, default=str))

                # Create zip file
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(backup_json, "backup.json")

                logger.info(f"Created backup: {backup_file}")
                return str(backup_file)

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise

    async def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup file.

        Args:
            backup_path: Path to the backup file

        Returns:
            True if restore was successful
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Extract backup
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    zf.extractall(temp_path)

                # Load backup data
                backup_json = temp_path / "backup.json"
                async with aiofiles.open(backup_json, 'r') as f:
                    backup_data = json.loads(await f.read())

                # Restore data (implementation depends on actual data storage)
                # This is a placeholder for the actual restore logic
                logger.info(f"Restored backup from: {backup_file}")
                return True

        except Exception as e:
            logger.error(f"Failed to restore backup: {str(e)}")
            raise

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups.

        Returns:
            List of backup information
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.zip"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.stem,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return sorted(backups, key=lambda x: x["created"], reverse=True)


class MetricsCollector:
    """Service for collecting and aggregating metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = defaultdict(list)
        self.max_data_points = 1000

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics.

        Returns:
            Dictionary of system metrics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()

            metrics = {
                "timestamp": datetime.utcnow(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "disk_percent": disk.percent,
                "disk_used": disk.used,
                "disk_total": disk.total,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv
            }

            # Store metrics
            for key, value in metrics.items():
                if key != "timestamp":
                    self.metrics[key].append({
                        "timestamp": metrics["timestamp"],
                        "value": value
                    })

                    # Trim to max data points
                    if len(self.metrics[key]) > self.max_data_points:
                        self.metrics[key] = self.metrics[key][-self.max_data_points:]

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")
            return {}

    async def get_metric_history(self, metric_name: str,
                                duration_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get historical data for a metric.

        Args:
            metric_name: Name of the metric
            duration_minutes: How many minutes of history to return

        Returns:
            List of metric data points
        """
        if metric_name not in self.metrics:
            return []

        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)

        return [
            point for point in self.metrics[metric_name]
            if point["timestamp"] > cutoff_time
        ]

    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.

        Returns:
            Summary statistics for all metrics
        """
        summary = {}

        for metric_name, data_points in self.metrics.items():
            if not data_points:
                continue

            values = [p["value"] for p in data_points]

            summary[metric_name] = {
                "current": values[-1] if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "avg": sum(values) / len(values) if values else 0,
                "data_points": len(values)
            }

        return summary


# Export all service classes
__all__ = [
    "TemplateService",
    "StaticFileService",
    "SessionManager",
    "WidgetManager",
    "ThemeManager",
    "WebSocketManager",
    "ActivityLogger",
    "BackupService",
    "MetricsCollector"
]
