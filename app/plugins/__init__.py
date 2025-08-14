"""Firewallo Plugin Framework.

This package provides a comprehensive plugin system for Firewallo, supporting
multiple plugin categories including VPN, firewall, monitoring, network tools,
and security features.

The framework includes:
- Base plugin classes and interfaces
- Plugin management and lifecycle
- Security validation and permissions
- Dynamic loading and hot-reloading
- Category-specific interfaces
"""

from .base import (
    BasePlugin,
    PluginError,
    PluginLoadError,
    PluginInitializationError,
    PluginConfigurationError,
    PluginNotFoundError,
    PluginAlreadyLoadedError,
    PluginNotLoadedError,
    VPNPluginError,
)

from .registry import (
    PluginManager,
    plugin_manager,
    PluginLoader,
    PluginValidator,
)

from .categories import (
    VPNPluginInterface,
    VPNServerCreate,
    VPNServerResponse,
    VPNClientCreate,
    VPNClientResponse,
    VPNConfigResponse,
    VPNConnectionStatus,
)

# Global plugin manager instance for easy access
manager = plugin_manager

__all__ = [
    # Core plugin framework
    "BasePlugin",
    "PluginManager",
    "manager",
    "plugin_manager",

    # Plugin utilities
    "PluginLoader",
    "PluginValidator",

    # Core exceptions
    "PluginError",
    "PluginLoadError",
    "PluginInitializationError",
    "PluginConfigurationError",
    "PluginNotFoundError",
    "PluginAlreadyLoadedError",
    "PluginNotLoadedError",
    "VPNPluginError",

    # VPN plugin interface
    "VPNPluginInterface",
    "VPNServerCreate",
    "VPNServerResponse",
    "VPNClientCreate",
    "VPNClientResponse",
    "VPNConfigResponse",
    "VPNConnectionStatus",
]

# Plugin framework version
__version__ = "1.0.0"
