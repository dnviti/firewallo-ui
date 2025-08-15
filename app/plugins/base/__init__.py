"""Base classes and interfaces for the Firewallo Plugin Framework."""

from .plugin import BasePlugin
from .menu_utils import MenuHelper
from .exceptions import (
    PluginError,
    PluginLoadError,
    PluginInitializationError,
    PluginConfigurationError,
    PluginPermissionError,
    PluginDependencyError,
    PluginValidationError,
    PluginManifestError,
    PluginNotFoundError,
    PluginAlreadyLoadedError,
    PluginNotLoadedError,
    PluginRuntimeError,
    PluginShutdownError,
    PluginAPIError,
    PluginDatabaseError,
    PluginSecurityError,
    PluginVersionError,
    VPNPluginError,
    FirewallPluginError,
    MonitoringPluginError,
    NetworkPluginError,
    SecurityPluginError,
)
from .interfaces import (
    PluginInterface,
    ConfigurableInterface,
    HealthCheckInterface,
    APIProviderInterface,
    DatabaseInterface,
    LifecycleInterface,
    CRUDInterface,
    RepositoryInterface,
    EventInterface,
    ValidationInterface,
    LoggingInterface,
    SecurityInterface,
    MonitoringInterface,
    BackupInterface,
    ScheduledInterface,
    NetworkInterface,
    PluginInfo,
    PluginHealth,
    PluginMetrics,
    PluginConfig,
    PluginEvent,
)
from .repository import BaseRepository

# Menu utilities
from .menu_utils import (
    MenuHelper,
    get_menu_helper,
    parse_plugin_name,
    create_menu_entry,
    suggest_structure,
)

__all__ = [
    # Base plugin class
    "BasePlugin",

    # Base repository
    "BaseRepository",

    # Menu utilities
    "MenuHelper",
    "get_menu_helper",
    "parse_plugin_name",
    "create_menu_entry",
    "suggest_structure",

    # Core exceptions
    "PluginError",
    "PluginLoadError",
    "PluginInitializationError",
    "PluginConfigurationError",
    "PluginPermissionError",
    "PluginDependencyError",
    "PluginValidationError",
    "PluginManifestError",
    "PluginNotFoundError",
    "PluginAlreadyLoadedError",
    "PluginNotLoadedError",
    "PluginRuntimeError",
    "PluginShutdownError",
    "PluginAPIError",
    "PluginDatabaseError",
    "PluginSecurityError",
    "PluginVersionError",

    # Category-specific exceptions
    "VPNPluginError",
    "FirewallPluginError",
    "MonitoringPluginError",
    "NetworkPluginError",
    "SecurityPluginError",

    # Core interfaces
    "PluginInterface",
    "ConfigurableInterface",
    "HealthCheckInterface",
    "APIProviderInterface",
    "DatabaseInterface",
    "LifecycleInterface",
    "CRUDInterface",
    "RepositoryInterface",
    "EventInterface",
    "ValidationInterface",
    "LoggingInterface",
    "SecurityInterface",
    "MonitoringInterface",
    "BackupInterface",
    "ScheduledInterface",
    "NetworkInterface",

    # Data models
    "PluginInfo",
    "PluginHealth",
    "PluginMetrics",
    "PluginConfig",
    "PluginEvent",
]
