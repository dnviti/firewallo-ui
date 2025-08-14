#!/usr/bin/env python3
"""
Plugin API endpoint tests for Firewallo UI.

Tests the plugin-related API endpoints including:
- Plugin discovery and listing
- Plugin loading/unloading
- Plugin configuration
- Plugin status monitoring
- Plugin API routing
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import status

# Test markers
pytestmark = [pytest.mark.api, pytest.mark.plugins, pytest.mark.asyncio]


class TestPluginDiscoveryEndpoints:
    """Test plugin discovery and listing endpoints."""

    async def test_list_all_plugins(self, test_client: AsyncClient):
        """Test retrieving all available plugins."""
        mock_plugins = [
            {
                "id": "vpn.wireguard",
                "name": "WireGuard VPN",
                "category": "vpn",
                "version": "1.0.0",
                "status": "loaded",
                "enabled": True,
                "description": "WireGuard VPN server management"
            },
            {
                "id": "system.webui",
                "name": "Web UI",
                "category": "system",
                "version": "1.0.0",
                "status": "loaded",
                "enabled": True,
                "description": "Web-based user interface"
            }
        ]

        with patch('app.plugins.plugin_manager.list_plugins') as mock_list:
            mock_list.return_value = mock_plugins

            response = await test_client.get("/api/plugins/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        # Check plugin structure
        plugin = data[0]
        assert "id" in plugin
        assert "name" in plugin
        assert "category" in plugin
        assert "version" in plugin
        assert "status" in plugin
        assert "enabled" in plugin

    async def test_list_plugins_by_category(self, test_client: AsyncClient):
        """Test retrieving plugins filtered by category."""
        mock_vpn_plugins = [
            {
                "id": "vpn.wireguard",
                "name": "WireGuard VPN",
                "category": "vpn",
                "version": "1.0.0",
                "status": "loaded",
                "enabled": True
            }
        ]

        with patch('app.plugins.plugin_manager.list_plugins') as mock_list:
            mock_list.return_value = mock_vpn_plugins

            response = await test_client.get("/api/plugins/?category=vpn")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["category"] == "vpn"

    async def test_list_plugins_by_status(self, test_client: AsyncClient):
        """Test retrieving plugins filtered by status."""
        mock_loaded_plugins = [
            {
                "id": "vpn.wireguard",
                "name": "WireGuard VPN",
                "category": "vpn",
                "status": "loaded",
                "enabled": True
            }
        ]

        with patch('app.plugins.plugin_manager.list_plugins') as mock_list:
            mock_list.return_value = mock_loaded_plugins

            response = await test_client.get("/api/plugins/?status=loaded")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        for plugin in data:
            assert plugin["status"] == "loaded"

    async def test_discover_plugins(self, test_client: AsyncClient, mock_auth_token):
        """Test plugin discovery endpoint."""
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        mock_discovered = ["vpn.wireguard", "system.webui", "vpn.openvpn"]

        with patch('app.plugins.plugin_manager.discover_plugins') as mock_discover:
            mock_discover.return_value = mock_discovered

            response = await test_client.post("/api/plugins/discover", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "discovered" in data
        assert len(data["discovered"]) == 3
        assert "vpn.wireguard" in data["discovered"]

    async def test_discover_plugins_unauthorized(self, test_client: AsyncClient):
        """Test that plugin discovery requires authentication."""
        response = await test_client.post("/api/plugins/discover")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPluginDetailsEndpoints:
    """Test plugin detail retrieval endpoints."""

    async def test_get_plugin_details(self, test_client: AsyncClient):
        """Test retrieving details for a specific plugin."""
        plugin_id = "vpn.wireguard"
        mock_plugin_details = {
            "id": plugin_id,
            "name": "WireGuard VPN",
            "category": "vpn",
            "version": "1.0.0",
            "description": "WireGuard VPN server management plugin",
            "author": "Firewallo Team",
            "status": "loaded",
            "enabled": True,
            "api_version": "1.0",
            "dependencies": [],
            "permissions": ["network", "filesystem"],
            "endpoints": [
                {"path": "/servers", "method": "GET"},
                {"path": "/servers", "method": "POST"},
                {"path": "/clients", "method": "GET"}
            ],
            "configuration": {
                "auto_start": True,
                "max_clients": 100,
                "port_range": "51820-51830"
            }
        }

        with patch('app.plugins.plugin_manager.get_plugin_info') as mock_get_info:
            mock_get_info.return_value = mock_plugin_details

            response = await test_client.get(f"/api/plugins/{plugin_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == plugin_id
        assert "name" in data
        assert "description" in data
        assert "version" in data
        assert "endpoints" in data
        assert "configuration" in data

    async def test_get_plugin_not_found(self, test_client: AsyncClient):
        """Test retrieving details for non-existent plugin."""
        plugin_id = "nonexistent.plugin"

        with patch('app.plugins.plugin_manager.get_plugin_info') as mock_get_info:
            mock_get_info.return_value = None

            response = await test_client.get(f"/api/plugins/{plugin_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_get_plugin_manifest(self, test_client: AsyncClient):
        """Test retrieving plugin manifest."""
        plugin_id = "vpn.wireguard"
        mock_manifest = {
            "name": "wireguard",
            "version": "1.0.0",
            "description": "WireGuard VPN plugin",
            "author": "Firewallo Team",
            "category": "vpn",
            "api_version": "1.0",
            "dependencies": [],
            "permissions": ["network", "filesystem"],
            "endpoints": [],
            "database_schema": {
                "tables": ["servers", "clients"]
            }
        }

        with patch('app.plugins.plugin_manager.get_plugin_manifest') as mock_get_manifest:
            mock_get_manifest.return_value = mock_manifest

            response = await test_client.get(f"/api/plugins/{plugin_id}/manifest")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "wireguard"
        assert data["category"] == "vpn"
        assert "permissions" in data
        assert "database_schema" in data

    async def test_get_plugin_health(self, test_client: AsyncClient):
        """Test retrieving plugin health status."""
        plugin_id = "vpn.wireguard"
        mock_health = {
            "status": "healthy",
            "last_check": "2023-01-01T12:00:00Z",
            "uptime": 86400,
            "errors": [],
            "warnings": [],
            "metrics": {
                "memory_usage": 1048576,
                "cpu_usage": 2.5,
                "active_connections": 25
            }
        }

        with patch('app.plugins.plugin_manager.get_plugin_health') as mock_get_health:
            mock_get_health.return_value = mock_health

            response = await test_client.get(f"/api/plugins/{plugin_id}/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert "metrics" in data
        assert "uptime" in data


class TestPluginManagementEndpoints:
    """Test plugin management operations."""

    async def test_load_plugin_success(self, test_client: AsyncClient, mock_auth_token):
        """Test successful plugin loading."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.load_plugin') as mock_load:
            mock_load.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/load", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Plugin {plugin_id} loaded successfully"

    async def test_load_plugin_failure(self, test_client: AsyncClient, mock_auth_token):
        """Test plugin loading failure."""
        plugin_id = "invalid.plugin"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.load_plugin') as mock_load:
            mock_load.return_value = False

            response = await test_client.post(f"/api/plugins/{plugin_id}/load", headers=headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "failed to load" in data["error"].lower()

    async def test_unload_plugin_success(self, test_client: AsyncClient, mock_auth_token):
        """Test successful plugin unloading."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.unload_plugin') as mock_unload:
            mock_unload.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/unload", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Plugin {plugin_id} unloaded successfully"

    async def test_enable_plugin(self, test_client: AsyncClient, mock_auth_token):
        """Test enabling a plugin."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.enable_plugin') as mock_enable:
            mock_enable.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/enable", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Plugin {plugin_id} enabled successfully"

    async def test_disable_plugin(self, test_client: AsyncClient, mock_auth_token):
        """Test disabling a plugin."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.disable_plugin') as mock_disable:
            mock_disable.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/disable", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Plugin {plugin_id} disabled successfully"

    async def test_restart_plugin(self, test_client: AsyncClient, mock_auth_token):
        """Test restarting a plugin."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.restart_plugin') as mock_restart:
            mock_restart.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/restart", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == f"Plugin {plugin_id} restarted successfully"

    async def test_plugin_management_unauthorized(self, test_client: AsyncClient):
        """Test that plugin management requires authentication."""
        plugin_id = "vpn.wireguard"

        response = await test_client.post(f"/api/plugins/{plugin_id}/load")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await test_client.post(f"/api/plugins/{plugin_id}/unload")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await test_client.post(f"/api/plugins/{plugin_id}/enable")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPluginConfigurationEndpoints:
    """Test plugin configuration endpoints."""

    async def test_get_plugin_config(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving plugin configuration."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        mock_config = {
            "auto_start": True,
            "max_clients": 100,
            "port_range": "51820-51830",
            "encryption": "ChaCha20Poly1305",
            "keep_alive": 25
        }

        with patch('app.plugins.plugin_manager.get_plugin_config') as mock_get_config:
            mock_get_config.return_value = mock_config

            response = await test_client.get(f"/api/plugins/{plugin_id}/config", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["auto_start"] is True
        assert data["max_clients"] == 100
        assert "port_range" in data

    async def test_update_plugin_config(self, test_client: AsyncClient, mock_auth_token):
        """Test updating plugin configuration."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        config_update = {
            "max_clients": 150,
            "port_range": "51820-51840",
            "auto_start": False
        }

        with patch('app.plugins.plugin_manager.update_plugin_config') as mock_update:
            mock_update.return_value = True

            response = await test_client.put(f"/api/plugins/{plugin_id}/config",
                                           json=config_update, headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Plugin configuration updated successfully"

    async def test_reset_plugin_config(self, test_client: AsyncClient, mock_auth_token):
        """Test resetting plugin configuration to defaults."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.reset_plugin_config') as mock_reset:
            mock_reset.return_value = True

            response = await test_client.post(f"/api/plugins/{plugin_id}/config/reset",
                                            headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "reset to defaults" in data["message"].lower()

    async def test_get_plugin_config_schema(self, test_client: AsyncClient):
        """Test retrieving plugin configuration schema."""
        plugin_id = "vpn.wireguard"

        mock_schema = {
            "type": "object",
            "properties": {
                "auto_start": {
                    "type": "boolean",
                    "description": "Automatically start on system boot",
                    "default": True
                },
                "max_clients": {
                    "type": "integer",
                    "description": "Maximum number of concurrent clients",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100
                },
                "port_range": {
                    "type": "string",
                    "description": "Port range for VPN servers",
                    "pattern": "^\\d+-\\d+$",
                    "default": "51820-51830"
                }
            },
            "required": ["max_clients"]
        }

        with patch('app.plugins.plugin_manager.get_plugin_config_schema') as mock_get_schema:
            mock_get_schema.return_value = mock_schema

            response = await test_client.get(f"/api/plugins/{plugin_id}/config/schema")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["type"] == "object"
        assert "properties" in data
        assert "auto_start" in data["properties"]
        assert "max_clients" in data["properties"]


class TestPluginLogsEndpoints:
    """Test plugin logging endpoints."""

    async def test_get_plugin_logs(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving plugin logs."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        mock_logs = [
            {
                "timestamp": "2023-01-01T12:00:00Z",
                "level": "INFO",
                "message": "WireGuard server started successfully",
                "context": {"server_id": "srv-1"}
            },
            {
                "timestamp": "2023-01-01T11:59:00Z",
                "level": "DEBUG",
                "message": "Client connection established",
                "context": {"client_id": "client-1", "ip": "10.0.0.5"}
            }
        ]

        with patch('app.plugins.plugin_manager.get_plugin_logs') as mock_get_logs:
            mock_get_logs.return_value = mock_logs

            response = await test_client.get(f"/api/plugins/{plugin_id}/logs", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        log_entry = data[0]
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "message" in log_entry

    async def test_get_plugin_logs_with_filters(self, test_client: AsyncClient, mock_auth_token):
        """Test retrieving plugin logs with filters."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        params = {
            "level": "ERROR",
            "limit": 50,
            "since": "2023-01-01T00:00:00Z"
        }

        with patch('app.plugins.plugin_manager.get_plugin_logs') as mock_get_logs:
            mock_get_logs.return_value = []

            response = await test_client.get(f"/api/plugins/{plugin_id}/logs",
                                           params=params, headers=headers)

        assert response.status_code == status.HTTP_200_OK

    async def test_clear_plugin_logs(self, test_client: AsyncClient, mock_auth_token):
        """Test clearing plugin logs."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        with patch('app.plugins.plugin_manager.clear_plugin_logs') as mock_clear:
            mock_clear.return_value = {"cleared": 150}

            response = await test_client.delete(f"/api/plugins/{plugin_id}/logs",
                                              headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cleared" in data


class TestPluginMetricsEndpoints:
    """Test plugin metrics endpoints."""

    async def test_get_plugin_metrics(self, test_client: AsyncClient):
        """Test retrieving plugin metrics."""
        plugin_id = "vpn.wireguard"

        mock_metrics = {
            "performance": {
                "cpu_usage": 2.5,
                "memory_usage": 1048576,
                "disk_usage": 10485760
            },
            "counters": {
                "total_connections": 1000,
                "active_connections": 25,
                "failed_connections": 5
            },
            "gauges": {
                "avg_response_time": 125.5,
                "throughput_mbps": 50.2
            },
            "timestamps": {
                "last_updated": "2023-01-01T12:00:00Z",
                "started_at": "2023-01-01T00:00:00Z"
            }
        }

        with patch('app.plugins.plugin_manager.get_plugin_metrics') as mock_get_metrics:
            mock_get_metrics.return_value = mock_metrics

            response = await test_client.get(f"/api/plugins/{plugin_id}/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "performance" in data
        assert "counters" in data
        assert "gauges" in data

    async def test_get_plugin_metrics_history(self, test_client: AsyncClient):
        """Test retrieving plugin metrics history."""
        plugin_id = "vpn.wireguard"

        params = {
            "metric": "cpu_usage",
            "duration": "1h",
            "resolution": "1m"
        }

        mock_history = {
            "metric": "cpu_usage",
            "duration": "1h",
            "resolution": "1m",
            "data_points": [
                {"timestamp": "2023-01-01T12:00:00Z", "value": 2.5},
                {"timestamp": "2023-01-01T12:01:00Z", "value": 2.8},
                {"timestamp": "2023-01-01T12:02:00Z", "value": 2.2}
            ]
        }

        with patch('app.plugins.plugin_manager.get_plugin_metrics_history') as mock_get_history:
            mock_get_history.return_value = mock_history

            response = await test_client.get(f"/api/plugins/{plugin_id}/metrics/history",
                                           params=params)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["metric"] == "cpu_usage"
        assert "data_points" in data
        assert len(data["data_points"]) == 3


class TestPluginAPIRouting:
    """Test plugin API routing and proxying."""

    async def test_plugin_api_proxy(self, test_client: AsyncClient, mock_auth_token):
        """Test proxying requests to plugin API endpoints."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        mock_response = {
            "servers": [
                {"id": "srv-1", "name": "Main Server", "status": "active"},
                {"id": "srv-2", "name": "Backup Server", "status": "inactive"}
            ]
        }

        with patch('app.plugins.plugin_manager.call_plugin_endpoint') as mock_call:
            mock_call.return_value = mock_response

            response = await test_client.get(f"/api/plugins/{plugin_id}/api/servers",
                                           headers=headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "servers" in data
        assert len(data["servers"]) == 2

    async def test_plugin_api_post_request(self, test_client: AsyncClient, mock_auth_token):
        """Test POST request to plugin API."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        request_data = {
            "name": "New Server",
            "endpoint": "192.168.1.100",
            "port": 51820
        }

        mock_response = {
            "id": "srv-3",
            "name": "New Server",
            "status": "created"
        }

        with patch('app.plugins.plugin_manager.call_plugin_endpoint') as mock_call:
            mock_call.return_value = mock_response

            response = await test_client.post(f"/api/plugins/{plugin_id}/api/servers",
                                            json=request_data, headers=headers)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Server"

    async def test_plugin_api_unauthorized(self, test_client: AsyncClient):
        """Test that plugin API requires authentication."""
        plugin_id = "vpn.wireguard"

        response = await test_client.get(f"/api/plugins/{plugin_id}/api/servers")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for plugin system."""

    async def test_plugin_lifecycle_integration(self, test_client: AsyncClient, mock_auth_token):
        """Test complete plugin lifecycle."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        # Discover plugins
        with patch('app.plugins.plugin_manager.discover_plugins') as mock_discover:
            mock_discover.return_value = [plugin_id]

            discover_response = await test_client.post("/api/plugins/discover", headers=headers)
            assert discover_response.status_code == status.HTTP_200_OK

        # Load plugin
        with patch('app.plugins.plugin_manager.load_plugin') as mock_load:
            mock_load.return_value = True

            load_response = await test_client.post(f"/api/plugins/{plugin_id}/load",
                                                 headers=headers)
            assert load_response.status_code == status.HTTP_200_OK

        # Enable plugin
        with patch('app.plugins.plugin_manager.enable_plugin') as mock_enable:
            mock_enable.return_value = True

            enable_response = await test_client.post(f"/api/plugins/{plugin_id}/enable",
                                                   headers=headers)
            assert enable_response.status_code == status.HTTP_200_OK

        # Get plugin details
        with patch('app.plugins.plugin_manager.get_plugin_info') as mock_get_info:
            mock_get_info.return_value = {"id": plugin_id, "status": "loaded", "enabled": True}

            details_response = await test_client.get(f"/api/plugins/{plugin_id}")
            assert details_response.status_code == status.HTTP_200_OK

        # Check health
        with patch('app.plugins.plugin_manager.get_plugin_health') as mock_health:
            mock_health.return_value = {"status": "healthy"}

            health_response = await test_client.get(f"/api/plugins/{plugin_id}/health")
            assert health_response.status_code == status.HTTP_200_OK

        # Disable plugin
        with patch('app.plugins.plugin_manager.disable_plugin') as mock_disable:
            mock_disable.return_value = True

            disable_response = await test_client.post(f"/api/plugins/{plugin_id}/disable",
                                                    headers=headers)
            assert disable_response.status_code == status.HTTP_200_OK

        # Unload plugin
        with patch('app.plugins.plugin_manager.unload_plugin') as mock_unload:
            mock_unload.return_value = True

            unload_response = await test_client.post(f"/api/plugins/{plugin_id}/unload",
                                                   headers=headers)
            assert unload_response.status_code == status.HTTP_200_OK

    async def test_plugin_configuration_workflow(self, test_client: AsyncClient, mock_auth_token):
        """Test plugin configuration management workflow."""
        plugin_id = "vpn.wireguard"
        headers = {"Authorization": f"Bearer {mock_auth_token['access_token']}"}

        # Get configuration schema
        mock_schema = {
            "type": "object",
            "properties": {
                "max_clients": {"type": "integer", "default": 100}
            }
        }

        with patch('app.plugins.plugin_manager.get_plugin_config_schema') as mock_schema_fn:
            mock_schema_fn.return_value = mock_schema

            schema_response = await test_client.get(f"/api/plugins/{plugin_id}/config/schema")
            assert schema_response.status_code == status.HTTP_200_OK

        # Get current configuration
        mock_config = {"max_clients": 100, "auto_start": True}

        with patch('app.plugins.plugin_manager.get_plugin_config') as mock_get_config:
            mock_get_config.return_value = mock_config

            config_response = await test_client.get(f"/api/plugins/{plugin_id}/config",
                                                  headers=headers)
            assert config_response.status_code == status.HTTP_200_OK

        # Update configuration
        config_update = {"max_clients": 150}

        with patch('app.plugins.plugin_manager.update_plugin_config') as mock_update:
            mock_update.return_value = True

            update_response = await test_client.put(f"/api/plugins/{plugin_id}/config",
                                                  json=config_update, headers=headers)
            assert update_response.status_code == status.HTTP_200_OK

        # Reset to defaults
        with patch('app.plugins.plugin_manager.reset_plugin_config') as mock_reset:
            mock_reset.return_value = True

            reset_response = await test_client.post(f"/api/plugins/{plugin_id}/config/reset",
                                                  headers=headers)
            assert reset_response.status_code == status.HTTP_200_OK
