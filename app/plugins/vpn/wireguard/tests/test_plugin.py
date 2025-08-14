#!/usr/bin/env python3
"""
WireGuard Plugin tests for Firewallo UI.

Tests the WireGuard VPN plugin functionality including:
- Plugin initialization and lifecycle
- Server management operations
- Client management operations
- Configuration generation
- Health monitoring
- API endpoints
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, List, Any

# Test markers
pytestmark = [pytest.mark.plugins, pytest.mark.unit, pytest.mark.asyncio]


class TestWireGuardPluginInitialization:
    """Test WireGuard plugin initialization and lifecycle."""

    def test_plugin_manifest_valid(self):
        """Test that plugin manifest is valid."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        manifest = plugin.get_manifest()

        assert manifest["name"] == "wireguard"
        assert manifest["category"] == "vpn"
        assert "version" in manifest
        assert "description" in manifest
        assert "api_version" in manifest
        assert isinstance(manifest["permissions"], list)

    async def test_plugin_initialization(self):
        """Test plugin initialization."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        with patch('app.plugins.vpn.wireguard.services.WireGuardService') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service.return_value = mock_service_instance

            await plugin.initialize()

            assert plugin.initialized is True
            mock_service_instance.initialize.assert_called_once()

    async def test_plugin_shutdown(self):
        """Test plugin shutdown."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        plugin.initialized = True

        with patch('app.plugins.vpn.wireguard.services.WireGuardService') as mock_service:
            mock_service_instance = AsyncMock()
            plugin.service = mock_service_instance

            await plugin.shutdown()

            assert plugin.initialized is False
            mock_service_instance.shutdown.assert_called_once()

    def test_plugin_info(self):
        """Test plugin information retrieval."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        info = plugin.get_info()

        assert info["name"] == "wireguard"
        assert info["category"] == "vpn"
        assert "version" in info
        assert "api_prefix" in info
        assert "endpoints" in info

    def test_plugin_health_status(self):
        """Test plugin health status."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        with patch.object(plugin, '_check_wireguard_binary') as mock_check:
            mock_check.return_value = True

            health = plugin.get_health_status()

            assert "status" in health
            assert health["status"] in ["healthy", "degraded", "unhealthy"]
            assert "last_check" in health

    def test_plugin_database_schema(self):
        """Test plugin database schema."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        schema = plugin.get_database_schema()

        assert "servers" in schema
        assert "clients" in schema

        # Check server table schema
        server_schema = schema["servers"]
        required_fields = ["id", "name", "public_key", "private_key", "endpoint", "port"]
        for field in required_fields:
            assert field in server_schema["fields"]

        # Check client table schema
        client_schema = schema["clients"]
        required_fields = ["id", "name", "public_key", "private_key", "server_id", "allocated_ip"]
        for field in required_fields:
            assert field in client_schema["fields"]


class TestWireGuardServerOperations:
    """Test WireGuard server management operations."""

    async def test_create_server_success(self):
        """Test successful server creation."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.categories.vpn import VPNServerCreate

        plugin = WireGuardPlugin()

        server_data = VPNServerCreate(
            name="test-server",
            endpoint="192.168.1.100",
            port=51820,
            network="10.0.0.0/24",
            dns_servers=["8.8.8.8", "8.8.4.4"],
            allowed_ips=["0.0.0.0/0"],
            mtu=1420,
            keep_alive=25,
            enabled=True,
            description="Test server"
        )

        mock_server = {
            "id": "srv-123",
            "name": "test-server",
            "public_key": "test-public-key",
            "private_key": "test-private-key",
            "endpoint": "192.168.1.100",
            "port": 51820,
            "network": "10.0.0.0/24",
            "enabled": True
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.create_server = AsyncMock(return_value=mock_server)

            result = await plugin.create_server(server_data)

            assert result is not None
            assert result["name"] == "test-server"
            assert result["port"] == 51820
            assert "public_key" in result

    async def test_create_server_invalid_data(self):
        """Test server creation with invalid data."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.categories.vpn import VPNServerCreate

        plugin = WireGuardPlugin()

        # Invalid port number
        with pytest.raises(ValueError):
            server_data = VPNServerCreate(
                name="test-server",
                endpoint="192.168.1.100",
                port=70000,  # Invalid port
                network="10.0.0.0/24"
            )

    async def test_get_server_success(self):
        """Test successful server retrieval."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        mock_server = {
            "id": server_id,
            "name": "test-server",
            "public_key": "test-public-key",
            "endpoint": "192.168.1.100",
            "port": 51820
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_server = AsyncMock(return_value=mock_server)

            result = await plugin.get_server(server_id)

            assert result is not None
            assert result["id"] == server_id
            assert result["name"] == "test-server"

    async def test_get_server_not_found(self):
        """Test server retrieval for non-existent server."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_server = AsyncMock(return_value=None)

            result = await plugin.get_server("nonexistent")

            assert result is None

    async def test_list_servers(self):
        """Test listing all servers."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        mock_servers = [
            {"id": "srv-1", "name": "server-1", "port": 51820},
            {"id": "srv-2", "name": "server-2", "port": 51821}
        ]

        with patch.object(plugin, 'service') as mock_service:
            mock_service.list_servers = AsyncMock(return_value=mock_servers)

            result = await plugin.list_servers()

            assert len(result) == 2
            assert result[0]["name"] == "server-1"
            assert result[1]["name"] == "server-2"

    async def test_update_server(self):
        """Test server update."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        update_data = {
            "name": "updated-server",
            "description": "Updated description"
        }

        mock_updated_server = {
            "id": server_id,
            "name": "updated-server",
            "description": "Updated description",
            "port": 51820
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.update_server = AsyncMock(return_value=mock_updated_server)

            result = await plugin.update_server(server_id, update_data)

            assert result is not None
            assert result["name"] == "updated-server"
            assert result["description"] == "Updated description"

    async def test_delete_server(self):
        """Test server deletion."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        with patch.object(plugin, 'service') as mock_service:
            mock_service.delete_server = AsyncMock(return_value=True)

            result = await plugin.delete_server(server_id)

            assert result is True

    async def test_start_server(self):
        """Test server startup."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        with patch.object(plugin, 'service') as mock_service:
            mock_service.start_server = AsyncMock(return_value=True)

            result = await plugin.start_server(server_id)

            assert result is True

    async def test_stop_server(self):
        """Test server shutdown."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        with patch.object(plugin, 'service') as mock_service:
            mock_service.stop_server = AsyncMock(return_value=True)

            result = await plugin.stop_server(server_id)

            assert result is True


class TestWireGuardClientOperations:
    """Test WireGuard client management operations."""

    async def test_create_client_success(self):
        """Test successful client creation."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.categories.vpn import VPNClientCreate

        plugin = WireGuardPlugin()

        client_data = VPNClientCreate(
            name="test-client",
            server_id="srv-123",
            email="test@example.com",
            allowed_ips=["0.0.0.0/0"],
            dns_servers=["8.8.8.8"],
            persistent_keepalive=25,
            enabled=True,
            description="Test client"
        )

        mock_client = {
            "id": "client-456",
            "name": "test-client",
            "server_id": "srv-123",
            "public_key": "client-public-key",
            "private_key": "client-private-key",
            "allocated_ip": "10.0.0.5",
            "enabled": True
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.create_client = AsyncMock(return_value=mock_client)

            result = await plugin.create_client(client_data)

            assert result is not None
            assert result["name"] == "test-client"
            assert result["server_id"] == "srv-123"
            assert "allocated_ip" in result

    async def test_get_client_success(self):
        """Test successful client retrieval."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        client_id = "client-456"

        mock_client = {
            "id": client_id,
            "name": "test-client",
            "server_id": "srv-123",
            "allocated_ip": "10.0.0.5"
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_client = AsyncMock(return_value=mock_client)

            result = await plugin.get_client(client_id)

            assert result is not None
            assert result["id"] == client_id
            assert result["name"] == "test-client"

    async def test_list_clients(self):
        """Test listing clients."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        mock_clients = [
            {"id": "client-1", "name": "client-1", "server_id": server_id},
            {"id": "client-2", "name": "client-2", "server_id": server_id}
        ]

        with patch.object(plugin, 'service') as mock_service:
            mock_service.list_clients = AsyncMock(return_value=mock_clients)

            result = await plugin.list_clients(server_id=server_id)

            assert len(result) == 2
            assert all(client["server_id"] == server_id for client in result)

    async def test_update_client(self):
        """Test client update."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        client_id = "client-456"

        update_data = {
            "name": "updated-client",
            "enabled": False
        }

        mock_updated_client = {
            "id": client_id,
            "name": "updated-client",
            "enabled": False,
            "server_id": "srv-123"
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.update_client = AsyncMock(return_value=mock_updated_client)

            result = await plugin.update_client(client_id, update_data)

            assert result is not None
            assert result["name"] == "updated-client"
            assert result["enabled"] is False

    async def test_delete_client(self):
        """Test client deletion."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        client_id = "client-456"

        with patch.object(plugin, 'service') as mock_service:
            mock_service.delete_client = AsyncMock(return_value=True)

            result = await plugin.delete_client(client_id)

            assert result is True


class TestWireGuardConfigurationGeneration:
    """Test WireGuard configuration generation."""

    async def test_generate_config_success(self):
        """Test successful configuration generation."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        client_id = "client-456"

        mock_config = {
            "config_content": """[Interface]
PrivateKey = client-private-key
Address = 10.0.0.5/24
DNS = 8.8.8.8

[Peer]
PublicKey = server-public-key
Endpoint = 192.168.1.100:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25""",
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "filename": "test-client.conf"
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.generate_config = AsyncMock(return_value=mock_config)

            result = await plugin.generate_config(client_id)

            assert result is not None
            assert "config_content" in result
            assert "[Interface]" in result["config_content"]
            assert "[Peer]" in result["config_content"]
            assert "qr_code" in result

    async def test_generate_config_client_not_found(self):
        """Test configuration generation for non-existent client."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        with patch.object(plugin, 'service') as mock_service:
            mock_service.generate_config = AsyncMock(return_value=None)

            result = await plugin.generate_config("nonexistent")

            assert result is None

    async def test_validate_config(self):
        """Test configuration validation."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        valid_config = """[Interface]
PrivateKey = test-private-key
Address = 10.0.0.5/24

[Peer]
PublicKey = test-public-key
Endpoint = 192.168.1.100:51820
AllowedIPs = 0.0.0.0/0"""

        with patch.object(plugin, 'service') as mock_service:
            mock_service.validate_config = MagicMock(return_value=True)

            result = plugin.validate_config(valid_config)

            assert result is True

    async def test_export_server_config(self):
        """Test server configuration export."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        mock_server_config = {
            "config_content": """[Interface]
PrivateKey = server-private-key
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
# Client 1
PublicKey = client1-public-key
AllowedIPs = 10.0.0.5/32

[Peer]
# Client 2
PublicKey = client2-public-key
AllowedIPs = 10.0.0.6/32""",
            "filename": "wg0.conf"
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.export_server_config = AsyncMock(return_value=mock_server_config)

            result = await plugin.export_server_config(server_id)

            assert result is not None
            assert "config_content" in result
            assert "ListenPort = 51820" in result["config_content"]


class TestWireGuardAPIEndpoints:
    """Test WireGuard API endpoints."""

    def test_get_api_routes(self):
        """Test API route registration."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        routes = plugin.get_api_routes()

        assert isinstance(routes, list)
        assert len(routes) > 0

        # Check for expected route patterns
        route_paths = [route.get("path", "") for route in routes]
        assert any("/servers" in path for path in route_paths)
        assert any("/clients" in path for path in route_paths)
        assert any("/config" in path for path in route_paths)

    async def test_handle_api_request_servers(self):
        """Test API request handling for servers endpoint."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        mock_servers = [
            {"id": "srv-1", "name": "server-1"},
            {"id": "srv-2", "name": "server-2"}
        ]

        with patch.object(plugin, 'list_servers') as mock_list:
            mock_list.return_value = mock_servers

            result = await plugin.handle_api_request("GET", "/servers", {})

            assert result["status_code"] == 200
            assert result["data"] == mock_servers

    async def test_handle_api_request_create_server(self):
        """Test API request handling for server creation."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        request_data = {
            "name": "new-server",
            "endpoint": "192.168.1.100",
            "port": 51820,
            "network": "10.0.0.0/24"
        }

        mock_server = {
            "id": "srv-new",
            "name": "new-server",
            "port": 51820
        }

        with patch.object(plugin, 'create_server') as mock_create:
            mock_create.return_value = mock_server

            result = await plugin.handle_api_request("POST", "/servers", request_data)

            assert result["status_code"] == 201
            assert result["data"]["name"] == "new-server"

    async def test_handle_api_request_invalid_endpoint(self):
        """Test API request handling for invalid endpoint."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        result = await plugin.handle_api_request("GET", "/invalid", {})

        assert result["status_code"] == 404
        assert "error" in result


class TestWireGuardMonitoring:
    """Test WireGuard monitoring and metrics."""

    def test_get_metrics(self):
        """Test metrics collection."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        mock_metrics = {
            "servers": {
                "total": 2,
                "active": 1,
                "inactive": 1
            },
            "clients": {
                "total": 10,
                "connected": 7,
                "disconnected": 3
            },
            "traffic": {
                "bytes_sent": 1048576,
                "bytes_received": 2097152,
                "packets_sent": 1000,
                "packets_received": 2000
            }
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_metrics = MagicMock(return_value=mock_metrics)

            result = plugin.get_metrics()

            assert "servers" in result
            assert "clients" in result
            assert "traffic" in result
            assert result["servers"]["total"] == 2

    async def test_get_server_status(self):
        """Test server status monitoring."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        server_id = "srv-123"

        mock_status = {
            "id": server_id,
            "status": "active",
            "uptime": 86400,
            "connected_clients": 5,
            "total_clients": 8,
            "traffic": {
                "bytes_sent": 524288,
                "bytes_received": 1048576
            }
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_server_status = AsyncMock(return_value=mock_status)

            result = await plugin.get_server_status(server_id)

            assert result["status"] == "active"
            assert result["connected_clients"] == 5

    async def test_get_client_status(self):
        """Test client status monitoring."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()
        client_id = "client-456"

        mock_status = {
            "id": client_id,
            "status": "connected",
            "last_handshake": "2023-01-01T12:00:00Z",
            "endpoint": "192.168.1.200:54321",
            "traffic": {
                "bytes_sent": 102400,
                "bytes_received": 204800
            }
        }

        with patch.object(plugin, 'service') as mock_service:
            mock_service.get_client_status = AsyncMock(return_value=mock_status)

            result = await plugin.get_client_status(client_id)

            assert result["status"] == "connected"
            assert "last_handshake" in result


@pytest.mark.integration
class TestWireGuardPluginIntegration:
    """Integration tests for WireGuard plugin."""

    async def test_complete_server_client_workflow(self):
        """Test complete server and client workflow."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin
        from app.plugins.categories.vpn import VPNServerCreate, VPNClientCreate

        plugin = WireGuardPlugin()

        # Mock service
        mock_service = AsyncMock()
        plugin.service = mock_service

        # Create server
        server_data = VPNServerCreate(
            name="integration-server",
            endpoint="192.168.1.100",
            port=51820,
            network="10.0.0.0/24"
        )

        mock_server = {
            "id": "srv-integration",
            "name": "integration-server",
            "port": 51820,
            "public_key": "server-key"
        }

        mock_service.create_server.return_value = mock_server
        server = await plugin.create_server(server_data)

        assert server["name"] == "integration-server"

        # Create client for the server
        client_data = VPNClientCreate(
            name="integration-client",
            server_id=server["id"],
            email="test@example.com"
        )

        mock_client = {
            "id": "client-integration",
            "name": "integration-client",
            "server_id": server["id"],
            "allocated_ip": "10.0.0.5"
        }

        mock_service.create_client.return_value = mock_client
        client = await plugin.create_client(client_data)

        assert client["server_id"] == server["id"]

        # Generate configuration
        mock_config = {
            "config_content": "[Interface]\nPrivateKey = test\n[Peer]\nPublicKey = test",
            "qr_code": "mock-qr-code"
        }

        mock_service.generate_config.return_value = mock_config
        config = await plugin.generate_config(client["id"])

        assert "[Interface]" in config["config_content"]
        assert "[Peer]" in config["config_content"]

    async def test_plugin_error_recovery(self):
        """Test plugin error handling and recovery."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        # Test service failure during initialization
        with patch('app.plugins.vpn.wireguard.services.WireGuardService') as mock_service_class:
            mock_service_class.side_effect = Exception("Service initialization failed")

            with pytest.raises(Exception):
                await plugin.initialize()

            # Plugin should remain in uninitialized state
            assert not plugin.initialized

    async def test_plugin_configuration_management(self):
        """Test plugin configuration management."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        plugin = WireGuardPlugin()

        # Get default configuration
        default_config = plugin.get_default_config()

        assert "port_range" in default_config
        assert "max_clients" in default_config
        assert "auto_start" in default_config

        # Update configuration
        new_config = {
            "max_clients": 200,
            "auto_start": False
        }

        result = plugin.update_config(new_config)
        assert result is True

        # Verify configuration was updated
        current_config = plugin.get_config()
        assert current_config["max_clients"] == 200
        assert current_config["auto_start"] is False
