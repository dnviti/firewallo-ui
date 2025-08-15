"""Test script for the hierarchical plugin menu system."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the components we're testing
from app.plugins.base.menu_utils import MenuHelper
from app.plugins.system.webui.services import MenuService
from app.plugins.base.plugin import BasePlugin


class TestMenuHelper:
    """Test cases for MenuHelper utility class."""

    def test_parse_plugin_name_simple(self):
        """Test parsing simple plugin names."""
        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name('wireguard', 'vpn')

        assert menu_id == 'vpn_wireguard'
        assert category_display == 'VPN'
        assert plugin_display == 'Wireguard'

    def test_parse_plugin_name_complex(self):
        """Test parsing complex plugin names with dots."""
        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name('iptables.advanced', 'firewall')

        assert menu_id == 'firewall_iptables.advanced'
        assert category_display == 'Firewall'
        assert plugin_display == 'Advanced'

    def test_get_category_config(self):
        """Test getting category configuration."""
        vpn_config = MenuHelper.get_category_config('vpn')

        assert vpn_config['display_name'] == 'VPN'
        assert vpn_config['icon'] == 'shield-lock'
        assert vpn_config['position'] == 10

    def test_get_category_config_unknown(self):
        """Test getting configuration for unknown category."""
        unknown_config = MenuHelper.get_category_config('unknown')

        assert unknown_config['display_name'] == 'Other'
        assert unknown_config['icon'] == 'puzzle'
        assert unknown_config['position'] == 999

    def test_validate_menu_entry_valid(self):
        """Test validation of valid menu entry."""
        menu_entry = {
            'id': 'vpn_wireguard',
            'title': 'Wireguard',
            'url': '/plugins/vpn/wireguard',
            'category': 'vpn',
            'icon': 'bi-shield-lock',
            'permissions': ['vpn.wireguard.view']
        }

        is_valid, errors = MenuHelper.validate_menu_entry(menu_entry)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_menu_entry_missing_fields(self):
        """Test validation of menu entry with missing fields."""
        menu_entry = {
            'id': 'vpn_wireguard',
            'title': 'Wireguard'
            # Missing url and category
        }

        is_valid, errors = MenuHelper.validate_menu_entry(menu_entry)

        assert is_valid is False
        assert 'Missing required field: url' in errors
        assert 'Missing required field: category' in errors

    def test_create_standard_menu_entry(self):
        """Test creation of standard menu entry."""
        menu_entry = MenuHelper.create_standard_menu_entry(
            'wireguard',
            'vpn',
            {'icon': 'bi-shield-plus', 'position': 15}
        )

        assert menu_entry['id'] == 'vpn_wireguard'
        assert menu_entry['title'] == 'Wireguard'
        assert menu_entry['category'] == 'vpn'
        assert menu_entry['icon'] == 'bi-shield-plus'
        assert menu_entry['position'] == 15
        assert menu_entry['url'] == '/plugins/vpn/wireguard'
        assert 'vpn.wireguard.view' in menu_entry['permissions']

    def test_normalize_icon(self):
        """Test icon normalization."""
        assert MenuHelper.normalize_icon('shield-lock') == 'bi-shield-lock'
        assert MenuHelper.normalize_icon('bi-shield-lock') == 'bi-shield-lock'
        assert MenuHelper.normalize_icon('') == 'bi-puzzle'
        assert MenuHelper.normalize_icon(None) == 'bi-puzzle'

    def test_suggest_menu_structure(self):
        """Test menu structure suggestions."""
        suggestion = MenuHelper.suggest_menu_structure('vpn.wireguard')

        assert suggestion['suggested_category'] == 'vpn'
        assert suggestion['suggested_name'] == 'wireguard'
        assert suggestion['menu_section'] == 'VPN'
        assert suggestion['menu_title'] == 'Wireguard'
        assert suggestion['menu_id'] == 'vpn_wireguard'
        assert suggestion['full_path'] == '/plugins/vpn/wireguard'

    def test_suggest_menu_structure_no_category(self):
        """Test menu structure suggestions for names without category."""
        suggestion = MenuHelper.suggest_menu_structure('standalone-tool')

        assert suggestion['suggested_category'] == 'other'
        assert suggestion['suggested_name'] == 'standalone-tool'
        assert suggestion['menu_section'] == 'Other'
        assert suggestion['menu_title'] == 'Standalone-tool'

    def test_get_category_breadcrumbs(self):
        """Test breadcrumb generation."""
        breadcrumbs = MenuHelper.get_category_breadcrumbs('vpn', 'wireguard')

        assert len(breadcrumbs) == 3
        assert breadcrumbs[0]['name'] == 'Home'
        assert breadcrumbs[1]['name'] == 'VPN'
        assert breadcrumbs[2]['name'] == 'Wireguard'


class TestMenuService:
    """Test cases for MenuService class."""

    def setup_method(self):
        """Setup for each test method."""
        # Reset MenuService state
        MenuService._menu_entries = {}
        MenuService._menu_categories = {}
        MenuService._menu_order = []
        MenuService._initialized = False

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test MenuService initialization."""
        with patch('app.plugins.base.BaseRepository') as mock_repo:
            mock_repo.return_value.get_data = AsyncMock(return_value=None)

            await MenuService.initialize()

            assert MenuService._initialized is True

    @pytest.mark.asyncio
    async def test_register_plugin_menu(self):
        """Test plugin menu registration."""
        # Initialize MenuService
        MenuService._initialized = True
        MenuService._repository = Mock()
        MenuService._repository.set_data = AsyncMock()

        menu_entry = {
            'id': 'vpn_wireguard',
            'title': 'Wireguard',
            'category': 'vpn',
            'url': '/plugins/vpn/wireguard',
            'icon': 'bi-shield-lock',
            'position': 10
        }

        result = await MenuService.register_plugin_menu(menu_entry)

        assert result is True
        assert 'vpn_wireguard' in MenuService._menu_entries
        assert 'vpn' in MenuService._menu_categories
        assert 'vpn_wireguard' in MenuService._menu_categories['vpn']

    @pytest.mark.asyncio
    async def test_get_categorized_menu_entries(self):
        """Test getting categorized menu entries."""
        # Setup test data
        MenuService._initialized = True
        MenuService._menu_entries = {
            'vpn_wireguard': {
                'id': 'vpn_wireguard',
                'title': 'Wireguard',
                'category': 'vpn',
                'url': '/plugins/vpn/wireguard',
                'icon': 'bi-shield-lock',
                'position': 10,
                'permissions': ['vpn.wireguard.view'],
                'visible': True,
                'active': True
            },
            'firewall_iptables': {
                'id': 'firewall_iptables',
                'title': 'IPTables',
                'category': 'firewall',
                'url': '/plugins/firewall/iptables',
                'icon': 'bi-shield-shaded',
                'position': 10,
                'permissions': ['firewall.iptables.view'],
                'visible': True,
                'active': True
            }
        }
        MenuService._menu_categories = {
            'vpn': ['vpn_wireguard'],
            'firewall': ['firewall_iptables']
        }

        # Test with admin permissions
        admin_permissions = ['vpn.wireguard.view', 'firewall.iptables.view']
        categorized = await MenuService.get_categorized_menu_entries(admin_permissions)

        assert 'vpn' in categorized
        assert 'firewall' in categorized
        assert categorized['vpn']['display_name'] == 'VPN'
        assert len(categorized['vpn']['entries']) == 1
        assert categorized['vpn']['entries'][0]['title'] == 'Wireguard'

    @pytest.mark.asyncio
    async def test_permission_filtering(self):
        """Test menu filtering based on permissions."""
        # Setup test data
        MenuService._initialized = True
        MenuService._menu_entries = {
            'vpn_wireguard': {
                'id': 'vpn_wireguard',
                'title': 'Wireguard',
                'category': 'vpn',
                'permissions': ['vpn.wireguard.view'],
                'visible': True,
                'active': True
            }
        }

        # Test with no permissions
        entries = await MenuService.get_menu_entries([])
        assert len(entries) == 0

        # Test with correct permissions
        entries = await MenuService.get_menu_entries(['vpn.wireguard.view'])
        assert len(entries) == 1

        # Test with superuser (None permissions)
        entries = await MenuService.get_menu_entries(None)
        assert len(entries) == 1


class TestPluginMenuIntegration:
    """Test integration between plugins and menu system."""

    def test_plugin_name_parsing(self):
        """Test plugin name parsing in BasePlugin context."""
        # Mock plugin with proper structure
        plugin = Mock()
        plugin.name = 'wireguard'
        plugin.category = 'vpn'

        # Test the parsing methods would work
        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name(
            plugin.name, plugin.category
        )

        assert menu_id == 'vpn_wireguard'
        assert category_display == 'VPN'
        assert plugin_display == 'Wireguard'

    def test_complex_plugin_name_parsing(self):
        """Test parsing complex plugin names."""
        plugin = Mock()
        plugin.name = 'iptables.advanced'
        plugin.category = 'firewall'

        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name(
            plugin.name, plugin.category
        )

        assert menu_id == 'firewall_iptables.advanced'
        assert category_display == 'Firewall'
        assert plugin_display == 'Advanced'

    @pytest.mark.asyncio
    async def test_menu_registration_flow(self):
        """Test the complete menu registration flow."""
        # Mock MenuService
        with patch('app.plugins.system.webui.services.MenuService') as mock_service:
            mock_service.register_plugin_menu = AsyncMock(return_value=True)

            # Create mock plugin
            plugin = Mock()
            plugin.name = 'wireguard'
            plugin.category = 'vpn'
            plugin.enabled = True
            plugin.webui_enabled = True
            plugin.menu_entry_registered = False
            plugin.webui_base_path = '/plugins/vpn/wireguard'
            plugin.manifest = {
                'webui': {
                    'menu_entry': {
                        'title': 'Wireguard',
                        'icon': 'bi-shield-lock',
                        'position': 10,
                        'permissions': ['vpn.wireguard.view']
                    }
                }
            }
            plugin.logger = Mock()

            # Test menu registration
            # This would be called by the actual BasePlugin.register_menu_entry()
            menu_entry = MenuHelper.create_standard_menu_entry(
                plugin.name,
                plugin.category,
                plugin.manifest['webui']['menu_entry']
            )

            result = await mock_service.register_plugin_menu(menu_entry)

            assert result is True
            mock_service.register_plugin_menu.assert_called_once()

            # Verify the menu entry structure
            call_args = mock_service.register_plugin_menu.call_args[0][0]
            assert call_args['id'] == 'vpn_wireguard'
            assert call_args['title'] == 'Wireguard'
            assert call_args['category'] == 'vpn'


class TestMenuSystemExamples:
    """Test real-world examples of menu system usage."""

    def test_wireguard_menu_structure(self):
        """Test WireGuard plugin menu structure."""
        menu_entry = MenuHelper.create_standard_menu_entry(
            'wireguard',
            'vpn',
            {
                'title': 'Wireguard',
                'icon': 'bi-shield-lock',
                'position': 10,
                'permissions': ['vpn.wireguard.view']
            }
        )

        # Verify structure follows naming convention
        assert menu_entry['id'] == 'vpn_wireguard'
        assert menu_entry['title'] == 'Wireguard'
        assert menu_entry['category'] == 'vpn'
        assert menu_entry['url'] == '/plugins/vpn/wireguard'
        assert menu_entry['plugin_full_name'] == 'vpn.wireguard'

    def test_multiple_plugins_same_category(self):
        """Test multiple plugins in the same category."""
        # Create entries for multiple VPN plugins
        wireguard_entry = MenuHelper.create_standard_menu_entry('wireguard', 'vpn', {'position': 10})
        openvpn_entry = MenuHelper.create_standard_menu_entry('openvpn', 'vpn', {'position': 20})

        assert wireguard_entry['category'] == 'vpn'
        assert openvpn_entry['category'] == 'vpn'
        assert wireguard_entry['id'] != openvpn_entry['id']
        assert wireguard_entry['position'] < openvpn_entry['position']

    def test_firewall_plugin_example(self):
        """Test firewall plugin menu structure."""
        menu_entry = MenuHelper.create_standard_menu_entry(
            'iptables',
            'firewall',
            {
                'title': 'IPTables',
                'icon': 'bi-shield-shaded',
                'position': 10
            }
        )

        assert menu_entry['id'] == 'firewall_iptables'
        assert menu_entry['title'] == 'IPTables'
        assert menu_entry['category'] == 'firewall'

    def test_monitoring_plugin_example(self):
        """Test monitoring plugin menu structure."""
        menu_entry = MenuHelper.create_standard_menu_entry(
            'netdata',
            'monitoring',
            {
                'title': 'NetData',
                'icon': 'bi-graph-up',
                'position': 15
            }
        )

        assert menu_entry['id'] == 'monitoring_netdata'
        assert menu_entry['title'] == 'NetData'
        assert menu_entry['category'] == 'monitoring'

    def test_suggest_structure_examples(self):
        """Test menu structure suggestions for various plugin names."""
        # Test VPN plugin
        vpn_suggestion = MenuHelper.suggest_menu_structure('vpn.wireguard')
        assert vpn_suggestion['menu_section'] == 'VPN'
        assert vpn_suggestion['menu_title'] == 'Wireguard'

        # Test firewall plugin
        fw_suggestion = MenuHelper.suggest_menu_structure('firewall.iptables')
        assert fw_suggestion['menu_section'] == 'Firewall'
        assert fw_suggestion['menu_title'] == 'Iptables'

        # Test plugin without category
        other_suggestion = MenuHelper.suggest_menu_structure('standalone-tool')
        assert other_suggestion['menu_section'] == 'Other'
        assert other_suggestion['menu_title'] == 'Standalone-tool'


class TestMenuHierarchy:
    """Test menu hierarchy and organization."""

    @pytest.mark.asyncio
    async def test_category_organization(self):
        """Test that plugins are properly organized by category."""
        # Setup MenuService with test data
        MenuService._initialized = True
        MenuService._repository = Mock()
        MenuService._repository.set_data = AsyncMock()

        # Register plugins from different categories
        vpn_entry = MenuHelper.create_standard_menu_entry('wireguard', 'vpn')
        firewall_entry = MenuHelper.create_standard_menu_entry('iptables', 'firewall')
        monitoring_entry = MenuHelper.create_standard_menu_entry('netdata', 'monitoring')

        await MenuService.register_plugin_menu(vpn_entry)
        await MenuService.register_plugin_menu(firewall_entry)
        await MenuService.register_plugin_menu(monitoring_entry)

        # Get categorized entries
        categorized = await MenuService.get_categorized_menu_entries(None)

        # Verify categories exist
        assert 'vpn' in categorized
        assert 'firewall' in categorized
        assert 'monitoring' in categorized

        # Verify category structure
        assert categorized['vpn']['display_name'] == 'VPN'
        assert categorized['firewall']['display_name'] == 'Firewall'
        assert categorized['monitoring']['display_name'] == 'Monitoring'

        # Verify entries within categories
        assert len(categorized['vpn']['entries']) == 1
        assert categorized['vpn']['entries'][0]['title'] == 'Wireguard'

    def test_menu_hierarchy_structure(self):
        """Test the complete menu hierarchy structure."""
        hierarchy = MenuHelper.get_menu_hierarchy()

        # Verify categories are in correct order
        categories = list(hierarchy.keys())
        positions = [hierarchy[cat]['position'] for cat in categories]

        # Positions should be in ascending order
        assert positions == sorted(positions)

        # Verify specific categories exist
        assert 'vpn' in hierarchy
        assert 'firewall' in hierarchy
        assert 'other' in hierarchy


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_wireguard_plugin_complete_flow(self):
        """Test complete flow for WireGuard plugin."""
        # Setup
        MenuService._initialized = True
        MenuService._repository = Mock()
        MenuService._repository.set_data = AsyncMock()

        # Simulate WireGuard plugin manifest
        wireguard_manifest = {
            'name': 'wireguard',
            'category': 'vpn',
            'webui': {
                'enabled': True,
                'menu_entry': {
                    'title': 'Wireguard',
                    'icon': 'bi-shield-lock',
                    'position': 10,
                    'permissions': ['vpn.wireguard.view']
                }
            }
        }

        # Create menu entry as BasePlugin would
        menu_entry = MenuHelper.create_standard_menu_entry(
            wireguard_manifest['name'],
            wireguard_manifest['category'],
            wireguard_manifest['webui']['menu_entry']
        )

        # Register menu
        result = await MenuService.register_plugin_menu(menu_entry)
        assert result is True

        # Verify in categorized view
        categorized = await MenuService.get_categorized_menu_entries(['vpn.wireguard.view'])

        assert 'vpn' in categorized
        assert len(categorized['vpn']['entries']) == 1

        entry = categorized['vpn']['entries'][0]
        assert entry['title'] == 'Wireguard'
        assert entry['id'] == 'vpn_wireguard'

    @pytest.mark.asyncio
    async def test_permission_filtering_realistic(self):
        """Test permission filtering with realistic scenarios."""
        # Setup MenuService with multiple plugins
        MenuService._initialized = True
        MenuService._repository = Mock()
        MenuService._repository.set_data = AsyncMock()

        # Register multiple plugins
        plugins = [
            ('wireguard', 'vpn', ['vpn.wireguard.view']),
            ('openvpn', 'vpn', ['vpn.openvpn.view']),
            ('iptables', 'firewall', ['firewall.iptables.view']),
            ('netdata', 'monitoring', ['monitoring.netdata.view'])
        ]

        for name, category, perms in plugins:
            entry = MenuHelper.create_standard_menu_entry(name, category, {'permissions': perms})
            await MenuService.register_plugin_menu(entry)

        # Test different permission levels

        # 1. User with only WireGuard access
        wg_user_menus = await MenuService.get_categorized_menu_entries(['vpn.wireguard.view'])
        assert 'vpn' in wg_user_menus
        assert len(wg_user_menus['vpn']['entries']) == 1
        assert 'firewall' not in wg_user_menus
        assert 'monitoring' not in wg_user_menus

        # 2. User with VPN access
        vpn_user_menus = await MenuService.get_categorized_menu_entries(['vpn.wireguard.view', 'vpn.openvpn.view'])
        assert 'vpn' in vpn_user_menus
        assert len(vpn_user_menus['vpn']['entries']) == 2

        # 3. Admin user (all permissions)
        admin_menus = await MenuService.get_categorized_menu_entries(None)
        assert len(admin_menus) == 3  # vpn, firewall, monitoring
        assert sum(len(cat['entries']) for cat in admin_menus.values()) == 4


def test_menu_examples():
    """Test various menu configuration examples."""
    examples = [
        # VPN Plugins
        {
            'input': ('wireguard', 'vpn'),
            'expected_section': 'VPN',
            'expected_title': 'Wireguard',
            'expected_id': 'vpn_wireguard'
        },
        {
            'input': ('openvpn', 'vpn'),
            'expected_section': 'VPN',
            'expected_title': 'Openvpn',
            'expected_id': 'vpn_openvpn'
        },

        # Firewall Plugins
        {
            'input': ('iptables', 'firewall'),
            'expected_section': 'Firewall',
            'expected_title': 'Iptables',
            'expected_id': 'firewall_iptables'
        },
        {
            'input': ('ufw', 'firewall'),
            'expected_section': 'Firewall',
            'expected_title': 'Ufw',
            'expected_id': 'firewall_ufw'
        },

        # Monitoring Plugins
        {
            'input': ('prometheus', 'monitoring'),
            'expected_section': 'Monitoring',
            'expected_title': 'Prometheus',
            'expected_id': 'monitoring_prometheus'
        },

        # Complex names
        {
            'input': ('iptables.advanced', 'firewall'),
            'expected_section': 'Firewall',
            'expected_title': 'Advanced',
            'expected_id': 'firewall_iptables.advanced'
        }
    ]

    for example in examples:
        plugin_name, category = example['input']
        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name(plugin_name, category)

        assert category_display == example['expected_section']
        assert plugin_display == example['expected_title']
        assert menu_id == example['expected_id']


if __name__ == "__main__":
    """Run tests manually for debugging."""
    import sys

    print("Testing Menu System...")

    # Test MenuHelper basic functionality
    print("\n1. Testing MenuHelper.parse_plugin_name...")
    menu_id, cat_display, plugin_display = MenuHelper.parse_plugin_name('wireguard', 'vpn')
    print(f"   vpn.wireguard -> Section: '{cat_display}', Entry: '{plugin_display}', ID: '{menu_id}'")

    # Test complex names
    menu_id2, cat_display2, plugin_display2 = MenuHelper.parse_plugin_name('iptables.advanced', 'firewall')
    print(f"   firewall.iptables.advanced -> Section: '{cat_display2}', Entry: '{plugin_display2}', ID: '{menu_id2}'")

    # Test menu entry creation
    print("\n2. Testing menu entry creation...")
    entry = MenuHelper.create_standard_menu_entry('wireguard', 'vpn')
    print(f"   Created entry: {entry}")

    # Test validation
    print("\n3. Testing validation...")
    is_valid, errors = MenuHelper.validate_menu_entry(entry)
    print(f"   Valid: {is_valid}, Errors: {errors}")

    # Test suggestions
    print("\n4. Testing structure suggestions...")
    suggestion = MenuHelper.suggest_menu_structure('vpn.wireguard')
    print(f"   Suggestion for 'vpn.wireguard': {suggestion}")

    print("\n✅ Basic tests completed successfully!")
    print("\nTo run full test suite: pytest app/plugins/tests/test_menu_system.py")
```

Now let's create a practical example by updating an existing plugin to use the new menu system. Let me check the WireGuard plugin:
