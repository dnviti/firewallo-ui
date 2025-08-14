"""Firewallo Web UI Plugin.

A modern, responsive Bootstrap-based web interface for managing the Firewallo firewall system.
This plugin provides a comprehensive dashboard, plugin management, system monitoring, and more.
"""

from .plugin import WebUIPlugin, plugin

# Plugin metadata
__name__ = "webui"
__version__ = "2.0.0"
__author__ = "Firewallo Team"
__description__ = "Modern Bootstrap-based web interface for Firewallo firewall management"
__category__ = "system"

# Export plugin class and instance
__all__ = [
    "WebUIPlugin",
    "plugin",
]

# Plugin instance that will be loaded by the plugin manager
webui_plugin = plugin
