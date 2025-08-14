#!/usr/bin/env python3
"""Test script for the Firewallo Plugin Framework.

This script tests the plugin system functionality including:
- Plugin discovery and loading
- WireGuard plugin operations
- API endpoint integration
- Error handling

Run with: python test_plugins.py
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.plugins import plugin_manager
try:
    from app.plugins.categories.vpn import VPNServerCreate, VPNClientCreate
except ImportError:
    # Categories might not be available if no plugins are loaded
    VPNServerCreate = None
    VPNClientCreate = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("plugin_test")


class PluginSystemTest:
    """Test suite for the plugin system."""

    def __init__(self):
        self.test_results = []
        self.test_server_id = None
        self.test_client_id = None

    async def run_all_tests(self):
        """Run all plugin system tests."""
        logger.info("Starting Firewallo Plugin Framework Tests")
        logger.info("=" * 50)

        tests = [
            self.test_plugin_discovery,
            self.test_plugin_loading,
            self.test_wireguard_plugin_basic,
            self.test_wireguard_server_operations,
            self.test_wireguard_client_operations,
            self.test_configuration_generation,
            self.test_plugin_cleanup,
        ]

        for test in tests:
            try:
                await test()
                self.test_results.append((test.__name__, "PASS"))
                logger.info(f"✅ {test.__name__} - PASSED")
            except Exception as e:
                self.test_results.append((test.__name__, f"FAIL: {str(e)}"))
                logger.error(f"❌ {test.__name__} - FAILED: {str(e)}")

        self.print_summary()

    async def test_plugin_discovery(self):
        """Test plugin discovery functionality."""
        logger.info("Testing plugin discovery...")

        discovered = await plugin_manager.discover_plugins()

        assert len(discovered) > 0, "No plugins discovered"
        assert "vpn.wireguard" in discovered, "WireGuard plugin not discovered"

        logger.info(f"Discovered {len(discovered)} plugins: {discovered}")

    async def test_plugin_loading(self):
        """Test plugin loading functionality."""
        logger.info("Testing plugin loading...")

        # Load WireGuard plugin
        success = await plugin_manager.load_plugin("vpn.wireguard", enable=True)
        assert success, "Failed to load WireGuard plugin"

        # Verify plugin is loaded and enabled
        assert plugin_manager.is_plugin_loaded("vpn.wireguard"), "Plugin not marked as loaded"
        assert plugin_manager.is_plugin_enabled("vpn.wireguard"), "Plugin not marked as enabled"

        # Get plugin instance
        plugin = plugin_manager.get_plugin("vpn.wireguard")
        assert plugin is not None, "Plugin instance not available"
        assert plugin.name == "wireguard", "Plugin name incorrect"
        assert plugin.category == "vpn", "Plugin category incorrect"

        logger.info("Plugin loaded and enabled successfully")

    async def test_wireguard_plugin_basic(self):
        """Test basic WireGuard plugin functionality."""
        logger.info("Testing WireGuard plugin basic functionality...")

        plugin = plugin_manager.get_plugin("vpn.wireguard")
        assert plugin is not None, "WireGuard plugin not available"

        # Test plugin info
        info = plugin.get_info()
        assert info["name"] == "wireguard", f"Plugin info incorrect: expected 'wireguard', got '{info['name']}'"
        assert info["category"] == "vpn", f"Plugin category incorrect: expected 'vpn', got '{info['category']}'"

        # Test health status
        health = plugin.get_health_status()
        assert health["status"] in ["healthy", "degraded", "not_initialized"], f"Plugin health status invalid: {health['status']}"

        # Test database schema
        schema = plugin.get_database_schema()
        assert "servers" in schema, "Servers schema missing"
        assert "clients" in schema, "Clients schema missing"

        # Test that plugin is self-contained
        api_routes = plugin.get_api_routes()
        assert len(api_routes) > 0, "Plugin should provide API routes"

        logger.info("Basic plugin functionality verified")

    async def test_wireguard_server_operations(self):
        """Test WireGuard server CRUD operations."""
        logger.info("Testing WireGuard server operations...")

        plugin = plugin_manager.get_plugin("vpn.wireguard")

        # Import VPN models from the plugin's category
        if VPNServerCreate is None:
            logger.warning("VPN models not available, skipping server operations test")
            return

        # Test server creation
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
            description="Test server for plugin framework"
        )

        server = await plugin.create_server(server_data)
        assert server is not None, "Failed to create server"
        assert server.name == "test-server", "Server name incorrect"
        assert server.port == 51820, "Server port incorrect"
        assert server.public_key is not None, "Server public key not generated"

        self.test_server_id = server.id
        logger.info(f"Created test server with ID: {self.test_server_id}")

        # Test server retrieval
        retrieved_server = await plugin.get_server(self.test_server_id)
        assert retrieved_server is not None, "Failed to retrieve server"
        assert retrieved_server.id == self.test_server_id, "Retrieved server ID mismatch"

        # Test server listing
        servers = await plugin.list_servers()
        assert len(servers) >= 1, "Server list empty"
        server_ids = [s.id for s in servers]
        assert self.test_server_id in server_ids, "Test server not in list"

        logger.info("Server CRUD operations verified")

    async def test_wireguard_client_operations(self):
        """Test WireGuard client CRUD operations."""
        logger.info("Testing WireGuard client operations...")

        if not self.test_server_id:
            raise ValueError("Test server not available for client operations")

        plugin = plugin_manager.get_plugin("vpn.wireguard")

        # Import VPN models from the plugin's category
        if VPNClientCreate is None:
            logger.warning("VPN models not available, skipping client operations test")
            return

        # Test client creation
        client_data = VPNClientCreate(
            name="test-client",
            server_id=self.test_server_id,
            email="test@example.com",
            allowed_ips=["0.0.0.0/0"],
            dns_servers=["8.8.8.8"],
            persistent_keepalive=25,
            enabled=True,
            description="Test client for plugin framework"
        )

        client = await plugin.create_client(client_data)
        assert client is not None, "Failed to create client"
        assert client.name == "test-client", "Client name incorrect"
        assert client.server_id == self.test_server_id, "Client server ID incorrect"
        assert client.public_key is not None, "Client public key not generated"
        assert client.private_key is not None, "Client private key not generated"
        assert client.allocated_ip is not None, "Client IP not allocated"

        self.test_client_id = client.id
        logger.info(f"Created test client with ID: {self.test_client_id}")

        # Test client retrieval
        retrieved_client = await plugin.get_client(self.test_client_id)
        assert retrieved_client is not None, "Failed to retrieve client"
        assert retrieved_client.id == self.test_client_id, "Retrieved client ID mismatch"

        # Test client listing
        clients = await plugin.list_clients(server_id=self.test_server_id)
        assert len(clients) >= 1, "Client list empty"
        client_ids = [c.id for c in clients]
        assert self.test_client_id in client_ids, "Test client not in list"

        logger.info("Client CRUD operations verified")

    async def test_configuration_generation(self):
        """Test WireGuard configuration generation."""
        logger.info("Testing configuration generation...")

        if not self.test_client_id:
            raise ValueError("Test client not available for configuration generation")

        plugin = plugin_manager.get_plugin("vpn.wireguard")

        # Test configuration generation
        config = await plugin.generate_config(self.test_client_id)
        assert config is not None, "Failed to generate configuration"
        assert config.config_content is not None, "Configuration content empty"
        assert "[Interface]" in config.config_content, "Invalid configuration format"
        assert "[Peer]" in config.config_content, "Peer section missing from configuration"

        # QR code generation might fail if dependencies are missing, so make it optional
        if config.qr_code is not None:
            logger.info("QR code generated successfully")
        else:
            logger.warning("QR code not generated (possibly missing dependencies)")

        logger.info("Configuration generation verified")
        logger.info(f"Configuration preview:\n{config.config_content[:200]}...")

    async def test_plugin_cleanup(self):
        """Test cleanup operations."""
        logger.info("Testing plugin cleanup...")

        plugin = plugin_manager.get_plugin("vpn.wireguard")

        # Clean up test client
        if self.test_client_id:
            success = await plugin.delete_client(self.test_client_id)
            assert success, "Failed to delete test client"
            logger.info("Test client deleted")

        # Clean up test server
        if self.test_server_id:
            success = await plugin.delete_server(self.test_server_id)
            assert success, "Failed to delete test server"
            logger.info("Test server deleted")

        logger.info("Cleanup completed")

    def print_summary(self):
        """Print test summary."""
        logger.info("=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)

        passed = sum(1 for _, result in self.test_results if result == "PASS")
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASS" else "❌"
            logger.info(f"{status_icon} {test_name}: {result}")

        logger.info("=" * 50)
        logger.info(f"RESULTS: {passed}/{total} tests passed")

        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Plugin framework is working correctly.")
        else:
            logger.error(f"💥 {total - passed} tests failed. Plugin framework needs attention.")

        return passed == total


async def main():
    """Main test execution function."""
    test_suite = PluginSystemTest()

    try:
        success = await test_suite.run_all_tests()

        # Test plugin isolation
        logger.info("Testing plugin isolation...")
        plugin = plugin_manager.get_plugin("vpn.wireguard")
        if plugin:
            # Verify plugin has its own namespace
            info = plugin.get_info()
            assert "api_prefix" in info, "Plugin should have its own API prefix"
            logger.info(f"Plugin API prefix: {info.get('api_prefix', 'N/A')}")

            # Verify plugin routes are properly isolated
            routes = plugin.get_api_routes()
            if routes:
                logger.info(f"Plugin provides {len(routes)} route group(s)")

        logger.info("Plugin isolation test completed")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're in the right directory
    if not Path("app/plugins").exists():
        logger.error("Please run this script from the firewallo-ui root directory")
        sys.exit(1)

    # Run the tests
    asyncio.run(main())
