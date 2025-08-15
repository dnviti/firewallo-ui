# Plugin Menu System Documentation

## Overview

The Firewallo UI implements a hierarchical menu system that automatically organizes plugins by category in the navigation sidebar. This system follows the plugin naming convention to create intuitive, organized menus.

## Menu Structure

### Hierarchical Organization

The menu system organizes plugins using a two-level hierarchy:

1. **Category Sections**: Top-level groupings (e.g., "VPN", "Firewall", "Monitoring")
2. **Plugin Entries**: Individual plugins within each category (e.g., "Wireguard", "IPTables")

### Plugin Naming Convention

Plugin names follow the structure: `{category}.{plugin_name}`

**Examples**:
- `vpn.wireguard` → **VPN** section → **Wireguard** entry
- `firewall.iptables` → **Firewall** section → **IPTables** entry
- `monitoring.netdata` → **Monitoring** section → **NetData** entry

## Category Configuration

### Supported Categories

| Category | Display Name | Icon | Position | Description |
|----------|--------------|------|----------|-------------|
| `vpn` | VPN | shield-lock | 10 | Virtual Private Network services |
| `firewall` | Firewall | shield-shaded | 20 | Firewall rules and protection |
| `monitoring` | Monitoring | activity | 30 | System and network monitoring |
| `network` | Network | diagram-3 | 40 | Network configuration and management |
| `security` | Security | shield-check | 50 | Security tools and services |
| `backup` | Backup | download | 60 | Backup and restore services |
| `system` | System | cpu | 70 | System administration tools |
| `logs` | Logs | file-text | 80 | Log management and analysis |
| `other` | Other | puzzle | 999 | Miscellaneous plugins |

### Adding New Categories

To add a new category, update the `CATEGORY_CONFIG` in `app/plugins/base/menu_utils.py`:

```python
CATEGORY_CONFIG = {
    "newcategory": {
        "display_name": "New Category",
        "icon": "icon-name",
        "position": 45,
        "description": "Description of the category"
    }
}
```

## Plugin Menu Configuration

### Manifest Configuration

Configure your plugin's menu entry in the `manifest.json` file:

```json
{
  "name": "wireguard",
  "category": "vpn",
  "webui": {
    "enabled": true,
    "menu_entry": {
      "title": "Wireguard",
      "icon": "bi-shield-lock",
      "position": 10,
      "permissions": ["vpn.wireguard.view"]
    },
    "routes": {
      "base_path": "/plugins/vpn/wireguard"
    }
  }
}
```

### Configuration Options

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `title` | string | No | Display name in menu | "Wireguard" |
| `icon` | string | No | Bootstrap icon class | "bi-shield-lock" |
| `position` | integer | No | Sort order within category | 10 |
| `permissions` | array | No | Required permissions | ["vpn.wireguard.view"] |

### Best Practices

1. **Titles**: Use concise, descriptive names
   - ✅ Good: "Wireguard", "IPTables", "NetData"
   - ❌ Bad: "WireGuard VPN Manager", "Advanced IPTables Configuration"

2. **Icons**: Choose relevant Bootstrap Icons
   - VPN plugins: `bi-shield-lock`, `bi-shield-plus`
   - Firewall plugins: `bi-shield-shaded`, `bi-shield-x`
   - Monitoring plugins: `bi-activity`, `bi-graph-up`

3. **Positions**: Use increments of 10 for easy reordering
   - Primary plugins: 10, 20, 30
   - Secondary plugins: 15, 25, 35

## Menu System Implementation

### MenuHelper Class

The `MenuHelper` class provides utilities for menu management:

```python
from app.plugins.base import MenuHelper

# Parse plugin name structure
menu_id, category_display, plugin_display = MenuHelper.parse_plugin_name('wireguard', 'vpn')
# Returns: ('vpn_wireguard', 'VPN', 'Wireguard')

# Create standardized menu entry
menu_entry = MenuHelper.create_standard_menu_entry(
    plugin_name='wireguard',
    category='vpn',
    custom_config={'icon': 'bi-shield-plus'}
)

# Get category configuration
category_config = MenuHelper.get_category_config('vpn')

# Validate menu entry
is_valid, errors = MenuHelper.validate_menu_entry(menu_entry)
```

### MenuService Class

The `MenuService` manages menu registration and organization:

```python
from app.plugins.system.webui.services import MenuService

# Get categorized menu entries
categorized_menus = await MenuService.get_categorized_menu_entries(user_permissions)

# Structure:
# {
#   "vpn": {
#     "display_name": "VPN",
#     "icon": "shield-lock",
#     "entries": [list of VPN plugin entries]
#   }
# }
```

### Automatic Menu Registration

When a plugin is loaded, the BasePlugin class automatically:

1. Parses the plugin name structure
2. Generates appropriate menu ID and title
3. Registers the menu entry with proper categorization
4. Applies permission filtering

```python
# Automatic registration in BasePlugin
async def register_menu_entry(self) -> bool:
    # Uses MenuHelper for standardized structure
    menu_entry = MenuHelper.create_standard_menu_entry(
        self.name,
        self.category,
        manifest_config
    )
    
    return await MenuService.register_plugin_menu(menu_entry)
```

## Dynamic Menu Updates

### Badge Management

Add notification badges to menu entries:

```python
# Add badge with count
await self.update_menu_badge(count=5, style="danger")

# Remove badge
await self.update_menu_badge(count=None)

# Badge styles: primary, secondary, success, danger, warning, info, light, dark
```

### Visibility Control

Show or hide menu entries dynamically:

```python
# Hide menu entry
await self.set_menu_visibility(visible=False)

# Show menu entry
await self.set_menu_visibility(visible=True)
```

### Title Updates

Update menu titles dynamically (useful for status indicators):

```python
# Update title with status
await self.update_menu_title("Wireguard (3 tunnels)")

# Reset to original title
await self.update_menu_title("Wireguard")
```

## Template Integration

### Template Context

The menu system provides categorized menu data to templates:

```python
# In route handlers
nav_context = await get_navigation_context(current_user)
context.update(nav_context)

# Available in templates:
# - categorized_plugin_menus: Dict of categories with entries
# - navigation: List of main navigation items
# - user_menu: User dropdown menu items
```

### Template Rendering

In your templates, the categorized menus are automatically rendered:

```html
<!-- Categorized Plugin Menu Sections -->
{% if categorized_plugin_menus %}
  {% for category, category_info in categorized_plugin_menus.items() %}
    {% if category_info.entries %}
      <h6 class="sidebar-heading px-3 mt-4 mb-1 text-muted">
        <span>
          <i class="bi bi-{{ category_info.icon }} me-1"></i>
          {{ category_info.display_name }}
        </span>
      </h6>
      <ul class="nav flex-column mb-2">
        {% for entry in category_info.entries %}
          <li class="nav-item">
            <a class="nav-link" href="{{ entry.url }}">
              <i class="bi bi-{{ entry.icon }} me-2"></i>
              {{ entry.title }}
              {% if entry.badge %}
                <span class="badge bg-{{ entry.badge.style }} ms-auto">
                  {{ entry.badge.count }}
                </span>
              {% endif %}
            </a>
          </li>
        {% endfor %}
      </ul>
    {% endif %}
  {% endfor %}
{% endif %}
```

## Permission System Integration

### Permission-Based Filtering

Menu entries are automatically filtered based on user permissions:

```python
# In MenuService.get_categorized_menu_entries()
if user_permissions is not None:
    required_perms = entry.get("permissions", [])
    if required_perms:
        # Check if user has at least one required permission
        if not any(perm in user_permissions for perm in required_perms):
            continue  # Skip this menu entry
```

### Permission Patterns

Recommended permission patterns:

- **View Access**: `{category}.{plugin}.view`
- **Configuration**: `{category}.{plugin}.config`
- **Administration**: `{category}.{plugin}.admin`

**Examples**:
- `vpn.wireguard.view` - View WireGuard interface
- `vpn.wireguard.config` - Configure WireGuard servers
- `firewall.iptables.admin` - Full IPTables administration

## Development Examples

### Example 1: VPN Plugin

```json
{
  "name": "openvpn",
  "category": "vpn",
  "webui": {
    "enabled": true,
    "menu_entry": {
      "title": "OpenVPN",
      "icon": "bi-shield-plus",
      "position": 20,
      "permissions": ["vpn.openvpn.view"]
    }
  }
}
```

**Result**: Menu appears under "VPN" section as "OpenVPN"

### Example 2: Monitoring Plugin

```json
{
  "name": "prometheus",
  "category": "monitoring",
  "webui": {
    "enabled": true,
    "menu_entry": {
      "title": "Prometheus",
      "icon": "bi-graph-up",
      "position": 15,
      "permissions": ["monitoring.prometheus.view"]
    }
  }
}
```

**Result**: Menu appears under "Monitoring" section as "Prometheus"

### Example 3: Custom Category Plugin

```json
{
  "name": "custom-tool",
  "category": "other",
  "webui": {
    "enabled": true,
    "menu_entry": {
      "title": "Custom Tool",
      "icon": "bi-wrench",
      "position": 10,
      "permissions": ["other.custom-tool.view"]
    }
  }
}
```

**Result**: Menu appears under "Other" section as "Custom Tool"

## Migration Guide

### Updating Existing Plugins

If you have existing plugins with menu entries, update them to follow the new structure:

**Old Structure**:
```json
{
  "webui": {
    "menu_entry": {
      "title": "WireGuard VPN Manager",
      "category": "plugins"
    }
  }
}
```

**New Structure**:
```json
{
  "webui": {
    "menu_entry": {
      "title": "Wireguard",
      "icon": "bi-shield-lock",
      "position": 10
    }
  }
}
```

The category is automatically determined from the plugin's directory structure and `category` field in the manifest.

## Troubleshooting

### Common Issues

1. **Menu Not Appearing**
   - Check plugin is properly loaded
   - Verify `webui.enabled` is `true` in manifest
   - Check user has required permissions

2. **Wrong Category**
   - Verify `category` field in manifest.json
   - Ensure category directory structure matches

3. **Icon Not Showing**
   - Use proper Bootstrap Icons format (`bi-icon-name`)
   - Check icon exists in Bootstrap Icons library

### Debug Endpoints

Use these endpoints for debugging menu issues:

- `/debug-menu-service` - Debug MenuService state
- `/debug-menu-permissions` - Test permission filtering
- `/debug-nav-context-permissions` - Test navigation context

### Logging

Enable debug logging to troubleshoot menu registration:

```python
# In your plugin
self.logger.debug(f"Registering menu entry: {menu_entry}")
```

## Future Enhancements

### Planned Features

1. **Nested Categories**: Support for sub-categories (e.g., `vpn.client.wireguard`)
2. **Menu Search**: Search functionality within menu categories
3. **Custom Ordering**: User-customizable menu order
4. **Menu Themes**: Category-specific styling and themes
5. **Quick Actions**: Context menus with quick actions

### API Extensions

Future MenuService API extensions:

- `get_menu_tree()` - Get complete hierarchical menu structure
- `bulk_register_menus()` - Register multiple menu entries at once
- `get_menu_analytics()` - Get usage statistics for menu entries
- `export_menu_config()` - Export menu configuration for backup

## Best Practices Summary

1. **Follow Naming Convention**: Use `{category}.{plugin_name}` structure
2. **Use Appropriate Categories**: Choose the most relevant category from the supported list
3. **Keep Titles Concise**: Use short, descriptive menu titles
4. **Choose Relevant Icons**: Select Bootstrap Icons that represent the plugin's function
5. **Set Proper Permissions**: Use the recommended permission pattern
6. **Test Menu Integration**: Verify menu appears correctly with different user permissions
7. **Update Documentation**: Document any custom menu behavior in your plugin's docs

## Migration Checklist

When updating existing plugins to use the new menu system:

- [ ] Update manifest.json with proper `category` field
- [ ] Simplify menu title to just the plugin name
- [ ] Add appropriate Bootstrap Icon
- [ ] Set position within category (use increments of 10)
- [ ] Define proper permissions following the pattern
- [ ] Test menu appearance with different user roles
- [ ] Update plugin documentation with menu structure
- [ ] Verify menu works after plugin reload