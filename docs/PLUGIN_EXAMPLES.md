# Plugin Examples

This document provides complete, working examples of plugins for different categories. Each example demonstrates best practices and common patterns for plugin development in Firewallo.

## WireGuard Plugin Example

The WireGuard plugin serves as the reference implementation for VPN plugins.

### Plugin Structure

```
app/plugins/vpn/wireguard/
├── __init__.py
├── plugin.py           # Main plugin class
├── manifest.json       # Plugin metadata
├── schemas.py          # Pydantic models
├── repository.py       # Data access layer
├── routes.py           # API routes
├── services.py         # Business logic
└── backends/
    ├── __init__.py
    └── litedb.py      # Database backend
```

### Complete Plugin Implementation

```python
# app/plugins/vpn/wireguard/plugin.py
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
from app.plugins.base.plugin import BasePlugin
from app.plugins.categories.vpn import VPNPluginInterface
from .repository import WireGuardRepository
from .services import WireGuardService

class WireGuardPlugin(BasePlugin, VPNPluginInterface):
    """WireGuard VPN plugin implementation."""
    
    def __init__(self):
        super().__init__()
        self.name = "wireguard"
        self.category = "vpn"
        self.version = "1.0.0"
        self.description = "WireGuard VPN server and peer management"
        self.author = "Firewallo Team"
        
        self.repository = WireGuardRepository()
        self.service = WireGuardService(self.repository)
    
    async def initialize(self) -> bool:
        """Initialize WireGuard plugin."""
        try:
            # Check if WireGuard tools are available
            import subprocess
            subprocess.run(["wg", "--version"], capture_output=True, check=True)
            
            self.logger.info("WireGuard plugin initialized successfully")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.logger.warning("WireGuard tools not found, using fallback implementation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize WireGuard plugin: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Cleanup WireGuard plugin resources."""
        self.logger.info("WireGuard plugin shutting down")
    
    def get_api_routes(self) -> List[APIRouter]:
        """Return API routes for WireGuard plugin."""
        from .routes import router
        return [router]
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema for WireGuard plugin."""
        return {
            "servers": [],
            "peers": []
        }
    
    # VPN Interface Implementation
    async def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a WireGuard server."""
        return await self.service.create_server(config)
    
    async def delete_server(self, server_id: str) -> bool:
        """Delete a WireGuard server."""
        return await self.service.delete_server(server_id)
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all WireGuard servers."""
        return await self.service.list_servers()
    
    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get WireGuard server details."""
        return await self.service.get_server(server_id)
    
    async def update_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update WireGuard server configuration."""
        return await self.service.update_server(server_id, config)
    
    async def create_client(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a WireGuard peer."""
        return await self.service.create_peer(server_id, config)
    
    async def delete_client(self, client_id: str) -> bool:
        """Delete a WireGuard peer."""
        return await self.service.delete_peer(client_id)
    
    async def list_clients(self, server_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List WireGuard peers."""
        return await self.service.list_peers(server_id)
    
    async def generate_config(self, client_id: str) -> str:
        """Generate WireGuard client configuration."""
        return await self.service.generate_peer_config(client_id)
    
    async def get_connection_status(self, client_id: str) -> Dict[str, Any]:
        """Get peer connection status."""
        return await self.service.get_peer_status(client_id)
    
    async def revoke_client(self, client_id: str) -> bool:
        """Revoke peer access."""
        return await self.service.revoke_peer(client_id)
```

### Service Layer

```python
# app/plugins/vpn/wireguard/services.py
import subprocess
import base64
import os
from typing import Dict, Any, List, Optional
from .repository import WireGuardRepository

class WireGuardService:
    """WireGuard business logic service."""
    
    def __init__(self, repository: WireGuardRepository):
        self.repository = repository
    
    async def create_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new WireGuard server."""
        # Generate server keys
        private_key = self._generate_private_key()
        public_key = self._generate_public_key(private_key)
        
        server_data = {
            "interface": config["interface"],
            "private_key": private_key,
            "public_key": public_key,
            "listen_port": config.get("listen_port", 51820),
            "address": config["address"],
            "mtu": config.get("mtu", 1420),
            "status": "created"
        }
        
        server_id = await self.repository.create_server(server_data)
        server_data["id"] = server_id
        
        return server_data
    
    async def delete_server(self, server_id: str) -> bool:
        """Delete a WireGuard server."""
        # Also delete associated peers
        peers = await self.repository.list_peers(server_id)
        for peer in peers:
            await self.repository.delete_peer(peer["id"])
        
        return await self.repository.delete_server(server_id)
    
    async def list_servers(self) -> List[Dict[str, Any]]:
        """List all WireGuard servers."""
        return await self.repository.list_servers()
    
    async def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server details."""
        return await self.repository.get_server(server_id)
    
    async def update_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update server configuration."""
        await self.repository.update_server(server_id, config)
        return await self.repository.get_server(server_id)
    
    async def create_peer(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new peer."""
        server = await self.repository.get_server(server_id)
        if not server:
            raise ValueError("Server not found")
        
        # Generate peer keys
        private_key = self._generate_private_key()
        public_key = self._generate_public_key(private_key)
        preshared_key = self._generate_preshared_key()
        
        # Allocate IP address
        private_ip = await self._allocate_ip(server_id, server["address"])
        
        peer_data = {
            "username": config["username"],
            "server_id": server_id,
            "private_ip": private_ip,
            "private_key": private_key,
            "public_key": public_key,
            "allowed_ips": config.get("allowed_ips", "0.0.0.0/0"),
            "endpoint": config.get("endpoint"),
            "preshared_key": preshared_key,
            "persistent_keepalive": config.get("persistent_keepalive"),
            "status": "active"
        }
        
        peer_id = await self.repository.create_peer(peer_data)
        peer_data["id"] = peer_id
        
        return peer_data
    
    async def generate_peer_config(self, peer_id: str) -> str:
        """Generate peer configuration file."""
        peer = await self.repository.get_peer(peer_id)
        if not peer:
            raise ValueError("Peer not found")
        
        server = await self.repository.get_server(peer["server_id"])
        if not server:
            raise ValueError("Server not found")
        
        config_lines = [
            "[Interface]",
            f"PrivateKey = {peer['private_key']}",
            f"Address = {peer['private_ip']}",
            f"MTU = {server['mtu']}",
            "",
            "[Peer]",
            f"PublicKey = {server['public_key']}",
            f"Endpoint = {peer.get('endpoint', '')}",
            f"AllowedIPs = {peer['allowed_ips']}",
            f"PresharedKey = {peer['preshared_key']}"
        ]
        
        if peer.get("persistent_keepalive"):
            config_lines.append(f"PersistentKeepalive = {peer['persistent_keepalive']}")
        
        return "\n".join(config_lines)
    
    def _generate_private_key(self) -> str:
        """Generate WireGuard private key."""
        try:
            return subprocess.check_output(["wg", "genkey"]).decode().strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback for development environments
            return base64.b64encode(os.urandom(32)).decode().rstrip("=")
    
    def _generate_public_key(self, private_key: str) -> str:
        """Generate WireGuard public key from private key."""
        try:
            proc = subprocess.Popen(["wg", "pubkey"], 
                                  stdin=subprocess.PIPE, 
                                  stdout=subprocess.PIPE)
            stdout, _ = proc.communicate(input=private_key.encode())
            return stdout.decode().strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback for development environments
            return base64.b64encode(os.urandom(32)).decode().rstrip("=")
    
    def _generate_preshared_key(self) -> str:
        """Generate WireGuard preshared key."""
        try:
            return subprocess.check_output(["wg", "genpsk"]).decode().strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Fallback for development environments
            return base64.b64encode(os.urandom(32)).decode().rstrip("=")
    
    async def _allocate_ip(self, server_id: str, server_address: str) -> str:
        """Allocate IP address for peer."""
        import ipaddress
        
        network = ipaddress.ip_network(server_address, strict=False)
        peers = await self.repository.list_peers(server_id)
        used_ips = {peer["private_ip"].split("/")[0] for peer in peers}
        
        for host in network.hosts():
            if str(host) not in used_ips:
                return f"{host}/{network.prefixlen}"
        
        raise ValueError("No available IP addresses in network")
```

## Monitoring Plugin Example

A comprehensive monitoring plugin that integrates with Prometheus and provides system metrics.

### Plugin Implementation

```python
# app/plugins/monitoring/prometheus/plugin.py
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
from app.plugins.base.plugin import BasePlugin
from app.plugins.categories.monitoring import MonitoringPluginInterface
from .repository import PrometheusRepository
from .services import PrometheusService

class PrometheusPlugin(BasePlugin, MonitoringPluginInterface):
    """Prometheus monitoring plugin."""
    
    def __init__(self):
        super().__init__()
        self.name = "prometheus"
        self.category = "monitoring"
        self.version = "1.0.0"
        self.description = "Prometheus metrics collection and monitoring"
        self.author = "Firewallo Team"
        
        self.repository = PrometheusRepository()
        self.service = PrometheusService(self.repository)
    
    async def initialize(self) -> bool:
        """Initialize Prometheus plugin."""
        try:
            # Start metrics collection
            await self.service.start_metrics_collection()
            self.logger.info("Prometheus plugin initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Prometheus plugin: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Cleanup Prometheus plugin resources."""
        await self.service.stop_metrics_collection()
        self.logger.info("Prometheus plugin shutting down")
    
    def get_api_routes(self) -> List[APIRouter]:
        """Return API routes for Prometheus plugin."""
        from .routes import router
        return [router]
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema for Prometheus plugin."""
        return {
            "monitors": [],
            "alerts": [],
            "targets": [],
            "config": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            }
        }
    
    # Monitoring Interface Implementation
    async def create_monitor(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new monitor."""
        return await self.service.create_monitor(config)
    
    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        return await self.service.delete_monitor(monitor_id)
    
    async def list_monitors(self) -> List[Dict[str, Any]]:
        """List all monitors."""
        return await self.service.list_monitors()
    
    async def get_metrics(self, monitor_id: str, time_range: str) -> Dict[str, Any]:
        """Get metrics for a specific monitor."""
        return await self.service.get_metrics(monitor_id, time_range)
    
    async def create_alert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule."""
        return await self.service.create_alert(config)
    
    async def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by status."""
        return await self.service.get_alerts(status)
```

### Service Implementation

```python
# app/plugins/monitoring/prometheus/services.py
import asyncio
import httpx
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .repository import PrometheusRepository

class PrometheusService:
    """Prometheus monitoring service."""
    
    def __init__(self, repository: PrometheusRepository):
        self.repository = repository
        self.metrics_task = None
        self.running = False
    
    async def start_metrics_collection(self):
        """Start collecting system metrics."""
        self.running = True
        self.metrics_task = asyncio.create_task(self._collect_metrics_loop())
    
    async def stop_metrics_collection(self):
        """Stop collecting metrics."""
        self.running = False
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
    
    async def create_monitor(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new monitor."""
        monitor_data = {
            "name": config["name"],
            "type": config.get("type", "system"),
            "interval": config.get("interval", 30),
            "targets": config.get("targets", []),
            "metrics": config.get("metrics", ["cpu", "memory", "disk"]),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        monitor_id = await self.repository.create_monitor(monitor_data)
        monitor_data["id"] = monitor_id
        
        return monitor_data
    
    async def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor."""
        return await self.repository.delete_monitor(monitor_id)
    
    async def list_monitors(self) -> List[Dict[str, Any]]:
        """List all monitors."""
        return await self.repository.list_monitors()
    
    async def get_metrics(self, monitor_id: str, time_range: str) -> Dict[str, Any]:
        """Get metrics for a monitor."""
        monitor = await self.repository.get_monitor(monitor_id)
        if not monitor:
            raise ValueError("Monitor not found")
        
        # Parse time range
        end_time = datetime.now()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        else:
            start_time = end_time - timedelta(hours=1)
        
        metrics = await self.repository.get_metrics(
            monitor_id, start_time, end_time
        )
        
        return {
            "monitor_id": monitor_id,
            "time_range": time_range,
            "metrics": metrics,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
    
    async def create_alert(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert rule."""
        alert_data = {
            "name": config["name"],
            "condition": config["condition"],
            "threshold": config["threshold"],
            "monitor_id": config.get("monitor_id"),
            "severity": config.get("severity", "warning"),
            "enabled": config.get("enabled", True),
            "created_at": datetime.now().isoformat()
        }
        
        alert_id = await self.repository.create_alert(alert_data)
        alert_data["id"] = alert_id
        
        return alert_data
    
    async def get_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts, optionally filtered by status."""
        return await self.repository.get_alerts(status)
    
    async def _collect_metrics_loop(self):
        """Main metrics collection loop."""
        while self.running:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """Collect system metrics."""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used
        memory_total = memory.total
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used = disk.used
        disk_total = disk.total
        
        # Network metrics
        network = psutil.net_io_counters()
        bytes_sent = network.bytes_sent
        bytes_recv = network.bytes_recv
        
        metrics_data = {
            "timestamp": timestamp.isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "percent": memory_percent,
                "used": memory_used,
                "total": memory_total
            },
            "disk": {
                "percent": disk_percent,
                "used": disk_used,
                "total": disk_total
            },
            "network": {
                "bytes_sent": bytes_sent,
                "bytes_recv": bytes_recv
            }
        }
        
        await self.repository.store_metrics("system", metrics_data)
        
        # Check alerts
        await self._check_alerts(metrics_data)
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """Check alert conditions."""
        alerts = await self.repository.get_alerts("enabled")
        
        for alert in alerts:
            if not alert.get("enabled"):
                continue
            
            condition = alert["condition"]
            threshold = alert["threshold"]
            
            triggered = False
            
            if condition == "cpu_high" and metrics["cpu"]["percent"] > threshold:
                triggered = True
            elif condition == "memory_high" and metrics["memory"]["percent"] > threshold:
                triggered = True
            elif condition == "disk_high" and metrics["disk"]["percent"] > threshold:
                triggered = True
            
            if triggered:
                await self._trigger_alert(alert, metrics)
    
    async def _trigger_alert(self, alert: Dict[str, Any], metrics: Dict[str, Any]):
        """Trigger an alert."""
        alert_instance = {
            "alert_id": alert["id"],
            "triggered_at": datetime.now().isoformat(),
            "status": "firing",
            "metrics": metrics,
            "message": f"Alert {alert['name']} triggered"
        }
        
        await self.repository.create_alert_instance(alert_instance)
```

## Firewall Plugin Example

A comprehensive iptables firewall management plugin.

### Plugin Implementation

```python
# app/plugins/firewall/iptables/plugin.py
from typing import Dict, List, Any, Optional
from fastapi import APIRouter
from app.plugins.base.plugin import BasePlugin
from app.plugins.categories.firewall import FirewallPluginInterface
from .repository import IptablesRepository
from .services import IptablesService

class IptablesPlugin(BasePlugin, FirewallPluginInterface):
    """iptables firewall management plugin."""
    
    def __init__(self):
        super().__init__()
        self.name = "iptables"
        self.category = "firewall"
        self.version = "1.0.0"
        self.description = "iptables firewall rule management"
        self.author = "Firewallo Team"
        
        self.repository = IptablesRepository()
        self.service = IptablesService(self.repository)
    
    async def initialize(self) -> bool:
        """Initialize iptables plugin."""
        try:
            # Check if iptables is available
            import subprocess
            result = subprocess.run(["iptables", "--version"], 
                                  capture_output=True, check=True)
            
            # Load current rules
            await self.service.sync_rules()
            
            self.logger.info("iptables plugin initialized successfully")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            self.logger.error(f"iptables not available: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize iptables plugin: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Cleanup iptables plugin resources."""
        self.logger.info("iptables plugin shutting down")
    
    def get_api_routes(self) -> List[APIRouter]:
        """Return API routes for iptables plugin."""
        from .routes import router
        return [router]
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Return database schema for iptables plugin."""
        return {
            "rules": [],
            "chains": [],
            "policies": {},
            "config": {
                "default_policy": "DROP",
                "log_dropped": True
            }
        }
    
    # Firewall Interface Implementation
    async def create_rule(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a firewall rule."""
        return await self.service.create_rule(rule_config)
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a firewall rule."""
        return await self.service.delete_rule(rule_id)
    
    async def list_rules(self, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List firewall rules."""
        return await self.service.list_rules(chain)
    
    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a firewall rule."""
        return await self.service.enable_rule(rule_id)
    
    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a firewall rule."""
        return await self.service.disable_rule(rule_id)
    
    async def backup_config(self) -> str:
        """Backup current firewall configuration."""
        return await self.service.backup_config()
    
    async def restore_config(self, backup_data: str) -> bool:
        """Restore firewall configuration from backup."""
        return await self.service.restore_config(backup_data)
```

### Service Implementation

```python
# app/plugins/firewall/iptables/services.py
import subprocess
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .repository import IptablesRepository

class IptablesService:
    """iptables management service."""
    
    def __init__(self, repository: IptablesRepository):
        self.repository = repository
    
    async def create_rule(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create and apply a new firewall rule."""
        # Build iptables command
        cmd = self._build_iptables_command(rule_config)
        
        # Apply rule
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to apply rule: {e.stderr.decode()}")
        
        # Store in database
        rule_data = {
            "name": rule_config.get("name", "Unnamed Rule"),
            "chain": rule_config.get("chain", "INPUT"),
            "table": rule_config.get("table", "filter"),
            "protocol": rule_config.get("protocol"),
            "source": rule_config.get("source"),
            "destination": rule_config.get("destination"),
            "port": rule_config.get("port"),
            "action": rule_config.get("action", "ACCEPT"),
            "enabled": True,
            "command": " ".join(cmd),
            "created_at": datetime.now().isoformat()
        }
        
        rule_id = await self.repository.create_rule(rule_data)
        rule_data["id"] = rule_id
        
        return rule_data
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a firewall rule."""
        rule = await self.repository.get_rule(rule_id)
        if not rule:
            return False
        
        # Remove from iptables
        cmd = rule["command"].replace("-A", "-D").split()
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # Rule might already be removed, continue with database cleanup
            pass
        
        return await self.repository.delete_rule(rule_id)
    
    async def list_rules(self, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List firewall rules."""
        return await self.repository.list_rules(chain)
    
    async def enable_rule(self, rule_id: str) -> bool:
        """Enable a firewall rule."""
        rule = await self.repository.get_rule(rule_id)
        if not rule or rule.get("enabled"):
            return False
        
        # Apply rule
        cmd = rule["command"].split()
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            await self.repository.update_rule(rule_id, {"enabled": True})
            return True
        except subprocess.CalledProcessError:
            return False
    
    async def disable_rule(self, rule_id: str) -> bool:
        """Disable a firewall rule."""
        rule = await self.repository.get_rule(rule_id)
        if not rule or not rule.get("enabled"):
            return False
        
        # Remove rule
        cmd = rule["command"].replace("-A", "-D").split()
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            await self.repository.update_rule(rule_id, {"enabled": False})
            return True
        except subprocess.CalledProcessError:
            return False
    
    async def sync_rules(self):
        """Synchronize database with current iptables rules."""
        # Get current iptables rules
        result = subprocess.run(["iptables-save"], 
                              capture_output=True, text=True)
        
        current_rules = result.stdout
        
        # Parse and store rules
        await self.repository.set_config("last_sync", datetime.now().isoformat())
        await self.repository.set_config("iptables_dump", current_rules)
    
    async def backup_config(self) -> str:
        """Create a backup of current configuration."""
        result = subprocess.run(["iptables-save"], 
                              capture_output=True, text=True)
        
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "iptables_rules": result.stdout,
            "firewallo_rules": await self.repository.list_rules()
        }
        
        backup_json = json.dumps(backup_data, indent=2)
        
        # Store backup
        backup_id = await self.repository.create_backup(backup_data)
        
        return backup_json
    
    async def restore_config(self, backup_data: str) -> bool:
        """Restore configuration from backup."""
        try:
            backup = json.loads(backup_data)
            
            # Restore iptables rules
            proc = subprocess.Popen(["iptables-restore"], 
                                  stdin=subprocess.PIPE)
            proc.communicate(input=backup["iptables_rules"].encode())
            
            if proc.returncode != 0:
                return False
            
            # Clear current rules in database
            await self.repository.clear_rules()
            
            # Restore Firewallo rules
            for rule in backup["firewallo_rules"]:
                rule_data = rule.copy()
                rule_data.pop("id", None)
                await self.repository.create_rule(rule_data)
            
            return True
        except Exception:
            return False
    
    def _build_iptables_command(self, config: Dict[str, Any]) -> List[str]:
        """Build iptables command from configuration."""
        cmd = ["iptables"]
        
        # Table
        if config.get("table") and config["table"] != "filter":
            cmd.extend(["-t", config["table"]])
        
        # Action (append)
        cmd.extend(["-A", config.get("chain", "INPUT")])
        
        # Protocol
        if config.get("protocol"):
            cmd.extend(["-p", config["protocol"]])
        
        # Source
        if config.get("source"):
            cmd.extend(["-s", config["source"]])
        
        # Destination
        if config.get("destination"):
            cmd.extend(["-d", config["destination"]])
        
        # Port
        if config.get("port"):
            if config.get("protocol") in ["tcp", "udp"]:
                cmd.extend(["--dport", str(config["port"])])
        
        # Source port
        if config.get("source_port"):
            if config.get("protocol") in ["tcp", "udp"]:
                cmd.extend(["--sport", str(config["source_port"])])
        
        # Interface
        if config.get("input_interface"):
            cmd.extend(["-i", config["input_interface"]])
        
        if config.get("output_interface"):
            cmd.extend(["-o", config["output_interface"]])
        
        # Action
        cmd.extend(["-j", config.get("action", "ACCEPT")])
        
        return cmd
```

## Plugin Manifest Examples

### Complete Manifest for VPN Plugin

```json
{
  "name": "openvpn",
  "display_name": "OpenVPN Server",
  "category": "vpn",
  "version": "1.2.0",
  "description": "OpenVPN server and client management with certificate authority support",
  "author": "OpenVPN Community",
  "email": "support@openvpn.example.com",
  "license": "GPL-2.0",
  "repository": "https://github.com/firewallo/openvpn-plugin",
  "homepage": "https://openvpn.net",
  "documentation": "https://docs.openvpn.example.com",
  "dependencies": {
    "python": ">=3.11,<4.0",
    "packages": [
      "cryptography>=3.4.0",
      "pyOpenSSL>=22.0.0",
      "python-dateutil>=2.8.0"
    ],
    "system": [
      "openvpn",
      "openssl",
      "easy-rsa"
    ],
    "optional": [
      "iptables"
    ]
  },
  "permissions": [
    "network.create",
    "network.modify",
    "network.read",
    "file.read",
    "file.write",
    "system.execute",
    "database.read",
    "database.write"
  ],
  "configuration": {
    "required": [
      "server_endpoint",
      "server_port",
      "ca_cert_path"
    ],
    "optional": [
      "cipher",
      "auth_digest",
      "compression",
      "max_clients",
      "client_to_client",
      "log_level"
    ],
    "defaults": {
      "server_port": 1194,
      "cipher": "AES-256-GCM",
      "auth_digest": "SHA256",
      "compression": "lz4",
      "max_clients": 100,
      "client_to_client": false,
      "log_level": "info"
    }
  },
  "api_prefix": "/api/vpn/openvpn",
  "database_path": "plugins.vpn.openvpn",
  "supports_hot_reload": true,
  "min_firewallo_version": "1.0.0",
  "max_firewallo_version": "2.0.0",
  "platform_support": ["linux", "windows", "darwin"],
  "architecture_support": ["x86_64", "arm64"],
  "tags": ["vpn", "openvpn", "ssl", "security"],
  "icon": "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPC9zdmc+",
  "screenshots": [
    "https://example.com/screenshot1.png",
    "https://example.com/screenshot2.png"
  ],
  "changelog": "https://github.com/firewallo/openvpn-plugin/blob/main/CHANGELOG.md",
  "security": {
    "vulnerabilities_url": "https://github.com/firewallo/openvpn-plugin/security/advisories",
    "pgp_key": "-----BEGIN PGP PUBLIC KEY BLOCK-----\n...\n-----END PGP PUBLIC KEY BLOCK-----"
  },
  "support": {
    "email": "support@example.com",
    "forum": "https://forum.example.com",
    "docs": "https://docs.example.com",
    "issues": "https://github.com/firewallo/openvpn-plugin/issues"
  },
  "metrics": {
    "collect_usage": true,
    "collect_errors": true,
    "anonymize_data": true
  }
}
```

These examples provide comprehensive implementations that demonstrate best practices for plugin development in Firewallo. Each example includes proper error handling, validation, logging, and follows the established patterns for integration with the platform.
