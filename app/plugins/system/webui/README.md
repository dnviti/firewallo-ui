# Firewallo Web UI Plugin

A modern, responsive Bootstrap-based web interface plugin for the Firewallo firewall management system. This plugin provides a comprehensive dashboard, real-time monitoring, plugin management, and administrative tools through an intuitive web interface.

## Overview

The WebUI plugin transforms your Firewallo system into a fully-featured web-managed firewall solution. Built with Bootstrap 5 and FastAPI, it provides a professional, responsive interface that works seamlessly across desktop and mobile devices.

## Features

### 🎨 Modern User Interface
- **Bootstrap 5 Framework**: Clean, responsive design that adapts to any screen size
- **Dark/Light Theme Support**: Multiple themes with customizable color schemes
- **Real-time Updates**: WebSocket support for live data streaming
- **Mobile-First Design**: Optimized for tablets and smartphones
- **Customizable Dashboard**: Drag-and-drop widgets with personalized layouts

### 📊 Comprehensive Dashboard
- **System Status Monitoring**: Real-time CPU, memory, disk, and network metrics
- **Plugin Management**: Enable, disable, and configure plugins from the web interface
- **Activity Timeline**: Track recent system events and user actions
- **Quick Actions**: Common administrative tasks at your fingertips
- **Interactive Charts**: Visualize system performance over time

### 🔒 Security Features
- **JWT Authentication**: Secure token-based authentication system
- **Session Management**: Automatic session timeout and cleanup
- **CSRF Protection**: Built-in cross-site request forgery protection
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Role-Based Access Control**: Fine-grained permission management

### 🛠️ Administrative Tools
- **Firewall Rule Management**: Create, edit, and delete firewall rules
- **Log Viewer**: Browse and search system logs with filtering
- **Backup & Restore**: Schedule automatic backups and restore configurations
- **User Management**: Add, edit, and manage user accounts
- **System Settings**: Configure system-wide preferences

## Installation

### As a Plugin

The WebUI plugin is automatically available in the Firewallo plugin system. To install:

1. Navigate to the plugin management interface
2. Search for "WebUI" in the system category
3. Click "Install" and then "Enable"

### Manual Installation

```bash
# Navigate to the plugins directory
cd /path/to/firewallo-ui/app/plugins/system/

# Clone or copy the webui plugin
cp -r webui /path/to/firewallo-ui/app/plugins/system/

# Restart the Firewallo service
systemctl restart firewallo
```

## Configuration

### Basic Configuration

The WebUI plugin can be configured through its `manifest.json` file or via the API:

```json
{
  "enabled": true,
  "port": 8080,
  "host": "0.0.0.0",
  "theme": "default",
  "auto_refresh_interval": 60,
  "session_timeout": 3600,
  "enable_notifications": true,
  "enable_dark_mode": false
}
```

### Environment Variables

You can override configuration using environment variables:

```bash
WEBUI_PORT=8080
WEBUI_HOST=0.0.0.0
WEBUI_THEME=dark
WEBUI_SESSION_TIMEOUT=7200
```

### Advanced Configuration

#### Dashboard Widgets

Customize which widgets appear on the dashboard:

```json
{
  "dashboard_widgets": [
    "system_status",
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    "network_traffic",
    "active_plugins",
    "recent_activity",
    "quick_actions"
  ]
}
```

#### Theme Customization

Create custom themes by adding them to the configuration:

```json
{
  "custom_themes": {
    "corporate": {
      "primary_color": "#003366",
      "secondary_color": "#0066cc",
      "background": "#f5f5f5",
      "text": "#333333"
    }
  }
}
```

## Usage

### Accessing the Web Interface

Once the plugin is enabled, access the web interface at:

```
http://your-firewallo-ip:8080
```

Default credentials:
- Username: `admin`
- Password: `admin` (change immediately after first login)

### Navigation

- **Dashboard**: Main overview and system status
- **Plugins**: Manage installed plugins
- **Firewall**: Configure firewall rules and policies
- **Monitoring**: View real-time system metrics
- **Logs**: Browse system and security logs
- **Settings**: Configure system and user preferences

### Keyboard Shortcuts

- `Alt + D`: Go to Dashboard
- `Alt + P`: Go to Plugins
- `Alt + L`: Go to Logs
- `Alt + S`: Go to Settings
- `Ctrl + R`: Refresh current page
- `Ctrl + K`: Open quick search

## API Endpoints

The WebUI plugin exposes several API endpoints:

### Status and Configuration

```bash
# Get plugin status
GET /api/webui/status

# Get configuration
GET /api/webui/config

# Update configuration
POST /api/webui/config
```

### Widget Management

```bash
# Get widget configuration
GET /api/webui/widgets

# Save widget layout
POST /api/webui/widgets
```

### User Preferences

```bash
# Get user preferences
GET /api/webui/preferences/{user_id}

# Update preferences
POST /api/webui/preferences/{user_id}
```

### Metrics and Activity

```bash
# Get metrics
GET /api/webui/metrics

# Get recent activity
GET /api/webui/activity
```

## Development

### Project Structure

```
webui/
├── __init__.py           # Plugin initialization
├── manifest.json         # Plugin manifest and configuration
├── plugin.py            # Main plugin implementation
├── services.py          # Service layer for complex operations
├── README.md           # This file
├── templates/          # Jinja2 HTML templates
│   ├── base.html      # Base template
│   ├── dashboard.html # Dashboard page
│   ├── plugins.html   # Plugin management
│   └── login.html     # Authentication page
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── img/          # Images and icons
└── tests/            # Unit and integration tests
```

### Adding New Pages

1. Create a new template in `templates/`:
```html
<!-- templates/custom_page.html -->
{% extends "base.html" %}
{% block content %}
    <!-- Your content here -->
{% endblock %}
```

2. Add a route in `plugin.py`:
```python
@self.web_router.get("/custom", response_class=HTMLResponse)
async def custom_page(request: Request):
    context = await self._get_template_context(request, "Custom Page")
    return self.templates.TemplateResponse("custom_page.html", context)
```

### Creating Custom Widgets

1. Define widget configuration:
```python
widget = {
    "id": "custom_widget",
    "name": "Custom Widget",
    "size": "medium",
    "refresh_interval": 30,
    "endpoint": "/api/webui/widgets/custom"
}
```

2. Implement widget data endpoint:
```python
@self.api_router.get("/widgets/custom")
async def get_custom_widget_data():
    return {
        "data": "Your widget data",
        "timestamp": datetime.utcnow()
    }
```

### WebSocket Integration

Enable real-time updates using WebSocket:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8080/ws');

// Handle messages
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};

// Send messages
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'metrics'
}));
```

## Testing

### Unit Tests

```bash
# Run unit tests
pytest app/plugins/system/webui/tests/

# Run with coverage
pytest --cov=app.plugins.system.webui
```

### Integration Tests

```bash
# Test API endpoints
python -m pytest tests/test_webui_api.py

# Test WebSocket connections
python -m pytest tests/test_websocket.py
```

### Manual Testing

1. Enable developer mode in settings
2. Use browser developer tools to inspect network requests
3. Test responsive design using device emulation
4. Verify accessibility with screen readers

## Performance Optimization

### Caching

The WebUI plugin implements several caching strategies:

- **Template caching**: Compiled templates are cached in memory
- **Static file caching**: Browser caching headers for static assets
- **API response caching**: Frequently accessed data is cached
- **Session caching**: User sessions are cached in memory

### Compression

Enable compression for better performance:

```json
{
  "enable_compression": true,
  "compression_level": 6
}
```

### Resource Limits

Configure resource limits to prevent abuse:

```json
{
  "max_sessions": 100,
  "max_request_size": "10MB",
  "rate_limit": "100/minute"
}
```

## Troubleshooting

### Common Issues

#### WebUI not accessible

1. Check if the plugin is enabled:
```bash
curl http://localhost:8000/api/plugins/
```

2. Verify port is not blocked:
```bash
netstat -an | grep 8080
```

3. Check logs:
```bash
tail -f /var/log/firewallo/webui.log
```

#### Slow performance

1. Check system resources:
```bash
top
free -h
df -h
```

2. Optimize configuration:
- Increase session timeout
- Reduce auto-refresh interval
- Disable unused widgets

#### Authentication issues

1. Clear browser cookies
2. Reset user password via CLI
3. Check JWT token expiration settings

### Debug Mode

Enable debug mode for detailed logging:

```json
{
  "debug": true,
  "log_level": "DEBUG"
}
```

## Security Considerations

### Best Practices

1. **Change default credentials** immediately after installation
2. **Use HTTPS** in production environments
3. **Enable rate limiting** to prevent brute force attacks
4. **Regular updates** to patch security vulnerabilities
5. **Backup regularly** to prevent data loss

### SSL/TLS Configuration

Enable HTTPS by configuring SSL certificates:

```json
{
  "ssl_enabled": true,
  "ssl_cert": "/path/to/cert.pem",
  "ssl_key": "/path/to/key.pem"
}
```

### Firewall Rules

Ensure proper firewall rules are configured:

```bash
# Allow WebUI port
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Restrict to local network only
iptables -A INPUT -p tcp --dport 8080 -s 192.168.1.0/24 -j ACCEPT
```

## Contributing

We welcome contributions! Please see the main project's CONTRIBUTING.md for guidelines.

### Reporting Issues

Report issues through the GitHub issue tracker with:
- Plugin version
- Browser and OS information
- Steps to reproduce
- Error messages and logs

### Feature Requests

Submit feature requests with:
- Use case description
- Proposed implementation
- Mockups or wireframes (if applicable)

## License

This plugin is part of the Firewallo project and is licensed under the MIT License.

## Support

- **Documentation**: https://docs.firewallo.com/plugins/webui
- **Community Forum**: https://community.firewallo.com
- **Issue Tracker**: https://github.com/firewallo/firewallo-ui/issues
- **Email**: support@firewallo.com

## Changelog

### Version 2.0.0 (Current)
- Complete rewrite as a plugin following framework standards
- Bootstrap 5 upgrade
- WebSocket support for real-time updates
- Enhanced security features
- Improved mobile responsiveness
- Custom theme support
- Widget system implementation
- Backup and restore functionality

### Version 1.0.0
- Initial release
- Basic dashboard functionality
- Plugin management interface
- System monitoring
- User authentication

## Credits

- **Bootstrap**: https://getbootstrap.com
- **FastAPI**: https://fastapi.tiangolo.com
- **Jinja2**: https://jinja.palletsprojects.com
- **Chart.js**: https://www.chartjs.org
- **Bootstrap Icons**: https://icons.getbootstrap.com