# Plugin System Documentation

This directory contains comprehensive documentation for Firewallo's extensible plugin framework, which is the core of the platform's flexibility and power.

## 📚 Documentation Contents

### Core Documentation

#### [Plugin Framework](./FRAMEWORK.md)
The foundational documentation covering:
- Plugin architecture and design patterns
- Base classes and interfaces
- Plugin lifecycle management
- Security and validation
- Event system and hooks

#### [Development Guide](./DEVELOPMENT.md)
Complete guide for plugin developers:
- Getting started with plugin development
- Plugin structure and requirements
- API integration patterns
- Best practices and conventions
- Testing and debugging plugins

#### [Plugin Examples](./EXAMPLES.md)
Real-world plugin implementations:
- VPN plugin examples (WireGuard, OpenVPN)
- Firewall plugin examples
- Monitoring plugin examples
- Step-by-step walkthroughs
- Code snippets and templates

### Installation & Management

#### [Installation Guide](./INSTALLATION.md)
How to install and manage plugins:
- Installation methods (Git, registry, local)
- Dependency management
- Configuration options
- Troubleshooting installation issues
- Plugin updates and versioning

#### [Migration Guide](./MIGRATION.md)
Plugin migration strategies:
- Version migration paths
- Data migration patterns
- Backward compatibility
- Migration tools and utilities
- Best practices for migrations

### User Interface Integration

#### [Menu System](./MENU_SYSTEM.md)
Plugin menu integration:
- Menu registration and configuration
- Dynamic menu generation
- Navigation patterns
- Access control for menu items
- Icon and styling guidelines

#### [WebUI Themes](./WEBUI_THEMES.md)
Plugin theming capabilities:
- Theme structure and components
- Custom styling for plugins
- Theme inheritance
- Dark/light mode support
- Responsive design patterns

#### [WebUI Summary](./WEBUI_SUMMARY.md)
Overview of plugin WebUI integration:
- Frontend framework integration
- Component architecture
- State management
- API communication patterns

### Technical Summaries

#### [Framework Integration Summary](./FRAMEWORK_INTEGRATION_SUMMARY.md)
Technical overview of framework integration:
- System integration points
- Hook system details
- Event propagation
- Performance considerations

## 🔌 Plugin Categories

Firewallo supports various plugin categories, each with specific interfaces and capabilities:

### VPN Plugins (`plugins.vpn.*`)
- **Purpose**: VPN server and client management
- **Examples**: WireGuard, OpenVPN, IPSec
- **Key Features**: Connection management, key generation, traffic routing

### Firewall Plugins (`plugins.firewall.*`)
- **Purpose**: Firewall rule and policy management
- **Examples**: iptables, nftables, pfSense
- **Key Features**: Rule creation, chain management, traffic filtering

### Monitoring Plugins (`plugins.monitoring.*`)
- **Purpose**: System and network monitoring
- **Examples**: Prometheus, Grafana, Zabbix
- **Key Features**: Metrics collection, alerting, dashboards

### Network Plugins (`plugins.network.*`)
- **Purpose**: Network service management
- **Examples**: DNS, DHCP, Load Balancer
- **Key Features**: Service configuration, address management, routing

### Security Plugins (`plugins.security.*`)
- **Purpose**: Security tools and intrusion detection
- **Examples**: IDS/IPS, vulnerability scanners
- **Key Features**: Threat detection, security auditing, compliance

## 🚀 Quick Start

### For Plugin Users

1. **Browse Available Plugins**: Check the plugin registry or community repositories
2. **Install a Plugin**: Follow the [Installation Guide](./INSTALLATION.md)
3. **Configure the Plugin**: Use the API or WebUI to configure plugin settings
4. **Manage Plugins**: Enable, disable, or update plugins as needed

### For Plugin Developers

1. **Understand the Framework**: Start with the [Plugin Framework](./FRAMEWORK.md) documentation
2. **Set Up Development Environment**: Follow the [Development Guide](./DEVELOPMENT.md)
3. **Study Examples**: Review [Plugin Examples](./EXAMPLES.md) for patterns and best practices
4. **Build Your Plugin**: Create your plugin following the framework guidelines
5. **Test and Deploy**: Use the testing framework and deployment guides

## 📊 Plugin Architecture Overview

```
Plugin System
├── Plugin Manager
│   ├── Discovery & Loading
│   ├── Dependency Resolution
│   └── Lifecycle Management
├── Plugin Categories
│   ├── VPN Plugins
│   ├── Firewall Plugins
│   ├── Monitoring Plugins
│   └── Network Plugins
├── Plugin Interfaces
│   ├── Base Plugin Class
│   ├── Category Interfaces
│   └── Hook System
└── Plugin Storage
    ├── Configuration
    ├── Data Storage
    └── State Management
```

## 🔧 Plugin Development Workflow

1. **Define Plugin Metadata** - Create plugin.json with plugin information
2. **Implement Base Interface** - Extend appropriate base class
3. **Add Business Logic** - Implement plugin-specific functionality
4. **Create API Endpoints** - Define RESTful API routes
5. **Build UI Components** - Create WebUI elements (optional)
6. **Write Tests** - Add unit and integration tests
7. **Package Plugin** - Create distributable package
8. **Publish** - Share via registry or repository

## 📝 Best Practices

- **Follow Framework Conventions** - Use standard patterns and interfaces
- **Implement Error Handling** - Graceful degradation and clear error messages
- **Document Your Plugin** - Include README and API documentation
- **Version Properly** - Use semantic versioning
- **Test Thoroughly** - Include comprehensive test coverage
- **Consider Security** - Validate inputs and handle permissions

## 🔗 Related Documentation

- [Main Documentation](../INDEX.md) - Platform overview
- [Architecture Documentation](../architecture/) - System design
- [WebUI Documentation](../webui/) - Frontend development
- [Testing Documentation](../testing/) - Testing strategies

## 📚 Additional Resources

- **Plugin Registry**: Browse and discover community plugins
- **Developer Forum**: Get help and share experiences
- **API Reference**: Complete API documentation at `/api/docs`
- **Example Repositories**: Reference implementations on GitLab

## 🤝 Contributing

We welcome plugin contributions! Please:
1. Review the development guidelines
2. Follow coding standards
3. Include tests and documentation
4. Submit via pull request

For more details, see [CONTRIBUTING.md](../../CONTRIBUTING.md).

---

*Need help? Check the [Installation Guide](./INSTALLATION.md) or [Development Guide](./DEVELOPMENT.md) to get started!*