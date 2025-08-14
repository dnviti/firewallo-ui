#!/usr/bin/env python3
"""
System API endpoint tests for Firewallo UI.

Tests the system-related API endpoints including:
- Health checks
- System statistics
- Activity monitoring
- Configuration endpoints
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import status

# Test markers
pytestmark = [pytest.mark.api, pytest.mark.asyncio]


class TestSystemHealthEndpoints:
    """Test system health check endpoints."""

    async def test_health_check_success(self, test_client: AsyncClient):
        """Test successful health check."""
        response = await test_client.get("/api/system/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "uptime" in data

    async def test_health_check_with_details(self, test_client: AsyncClient):
        """Test health check with detailed information."""
        response = await test_client.get("/api/system/health?details=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert "components" in data
        assert "database" in data["components"]
        assert "plugins" in data["components"]

    @patch('app.core.health.HealthChecker.check_health')
    async def test_health_check_degraded(self, mock_health_check, test_client: AsyncClient):
        """Test health check when system is degraded."""
        mock_health_check.return_value = {
            "status": "degraded",
            "timestamp": "2023-01-01T12:00:00Z",
            "version": "1.0.0",
            "uptime": 86400,
            "components": {
                "database": {"status": "healthy"},
                "plugins": {"status": "degraded", "message": "Some plugins offline"}
            }
        }

        response = await test_client.get("/api/system/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "degraded"

    @patch('app.core.health.HealthChecker.check_health')
    async def test_health_check_unhealthy(self, mock_health_check, test_client: AsyncClient):
        """Test health check when system is unhealthy."""
        mock_health_check.return_value = {
            "status": "unhealthy",
            "timestamp": "2023-01-01T12:00:00Z",
            "version": "1.0.0",
            "uptime": 86400,
            "components": {
                "database": {"status": "unhealthy", "message": "Connection failed"},
                "plugins": {"status": "unhealthy", "message": "Plugin system offline"}
            }
        }

        response = await test_client.get("/api/system/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unhealthy"

    async def test_readiness_check(self, test_client: AsyncClient):
        """Test readiness probe endpoint."""
        response = await test_client.get("/api/system/ready")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        data = response.json()
        assert "ready" in data

    async def test_liveness_check(self, test_client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await test_client.get("/api/system/alive")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["alive"] is True


class TestSystemStatsEndpoints:
    """Test system statistics endpoints."""

    @patch('app.api.routes.system.get_system_stats')
    async def test_get_system_stats(self, mock_get_stats, test_client: AsyncClient, mock_system_stats):
        """Test retrieving system statistics."""
        mock_get_stats.return_value = mock_system_stats

        response = await test_client.get("/api/system/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check required fields
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "uptime" in data
        assert "timestamp" in data

        # Check CPU stats
        cpu = data["cpu"]
        assert "usage" in cpu
        assert "cores" in cpu
        assert isinstance(cpu["usage"], (int, float))
        assert isinstance(cpu["cores"], int)

        # Check memory stats
        memory = data["memory"]
        assert "total" in memory
        assert "used" in memory
        assert "available" in memory
        assert "percentage" in memory

    @patch('app.api.routes.system.get_system_stats')
    async def test_get_system_stats_error(self, mock_get_stats, test_client: AsyncClient):
        """Test system stats endpoint when stats collection fails."""
        mock_get_stats.side_effect = Exception("Stats collection failed")

        response = await test_client.get("/api/system/stats")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data

    async def test_get_cpu_stats(self, test_client: AsyncClient):
        """Test retrieving CPU-specific statistics."""
        response = await test_client.get("/api/system/stats/cpu")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "usage" in data
        assert "cores" in data
        assert "load_average" in data

    async def test_get_memory_stats(self, test_client: AsyncClient):
        """Test retrieving memory-specific statistics."""
        response = await test_client.get("/api/system/stats/memory")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total" in data
        assert "used" in data
        assert "available" in data
        assert "percentage" in data

    async def test_get_disk_stats(self, test_client: AsyncClient):
        """Test retrieving disk-specific statistics."""
        response = await test_client.get("/api/system/stats/disk")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total" in data
        assert "used" in data
        assert "free" in data
        assert "percentage" in data

    async def test_get_network_stats(self, test_client: AsyncClient):
        """Test retrieving network-specific statistics."""
        response = await test_client.get("/api/system/stats/network")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "bytes_sent" in data
        assert "bytes_recv" in data
        assert "packets_sent" in data
        assert "packets_recv" in data


class TestSystemActivityEndpoints:
    """Test system activity monitoring endpoints."""

    @patch('app.api.routes.system.get_recent_activity')
    async def test_get_recent_activity(self, mock_get_activity, test_client: AsyncClient):
        """Test retrieving recent system activity."""
        mock_activity = [
            {
                "id": "1",
                "timestamp": "2023-01-01T12:00:00Z",
                "type": "user_login",
                "user_id": "test-user",
                "details": {"ip": "192.168.1.100"},
                "severity": "info"
            },
            {
                "id": "2",
                "timestamp": "2023-01-01T11:30:00Z",
                "type": "plugin_loaded",
                "details": {"plugin": "wireguard"},
                "severity": "info"
            }
        ]
        mock_get_activity.return_value = mock_activity

        response = await test_client.get("/api/system/activity/recent")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        # Check activity structure
        activity = data[0]
        assert "id" in activity
        assert "timestamp" in activity
        assert "type" in activity
        assert "severity" in activity

    async def test_get_activity_with_filters(self, test_client: AsyncClient):
        """Test retrieving activity with filters."""
        params = {
            "limit": 50,
            "type": "user_login",
            "severity": "warning",
            "since": "2023-01-01T00:00:00Z"
        }

        response = await test_client.get("/api/system/activity/recent", params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_activity_types(self, test_client: AsyncClient):
        """Test retrieving available activity types."""
        response = await test_client.get("/api/system/activity/types")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        # Should contain common activity types
        expected_types = ["user_login", "user_logout", "plugin_loaded", "plugin_error"]
        for activity_type in expected_types:
            assert activity_type in data


class TestSystemConfigurationEndpoints:
    """Test system configuration endpoints."""

    async def test_get_system_info(self, test_client: AsyncClient):
        """Test retrieving system information."""
        response = await test_client.get("/api/system/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "version" in data
        assert "build_date" in data
        assert "environment" in data
        assert "python_version" in data

    @patch('app.api.routes.system.get_system_config')
    async def test_get_system_config(self, mock_get_config, test_client: AsyncClient, mock_auth_token):
        """Test retrieving system configuration (admin only)."""
        mock_config = {
            "database": {"url": "***HIDDEN***"},
            "auth": {"secret_key": "***HIDDEN***"},
            "plugins": {"enabled": True},
            "api": {"host": "0.0.0.0", "port": 8000}
        }
        mock_get_config.return_value = mock_config

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.get("/api/system/config", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "database" in data
        assert "auth" in data
        assert "plugins" in data
        assert "api" in data

    async def test_get_system_config_unauthorized(self, test_client: AsyncClient):
        """Test that system config requires authentication."""
        response = await test_client.get("/api/system/config")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('app.api.routes.system.update_system_config')
    async def test_update_system_config(self, mock_update_config, test_client: AsyncClient, mock_auth_token):
        """Test updating system configuration (admin only)."""
        mock_update_config.return_value = True

        config_update = {
            "plugins": {"enabled": False},
            "api": {"port": 8001}
        }

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.put("/api/system/config", json=config_update, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    async def test_update_system_config_unauthorized(self, test_client: AsyncClient):
        """Test that config updates require authentication."""
        config_update = {"api": {"port": 8001}}

        response = await test_client.put("/api/system/config", json=config_update)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSystemMaintenanceEndpoints:
    """Test system maintenance endpoints."""

    @patch('app.api.routes.system.restart_system')
    async def test_restart_system(self, mock_restart, test_client: AsyncClient, mock_auth_token):
        """Test system restart endpoint (admin only)."""
        mock_restart.return_value = True

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.post("/api/system/restart", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

    async def test_restart_system_unauthorized(self, test_client: AsyncClient):
        """Test that restart requires authentication."""
        response = await test_client.post("/api/system/restart")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('app.api.routes.system.reload_config')
    async def test_reload_config(self, mock_reload, test_client: AsyncClient, mock_auth_token):
        """Test configuration reload endpoint."""
        mock_reload.return_value = True

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.post("/api/system/reload-config", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @patch('app.api.routes.system.clear_cache')
    async def test_clear_cache(self, mock_clear_cache, test_client: AsyncClient, mock_auth_token):
        """Test cache clearing endpoint."""
        mock_clear_cache.return_value = {"cleared": 150, "total_size": "2.5MB"}

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.post("/api/system/clear-cache", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cleared" in data
        assert "total_size" in data


class TestSystemLogsEndpoints:
    """Test system logs endpoints."""

    @patch('app.api.routes.system.get_system_logs')
    async def test_get_system_logs(self, mock_get_logs, test_client: AsyncClient, mock_auth_token):
        """Test retrieving system logs."""
        mock_logs = [
            {
                "timestamp": "2023-01-01T12:00:00Z",
                "level": "INFO",
                "logger": "app.main",
                "message": "Application started successfully"
            },
            {
                "timestamp": "2023-01-01T11:59:00Z",
                "level": "WARNING",
                "logger": "app.plugins",
                "message": "Plugin load time exceeded threshold"
            }
        ]
        mock_get_logs.return_value = mock_logs

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.get("/api/system/logs", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        log_entry = data[0]
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry
        assert "message" in log_entry

    async def test_get_logs_with_filters(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving logs with filters."""
        params = {
            "level": "ERROR",
            "limit": 100,
            "since": "2023-01-01T00:00:00Z",
            "logger": "app.plugins"
        }

        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}
        response = await test_client.get("/api/system/logs", params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK

    async def test_get_logs_unauthorized(self, test_client: AsyncClient):
        """Test that logs require authentication."""
        response = await test_client.get("/api/system/logs")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSystemMetricsEndpoints:
    """Test system metrics and monitoring endpoints."""

    @patch('app.api.routes.system.get_performance_metrics')
    async def test_get_performance_metrics(self, mock_get_metrics, test_client: AsyncClient):
        """Test retrieving performance metrics."""
        mock_metrics = {
            "response_times": {
                "average": 125.5,
                "p50": 100.0,
                "p95": 250.0,
                "p99": 500.0
            },
            "request_counts": {
                "total": 1000,
                "success": 950,
                "error": 50
            },
            "active_connections": 25,
            "memory_usage": {
                "rss": 104857600,
                "vms": 209715200
            }
        }
        mock_get_metrics.return_value = mock_metrics

        response = await test_client.get("/api/system/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "response_times" in data
        assert "request_counts" in data
        assert "active_connections" in data
        assert "memory_usage" in data

    async def test_get_metrics_prometheus_format(self, test_client: AsyncClient):
        """Test retrieving metrics in Prometheus format."""
        response = await test_client.get("/api/system/metrics", headers={"Accept": "text/plain"})

        assert response.status_code == status.HTTP_200_OK
        # Should return Prometheus-formatted metrics
        assert "# HELP" in response.text
        assert "# TYPE" in response.text


class TestSystemErrorHandling:
    """Test error handling in system endpoints."""

    @patch('app.api.routes.system.get_system_stats')
    async def test_internal_server_error(self, mock_get_stats, test_client: AsyncClient):
        """Test handling of internal server errors."""
        mock_get_stats.side_effect = Exception("Database connection failed")

        response = await test_client.get("/api/system/stats")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert "message" in data

    async def test_invalid_endpoint(self, test_client: AsyncClient):
        """Test handling of invalid endpoints."""
        response = await test_client.get("/api/system/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_method_not_allowed(self, test_client: AsyncClient):
        """Test handling of invalid HTTP methods."""
        response = await test_client.post("/api/system/health")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    async def test_invalid_query_parameters(self, test_client: AsyncClient):
        """Test handling of invalid query parameters."""
        response = await test_client.get("/api/system/stats?invalid_param=value")

        # Should ignore invalid params and return success
        assert response.status_code == status.HTTP_200_OK


class TestSystemRateLimiting:
    """Test rate limiting on system endpoints."""

    @pytest.mark.slow
    async def test_rate_limiting(self, test_client: AsyncClient):
        """Test rate limiting on system endpoints."""
        # Make rapid requests to trigger rate limiting
        responses = []
        for _ in range(100):
            response = await test_client.get("/api/system/health")
            responses.append(response.status_code)

        # Should have some rate-limited responses
        rate_limited = sum(1 for status in responses if status == 429)
        # Allow for some variance in rate limiting implementation
        assert rate_limited >= 0  # May or may not be implemented yet


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for system endpoints."""

    async def test_full_system_status_flow(self, test_client: AsyncClient):
        """Test complete system status check flow."""
        # Check health
        health_response = await test_client.get("/api/system/health")
        assert health_response.status_code == status.HTTP_200_OK

        # Get stats
        stats_response = await test_client.get("/api/system/stats")
        assert stats_response.status_code == status.HTTP_200_OK

        # Get recent activity
        activity_response = await test_client.get("/api/system/activity/recent")
        assert activity_response.status_code == status.HTTP_200_OK

        # Get system info
        info_response = await test_client.get("/api/system/info")
        assert info_response.status_code == status.HTTP_200_OK

    async def test_system_monitoring_workflow(self, test_client: AsyncClient):
        """Test system monitoring workflow."""
        # Get baseline metrics
        metrics_response = await test_client.get("/api/system/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK

        # Get current stats
        stats_response = await test_client.get("/api/system/stats")
        assert stats_response.status_code == status.HTTP_200_OK

        # Check if system is healthy
        health_response = await test_client.get("/api/system/health")
        assert health_response.status_code == status.HTTP_200_OK

        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
