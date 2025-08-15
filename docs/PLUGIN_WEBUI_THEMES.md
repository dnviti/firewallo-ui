# Plugin WebUI Theme Consistency Guide

This document explains how the Firewallo UI theme system ensures consistent theming across all plugin WebUIs, including the WireGuard VPN plugin and any future plugins.

## Overview

The Firewallo UI implements a unified theme system that automatically applies consistent light and dark themes across:
- Main application UI
- System WebUI plugin
- All individual plugin WebUIs (WireGuard, etc.)
- Dynamically loaded content

## Architecture

### Multi-Layer Theme System

The theme system uses a multi-layer approach to ensure consistency:

1. **Base CSS Variables** (`/static/css/custom.css`)
   - Defines core theme variables for light and dark modes
   - Provides fallback values for system preference detection

2. **Plugin Compatibility CSS** (`/static/css/plugin-theme-compat.css`)
   - Ultra-specific overrides for plugin WebUIs
   - Forces theme compliance for stubborn plugin components
   - Emergency overrides for hardcoded styles

3. **Plugin Theme Initialization** (`/static/js/plugin-theme-init.js`)
   - Ensures theme system is available in all plugin contexts
   - Provides fallback theme implementation
   - Handles dynamic content theming

4. **Theme Enforcer** (`/static/js/theme-enforcer.js`)
   - Continuously monitors and fixes theme issues
   - Removes conflicting inline styles
   - Aggressively enforces theme consistency

## Plugin WebUI Integration

### Automatic Integration

All plugin WebUIs automatically inherit theme consistency through:

1. **Template Inheritance**
   ```html
   {% extends "system/webui/templates/base.html" if has_system_base else "base.html" %}
   ```

2. **CSS Inclusion**
   - `custom.css` - Core theme system
   - `plugin-theme-compat.css` - Plugin-specific overrides

3. **JavaScript Inclusion**
   - `common.js` - Core theme API
   - `plugin-theme-init.js` - Plugin theme initialization
   - `theme-enforcer.js` - Aggressive theme enforcement

### Theme Variables Available to Plugins

All plugins have access to the complete set of CSS variables:

#### Core Colors
```css
var(--primary-color)      /* Brand primary color */
var(--secondary-color)    /* Brand secondary color */
var(--success-color)      /* Success states */
var(--danger-color)       /* Error/danger states */
var(--warning-color)      /* Warning states */
var(--info-color)         /* Information states */
```

#### Layout Colors
```css
var(--background-color)   /* Main page background */
var(--body-bg)           /* Body background */
var(--surface-color)     /* Card/panel backgrounds */
var(--surface-secondary) /* Secondary surfaces */
```

#### Text Colors
```css
var(--text-primary)      /* Primary text */
var(--text-secondary)    /* Secondary text */
var(--text-muted)        /* Muted/disabled text */
var(--text-inverse)      /* Inverse text color */
```

#### Component-Specific Colors
```css
var(--navbar-bg)         /* Navigation bar background */
var(--sidebar-bg)        /* Sidebar background */
var(--card-bg)           /* Card backgrounds */
var(--table-bg)          /* Table backgrounds */
var(--input-bg)          /* Form input backgrounds */
var(--modal-bg)          /* Modal backgrounds */
var(--dropdown-bg)       /* Dropdown backgrounds */
```

## Sidebar Theme Consistency

The left sidebar/menu is the most critical component for theme consistency. The system uses ultra-specific CSS selectors to ensure proper theming:

### Sidebar Selectors Covered
```css
.sidebar,
nav.sidebar,
.col-md-3.sidebar,
.col-lg-2.sidebar,
nav.col-md-3,
nav.col-lg-2,
.d-md-block.sidebar
```

### Sidebar Link States
- **Default**: Uses `--sidebar-link-color`
- **Hover**: Uses `--sidebar-link-hover-bg` and `--primary-color`
- **Active**: Uses `--sidebar-link-active-bg` and `--sidebar-link-active-color`

### Plugin-Specific Sidebar Fixes
```css
/* WireGuard specific sidebar fixes */
.sidebar .nav-link[href*="wireguard"],
.sidebar a[href*="wireguard"] {
    background-color: transparent !important;
    color: var(--sidebar-link-color) !important;
}
```

## Plugin Development Guidelines

### For Plugin Developers

1. **Use Template Inheritance**
   ```html
   {% extends "system/webui/templates/base.html" if has_system_base else "base.html" %}
   ```

2. **Use CSS Variables Instead of Hardcoded Colors**
   ```css
   /* ❌ Don't do this */
   .my-component {
       background-color: #f8f9fa;
       color: #333;
   }

   /* ✅ Do this instead */
   .my-component {
       background-color: var(--surface-color);
       color: var(--text-primary);
   }
   ```

3. **Avoid Inline Styles with Colors**
   ```html
   <!-- ❌ Don't do this -->
   <div style="background-color: #fff; color: #333;">Content</div>

   <!-- ✅ Do this instead -->
   <div class="bg-surface text-primary-custom">Content</div>
   ```

4. **Use Theme-Aware Classes**
   ```html
   <!-- Theme-aware utility classes -->
   <div class="bg-surface text-primary-custom">
   <span class="text-muted-custom">
   <button class="btn btn-primary">
   ```

### CSS Best Practices for Plugins

1. **Always Use CSS Variables**
   ```css
   .plugin-component {
       background-color: var(--card-bg);
       border: 1px solid var(--border-color);
       color: var(--text-primary);
   }
   ```

2. **Add Proper Hover States**
   ```css
   .plugin-button:hover {
       background-color: var(--surface-secondary);
       color: var(--primary-color);
   }
   ```

3. **Use Theme-Aware Shadows and Effects**
   ```css
   .plugin-card {
       box-shadow: var(--card-shadow);
       border-radius: var(--border-radius);
   }

   .plugin-card:hover {
       box-shadow: var(--card-shadow-hover);
   }
   ```

## Troubleshooting Plugin Theme Issues

### Common Issues and Solutions

#### 1. Sidebar Menu Not Themed
**Problem**: Plugin sidebar menu items appear with wrong colors
**Solution**: Ensure the template extends the correct base template

#### 2. Tables Not Respecting Theme
**Problem**: Table rows don't change color with theme
**Solution**: Use `table-hover` and `table-striped` classes, avoid custom table CSS

#### 3. Cards Have Wrong Background
**Problem**: Plugin cards show wrong background color
**Solution**: Remove any hardcoded background styles, use CSS variables

#### 4. Forms Don't Match Theme
**Problem**: Form inputs have wrong colors in dark/light mode
**Solution**: Use standard Bootstrap form classes, avoid custom input styling

### Debug Tools

#### 1. Enable Theme Enforcer Debug Mode
```javascript
// In browser console
ThemeEnforcer.enableDebug();
ThemeEnforcer.forceEnforce();
```

#### 2. Check Current Theme
```javascript
// In browser console
console.log('Current theme:', document.documentElement.getAttribute('data-theme'));
console.log('Theme variables:', getComputedStyle(document.documentElement));
```

#### 3. Force Theme Re-application
```javascript
// In browser console
theme.forceThemeUpdate();
```

### Manual Override for Problematic Plugins

If a plugin has persistent theme issues, add this to its template:

```html
<!-- Emergency theme override -->
<style>
.problematic-element {
    background-color: var(--surface-color) !important;
    color: var(--text-primary) !important;
    border-color: var(--border-color) !important;
}
</style>
```

## Testing Plugin Theme Consistency

### Automated Testing
Run the theme consistency tester:
```bash
python test_theme_consistency.py
```

### Manual Testing Checklist

For each plugin WebUI:

1. **Theme Toggle Works**
   - [ ] Theme toggle button is present in navigation
   - [ ] Clicking toggle changes entire plugin UI
   - [ ] Theme preference is persistent across plugin pages

2. **Sidebar Consistency**
   - [ ] Sidebar background matches main UI
   - [ ] Sidebar links have proper hover effects
   - [ ] Active page is properly highlighted
   - [ ] Plugin-specific menu items are themed correctly

3. **Content Area**
   - [ ] Cards have proper background and borders
   - [ ] Tables have proper row colors and hover effects
   - [ ] Forms match the theme colors
   - [ ] Text colors are consistent and readable

4. **Interactive Elements**
   - [ ] Buttons use theme colors
   - [ ] Dropdowns match theme
   - [ ] Modals have proper styling
   - [ ] Alerts and badges are properly colored

### Browser Developer Tools Testing

1. **Inspect Elements**
   - Check that elements use `var(--*)` values
   - Verify no hardcoded colors are applied
   - Ensure CSS variables resolve correctly

2. **Toggle Theme**
   - Watch CSS variables change in real-time
   - Verify smooth transitions
   - Check for any elements that don't update

3. **Check Console**
   - Look for theme-related warnings
   - Verify theme enforcer is running
   - Check for JavaScript errors

## Plugin WebUI File Structure

```
plugin-name/
├── webui/
│   ├── templates/
│   │   ├── system/webui/templates/
│   │   │   └── base.html          # Unified base template
│   │   ├── dashboard.html         # Plugin dashboard
│   │   ├── settings.html          # Plugin settings
│   │   └── *.html                 # Other plugin pages
│   ├── static/                    # Plugin-specific assets (optional)
│   │   ├── css/
│   │   │   └── plugin.css         # Plugin CSS (use theme variables)
│   │   └── js/
│   │       └── plugin.js          # Plugin JS (use theme API)
│   └── routes.py                  # Plugin routes
```

## Migration from Old Plugin UIs

If you have an existing plugin with its own theme implementation:

### Step 1: Update Base Template
```html
<!-- Change from custom base -->
{% extends "my-plugin-base.html" %}

<!-- To unified base -->
{% extends "system/webui/templates/base.html" if has_system_base else "base.html" %}
```

### Step 2: Replace Hardcoded Colors
```css
/* Before */
.my-component {
    background-color: #f8f9fa;
    color: #333;
    border: 1px solid #dee2e6;
}

/* After */
.my-component {
    background-color: var(--surface-color);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}
```

### Step 3: Remove Custom Theme Logic
- Remove any plugin-specific dark/light mode CSS
- Remove custom theme toggle implementations
- Use the unified theme API instead

### Step 4: Test Thoroughly
- Test in both light and dark modes
- Verify all interactive elements work correctly
- Check responsive behavior
- Test theme persistence

## Performance Considerations

### Theme System Performance
- CSS variables provide native browser performance
- Theme changes are instant (no page reload)
- Minimal memory overhead
- Smooth transitions without JavaScript

### Plugin Impact
- Theme enforcer runs for limited time (50 seconds max)
- Uses efficient DOM queries
- Minimal performance impact on plugin functionality
- Automatic cleanup after initial enforcement

## Future Plugin Development

### Required Elements for New Plugins

1. **Base Template Usage**
   ```html
   {% extends "system/webui/templates/base.html" if has_system_base else "base.html" %}
   ```

2. **CSS Variable Usage**
   ```css
   .plugin-specific-class {
       background-color: var(--surface-color);
       color: var(--text-primary);
   }
   ```

3. **No Hardcoded Theme Logic**
   - Don't implement custom dark/light mode detection
   - Don't create plugin-specific theme toggles
   - Trust the unified theme system

4. **Test Coverage**
   - Include theme tests in plugin test suite
   - Verify both light and dark modes
   - Test theme persistence

## Conclusion

The Firewallo UI theme system provides comprehensive, automatic theme consistency across all plugin WebUIs. By following the guidelines in this document, plugin developers can ensure their UIs integrate seamlessly with the main application theme, providing users with a consistent and professional experience regardless of which plugin they're using.

For any theme-related issues or questions, refer to the main `THEME_GUIDE.md` or use the debugging tools provided in the theme enforcer system.