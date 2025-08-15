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
- Username: `admin@firewallo.io`
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
    ├── __init__.py   # Test package initialization
    ├── test_plugin.py # Core plugin functionality tests
    ├── test_integration.py # Plugin manager integration tests
    ├── test_api.py   # API endpoint tests
    ├── test_services.py # Service layer tests
    ├── run_tests.py  # Test runner script
    └── pytest.ini   # Pytest configuration
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

### Comprehensive Test Suite

The WebUI plugin includes a dedicated test suite with comprehensive coverage:

```bash
# Navigate to the plugin tests directory
cd app/plugins/system/webui/tests/

# Run all tests with the test runner
python run_tests.py

# Run with verbose output
python run_tests.py -v

# Run with coverage report
python run_tests.py --coverage

# Check test dependencies
python run_tests.py --check-deps
```

### Test Categories

#### Unit Tests (`test_plugin.py`)
- Plugin structure and file validation
- Manifest validation and completeness
- Plugin inheritance and method implementation
- Configuration validation
- Health status reporting
- Plugin lifecycle (initialization/shutdown)

#### Integration Tests (`test_integration.py`)
- Plugin manager integration
- Plugin loading/unloading
- Plugin discovery and validation
- Database schema integration
- Configuration management
- Error handling and recovery
- Performance characteristics

#### API Tests (`test_api.py`)
- Web route functionality
- API endpoint testing
- Request/response validation
- Error handling
- Authentication/authorization
- Input validation
- Performance testing

#### Service Tests (`test_services.py`)
- Template service functionality
- Static file serving
- Session management
- Widget management
- Theme management
- WebSocket management
- Activity logging
- Backup/restore operations
- Metrics collection

### Running Specific Tests

```bash
# Run specific test file
python run_tests.py --test test_plugin.py

# Run specific test function
python run_tests.py --test test_plugin.py --function test_plugin_import

# Run with pytest directly
pytest test_plugin.py -v

# Run specific test class
pytest test_plugin.py::TestWebUIPluginStructure -v
```

### Test Requirements

Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-json-report coverage
```

### Coverage Reports

Generate detailed coverage reports:

```bash
# Run tests with coverage
python run_tests.py --coverage

# View HTML coverage report
open tests/coverage_html/index.html
```

### Manual Testing

1. Enable developer mode in settings
2. Use browser developer tools to inspect network requests
3. Test responsive design using device emulation
4. Verify accessibility with screen readers
5. Test plugin loading/unloading via plugin manager
6. Validate configuration changes take effect
7. Test WebSocket real-time updates

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

### Development Setup

1. **Clone the repository** and navigate to the WebUI plugin
2. **Install dependencies** including test requirements
3. **Run the test suite** to ensure everything works
4. **Make your changes** following plugin framework standards
5. **Add tests** for new functionality
6. **Run tests again** to ensure nothing breaks
7. **Submit a pull request** with clear description

### Adding New Features

When adding new features to the WebUI plugin:

1. **Update the manifest.json** if new permissions or configuration options are needed
2. **Add appropriate routes** in the plugin.py file
3. **Create service classes** in services.py for complex operations
4. **Add comprehensive tests** in the tests/ directory
5. **Update documentation** including this README

### Test Requirements

All new code must include:
- Unit tests for individual functions/methods
- Integration tests for plugin framework interaction
- API tests for new endpoints
- Service tests for new service functionality

### Running Quality Checks

```bash
# Run all tests
python tests/run_tests.py

# Check code coverage (should be > 80%)
python tests/run_tests.py --coverage

# Run linting (if configured)
flake8 plugin.py services.py

# Check type hints (if using mypy)
mypy plugin.py services.py
```

### Reporting Issues

Report issues through the GitHub issue tracker with:
- Plugin version
- Browser and OS information
- Steps to reproduce
- Error messages and logs
- Test results if applicable

### Feature Requests

Submit feature requests with:
- Use case description
- Proposed implementation
- Mockups or wireframes (if applicable)
- Test plan for the new feature

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
