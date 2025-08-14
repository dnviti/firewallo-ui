"""Plugin category interfaces for the Firewallo Plugin Framework."""

from .vpn import (
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

# TODO: Import other category interfaces when implemented
# from .firewall import FirewallPluginInterface
# from .monitoring import MonitoringPluginInterface
# from .network import NetworkPluginInterface
# from .security import SecurityPluginInterface

__all__ = [
    # VPN plugin interface and models
    "VPNPluginInterface",
    "VPNServerCreate",
    "VPNServerResponse",
    "VPNServerUpdate",
    "VPNClientCreate",
    "VPNClientResponse",
    "VPNClientUpdate",
    "VPNConfigResponse",
    "VPNConnectionStatus",
    "VPNStatistics",

    # TODO: Add other category interfaces
    # "FirewallPluginInterface",
    # "MonitoringPluginInterface",
    # "NetworkPluginInterface",
    # "SecurityPluginInterface",
]
