"""Plugin permission management for the Firewallo Plugin Framework."""

from typing import Set, List, Optional, Callable, Any
from functools import wraps
import logging

from .exceptions import PluginPermissionError


class PluginPermissions:
    """Plugin permission management.

    This class handles permission checking and enforcement for plugins.
    Permissions follow a hierarchical structure: category.resource.action
    """

    # Network permissions
    NETWORK_CREATE = "network.create"
    NETWORK_MODIFY = "network.modify"
    NETWORK_READ = "network.read"
    NETWORK_DELETE = "network.delete"
    NETWORK_ADMIN = "network.admin"

    # File system permissions
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    FILE_EXECUTE = "file.execute"

    # System permissions
    SYSTEM_EXECUTE = "system.execute"
    SYSTEM_READ = "system.read"
    SYSTEM_WRITE = "system.write"
    SYSTEM_ADMIN = "system.admin"
    SYSTEM_REBOOT = "system.reboot"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Database permissions
    DATABASE_READ = "database.read"
    DATABASE_WRITE = "database.write"
    DATABASE_DELETE = "database.delete"
    DATABASE_ADMIN = "database.admin"

    # VPN specific permissions
    VPN_CREATE_SERVER = "vpn.server.create"
    VPN_MODIFY_SERVER = "vpn.server.modify"
    VPN_DELETE_SERVER = "vpn.server.delete"
    VPN_CREATE_CLIENT = "vpn.client.create"
    VPN_MODIFY_CLIENT = "vpn.client.modify"
    VPN_DELETE_CLIENT = "vpn.client.delete"
    VPN_READ = "vpn.read"
    VPN_ADMIN = "vpn.admin"

    # Firewall specific permissions
    FIREWALL_CREATE_RULE = "firewall.rule.create"
    FIREWALL_MODIFY_RULE = "firewall.rule.modify"
    FIREWALL_DELETE_RULE = "firewall.rule.delete"
    FIREWALL_CREATE_ZONE = "firewall.zone.create"
    FIREWALL_MODIFY_ZONE = "firewall.zone.modify"
    FIREWALL_DELETE_ZONE = "firewall.zone.delete"
    FIREWALL_READ = "firewall.read"
    FIREWALL_ADMIN = "firewall.admin"

    # Monitoring specific permissions
    MONITORING_CREATE = "monitoring.create"
    MONITORING_MODIFY = "monitoring.modify"
    MONITORING_DELETE = "monitoring.delete"
    MONITORING_READ = "monitoring.read"
    MONITORING_ADMIN = "monitoring.admin"

    # Security specific permissions
    SECURITY_CREATE_CERT = "security.certificate.create"
    SECURITY_REVOKE_CERT = "security.certificate.revoke"
    SECURITY_CREATE_POLICY = "security.policy.create"
    SECURITY_MODIFY_POLICY = "security.policy.modify"
    SECURITY_DELETE_POLICY = "security.policy.delete"
    SECURITY_SCAN = "security.scan"
    SECURITY_READ = "security.read"
    SECURITY_ADMIN = "security.admin"

    # API permissions
    API_READ = "api.read"
    API_WRITE = "api.write"
    API_DELETE = "api.delete"
    API_ADMIN = "api.admin"

    # UI permissions
    UI_ACCESS = "ui.access"
    UI_MODIFY = "ui.modify"
    UI_ADMIN = "ui.admin"

    # Plugin management permissions
    PLUGIN_INSTALL = "plugin.install"
    PLUGIN_UNINSTALL = "plugin.uninstall"
    PLUGIN_ENABLE = "plugin.enable"
    PLUGIN_DISABLE = "plugin.disable"
    PLUGIN_CONFIG = "plugin.config"
    PLUGIN_ADMIN = "plugin.admin"

    # All available permissions (for validation)
    ALL_PERMISSIONS = {
        # Network
        NETWORK_CREATE, NETWORK_MODIFY, NETWORK_READ, NETWORK_DELETE, NETWORK_ADMIN,
        # File system
        FILE_READ, FILE_WRITE, FILE_DELETE, FILE_EXECUTE,
        # System
        SYSTEM_EXECUTE, SYSTEM_READ, SYSTEM_WRITE, SYSTEM_ADMIN, SYSTEM_REBOOT, SYSTEM_SHUTDOWN,
        # Database
        DATABASE_READ, DATABASE_WRITE, DATABASE_DELETE, DATABASE_ADMIN,
        # VPN
        VPN_CREATE_SERVER, VPN_MODIFY_SERVER, VPN_DELETE_SERVER,
        VPN_CREATE_CLIENT, VPN_MODIFY_CLIENT, VPN_DELETE_CLIENT, VPN_READ, VPN_ADMIN,
        # Firewall
        FIREWALL_CREATE_RULE, FIREWALL_MODIFY_RULE, FIREWALL_DELETE_RULE,
        FIREWALL_CREATE_ZONE, FIREWALL_MODIFY_ZONE, FIREWALL_DELETE_ZONE,
        FIREWALL_READ, FIREWALL_ADMIN,
        # Monitoring
        MONITORING_CREATE, MONITORING_MODIFY, MONITORING_DELETE, MONITORING_READ, MONITORING_ADMIN,
        # Security
        SECURITY_CREATE_CERT, SECURITY_REVOKE_CERT,
        SECURITY_CREATE_POLICY, SECURITY_MODIFY_POLICY, SECURITY_DELETE_POLICY,
        SECURITY_SCAN, SECURITY_READ, SECURITY_ADMIN,
        # API
        API_READ, API_WRITE, API_DELETE, API_ADMIN,
        # UI
        UI_ACCESS, UI_MODIFY, UI_ADMIN,
        # Plugin management
        PLUGIN_INSTALL, PLUGIN_UNINSTALL, PLUGIN_ENABLE, PLUGIN_DISABLE, PLUGIN_CONFIG, PLUGIN_ADMIN,
    }

    # Permission hierarchy for admin permissions
    ADMIN_PERMISSIONS = {
        NETWORK_ADMIN: {NETWORK_CREATE, NETWORK_MODIFY, NETWORK_READ, NETWORK_DELETE},
        SYSTEM_ADMIN: {SYSTEM_EXECUTE, SYSTEM_READ, SYSTEM_WRITE, SYSTEM_REBOOT, SYSTEM_SHUTDOWN},
        DATABASE_ADMIN: {DATABASE_READ, DATABASE_WRITE, DATABASE_DELETE},
        VPN_ADMIN: {VPN_CREATE_SERVER, VPN_MODIFY_SERVER, VPN_DELETE_SERVER,
                    VPN_CREATE_CLIENT, VPN_MODIFY_CLIENT, VPN_DELETE_CLIENT, VPN_READ},
        FIREWALL_ADMIN: {FIREWALL_CREATE_RULE, FIREWALL_MODIFY_RULE, FIREWALL_DELETE_RULE,
                        FIREWALL_CREATE_ZONE, FIREWALL_MODIFY_ZONE, FIREWALL_DELETE_ZONE,
                        FIREWALL_READ},
        MONITORING_ADMIN: {MONITORING_CREATE, MONITORING_MODIFY, MONITORING_DELETE, MONITORING_READ},
        SECURITY_ADMIN: {SECURITY_CREATE_CERT, SECURITY_REVOKE_CERT,
                        SECURITY_CREATE_POLICY, SECURITY_MODIFY_POLICY, SECURITY_DELETE_POLICY,
                        SECURITY_SCAN, SECURITY_READ},
        API_ADMIN: {API_READ, API_WRITE, API_DELETE},
        UI_ADMIN: {UI_ACCESS, UI_MODIFY},
        PLUGIN_ADMIN: {PLUGIN_INSTALL, PLUGIN_UNINSTALL, PLUGIN_ENABLE, PLUGIN_DISABLE, PLUGIN_CONFIG},
    }

    def __init__(self, plugin_name: str, granted_permissions: List[str]):
        """Initialize plugin permissions.

        Args:
            plugin_name: Name of the plugin.
            granted_permissions: List of permissions granted to the plugin.
        """
        self.plugin_name = plugin_name
        self.granted_permissions = self._expand_permissions(granted_permissions)
        self.logger = logging.getLogger(f"firewallo.plugins.{plugin_name}.permissions")

        # Validate permissions
        self._validate_permissions(granted_permissions)

    def _expand_permissions(self, permissions: List[str]) -> Set[str]:
        """Expand admin permissions to include their sub-permissions.

        Args:
            permissions: List of permissions to expand.

        Returns:
            Set of expanded permissions.
        """
        expanded = set(permissions)

        for perm in permissions:
            if perm in self.ADMIN_PERMISSIONS:
                expanded.update(self.ADMIN_PERMISSIONS[perm])

        return expanded

    def _validate_permissions(self, permissions: List[str]) -> None:
        """Validate that all permissions are recognized.

        Args:
            permissions: List of permissions to validate.

        Raises:
            PluginPermissionError: If invalid permissions are found.
        """
        invalid_permissions = [p for p in permissions if p not in self.ALL_PERMISSIONS]
        if invalid_permissions:
            raise PluginPermissionError(
                f"Invalid permissions requested: {invalid_permissions}",
                plugin_name=self.plugin_name
            )

    def has_permission(self, permission: str) -> bool:
        """Check if plugin has specific permission.

        Args:
            permission: Permission to check.

        Returns:
            bool: True if plugin has the permission.
        """
        return permission in self.granted_permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        """Check if plugin has any of the specified permissions.

        Args:
            permissions: List of permissions to check.

        Returns:
            bool: True if plugin has at least one of the permissions.
        """
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Check if plugin has all specified permissions.

        Args:
            permissions: List of permissions to check.

        Returns:
            bool: True if plugin has all the permissions.
        """
        return all(self.has_permission(p) for p in permissions)

    def check_permission(self, permission: str) -> None:
        """Check permission and raise exception if not granted.

        Args:
            permission: Permission to check.

        Raises:
            PluginPermissionError: If permission is not granted.
        """
        if not self.has_permission(permission):
            self.logger.warning(f"Permission denied: {permission}")
            raise PluginPermissionError(
                f"Plugin '{self.plugin_name}' lacks permission: {permission}",
                plugin_name=self.plugin_name,
                details={"required_permission": permission}
            )

    def require_permission(self, permission: str) -> Callable:
        """Decorator to require specific permission for a function.

        Args:
            permission: Permission required to execute the function.

        Returns:
            Decorator function.

        Example:
            @permissions.require_permission(PluginPermissions.NETWORK_CREATE)
            async def create_network_interface(self, ...):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                self.check_permission(permission)
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                self.check_permission(permission)
                return await func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def require_any_permission(self, permissions: List[str]) -> Callable:
        """Decorator to require at least one of the specified permissions.

        Args:
            permissions: List of permissions (at least one required).

        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                if not self.has_any_permission(permissions):
                    raise PluginPermissionError(
                        f"Plugin '{self.plugin_name}' lacks any of required permissions: {permissions}",
                        plugin_name=self.plugin_name,
                        details={"required_permissions": permissions}
                    )
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                if not self.has_any_permission(permissions):
                    raise PluginPermissionError(
                        f"Plugin '{self.plugin_name}' lacks any of required permissions: {permissions}",
                        plugin_name=self.plugin_name,
                        details={"required_permissions": permissions}
                    )
                return await func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def require_all_permissions(self, permissions: List[str]) -> Callable:
        """Decorator to require all specified permissions.

        Args:
            permissions: List of permissions (all required).

        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                for permission in permissions:
                    self.check_permission(permission)
                return func(*args, **kwargs)

            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                for permission in permissions:
                    self.check_permission(permission)
                return await func(*args, **kwargs)

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_granted_permissions(self) -> List[str]:
        """Get list of granted permissions.

        Returns:
            List of permission strings.
        """
        return sorted(list(self.granted_permissions))

    def get_missing_permissions(self, required: List[str]) -> List[str]:
        """Get list of permissions that are required but not granted.

        Args:
            required: List of required permissions.

        Returns:
            List of missing permissions.
        """
        return [p for p in required if not self.has_permission(p)]

    def is_admin(self, category: Optional[str] = None) -> bool:
        """Check if plugin has admin permissions.

        Args:
            category: Optional category to check admin for (e.g., 'network', 'vpn').
                     If None, checks for any admin permission.

        Returns:
            bool: True if plugin has admin permissions.
        """
        if category:
            admin_perm = f"{category}.admin"
            return self.has_permission(admin_perm)
        else:
            # Check for any admin permission
            admin_perms = [p for p in self.ALL_PERMISSIONS if p.endswith('.admin')]
            return self.has_any_permission(admin_perms)

    @classmethod
    def get_permission_description(cls, permission: str) -> str:
        """Get human-readable description of a permission.

        Args:
            permission: Permission string.

        Returns:
            Human-readable description.
        """
        descriptions = {
            cls.NETWORK_CREATE: "Create network interfaces and configurations",
            cls.NETWORK_MODIFY: "Modify existing network configurations",
            cls.NETWORK_READ: "Read network configuration and status",
            cls.NETWORK_DELETE: "Delete network interfaces and configurations",
            cls.NETWORK_ADMIN: "Full network administration access",

            cls.FILE_READ: "Read files from the file system",
            cls.FILE_WRITE: "Write files to the file system",
            cls.FILE_DELETE: "Delete files from the file system",
            cls.FILE_EXECUTE: "Execute files on the system",

            cls.SYSTEM_EXECUTE: "Execute system commands",
            cls.SYSTEM_READ: "Read system information and status",
            cls.SYSTEM_WRITE: "Modify system configuration",
            cls.SYSTEM_ADMIN: "Full system administration access",
            cls.SYSTEM_REBOOT: "Reboot the system",
            cls.SYSTEM_SHUTDOWN: "Shutdown the system",

            cls.DATABASE_READ: "Read from the database",
            cls.DATABASE_WRITE: "Write to the database",
            cls.DATABASE_DELETE: "Delete from the database",
            cls.DATABASE_ADMIN: "Full database administration access",

            cls.VPN_CREATE_SERVER: "Create VPN servers",
            cls.VPN_MODIFY_SERVER: "Modify VPN server configurations",
            cls.VPN_DELETE_SERVER: "Delete VPN servers",
            cls.VPN_CREATE_CLIENT: "Create VPN clients",
            cls.VPN_MODIFY_CLIENT: "Modify VPN client configurations",
            cls.VPN_DELETE_CLIENT: "Delete VPN clients",
            cls.VPN_READ: "Read VPN configurations and status",
            cls.VPN_ADMIN: "Full VPN administration access",

            cls.FIREWALL_CREATE_RULE: "Create firewall rules",
            cls.FIREWALL_MODIFY_RULE: "Modify firewall rules",
            cls.FIREWALL_DELETE_RULE: "Delete firewall rules",
            cls.FIREWALL_CREATE_ZONE: "Create firewall zones",
            cls.FIREWALL_MODIFY_ZONE: "Modify firewall zones",
            cls.FIREWALL_DELETE_ZONE: "Delete firewall zones",
            cls.FIREWALL_READ: "Read firewall configuration and status",
            cls.FIREWALL_ADMIN: "Full firewall administration access",

            cls.MONITORING_CREATE: "Create monitoring configurations",
            cls.MONITORING_MODIFY: "Modify monitoring configurations",
            cls.MONITORING_DELETE: "Delete monitoring configurations",
            cls.MONITORING_READ: "Read monitoring data and metrics",
            cls.MONITORING_ADMIN: "Full monitoring administration access",

            cls.SECURITY_CREATE_CERT: "Create security certificates",
            cls.SECURITY_REVOKE_CERT: "Revoke security certificates",
            cls.SECURITY_CREATE_POLICY: "Create security policies",
            cls.SECURITY_MODIFY_POLICY: "Modify security policies",
            cls.SECURITY_DELETE_POLICY: "Delete security policies",
            cls.SECURITY_SCAN: "Perform security scans",
            cls.SECURITY_READ: "Read security configuration and logs",
            cls.SECURITY_ADMIN: "Full security administration access",

            cls.API_READ: "Read data through API",
            cls.API_WRITE: "Write data through API",
            cls.API_DELETE: "Delete data through API",
            cls.API_ADMIN: "Full API administration access",

            cls.UI_ACCESS: "Access the user interface",
            cls.UI_MODIFY: "Modify user interface settings",
            cls.UI_ADMIN: "Full UI administration access",

            cls.PLUGIN_INSTALL: "Install plugins",
            cls.PLUGIN_UNINSTALL: "Uninstall plugins",
            cls.PLUGIN_ENABLE: "Enable plugins",
            cls.PLUGIN_DISABLE: "Disable plugins",
            cls.PLUGIN_CONFIG: "Configure plugins",
            cls.PLUGIN_ADMIN: "Full plugin administration access",
        }

        return descriptions.get(permission, f"Permission: {permission}")

    @classmethod
    def get_category_permissions(cls, category: str) -> List[str]:
        """Get all permissions for a specific category.

        Args:
            category: Category name (e.g., 'network', 'vpn', 'firewall').

        Returns:
            List of permissions for that category.
        """
        return [p for p in cls.ALL_PERMISSIONS if p.startswith(f"{category}.")]

    def __str__(self) -> str:
        """String representation of permissions."""
        return f"PluginPermissions(plugin={self.plugin_name}, permissions={len(self.granted_permissions)})"

    def __repr__(self) -> str:
        """Detailed representation of permissions."""
        return f"PluginPermissions(plugin={self.plugin_name}, granted={self.get_granted_permissions()})"
