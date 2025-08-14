"""WireGuard VPN plugin for the Firewallo Plugin Framework."""

from .plugin import WireGuardPlugin

# Export the main plugin class
__all__ = ["WireGuardPlugin"]

# Plugin metadata
__version__ = "1.0.0"
__author__ = "Firewallo Team"
__description__ = "Modern, fast, and secure VPN implementation using WireGuard protocol"
