"""Base classes and utilities for plugin testing."""

import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from unittest.mock import Mock, AsyncMock, MagicMock
import pytest
from datetime import datetime

from app.plugins.base import BasePlugin, PluginError
from app.plugins.registry.manager import PluginManager
from app.plugins.registry.loader import PluginLoader
from app.plugins.registry.validator import PluginValidator
from app.plugins.base.repository import BaseRepository
from app.plugins.base.permissions import PluginPermissions


class PluginTestCase:
    """Base class for plugin testing.

    Provides common setup, teardown, and assertion methods for testing plugins.
    """

    def setup_method(self):
        """Setup test environment before each test."""
        self.plugin_manager = PluginManager()
        self.plugin = None
        self.test_data_dir = tempfile.mkdtemp(prefix="plugin_test_")
        self.test_plugins = []

    def teardown_method(self):
        """Cleanup after each test."""
        # Shutdown all test plugins
        for plugin in self.test_plugins:
            if hasattr(plugin, 'shutdown'):
                try:
                    # Handle both sync and async shutdown
                    if asyncio.iscoroutinefunction(plugin.shutdown):
                        asyncio.run(plugin.shutdown())
                    else:
                        plugin.shutdown()
                except Exception:
                    pass

        # Clean up test data directory
        if self.test_data_dir and Path(self.test_data_dir).exists():
            shutil.rmtree(self.test_data_dir)

        # Clear plugin manager
        self.plugin_manager = None

    def load_test_plugin(self, plugin_path: str) -> BasePlugin:
        """Load a plugin for testing (synchronous).

        Args:
            plugin_path: Plugin path in format "category.plugin_name".

        Returns:
            Loaded plugin instance.

        Raises:
            AssertionError: If plugin loading fails.
        """
        # For synchronous tests, run the async method in an event loop
        plugin = asyncio.run(self.async_load_test_plugin(plugin_path))
        return plugin

    async def async_load_test_plugin(self, plugin_path: str) -> BasePlugin:
        """Load a plugin for testing (asynchronous).

        Args:
            plugin_path: Plugin path in format "category.plugin_name".

        Returns:
            Loaded plugin instance.

        Raises:
            AssertionError: If plugin loading fails.
        """
        success = await self.plugin_manager.load_plugin(plugin_path, enable=True)
        assert success, f"Failed to load plugin: {plugin_path}"

        plugin = self.plugin_manager.get_plugin(plugin_path)
        assert plugin is not None, f"Plugin instance not available: {plugin_path}"

        self.test_plugins.append(plugin)
        return plugin

    def assert_plugin_valid(self, plugin: BasePlugin):
        """Assert that a plugin meets basic requirements.

        Args:
            plugin: Plugin instance to validate.

        Raises:
            AssertionError: If plugin is invalid.
        """
        assert plugin.name, "Plugin must have a name"
        assert plugin.category, "Plugin must have a category"
        assert plugin.version, "Plugin must have a version"
        assert hasattr(plugin, 'initialize'), "Plugin must implement initialize()"
        assert hasattr(plugin, 'shutdown'), "Plugin must implement shutdown()"
        assert hasattr(plugin, 'get_api_routes'), "Plugin must implement get_api_routes()"
        assert hasattr(plugin, 'get_database_schema'), "Plugin must implement get_database_schema()"

    def assert_plugin_initialized(self, plugin: BasePlugin):
        """Assert that a plugin has been properly initialized.

        Args:
            plugin: Plugin instance to check.

        Raises:
            AssertionError: If plugin is not initialized.
        """
        assert plugin._initialized, "Plugin should be initialized"
        assert plugin._startup_time is not None, "Plugin should have startup time"

    def assert_plugin_permissions(self, plugin: BasePlugin, required_permissions: List[str]):
        """Assert that a plugin has required permissions.

        Args:
            plugin: Plugin instance to check.
            required_permissions: List of required permission strings.

        Raises:
            AssertionError: If plugin lacks required permissions.
        """
        if not hasattr(plugin, 'manifest') or not plugin.manifest:
            pytest.skip("Plugin has no manifest to check permissions")

        plugin_permissions = plugin.manifest.get('permissions', [])
        for perm in required_permissions:
            assert perm in plugin_permissions, f"Plugin lacks required permission: {perm}"

    def create_mock_repository(self, plugin_name: str = "test_plugin",
                             category: str = "test") -> Mock:
        """Create a mock repository for testing.

        Args:
            plugin_name: Name of the plugin.
            category: Plugin category.

        Returns:
            Mock repository instance.
        """
        mock_repo = Mock(spec=BaseRepository)
        mock_repo.plugin_name = plugin_name
        mock_repo.category = category
        mock_repo.get_data = AsyncMock(return_value={})
        mock_repo.set_data = AsyncMock(return_value=True)
        mock_repo.delete_data = AsyncMock(return_value=True)
        mock_repo.list_data = AsyncMock(return_value=[])
        return mock_repo


class AsyncPluginTestCase(PluginTestCase):
    """Base class for async plugin testing.

    Extends PluginTestCase with async-specific test methods.
    """

    @pytest.mark.asyncio
    async def async_setup_method(self):
        """Async setup method for pytest-asyncio."""
        self.setup_method()

    @pytest.mark.asyncio
    async def async_teardown_method(self):
        """Async teardown method for pytest-asyncio."""
        # Shutdown all test plugins asynchronously
        for plugin in self.test_plugins:
            if hasattr(plugin, 'shutdown'):
                await plugin.shutdown()

        self.teardown_method()

    async def assert_plugin_health(self, plugin: BasePlugin):
        """Assert that a plugin is healthy.

        Args:
            plugin: Plugin instance to check.

        Raises:
            AssertionError: If plugin is not healthy.
        """
        health = plugin.get_health_status()
        assert health['status'] in ['healthy', 'degraded'], f"Plugin unhealthy: {health['status']}"

    async def test_plugin_lifecycle(self, plugin: BasePlugin):
        """Test complete plugin lifecycle.

        Args:
            plugin: Plugin instance to test.
        """
        # Test initialization
        success = await plugin.initialize()
        assert success, "Plugin initialization failed"
        self.assert_plugin_initialized(plugin)

        # Test health check
        await self.assert_plugin_health(plugin)

        # Test metrics
        metrics = plugin.get_metrics()
        assert isinstance(metrics, dict), "Metrics should be a dictionary"

        # Test shutdown
        await plugin.shutdown()
        assert plugin._shutdown_time is not None, "Plugin should have shutdown time"


class MockPluginManager(PluginManager):
    """Mock plugin manager for testing."""

    def __init__(self):
        """Initialize mock plugin manager."""
        super().__init__()
        self.mock_plugins = {}
        self.load_attempts = []
        self.unload_attempts = []

    async def load_plugin(self, plugin_path: str, enable: bool = True) -> bool:
        """Mock plugin loading.

        Args:
            plugin_path: Plugin path.
            enable: Whether to enable the plugin.

        Returns:
            True if loading succeeds.
        """
        self.load_attempts.append(plugin_path)

        if plugin_path in self.mock_plugins:
            self.plugins[plugin_path] = self.mock_plugins[plugin_path]
            if enable:
                self.enabled_plugins.add(plugin_path)
            return True
        return False

    async def unload_plugin(self, plugin_path: str) -> bool:
        """Mock plugin unloading.

        Args:
            plugin_path: Plugin path.

        Returns:
            True if unloading succeeds.
        """
        self.unload_attempts.append(plugin_path)

        if plugin_path in self.plugins:
            del self.plugins[plugin_path]
            self.enabled_plugins.discard(plugin_path)
            return True
        return False

    def add_mock_plugin(self, plugin_path: str, plugin: BasePlugin):
        """Add a mock plugin to the manager.

        Args:
            plugin_path: Plugin path.
            plugin: Plugin instance.
        """
        self.mock_plugins[plugin_path] = plugin


class MockRepository(BaseRepository):
    """Mock repository for testing."""

    def __init__(self, plugin_name: str = "test_plugin", category: str = "test"):
        """Initialize mock repository.

        Args:
            plugin_name: Plugin name.
            category: Plugin category.
        """
        super().__init__(plugin_name, category)
        self.data_store = {}
        self.operation_log = []

    async def get_data(self, path: str, default: Optional[Any] = None) -> Optional[Any]:
        """Mock data retrieval.

        Args:
            path: Data path.
            default: Default value if not found.

        Returns:
            Data at path or default.
        """
        self.operation_log.append(('get', path))
        return self.data_store.get(path, default)

    async def set_data(self, path: str, data: Any) -> bool:
        """Mock data storage.

        Args:
            path: Data path.
            data: Data to store.

        Returns:
            True if successful.
        """
        self.operation_log.append(('set', path, data))
        self.data_store[path] = data
        return True

    async def delete_data(self, path: str) -> bool:
        """Mock data deletion.

        Args:
            path: Data path.

        Returns:
            True if successful.
        """
        self.operation_log.append(('delete', path))
        if path in self.data_store:
            del self.data_store[path]
            return True
        return False

    async def list_data(self, path: str) -> List[str]:
        """Mock data listing.

        Args:
            path: Data path prefix.

        Returns:
            List of keys under path.
        """
        self.operation_log.append(('list', path))
        return [k for k in self.data_store.keys() if k.startswith(path)]

    def clear_log(self):
        """Clear the operation log."""
        self.operation_log.clear()


class TestPlugin(BasePlugin):
    """Test plugin implementation for testing purposes."""

    def __init__(self, name: str = "test_plugin", category: str = "test"):
        """Initialize test plugin.

        Args:
            name: Plugin name.
            category: Plugin category.
        """
        super().__init__()
        self.name = name
        self.category = category
        self.version = "1.0.0"
        self.description = "Test plugin for testing"
        self.author = "Test Author"
        self.license = "MIT"

        # Track method calls for testing
        self.method_calls = []

    async def initialize(self) -> bool:
        """Initialize the test plugin.

        Returns:
            True if successful.
        """
        self.method_calls.append('initialize')
        self._initialized = True
        self._startup_time = datetime.utcnow()
        return True

    async def shutdown(self) -> None:
        """Shutdown the test plugin."""
        self.method_calls.append('shutdown')
        self._shutdown_time = datetime.utcnow()
        self._initialized = False

    def get_api_routes(self) -> List:
        """Get API routes.

        Returns:
            Empty list for test plugin.
        """
        self.method_calls.append('get_api_routes')
        return []

    def get_database_schema(self) -> Dict[str, Any]:
        """Get database schema.

        Returns:
            Test schema.
        """
        self.method_calls.append('get_database_schema')
        return {
            "test_data": [],
            "config": {}
        }

    def was_called(self, method_name: str) -> bool:
        """Check if a method was called.

        Args:
            method_name: Name of the method.

        Returns:
            True if method was called.
        """
        return method_name in self.method_calls

    def reset_calls(self):
        """Reset method call tracking."""
        self.method_calls.clear()


def create_test_plugin(name: str = "test_plugin",
                      category: str = "test",
                      **kwargs) -> TestPlugin:
    """Create a test plugin instance.

    Args:
        name: Plugin name.
        category: Plugin category.
        **kwargs: Additional attributes to set.

    Returns:
        TestPlugin instance.
    """
    plugin = TestPlugin(name, category)

    # Set additional attributes
    for key, value in kwargs.items():
        setattr(plugin, key, value)

    return plugin


def load_test_manifest(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    """Load a test manifest file.

    Args:
        manifest_path: Path to manifest file. If None, returns default manifest.

    Returns:
        Manifest dictionary.
    """
    if manifest_path and Path(manifest_path).exists():
        with open(manifest_path, 'r') as f:
            return json.load(f)

    # Return default test manifest
    return {
        "name": "test_plugin",
        "display_name": "Test Plugin",
        "category": "test",
        "version": "1.0.0",
        "description": "Test plugin for testing",
        "author": "Test Author",
        "email": "test@example.com",
        "license": "MIT",
        "repository": "https://github.com/test/test-plugin",
        "dependencies": {
            "python": ">=3.11",
            "packages": [],
            "system": []
        },
        "permissions": [
            "database.read",
            "database.write"
        ],
        "configuration": {
            "required": [],
            "optional": ["debug", "log_level"]
        },
        "api_prefix": "/api/test/test_plugin",
        "database_path": "plugins.test.test_plugin",
        "supports_hot_reload": True,
        "min_firewallo_version": "1.0.0"
    }


def validate_test_plugin(plugin: BasePlugin, manifest: Optional[Dict[str, Any]] = None) -> bool:
    """Validate a test plugin against requirements.

    Args:
        plugin: Plugin instance to validate.
        manifest: Optional manifest to validate against.

    Returns:
        True if plugin is valid.

    Raises:
        AssertionError: If validation fails.
    """
    # Basic plugin validation
    assert plugin.name, "Plugin must have a name"
    assert plugin.category, "Plugin must have a category"
    assert plugin.version, "Plugin must have a version"

    # Method validation
    assert hasattr(plugin, 'initialize'), "Plugin must have initialize method"
    assert hasattr(plugin, 'shutdown'), "Plugin must have shutdown method"
    assert hasattr(plugin, 'get_api_routes'), "Plugin must have get_api_routes method"
    assert hasattr(plugin, 'get_database_schema'), "Plugin must have get_database_schema method"

    # Manifest validation if provided
    if manifest:
        assert plugin.name == manifest.get('name'), "Plugin name must match manifest"
        assert plugin.category == manifest.get('category'), "Plugin category must match manifest"
        assert plugin.version == manifest.get('version'), "Plugin version must match manifest"

    return True


# Export pytest fixtures for easy use in tests
@pytest.fixture
def plugin_manager():
    """Pytest fixture for plugin manager."""
    return PluginManager()


@pytest.fixture
def mock_plugin_manager():
    """Pytest fixture for mock plugin manager."""
    return MockPluginManager()


@pytest.fixture
def test_plugin():
    """Pytest fixture for test plugin."""
    return create_test_plugin()


@pytest.fixture
def mock_repository():
    """Pytest fixture for mock repository."""
    return MockRepository()


@pytest.fixture
def test_manifest():
    """Pytest fixture for test manifest."""
    return load_test_manifest()
