# Firewallo UI Theme System Guide

## Overview

The Firewallo UI now features a comprehensive light/dark theme system that provides a consistent and modern user experience. The theme system automatically adapts to user preferences and system settings while maintaining accessibility and visual appeal.

## Features

- **Automatic Theme Detection**: Respects system preference (light/dark) by default
- **Manual Theme Toggle**: Users can manually switch between light and dark themes
- **Persistent Preferences**: Theme choice is saved in localStorage
- **Smooth Transitions**: All theme changes include smooth CSS transitions
- **Comprehensive Coverage**: All UI components are properly themed
- **Responsive Design**: Themes work seamlessly across all device sizes

## Implementation Details

### CSS Variables Structure

The theme system uses CSS custom properties (variables) organized into logical groups:

#### Core Colors
- `--primary-color`: Main brand color
- `--secondary-color`: Secondary accent color
- `--success-color`: Success states (green)
- `--danger-color`: Error/danger states (red)
- `--warning-color`: Warning states (yellow/orange)
- `--info-color`: Informational states (blue)

#### Background Colors
- `--background-color`: Main page background
- `--body-bg`: Body background
- `--surface-color`: Card/panel backgrounds
- `--surface-secondary`: Secondary surface color

#### Text Colors
- `--text-primary`: Primary text color
- `--text-secondary`: Secondary text color
- `--text-muted`: Muted/disabled text
- `--text-inverse`: Inverse text color

#### Component-Specific Colors
- Navigation, sidebar, cards, forms, tables, modals, and more

### Theme Definitions

#### Light Theme
```css
[data-theme="light"] {
  --primary-color: #667eea;
  --background-color: #ffffff;
  --text-primary: #212529;
  /* ... additional variables */
}
```

#### Dark Theme
```css
[data-theme="dark"] {
  --primary-color: #764ba2;
  --background-color: #1a202c;
  --text-primary: #e2e8f0;
  /* ... additional variables */
}
```

### JavaScript Theme Management

The theme system includes a JavaScript API for programmatic control:

```javascript
// Initialize theme system
theme.init();

// Set specific theme
theme.set('light'); // or 'dark'

// Toggle between themes
theme.toggle();

// Get current theme
const currentTheme = document.documentElement.getAttribute('data-theme');
```

## Usage Guide

### For Users

#### Theme Toggle Button
- Located in the top navigation bar
- Shows moon icon (🌙) in light mode, sun icon (☀️) in dark mode
- Click to instantly switch themes
- Preference is automatically saved

#### Automatic Detection
- On first visit, the theme follows your system preference
- If your system is set to dark mode, the UI will be dark
- If your system is set to light mode, the UI will be light

### For Developers

#### Adding New Components

When creating new components, use the CSS variables instead of hardcoded colors:

```css
.my-component {
  background-color: var(--surface-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}
```

#### Available CSS Variables

**Colors:**
- `var(--primary-color)`
- `var(--secondary-color)`
- `var(--success-color)`
- `var(--danger-color)`
- `var(--warning-color)`
- `var(--info-color)`

**Backgrounds:**
- `var(--background-color)`
- `var(--body-bg)`
- `var(--surface-color)`
- `var(--surface-secondary)`

**Text:**
- `var(--text-primary)`
- `var(--text-secondary)`
- `var(--text-muted)`
- `var(--text-inverse)`

**Borders:**
- `var(--border-color)`
- `var(--border-light)`
- `var(--border-dark)`

**Components:**
- `var(--navbar-bg)`
- `var(--sidebar-bg)`
- `var(--card-bg)`
- `var(--input-bg)`
- `var(--table-bg)`
- `var(--modal-bg)`
- `var(--dropdown-bg)`

#### Custom Theme Integration

To integrate with the theme system in custom JavaScript:

```javascript
// Listen for theme changes
const observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.type === 'attributes' && 
        mutation.attributeName === 'data-theme') {
      // Theme changed, update your component
      updateMyComponent();
    }
  });
});

observer.observe(document.documentElement, {
  attributes: true,
  attributeFilter: ['data-theme']
});
```

## File Structure

```
firewallo-ui/
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── custom.css          # Main theme definitions
│   │   └── js/
│   │       └── common.js           # Theme JavaScript API
│   └── templates/
│       └── base.html               # Theme toggle implementation
└── docs/
    └── THEME_GUIDE.md             # This guide
```

## Technical Specifications

### Browser Support
- Chrome 49+
- Firefox 31+
- Safari 9.1+
- Edge 16+

### Performance
- All theme transitions use CSS transitions for smooth animations
- Theme changes are instant with no page reload required
- Minimal performance impact due to efficient CSS variable usage

### Accessibility
- Maintains proper contrast ratios in both themes
- Respects `prefers-color-scheme` media query
- Keyboard navigation works in both themes
- Screen reader compatibility maintained

## Customization

### Adding New Color Schemes

To add a new theme (e.g., "blue"):

1. Define the theme in CSS:
```css
[data-theme="blue"] {
  --primary-color: #3b82f6;
  --secondary-color: #1e40af;
  /* ... other variables */
}
```

2. Update the JavaScript theme API:
```javascript
// In theme.set() function, add support for 'blue'
theme.set('blue');
```

3. Add UI controls for the new theme option.

### Overriding Specific Components

For component-specific theming:

```css
[data-theme="dark"] .my-special-component {
  background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
  border-radius: var(--border-radius-lg);
}
```

## Troubleshooting

### Theme Not Applying
1. Check if `data-theme` attribute is set on `<html>` element
2. Verify CSS custom properties are defined
3. Ensure JavaScript theme API is loaded

### Flashing on Page Load
- The theme is initialized on `DOMContentLoaded`
- Consider adding theme detection to page `<head>` for faster loading

### Custom Components Not Themed
- Ensure you're using CSS variables instead of hardcoded colors
- Check that your component CSS has appropriate specificity

## Examples

### Button Component
```css
.btn-custom {
  background-color: var(--primary-color);
  color: var(--btn-text);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.btn-custom:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
}
```

### Card Component
```css
.custom-card {
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--border-radius);
  box-shadow: var(--card-shadow);
  color: var(--text-primary);
}

.custom-card-header {
  background-color: var(--card-header-bg);
  border-bottom: 1px solid var(--border-color);
  padding: 1rem;
}
```

### Form Component
```css
.custom-input {
  background-color: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--input-text);
  border-radius: var(--border-radius);
}

.custom-input:focus {
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.custom-input::placeholder {
  color: var(--input-placeholder);
}
```

## Migration from Old System

If you have existing components using the old theme system:

1. **Replace hardcoded colors** with CSS variables
2. **Remove media queries** for dark mode (handled by CSS variables now)
3. **Update JavaScript** to use the new theme API
4. **Test thoroughly** in both light and dark modes

## Best Practices

1. **Always use CSS variables** for colors and spacing
2. **Test in both themes** during development
3. **Respect user preferences** (don't force a specific theme)
4. **Provide visual feedback** for theme changes
5. **Maintain consistency** across all components
6. **Consider accessibility** in color choices

---

For additional support or questions about the theme system, please refer to the project documentation or open an issue on the repository.