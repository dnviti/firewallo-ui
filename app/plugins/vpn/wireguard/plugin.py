"""WireGuard VPN plugin implementation."""

import subprocess
import asyncio
import base64
import qrcode
import io
import os
import ipaddress
import secrets
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, PlainTextResponse
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import logging
from pathlib import Path

from app.plugins.base import BasePlugin, BaseRepository, VPNPluginError
from app.plugins.categories.vpn import (
    VPNPluginInterface,
    VPNServerCreate,
    VPNServerResponse,
    VPNServerUpdate,
    VPNClientCreate,
    VPNClientResponse,
    VPNClientUpdate,
    VPNConfigResponse,
    VPNConnectionStatus,
    VPNStatistics,
)
from app.auth.models import current_active_user


# Import all WireGuard services from the services module
from .services import (
    KeyGenerationService,
    KeyTriplet,
    IPAllocationService,
    ValidationService,
    WireGuardConfigRenderer,
    QRCodeService,
    WireGuardSystemService,
    WireGuardRepository,
)


class WireGuardPlugin(BasePlugin, VPNPluginInterface):
    """WireGuard VPN plugin implementation."""

    def __init__(self):
        super().__init__()
        self.name = "wireguard"
        self.category = "vpn"
        self.version = "1.0.0"
        self.description = "Modern, fast, and secure VPN implementation using WireGuard protocol"
        self.author = "Firewallo Team"
        self.license = "MIT"

        # Load manifest
        import json
        manifest_path = Path(__file__).parent / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                self.set_manifest(manifest)

        self.repository = WireGuardRepository()
        self.router = APIRouter(prefix="/wireguard", tags=["wireguard"])
        self._setup_routes()

        # WebUI will be initialized by the base class when needed



    async def initialize(self) -> bool:
        """Initialize the WireGuard plugin."""
        try:
            self.logger.info("Initializing WireGuard plugin...")

            # Check if WireGuard tools are installed
            if not await self._check_wireguard_tools():
                self.log_error("WireGuard tools not found. Please install wireguard-tools package.")
                return False

            # Initialize default configuration
            default_config = {
                "interface_name": "wg0",
                "listen_port": 51820,
                "network_range": "10.0.0.0/24",
                "dns_servers": ["8.8.8.8", "8.8.4.4"],
                "mtu": 1420,
                "keep_alive": 25,
                "save_config": True,
                "table": "auto"
            }

            current_config = await self.repository.get_config()
            if not current_config:
                await self.repository.set_config("default", default_config)

            # Mark as initialized
            self.mark_initialized()

            # Force menu registration
            if self.webui_enabled:
                try:
                    import asyncio
                    await self.register_menu_entry()
                    self.logger.info("Menu registration completed during initialization")
                except Exception as e:
                    self.logger.error(f"Menu registration failed during initialization: {e}")

            self.logger.info("WireGuard plugin initialized successfully")
            return True

        except Exception as e:
            self.log_error(f"Failed to initialize WireGuard plugin: {str(e)}", e)
            return False

    async def shutdown(self) -> None:
        """Shutdown the WireGuard plugin."""
        try:
            self.logger.info("Shutting down WireGuard plugin...")

            # Stop all running servers
            servers = await self.list_servers(enabled=True)
            for server in servers:
                try:
                    await self._stop_wireguard_interface(server.name)
                except Exception as e:
                    self.logger.warning(f"Failed to stop server {server.name}: {e}")

            self.logger.info("WireGuard plugin shutdown complete")

        except Exception as e:
            self.log_error(f"Error during WireGuard plugin shutdown: {str(e)}", e)

    def get_api_routes(self) -> List[APIRouter]:
        """Return FastAPI routers for this plugin."""
        return [self.router]

    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema for this plugin."""
        return {
            "servers": {
                "description": "WireGuard server configurations",
                "fields": {
                    "id": "string",
                    "name": "string (interface name)",
                    "endpoint": "string",
                    "port": "integer",
                    "private_key": "string",
                    "public_key": "string",
                    "network": "string (CIDR)",
                    "dns_servers": "array of strings",
                    "allowed_ips": "array of strings",
                    "keep_alive": "integer",
                    "mtu": "integer",
                    "enabled": "boolean",
                    "description": "string",
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            },
            "clients": {
                "description": "WireGuard client configurations",
                "fields": {
                    "id": "string",
                    "name": "string (username)",
                    "server_id": "string",
                    "email": "string",
                    "private_key": "string",
                    "public_key": "string",
                    "preshared_key": "string",
                    "allocated_ip": "string (CIDR)",
                    "allowed_ips": "array of strings",
                    "dns_servers": "array of strings",
                    "persistent_keepalive": "integer",
                    "enabled": "boolean",
                    "group": "string",
                    "description": "string",
                    "created_at": "datetime",
                    "updated_at": "datetime"
                }
            },
            "config": {
                "description": "Plugin configuration",
                "fields": {
                    "interface_name": "string",
                    "listen_port": "integer",
                    "network_range": "string",
                    "dns_servers": "array",
                    "mtu": "integer",
                    "keep_alive": "integer"
                }
            }
        }

    # VPN Interface Implementation

    async def create_server(self, server_data: VPNServerCreate) -> VPNServerResponse:
        """Create a new WireGuard server."""
        try:
            # Check if server already exists
            existing = await self.repository.get_server_by_interface(server_data.name)
            if existing:
                raise VPNPluginError(f"Server with interface '{server_data.name}' already exists")

            # Validate IP address
            if not ValidationService.validate_ip_address(server_data.network):
                raise VPNPluginError(f"Invalid network address: {server_data.network}")

            # Generate keys if not provided
            private_key = server_data.private_key
            public_key = server_data.public_key
            if not private_key or not public_key:
                self.logger.info(f"Generating new keys for server {server_data.name}")
                private_key, public_key = KeyGenerationService.generate_server_keys()
                self.logger.info(f"Generated keys - Private: {private_key[:10]}..., Public: {public_key[:10]}...")

            # Create server record
            server_dict = {
                "name": server_data.name,
                "endpoint": server_data.endpoint,
                "port": server_data.port,
                "private_key": private_key,
                "public_key": public_key,
                "network": server_data.network,
                "dns_servers": server_data.dns_servers,
                "allowed_ips": server_data.allowed_ips,
                "keep_alive": server_data.keep_alive,
                "mtu": server_data.mtu,
                "enabled": server_data.enabled,
                "description": server_data.description,
                "config": server_data.config or {}
            }

            self.logger.info(f"Creating server with keys - Private: {server_dict['private_key'][:10] if server_dict['private_key'] else 'None'}...")

            server_id = await self.repository.create_item("servers", server_dict)

            # Start server if enabled
            if server_data.enabled:
                await self._start_wireguard_server(server_id)

            return await self._get_server_response(server_id)

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to create WireGuard server: {str(e)}")

    async def delete_server(self, server_id: str) -> bool:
        """Delete a WireGuard server."""
        try:
            server = await self.repository.get_item("servers", server_id)
            if not server:
                return False

            # Stop server if running
            try:
                await self._stop_wireguard_interface(server["name"])
            except Exception as e:
                self.logger.warning(f"Failed to stop server interface: {e}")

            # Delete all clients
            clients = await self.list_clients(server_id=server_id)
            for client in clients:
                await self.delete_client(client.id)

            # Delete server
            return await self.repository.delete_item("servers", server_id)

        except Exception as e:
            self.logger.error(f"Failed to delete server {server_id}: {e}")
            return False

    async def list_servers(self, **filters) -> List[VPNServerResponse]:
        """List all WireGuard servers."""
        try:
            servers = await self.repository.list_items("servers")

            # Apply filters
            if filters:
                servers = [s for s in servers if self._matches_filters(s, filters)]

            return [await self._server_dict_to_response(server) for server in servers]

        except Exception as e:
            self.logger.error(f"Failed to list servers: {e}")
            return []

    async def get_server(self, server_id: str) -> Optional[VPNServerResponse]:
        """Get a specific WireGuard server."""
        try:
            # Use the repository's get_server method to ensure fresh data
            server = await self.repository.get_server(server_id)
            if not server:
                self.logger.warning(f"Server {server_id} not found")
                return None

            self.logger.debug(f"Retrieved server {server_id} with private key: {server.get('private_key', 'N/A')[:10]}...")
            return await self._server_dict_to_response(server)

        except Exception as e:
            self.logger.error(f"Failed to get server {server_id}: {e}")
            return None

    async def update_server(self, server_id: str, update_data: VPNServerUpdate) -> Optional[VPNServerResponse]:
        """Update a WireGuard server."""
        try:
            updates = {k: v for k, v in update_data.dict().items() if v is not None}
            if not updates:
                return await self.get_server(server_id)

            # Validate network if being updated
            if "network" in updates and not ValidationService.validate_ip_address(updates["network"]):
                raise VPNPluginError(f"Invalid network address: {updates['network']}")

            success = await self.repository.update_item("servers", server_id, updates)
            if not success:
                return None

            # Handle server enable/disable state changes
            if "enabled" in updates:
                server = await self.repository.get_item("servers", server_id)
                if updates["enabled"]:
                    # Server is being enabled - start it
                    await self._start_wireguard_server(server_id)
                else:
                    # Server is being disabled - stop it
                    await self._stop_wireguard_interface(server["name"])
            elif any(key in updates for key in ["endpoint", "port", "network"]):
                # Other configuration changed - restart if server is enabled
                server = await self.repository.get_item("servers", server_id)
                if server and server.get("enabled"):
                    await self._restart_wireguard_server(server_id)

            return await self.get_server(server_id)

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to update server {server_id}: {str(e)}")

    async def create_client(self, client_data: VPNClientCreate) -> VPNClientResponse:
        """Create a new WireGuard client."""
        try:
            # Verify server exists
            server = await self.repository.get_item("servers", client_data.server_id)
            if not server:
                raise VPNPluginError(f"Server {client_data.server_id} not found")

            # Check if client already exists
            existing = await self.repository.get_client_for_server(client_data.server_id, client_data.name)
            if existing:
                raise VPNPluginError(f"Client '{client_data.name}' already exists on this server")

            # Generate keys if not provided
            private_key = client_data.private_key
            public_key = client_data.public_key
            if not private_key:
                keys = KeyGenerationService.generate_key_triplet()
                private_key = keys.private_key
                public_key = keys.public_key
                preshared_key = keys.preshared_key
            else:
                public_key = KeyGenerationService.derive_public_key(private_key)
                preshared_key = KeyGenerationService.generate_preshared_key()

            # Allocate IP address
            allocated_ip = await self._resolve_private_ip(server, client_data.name, "auto")

            # Validate IPs
            ValidationService.validate_peer_ips(allocated_ip, ",".join(client_data.allowed_ips))

            # Create client record
            client_dict = {
                "name": client_data.name,
                "server_id": client_data.server_id,
                "email": client_data.email,
                "private_key": private_key,
                "public_key": public_key,
                "preshared_key": preshared_key,
                "allocated_ip": allocated_ip,
                "allowed_ips": client_data.allowed_ips,
                "dns_servers": client_data.dns_servers,
                "persistent_keepalive": client_data.persistent_keepalive,
                "enabled": client_data.enabled,
                "group": "default",
                "description": client_data.description,
                "config": client_data.config or {}
            }

            client_id = await self.repository.create_item("clients", client_dict)

            # Update server configuration
            await self._update_server_config(client_data.server_id)

            return await self._get_client_response(client_id)

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to create WireGuard client: {str(e)}")

    async def delete_client(self, client_id: str) -> bool:
        """Delete a WireGuard client."""
        try:
            client = await self.repository.get_item("clients", client_id)
            if not client:
                return False

            server_id = client["server_id"]
            success = await self.repository.delete_item("clients", client_id)

            if success:
                # Update server configuration
                await self._update_server_config(server_id)

            return success

        except Exception as e:
            self.logger.error(f"Failed to delete client {client_id}: {e}")
            return False

    async def list_clients(self, server_id: Optional[str] = None, **filters) -> List[VPNClientResponse]:
        """List WireGuard clients."""
        try:
            clients = await self.repository.list_items("clients")

            # Filter by server if specified
            if server_id:
                clients = [c for c in clients if c.get("server_id") == server_id]

            # Apply additional filters
            if filters:
                clients = [c for c in clients if self._matches_filters(c, filters)]

            return [await self._client_dict_to_response(client) for client in clients]

        except Exception as e:
            self.logger.error(f"Failed to list clients: {e}")
            return []

    async def get_client(self, client_id: str) -> Optional[VPNClientResponse]:
        """Get a specific WireGuard client."""
        try:
            client = await self.repository.get_item("clients", client_id)
            if not client:
                return None

            return await self._client_dict_to_response(client)

        except Exception as e:
            self.logger.error(f"Failed to get client {client_id}: {e}")
            return None

    async def update_client(self, client_id: str, update_data: VPNClientUpdate) -> Optional[VPNClientResponse]:
        """Update a WireGuard client."""
        try:
            updates = {k: v for k, v in update_data.dict().items() if v is not None}
            if not updates:
                return await self.get_client(client_id)

            client = await self.repository.get_item("clients", client_id)
            if not client:
                return None

            # Validate allowed IPs if being updated
            if "allowed_ips" in updates:
                ValidationService.validate_allowed_ips_format(",".join(updates["allowed_ips"]))

            success = await self.repository.update_item("clients", client_id, updates)
            if not success:
                return None

            # Update server configuration
            await self._update_server_config(client["server_id"])

            return await self.get_client(client_id)

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to update client {client_id}: {str(e)}")

    async def generate_config(self, client_id: str, format: str = "wireguard") -> VPNConfigResponse:
        """Generate configuration file for a client."""
        try:
            client = await self.repository.get_item("clients", client_id)
            if not client:
                raise VPNPluginError(f"Client {client_id} not found")

            server = await self.repository.get_item("servers", client["server_id"])
            if not server:
                raise VPNPluginError(f"Server {client['server_id']} not found")

            # Generate WireGuard config
            config_content = WireGuardConfigRenderer.render_client_config(client, server)

            # Generate QR code
            qr_code_data = None
            if format == "wireguard":
                qr_code_data = self._generate_qr_code(config_content)

            return VPNConfigResponse(
                config_content=config_content,
                qr_code=qr_code_data,
                format=format
            )

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to generate config for client {client_id}: {str(e)}")

    async def get_connection_status(self, server_id: str, client_id: Optional[str] = None) -> VPNConnectionStatus:
        """Get connection status for server or specific client."""
        try:
            server = await self.repository.get_item("servers", server_id)
            if not server:
                raise VPNPluginError(f"Server {server_id} not found")

            # Get WireGuard interface status
            status_info = await self._get_interface_status(server["name"])

            if client_id:
                # Get specific client status
                client = await self.repository.get_item("clients", client_id)
                if not client:
                    raise VPNPluginError(f"Client {client_id} not found")

                return VPNConnectionStatus(
                    server_id=server_id,
                    client_id=client_id,
                    status="connected" if status_info.get("active") else "disconnected",
                    connected_clients=1 if status_info.get("active") else 0,
                    total_clients=1,
                    transfer_rx=status_info.get("rx_bytes", 0),
                    transfer_tx=status_info.get("tx_bytes", 0)
                )
            else:
                # Get server status
                clients = await self.list_clients(server_id=server_id)
                active_clients = len([c for c in clients if c.status == "connected"])

                return VPNConnectionStatus(
                    server_id=server_id,
                    status="connected" if status_info.get("active") else "disconnected",
                    connected_clients=active_clients,
                    total_clients=len(clients),
                    transfer_rx=status_info.get("rx_bytes", 0),
                    transfer_tx=status_info.get("tx_bytes", 0)
                )

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to get connection status: {str(e)}")

    async def revoke_client(self, client_id: str) -> bool:
        """Revoke a WireGuard client."""
        try:
            update_data = VPNClientUpdate(enabled=False)
            result = await self.update_client(client_id, update_data)
            return result is not None

        except Exception as e:
            self.logger.error(f"Failed to revoke client {client_id}: {e}")
            return False

    async def restart_server(self, server_id: str) -> bool:
        """Restart a WireGuard server."""
        try:
            server = await self.repository.get_server(server_id)
            if not server:
                return False

            # Stop the server first
            success_stop = await self._stop_wireguard_interface(server.get("interface_name", "wg0"))

            # Start the server again
            success_start = await self._start_wireguard_server(server_id)

            return success_stop and success_start

        except Exception as e:
            self.logger.error(f"Failed to restart server {server_id}: {e}")
            return False

    async def regenerate_server_keys(self, server_id: str) -> bool:
        """Regenerate server keys."""
        try:
            server = await self.repository.get_server(server_id)
            if not server:
                self.logger.error(f"Server {server_id} not found")
                return False

            self.logger.info(f"Regenerating keys for server {server_id}")

            # Generate new keys using the keypair method (not triplet)
            private_key, public_key = KeyGenerationService.generate_server_keys()

            self.logger.info(f"Generated new keys - Private: {private_key[:10]}..., Public: {public_key[:10]}...")

            # Update server with new keys
            update_data = {
                "private_key": private_key,
                "public_key": public_key
            }

            success = await self.repository.update_server(server_id, update_data)
            if not success:
                self.logger.error(f"Failed to update server {server_id} with new keys")
                return False

            self.logger.info(f"Successfully updated server {server_id} with new keys")

            # Update server configuration
            await self._update_server_config(server_id)

            return True

        except Exception as e:
            self.logger.error(f"Failed to regenerate keys for server {server_id}: {e}")
            return False

    async def get_server_config(self, server_id: str) -> str:
        """Get server configuration content."""
        try:
            server = await self.repository.get_server(server_id)
            if not server:
                raise VPNPluginError(f"Server {server_id} not found")

            clients = await self.repository.get_clients(server_id=server_id)

            # Generate server configuration
            config_content = WireGuardConfigRenderer.render_server_config(server, clients)

            return config_content

        except Exception as e:
            self.logger.error(f"Failed to get config for server {server_id}: {e}")
            raise VPNPluginError(f"Failed to get server config: {str(e)}")

    async def restart_service(self) -> bool:
        """Restart the entire WireGuard service."""
        try:
            # Get all active servers
            servers = await self.repository.get_servers()

            # Stop all interfaces
            for server in servers:
                if server.get("enabled", False):
                    interface_name = server.get("interface_name", "wg0")
                    await self._stop_wireguard_interface(interface_name)

            # Wait a moment
            await asyncio.sleep(1)

            # Start all enabled servers again
            success = True
            for server in servers:
                if server.get("enabled", False):
                    result = await self._start_wireguard_server(server["id"])
                    success = success and result

            return success

        except Exception as e:
            self.logger.error(f"Failed to restart WireGuard service: {e}")
            return False

    async def get_logs(self) -> List[Dict[str, Any]]:
        """Get WireGuard logs."""
        try:
            logs = []

            # Try to get system logs related to WireGuard
            try:
                # Get journalctl logs for WireGuard
                result = await asyncio.create_subprocess_exec(
                    'journalctl', '-u', 'wg-quick@*', '--no-pager', '-n', '100', '--output=json',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await result.communicate()

                if result.returncode == 0:
                    import json
                    for line in stdout.decode().strip().split('\n'):
                        if line.strip():
                            try:
                                log_entry = json.loads(line)
                                logs.append({
                                    'timestamp': datetime.fromisoformat(log_entry.get('__REALTIME_TIMESTAMP', '')[:-6]) if log_entry.get('__REALTIME_TIMESTAMP') else datetime.now(),
                                    'level': 'INFO',
                                    'component': 'WireGuard',
                                    'message': log_entry.get('MESSAGE', '')
                                })
                            except (json.JSONDecodeError, ValueError):
                                continue

            except Exception as e:
                self.logger.warning(f"Could not get system logs: {e}")

            # Add some plugin-specific logs
            logs.extend([
                {
                    'timestamp': datetime.now(),
                    'level': 'INFO',
                    'component': 'Plugin',
                    'message': f'WireGuard plugin {self.version} is running'
                },
                {
                    'timestamp': datetime.now(),
                    'level': 'INFO',
                    'component': 'Plugin',
                    'message': f'Servers count: {len(await self.list_servers())}'
                }
            ])

            # Sort by timestamp, newest first
            logs.sort(key=lambda x: x['timestamp'], reverse=True)

            return logs[:100]  # Return last 100 logs

        except Exception as e:
            self.logger.error(f"Failed to get logs: {e}")
            return [
                {
                    'timestamp': datetime.now(),
                    'level': 'ERROR',
                    'component': 'Plugin',
                    'message': f'Failed to retrieve logs: {str(e)}'
                }
            ]

    async def clear_logs(self) -> bool:
        """Clear WireGuard logs."""
        try:
            # For now, we'll just return True as clearing system logs
            # would typically require specific system permissions
            # In a real implementation, you might clear application-specific logs
            self.logger.info("Logs cleared by user request")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear logs: {e}")
            return False

    # Helper Methods

    async def _resolve_private_ip(self, server: Dict[str, Any], username: str, requested: str) -> str:
        """Resolve the private IP for a peer, auto-allocating if needed."""
        requested = (requested or '').strip()
        if requested and requested.lower() != 'auto':
            return requested

        return await self.repository.get_next_ip(server["id"], server["network"])

    def _generate_qr_code(self, config_content: str) -> str:
        """Generate QR code for configuration."""
        return QRCodeService.generate_qr_code(config_content)

    async def _check_wireguard_tools(self) -> bool:
        """Check if WireGuard tools are installed."""
        return await WireGuardSystemService.check_wireguard_tools()

    async def _start_wireguard_server(self, server_id: str) -> bool:
        """Start WireGuard server interface."""
        try:
            server = await self.repository.get_item("servers", server_id)
            if not server:
                return False

            # Generate server configuration
            clients = await self.list_clients(server_id=server_id, enabled=True)
            config_content = WireGuardConfigRenderer.render_server_config(
                server, [client.__dict__ for client in clients]
            )

            # Write configuration file
            config_dir = Path("/etc/wireguard")
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / f"{server['name']}.conf"

            with open(config_file, 'w') as f:
                f.write(config_content)

            # Start interface
            result = await asyncio.create_subprocess_exec(
                "wg-quick", "up", server['name'],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Failed to start WireGuard server: {e}")
            return False

    async def _stop_wireguard_interface(self, interface_name: str) -> bool:
        """Stop WireGuard interface."""
        success = await WireGuardSystemService.stop_interface(interface_name)
        if not success:
            self.logger.error(f"Failed to stop WireGuard interface {interface_name}")
        return success

    async def _get_interface_status(self, interface_name: str) -> Dict[str, Any]:
        """Get interface status information."""
        return await WireGuardSystemService.get_interface_status(interface_name)

    async def _update_server_config(self, server_id: str) -> None:
        """Update server configuration and restart if needed."""
        try:
            server = await self.repository.get_item("servers", server_id)
            if server and server.get("enabled"):
                await self._restart_wireguard_server(server_id)
        except Exception as e:
            self.logger.error(f"Failed to update server config: {e}")

    async def _restart_wireguard_server(self, server_id: str) -> bool:
        """Restart WireGuard server."""
        try:
            server = await self.repository.get_item("servers", server_id)
            if not server:
                return False

            await self._stop_wireguard_interface(server["name"])
            return await self._start_wireguard_server(server_id)

        except Exception as e:
            self.logger.error(f"Failed to restart WireGuard server: {e}")
            return False

    def _matches_filters(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if item matches filter criteria."""
        for key, value in filters.items():
            if key not in item or item[key] != value:
                return False
        return True

    async def _server_dict_to_response(self, server: Dict[str, Any]) -> VPNServerResponse:
        """Convert server dict to response model."""
        clients = await self.list_clients(server_id=server["id"])

        return VPNServerResponse(
            id=server["id"],
            name=server["name"],
            endpoint=server["endpoint"],
            port=server["port"],
            private_key=server.get("private_key"),
            public_key=server["public_key"],
            network=server["network"],
            dns_servers=server.get("dns_servers", []),
            allowed_ips=server.get("allowed_ips", []),
            keep_alive=server.get("keep_alive"),
            mtu=server.get("mtu"),
            enabled=server["enabled"],
            description=server.get("description"),
            created_at=datetime.fromisoformat(server["created_at"]),
            updated_at=datetime.fromisoformat(server["updated_at"]),
            client_count=len(clients),
            status="active" if server["enabled"] else "inactive",
            config=server.get("config")
        )

    async def _client_dict_to_response(self, client: Dict[str, Any]) -> VPNClientResponse:
        """Convert client dict to response model."""
        return VPNClientResponse(
            id=client["id"],
            name=client["name"],
            server_id=client["server_id"],
            email=client.get("email"),
            public_key=client["public_key"],
            private_key=client["private_key"],
            allowed_ips=client.get("allowed_ips", []),
            dns_servers=client.get("dns_servers"),
            persistent_keepalive=client.get("persistent_keepalive"),
            enabled=client["enabled"],
            description=client.get("description"),
            created_at=datetime.fromisoformat(client["created_at"]),
            updated_at=datetime.fromisoformat(client["updated_at"]),
            last_handshake=None,  # Would get from interface status
            transfer_rx=0,  # Would get from interface status
            transfer_tx=0,  # Would get from interface status
            endpoint=None,
            status="unknown",  # Would get from interface status
            config=client.get("config")
        )

    async def _get_server_response(self, server_id: str) -> VPNServerResponse:
        """Get server response by ID."""
        server = await self.get_server(server_id)
        if not server:
            raise VPNPluginError(f"Server {server_id} not found")
        return server

    async def _get_client_response(self, client_id: str) -> VPNClientResponse:
        """Get client response by ID."""
        client = await self.get_client(client_id)
        if not client:
            raise VPNPluginError(f"Client {client_id} not found")
        return client

    def _setup_routes(self) -> None:
        """Setup comprehensive API routes for WireGuard plugin."""
        from fastapi.responses import FileResponse, PlainTextResponse

        # Server Management Routes
        @self.router.get("/servers", response_model=List[VPNServerResponse])
        async def list_servers(user = Depends(current_active_user)):
            return await self.list_servers()

        @self.router.post("/servers", response_model=VPNServerResponse)
        async def create_server(server_data: VPNServerCreate, user = Depends(current_active_user)):
            return await self.create_server(server_data)

        @self.router.get("/servers/{server_id}", response_model=VPNServerResponse)
        async def get_server(server_id: str, user = Depends(current_active_user)):
            server = await self.get_server(server_id)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            return server

        @self.router.put("/servers/{server_id}", response_model=VPNServerResponse)
        async def update_server(server_id: str, update_data: VPNServerUpdate, user = Depends(current_active_user)):
            server = await self.update_server(server_id, update_data)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")
            return server

        @self.router.delete("/servers/{server_id}")
        async def delete_server(server_id: str, user = Depends(current_active_user)):
            success = await self.delete_server(server_id)
            if not success:
                raise HTTPException(status_code=404, detail="Server not found")
            return {"success": True, "detail": "Server deleted"}

        @self.router.post("/servers/{server_id}/start")
        async def start_server(server_id: str, user = Depends(current_active_user)):
            success = await self.start_server(server_id)
            return {"success": success, "detail": "Server started" if success else "Failed to start server"}

        @self.router.post("/servers/{server_id}/stop")
        async def stop_server(server_id: str, user = Depends(current_active_user)):
            success = await self.stop_server(server_id)
            return {"success": success, "detail": "Server stopped" if success else "Failed to stop server"}

        @self.router.post("/servers/{server_id}/restart")
        async def restart_server(server_id: str, user = Depends(current_active_user)):
            success = await self.restart_server(server_id)
            return {"success": success, "detail": "Server restarted" if success else "Failed to restart server"}

        @self.router.get("/servers/{server_id}/status", response_model=VPNConnectionStatus)
        async def get_server_status(server_id: str, user = Depends(current_active_user)):
            return await self.get_connection_status(server_id)

        @self.router.get("/servers/{server_id}/statistics")
        async def get_server_statistics(server_id: str, user = Depends(current_active_user)):
            stats = await self.get_server_statistics(server_id)
            return stats

        @self.router.post("/servers/{server_id}/persist")
        async def persist_server_config(server_id: str, user = Depends(current_active_user)):
            server = await self.repository.get_item("servers", server_id)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")

            clients = await self.list_clients(server_id=server_id)
            config_content = WireGuardConfigRenderer.render_server_config(
                server, [client.__dict__ for client in clients]
            )

            filename = f"{server['name']}.conf"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(config_content)
            return FileResponse(filename, media_type="text/plain", filename=filename)

        @self.router.post("/servers/{server_id}/backup")
        async def backup_server_config(server_id: str, user = Depends(current_active_user)):
            backup = await self.backup_server_config(server_id)
            return backup

        @self.router.post("/servers/restore")
        async def restore_server_config(backup_data: dict, user = Depends(current_active_user)):
            server_id = await self.restore_server_config(backup_data)
            return {"success": True, "server_id": server_id, "detail": "Server configuration restored"}

        # Client Management Routes
        @self.router.get("/clients", response_model=List[VPNClientResponse])
        async def list_clients(server_id: Optional[str] = Query(None), user = Depends(current_active_user)):
            return await self.list_clients(server_id=server_id)

        @self.router.post("/clients", response_model=VPNClientResponse)
        async def create_client(client_data: VPNClientCreate, user = Depends(current_active_user)):
            return await self.create_client(client_data)

        @self.router.post("/servers/{server_id}/clients", response_model=VPNClientResponse)
        async def create_client_for_server(server_id: str, client_data: VPNClientCreate, user = Depends(current_active_user)):
            client_data.server_id = server_id
            return await self.create_client(client_data)

        @self.router.get("/clients/{client_id}", response_model=VPNClientResponse)
        async def get_client(client_id: str, user = Depends(current_active_user)):
            client = await self.get_client(client_id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            return client

        @self.router.put("/clients/{client_id}", response_model=VPNClientResponse)
        async def update_client(client_id: str, update_data: VPNClientUpdate, user = Depends(current_active_user)):
            client = await self.update_client(client_id, update_data)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            return client

        @self.router.delete("/clients/{client_id}")
        async def delete_client(client_id: str, user = Depends(current_active_user)):
            success = await self.delete_client(client_id)
            if not success:
                raise HTTPException(status_code=404, detail="Client not found")
            return {"success": True, "detail": "Client deleted"}

        @self.router.post("/clients/{client_id}/enable")
        async def enable_client(client_id: str, user = Depends(current_active_user)):
            update_data = VPNClientUpdate(enabled=True)
            updated_client = await self.update_client(client_id, update_data)
            if not updated_client:
                raise HTTPException(status_code=404, detail="Client not found")
            return {"success": True, "detail": "Client enabled"}

        @self.router.post("/clients/{client_id}/disable")
        async def disable_client(client_id: str, user = Depends(current_active_user)):
            update_data = VPNClientUpdate(enabled=False)
            updated_client = await self.update_client(client_id, update_data)
            if not updated_client:
                raise HTTPException(status_code=404, detail="Client not found")
            return {"success": True, "detail": "Client disabled"}

        @self.router.post("/clients/{client_id}/revoke")
        async def revoke_client(client_id: str, user = Depends(current_active_user)):
            success = await self.revoke_client(client_id)
            return {"success": success, "detail": "Client revoked" if success else "Failed to revoke client"}

        @self.router.get("/clients/{client_id}/status", response_model=VPNConnectionStatus)
        async def get_client_status(client_id: str, user = Depends(current_active_user)):
            client = await self.repository.get_item("clients", client_id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            return await self.get_connection_status(client["server_id"], client_id)

        # Configuration and File Generation Routes
        @self.router.get("/clients/{client_id}/config", response_model=VPNConfigResponse)
        async def get_client_config(client_id: str, user = Depends(current_active_user)):
            return await self.generate_config(client_id)

        @self.router.post("/clients/{client_id}/persist")
        async def persist_client_config(
            client_id: str,
            custom_allowed_ips: Optional[str] = Query(None),
            user = Depends(current_active_user)
        ):
            client = await self.repository.get_item("clients", client_id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")

            server = await self.repository.get_item("servers", client["server_id"])
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")

            # Use custom allowed IPs if provided
            if custom_allowed_ips:
                ValidationService.validate_allowed_ips_format(custom_allowed_ips)
                client = client.copy()
                client["allowed_ips"] = custom_allowed_ips.split(',')

            config_content = WireGuardConfigRenderer.render_client_config(client, server)

            filename = f"{client['name']}.conf"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(config_content)
            return FileResponse(filename, media_type="text/plain", filename=filename)

        # Legacy compatibility routes (for backward compatibility)
        @self.router.put("/clients/{client_id}/allowed_ips", response_model=VPNClientResponse)
        async def update_client_allowed_ips(
            client_id: str,
            allowed_ips: str = Query(...),
            user = Depends(current_active_user)
        ):
            client = await self.repository.get_item("clients", client_id)
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")

            ValidationService.validate_allowed_ips_format(allowed_ips)
            update_data = VPNClientUpdate(allowed_ips=allowed_ips.split(','))

            updated_client = await self.update_client(client_id, update_data)
            if not updated_client:
                raise HTTPException(status_code=404, detail="Failed to update client")
            return updated_client

        @self.router.put("/servers/{server_id}/clients/{client_username}", response_model=VPNClientResponse)
        async def update_client_by_username(
            server_id: str,
            client_username: str,
            update_data: VPNClientUpdate,
            user = Depends(current_active_user)
        ):
            # Find client by username and server
            clients = await self.list_clients(server_id=server_id)
            target_client = None
            for client in clients:
                if client.name == client_username:
                    target_client = client
                    break

            if not target_client:
                raise HTTPException(status_code=404, detail="Client not found")

            updated_client = await self.update_client(target_client.id, update_data)
            if not updated_client:
                raise HTTPException(status_code=404, detail="Failed to update client")
            return updated_client

        @self.router.delete("/servers/{server_id}/clients/{client_username}")
        async def delete_client_by_username(
            server_id: str,
            client_username: str,
            user = Depends(current_active_user)
        ):
            # Find client by username and server
            clients = await self.list_clients(server_id=server_id)
            target_client = None
            for client in clients:
                if client.name == client_username:
                    target_client = client
                    break

            if not target_client:
                raise HTTPException(status_code=404, detail="Client not found")

            success = await self.delete_client(target_client.id)
            if not success:
                raise HTTPException(status_code=404, detail="Failed to delete client")
            return {"success": True, "detail": "Client deleted"}

        @self.router.post("/clients/{client_username}/persist")
        async def persist_client_config_by_username(
            client_username: str,
            custom_allowed_ips: Optional[str] = Query(None),
            user = Depends(current_active_user)
        ):
            # Find client by username
            all_clients = await self.list_clients()
            target_client = None
            for client in all_clients:
                if client.name == client_username:
                    target_client = client
                    break

            if not target_client:
                raise HTTPException(status_code=404, detail="Client not found")

            return await persist_client_config(target_client.id, custom_allowed_ips, user)

        # Utility Routes
        @self.router.get("/next_ip")
        async def get_next_ip(
            server_id: Optional[str] = Query(None),
            user = Depends(current_active_user)
        ):
            if not server_id:
                return PlainTextResponse(IPAllocationService.get_first_ip_when_empty(""))

            server = await self.repository.get_item("servers", server_id)
            if not server:
                raise HTTPException(status_code=404, detail="Server not found")

            clients = await self.list_clients(server_id=server_id)
            used_ips = {client.allocated_ip.split('/')[0] for client in clients if client.allocated_ip and '/' in client.allocated_ip}

            if not used_ips:
                return PlainTextResponse(IPAllocationService.get_first_ip_when_empty(server_id))

            return PlainTextResponse(IPAllocationService.increment_ip(used_ips))

        # Plugin Information Routes
        @self.router.get("/info")
        async def get_plugin_info(user = Depends(current_active_user)):
            return self.get_info()

        @self.router.get("/health")
        async def get_plugin_health(user = Depends(current_active_user)):
            return self.get_health_status()

        @self.router.get("/metrics")
        async def get_plugin_metrics(user = Depends(current_active_user)):
            return self.get_metrics()

        @self.router.get("/schema")
        async def get_database_schema(user = Depends(current_active_user)):
            return self.get_database_schema()

        # Administrative Routes
        @self.router.post("/reload")
        async def reload_plugin(user = Depends(current_active_user)):
            # This would typically be handled by the plugin manager
            return {"success": True, "detail": "Plugin reload requested"}

        @self.router.get("/routes")
        async def list_plugin_routes(user = Depends(current_active_user)):
            routes = []
            for route in self.router.routes:
                if hasattr(route, 'methods') and hasattr(route, 'path'):
                    routes.append({
                        "path": route.path,
                        "methods": list(route.methods),
                        "name": getattr(route, 'name', None),
                        "summary": getattr(route, 'summary', None)
                    })
            return {"routes": routes, "total": len(routes)}
