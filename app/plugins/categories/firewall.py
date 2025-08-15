"""Firewall plugin interface for the Firewallo Plugin Framework."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.plugins.base import FirewallPluginError


class FirewallAction(str, Enum):
    """Firewall rule actions."""
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"
    LOG = "log"
    MASQUERADE = "masquerade"
    REDIRECT = "redirect"


class FirewallProtocol(str, Enum):
    """Network protocols."""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    ALL = "all"


class FirewallChain(str, Enum):
    """Firewall chains."""
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    FORWARD = "FORWARD"
    PREROUTING = "PREROUTING"
    POSTROUTING = "POSTROUTING"
    CUSTOM = "CUSTOM"


class FirewallRuleCreate(BaseModel):
    """Model for creating a firewall rule."""
    name: str
    chain: FirewallChain
    action: FirewallAction
    protocol: FirewallProtocol = FirewallProtocol.ALL
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    priority: int = 100
    enabled: bool = True
    description: Optional[str] = None
    log_prefix: Optional[str] = None
    rate_limit: Optional[str] = None
    state: Optional[List[str]] = None  # NEW, ESTABLISHED, RELATED, INVALID
    custom_options: Optional[Dict[str, Any]] = None


class FirewallRuleResponse(BaseModel):
    """Model for firewall rule response."""
    id: str
    name: str
    chain: FirewallChain
    action: FirewallAction
    protocol: FirewallProtocol
    source_ip: Optional[str]
    source_port: Optional[int]
    destination_ip: Optional[str]
    destination_port: Optional[int]
    interface_in: Optional[str]
    interface_out: Optional[str]
    priority: int
    enabled: bool
    description: Optional[str]
    log_prefix: Optional[str]
    rate_limit: Optional[str]
    state: Optional[List[str]]
    custom_options: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    hit_count: int = 0
    last_hit: Optional[datetime] = None
    status: str  # active, inactive, error


class FirewallRuleUpdate(BaseModel):
    """Model for updating a firewall rule."""
    name: Optional[str] = None
    chain: Optional[FirewallChain] = None
    action: Optional[FirewallAction] = None
    protocol: Optional[FirewallProtocol] = None
    source_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = None
    interface_in: Optional[str] = None
    interface_out: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    log_prefix: Optional[str] = None
    rate_limit: Optional[str] = None
    state: Optional[List[str]] = None
    custom_options: Optional[Dict[str, Any]] = None


class FirewallZoneCreate(BaseModel):
    """Model for creating a firewall zone."""
    name: str
    interfaces: List[str]
    trusted: bool = False
    default_action: FirewallAction = FirewallAction.DROP
    masquerade: bool = False
    description: Optional[str] = None
    allowed_services: List[str] = []
    allowed_ports: List[Dict[str, Any]] = []  # [{"protocol": "tcp", "port": 80}]
    icmp_blocks: List[str] = []
    forward_ports: List[Dict[str, Any]] = []
    rich_rules: List[str] = []


class FirewallZoneResponse(BaseModel):
    """Model for firewall zone response."""
    id: str
    name: str
    interfaces: List[str]
    trusted: bool
    default_action: FirewallAction
    masquerade: bool
    description: Optional[str]
    allowed_services: List[str]
    allowed_ports: List[Dict[str, Any]]
    icmp_blocks: List[str]
    forward_ports: List[Dict[str, Any]]
    rich_rules: List[str]
    created_at: datetime
    updated_at: datetime
    active: bool
    rule_count: int


class FirewallZoneUpdate(BaseModel):
    """Model for updating a firewall zone."""
    name: Optional[str] = None
    interfaces: Optional[List[str]] = None
    trusted: Optional[bool] = None
    default_action: Optional[FirewallAction] = None
    masquerade: Optional[bool] = None
    description: Optional[str] = None
    allowed_services: Optional[List[str]] = None
    allowed_ports: Optional[List[Dict[str, Any]]] = None
    icmp_blocks: Optional[List[str]] = None
    forward_ports: Optional[List[Dict[str, Any]]] = None
    rich_rules: Optional[List[str]] = None


class FirewallNATRule(BaseModel):
    """Model for NAT rules."""
    name: str
    type: str  # SNAT, DNAT, MASQUERADE
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    translated_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    translated_port: Optional[int] = None
    protocol: FirewallProtocol = FirewallProtocol.ALL
    interface: Optional[str] = None
    enabled: bool = True
    description: Optional[str] = None


class FirewallStatistics(BaseModel):
    """Model for firewall statistics."""
    total_rules: int
    active_rules: int
    disabled_rules: int
    total_zones: int
    active_zones: int
    total_packets_processed: int
    total_packets_dropped: int
    total_packets_accepted: int
    total_packets_rejected: int
    rules_by_chain: Dict[str, int]
    rules_by_action: Dict[str, int]
    top_hit_rules: List[Dict[str, Any]]
    last_updated: datetime


class FirewallBackup(BaseModel):
    """Model for firewall backup."""
    backup_id: str
    timestamp: datetime
    description: Optional[str]
    rules: List[Dict[str, Any]]
    zones: List[Dict[str, Any]]
    nat_rules: List[Dict[str, Any]]
    custom_chains: List[Dict[str, Any]]
    version: str
    checksum: str


class FirewallPluginInterface(ABC):
    """Interface that all firewall plugins must implement."""

    @abstractmethod
    async def create_rule(self, rule_data: FirewallRuleCreate) -> FirewallRuleResponse:
        """Create a new firewall rule.

        Args:
            rule_data: Rule configuration data.

        Returns:
            FirewallRuleResponse: Created rule information.

        Raises:
            FirewallPluginError: If rule creation fails.
        """
        pass

    @abstractmethod
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a firewall rule.

        Args:
            rule_id: ID of the rule to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            FirewallPluginError: If rule deletion fails.
        """
        pass

    @abstractmethod
    async def list_rules(self, chain: Optional[FirewallChain] = None, **filters) -> List[FirewallRuleResponse]:
        """List firewall rules with optional filtering.

        Args:
            chain: Optional chain to filter by.
            **filters: Optional filters (enabled, action, protocol, etc.).

        Returns:
            List[FirewallRuleResponse]: List of rules.
        """
        pass

    @abstractmethod
    async def get_rule(self, rule_id: str) -> Optional[FirewallRuleResponse]:
        """Get a specific firewall rule by ID.

        Args:
            rule_id: ID of the rule to retrieve.

        Returns:
            Optional[FirewallRuleResponse]: Rule information if found.
        """
        pass

    @abstractmethod
    async def update_rule(self, rule_id: str, update_data: FirewallRuleUpdate) -> Optional[FirewallRuleResponse]:
        """Update a firewall rule.

        Args:
            rule_id: ID of the rule to update.
            update_data: Update data.

        Returns:
            Optional[FirewallRuleResponse]: Updated rule information.

        Raises:
            FirewallPluginError: If rule update fails.
        """
        pass

    @abstractmethod
    async def create_zone(self, zone_data: FirewallZoneCreate) -> FirewallZoneResponse:
        """Create a new firewall zone.

        Args:
            zone_data: Zone configuration data.

        Returns:
            FirewallZoneResponse: Created zone information.

        Raises:
            FirewallPluginError: If zone creation fails.
        """
        pass

    @abstractmethod
    async def delete_zone(self, zone_id: str) -> bool:
        """Delete a firewall zone.

        Args:
            zone_id: ID of the zone to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            FirewallPluginError: If zone deletion fails.
        """
        pass

    @abstractmethod
    async def list_zones(self, **filters) -> List[FirewallZoneResponse]:
        """List firewall zones with optional filtering.

        Args:
            **filters: Optional filters (active, trusted, etc.).

        Returns:
            List[FirewallZoneResponse]: List of zones.
        """
        pass

    @abstractmethod
    async def get_zone(self, zone_id: str) -> Optional[FirewallZoneResponse]:
        """Get a specific firewall zone by ID.

        Args:
            zone_id: ID of the zone to retrieve.

        Returns:
            Optional[FirewallZoneResponse]: Zone information if found.
        """
        pass

    @abstractmethod
    async def update_zone(self, zone_id: str, update_data: FirewallZoneUpdate) -> Optional[FirewallZoneResponse]:
        """Update a firewall zone.

        Args:
            zone_id: ID of the zone to update.
            update_data: Update data.

        Returns:
            Optional[FirewallZoneResponse]: Updated zone information.

        Raises:
            FirewallPluginError: If zone update fails.
        """
        pass

    @abstractmethod
    async def apply_rules(self) -> bool:
        """Apply all firewall rules to the system.

        Returns:
            bool: True if rules were applied successfully.

        Raises:
            FirewallPluginError: If rule application fails.
        """
        pass

    @abstractmethod
    async def reload_firewall(self) -> bool:
        """Reload the firewall configuration.

        Returns:
            bool: True if reload was successful.

        Raises:
            FirewallPluginError: If reload fails.
        """
        pass

    @abstractmethod
    async def get_statistics(self) -> FirewallStatistics:
        """Get firewall statistics.

        Returns:
            FirewallStatistics: Current firewall statistics.
        """
        pass

    # Optional methods with default implementations
    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a firewall rule.

        Args:
            rule_id: ID of the rule to enable.

        Returns:
            bool: True if rule was enabled successfully.
        """
        update_data = FirewallRuleUpdate(enabled=True)
        result = await self.update_rule(rule_id, update_data)
        return result is not None

    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a firewall rule.

        Args:
            rule_id: ID of the rule to disable.

        Returns:
            bool: True if rule was disabled successfully.
        """
        update_data = FirewallRuleUpdate(enabled=False)
        result = await self.update_rule(rule_id, update_data)
        return result is not None

    async def backup_configuration(self) -> FirewallBackup:
        """Backup firewall configuration.

        Returns:
            FirewallBackup: Backup data.
        """
        import hashlib
        import json
        import uuid

        rules = await self.list_rules()
        zones = await self.list_zones()

        backup_data = {
            "rules": [rule.dict() for rule in rules],
            "zones": [zone.dict() for zone in zones],
            "nat_rules": [],  # Implementation-specific
            "custom_chains": [],  # Implementation-specific
        }

        # Generate checksum
        backup_json = json.dumps(backup_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(backup_json.encode()).hexdigest()

        return FirewallBackup(
            backup_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            description=f"Firewall backup at {datetime.utcnow().isoformat()}",
            rules=backup_data["rules"],
            zones=backup_data["zones"],
            nat_rules=backup_data["nat_rules"],
            custom_chains=backup_data["custom_chains"],
            version=getattr(self, 'version', '1.0.0'),
            checksum=checksum
        )

    async def restore_configuration(self, backup: FirewallBackup) -> bool:
        """Restore firewall configuration from backup.

        Args:
            backup: Backup data to restore.

        Returns:
            bool: True if restore was successful.

        Raises:
            FirewallPluginError: If restore fails.
        """
        # Clear existing rules
        existing_rules = await self.list_rules()
        for rule in existing_rules:
            await self.delete_rule(rule.id)

        # Clear existing zones
        existing_zones = await self.list_zones()
        for zone in existing_zones:
            await self.delete_zone(zone.id)

        # Restore zones
        for zone_data in backup.zones:
            zone_create = FirewallZoneCreate(**{
                k: v for k, v in zone_data.items()
                if k in FirewallZoneCreate.__fields__
            })
            await self.create_zone(zone_create)

        # Restore rules
        for rule_data in backup.rules:
            rule_create = FirewallRuleCreate(**{
                k: v for k, v in rule_data.items()
                if k in FirewallRuleCreate.__fields__
            })
            await self.create_rule(rule_create)

        # Apply configuration
        return await self.apply_rules()

    async def validate_rule(self, rule_data: FirewallRuleCreate) -> Tuple[bool, List[str]]:
        """Validate a firewall rule before creation.

        Args:
            rule_data: Rule data to validate.

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Validate IP addresses
        if rule_data.source_ip:
            try:
                import ipaddress
                ipaddress.ip_network(rule_data.source_ip)
            except ValueError:
                errors.append(f"Invalid source IP: {rule_data.source_ip}")

        if rule_data.destination_ip:
            try:
                import ipaddress
                ipaddress.ip_network(rule_data.destination_ip)
            except ValueError:
                errors.append(f"Invalid destination IP: {rule_data.destination_ip}")

        # Validate ports
        if rule_data.source_port and not (1 <= rule_data.source_port <= 65535):
            errors.append(f"Invalid source port: {rule_data.source_port}")

        if rule_data.destination_port and not (1 <= rule_data.destination_port <= 65535):
            errors.append(f"Invalid destination port: {rule_data.destination_port}")

        # Validate state combinations
        if rule_data.state and rule_data.protocol == FirewallProtocol.ICMP:
            if "NEW" in rule_data.state or "ESTABLISHED" in rule_data.state:
                errors.append("ICMP protocol does not support connection states")

        return len(errors) == 0, errors

    async def create_nat_rule(self, nat_rule: FirewallNATRule) -> Dict[str, Any]:
        """Create a NAT rule.

        Args:
            nat_rule: NAT rule configuration.

        Returns:
            Dict[str, Any]: Created NAT rule information.
        """
        # Implementation-specific
        raise NotImplementedError("NAT rules are implementation-specific")

    async def list_nat_rules(self) -> List[FirewallNATRule]:
        """List all NAT rules.

        Returns:
            List[FirewallNATRule]: List of NAT rules.
        """
        # Implementation-specific
        raise NotImplementedError("NAT rules are implementation-specific")
