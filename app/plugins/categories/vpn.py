"""VPN plugin interface for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

from app.plugins.base import VPNPluginError


class VPNServerCreate(BaseModel):
    """Model for creating a VPN server."""
    name: str
    endpoint: str
    port: int
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    network: str = "10.0.0.0/24"
    dns_servers: List[str] = ["8.8.8.8", "8.8.4.4"]
    allowed_ips: List[str] = ["0.0.0.0/0"]
    keep_alive: Optional[int] = 25
    mtu: Optional[int] = 1420
    enabled: bool = True
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class VPNServerResponse(BaseModel):
    """Model for VPN server response."""
    id: str
    name: str
    endpoint: str
    port: int
    private_key: Optional[str] = None
    public_key: str
    network: str
    dns_servers: List[str]
    allowed_ips: List[str]
    keep_alive: Optional[int]
    mtu: Optional[int]
    enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    client_count: int
    status: str  # active, inactive, error
    config: Optional[Dict[str, Any]] = None


class VPNServerUpdate(BaseModel):
    """Model for updating a VPN server."""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    port: Optional[int] = None
    network: Optional[str] = None
    dns_servers: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    keep_alive: Optional[int] = None
    mtu: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class VPNClientCreate(BaseModel):
    """Model for creating a VPN client."""
    name: str
    server_id: str
    email: Optional[str] = None
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    allowed_ips: List[str] = ["0.0.0.0/0"]
    dns_servers: Optional[List[str]] = None
    persistent_keepalive: Optional[int] = None
    enabled: bool = True
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class VPNClientResponse(BaseModel):
    """Model for VPN client response."""
    id: str
    name: str
    server_id: str
    email: Optional[str]
    public_key: str
    private_key: str
    allowed_ips: List[str]
    dns_servers: Optional[List[str]]
    persistent_keepalive: Optional[int]
    enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    last_handshake: Optional[datetime]
    transfer_rx: int = 0
    transfer_tx: int = 0
    endpoint: Optional[str] = None
    status: str  # connected, disconnected, unknown
    config: Optional[Dict[str, Any]] = None


class VPNClientUpdate(BaseModel):
    """Model for updating a VPN client."""
    name: Optional[str] = None
    email: Optional[str] = None
    allowed_ips: Optional[List[str]] = None
    dns_servers: Optional[List[str]] = None
    persistent_keepalive: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class VPNConfigResponse(BaseModel):
    """Model for VPN configuration response."""
    config_content: str
    qr_code: Optional[str] = None
    download_url: Optional[str] = None
    format: str = "wireguard"  # wireguard, openvpn, etc.


class VPNConnectionStatus(BaseModel):
    """Model for VPN connection status."""
    server_id: str
    client_id: Optional[str] = None
    status: str  # connected, disconnected, connecting, error
    connected_clients: int = 0
    total_clients: int = 0
    last_handshake: Optional[datetime] = None
    transfer_rx: int = 0
    transfer_tx: int = 0
    uptime: Optional[int] = None
    errors: List[str] = []
    details: Optional[Dict[str, Any]] = None


class VPNStatistics(BaseModel):
    """Model for VPN statistics."""
    server_id: str
    total_clients: int
    active_clients: int
    total_transfer_rx: int
    total_transfer_tx: int
    peak_connections: int
    average_uptime: float
    error_count: int
    last_updated: datetime


class VPNPluginInterface(ABC):
    """Interface that all VPN plugins must implement."""

    @abstractmethod
    async def create_server(self, server_data: VPNServerCreate) -> VPNServerResponse:
        """Create a new VPN server.

        Args:
            server_data: Server configuration data.

        Returns:
            VPNServerResponse: Created server information.

        Raises:
            VPNPluginError: If server creation fails.
        """
        pass

    @abstractmethod
    async def delete_server(self, server_id: str) -> bool:
        """Delete a VPN server.

        Args:
            server_id: ID of the server to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            VPNPluginError: If server deletion fails.
        """
        pass

    @abstractmethod
    async def list_servers(self, **filters) -> List[VPNServerResponse]:
        """List all VPN servers with optional filtering.

        Args:
            **filters: Optional filters (enabled, status, etc.).

        Returns:
            List[VPNServerResponse]: List of servers.
        """
        pass

    @abstractmethod
    async def get_server(self, server_id: str) -> Optional[VPNServerResponse]:
        """Get a specific VPN server by ID.

        Args:
            server_id: ID of the server to retrieve.

        Returns:
            Optional[VPNServerResponse]: Server information if found.
        """
        pass

    @abstractmethod
    async def update_server(self, server_id: str, update_data: VPNServerUpdate) -> Optional[VPNServerResponse]:
        """Update a VPN server.

        Args:
            server_id: ID of the server to update.
            update_data: Update data.

        Returns:
            Optional[VPNServerResponse]: Updated server information.

        Raises:
            VPNPluginError: If server update fails.
        """
        pass

    @abstractmethod
    async def create_client(self, client_data: VPNClientCreate) -> VPNClientResponse:
        """Create a new VPN client.

        Args:
            client_data: Client configuration data.

        Returns:
            VPNClientResponse: Created client information.

        Raises:
            VPNPluginError: If client creation fails.
        """
        pass

    @abstractmethod
    async def delete_client(self, client_id: str) -> bool:
        """Delete a VPN client.

        Args:
            client_id: ID of the client to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            VPNPluginError: If client deletion fails.
        """
        pass

    @abstractmethod
    async def list_clients(self, server_id: Optional[str] = None, **filters) -> List[VPNClientResponse]:
        """List VPN clients with optional filtering.

        Args:
            server_id: Optional server ID to filter by.
            **filters: Optional filters (enabled, status, etc.).

        Returns:
            List[VPNClientResponse]: List of clients.
        """
        pass

    @abstractmethod
    async def get_client(self, client_id: str) -> Optional[VPNClientResponse]:
        """Get a specific VPN client by ID.

        Args:
            client_id: ID of the client to retrieve.

        Returns:
            Optional[VPNClientResponse]: Client information if found.
        """
        pass

    @abstractmethod
    async def update_client(self, client_id: str, update_data: VPNClientUpdate) -> Optional[VPNClientResponse]:
        """Update a VPN client.

        Args:
            client_id: ID of the client to update.
            update_data: Update data.

        Returns:
            Optional[VPNClientResponse]: Updated client information.

        Raises:
            VPNPluginError: If client update fails.
        """
        pass

    @abstractmethod
    async def generate_config(self, client_id: str, format: str = "wireguard") -> VPNConfigResponse:
        """Generate configuration file for a client.

        Args:
            client_id: ID of the client.
            format: Configuration format (wireguard, openvpn, etc.).

        Returns:
            VPNConfigResponse: Configuration data.

        Raises:
            VPNPluginError: If config generation fails.
        """
        pass

    @abstractmethod
    async def get_connection_status(self, server_id: str, client_id: Optional[str] = None) -> VPNConnectionStatus:
        """Get connection status for server or specific client.

        Args:
            server_id: ID of the server.
            client_id: Optional client ID for specific client status.

        Returns:
            VPNConnectionStatus: Connection status information.
        """
        pass

    @abstractmethod
    async def revoke_client(self, client_id: str) -> bool:
        """Revoke a VPN client (disable access).

        Args:
            client_id: ID of the client to revoke.

        Returns:
            bool: True if revocation was successful.

        Raises:
            VPNPluginError: If client revocation fails.
        """
        pass

    # Optional methods with default implementations
    async def start_server(self, server_id: str) -> bool:
        """Start a VPN server.

        Args:
            server_id: ID of the server to start.

        Returns:
            bool: True if server was started successfully.
        """
        # Default implementation - update server to enabled
        update_data = VPNServerUpdate(enabled=True)
        result = await self.update_server(server_id, update_data)
        return result is not None

    async def stop_server(self, server_id: str) -> bool:
        """Stop a VPN server.

        Args:
            server_id: ID of the server to stop.

        Returns:
            bool: True if server was stopped successfully.
        """
        # Default implementation - update server to disabled
        update_data = VPNServerUpdate(enabled=False)
        result = await self.update_server(server_id, update_data)
        return result is not None

    async def restart_server(self, server_id: str) -> bool:
        """Restart a VPN server.

        Args:
            server_id: ID of the server to restart.

        Returns:
            bool: True if server was restarted successfully.
        """
        # Default implementation - stop then start
        if await self.stop_server(server_id):
            return await self.start_server(server_id)
        return False

    async def get_server_statistics(self, server_id: str) -> VPNStatistics:
        """Get statistics for a VPN server.

        Args:
            server_id: ID of the server.

        Returns:
            VPNStatistics: Server statistics.
        """
        # Default implementation - basic stats from server and clients
        server = await self.get_server(server_id)
        if not server:
            raise VPNPluginError(f"Server {server_id} not found")

        clients = await self.list_clients(server_id=server_id)
        active_clients = len([c for c in clients if c.status == "connected"])

        total_rx = sum(c.transfer_rx for c in clients)
        total_tx = sum(c.transfer_tx for c in clients)

        return VPNStatistics(
            server_id=server_id,
            total_clients=len(clients),
            active_clients=active_clients,
            total_transfer_rx=total_rx,
            total_transfer_tx=total_tx,
            peak_connections=len(clients),  # Simplified
            average_uptime=0.0,  # Would need historical data
            error_count=0,  # Would need error tracking
            last_updated=datetime.utcnow()
        )

    async def backup_server_config(self, server_id: str) -> Dict[str, Any]:
        """Backup server configuration.

        Args:
            server_id: ID of the server to backup.

        Returns:
            Dict[str, Any]: Backup data.
        """
        server = await self.get_server(server_id)
        if not server:
            raise VPNPluginError(f"Server {server_id} not found")

        clients = await self.list_clients(server_id=server_id)

        return {
            "server": server.dict(),
            "clients": [client.dict() for client in clients],
            "backup_timestamp": datetime.utcnow().isoformat(),
            "plugin_version": getattr(self, 'version', '1.0.0')
        }

    async def restore_server_config(self, backup_data: Dict[str, Any]) -> str:
        """Restore server configuration from backup.

        Args:
            backup_data: Backup data to restore.

        Returns:
            str: ID of the restored server.

        Raises:
            VPNPluginError: If restore fails.
        """
        if "server" not in backup_data or "clients" not in backup_data:
            raise VPNPluginError("Invalid backup data format")

        server_data = backup_data["server"]
        clients_data = backup_data["clients"]

        # Create server
        server_create = VPNServerCreate(**{
            k: v for k, v in server_data.items()
            if k in VPNServerCreate.__fields__
        })

        restored_server = await self.create_server(server_create)

        # Create clients
        for client_data in clients_data:
            client_create = VPNClientCreate(**{
                k: v for k, v in client_data.items()
                if k in VPNClientCreate.__fields__
            })
            client_create.server_id = restored_server.id
            await self.create_client(client_create)

        return restored_server.id
