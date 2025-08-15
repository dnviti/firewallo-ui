"""Tests for Plugin Web UI Framework."""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.testclient import TestClient
from fastapi.templating import Jinja2Templates

# Import plugin components
from app.plugins.base import BasePlugin
from app.plugins.system.webui.services import MenuService


class MockWebUIPlugin(BasePlugin):
    """Mock plugin with WebUI capabilities for testing."""

    def __init__(self):
        super().__init__()
        self.name = "test_plugin"
        self.category = "test"
        self.version = "1.0.0"
        self.description = "Test plugin with WebUI"

        # Set manifest with WebUI configuration
        self.set_manifest({
            "name": "test_plugin",
            "category": "test",
            "version": "1.0.0",
            "webui": {
                "enabled": True,
                "menu_entry": {
                    "title": "Test Plugin",
                    "icon": "bi-test",
                    "category": "test",
                    "position": 50,
                    "permissions": ["test.view"]
                },
                "routes": {
                    "base_path": "/plugins/test/test_plugin",
                    "use_system_theme": True,
                    "custom_theme": None
                },
                "static_path": "webui/static",
                "template_path": "webui/templates"
            }
        })

    async def initialize(self) -> bool:
        """Initialize the test plugin."""
        self.mark_initialized()
        return True

    async def shutdown(self) -> None:
        """Shutdown the test plugin."""
        self.mark_shutdown()

    def get_api_routes(self) -> List[APIRouter]:
        """Return API routes."""
        router = APIRouter()

        @router.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        return [router]

    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema."""
        return {"test": {"data": {}}}


class TestPluginWebUIInitialization:
    """Test plugin WebUI initialization."""

    @pytest.mark.asyncio
    async def test_webui_initialization_with_manifest(self):
        """Test that WebUI is initialized when manifest has webui config."""
        plugin = MockWebUIPlugin()

        assert plugin.webui_enabled is True
        assert plugin.webui_base_path == "/plugins/test/test_plugin"
        assert plugin.webui_router is None  # Not initialized until initialize_webui called
        assert plugin.menu_entry_registered is False

    @pytest.mark.asyncio
    async def test_webui_initialization_without_manifest(self):
        """Test that WebUI is not initialized without webui config."""
        plugin = BasePlugin()
        plugin.name = "no_webui"
        plugin.category = "test"

        assert plugin.webui_enabled is False
        assert plugin.webui_router is None
        assert plugin.menu_entry_registered is False

    @pytest.mark.asyncio
    async def test_initialize_webui_with_module(self):
        """Test WebUI initialization with webui module."""
        plugin = MockWebUIPlugin()

        # Mock the webui module import
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_webui_class = MagicMock()
            mock_webui_instance = MagicMock()
            mock_webui_instance.router = APIRouter()
            mock_webui_class.return_value = mock_webui_instance
            mock_module.PluginWebUI = mock_webui_class
            mock_import.return_value = mock_module

            # Mock MenuService
            with patch.object(MenuService, 'register_plugin_menu', new_callable=AsyncMock) as mock_register:
                mock_register.return_value = True

                result = await plugin.initialize_webui()

                assert result is True
                assert plugin.webui_handler is mock_webui_instance
                assert plugin.webui_router is mock_webui_instance.router
                mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_webui_without_module(self):
        """Test WebUI initialization when webui module doesn't exist."""
        plugin = MockWebUIPlugin()

        # Mock the webui module import to fail
        with patch('importlib.import_module', side_effect=ImportError("No module")):
            with patch.object(plugin.logger, 'warning') as mock_warning:
                result = await plugin.initialize_webui()

                assert result is False
                assert plugin.webui_handler is None
                assert plugin.webui_router is None
                mock_warning.assert_called()


class TestMenuService:
    """Test MenuService functionality."""

    @pytest.mark.asyncio
    async def test_menu_registration(self):
        """Test registering a plugin menu entry."""
        # Reset MenuService state
        MenuService._menu_entries = {}
        MenuService._menu_order = []

        menu_entry = {
            'id': 'test_plugin',
            'title': 'Test Plugin',
            'icon': 'bi-test',
            'url': '/plugins/test/test_plugin',
            'category': 'test',
            'position': 50,
            'permissions': ['test.view'],
            'badge': None,
            'active': True
        }

        with patch.object(MenuService, '_save_menu_configuration', new_callable=AsyncMock):
            result = await MenuService.register_plugin_menu(menu_entry)

            assert result is True
            assert 'test_plugin' in MenuService._menu_entries
            assert MenuService._menu_entries['test_plugin']['title'] == 'Test Plugin'

    @pytest.mark.asyncio
    async def test_menu_unregistration(self):
        """Test unregistering a plugin menu entry."""
        # Setup initial menu entry
        MenuService._menu_entries = {'test_plugin': {'title': 'Test'}}
        MenuService._menu_order = ['test_plugin']

        with patch.object(MenuService, '_save_menu_configuration', new_callable=AsyncMock):
            result = await MenuService.unregister_plugin_menu('test_plugin')

            assert result is True
            assert 'test_plugin' not in MenuService._menu_entries
            assert 'test_plugin' not in MenuService._menu_order

    @pytest.mark.asyncio
    async def test_update_menu_badge(self):
        """Test updating menu badge."""
        # Setup initial menu entry
        MenuService._menu_entries = {'test_plugin': {'title': 'Test', 'badge': None}}

        with patch.object(MenuService, '_save_menu_configuration', new_callable=AsyncMock):
            # Add badge
            result = await MenuService.update_badge('test_plugin', 5, 'danger')
            assert result is True
            assert MenuService._menu_entries['test_plugin']['badge'] == {
                'count': 5,
                'style': 'danger'
            }

            # Remove badge
            result = await MenuService.update_badge('test_plugin', None)
            assert result is True
            assert MenuService._menu_entries['test_plugin']['badge'] is None

    @pytest.mark.asyncio
    async def test_set_menu_visibility(self):
        """Test setting menu visibility."""
        MenuService._menu_entries = {'test_plugin': {'title': 'Test', 'visible': True}}

        with patch.object(MenuService, '_save_menu_configuration', new_callable=AsyncMock):
            result = await MenuService.set_visibility('test_plugin', False)

            assert result is True
            assert MenuService._menu_entries['test_plugin']['visible'] is False

    @pytest.mark.asyncio
    async def test_update_menu_title(self):
        """Test updating menu title."""
        MenuService._menu_entries = {'test_plugin': {'title': 'Old Title'}}

        with patch.object(MenuService, '_save_menu_configuration', new_callable=AsyncMock):
            result = await MenuService.update_title('test_plugin', 'New Title')

            assert result is True
            assert MenuService._menu_entries['test_plugin']['title'] == 'New Title'

    @pytest.mark.asyncio
    async def test_get_menu_entries_with_permissions(self):
        """Test getting menu entries filtered by permissions."""
        MenuService._menu_entries = {
            'plugin1': {
                'title': 'Plugin 1',
                'permissions': ['admin.view'],
                'visible': True,
                'active': True
            },
            'plugin2': {
                'title': 'Plugin 2',
                'permissions': ['user.view'],
                'visible': True,
                'active': True
            },
            'plugin3': {
                'title': 'Plugin 3',
                'permissions': [],
                'visible': True,
                'active': True
            }
        }
        MenuService._menu_order = ['plugin1', 'plugin2', 'plugin3']

        # Test with admin permissions
        admin_menus = await MenuService.get_menu_entries(['admin.view'])
        assert len(admin_menus) == 2  # plugin1 and plugin3 (no permissions required)

        # Test with user permissions
        user_menus = await MenuService.get_menu_entries(['user.view'])
        assert len(user_menus) == 2  # plugin2 and plugin3

        # Test with no permissions specified (returns all visible and active)
        all_menus = await MenuService.get_menu_entries(None)
        assert len(all_menus) == 3

    @pytest.mark.asyncio
    async def test_get_menu_by_category(self):
        """Test getting menu entries by category."""
        MenuService._menu_entries = {
            'vpn1': {'category': 'vpn', 'title': 'VPN 1'},
            'vpn2': {'category': 'vpn', 'title': 'VPN 2'},
            'firewall1': {'category': 'firewall', 'title': 'Firewall 1'}
        }
        MenuService._menu_order = ['vpn1', 'vpn2', 'firewall1']

        vpn_menus = await MenuService.get_menu_by_category('vpn')
        assert len(vpn_menus) == 2
        assert all(menu['category'] == 'vpn' for menu in vpn_menus)


class TestPluginWebUIIntegration:
    """Test plugin WebUI integration with main app."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        from fastapi import FastAPI
        app = FastAPI()
        return app

    @pytest.mark.asyncio
    async def test_plugin_webui_route_registration(self, mock_app):
        """Test that plugin WebUI routes are registered correctly."""
        plugin = MockWebUIPlugin()

        # Create a mock WebUI router
        webui_router = APIRouter()

        @webui_router.get("/")
        async def plugin_home():
            return {"page": "home"}

        plugin.webui_router = webui_router
        plugin.webui_enabled = True

        # Register the router
        mock_app.include_router(
            plugin.webui_router,
            prefix=plugin.webui_base_path
        )

        # Test with TestClient
        client = TestClient(mock_app)
        response = client.get("/plugins/test/test_plugin/")

        assert response.status_code == 200
        assert response.json() == {"page": "home"}

    @pytest.mark.asyncio
    async def test_plugin_webui_static_mounting(self, mock_app):
        """Test that plugin static files are mounted correctly."""
        from fastapi.staticfiles import StaticFiles

        plugin = MockWebUIPlugin()

        # Create a temporary static directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            static_dir = Path(tmpdir) / "static"
            static_dir.mkdir()

            # Create a test static file
            test_file = static_dir / "test.css"
            test_file.write_text("body { color: red; }")

            # Mount static files
            mock_app.mount(
                f"{plugin.webui_base_path}/static",
                StaticFiles(directory=str(static_dir)),
                name=f"{plugin.name}_static"
            )

            # Test with TestClient
            client = TestClient(mock_app)
            response = client.get(f"{plugin.webui_base_path}/static/test.css")

            assert response.status_code == 200
            assert response.text == "body { color: red; }"

    @pytest.mark.asyncio
    async def test_plugin_menu_updates(self):
        """Test that plugins can update their menu entries."""
        plugin = MockWebUIPlugin()
        plugin.menu_entry_registered = True

        # Mock MenuService methods
        with patch.object(MenuService, 'update_badge', new_callable=AsyncMock) as mock_badge:
            with patch.object(MenuService, 'set_visibility', new_callable=AsyncMock) as mock_visibility:
                with patch.object(MenuService, 'update_title', new_callable=AsyncMock) as mock_title:
                    mock_badge.return_value = True
                    mock_visibility.return_value = True
                    mock_title.return_value = True

                    # Test badge update
                    result = await plugin.update_menu_badge(3, "warning")
                    assert result is True
                    mock_badge.assert_called_with("test_test_plugin", 3, "warning")

                    # Test visibility update
                    result = await plugin.set_menu_visibility(False)
                    assert result is True
                    mock_visibility.assert_called_with("test_test_plugin", False)

                    # Test title update
                    result = await plugin.update_menu_title("Updated Title")
                    assert result is True
                    mock_title.assert_called_with("test_test_plugin", "Updated Title")

    @pytest.mark.asyncio
    async def test_webui_info_retrieval(self):
        """Test getting WebUI information from plugin."""
        plugin = MockWebUIPlugin()
        plugin.webui_router = APIRouter()
        plugin.webui_templates = Jinja2Templates(directory=".")
        plugin.webui_static_mounted = True
        plugin.menu_entry_registered = True

        info = plugin.get_webui_info()

        assert info['enabled'] is True
        assert info['base_path'] == "/plugins/test/test_plugin"
        assert info['has_router'] is True
        assert info['has_templates'] is True
        assert info['static_mounted'] is True
        assert info['menu_registered'] is True
        assert info['use_system_theme'] is True
        assert info['static_path'] == "/plugins/test/test_plugin/static"

    @pytest.mark.asyncio
    async def test_standalone_access_without_main_webui(self):
        """Test that plugin WebUI is accessible when main WebUI is disabled."""
        from fastapi import FastAPI

        app = FastAPI()
        plugin = MockWebUIPlugin()

        # Create plugin WebUI router
        webui_router = APIRouter()

        @webui_router.get("/standalone")
        async def standalone_page():
            return {"message": "Plugin works without main WebUI"}

        plugin.webui_router = webui_router

        # Register only plugin routes (simulating main WebUI disabled)
        app.include_router(
            plugin.webui_router,
            prefix=plugin.webui_base_path
        )

        # Test access
        client = TestClient(app)
        response = client.get("/plugins/test/test_plugin/standalone")

        assert response.status_code == 200
        assert response.json() == {"message": "Plugin works without main WebUI"}


class TestWireGuardWebUI:
    """Test WireGuard plugin WebUI specifically."""

    @pytest.mark.asyncio
    async def test_wireguard_webui_initialization(self):
        """Test WireGuard WebUI initialization."""
        from app.plugins.vpn.wireguard.plugin import WireGuardPlugin

        with patch('app.plugins.vpn.wireguard.plugin.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps({
                "name": "wireguard",
                "category": "vpn",
                "version": "1.0.0",
                "webui": {
                    "enabled": True,
                    "menu_entry": {
                        "title": "WireGuard VPN",
                        "icon": "bi-shield-lock",
                        "category": "vpn",
                        "position": 10,
                        "permissions": ["vpn.wireguard.view"]
                    },
                    "routes": {
                        "base_path": "/plugins/vpn/wireguard",
                        "use_system_theme": True
                    }
                }
            }))):
                with patch.object(WireGuardPlugin, '_initialize_webui'):
                    plugin = WireGuardPlugin()

                    assert plugin.webui_enabled is True
                    assert plugin.webui_base_path == "/plugins/vpn/wireguard"
                    assert plugin.name == "wireguard"
                    assert plugin.category == "vpn"


def mock_open(read_data=''):
    """Helper to create a mock file open."""
    import io
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=io.StringIO(read_data))
    mock.__exit__ = MagicMock(return_value=None)
    return MagicMock(return_value=mock)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
