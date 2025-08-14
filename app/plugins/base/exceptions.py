"""Plugin-specific exceptions for the Firewallo Plugin Framework."""

from typing import Optional, Any, Dict


class PluginError(Exception):
    """Base exception for all plugin-related errors."""

    def __init__(self, message: str, plugin_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.plugin_name = plugin_name
        self.details = details or {}
        super().__init__(message)


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginInitializationError(PluginError):
    """Raised when a plugin fails to initialize."""
    pass


class PluginConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""
    pass


class PluginPermissionError(PluginError):
    """Raised when a plugin lacks required permissions."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are not met."""

    def __init__(self, message: str, missing_dependencies: Optional[list] = None, **kwargs):
        self.missing_dependencies = missing_dependencies or []
        super().__init__(message, **kwargs)


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""

    def __init__(self, message: str, validation_errors: Optional[list] = None, **kwargs):
        self.validation_errors = validation_errors or []
        super().__init__(message, **kwargs)


class PluginManifestError(PluginError):
    """Raised when plugin manifest is invalid or missing."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not found."""
    pass


class PluginAlreadyLoadedError(PluginError):
    """Raised when attempting to load an already loaded plugin."""
    pass


class PluginNotLoadedError(PluginError):
    """Raised when attempting to operate on a non-loaded plugin."""
    pass


class PluginRuntimeError(PluginError):
    """Raised when a plugin encounters a runtime error."""
    pass


class PluginShutdownError(PluginError):
    """Raised when a plugin fails to shutdown properly."""
    pass


class PluginAPIError(PluginError):
    """Raised when plugin API operations fail."""

    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        self.status_code = status_code
        super().__init__(message, **kwargs)


class PluginDatabaseError(PluginError):
    """Raised when plugin database operations fail."""
    pass


class PluginSecurityError(PluginError):
    """Raised when plugin security validation fails."""
    pass


class PluginVersionError(PluginError):
    """Raised when plugin version requirements are not met."""

    def __init__(self, message: str, required_version: Optional[str] = None,
                 current_version: Optional[str] = None, **kwargs):
        self.required_version = required_version
        self.current_version = current_version
        super().__init__(message, **kwargs)


# Category-specific exceptions
class VPNPluginError(PluginError):
    """Base exception for VPN plugin errors."""
    pass


class FirewallPluginError(PluginError):
    """Base exception for Firewall plugin errors."""
    pass


class MonitoringPluginError(PluginError):
    """Base exception for Monitoring plugin errors."""
    pass


class NetworkPluginError(PluginError):
    """Base exception for Network plugin errors."""
    pass


class SecurityPluginError(PluginError):
    """Base exception for Security plugin errors."""
    pass
