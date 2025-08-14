#!/usr/bin/env python3
"""
API endpoint tests for WebUI Plugin.
Tests all API routes, request/response handling, and endpoint functionality.
"""

import sys
import os
import json
import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import httpx

# Add paths for testing
plugin_dir = Path(__file__).parent.parent
app_dir = plugin_dir.parent.parent.parent.parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(plugin_dir))


@pytest.fixture
async def webui_plugin():
    """Create and initialize WebUI plugin for testing."""
    from plugin import WebUIPlugin

    plugin = WebUIPlugin()
    await plugin.initialize()
    yield plugin
    await plugin.shutdown()


@pytest.fixture
def test_app(webui_plugin):
    """Create FastAPI test application with WebUI routes."""
    app = FastAPI()

    # Add WebUI routes to test app
    routers = webui_plugin.get_api_routes()
    for router in routers:
        app.include_router(router)

    return app


@pytest.fixture
def client(test_app):
    """Create test client for API testing."""
    return TestClient(test_app)


class TestWebUIWebRoutes:
    """Test WebUI web interface routes."""

    def test_root_redirect(self, client):
        """Test root path redirects to dashboard."""
        response = client.get("/", allow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/dashboard"

    def test_dashboard_route(self, client):
        """Test dashboard route returns HTML."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/dashboard")

            # Should attempt to render template
            mock_templates.TemplateResponse.assert_called_once()

    def test_plugins_route(self, client):
        """Test plugins management route."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/plugins")

            mock_templates.TemplateResponse.assert_called_once()

    def test_login_route(self, client):
        """Test login route returns login page."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/login")

            mock_templates.TemplateResponse.assert_called_once()

    def test_logout_route(self, client):
        """Test logout route redirects and clears cookies."""
        response = client.get("/logout", allow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_firewall_route(self, client):
        """Test firewall management route."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/firewall")

            mock_templates.TemplateResponse.assert_called_once()

    def test_monitoring_route(self, client):
        """Test monitoring route."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/monitoring")

            mock_templates.TemplateResponse.assert_called_once()

    def test_logs_route(self, client):
        """Test logs viewer route."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/logs")

            mock_templates.TemplateResponse.assert_called_once()

    def test_settings_route(self, client):
        """Test settings route."""
        with patch('plugin.WebUIPlugin.templates') as mock_templates:
            mock_templates.TemplateResponse.return_value = Mock()
            mock_templates.TemplateResponse.return_value.status_code = 200

            response = client.get("/settings")

            mock_templates.TemplateResponse.assert_called_once()


class TestWebUIAPIRoutes:
    """Test WebUI API routes."""

    def test_get_status(self, client, webui_plugin):
        """Test GET /api/webui/status endpoint."""
        response = client.get("/api/webui/status")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "uptime" in data
        assert "config" in data
        assert "metrics" in data

        assert data["version"] == "2.0.0"
        assert isinstance(data["uptime"], (int, float))
        assert isinstance(data["config"], dict)
        assert isinstance(data["metrics"], dict)

    def test_get_config(self, client, webui_plugin):
        """Test GET /api/webui/config endpoint."""
        response = client.get("/api/webui/config")

        assert response.status_code == 200
        data = response.json()

        # Should contain default configuration fields
        expected_fields = [
            "enabled", "port", "host", "theme",
            "auto_refresh_interval", "session_timeout"
        ]

        for field in expected_fields:
            assert field in data, f"Config should contain {field}"

    def test_update_config_valid(self, client, webui_plugin):
        """Test POST /api/webui/config with valid data."""
        valid_config = {
            "enabled": True,
            "port": 8080,
            "host": "0.0.0.0",
            "theme": "dark",
            "auto_refresh_interval": 120,
            "session_timeout": 7200,
            "max_sessions": 50,
            "enable_notifications": True,
            "enable_sound_alerts": False,
            "enable_dark_mode": True,
            "enable_api_docs": True,
            "dashboard_widgets": ["system_status", "cpu_usage"],
            "default_language": "en",
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD HH:mm:ss",
            "enable_metrics": True,
            "enable_activity_log": True,
            "max_log_entries": 500
        }

        response = client.post("/api/webui/config", json=valid_config)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data

    def test_update_config_invalid(self, client, webui_plugin):
        """Test POST /api/webui/config with invalid data."""
        invalid_config = {
            "port": "not_a_number",
            "session_timeout": "invalid"
        }

        response = client.post("/api/webui/config", json=invalid_config)

        assert response.status_code == 422  # Validation error

    def test_get_metrics(self, client, webui_plugin):
        """Test GET /api/webui/metrics endpoint."""
        response = client.get("/api/webui/metrics")

        assert response.status_code == 200
        data = response.json()

        expected_fields = [
            "uptime_seconds", "active_sessions", "total_requests"
        ]

        for field in expected_fields:
            assert field in data, f"Metrics should contain {field}"
            assert isinstance(data[field], (int, float))

    def test_get_widgets_default_user(self, client, webui_plugin):
        """Test GET /api/webui/widgets endpoint with default user."""
        response = client.get("/api/webui/widgets")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Should return default widgets if none configured
        if len(data) > 0:
            widget = data[0]
            assert "id" in widget
            assert "enabled" in widget
            assert "position" in widget

    def test_get_widgets_specific_user(self, client, webui_plugin):
        """Test GET /api/webui/widgets endpoint with specific user."""
        response = client.get("/api/webui/widgets?user_id=test_user")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    def test_save_widgets(self, client, webui_plugin):
        """Test POST /api/webui/widgets endpoint."""
        widget_config = [
            {
                "id": "system_status",
                "enabled": True,
                "position": 0,
                "size": "small",
                "refresh_interval": 30,
                "settings": {}
            },
            {
                "id": "cpu_usage",
                "enabled": True,
                "position": 1,
                "size": "medium",
                "refresh_interval": 10,
                "settings": {}
            }
        ]

        response = client.post("/api/webui/widgets", json=widget_config)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data

    def test_get_preferences(self, client, webui_plugin):
        """Test GET /api/webui/preferences/{user_id} endpoint."""
        response = client.get("/api/webui/preferences/test_user")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, dict)
        # Should have default preferences structure
        expected_fields = ["theme", "language", "dashboard_layout", "notifications"]
        for field in expected_fields:
            assert field in data

    def test_save_preferences(self, client, webui_plugin):
        """Test POST /api/webui/preferences/{user_id} endpoint."""
        preferences = {
            "theme": "dark",
            "language": "en",
            "dashboard_layout": ["widget1", "widget2"],
            "notifications": True,
            "sidebar_collapsed": False
        }

        response = client.post("/api/webui/preferences/test_user", json=preferences)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data

    def test_get_activity(self, client, webui_plugin):
        """Test GET /api/webui/activity endpoint."""
        response = client.get("/api/webui/activity")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Each activity should have required fields
        for activity in data:
            assert "timestamp" in activity
            assert "type" in activity
            assert "description" in activity

    def test_get_activity_with_limit(self, client, webui_plugin):
        """Test GET /api/webui/activity endpoint with limit parameter."""
        response = client.get("/api/webui/activity?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) <= 10

    def test_set_theme(self, client, webui_plugin):
        """Test POST /api/webui/theme endpoint."""
        theme_config = {
            "name": "dark",
            "primary_color": "#333333",
            "secondary_color": "#666666",
            "dark_mode": True,
            "custom_css": None
        }

        response = client.post("/api/webui/theme", json=theme_config)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "dark" in data["message"]


class TestWebUIAPIErrorHandling:
    """Test WebUI API error handling."""

    def test_invalid_endpoint(self, client):
        """Test request to non-existent endpoint."""
        response = client.get("/api/webui/nonexistent")

        assert response.status_code == 404

    def test_invalid_method(self, client):
        """Test invalid HTTP method on valid endpoint."""
        response = client.delete("/api/webui/status")

        assert response.status_code == 405  # Method not allowed

    def test_malformed_json(self, client):
        """Test request with malformed JSON."""
        response = client.post(
            "/api/webui/config",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable entity

    def test_missing_required_fields(self, client):
        """Test request missing required fields."""
        incomplete_config = {
            "theme": "dark"
            # Missing required fields like enabled, port, host
        }

        response = client.post("/api/webui/config", json=incomplete_config)

        assert response.status_code == 422

    def test_invalid_user_id(self, client):
        """Test request with invalid user ID format."""
        # Test with various invalid user IDs
        invalid_ids = ["", " ", "user@invalid", "user/invalid"]

        for user_id in invalid_ids:
            response = client.get(f"/api/webui/preferences/{user_id}")
            # Should either handle gracefully or return appropriate error
            assert response.status_code in [200, 400, 422]


class TestWebUIAPIAuthentication:
    """Test WebUI API authentication and authorization."""

    def test_unauthenticated_request(self, client):
        """Test API request without authentication."""
        # For now, WebUI doesn't enforce authentication in tests
        # This test documents the expected behavior
        response = client.get("/api/webui/status")

        # Currently allows unauthenticated access
        assert response.status_code == 200

    def test_authenticated_request(self, client):
        """Test API request with authentication token."""
        headers = {"Authorization": "Bearer test-token"}
        response = client.get("/api/webui/status", headers=headers)

        # Should work with or without token currently
        assert response.status_code == 200

    def test_invalid_token(self, client):
        """Test API request with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/webui/status", headers=headers)

        # Should work regardless of token validity currently
        assert response.status_code == 200


class TestWebUIAPIPerformance:
    """Test WebUI API performance characteristics."""

    def test_status_endpoint_performance(self, client):
        """Test status endpoint response time."""
        import time

        start_time = time.time()
        response = client.get("/api/webui/status")
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_concurrent_requests(self, client):
        """Test handling of concurrent API requests."""
        import concurrent.futures
        import time

        def make_request():
            return client.get("/api/webui/status")

        # Make 10 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        end_time = time.time()

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

        # Should complete within reasonable time
        assert (end_time - start_time) < 5.0

    def test_large_config_update(self, client):
        """Test API handling of large configuration updates."""
        # Create a large configuration object
        large_config = {
            "enabled": True,
            "port": 8080,
            "host": "0.0.0.0",
            "theme": "default",
            "auto_refresh_interval": 60,
            "session_timeout": 3600,
            "max_sessions": 100,
            "enable_notifications": True,
            "enable_sound_alerts": False,
            "enable_dark_mode": False,
            "enable_api_docs": True,
            "dashboard_widgets": [f"widget_{i}" for i in range(100)],  # Large list
            "default_language": "en",
            "timezone": "UTC",
            "date_format": "YYYY-MM-DD HH:mm:ss",
            "enable_metrics": True,
            "enable_activity_log": True,
            "max_log_entries": 1000,
            "custom_data": {f"key_{i}": f"value_{i}" for i in range(100)}  # Large dict
        }

        response = client.post("/api/webui/config", json=large_config)

        # Should handle large payloads gracefully
        assert response.status_code in [200, 413, 422]  # Success or payload too large


class TestWebUIAPIValidation:
    """Test WebUI API input validation."""

    def test_config_validation_port_range(self, client):
        """Test port validation in configuration."""
        invalid_ports = [-1, 0, 99999, "string", None]

        for port in invalid_ports:
            config = {
                "enabled": True,
                "port": port,
                "host": "0.0.0.0",
                "theme": "default",
                "auto_refresh_interval": 60,
                "session_timeout": 3600,
                "max_sessions": 100,
                "enable_notifications": True,
                "enable_sound_alerts": False,
                "enable_dark_mode": False,
                "enable_api_docs": True,
                "dashboard_widgets": [],
                "default_language": "en",
                "timezone": "UTC",
                "date_format": "YYYY-MM-DD HH:mm:ss",
                "enable_metrics": True,
                "enable_activity_log": True,
                "max_log_entries": 1000
            }

            response = client.post("/api/webui/config", json=config)
            assert response.status_code == 422, f"Invalid port {port} should be rejected"

    def test_config_validation_session_timeout(self, client):
        """Test session timeout validation."""
        invalid_timeouts = [-1, 0, 30, "string", None]  # Too low or invalid

        for timeout in invalid_timeouts:
            config = {
                "enabled": True,
                "port": 8080,
                "host": "0.0.0.0",
                "theme": "default",
                "auto_refresh_interval": 60,
                "session_timeout": timeout,
                "max_sessions": 100,
                "enable_notifications": True,
                "enable_sound_alerts": False,
                "enable_dark_mode": False,
                "enable_api_docs": True,
                "dashboard_widgets": [],
                "default_language": "en",
                "timezone": "UTC",
                "date_format": "YYYY-MM-DD HH:mm:ss",
                "enable_metrics": True,
                "enable_activity_log": True,
                "max_log_entries": 1000
            }

            response = client.post("/api/webui/config", json=config)
            assert response.status_code == 422, f"Invalid timeout {timeout} should be rejected"

    def test_widget_validation(self, client):
        """Test widget configuration validation."""
        invalid_widget_configs = [
            # Missing required fields
            [{"enabled": True}],
            # Invalid types
            [{"id": 123, "enabled": "yes", "position": "first"}],
            # Invalid values
            [{"id": "", "enabled": True, "position": -1}]
        ]

        for widget_config in invalid_widget_configs:
            response = client.post("/api/webui/widgets", json=widget_config)
            assert response.status_code == 422, f"Invalid widget config should be rejected: {widget_config}"

    def test_theme_validation(self, client):
        """Test theme configuration validation."""
        invalid_themes = [
            {"name": ""},  # Empty name
            {"name": "valid", "dark_mode": "yes"},  # Wrong type for dark_mode
            {"name": "valid", "primary_color": "not-a-color"},  # Invalid color
        ]

        for theme in invalid_themes:
            response = client.post("/api/webui/theme", json=theme)
            assert response.status_code == 422, f"Invalid theme should be rejected: {theme}"


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
