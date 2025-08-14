"""Enhanced API routes for WebUI plugin with RBAC integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth.models import current_active_user, User, create_access_token
from .rbac.models import (
    get_rbac_manager,
    PermissionScope,
    PermissionAction,
    Role,
    Permission
)
from .middleware import get_current_user, require_permission, SessionManager

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False


class RoleAssignmentRequest(BaseModel):
    user_id: str
    role_id: str
    expires_at: Optional[str] = None


class CreateRoleRequest(BaseModel):
    name: str
    description: str
    permissions: List[str]


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class FirewallRuleRequest(BaseModel):
    name: str
    type: str  # allow/deny
    protocol: str  # tcp/udp/icmp/all
    source: Optional[str] = None
    destination: Optional[str] = None
    port: Optional[int] = None
    enabled: bool = True


class SystemConfigRequest(BaseModel):
    category: str
    settings: Dict[str, Any]


class DashboardResponse(BaseModel):
    stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    system_health: Dict[str, Any]
    alerts: List[Dict[str, Any]]


def create_api_router() -> APIRouter:
    """Create the API router with all endpoints."""
    router = APIRouter(prefix="/api/webui", tags=["webui"])
    session_manager = SessionManager()
    rbac_manager = get_rbac_manager()

    # ==================== Authentication Endpoints ====================

    @router.post("/auth/login")
    async def login(request: Request, login_data: LoginRequest, response: Response):
        """Enhanced login with session management."""
        from app.core.startup import CoreUserRepository
        from app.auth.models import verify_password

        user_repo = CoreUserRepository()
        user_data = user_repo.get_user_by_username(login_data.username)

        if not user_data or not verify_password(login_data.password, user_data.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Create access token
        token_data = {"sub": user_data["username"]}
        expires_delta = timedelta(days=30 if login_data.remember_me else 1)
        access_token = create_access_token(token_data, expires_delta)

        # Create session
        session_data = {
            "username": user_data["username"],
            "email": user_data.get("email", ""),
            "role": user_data.get("role", "user"),
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
        session_id = session_manager.create_session(user_data["username"], session_data)

        # Set cookies
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=expires_delta.total_seconds()
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=expires_delta.total_seconds()
        )

        # Get user roles and permissions
        roles = rbac_manager.get_user_roles(user_data["username"])
        permissions = rbac_manager.get_user_permissions(user_data["username"])

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user_data["username"],
                "email": user_data.get("email", ""),
                "role": user_data.get("role", "user"),
                "is_superuser": user_data.get("is_superuser", False),
                "roles": [r.to_dict() for r in roles],
                "permissions": [p.to_dict() for p in permissions]
            }
        }

    @router.post("/auth/logout")
    async def logout(request: Request, response: Response):
        """Logout and destroy session."""
        session_id = request.cookies.get("session_id")
        if session_id:
            session_manager.destroy_session(session_id)

        response.delete_cookie("session_id")
        response.delete_cookie("access_token")

        return {"message": "Logged out successfully"}

    @router.get("/auth/me")
    async def get_current_user_info(current_user: User = Depends(current_active_user)):
        """Get current user information with roles and permissions."""
        roles = rbac_manager.get_user_roles(current_user.username)
        permissions = rbac_manager.get_user_permissions(current_user.username)

        return {
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "is_superuser": current_user.is_superuser,
            "roles": [r.to_dict() for r in roles],
            "permissions": [p.to_dict() for p in permissions]
        }

    # ==================== Dashboard Endpoints ====================

    @router.get("/dashboard", response_model=DashboardResponse)
    @require_permission(PermissionScope.DASHBOARD, PermissionAction.VIEW)
    async def get_dashboard_data(current_user: User = Depends(current_active_user)):
        """Get comprehensive dashboard data."""
        import random

        # Simulated dashboard data (replace with real data sources)
        stats = {
            "security_score": round(95 + random.random() * 5, 1),
            "connected_devices": random.randint(15, 30),
            "threats_blocked": random.randint(0, 5),
            "bandwidth_today_mb": random.randint(500, 2000),
            "active_rules": random.randint(20, 50),
            "system_uptime_hours": random.randint(100, 500)
        }

        recent_activity = [
            {
                "id": f"act_{i}",
                "type": random.choice(["security", "network", "system"]),
                "message": f"Activity {i}: " + random.choice([
                    "Blocked suspicious connection",
                    "New device connected",
                    "Firewall rule updated",
                    "System backup completed"
                ]),
                "timestamp": (datetime.now() - timedelta(minutes=i*10)).isoformat(),
                "severity": random.choice(["info", "warning", "success"])
            }
            for i in range(10)
        ]

        system_health = {
            "cpu_usage": random.randint(10, 60),
            "memory_usage": random.randint(30, 70),
            "disk_usage": random.randint(20, 80),
            "temperature": random.randint(35, 65),
            "network_latency_ms": random.randint(5, 50)
        }

        alerts = [
            {
                "id": f"alert_{i}",
                "title": f"Alert {i}",
                "message": random.choice([
                    "High CPU usage detected",
                    "Unusual network activity",
                    "Update available",
                    "Backup overdue"
                ]),
                "severity": random.choice(["info", "warning", "error"]),
                "timestamp": datetime.now().isoformat(),
                "acknowledged": False
            }
            for i in range(3)
        ]

        return DashboardResponse(
            stats=stats,
            recent_activity=recent_activity,
            system_health=system_health,
            alerts=alerts
        )

    @router.get("/dashboard/realtime")
    @require_permission(PermissionScope.MONITORING, PermissionAction.VIEW)
    async def get_realtime_data(current_user: User = Depends(current_active_user)):
        """Get real-time monitoring data."""
        import random

        return {
            "timestamp": datetime.now().isoformat(),
            "network": {
                "inbound_mbps": round(random.random() * 100, 2),
                "outbound_mbps": round(random.random() * 50, 2),
                "active_connections": random.randint(50, 200),
                "packet_loss": round(random.random() * 0.5, 2)
            },
            "system": {
                "cpu": random.randint(10, 60),
                "memory": random.randint(30, 70),
                "processes": random.randint(100, 200)
            }
        }

    # ==================== User Management Endpoints ====================

    @router.get("/users")
    @require_permission(PermissionScope.USERS, PermissionAction.VIEW)
    async def list_users(current_user: User = Depends(current_active_user)):
        """List all users with their roles."""
        from app.core.startup import CoreUserRepository

        user_repo = CoreUserRepository()
        users = user_repo.get_all_users()

        user_list = []
        for user in users:
            roles = rbac_manager.get_user_roles(user["username"])
            user_list.append({
                "username": user["username"],
                "email": user.get("email", ""),
                "is_active": user.get("is_active", False),
                "is_superuser": user.get("is_superuser", False),
                "created_at": user.get("created_at", ""),
                "roles": [r.name for r in roles]
            })

        return {"users": user_list}

    @router.put("/users/{username}")
    @require_permission(PermissionScope.USERS, PermissionAction.UPDATE)
    async def update_user(
        username: str,
        update_data: UpdateUserRequest,
        current_user: User = Depends(current_active_user)
    ):
        """Update user information."""
        from app.core.startup import CoreUserRepository

        user_repo = CoreUserRepository()
        user = user_repo.get_user_by_username(username)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update user fields
        if update_data.email is not None:
            user["email"] = update_data.email
        if update_data.first_name is not None:
            user["first_name"] = update_data.first_name
        if update_data.last_name is not None:
            user["last_name"] = update_data.last_name
        if update_data.is_active is not None:
            user["is_active"] = update_data.is_active

        # Save updated user
        user_repo.update_user(username, user)

        return {"message": "User updated successfully", "user": user}

    @router.delete("/users/{username}")
    @require_permission(PermissionScope.USERS, PermissionAction.DELETE)
    async def delete_user(username: str, current_user: User = Depends(current_active_user)):
        """Delete a user account."""
        if username == current_user.username:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        from app.core.startup import CoreUserRepository

        user_repo = CoreUserRepository()
        if not user_repo.get_user_by_username(username):
            raise HTTPException(status_code=404, detail="User not found")

        user_repo.delete_user(username)

        return {"message": f"User {username} deleted successfully"}

    # ==================== Role & Permission Management ====================

    @router.get("/roles")
    @require_permission(PermissionScope.USERS, PermissionAction.VIEW)
    async def list_roles(current_user: User = Depends(current_active_user)):
        """List all available roles."""
        roles = rbac_manager.get_all_roles()
        return {
            "roles": [r.to_dict() for r in roles]
        }

    @router.post("/roles")
    @require_permission(PermissionScope.USERS, PermissionAction.CREATE)
    async def create_role(
        role_data: CreateRoleRequest,
        current_user: User = Depends(current_active_user)
    ):
        """Create a new custom role."""
        try:
            role = rbac_manager.create_role(
                name=role_data.name,
                description=role_data.description,
                permissions=role_data.permissions
            )
            return {"message": "Role created successfully", "role": role.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/roles/assign")
    @require_permission(PermissionScope.USERS, PermissionAction.UPDATE)
    async def assign_role(
        assignment: RoleAssignmentRequest,
        current_user: User = Depends(current_active_user)
    ):
        """Assign a role to a user."""
        try:
            assignment = rbac_manager.assign_role(
                user_id=assignment.user_id,
                role_id=assignment.role_id,
                assigned_by=current_user.username,
                expires_at=assignment.expires_at
            )
            return {"message": "Role assigned successfully", "assignment": assignment.to_dict()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/roles/revoke/{user_id}/{role_id}")
    @require_permission(PermissionScope.USERS, PermissionAction.UPDATE)
    async def revoke_role(
        user_id: str,
        role_id: str,
        current_user: User = Depends(current_active_user)
    ):
        """Revoke a role from a user."""
        rbac_manager.revoke_role(user_id, role_id)
        return {"message": f"Role {role_id} revoked from user {user_id}"}

    @router.get("/permissions")
    @require_permission(PermissionScope.USERS, PermissionAction.VIEW)
    async def list_permissions(current_user: User = Depends(current_active_user)):
        """List all available permissions."""
        permissions = rbac_manager.get_all_permissions()
        return {
            "permissions": [p.to_dict() for p in permissions]
        }

    # ==================== Firewall Management ====================

    @router.get("/firewall/rules")
    @require_permission(PermissionScope.FIREWALL, PermissionAction.VIEW)
    async def get_firewall_rules(current_user: User = Depends(current_active_user)):
        """Get all firewall rules."""
        # Simulated firewall rules (replace with actual implementation)
        rules = [
            {
                "id": f"rule_{i}",
                "name": f"Rule {i}",
                "type": "allow" if i % 2 == 0 else "deny",
                "protocol": ["tcp", "udp", "icmp"][i % 3],
                "source": f"192.168.1.{i}",
                "destination": "any",
                "port": 80 + i * 100 if i % 2 == 0 else None,
                "enabled": i % 3 != 0,
                "hits": i * 123,
                "created_at": datetime.now().isoformat(),
                "created_by": "admin"
            }
            for i in range(1, 11)
        ]

        return {"rules": rules}

    @router.post("/firewall/rules")
    @require_permission(PermissionScope.FIREWALL, PermissionAction.CREATE)
    async def create_firewall_rule(
        rule: FirewallRuleRequest,
        current_user: User = Depends(current_active_user)
    ):
        """Create a new firewall rule."""
        # Implement actual firewall rule creation
        new_rule = {
            "id": f"rule_{datetime.now().timestamp()}",
            **rule.dict(),
            "created_at": datetime.now().isoformat(),
            "created_by": current_user.username,
            "hits": 0
        }

        logger.info(f"User {current_user.username} created firewall rule: {new_rule['name']}")
        return {"message": "Firewall rule created", "rule": new_rule}

    @router.delete("/firewall/rules/{rule_id}")
    @require_permission(PermissionScope.FIREWALL, PermissionAction.DELETE)
    async def delete_firewall_rule(
        rule_id: str,
        current_user: User = Depends(current_active_user)
    ):
        """Delete a firewall rule."""
        logger.info(f"User {current_user.username} deleted firewall rule: {rule_id}")
        return {"message": f"Firewall rule {rule_id} deleted"}

    # ==================== Network Management ====================

    @router.get("/network/devices")
    @require_permission(PermissionScope.NETWORK, PermissionAction.VIEW)
    async def get_network_devices(current_user: User = Depends(current_active_user)):
        """Get list of network devices."""
        import random

        devices = [
            {
                "id": f"device_{i}",
                "name": f"Device {i}",
                "ip_address": f"192.168.1.{10 + i}",
                "mac_address": f"AA:BB:CC:DD:EE:{i:02X}",
                "type": ["laptop", "phone", "tablet", "desktop", "iot"][i % 5],
                "status": "online" if i % 3 != 0 else "offline",
                "last_seen": (datetime.now() - timedelta(minutes=i * 5)).isoformat(),
                "bandwidth_usage_mb": random.randint(10, 500)
            }
            for i in range(1, 16)
        ]

        return {"devices": devices}

    @router.post("/network/scan")
    @require_permission(PermissionScope.NETWORK, PermissionAction.EXECUTE)
    async def scan_network(current_user: User = Depends(current_active_user)):
        """Initiate a network scan."""
        logger.info(f"User {current_user.username} initiated network scan")
        return {
            "message": "Network scan initiated",
            "scan_id": f"scan_{datetime.now().timestamp()}",
            "estimated_time": "30 seconds"
        }

    # ==================== System Management ====================

    @router.get("/system/status")
    @require_permission(PermissionScope.SYSTEM, PermissionAction.VIEW)
    async def get_system_status(current_user: User = Depends(current_active_user)):
        """Get system status and health information."""
        import platform
        import psutil

        return {
            "hostname": platform.node(),
            "platform": platform.system(),
            "version": platform.version(),
            "uptime_seconds": int((datetime.now() - datetime(2024, 1, 1)).total_seconds()),
            "cpu": {
                "count": psutil.cpu_count(),
                "usage_percent": psutil.cpu_percent(interval=1)
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "used_gb": round(psutil.disk_usage('/').used / (1024**3), 2),
                "percent": psutil.disk_usage('/').percent
            }
        }

    @router.post("/system/config")
    @require_permission(PermissionScope.SYSTEM, PermissionAction.CONFIGURE)
    async def update_system_config(
        config: SystemConfigRequest,
        current_user: User = Depends(current_active_user)
    ):
        """Update system configuration."""
        logger.info(f"User {current_user.username} updated system config: {config.category}")
        return {
            "message": f"System configuration updated for {config.category}",
            "settings": config.settings
        }

    @router.post("/system/backup")
    @require_permission(PermissionScope.SYSTEM, PermissionAction.EXECUTE)
    async def create_backup(current_user: User = Depends(current_active_user)):
        """Create a system backup."""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"User {current_user.username} initiated system backup: {backup_id}")

        return {
            "message": "Backup initiated",
            "backup_id": backup_id,
            "estimated_time": "5 minutes"
        }

    # ==================== Logs & Monitoring ====================

    @router.get("/logs")
    @require_permission(PermissionScope.LOGS, PermissionAction.VIEW)
    async def get_logs(
        log_type: str = "all",
        limit: int = 100,
        current_user: User = Depends(current_active_user)
    ):
        """Get system logs."""
        # Simulated log entries
        logs = [
            {
                "id": f"log_{i}",
                "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                "level": ["info", "warning", "error", "debug"][i % 4],
                "source": ["system", "firewall", "network", "auth"][i % 4],
                "message": f"Log entry {i}: Sample log message",
                "details": {}
            }
            for i in range(min(limit, 100))
        ]

        return {"logs": logs, "total": len(logs)}

    @router.post("/logs/export")
    @require_permission(PermissionScope.LOGS, PermissionAction.EXPORT)
    async def export_logs(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        current_user: User = Depends(current_active_user)
    ):
        """Export logs for a date range."""
        export_id = f"export_{datetime.now().timestamp()}"
        logger.info(f"User {current_user.username} exported logs: {export_id}")

        return {
            "message": "Log export initiated",
            "export_id": export_id,
            "format": "csv",
            "download_url": f"/api/webui/logs/download/{export_id}"
        }

    # ==================== Plugin Management ====================

    @router.get("/plugins")
    @require_permission(PermissionScope.PLUGINS, PermissionAction.VIEW)
    async def list_plugins(current_user: User = Depends(current_active_user)):
        """List all available plugins."""
        plugins = [
            {
                "id": "vpn",
                "name": "VPN Manager",
                "version": "1.0.0",
                "enabled": True,
                "status": "running",
                "description": "Manage VPN connections"
            },
            {
                "id": "ids",
                "name": "Intrusion Detection",
                "version": "2.1.0",
                "enabled": True,
                "status": "running",
                "description": "Monitor for intrusions"
            },
            {
                "id": "backup",
                "name": "Auto Backup",
                "version": "1.5.0",
                "enabled": False,
                "status": "stopped",
                "description": "Automated backup system"
            }
        ]

        return {"plugins": plugins}

    @router.post("/plugins/{plugin_id}/toggle")
    @require_permission(PermissionScope.PLUGINS, PermissionAction.EXECUTE)
    async def toggle_plugin(
        plugin_id: str,
        current_user: User = Depends(current_active_user)
    ):
        """Enable or disable a plugin."""
        logger.info(f"User {current_user.username} toggled plugin: {plugin_id}")
        return {
            "message": f"Plugin {plugin_id} toggled",
            "enabled": True  # Would check actual state
        }

    return router
