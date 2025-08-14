"""
WireGuard Plugin tests package for Firewallo UI.

This package contains comprehensive tests for the WireGuard VPN plugin.

Test modules:
- test_plugin.py: Main plugin functionality tests
- test_services.py: WireGuard service layer tests
- test_api.py: Plugin API endpoint tests
- test_integration.py: Integration tests with the plugin system
- test_config.py: Configuration management tests
- test_security.py: Security and key management tests
- test_monitoring.py: Server and client monitoring tests
- test_performance.py: Performance and load tests

The WireGuard plugin provides VPN server and client management functionality
with secure key generation, configuration management, and monitoring capabilities.

Test Coverage Areas:
- Server lifecycle (create, start, stop, delete)
- Client management (create, configure, delete)
- Configuration generation and validation
- Key pair generation and management
- Network configuration and routing
- Monitoring and status reporting
- API endpoint functionality
- Error handling and recovery
- Security validations
- Performance under load

Usage:
    # Run all WireGuard plugin tests
    python run_tests.py

    # Run specific test module
    pytest test_plugin.py

    # Run with coverage
    pytest --cov=../plugin.py --cov=../services.py

    # Run integration tests only
    pytest -m integration

Environment Requirements:
- WireGuard tools (wg, wg-quick) for integration tests
- Network permissions for testing network configurations
- Sufficient system resources for load testing

Test Data:
- Mock servers and clients for unit tests
- Test network configurations
- Sample WireGuard configurations
- Performance benchmarks and thresholds
"""

import sys
from pathlib import Path

# Add plugin directory and project root to Python path
plugin_dir = Path(__file__).parent.parent
project_root = plugin_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(plugin_dir))

# Plugin test configuration
PLUGIN_NAME = "wireguard"
PLUGIN_CATEGORY = "vpn"
PLUGIN_VERSION = "1.0.0"

# Test configuration constants
TEST_CONFIG = {
    "test_network": "192.168.100.0/24",
    "test_port_range": "52000-52010",
    "test_endpoint": "192.168.1.100",
    "max_test_clients": 10,
    "test_timeout": 30,
    "performance_thresholds": {
        "max_response_time": 1000,  # milliseconds
        "min_throughput": 10,  # Mbps
        "max_memory_usage": 100  # MB
    }
}

# Test data generators
def generate_test_server_data():
    """Generate test server configuration data."""
    return {
        "name": "test-server",
        "endpoint": TEST_CONFIG["test_endpoint"],
        "port": 52000,
        "network": TEST_CONFIG["test_network"],
        "dns_servers": ["8.8.8.8", "8.8.4.4"],
        "allowed_ips": ["0.0.0.0/0"],
        "mtu": 1420,
        "keep_alive": 25,
        "enabled": True,
        "description": "Test WireGuard server"
    }

def generate_test_client_data(server_id="test-server-id"):
    """Generate test client configuration data."""
    return {
        "name": "test-client",
        "server_id": server_id,
        "email": "test@example.com",
        "allowed_ips": ["0.0.0.0/0"],
        "dns_servers": ["8.8.8.8"],
        "persistent_keepalive": 25,
        "enabled": True,
        "description": "Test WireGuard client"
    }

def generate_test_keypair():
    """Generate test key pair for testing."""
    return {
        "private_key": "cK8ZuPCn7n3K8ZuPCn7n3K8ZuPCn7n3K8ZuPCn7n3K=",
        "public_key": "dL9AvQDo8o4L9AvQDo8o4L9AvQDo8o4L9AvQDo8o4L="
    }

# Test utilities
class WireGuardTestHelper:
    """Helper class for WireGuard plugin testing."""

    @staticmethod
    def create_mock_server(server_id="srv-123", **kwargs):
        """Create a mock server object for testing."""
        default_data = generate_test_server_data()
        default_data.update(kwargs)
        default_data["id"] = server_id
        keypair = generate_test_keypair()
        default_data.update(keypair)
        return default_data

    @staticmethod
    def create_mock_client(client_id="client-456", server_id="srv-123", **kwargs):
        """Create a mock client object for testing."""
        default_data = generate_test_client_data(server_id)
        default_data.update(kwargs)
        default_data["id"] = client_id
        keypair = generate_test_keypair()
        default_data.update(keypair)
        default_data["allocated_ip"] = "192.168.100.5"
        return default_data

    @staticmethod
    def create_mock_config(client_name="test-client"):
        """Create a mock WireGuard configuration."""
        return {
            "config_content": f"""[Interface]
PrivateKey = cK8ZuPCn7n3K8ZuPCn7n3K8ZuPCn7n3K8ZuPCn7n3K=
Address = 192.168.100.5/24
DNS = 8.8.8.8

[Peer]
PublicKey = dL9AvQDo8o4L9AvQDo8o4L9AvQDo8o4L9AvQDo8o4L=
Endpoint = {TEST_CONFIG["test_endpoint"]}:52000
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25""",
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "filename": f"{client_name}.conf"
        }

    @staticmethod
    def validate_wireguard_config(config_content):
        """Validate WireGuard configuration format."""
        required_sections = ["[Interface]", "[Peer]"]
        required_interface_keys = ["PrivateKey", "Address"]
        required_peer_keys = ["PublicKey", "Endpoint"]

        for section in required_sections:
            if section not in config_content:
                return False, f"Missing required section: {section}"

        # Basic validation - in real implementation would be more thorough
        for key in required_interface_keys + required_peer_keys:
            if key not in config_content:
                return False, f"Missing required key: {key}"

        return True, "Configuration is valid"

# Export test utilities
__all__ = [
    "PLUGIN_NAME",
    "PLUGIN_CATEGORY",
    "PLUGIN_VERSION",
    "TEST_CONFIG",
    "generate_test_server_data",
    "generate_test_client_data",
    "generate_test_keypair",
    "WireGuardTestHelper"
]
