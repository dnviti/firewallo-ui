"""Network plugin interface for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

from app.plugins.base import NetworkPluginError


class NetworkProtocol(str, Enum):
    """Network protocols."""
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    BOTH = "both"


class InterfaceType(str, Enum):
    """Network interface types."""
    ETHERNET = "ethernet"
    WIFI = "wifi"
    BRIDGE = "bridge"
    VLAN = "vlan"
    TUN = "tun"
    TAP = "tap"
    LOOPBACK = "loopback"
    VIRTUAL = "virtual"


class InterfaceStatus(str, Enum):
    """Interface status."""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    CONFIGURING = "configuring"
    ERROR = "error"


class DHCPMode(str, Enum):
    """DHCP modes."""
    SERVER = "server"
    CLIENT = "client"
    RELAY = "relay"
    DISABLED = "disabled"


class DNSRecordType(str, Enum):
    """DNS record types."""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    TXT = "TXT"
    NS = "NS"
    PTR = "PTR"
    SRV = "SRV"
    SOA = "SOA"


class LoadBalancerAlgorithm(str, Enum):
    """Load balancer algorithms."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    IP_HASH = "ip_hash"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"


class NetworkInterfaceCreate(BaseModel):
    """Model for creating a network interface."""
    name: str
    type: InterfaceType
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    ipv6_address: Optional[str] = None
    ipv6_prefix: Optional[int] = None
    mtu: int = 1500
    mac_address: Optional[str] = None
    vlan_id: Optional[int] = None
    parent_interface: Optional[str] = None  # For VLANs and bridges
    bridge_members: Optional[List[str]] = None  # For bridges
    dhcp_enabled: bool = False
    dns_servers: List[str] = []
    search_domains: List[str] = []
    enabled: bool = True
    description: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


class NetworkInterfaceResponse(BaseModel):
    """Model for network interface response."""
    id: str
    name: str
    type: InterfaceType
    status: InterfaceStatus
    ip_address: Optional[str]
    netmask: Optional[str]
    gateway: Optional[str]
    ipv6_address: Optional[str]
    ipv6_prefix: Optional[int]
    mtu: int
    mac_address: str
    vlan_id: Optional[int]
    parent_interface: Optional[str]
    bridge_members: Optional[List[str]]
    dhcp_enabled: bool
    dns_servers: List[str]
    search_domains: List[str]
    enabled: bool
    description: Optional[str]
    custom_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    rx_bytes: int
    tx_bytes: int
    rx_packets: int
    tx_packets: int
    rx_errors: int
    tx_errors: int
    link_speed: Optional[int]  # Mbps


class NetworkInterfaceUpdate(BaseModel):
    """Model for updating a network interface."""
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    ipv6_address: Optional[str] = None
    ipv6_prefix: Optional[int] = None
    mtu: Optional[int] = None
    vlan_id: Optional[int] = None
    bridge_members: Optional[List[str]] = None
    dhcp_enabled: Optional[bool] = None
    dns_servers: Optional[List[str]] = None
    search_domains: Optional[List[str]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


class DHCPServerCreate(BaseModel):
    """Model for creating a DHCP server."""
    name: str
    interface: str
    start_ip: str
    end_ip: str
    subnet_mask: str
    gateway: str
    dns_servers: List[str]
    domain_name: Optional[str] = None
    lease_time: int = 86400  # seconds
    enabled: bool = True
    options: Dict[int, str] = {}  # DHCP options
    static_leases: List[Dict[str, str]] = []  # [{"mac": "...", "ip": "..."}]
    excluded_ips: List[str] = []
    description: Optional[str] = None


class DHCPServerResponse(BaseModel):
    """Model for DHCP server response."""
    id: str
    name: str
    interface: str
    start_ip: str
    end_ip: str
    subnet_mask: str
    gateway: str
    dns_servers: List[str]
    domain_name: Optional[str]
    lease_time: int
    enabled: bool
    options: Dict[int, str]
    static_leases: List[Dict[str, str]]
    excluded_ips: List[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    active_leases: int
    total_addresses: int
    available_addresses: int


class DHCPLease(BaseModel):
    """Model for DHCP lease."""
    ip_address: str
    mac_address: str
    hostname: Optional[str]
    client_id: Optional[str]
    lease_start: datetime
    lease_end: datetime
    state: str  # active, expired, reserved
    interface: str
    vendor_class: Optional[str]


class DNSZoneCreate(BaseModel):
    """Model for creating a DNS zone."""
    name: str
    type: str = "master"  # master, slave, forward
    records: List[Dict[str, Any]] = []
    ttl: int = 3600
    refresh: int = 7200
    retry: int = 3600
    expire: int = 1209600
    minimum: int = 3600
    serial: Optional[int] = None
    primary_ns: Optional[str] = None
    admin_email: Optional[str] = None
    enabled: bool = True
    dnssec_enabled: bool = False
    allow_transfer: List[str] = []
    forwarders: List[str] = []
    description: Optional[str] = None


class DNSZoneResponse(BaseModel):
    """Model for DNS zone response."""
    id: str
    name: str
    type: str
    records: List[Dict[str, Any]]
    ttl: int
    refresh: int
    retry: int
    expire: int
    minimum: int
    serial: int
    primary_ns: Optional[str]
    admin_email: Optional[str]
    enabled: bool
    dnssec_enabled: bool
    allow_transfer: List[str]
    forwarders: List[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    record_count: int
    last_modified: datetime


class DNSRecordCreate(BaseModel):
    """Model for creating a DNS record."""
    zone_id: str
    name: str
    type: DNSRecordType
    value: str
    ttl: Optional[int] = None
    priority: Optional[int] = None  # For MX records
    weight: Optional[int] = None  # For SRV records
    port: Optional[int] = None  # For SRV records
    enabled: bool = True
    description: Optional[str] = None


class DNSRecordResponse(BaseModel):
    """Model for DNS record response."""
    id: str
    zone_id: str
    name: str
    type: DNSRecordType
    value: str
    ttl: Optional[int]
    priority: Optional[int]
    weight: Optional[int]
    port: Optional[int]
    enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


class RouteCreate(BaseModel):
    """Model for creating a route."""
    destination: str  # CIDR notation
    gateway: str
    interface: Optional[str] = None
    metric: int = 100
    description: Optional[str] = None
    enabled: bool = True


class RouteResponse(BaseModel):
    """Model for route response."""
    id: str
    destination: str
    gateway: str
    interface: Optional[str]
    metric: int
    description: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    flags: List[str]  # U=up, G=gateway, H=host, etc.
    use_count: int


class LoadBalancerCreate(BaseModel):
    """Model for creating a load balancer."""
    name: str
    algorithm: LoadBalancerAlgorithm
    frontend_ip: str
    frontend_port: int
    backend_servers: List[Dict[str, Any]]  # [{"ip": "...", "port": ..., "weight": ...}]
    health_check_enabled: bool = True
    health_check_path: str = "/"
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 5  # seconds
    health_check_unhealthy_threshold: int = 3
    health_check_healthy_threshold: int = 2
    session_persistence: bool = False
    session_timeout: int = 300  # seconds
    enabled: bool = True
    description: Optional[str] = None


class LoadBalancerResponse(BaseModel):
    """Model for load balancer response."""
    id: str
    name: str
    algorithm: LoadBalancerAlgorithm
    frontend_ip: str
    frontend_port: int
    backend_servers: List[Dict[str, Any]]
    health_check_enabled: bool
    health_check_path: str
    health_check_interval: int
    health_check_timeout: int
    health_check_unhealthy_threshold: int
    health_check_healthy_threshold: int
    session_persistence: bool
    session_timeout: int
    enabled: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    active_connections: int
    total_connections: int
    healthy_backends: int
    total_backends: int


class NetworkStatistics(BaseModel):
    """Model for network statistics."""
    total_interfaces: int
    active_interfaces: int
    total_rx_bytes: int
    total_tx_bytes: int
    total_rx_packets: int
    total_tx_packets: int
    total_rx_errors: int
    total_tx_errors: int
    dhcp_servers: int
    active_dhcp_leases: int
    dns_zones: int
    dns_records: int
    routes: int
    load_balancers: int
    active_connections: int
    last_updated: datetime


class NetworkPluginInterface(ABC):
    """Interface that all network plugins must implement."""

    @abstractmethod
    async def create_interface(self, interface_data: NetworkInterfaceCreate) -> NetworkInterfaceResponse:
        """Create a new network interface.

        Args:
            interface_data: Interface configuration.

        Returns:
            NetworkInterfaceResponse: Created interface.

        Raises:
            NetworkPluginError: If interface creation fails.
        """
        pass

    @abstractmethod
    async def delete_interface(self, interface_id: str) -> bool:
        """Delete a network interface.

        Args:
            interface_id: ID of the interface to delete.

        Returns:
            bool: True if deletion was successful.
        """
        pass

    @abstractmethod
    async def list_interfaces(self, **filters) -> List[NetworkInterfaceResponse]:
        """List network interfaces with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[NetworkInterfaceResponse]: List of interfaces.
        """
        pass

    @abstractmethod
    async def get_interface(self, interface_id: str) -> Optional[NetworkInterfaceResponse]:
        """Get a specific network interface by ID.

        Args:
            interface_id: ID of the interface to retrieve.

        Returns:
            Optional[NetworkInterfaceResponse]: Interface if found.
        """
        pass

    @abstractmethod
    async def update_interface(self, interface_id: str, update_data: NetworkInterfaceUpdate) -> Optional[NetworkInterfaceResponse]:
        """Update a network interface.

        Args:
            interface_id: ID of the interface to update.
            update_data: Update data.

        Returns:
            Optional[NetworkInterfaceResponse]: Updated interface.
        """
        pass

    @abstractmethod
    async def create_dhcp_server(self, dhcp_data: DHCPServerCreate) -> DHCPServerResponse:
        """Create a new DHCP server.

        Args:
            dhcp_data: DHCP server configuration.

        Returns:
            DHCPServerResponse: Created DHCP server.
        """
        pass

    @abstractmethod
    async def list_dhcp_servers(self, **filters) -> List[DHCPServerResponse]:
        """List DHCP servers with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[DHCPServerResponse]: List of DHCP servers.
        """
        pass

    @abstractmethod
    async def get_dhcp_leases(self, server_id: Optional[str] = None) -> List[DHCPLease]:
        """Get DHCP leases.

        Args:
            server_id: Optional server ID to filter by.

        Returns:
            List[DHCPLease]: List of DHCP leases.
        """
        pass

    @abstractmethod
    async def create_dns_zone(self, zone_data: DNSZoneCreate) -> DNSZoneResponse:
        """Create a new DNS zone.

        Args:
            zone_data: DNS zone configuration.

        Returns:
            DNSZoneResponse: Created DNS zone.
        """
        pass

    @abstractmethod
    async def list_dns_zones(self, **filters) -> List[DNSZoneResponse]:
        """List DNS zones with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[DNSZoneResponse]: List of DNS zones.
        """
        pass

    @abstractmethod
    async def create_dns_record(self, record_data: DNSRecordCreate) -> DNSRecordResponse:
        """Create a new DNS record.

        Args:
            record_data: DNS record configuration.

        Returns:
            DNSRecordResponse: Created DNS record.
        """
        pass

    @abstractmethod
    async def create_route(self, route_data: RouteCreate) -> RouteResponse:
        """Create a new route.

        Args:
            route_data: Route configuration.

        Returns:
            RouteResponse: Created route.
        """
        pass

    @abstractmethod
    async def list_routes(self, **filters) -> List[RouteResponse]:
        """List routes with optional filtering.

        Args:
            **filters: Optional filters.

        Returns:
            List[RouteResponse]: List of routes.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> NetworkStatistics:
        """Get network statistics.

        Returns:
            NetworkStatistics: Current network statistics.
        """
        pass

    # Optional methods with default implementations
    async def create_load_balancer(self, lb_data: LoadBalancerCreate) -> LoadBalancerResponse:
        """Create a new load balancer.

        Args:
            lb_data: Load balancer configuration.

        Returns:
            LoadBalancerResponse: Created load balancer.
        """
        raise NotImplementedError("Load balancer functionality not implemented")

    async def restart_interface(self, interface_id: str) -> bool:
        """Restart a network interface.

        Args:
            interface_id: ID of the interface to restart.

        Returns:
            bool: True if restart was successful.
        """
        # Down and up the interface
        interface = await self.get_interface(interface_id)
        if not interface:
            return False

        update_down = NetworkInterfaceUpdate(enabled=False)
        await self.update_interface(interface_id, update_down)

        import asyncio
        await asyncio.sleep(1)  # Brief pause

        update_up = NetworkInterfaceUpdate(enabled=True)
        result = await self.update_interface(interface_id, update_up)
        return result is not None

    async def scan_network(self, network: str) -> List[Dict[str, Any]]:
        """Scan network for devices.

        Args:
            network: Network to scan in CIDR notation.

        Returns:
            List[Dict[str, Any]]: List of discovered devices.
        """
        raise NotImplementedError("Network scanning not implemented")

    async def test_connectivity(self, target: str, port: Optional[int] = None) -> Dict[str, Any]:
        """Test network connectivity to a target.

        Args:
            target: Target IP or hostname.
            port: Optional port to test.

        Returns:
            Dict[str, Any]: Connectivity test results.
        """
        import socket
        import time

        start_time = time.time()
        success = False
        error_msg = None

        try:
            if port:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((target, port))
                sock.close()
                success = result == 0
            else:
                # Simple ping-like test
                socket.gethostbyname(target)
                success = True
        except Exception as e:
            error_msg = str(e)

        response_time = (time.time() - start_time) * 1000  # ms

        return {
            "target": target,
            "port": port,
            "success": success,
            "response_time_ms": response_time,
            "error": error_msg,
            "timestamp": datetime.utcnow()
        }
