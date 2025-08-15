"""WireGuard services and utilities.

This module contains all WireGuard-specific services, utilities, and dependencies
to keep the plugin completely self-contained and isolated from the main application.
"""

import base64
import secrets
import ipaddress
import qrcode
import io
from typing import Dict, List, Optional, Any, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from app.plugins.base import VPNPluginError


class KeyTriplet:
    """Container for WireGuard key triplet (private, public, preshared)."""

    def __init__(self, private_key: str, public_key: str, preshared_key: str):
        self.private_key = private_key
        self.public_key = public_key
        self.preshared_key = preshared_key


class KeyGenerationService:
    """Service for generating WireGuard cryptographic keys."""

    @staticmethod
    def generate_private_key() -> str:
        """Generate a WireGuard private key.

        Returns:
            str: Base64-encoded private key.
        """
        private_key = X25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        return base64.b64encode(private_bytes).decode('ascii')

    @staticmethod
    def derive_public_key(private_key: str) -> str:
        """Derive public key from private key.

        Args:
            private_key: Base64-encoded private key.

        Returns:
            str: Base64-encoded public key.

        Raises:
            VPNPluginError: If key derivation fails.
        """
        try:
            private_bytes = base64.b64decode(private_key)
            private_key_obj = X25519PrivateKey.from_private_bytes(private_bytes)
            public_bytes = private_key_obj.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            return base64.b64encode(public_bytes).decode('ascii')
        except Exception as e:
            raise VPNPluginError(f"Failed to derive public key: {str(e)}")

    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """Generate a WireGuard keypair.

        Returns:
            Tuple[str, str]: (private_key, public_key) pair.
        """
        private_key = KeyGenerationService.generate_private_key()
        public_key = KeyGenerationService.derive_public_key(private_key)
        return private_key, public_key

    @staticmethod
    def generate_preshared_key() -> str:
        """Generate a WireGuard preshared key.

        Returns:
            str: Base64-encoded preshared key.
        """
        key_bytes = secrets.token_bytes(32)
        return base64.b64encode(key_bytes).decode('ascii')

    @staticmethod
    def generate_server_keys() -> Tuple[str, str]:
        """Generate server keypair.

        Returns:
            Tuple[str, str]: (private_key, public_key) pair.
        """
        return KeyGenerationService.generate_keypair()

    @staticmethod
    def generate_key_triplet() -> KeyTriplet:
        """Generate private key, public key, and preshared key.

        Returns:
            KeyTriplet: Container with all three keys.
        """
        private_key, public_key = KeyGenerationService.generate_keypair()
        preshared_key = KeyGenerationService.generate_preshared_key()
        return KeyTriplet(private_key, public_key, preshared_key)

    @staticmethod
    def validate_private_key(private_key: str) -> bool:
        """Validate a WireGuard private key format.

        Args:
            private_key: Private key to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            private_bytes = base64.b64decode(private_key)
            return len(private_bytes) == 32
        except Exception:
            return False

    @staticmethod
    def validate_public_key(public_key: str) -> bool:
        """Validate a WireGuard public key format.

        Args:
            public_key: Public key to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            public_bytes = base64.b64decode(public_key)
            return len(public_bytes) == 32
        except Exception:
            return False


class IPAllocationService:
    """Service for IP address allocation and management."""

    @staticmethod
    def get_next_available_ip(server_interface: str, server_address: str, used_ips: Optional[set] = None) -> str:
        """Get the next available IP address in the server network.

        Args:
            server_interface: Server interface name (for logging).
            server_address: Server network address in CIDR format.
            used_ips: Set of already used IP addresses.

        Returns:
            str: Next available IP address in CIDR format.

        Raises:
            VPNPluginError: If no IP addresses are available.
        """
        try:
            # Parse server network
            network = ipaddress.IPv4Network(server_address, strict=False)

            if used_ips is None:
                used_ips = set()

            # Server typically uses the first IP (gateway)
            gateway_ip = str(network.network_address + 1)
            used_ips.add(gateway_ip)

            # Find next available IP
            for ip in network.hosts():
                ip_str = str(ip)
                if ip_str not in used_ips:
                    return f"{ip_str}/{network.prefixlen}"

            raise VPNPluginError(f"No available IP addresses in network {server_address}")

        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to allocate IP address: {str(e)}")

    @staticmethod
    def get_first_ip_when_empty(server_interface: str, server_network: str = "10.0.0.0/24") -> str:
        """Get the first available IP when no peers exist.

        Args:
            server_interface: Server interface name.
            server_network: Server network in CIDR format.

        Returns:
            str: First available IP address.
        """
        try:
            network = ipaddress.IPv4Network(server_network, strict=False)
            # First IP is gateway (network + 1), second is first client (network + 2)
            first_client_ip = str(network.network_address + 2)
            return f"{first_client_ip}/{network.prefixlen}"
        except Exception:
            # Fallback to default
            return "10.0.0.2/24"

    @staticmethod
    def increment_ip(used_ips: set, network: str = "10.0.0.0/24") -> str:
        """Find the next available IP given a set of used IPs.

        Args:
            used_ips: Set of used IP addresses (without CIDR).
            network: Network in CIDR format.

        Returns:
            str: Next available IP address in CIDR format.

        Raises:
            VPNPluginError: If no available IP addresses.
        """
        try:
            net = ipaddress.IPv4Network(network, strict=False)

            # Convert used_ips to IPv4Address objects for proper comparison
            used_addresses = set()
            for ip_str in used_ips:
                try:
                    used_addresses.add(ipaddress.IPv4Address(ip_str))
                except:
                    continue  # Skip invalid IPs

            # Find next available IP
            for ip in net.hosts():
                if ip not in used_addresses:
                    return f"{str(ip)}/{net.prefixlen}"

            raise VPNPluginError(f"No available IP addresses in network {network}")
        except Exception as e:
            if isinstance(e, VPNPluginError):
                raise
            raise VPNPluginError(f"Failed to find next IP: {str(e)}")

    @staticmethod
    def validate_ip_in_network(ip_address: str, network: str) -> bool:
        """Validate that an IP address is within a network.

        Args:
            ip_address: IP address to validate (with or without CIDR).
            network: Network in CIDR format.

        Returns:
            bool: True if IP is in network, False otherwise.
        """
        try:
            # Remove CIDR from IP if present
            if '/' in ip_address:
                ip_address = ip_address.split('/')[0]

            ip = ipaddress.IPv4Address(ip_address)
            net = ipaddress.IPv4Network(network, strict=False)
            return ip in net
        except Exception:
            return False

    @staticmethod
    def get_network_info(network: str) -> Dict[str, Any]:
        """Get information about a network.

        Args:
            network: Network in CIDR format.

        Returns:
            Dict[str, Any]: Network information.
        """
        try:
            net = ipaddress.IPv4Network(network, strict=False)
            return {
                "network": str(net.network_address),
                "netmask": str(net.netmask),
                "broadcast": str(net.broadcast_address),
                "prefix_length": net.prefixlen,
                "num_addresses": net.num_addresses,
                "num_hosts": len(list(net.hosts())),
                "gateway": str(net.network_address + 1),
                "first_host": str(net.network_address + 2),
                "last_host": str(net.broadcast_address - 1)
            }
        except Exception as e:
            raise VPNPluginError(f"Failed to get network info: {str(e)}")


class ValidationService:
    """Service for validating WireGuard configurations and inputs."""

    @staticmethod
    def validate_ip_address(address: str) -> bool:
        """Validate IP address or network format.

        Args:
            address: IP address or network in CIDR format.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            ipaddress.IPv4Network(address, strict=False)
            return True
        except ValueError:
            try:
                ipaddress.IPv4Address(address)
                return True
            except ValueError:
                return False

    @staticmethod
    def validate_peer_ips(private_ip: str, allowed_ips: str) -> None:
        """Validate peer IP addresses.

        Args:
            private_ip: Private IP address in CIDR format.
            allowed_ips: Comma-separated list of allowed IP ranges.

        Raises:
            VPNPluginError: If validation fails.
        """
        try:
            # Validate private IP
            ipaddress.IPv4Network(private_ip, strict=False)

            # Validate allowed IPs
            ValidationService.validate_allowed_ips_format(allowed_ips)

        except ValueError as e:
            raise VPNPluginError(f"Invalid IP configuration: {str(e)}")

    @staticmethod
    def validate_allowed_ips_format(allowed_ips: str) -> None:
        """Validate allowed IPs format.

        Args:
            allowed_ips: Comma-separated list of IP ranges.

        Raises:
            VPNPluginError: If format is invalid.
        """
        try:
            for ip_range in allowed_ips.split(','):
                ip_range = ip_range.strip()
                if ip_range:
                    ipaddress.IPv4Network(ip_range, strict=False)
        except ValueError as e:
            raise VPNPluginError(f"Invalid allowed IPs format: {str(e)}")

    @staticmethod
    def validate_port(port: int) -> bool:
        """Validate port number.

        Args:
            port: Port number to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return 1 <= port <= 65535

    @staticmethod
    def validate_mtu(mtu: int) -> bool:
        """Validate MTU value.

        Args:
            mtu: MTU value to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        return 576 <= mtu <= 1500

    @staticmethod
    def validate_interface_name(name: str) -> bool:
        """Validate WireGuard interface name.

        Args:
            name: Interface name to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        import re
        # Interface name should be alphanumeric and may contain hyphens/underscores
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name)) and len(name) <= 15

    @staticmethod
    def validate_endpoint(endpoint: str) -> bool:
        """Validate endpoint format (IP or hostname).

        Args:
            endpoint: Endpoint to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            # Try as IP address first
            ipaddress.IPv4Address(endpoint)
            return True
        except ValueError:
            # Try as hostname
            import re
            hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            return bool(re.match(hostname_pattern, endpoint))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format.

        Args:
            email: Email address to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))


class WireGuardConfigRenderer:
    """Service for rendering WireGuard configuration files."""

    @staticmethod
    def render_server_config(server: Dict[str, Any], clients: List[Dict[str, Any]]) -> str:
        """Render WireGuard server configuration file.

        Args:
            server: Server configuration dictionary.
            clients: List of client configuration dictionaries.

        Returns:
            str: Complete WireGuard server configuration.
        """
        config_lines = [
            "[Interface]",
            f"PrivateKey = {server['private_key']}",
            f"Address = {server['network']}",
            f"ListenPort = {server['port']}",
        ]

        if server.get("mtu"):
            config_lines.append(f"MTU = {server['mtu']}")

        # Add post-up and post-down scripts for iptables
        interface = server['name']
        config_lines.extend([
            f"PostUp = iptables -A FORWARD -i {interface} -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE",
            f"PostDown = iptables -D FORWARD -i {interface} -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE"
        ])

        # Add save config if specified
        if server.get("save_config", True):
            config_lines.append("SaveConfig = true")

        # Add client peers
        for client in clients:
            if client.get("enabled", True):
                config_lines.extend([
                    "",
                    "[Peer]",
                    f"PublicKey = {client['public_key']}",
                    f"AllowedIPs = {client['allocated_ip']}",
                ])

                if client.get("preshared_key"):
                    config_lines.append(f"PresharedKey = {client['preshared_key']}")

                if client.get("persistent_keepalive"):
                    config_lines.append(f"PersistentKeepalive = {client['persistent_keepalive']}")

        return "\n".join(config_lines)

    @staticmethod
    def render_client_config(client: Dict[str, Any], server: Dict[str, Any]) -> str:
        """Render WireGuard client configuration file.

        Args:
            client: Client configuration dictionary.
            server: Server configuration dictionary.

        Returns:
            str: Complete WireGuard client configuration.
        """
        config_lines = [
            "[Interface]",
            f"PrivateKey = {client['private_key']}",
            f"Address = {client['allocated_ip']}",
        ]

        # Add DNS if specified
        dns_servers = client.get("dns_servers") or server.get("dns_servers")
        if dns_servers:
            config_lines.append(f"DNS = {', '.join(dns_servers)}")

        if server.get("mtu"):
            config_lines.append(f"MTU = {server['mtu']}")

        config_lines.extend([
            "",
            "[Peer]",
            f"PublicKey = {server['public_key']}",
            f"Endpoint = {server['endpoint']}:{server['port']}",
            f"AllowedIPs = {', '.join(client.get('allowed_ips', ['0.0.0.0/0']))}",
        ])

        if client.get("preshared_key"):
            config_lines.append(f"PresharedKey = {client['preshared_key']}")

        if client.get("persistent_keepalive"):
            config_lines.append(f"PersistentKeepalive = {client['persistent_keepalive']}")

        return "\n".join(config_lines)

    @staticmethod
    def render_mobile_config(client: Dict[str, Any], server: Dict[str, Any]) -> str:
        """Render mobile-optimized WireGuard configuration.

        Args:
            client: Client configuration dictionary.
            server: Server configuration dictionary.

        Returns:
            str: Mobile-optimized WireGuard configuration.
        """
        # Mobile configs often have optimized settings
        config = WireGuardConfigRenderer.render_client_config(client, server)

        # Add mobile-specific optimizations if needed
        # For example, shorter keepalive intervals for mobile networks
        if not client.get("persistent_keepalive"):
            config += "\nPersistentKeepalive = 15"

        return config


class QRCodeService:
    """Service for generating QR codes for WireGuard configurations."""

    @staticmethod
    def generate_qr_code(config_content: str, size: int = 10, border: int = 5) -> str:
        """Generate QR code for WireGuard configuration.

        Args:
            config_content: WireGuard configuration content.
            size: QR code box size.
            border: QR code border size.

        Returns:
            str: Base64-encoded PNG image of QR code.

        Raises:
            VPNPluginError: If QR code generation fails.
        """
        try:
            qr = qrcode.QRCode(version=1, box_size=size, border=border)
            qr.add_data(config_content)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return base64.b64encode(buffer.getvalue()).decode('ascii')
        except Exception as e:
            raise VPNPluginError(f"Failed to generate QR code: {str(e)}")

    @staticmethod
    def generate_qr_code_svg(config_content: str) -> str:
        """Generate SVG QR code for WireGuard configuration.

        Args:
            config_content: WireGuard configuration content.

        Returns:
            str: SVG content of QR code.

        Raises:
            VPNPluginError: If QR code generation fails.
        """
        try:
            import qrcode.image.svg

            factory = qrcode.image.svg.SvgPathImage
            qr = qrcode.QRCode(image_factory=factory)
            qr.add_data(config_content)
            qr.make(fit=True)

            img = qr.make_image()
            return img.to_string().decode('utf-8')
        except Exception as e:
            raise VPNPluginError(f"Failed to generate SVG QR code: {str(e)}")


class WireGuardSystemService:
    """Service for interacting with WireGuard system tools."""

    @staticmethod
    async def check_wireguard_tools() -> bool:
        """Check if WireGuard tools are installed.

        Returns:
            bool: True if WireGuard tools are available.
        """
        import asyncio
        try:
            result = await asyncio.create_subprocess_exec(
                "wg", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    async def get_interface_status(interface_name: str) -> Dict[str, Any]:
        """Get WireGuard interface status.

        Args:
            interface_name: Name of the WireGuard interface.

        Returns:
            Dict[str, Any]: Interface status information.
        """
        import asyncio
        try:
            result = await asyncio.create_subprocess_exec(
                "wg", "show", interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0:
                # Parse WireGuard status output
                status = {
                    "active": True,
                    "rx_bytes": 0,
                    "tx_bytes": 0,
                    "peers": []
                }

                # TODO: Parse actual status from stdout
                # This would involve parsing the wg show output format

                return status
            else:
                return {"active": False, "error": stderr.decode(), "rx_bytes": 0, "tx_bytes": 0}

        except Exception as e:
            return {"active": False, "error": str(e), "rx_bytes": 0, "tx_bytes": 0}

    @staticmethod
    async def start_interface(interface_name: str) -> bool:
        """Start a WireGuard interface.

        Args:
            interface_name: Name of the interface to start.

        Returns:
            bool: True if successful.
        """
        import asyncio
        try:
            result = await asyncio.create_subprocess_exec(
                "wg-quick", "up", interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    async def stop_interface(interface_name: str) -> bool:
        """Stop a WireGuard interface.

        Args:
            interface_name: Name of the interface to stop.

        Returns:
            bool: True if successful.
        """
        import asyncio
        try:
            result = await asyncio.create_subprocess_exec(
                "wg-quick", "down", interface_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except Exception:
            return False


class WireGuardRepository:
    """Repository for WireGuard plugin data."""

    def __init__(self):
        from app.plugins.base import BaseRepository
        self.base_repo = BaseRepository("wireguard", "vpn")

    async def get_next_ip(self, server_id: str, network: str, used_ips: Optional[set] = None) -> str:
        """Get the next available IP address in the network."""
        if used_ips is None:
            # Get all client IPs for this server
            clients = await self.base_repo.list_items("clients")
            used_ips = set()
            for client in clients:
                if client.get("server_id") == server_id:
                    client_ip = client.get("allocated_ip")
                    if client_ip and '/' in client_ip:
                        used_ips.add(client_ip.split('/')[0])

        return IPAllocationService.get_next_available_ip(server_id, network, used_ips)

    async def get_server_by_interface(self, interface: str) -> Optional[Dict[str, Any]]:
        """Get server by interface name."""
        servers = await self.base_repo.list_items("servers")
        for server in servers:
            if server.get("name") == interface:
                return server
        return None

    async def get_client_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get client by username."""
        clients = await self.base_repo.list_items("clients")
        for client in clients:
            if client.get("name") == username:
                return client
        return None

    async def get_client_for_server(self, server_id: str, username: str) -> Optional[Dict[str, Any]]:
        """Get client for specific server."""
        clients = await self.base_repo.list_items("clients")
        for client in clients:
            if client.get("server_id") == server_id and client.get("name") == username:
                return client
        return None

    # Delegate all other methods to base repository
    async def create_item(self, collection: str, item_data: Dict[str, Any], item_id: Optional[str] = None) -> str:
        return await self.base_repo.create_item(collection, item_data, item_id)

    async def get_item(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        return await self.base_repo.get_item(collection, item_id)

    async def update_item(self, collection: str, item_id: str, updates: Dict[str, Any]) -> bool:
        return await self.base_repo.update_item(collection, item_id, updates)

    async def update_server(self, server_id: str, updates: Dict[str, Any]) -> bool:
        """Update a server with the given data."""
        return await self.update_item("servers", server_id, updates)

    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get a server by ID."""
        return await self.get_item("servers", server_id)

    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get all servers."""
        return await self.base_repo.list_items("servers")

    async def delete_item(self, collection: str, item_id: str) -> bool:
        return await self.base_repo.delete_item(collection, item_id)

    async def list_items(self, collection: str) -> List[Dict[str, Any]]:
        return await self.base_repo.list_items(collection)

    async def get_config(self, key: Optional[str] = None, default: Optional[Any] = None) -> Any:
        return await self.base_repo.get_config(key, default)

    async def set_config(self, key: str, value: Any) -> bool:
        return await self.base_repo.set_config(key, value)

    def generate_id(self) -> str:
        return self.base_repo.generate_id()

    def get_timestamp(self) -> str:
        return self.base_repo.get_timestamp()
