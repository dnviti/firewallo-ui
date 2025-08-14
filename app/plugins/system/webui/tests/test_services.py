#!/usr/bin/env python3
"""
Service layer tests for WebUI Plugin.
Tests all service classes and their functionality.
"""

import sys
import os
import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Add paths for testing
plugin_dir = Path(__file__).parent.parent
app_dir = plugin_dir.parent.parent.parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plugin_dir))


class TestTemplateService:
    """Test TemplateService functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.templates_dir = self.temp_dir / "templates"
        self.templates_dir.mkdir()

        # Create test template
        test_template = self.templates_dir / "test.html"
        test_template.write_text("""
        <html>
        <head><title>{{ title }}</title></head>
        <body><h1>{{ heading }}</h1></body>
        </html>
        """)

        from services import TemplateService
        self.service = TemplateService(self.templates_dir)

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_render_template(self):
        """Test template rendering with context."""
        context = {"title": "Test Title", "heading": "Test Heading"}

        result = await self.service.render_template("test.html", context)

        assert "Test Title" in result
        assert "Test Heading" in result
        assert "<html>" in result

    def test_list_templates(self):
        """Test listing available templates."""
        # Create additional template
        (self.templates_dir / "another.html").write_text("<html></html>")

        templates = self.service.list_templates()

        assert "test.html" in templates
        assert "another.html" in templates
        assert len(templates) == 2

    def test_validate_template_valid(self):
        """Test validation of existing template."""
        result = self.service.validate_template("test.html")
        assert result is True

    def test_validate_template_invalid(self):
        """Test validation of non-existent template."""
        result = self.service.validate_template("nonexistent.html")
        assert result is False


class TestStaticFileService:
    """Test StaticFileService functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.static_dir = self.temp_dir / "static"
        self.static_dir.mkdir()

        # Create test files
        css_dir = self.static_dir / "css"
        css_dir.mkdir()
        (css_dir / "style.css").write_text("body { color: red; }")

        js_dir = self.static_dir / "js"
        js_dir.mkdir()
        (js_dir / "script.js").write_text("console.log('test');")

        from services import StaticFileService
        self.service = StaticFileService(self.static_dir)

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_serve_file_css(self):
        """Test serving CSS file."""
        response = await self.service.serve_file("css/style.css")

        assert response.status_code == 200
        assert response.media_type == "text/css"

    @pytest.mark.asyncio
    async def test_serve_file_js(self):
        """Test serving JavaScript file."""
        response = await self.service.serve_file("js/script.js")

        assert response.status_code == 200
        assert "javascript" in response.media_type

    @pytest.mark.asyncio
    async def test_serve_file_not_found(self):
        """Test serving non-existent file."""
        with pytest.raises(FileNotFoundError):
            await self.service.serve_file("nonexistent.css")

    @pytest.mark.asyncio
    async def test_serve_file_security(self):
        """Test security check for path traversal."""
        with pytest.raises(PermissionError):
            await self.service.serve_file("../../../etc/passwd")

    def test_list_static_files(self):
        """Test listing static files by type."""
        files = self.service.list_static_files()

        assert "css" in files
        assert "js" in files
        assert "css/style.css" in files["css"]
        assert "js/script.js" in files["js"]


class TestSessionManager:
    """Test SessionManager functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import SessionManager
        self.manager = SessionManager(max_sessions=5, timeout=3600)

    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation."""
        session_id = await self.manager.create_session("user1", {"test": "data"})

        assert session_id is not None
        assert len(session_id) > 0
        assert session_id in self.manager.sessions

    @pytest.mark.asyncio
    async def test_get_session_valid(self):
        """Test getting valid session."""
        session_id = await self.manager.create_session("user1", {"test": "data"})

        session = await self.manager.get_session(session_id)

        assert session is not None
        assert session["user_id"] == "user1"
        assert session["data"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_get_session_invalid(self):
        """Test getting invalid session."""
        session = await self.manager.get_session("invalid_session_id")

        assert session is None

    @pytest.mark.asyncio
    async def test_destroy_session(self):
        """Test session destruction."""
        session_id = await self.manager.create_session("user1")

        result = await self.manager.destroy_session(session_id)

        assert result is True
        assert session_id not in self.manager.sessions

    @pytest.mark.asyncio
    async def test_session_timeout(self):
        """Test session timeout handling."""
        # Create session with short timeout
        manager = SessionManager(timeout=1)
        session_id = await manager.create_session("user1")

        # Wait for timeout
        await asyncio.sleep(2)

        session = await manager.get_session(session_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_max_sessions_limit(self):
        """Test maximum sessions limit."""
        # Create maximum number of sessions
        for i in range(5):
            await self.manager.create_session(f"user{i}")

        # Try to create one more
        with pytest.raises(RuntimeError):
            await self.manager.create_session("user6")

    def test_get_active_sessions(self):
        """Test getting active session count."""
        initial_count = self.manager.get_active_sessions()
        assert initial_count == 0

    def test_get_session_stats(self):
        """Test getting session statistics."""
        stats = self.manager.get_session_stats()

        assert "active" in stats
        assert "average_duration" in stats
        assert "max_duration" in stats
        assert "users" in stats


class TestWidgetManager:
    """Test WidgetManager functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import WidgetManager
        self.manager = WidgetManager()

    @pytest.mark.asyncio
    async def test_register_widget(self):
        """Test widget registration."""
        widget = {
            "id": "test_widget",
            "name": "Test Widget",
            "description": "A test widget",
            "size": "medium"
        }

        result = await self.manager.register_widget(widget)

        assert result is True
        assert "test_widget" in self.manager.widgets

    @pytest.mark.asyncio
    async def test_register_widget_no_id(self):
        """Test widget registration without ID."""
        widget = {"name": "Test Widget"}

        with pytest.raises(ValueError):
            await self.manager.register_widget(widget)

    @pytest.mark.asyncio
    async def test_get_widget(self):
        """Test getting widget configuration."""
        widget = {"id": "test_widget", "name": "Test Widget"}
        await self.manager.register_widget(widget)

        result = await self.manager.get_widget("test_widget")

        assert result is not None
        assert result["id"] == "test_widget"
        assert result["name"] == "Test Widget"
        assert "registered_at" in result

    @pytest.mark.asyncio
    async def test_get_widget_not_found(self):
        """Test getting non-existent widget."""
        result = await self.manager.get_widget("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_layout_default(self):
        """Test getting default user layout."""
        layout = await self.manager.get_user_layout("user1")

        assert isinstance(layout, list)
        assert len(layout) > 0
        # Should return default layout with system widgets

    @pytest.mark.asyncio
    async def test_save_user_layout(self):
        """Test saving user layout."""
        layout = [
            {"id": "widget1", "position": {"x": 0, "y": 0}},
            {"id": "widget2", "position": {"x": 1, "y": 0}}
        ]

        result = await self.manager.save_user_layout("user1", layout)

        assert result is True
        assert "user1" in self.manager.user_layouts

    @pytest.mark.asyncio
    async def test_get_saved_user_layout(self):
        """Test getting saved user layout."""
        layout = [{"id": "widget1", "position": {"x": 0, "y": 0}}]
        await self.manager.save_user_layout("user1", layout)

        result = await self.manager.get_user_layout("user1")

        assert result == layout


class TestThemeManager:
    """Test ThemeManager functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import ThemeManager
        self.manager = ThemeManager()

    @pytest.mark.asyncio
    async def test_get_theme(self):
        """Test getting theme configuration."""
        theme = await self.manager.get_theme("default")

        assert theme is not None
        assert theme["name"] == "Default"
        assert "primary_color" in theme
        assert "secondary_color" in theme

    @pytest.mark.asyncio
    async def test_get_theme_not_found(self):
        """Test getting non-existent theme."""
        theme = await self.manager.get_theme("nonexistent")

        assert theme is None

    @pytest.mark.asyncio
    async def test_get_user_theme_default(self):
        """Test getting user theme defaults to default theme."""
        theme = await self.manager.get_user_theme("user1")

        assert theme is not None
        assert theme["name"] == "Default"

    @pytest.mark.asyncio
    async def test_set_user_theme(self):
        """Test setting user theme."""
        result = await self.manager.set_user_theme("user1", "dark")

        assert result is True
        assert self.manager.user_themes["user1"] == "dark"

    @pytest.mark.asyncio
    async def test_set_user_theme_invalid(self):
        """Test setting invalid user theme."""
        with pytest.raises(ValueError):
            await self.manager.set_user_theme("user1", "nonexistent")

    @pytest.mark.asyncio
    async def test_get_user_theme_after_set(self):
        """Test getting user theme after setting."""
        await self.manager.set_user_theme("user1", "dark")

        theme = await self.manager.get_user_theme("user1")

        assert theme["name"] == "Dark"

    def test_list_themes(self):
        """Test listing available themes."""
        themes = self.manager.list_themes()

        assert "default" in themes
        assert "dark" in themes
        assert "high_contrast" in themes


class TestWebSocketManager:
    """Test WebSocketManager functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import WebSocketManager
        self.manager = WebSocketManager()

    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test WebSocket connection."""
        mock_websocket = AsyncMock()

        await self.manager.connect(mock_websocket, "user1", "test_channel")

        assert mock_websocket in self.manager.connections["test_channel"]
        assert mock_websocket in self.manager.user_connections["user1"]
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self):
        """Test WebSocket disconnection."""
        mock_websocket = AsyncMock()
        await self.manager.connect(mock_websocket, "user1", "test_channel")

        await self.manager.disconnect(mock_websocket, "user1", "test_channel")

        assert mock_websocket not in self.manager.connections["test_channel"]
        assert mock_websocket not in self.manager.user_connections["user1"]

    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        """Test broadcasting message to channel."""
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()

        await self.manager.connect(mock_websocket1, channel="test_channel")
        await self.manager.connect(mock_websocket2, channel="test_channel")

        message = {"type": "test", "data": "hello"}
        await self.manager.broadcast(message, "test_channel")

        mock_websocket1.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_to_user(self):
        """Test sending message to specific user."""
        mock_websocket = AsyncMock()
        await self.manager.connect(mock_websocket, "user1")

        message = {"type": "test", "data": "hello user1"}
        await self.manager.send_to_user("user1", message)

        mock_websocket.send_json.assert_called_once_with(message)

    def test_get_connection_stats(self):
        """Test getting connection statistics."""
        stats = self.manager.get_connection_stats()

        assert "total_connections" in stats
        assert "total_users" in stats
        assert "channels" in stats
        assert "users_connected" in stats
        assert isinstance(stats["total_connections"], int)


class TestActivityLogger:
    """Test ActivityLogger functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import ActivityLogger
        self.logger = ActivityLogger(max_entries=10)

    @pytest.mark.asyncio
    async def test_log_activity(self):
        """Test logging activity."""
        await self.logger.log_activity("test", "Test activity", "user1", {"key": "value"})

        assert len(self.logger.activities) == 1
        activity = self.logger.activities[0]

        assert activity["type"] == "test"
        assert activity["description"] == "Test activity"
        assert activity["user_id"] == "user1"
        assert activity["metadata"]["key"] == "value"
        assert "timestamp" in activity

    @pytest.mark.asyncio
    async def test_get_recent_activities(self):
        """Test getting recent activities."""
        # Log multiple activities
        for i in range(5):
            await self.logger.log_activity("test", f"Activity {i}", f"user{i}")

        activities = await self.logger.get_recent_activities(3)

        assert len(activities) == 3
        # Should be in reverse chronological order (most recent first)
        assert activities[0]["description"] == "Activity 4"
        assert activities[1]["description"] == "Activity 3"

    @pytest.mark.asyncio
    async def test_get_recent_activities_filtered_by_type(self):
        """Test getting activities filtered by type."""
        await self.logger.log_activity("login", "User logged in", "user1")
        await self.logger.log_activity("logout", "User logged out", "user1")
        await self.logger.log_activity("login", "User logged in", "user2")

        activities = await self.logger.get_recent_activities(10, activity_type="login")

        assert len(activities) == 2
        for activity in activities:
            assert activity["type"] == "login"

    @pytest.mark.asyncio
    async def test_get_recent_activities_filtered_by_user(self):
        """Test getting activities filtered by user."""
        await self.logger.log_activity("login", "User logged in", "user1")
        await self.logger.log_activity("logout", "User logged out", "user2")
        await self.logger.log_activity("login", "User logged in", "user1")

        activities = await self.logger.get_recent_activities(10, user_id="user1")

        assert len(activities) == 2
        for activity in activities:
            assert activity["user_id"] == "user1"

    @pytest.mark.asyncio
    async def test_max_entries_limit(self):
        """Test maximum entries limit."""
        # Log more activities than the limit
        for i in range(15):
            await self.logger.log_activity("test", f"Activity {i}", "user1")

        assert len(self.logger.activities) == 10  # Should be trimmed to max_entries

    def test_get_activity_stats(self):
        """Test getting activity statistics."""
        stats = self.logger.get_activity_stats()

        assert "total" in stats
        assert "by_type" in stats
        assert "by_user" in stats
        assert "recent_hour" in stats
        assert isinstance(stats["total"], int)


class TestBackupService:
    """Test BackupService functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.temp_dir / "backups"

        from services import BackupService
        self.service = BackupService(self.backup_dir)

    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_create_backup(self):
        """Test creating backup."""
        backup_path = await self.service.create_backup("test_backup")

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert backup_path.endswith(".zip")

    @pytest.mark.asyncio
    async def test_create_backup_auto_name(self):
        """Test creating backup with auto-generated name."""
        backup_path = await self.service.create_backup()

        assert backup_path is not None
        assert Path(backup_path).exists()
        assert "webui_backup_" in backup_path

    def test_list_backups(self):
        """Test listing backups."""
        # Create a test backup file
        test_backup = self.backup_dir / "test_backup.zip"
        test_backup.parent.mkdir(parents=True, exist_ok=True)
        test_backup.write_bytes(b"test backup content")

        backups = self.service.list_backups()

        assert len(backups) == 1
        assert backups[0]["name"] == "test_backup"
        assert "size" in backups[0]
        assert "created" in backups[0]

    @pytest.mark.asyncio
    async def test_restore_backup(self):
        """Test restoring from backup."""
        # Create a test backup first
        backup_path = await self.service.create_backup("test_restore")

        # Test restore
        result = await self.service.restore_backup(backup_path)

        assert result is True

    @pytest.mark.asyncio
    async def test_restore_backup_not_found(self):
        """Test restoring from non-existent backup."""
        with pytest.raises(FileNotFoundError):
            await self.service.restore_backup("/nonexistent/backup.zip")


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    def setup_method(self):
        """Setup test environment."""
        from services import MetricsCollector
        self.collector = MetricsCollector()

    @pytest.mark.asyncio
    async def test_collect_system_metrics(self):
        """Test collecting system metrics."""
        metrics = await self.collector.collect_system_metrics()

        assert isinstance(metrics, dict)
        if metrics:  # If psutil is available
            assert "timestamp" in metrics
            assert "cpu_percent" in metrics
            assert "memory_percent" in metrics
            assert isinstance(metrics["cpu_percent"], (int, float))

    @pytest.mark.asyncio
    async def test_get_metric_history(self):
        """Test getting metric history."""
        # Collect some metrics first
        await self.collector.collect_system_metrics()
        await asyncio.sleep(0.1)
        await self.collector.collect_system_metrics()

        history = await self.collector.get_metric_history("cpu_percent", 60)

        assert isinstance(history, list)
        # May be empty if psutil is not available

    @pytest.mark.asyncio
    async def test_get_metric_history_nonexistent(self):
        """Test getting history for non-existent metric."""
        history = await self.collector.get_metric_history("nonexistent_metric", 60)

        assert history == []

    def test_get_metric_summary(self):
        """Test getting metric summary."""
        summary = self.collector.get_metric_summary()

        assert isinstance(summary, dict)
        # Summary may be empty if no metrics have been collected

    def test_max_data_points_limit(self):
        """Test that metrics don't exceed max data points."""
        # Manually add metrics to test limit
        import datetime
        now = datetime.datetime.utcnow()

        # Add more than max_data_points
        for i in range(1100):
            self.collector.metrics["test_metric"].append({
                "timestamp": now,
                "value": i
            })

        # Should be trimmed to max_data_points (1000)
        assert len(self.collector.metrics["test_metric"]) == 1000


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
