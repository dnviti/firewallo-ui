"""VPN plugins category for the Firewallo Plugin Framework."""

from .wireguard import WireGuardPlugin

# Available VPN plugins in this category
__plugins__ = {
    "wireguard": WireGuardPlugin,
    # Future VPN plugins can be added here:
    # "openvpn": OpenVPNPlugin,
    # "ipsec": IPSecPlugin,
    # "sstp": SSTPPlugin,
}

# Category metadata
__category__ = "vpn"
__version__ = "1.0.0"
__description__ = "VPN (Virtual Private Network) plugins for secure network tunneling"
__author__ = "Firewallo Team"

# Export all available plugins
__all__ = ["WireGuardPlugin", "__plugins__", "__category__"]
