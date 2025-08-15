"""Menu utilities for the Firewallo Plugin Framework.

This module provides utility functions and helpers for managing plugin menus
and navigation in the Firewallo UI system.
"""

from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class MenuHelper:
    """Helper class for plugin menu management."""

    # Standard category configurations
    CATEGORY_CONFIG = {
        "vpn": {
            "display_name": "VPN",
            "icon": "shield-lock",
            "position": 10,
            "description": "Virtual Private Network services"
        },
        "firewall": {
            "display_name": "Firewall",
            "icon": "shield-shaded",
            "position": 20,
            "description": "Firewall rules and protection"
        },
        "monitoring": {
            "display_name": "Monitoring",
            "icon": "activity",
            "position": 30,
            "description": "System and network monitoring"
        },
        "network": {
            "display_name": "Network",
            "icon": "diagram-3",
            "position": 40,
            "description": "Network configuration and management"
        },
        "security": {
            "display_name": "Security",
            "icon": "shield-check",
            "position": 50,
            "description": "Security tools and services"
        },
        "backup": {
            "display_name": "Backup",
            "icon": "download",
            "position": 60,
            "description": "Backup and restore services"
        },
        "system": {
            "display_name": "System",
            "icon": "cpu",
            "position": 70,
            "description": "System administration tools"
        },
        "logs": {
            "display_name": "Logs",
            "icon": "file-text",
            "position": 80,
            "description": "Log management and analysis"
        },
        "other": {
            "display_name": "Other",
            "icon": "puzzle",
            "position": 999,
            "description": "Miscellaneous plugins"
        }
    }

    @staticmethod
    def parse_plugin_name(plugin_name: str, category: str) -> Tuple[str, str, str]:
        """Parse plugin name structure to extract components.

        Plugin naming convention: {category}.{plugin_name}
        Example: 'vpn.wireguard' -> category='vpn', name='wireguard'

        Args:
            plugin_name: Full plugin name (e.g., 'wireguard' or 'vpn.wireguard')
            category: Plugin category (e.g., 'vpn')

        Returns:
            tuple: (menu_id, category_display_name, plugin_display_name)

        Examples:
            >>> MenuHelper.parse_plugin_name('wireguard', 'vpn')
            ('vpn_wireguard', 'VPN', 'Wireguard')

            >>> MenuHelper.parse_plugin_name('iptables.advanced', 'firewall')
            ('firewall_iptables.advanced', 'Firewall', 'Advanced')
        """
        # Generate menu ID
        menu_id = f"{category}_{plugin_name}"

        # Get category display name
        category_config = MenuHelper.CATEGORY_CONFIG.get(category, MenuHelper.CATEGORY_CONFIG["other"])
        category_display = category_config["display_name"]

        # Extract plugin display name (last part after dot if present)
        if '.' in plugin_name:
            plugin_display = plugin_name.split('.')[-1].title()
        else:
            plugin_display = plugin_name.title()

        return menu_id, category_display, plugin_display

    @staticmethod
    def get_category_config(category: str) -> Dict[str, Any]:
        """Get configuration for a specific category.

        Args:
            category: Category name (e.g., 'vpn', 'firewall')

        Returns:
            Dict containing category configuration
        """
        return MenuHelper.CATEGORY_CONFIG.get(category, MenuHelper.CATEGORY_CONFIG["other"]).copy()

    @staticmethod
    def validate_menu_entry(menu_entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a menu entry structure.

        Args:
            menu_entry: Menu entry dictionary to validate

        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ['id', 'title', 'url', 'category']

        for field in required_fields:
            if field not in menu_entry:
                errors.append(f"Missing required field: {field}")

        # Validate category exists
        category = menu_entry.get('category', '')
        if category and category not in MenuHelper.CATEGORY_CONFIG:
            logger.warning(f"Unknown category '{category}', will use 'other' category")

        # Validate icon format
        icon = menu_entry.get('icon', '')
        if icon and not (icon.startswith('bi-') or icon in ['puzzle', 'shield-lock', 'cpu']):
            logger.warning(f"Icon '{icon}' should use Bootstrap Icons format (bi-icon-name)")

        # Validate permissions format
        permissions = menu_entry.get('permissions', [])
        if not isinstance(permissions, list):
            errors.append("Permissions must be a list")

        return len(errors) == 0, errors

    @staticmethod
    def create_standard_menu_entry(
        plugin_name: str,
        category: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized menu entry for a plugin.

        Args:
            plugin_name: Plugin name (e.g., 'wireguard')
            category: Plugin category (e.g., 'vpn')
            custom_config: Optional custom configuration to override defaults

        Returns:
            Dict: Standardized menu entry

        Example:
            >>> entry = MenuHelper.create_standard_menu_entry('wireguard', 'vpn')
            >>> print(entry['id'])  # 'vpn_wireguard'
            >>> print(entry['title'])  # 'Wireguard'
        """
        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name(plugin_name, category)
        category_config = MenuHelper.get_category_config(category)

        # Create base menu entry
        menu_entry = {
            'id': menu_id,
            'title': plugin_display,
            'icon': 'bi-puzzle',  # Default icon
            'url': f'/plugins/{category}/{plugin_name}',
            'category': category,
            'position': 50,  # Default position within category
            'permissions': [f'{category}.{plugin_name}.view'],
            'badge': None,
            'active': True,
            'visible': True,
            'plugin_full_name': f"{category}.{plugin_name}"
        }

        # Apply custom configuration if provided
        if custom_config:
            menu_entry.update(custom_config)

        return menu_entry

    @staticmethod
    def get_menu_hierarchy() -> Dict[str, Dict[str, Any]]:
        """Get the complete menu hierarchy structure.

        Returns:
            Dict: Menu hierarchy with categories sorted by position
        """
        # Sort categories by position
        sorted_categories = sorted(
            MenuHelper.CATEGORY_CONFIG.items(),
            key=lambda x: x[1]['position']
        )

        return {
            category: config.copy()
            for category, config in sorted_categories
        }

    @staticmethod
    def normalize_icon(icon: str) -> str:
        """Normalize icon format to ensure consistency.

        Args:
            icon: Icon string (may or may not have 'bi-' prefix)

        Returns:
            str: Normalized icon with 'bi-' prefix
        """
        if not icon:
            return 'bi-puzzle'

        if icon.startswith('bi-'):
            return icon
        else:
            return f'bi-{icon}'

    @staticmethod
    def get_category_breadcrumbs(category: str, plugin_name: str) -> List[Dict[str, str]]:
        """Generate breadcrumbs for plugin navigation.

        Args:
            category: Plugin category
            plugin_name: Plugin name

        Returns:
            List of breadcrumb items
        """
        _, category_display, plugin_display = MenuHelper.parse_plugin_name(plugin_name, category)

        return [
            {"name": "Home", "url": "/dashboard"},
            {"name": category_display, "url": f"/plugins/category/{category}"},
            {"name": plugin_display, "url": f"/plugins/{category}/{plugin_name}"}
        ]

    @staticmethod
    def suggest_menu_structure(plugin_full_name: str) -> Dict[str, str]:
        """Suggest menu structure based on plugin full name.

        Args:
            plugin_full_name: Full plugin name (e.g., 'vpn.wireguard')

        Returns:
            Dict with suggested structure

        Example:
            >>> MenuHelper.suggest_menu_structure('vpn.wireguard')
            {
                'suggested_category': 'vpn',
                'suggested_name': 'wireguard',
                'menu_section': 'VPN',
                'menu_title': 'Wireguard',
                'menu_id': 'vpn_wireguard'
            }
        """
        if '.' in plugin_full_name:
            parts = plugin_full_name.split('.')
            category = parts[0]
            name = '.'.join(parts[1:])  # Handle nested names like 'iptables.advanced'
        else:
            # If no category in name, suggest 'other'
            category = 'other'
            name = plugin_full_name

        menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name(name, category)

        return {
            'suggested_category': category,
            'suggested_name': name,
            'menu_section': category_display,
            'menu_title': plugin_display,
            'menu_id': menu_id,
            'full_path': f'/plugins/{category}/{name}'
        }


def get_menu_helper() -> MenuHelper:
    """Get MenuHelper instance.

    Returns:
        MenuHelper: Helper instance for menu operations
    """
    return MenuHelper()


# Convenience functions for common operations
def parse_plugin_name(plugin_name: str, category: str) -> Tuple[str, str, str]:
    """Convenience function for parsing plugin names."""
    return MenuHelper.parse_plugin_name(plugin_name, category)


def create_menu_entry(plugin_name: str, category: str, **kwargs) -> Dict[str, Any]:
    """Convenience function for creating menu entries."""
    return MenuHelper.create_standard_menu_entry(plugin_name, category, kwargs)


def suggest_structure(plugin_full_name: str) -> Dict[str, str]:
    """Convenience function for suggesting menu structure."""
    return MenuHelper.suggest_menu_structure(plugin_full_name)
