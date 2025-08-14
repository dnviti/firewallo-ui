"""Role-Based Access Control (RBAC) models for WebUI plugin."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import json
import logging

# Import main application auth components
from app.auth.models import User as AuthUser, get_current_user
from app.core.startup import CoreUserRepository

logger = logging.getLogger(__name__)


class PermissionScope(Enum):
    """Permission scopes for different system areas."""
    DASHBOARD = "dashboard"
    FIREWALL = "firewall"
    NETWORK = "network"
    MONITORING = "monitoring"
    PLUGINS = "plugins"
    SYSTEM = "system"
    LOGS = "logs"
    USERS = "users"
    SETTINGS = "settings"
    API = "api"


class PermissionAction(Enum):
    """Permission actions that can be performed."""
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    CONFIGURE = "configure"
    EXPORT = "export"
    IMPORT = "import"


class RoleType(Enum):
    """Built-in role types."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    CUSTOM = "custom"


@dataclass
class Permission:
    """Individual permission definition."""
    id: str
    name: str
    scope: PermissionScope
    action: PermissionAction
    description: str
    resource: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Permission):
            return self.id == other.id
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert permission to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "scope": self.scope.value,
            "action": self.action.value,
            "description": self.description,
            "resource": self.resource,
            "constraints": self.constraints,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Permission:
        """Create permission from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            scope=PermissionScope(data["scope"]),
            action=PermissionAction(data["action"]),
            description=data["description"],
            resource=data.get("resource"),
            constraints=data.get("constraints", {}),
            created_at=data.get("created_at", datetime.now().isoformat())
        )

    def matches(self, scope: str, action: str, resource: Optional[str] = None) -> bool:
        """Check if permission matches the given scope, action, and resource."""
        if self.scope.value != scope:
            return False

        if self.action.value != action:
            return False

        if self.resource and resource:
            # Check resource pattern matching
            if '*' in self.resource:
                # Wildcard matching
                pattern = self.resource.replace('*', '.*')
                import re
                if not re.match(pattern, resource):
                    return False
            elif self.resource != resource:
                return False

        return True


@dataclass
class Role:
    """Role definition with permissions."""
    id: str
    name: str
    type: RoleType
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    parent_role: Optional[str] = None
    priority: int = 100
    is_system: bool = False
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Role):
            return self.id == other.id
        return False

    def add_permission(self, permission: Permission):
        """Add a permission to the role."""
        self.permissions.add(permission)
        self.updated_at = datetime.now().isoformat()

    def remove_permission(self, permission: Permission):
        """Remove a permission from the role."""
        self.permissions.discard(permission)
        self.updated_at = datetime.now().isoformat()

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions

    def has_permission_for(self, scope: str, action: str, resource: Optional[str] = None) -> bool:
        """Check if role has permission for scope/action/resource."""
        for perm in self.permissions:
            if perm.matches(scope, action, resource):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "permissions": [p.to_dict() for p in self.permissions],
            "parent_role": self.parent_role,
            "priority": self.priority,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Role:
        """Create role from dictionary."""
        permissions = set()
        for perm_data in data.get("permissions", []):
            permissions.add(Permission.from_dict(perm_data))

        return cls(
            id=data["id"],
            name=data["name"],
            type=RoleType(data["type"]),
            description=data["description"],
            permissions=permissions,
            parent_role=data.get("parent_role"),
            priority=data.get("priority", 100),
            is_system=data.get("is_system", False),
            is_active=data.get("is_active", True),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )


@dataclass
class UserRoleAssignment:
    """Assignment of roles to users."""
    user_id: str
    role_id: str
    assigned_by: str
    assigned_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def is_expired(self) -> bool:
        """Check if assignment has expired."""
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert assignment to dictionary."""
        return {
            "user_id": self.user_id,
            "role_id": self.role_id,
            "assigned_by": self.assigned_by,
            "assigned_at": self.assigned_at,
            "expires_at": self.expires_at,
            "conditions": self.conditions,
            "is_active": self.is_active
        }


class RBACManager:
    """RBAC management system integrated with main application auth."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize RBAC manager."""
        self.storage_path = storage_path or Path("data/rbac.json")
        self.roles: Dict[str, Role] = {}
        self.permissions: Dict[str, Permission] = {}
        self.assignments: List[UserRoleAssignment] = []
        self._initialized = False

        # Initialize user repository for integration
        self.user_repo = CoreUserRepository()

        # Initialize default permissions
        self._init_default_permissions()
        # Initialize default roles
        self._init_default_roles()
        # Load custom configurations
        self._load_custom_config()
        # Sync with main application users
        self._sync_with_main_auth()

    def _init_default_permissions(self):
        """Initialize default system permissions."""
        default_permissions = [
            # Dashboard permissions
            Permission("dashboard.view", "View Dashboard", PermissionScope.DASHBOARD, PermissionAction.VIEW,
                      "View dashboard and statistics"),
            Permission("dashboard.export", "Export Dashboard", PermissionScope.DASHBOARD, PermissionAction.EXPORT,
                      "Export dashboard data and reports"),

            # Firewall permissions
            Permission("firewall.view", "View Firewall Rules", PermissionScope.FIREWALL, PermissionAction.VIEW,
                      "View firewall rules and configurations"),
            Permission("firewall.create", "Create Firewall Rules", PermissionScope.FIREWALL, PermissionAction.CREATE,
                      "Create new firewall rules"),
            Permission("firewall.update", "Update Firewall Rules", PermissionScope.FIREWALL, PermissionAction.UPDATE,
                      "Modify existing firewall rules"),
            Permission("firewall.delete", "Delete Firewall Rules", PermissionScope.FIREWALL, PermissionAction.DELETE,
                      "Delete firewall rules"),
            Permission("firewall.execute", "Execute Firewall Actions", PermissionScope.FIREWALL, PermissionAction.EXECUTE,
                      "Apply or reload firewall configurations"),

            # Network permissions
            Permission("network.view", "View Network Config", PermissionScope.NETWORK, PermissionAction.VIEW,
                      "View network configurations"),
            Permission("network.configure", "Configure Network", PermissionScope.NETWORK, PermissionAction.CONFIGURE,
                      "Modify network settings"),

            # Monitoring permissions
            Permission("monitoring.view", "View Monitoring", PermissionScope.MONITORING, PermissionAction.VIEW,
                      "View system monitoring data"),
            Permission("monitoring.configure", "Configure Monitoring", PermissionScope.MONITORING, PermissionAction.CONFIGURE,
                      "Configure monitoring settings"),

            # Plugin permissions
            Permission("plugins.view", "View Plugins", PermissionScope.PLUGINS, PermissionAction.VIEW,
                      "View installed plugins"),
            Permission("plugins.create", "Install Plugins", PermissionScope.PLUGINS, PermissionAction.CREATE,
                      "Install new plugins"),
            Permission("plugins.update", "Update Plugins", PermissionScope.PLUGINS, PermissionAction.UPDATE,
                      "Update plugin configurations"),
            Permission("plugins.delete", "Remove Plugins", PermissionScope.PLUGINS, PermissionAction.DELETE,
                      "Uninstall plugins"),
            Permission("plugins.execute", "Execute Plugin Actions", PermissionScope.PLUGINS, PermissionAction.EXECUTE,
                      "Enable/disable plugins"),

            # System permissions
            Permission("system.view", "View System Info", PermissionScope.SYSTEM, PermissionAction.VIEW,
                      "View system information"),
            Permission("system.configure", "Configure System", PermissionScope.SYSTEM, PermissionAction.CONFIGURE,
                      "Modify system settings"),
            Permission("system.execute", "Execute System Commands", PermissionScope.SYSTEM, PermissionAction.EXECUTE,
                      "Execute system-level commands"),

            # Log permissions
            Permission("logs.view", "View Logs", PermissionScope.LOGS, PermissionAction.VIEW,
                      "View system and application logs"),
            Permission("logs.export", "Export Logs", PermissionScope.LOGS, PermissionAction.EXPORT,
                      "Export log files"),
            Permission("logs.delete", "Clear Logs", PermissionScope.LOGS, PermissionAction.DELETE,
                      "Clear or delete log files"),

            # User management permissions
            Permission("users.view", "View Users", PermissionScope.USERS, PermissionAction.VIEW,
                      "View user accounts"),
            Permission("users.create", "Create Users", PermissionScope.USERS, PermissionAction.CREATE,
                      "Create new user accounts"),
            Permission("users.update", "Update Users", PermissionScope.USERS, PermissionAction.UPDATE,
                      "Modify user accounts"),
            Permission("users.delete", "Delete Users", PermissionScope.USERS, PermissionAction.DELETE,
                      "Delete user accounts"),

            # Settings permissions
            Permission("settings.view", "View Settings", PermissionScope.SETTINGS, PermissionAction.VIEW,
                      "View application settings"),
            Permission("settings.update", "Update Settings", PermissionScope.SETTINGS, PermissionAction.UPDATE,
                      "Modify application settings"),

            # API permissions
            Permission("api.access", "API Access", PermissionScope.API, PermissionAction.VIEW,
                      "Access API endpoints"),
            Permission("api.admin", "API Admin", PermissionScope.API, PermissionAction.CONFIGURE,
                      "Full API administrative access")
        ]

        for perm in default_permissions:
            self.permissions[perm.id] = perm

    def _init_default_roles(self):
        """Initialize default system roles."""
        # Super Admin role - full access
        super_admin = Role(
            id="super_admin",
            name="Super Administrator",
            type=RoleType.SUPER_ADMIN,
            description="Full system access with all permissions",
            permissions=set(self.permissions.values()),
            priority=1,
            is_system=True
        )

        # Admin role - most permissions except system-critical
        admin_perms = {p for p in self.permissions.values()
                      if not (p.scope == PermissionScope.SYSTEM and p.action == PermissionAction.EXECUTE)}
        admin = Role(
            id="admin",
            name="Administrator",
            type=RoleType.ADMIN,
            description="Administrative access with most permissions",
            permissions=admin_perms,
            priority=10,
            is_system=True
        )

        # Operator role - manage firewall and network
        operator_perms = {p for p in self.permissions.values()
                         if p.scope in [PermissionScope.DASHBOARD, PermissionScope.FIREWALL,
                                      PermissionScope.NETWORK, PermissionScope.MONITORING]
                         and p.action != PermissionAction.DELETE}
        operator = Role(
            id="operator",
            name="Network Operator",
            type=RoleType.OPERATOR,
            description="Manage firewall rules and network configurations",
            permissions=operator_perms,
            priority=50,
            is_system=True
        )

        # Viewer role - read-only access
        viewer_perms = {p for p in self.permissions.values()
                       if p.action == PermissionAction.VIEW}
        viewer = Role(
            id="viewer",
            name="Viewer",
            type=RoleType.VIEWER,
            description="Read-only access to system information",
            permissions=viewer_perms,
            priority=100,
            is_system=True
        )

        self.roles["super_admin"] = super_admin
        self.roles["admin"] = admin
        self.roles["operator"] = operator
        self.roles["viewer"] = viewer

    def _load_custom_config(self):
        """Load custom RBAC configuration from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                # Load custom permissions
                for perm_data in data.get("custom_permissions", []):
                    perm = Permission.from_dict(perm_data)
                    if not perm.id.startswith("custom."):
                        perm.id = f"custom.{perm.id}"
                    self.permissions[perm.id] = perm

                # Load custom roles
                for role_data in data.get("custom_roles", []):
                    role = Role.from_dict(role_data)
                    if not role.is_system:
                        self.roles[role.id] = role

                # Load assignments
                for assign_data in data.get("assignments", []):
                    assignment = UserRoleAssignment(**assign_data)
                    if not assignment.is_expired():
                        self.assignments.append(assignment)

                logger.info(f"Loaded RBAC configuration from {self.storage_path}")
            except Exception as e:
                logger.error(f"Failed to load RBAC configuration: {e}")

    def save_config(self):
        """Save current RBAC configuration."""
        try:
            custom_permissions = [p.to_dict() for p in self.permissions.values()
                                if p.id.startswith("custom.")]
            custom_roles = [r.to_dict() for r in self.roles.values()
                          if not r.is_system]

            data = {
                "custom_permissions": custom_permissions,
                "custom_roles": custom_roles,
                "assignments": [a.to_dict() for a in self.assignments]
            }

            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved RBAC configuration to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save RBAC configuration: {e}")

    def create_role(self, name: str, description: str, permissions: List[str]) -> Role:
        """Create a new custom role."""
        role_id = name.lower().replace(' ', '_')
        if role_id in self.roles:
            raise ValueError(f"Role {role_id} already exists")

        role_perms = set()
        for perm_id in permissions:
            if perm_id in self.permissions:
                role_perms.add(self.permissions[perm_id])

        role = Role(
            id=role_id,
            name=name,
            type=RoleType.CUSTOM,
            description=description,
            permissions=role_perms,
            is_system=False
        )

        self.roles[role_id] = role
        self.save_config()
        return role

    def assign_role(self, user_id: str, role_id: str, assigned_by: str,
                   expires_at: Optional[str] = None) -> UserRoleAssignment:
        """Assign a role to a user."""
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} does not exist")

        # Remove existing assignment if any
        self.revoke_role(user_id, role_id)

        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            expires_at=expires_at
        )

        self.assignments.append(assignment)
        self.save_config()
        return assignment

    def revoke_role(self, user_id: str, role_id: str):
        """Revoke a role from a user."""
        self.assignments = [a for a in self.assignments
                          if not (a.user_id == user_id and a.role_id == role_id)]
        self.save_config()

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all active roles for a user, including roles from main auth system."""
        roles = []

        # Get explicit role assignments
        for assignment in self.assignments:
            if assignment.user_id == user_id and assignment.is_active:
                if not assignment.is_expired():
                    if assignment.role_id in self.roles:
                        roles.append(self.roles[assignment.role_id])

        # Get user from main auth system and map to RBAC roles
        user_data = self.user_repo.get_user_by_username(user_id)
        if user_data:
            user_role = user_data.get("role", "user")
            is_superuser = user_data.get("is_superuser", False)

            # Map main auth roles to RBAC roles
            if is_superuser and "super_admin" in self.roles:
                if not any(r.id == "super_admin" for r in roles):
                    roles.append(self.roles["super_admin"])
            elif user_role == "admin" and "admin" in self.roles:
                if not any(r.id == "admin" for r in roles):
                    roles.append(self.roles["admin"])
            elif user_role == "operator" and "operator" in self.roles:
                if not any(r.id == "operator" for r in roles):
                    roles.append(self.roles["operator"])
            elif "viewer" in self.roles:
                if not any(r.id == "viewer" for r in roles):
                    roles.append(self.roles["viewer"])

        # Sort by priority
        roles.sort(key=lambda r: r.priority)
        return roles

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user based on their roles."""
        permissions = set()
        for role in self.get_user_roles(user_id):
            if role.is_active:
                permissions.update(role.permissions)
        return permissions

    def check_permission(self, user_id: str, scope: str, action: str,
                        resource: Optional[str] = None) -> bool:
        """Check if user has permission for scope/action/resource."""
        # Check if user is superuser in main auth system (always has access)
        user_data = self.user_repo.get_user_by_username(user_id)
        if user_data and user_data.get("is_superuser", False):
            return True

        # Check role-based permissions
        for role in self.get_user_roles(user_id):
            if role.has_permission_for(scope, action, resource):
                return True
        return False

    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return self.roles.get(role_id)

    def get_all_roles(self) -> List[Role]:
        """Get all available roles."""
        return list(self.roles.values())

    def get_all_permissions(self) -> List[Permission]:
        """Get all available permissions."""
        return list(self.permissions.values())

    def _sync_with_main_auth(self):
        """Sync RBAC system with main application auth users."""
        try:
            users = self.user_repo.list_users()
            synced_count = 0

            for user in users:
                username = user.get("username")
                user_role = user.get("role", "user")

                if username:
                    # Check if user has explicit role assignment
                    has_assignment = any(
                        a.user_id == username for a in self.assignments
                    )

                    # If no explicit assignment, create one based on main auth role
                    if not has_assignment:
                        role_mapping = {
                            "admin": "admin",
                            "operator": "operator",
                            "user": "viewer"
                        }

                        rbac_role = role_mapping.get(user_role, "viewer")
                        if rbac_role in self.roles:
                            assignment = UserRoleAssignment(
                                user_id=username,
                                role_id=rbac_role,
                                assigned_by="system_sync",
                                assigned_at=datetime.now().isoformat()
                            )
                            self.assignments.append(assignment)
                            synced_count += 1

            if synced_count > 0:
                self.save_config()
                logger.info(f"Synced {synced_count} users with RBAC system")

        except Exception as e:
            logger.error(f"Failed to sync with main auth system: {e}")

    def sync_user_role(self, username: str):
        """Sync a specific user's role with main auth system."""
        try:
            user_data = self.user_repo.get_user_by_username(username)
            if not user_data:
                return False

            user_role = user_data.get("role", "user")

            # Remove existing system-assigned roles
            self.assignments = [
                a for a in self.assignments
                if not (a.user_id == username and a.assigned_by == "system_sync")
            ]

            # Add new role based on main auth
            role_mapping = {
                "admin": "admin",
                "operator": "operator",
                "user": "viewer"
            }

            rbac_role = role_mapping.get(user_role, "viewer")
            if rbac_role in self.roles:
                assignment = UserRoleAssignment(
                    user_id=username,
                    role_id=rbac_role,
                    assigned_by="system_sync",
                    assigned_at=datetime.now().isoformat()
                )
                self.assignments.append(assignment)
                self.save_config()
                return True

        except Exception as e:
            logger.error(f"Failed to sync user {username}: {e}")
        return False


# Global RBAC manager instance
_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get global RBAC manager instance."""
    global _rbac_manager
    if _rbac_manager is None:
        _rbac_manager = RBACManager()
    return _rbac_manager


def require_permission(scope: str, action: str, resource: Optional[str] = None):
    """Decorator to require specific permission for a function."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user from context (assumes user is passed as keyword argument)
            user = kwargs.get('current_user')
            if not user:
                raise PermissionError("Authentication required")

            rbac = get_rbac_manager()

            # Handle both User objects and string usernames
            if isinstance(user, (AuthUser, str)):
                user_id = getattr(user, 'username', str(user))
            else:
                user_id = getattr(user, 'username', str(user))

            if not rbac.check_permission(user_id, scope, action, resource):
                raise PermissionError(
                    f"Permission denied: {scope}.{action}" +
                    (f" for resource {resource}" if resource else "")
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def check_user_permission(user: AuthUser, scope: str, action: str, resource: Optional[str] = None) -> bool:
    """Check if a user has a specific permission."""
    rbac = get_rbac_manager()
    return rbac.check_permission(user.username, scope, action, resource)


def get_user_permissions_list(user: AuthUser) -> List[Dict[str, Any]]:
    """Get all permissions for a user as a list of dictionaries."""
    rbac = get_rbac_manager()
    permissions = rbac.get_user_permissions(user.username)
    return [p.to_dict() for p in permissions]


def get_user_roles_list(user: AuthUser) -> List[Dict[str, Any]]:
    """Get all roles for a user as a list of dictionaries."""
    rbac = get_rbac_manager()
    roles = rbac.get_user_roles(user.username)
    return [r.to_dict() for r in roles]
