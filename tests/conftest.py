"""
Pytest configuration and shared fixtures for Firewallo UI tests.

This module contains common fixtures, test utilities, and configuration
that can be used across all test modules in the application.
"""

import asyncio
import os
import sys
import tempfile
import pytest
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Add the app directory to Python path for imports
project_root = Path(__file__).parent.parent
app_dir = project_root / "app"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(app_dir))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    """Return the project root directory path."""
    return project_root


@pytest.fixture(scope="session")
def app_path() -> Path:
    """Return the app directory path."""
    return app_dir


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Mock environment variables for testing."""
    original_env = os.environ.copy()
    test_env = {
        "FIREWALLO_ENV": "test",
        "DATABASE_URL": "sqlite:///test.db",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
    }

    # Apply test environment
    os.environ.update(test_env)

    try:
        yield test_env
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.fixture
async def mock_database():
    """Mock database connection and operations."""
    with patch('app.db.database.Database') as mock_db_class:
        mock_db = AsyncMock()
        mock_db_class.return_value = mock_db

        # Mock common database operations
        mock_db.connect = AsyncMock()
        mock_db.disconnect = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.fetch_all = AsyncMock(return_value=[])
        mock_db.fetch_one = AsyncMock(return_value=None)
        mock_db.execute_many = AsyncMock()

        yield mock_db


@pytest.fixture
async def mock_plugin_manager():
    """Mock plugin manager for testing."""
    with patch('app.plugins.plugin_manager') as mock_manager:
        # Setup mock plugin manager
        mock_manager.discover_plugins = AsyncMock(return_value=["test.plugin"])
        mock_manager.load_plugin = AsyncMock(return_value=True)
        mock_manager.unload_plugin = AsyncMock(return_value=True)
        mock_manager.is_plugin_loaded = MagicMock(return_value=False)
        mock_manager.is_plugin_enabled = MagicMock(return_value=False)
        mock_manager.get_plugin = MagicMock(return_value=None)
        mock_manager.list_plugins = MagicMock(return_value=[])
        mock_manager.get_plugin_info = MagicMock(return_value={})

        yield mock_manager


@pytest.fixture
def mock_config():
    """Mock application configuration."""
    config_data = {
        "database": {
            "url": "sqlite:///test.db",
            "pool_size": 5,
            "max_overflow": 10
        },
        "auth": {
            "secret_key": "test-secret-key",
            "algorithm": "HS256",
            "token_expire_minutes": 30
        },
        "plugins": {
            "enabled": True,
            "auto_load": False,
            "plugin_dirs": ["app/plugins"]
        },
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "reload": False
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }

    with patch('app.core.config.get_config') as mock_get_config:
        mock_get_config.return_value = config_data
        yield config_data


@pytest.fixture
async def fastapi_app():
    """Create FastAPI application instance for testing."""
    from app.main import app
    return app


@pytest.fixture
async def test_client(fastapi_app):
    """Create test client for FastAPI application."""
    from httpx import AsyncClient

    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_auth_token():
    """Mock authentication token for testing authenticated endpoints."""
    token_data = {
        "access_token": "test-access-token",
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": "test-user-id",
        "username": "testuser"
    }

    with patch('app.auth.jwt_handler.verify_token') as mock_verify:
        mock_verify.return_value = token_data
        yield token_data


@pytest.fixture
def mock_user():
    """Mock user object for testing."""
    return {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
        "is_admin": False,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user object for testing."""
    return {
        "id": "admin-user-id",
        "username": "admin",
        "email": "admin@example.com",
        "is_active": True,
        "is_admin": True,
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_plugin_manifest():
    """Sample plugin manifest for testing."""
    return {
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "Test plugin for unit tests",
        "author": "Test Author",
        "category": "test",
        "api_version": "1.0",
        "dependencies": [],
        "permissions": ["read", "write"],
        "endpoints": [
            {
                "path": "/test",
                "method": "GET",
                "description": "Test endpoint"
            }
        ],
        "database_schema": {
            "tables": []
        }
    }


@pytest.fixture
async def mock_plugin():
    """Mock plugin instance for testing."""
    from app.plugins.base.plugin import BasePlugin

    class MockPlugin(BasePlugin):
        def __init__(self):
            self.name = "test-plugin"
            self.category = "test"
            self.version = "1.0.0"
            self.enabled = True

        async def initialize(self):
            pass

        async def shutdown(self):
            pass

        def get_info(self):
            return {
                "name": self.name,
                "category": self.category,
                "version": self.version,
                "enabled": self.enabled
            }

        def get_health_status(self):
            return {"status": "healthy"}

        def get_api_routes(self):
            return []

        def get_database_schema(self):
            return {}

    return MockPlugin()


@pytest.fixture
def mock_system_stats():
    """Mock system statistics for testing."""
    return {
        "cpu": {
            "usage": 25.5,
            "cores": 4,
            "load_average": [1.2, 1.1, 1.0]
        },
        "memory": {
            "total": 8589934592,  # 8GB
            "available": 4294967296,  # 4GB
            "used": 4294967296,  # 4GB
            "percentage": 50.0
        },
        "disk": {
            "total": 107374182400,  # 100GB
            "used": 53687091200,   # 50GB
            "free": 53687091200,   # 50GB
            "percentage": 50.0
        },
        "network": {
            "bytes_sent": 1024000,
            "bytes_recv": 2048000,
            "packets_sent": 1000,
            "packets_recv": 2000
        },
        "uptime": 86400,  # 1 day
        "timestamp": "2023-01-01T12:00:00Z"
    }


@pytest.fixture
def mock_requests():
    """Mock requests library for HTTP testing."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put, \
         patch('requests.delete') as mock_delete:

        # Configure default responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.text = '{"status": "ok"}'

        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        mock_put.return_value = mock_response
        mock_delete.return_value = mock_response

        yield {
            "get": mock_get,
            "post": mock_post,
            "put": mock_put,
            "delete": mock_delete,
            "response": mock_response
        }


@pytest.fixture
def capture_logs():
    """Capture log messages during testing."""
    import logging
    from io import StringIO

    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    # Get root logger and add our handler
    logger = logging.getLogger()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    try:
        yield log_capture
    finally:
        logger.removeHandler(handler)
        logger.setLevel(original_level)


# Test data generators
@pytest.fixture
def plugin_test_data():
    """Generate test data for plugin testing."""
    return {
        "valid_manifest": {
            "name": "test-plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "category": "system",
            "api_version": "1.0"
        },
        "invalid_manifest": {
            "name": "",  # Invalid: empty name
            "version": "invalid-version",  # Invalid: bad version format
        },
        "plugin_directory": "test-plugin-dir"
    }


# Async test utilities
@pytest.fixture
async def async_context_manager():
    """Utility for testing async context managers."""
    class AsyncContextManager:
        def __init__(self, return_value=None):
            self.return_value = return_value

        async def __aenter__(self):
            return self.return_value

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return AsyncContextManager


# Performance testing fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "min_rounds": 5,
        "max_time": 10.0,
        "warmup": True,
        "warmup_iterations": 2
    }


# Security testing fixtures
@pytest.fixture
def security_headers():
    """Expected security headers for testing."""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'"
    }


# Database testing utilities
@pytest.fixture
async def clean_database(mock_database):
    """Ensure clean database state for each test."""
    # Setup: Clean state
    await mock_database.execute("DELETE FROM test_table")

    yield mock_database

    # Teardown: Clean up after test
    await mock_database.execute("DELETE FROM test_table")


# Plugin system test utilities
@pytest.fixture
def plugin_loader_mock():
    """Mock plugin loader for testing plugin discovery and loading."""
    with patch('app.plugins.registry.loader.PluginLoader') as mock_loader_class:
        mock_loader = MagicMock()
        mock_loader_class.return_value = mock_loader

        mock_loader.discover_plugins = AsyncMock(return_value=[])
        mock_loader.load_plugin = AsyncMock(return_value=True)
        mock_loader.unload_plugin = AsyncMock(return_value=True)
        mock_loader.validate_plugin = MagicMock(return_value=True)

        yield mock_loader


# Test markers and utilities
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication test"
    )
    config.addinivalue_line(
        "markers", "plugins: mark test as plugin system test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file path
        test_path = str(item.fspath)

        if "test_api" in test_path:
            item.add_marker(pytest.mark.api)
        if "test_auth" in test_path:
            item.add_marker(pytest.mark.auth)
        if "test_plugins" in test_path:
            item.add_marker(pytest.mark.plugins)
        if "integration" in test_path:
            item.add_marker(pytest.mark.integration)
        if "unit" in test_path:
            item.add_marker(pytest.mark.unit)
