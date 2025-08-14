"""Base classes and interfaces for the Firewallo Plugin Framework."""

from .plugin import BasePlugin
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

__all__ = [
    # Base plugin class
    "BasePlugin",

    # Base repository
    "BaseRepository",

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
