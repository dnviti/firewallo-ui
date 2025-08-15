# Plugin Installation Guide

This guide covers the complete plugin installation process for Firewallo, including installation from various sources, dependency management, and troubleshooting.

## Installation Methods

### 1. From Git Repository

Install plugins directly from Git repositories:

```bash
# Install from GitHub
firewallo plugin install https://github.com/developer/myvpn-plugin.git

# Install specific version/tag
firewallo plugin install https://github.com/developer/myvpn-plugin.git@v1.2.0

# Install from specific branch
firewallo plugin install https://github.com/developer/myvpn-plugin.git@feature-branch

# Install from GitLab
firewallo plugin install https://gitlab.com/developer/myvpn-plugin.git

# Install from private repository (with authentication)
firewallo plugin install https://username:token@github.com/private/repo.git
```

### 2. From Local Directory

Install plugins from local development directories:

```bash
# Install from current directory
firewallo plugin install .

# Install from specific path
firewallo plugin install /path/to/plugin/directory

# Install in development mode (symlink)
firewallo plugin install --dev /path/to/plugin/directory
```

### 3. From Package Archive

Install from packaged plugin files:

```bash
# Install from tar.gz file
firewallo plugin install myvpn-plugin-1.0.0.tar.gz

# Install from URL
firewallo plugin install https://releases.example.com/myvpn-plugin-1.0.0.tar.gz

# Install from zip file
firewallo plugin install myvpn-plugin-1.0.0.zip
```

### 4. From Plugin Registry

Install from the official Firewallo plugin registry:

```bash
# Install latest version
firewallo plugin install openvpn

# Install specific version
firewallo plugin install openvpn@1.2.0

# Search for plugins
firewallo plugin search vpn

# Show plugin information
firewallo plugin info openvpn
```

## Installation Options

### Standard Installation

```bash
# Basic installation
firewallo plugin install plugin-name

# Force reinstall
firewallo plugin install --force plugin-name

# Install without dependencies
firewallo plugin install --no-deps plugin-name

# Install with specific configuration
firewallo plugin install --config config.json plugin-name
```

### Development Installation

```bash
# Development mode (symlink, auto-reload)
firewallo plugin install --dev /path/to/plugin

# Install with debug logging
firewallo plugin install --debug plugin-name

# Install with testing dependencies
firewallo plugin install --dev-deps plugin-name
```

### Advanced Options

```bash
# Install to specific location
firewallo plugin install --install-dir /custom/path plugin-name

# Install with environment variables
firewallo plugin install --env CUSTOM_VAR=value plugin-name

# Install with specific Python environment
firewallo plugin install --python /path/to/python plugin-name

# Skip validation checks
firewallo plugin install --skip-validation plugin-name
```

## Dependency Management

### Automatic Dependency Resolution

Firewallo automatically handles plugin dependencies:

```json
{
  "dependencies": {
    "python": ">=3.11,<4.0",
    "packages": [
      "cryptography>=3.4.0",
      "requests>=2.25.0",
      "pydantic>=1.8.0"
    ],
    "system": [
      "openvpn",
      "iptables"
    ],
    "optional": [
      "docker"
    ]
  }
}
```

### Manual Dependency Installation

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install openvpn iptables openssl

# Install system dependencies (CentOS/RHEL)
sudo yum install openvpn iptables openssl

# Install Python dependencies
pip install cryptography requests pydantic

# Install optional dependencies
firewallo plugin install-deps --optional plugin-name
```

### Dependency Conflicts

When dependency conflicts occur:

```bash
# Show dependency tree
firewallo plugin deps plugin-name

# Resolve conflicts interactively
firewallo plugin install --resolve-conflicts plugin-name

# Force installation (bypass conflicts)
firewallo plugin install --force-deps plugin-name

# Use virtual environment
firewallo plugin install --venv plugin-name
```

## Configuration

### Plugin Configuration

Configure plugins during or after installation:

```bash
# Install with configuration file
firewallo plugin install --config config.json plugin-name

# Configure after installation
firewallo plugin configure plugin-name

# Set specific configuration values
firewallo plugin config set plugin-name key=value

# Show current configuration
firewallo plugin config show plugin-name
```

### Configuration File Example

```json
{
  "plugin": "openvpn",
  "config": {
    "server_endpoint": "vpn.example.com",
    "server_port": 1194,
    "encryption": "AES-256-GCM",
    "max_clients": 100,
    "log_level": "info"
  },
  "environment": {
    "OPENVPN_CONFIG_DIR": "/etc/openvpn",
    "OPENVPN_LOG_DIR": "/var/log/openvpn"
  },
  "permissions": {
    "grant_all": false,
    "specific": [
      "network.create",
      "network.modify",
      "file.write"
    ]
  }
}
```

### Environment Variables

```bash
# Plugin-specific environment variables
export FIREWALLO_PLUGIN_OPENVPN_CONFIG_DIR=/etc/openvpn
export FIREWALLO_PLUGIN_OPENVPN_LOG_LEVEL=debug

# Global plugin settings
export FIREWALLO_PLUGIN_AUTO_ENABLE=true
export FIREWALLO_PLUGIN_VALIDATE_SIGNATURES=true
export FIREWALLO_PLUGIN_INSTALL_DIR=/opt/firewallo/plugins
```

## Validation and Security

### Plugin Validation

Firewallo validates plugins before installation:

```bash
# Validate plugin before installation
firewallo plugin validate plugin-source

# Show validation report
firewallo plugin validate --verbose plugin-source

# Skip validation (not recommended)
firewallo plugin install --skip-validation plugin-source
```

### Security Checks

```bash
# Check plugin signatures
firewallo plugin verify plugin-name

# Scan for security vulnerabilities
firewallo plugin security-scan plugin-name

# Check permissions
firewallo plugin permissions plugin-name

# Audit plugin activity
firewallo plugin audit plugin-name
```

### Signature Verification

```bash
# Install with signature verification
firewallo plugin install --verify-signature plugin-name

# Add trusted publisher
firewallo plugin trust-publisher publisher-key

# List trusted publishers
firewallo plugin list-publishers

# Remove trusted publisher
firewallo plugin untrust-publisher publisher-key
```

## Plugin Management

### Listing Plugins

```bash
# List all plugins
firewallo plugin list

# List enabled plugins
firewallo plugin list --enabled

# List plugins by category
firewallo plugin list --category vpn

# Show detailed information
firewallo plugin list --verbose
```

### Plugin Control

```bash
# Enable plugin
firewallo plugin enable plugin-name

# Disable plugin
firewallo plugin disable plugin-name

# Restart plugin
firewallo plugin restart plugin-name

# Check plugin status
firewallo plugin status plugin-name

# Show plugin logs
firewallo plugin logs plugin-name
```

### Plugin Updates

```bash
# Update specific plugin
firewallo plugin update plugin-name

# Update all plugins
firewallo plugin update --all

# Check for updates
firewallo plugin check-updates

# Show update changelog
firewallo plugin changelog plugin-name
```

### Plugin Removal

```bash
# Remove plugin
firewallo plugin remove plugin-name

# Remove with dependencies
firewallo plugin remove --deps plugin-name

# Force removal
firewallo plugin remove --force plugin-name

# Remove and cleanup data
firewallo plugin remove --purge plugin-name
```

## Troubleshooting

### Common Installation Issues

#### 1. Dependency Conflicts

```bash
# Error: Conflicting dependencies
# Solution: Use virtual environment
firewallo plugin install --venv plugin-name

# Or resolve manually
firewallo plugin install --resolve-conflicts plugin-name
```

#### 2. Permission Errors

```bash
# Error: Permission denied
# Solution: Run with appropriate permissions
sudo firewallo plugin install plugin-name

# Or install to user directory
firewallo plugin install --user plugin-name
```

#### 3. Network Issues

```bash
# Error: Failed to download
# Solution: Use proxy or alternative source
firewallo plugin install --proxy http://proxy:8080 plugin-name

# Or install from local file
firewallo plugin install /path/to/plugin.tar.gz
```

#### 4. System Dependencies Missing

```bash
# Error: System dependency not found
# Solution: Install system dependencies first
sudo apt-get install missing-package

# Then retry plugin installation
firewallo plugin install plugin-name
```

### Diagnostic Commands

```bash
# Check system requirements
firewallo system check

# Verify Firewallo installation
firewallo doctor

# Check plugin compatibility
firewallo plugin compat-check plugin-name

# Generate diagnostic report
firewallo plugin diagnose plugin-name
```

### Debug Installation

```bash
# Install with debug output
firewallo plugin install --debug plugin-name

# Show installation logs
firewallo plugin logs --installation plugin-name

# Trace installation steps
firewallo plugin install --trace plugin-name

# Dry run (simulate installation)
firewallo plugin install --dry-run plugin-name
```

### Plugin Recovery

```bash
# Repair corrupted plugin
firewallo plugin repair plugin-name

# Reinstall plugin
firewallo plugin reinstall plugin-name

# Reset plugin to defaults
firewallo plugin reset plugin-name

# Rollback to previous version
firewallo plugin rollback plugin-name
```

## Installation Scripts

### Automated Installation Script

```bash
#!/bin/bash
# install-plugins.sh

set -e

PLUGINS=(
    "wireguard"
    "openvpn@1.2.0"
    "https://github.com/custom/firewall-plugin.git"
    "monitoring-prometheus"
)

echo "Installing Firewallo plugins..."

for plugin in "${PLUGINS[@]}"; do
    echo "Installing $plugin..."
    
    if firewallo plugin install "$plugin"; then
        echo "✓ Successfully installed $plugin"
        firewallo plugin enable "$plugin"
    else
        echo "✗ Failed to install $plugin"
        exit 1
    fi
done

echo "All plugins installed successfully!"

# Configure plugins
echo "Configuring plugins..."
firewallo plugin config set wireguard server_port=51820
firewallo plugin config set openvpn server_port=1194

echo "Plugin installation and configuration complete!"
```

### Docker Installation

```dockerfile
# Dockerfile for Firewallo with plugins
FROM firewallo:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openvpn \
    iptables \
    wireguard-tools \
    && rm -rf /var/lib/apt/lists/*

# Install plugins
COPY plugins.txt /tmp/
RUN while read plugin; do \
        firewallo plugin install "$plugin"; \
    done < /tmp/plugins.txt

# Copy plugin configurations
COPY plugin-configs/ /etc/firewallo/plugins/

# Enable plugins
RUN firewallo plugin enable --all

EXPOSE 8000
CMD ["firewallo", "start"]
```

### Plugin Installation in CI/CD

```yaml
# .github/workflows/install-plugins.yml
name: Install Firewallo Plugins

on:
  push:
    branches: [main]

jobs:
  install-plugins:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Install Firewallo
      run: |
        pip install firewallo
    
    - name: Install plugins
      run: |
        firewallo plugin install wireguard
        firewallo plugin install openvpn
        firewallo plugin install --config config.json monitoring
    
    - name: Validate installation
      run: |
        firewallo plugin list --enabled
        firewallo system check
    
    - name: Run tests
      run: |
        firewallo plugin test --all
```

## Best Practices

### 1. Installation Planning

- Review plugin requirements before installation
- Check compatibility with current Firewallo version
- Plan for dependency conflicts
- Consider resource requirements

### 2. Security

- Always verify plugin signatures when possible
- Review plugin permissions before granting
- Install plugins from trusted sources
- Regularly update plugins for security patches

### 3. Testing

- Test plugins in development environment first
- Validate plugin functionality after installation
- Monitor system performance after plugin installation
- Have rollback plan ready

### 4. Documentation

- Document installed plugins and their configurations
- Keep track of plugin versions
- Document custom configurations
- Maintain installation procedures

### 5. Maintenance

- Regularly update plugins
- Monitor plugin logs for issues
- Remove unused plugins
- Backup plugin configurations

This comprehensive installation guide ensures that users can successfully install, configure, and manage plugins in their Firewallo environment while following security best practices and troubleshooting common issues.
