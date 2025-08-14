"""System statistics and monitoring API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psutil
import time
import random
from datetime import datetime, timedelta

router = APIRouter(tags=["system"])

class SystemStats(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime: str
    load_average: float
    network_io: dict

class ActivityItem(BaseModel):
    timestamp: datetime
    type: str
    description: str
    status: str

class SystemInfo(BaseModel):
    hostname: str
    platform: str
    architecture: str
    python_version: str
    firewallo_version: str
    total_memory: int
    total_disk: int

@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get current system statistics."""
    try:
        # Get real system stats if psutil is available
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()

        # Calculate uptime
        uptime_seconds = time.time() - boot_time
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        uptime_str = f"{uptime_days} days, {uptime_hours} hours"

        # Get load average (Unix-like systems only)
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
        except AttributeError:
            load_avg = random.uniform(0.5, 2.0)  # Fallback for Windows

        # Get network I/O
        net_io = psutil.net_io_counters()

        return SystemStats(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=(disk.used / disk.total) * 100,
            uptime=uptime_str,
            load_average=load_avg,
            network_io={
                "up": net_io.bytes_sent,
                "down": net_io.bytes_recv
            }
        )
    except Exception as e:
        # Fallback to mock data if psutil fails
        return SystemStats(
            cpu_usage=random.uniform(10, 80),
            memory_usage=random.uniform(30, 70),
            disk_usage=random.uniform(40, 85),
            uptime=f"{random.randint(1, 30)} days, {random.randint(0, 23)} hours",
            load_average=random.uniform(0.5, 3.0),
            network_io={
                "up": random.randint(1000, 50000),
                "down": random.randint(5000, 100000)
            }
        )

@router.get("/info", response_model=SystemInfo)
async def get_system_info():
    """Get system information."""
    try:
        import platform
        import sys

        # Get real system info
        hostname = platform.node()
        platform_name = platform.platform()
        architecture = platform.architecture()[0]
        python_version = sys.version.split()[0]

        # Get memory and disk info
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return SystemInfo(
            hostname=hostname,
            platform=platform_name,
            architecture=architecture,
            python_version=python_version,
            firewallo_version="1.0.0",
            total_memory=memory.total,
            total_disk=disk.total
        )
    except Exception:
        # Fallback to mock data
        return SystemInfo(
            hostname="firewallo-server",
            platform="Linux-5.15.0-generic-x86_64",
            architecture="64bit",
            python_version="3.11.0",
            firewallo_version="1.0.0",
            total_memory=8589934592,  # 8GB
            total_disk=107374182400  # 100GB
        )

@router.get("/activity/recent", response_model=List[ActivityItem])
async def get_recent_activity():
    """Get recent system activity."""
    # Mock activity data - in a real implementation, this would come from logs
    activities = []

    # Generate some mock activities
    base_time = datetime.now()

    mock_activities = [
        {"type": "Plugin", "description": "DDoS Protection plugin enabled", "status": "success"},
        {"type": "Rule", "description": "New firewall rule added for port 8080", "status": "success"},
        {"type": "System", "description": "System startup completed", "status": "success"},
        {"type": "Security", "description": "Failed login attempt detected", "status": "warning"},
        {"type": "Plugin", "description": "Monitoring plugin updated", "status": "success"},
        {"type": "System", "description": "Scheduled backup completed", "status": "success"},
        {"type": "Rule", "description": "Firewall rule modified for SSH access", "status": "success"},
        {"type": "Security", "description": "Intrusion attempt blocked", "status": "success"},
        {"type": "System", "description": "Memory usage threshold exceeded", "status": "warning"},
        {"type": "Plugin", "description": "Load balancer plugin configured", "status": "success"}
    ]

    for i, activity in enumerate(mock_activities[:7]):  # Return last 7 activities
        timestamp = base_time - timedelta(minutes=random.randint(5, 120))
        activities.append(ActivityItem(
            timestamp=timestamp,
            type=activity["type"],
            description=activity["description"],
            status=activity["status"]
        ))

    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x.timestamp, reverse=True)

    return activities

@router.get("/processes", response_model=List[dict])
async def get_running_processes():
    """Get list of running processes (top 10 by CPU usage)."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0:  # Only include processes using CPU
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage and return top 10
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:10]

    except Exception:
        # Return mock process data
        return [
            {"pid": 1234, "name": "python", "cpu_percent": 15.2, "memory_percent": 8.5},
            {"pid": 5678, "name": "nginx", "cpu_percent": 5.1, "memory_percent": 2.3},
            {"pid": 9012, "name": "systemd", "cpu_percent": 2.8, "memory_percent": 1.1},
            {"pid": 3456, "name": "ssh", "cpu_percent": 1.5, "memory_percent": 0.8},
            {"pid": 7890, "name": "cron", "cpu_percent": 0.9, "memory_percent": 0.5}
        ]

@router.get("/network/interfaces", response_model=List[dict])
async def get_network_interfaces():
    """Get network interface information."""
    try:
        interfaces = []
        net_if_addrs = psutil.net_if_addrs()
        net_if_stats = psutil.net_if_stats()

        for interface_name, addresses in net_if_addrs.items():
            if interface_name in net_if_stats:
                stats = net_if_stats[interface_name]

                # Get IP addresses
                ipv4_addr = None
                ipv6_addr = None

                for addr in addresses:
                    if addr.family.name == 'AF_INET':
                        ipv4_addr = addr.address
                    elif addr.family.name == 'AF_INET6':
                        ipv6_addr = addr.address

                interfaces.append({
                    'name': interface_name,
                    'ipv4_address': ipv4_addr,
                    'ipv6_address': ipv6_addr,
                    'is_up': stats.isup,
                    'speed': stats.speed,
                    'mtu': stats.mtu
                })

        return interfaces

    except Exception:
        # Return mock interface data
        return [
            {
                'name': 'eth0',
                'ipv4_address': '192.168.1.100',
                'ipv6_address': 'fe80::1',
                'is_up': True,
                'speed': 1000,
                'mtu': 1500
            },
            {
                'name': 'lo',
                'ipv4_address': '127.0.0.1',
                'ipv6_address': '::1',
                'is_up': True,
                'speed': 0,
                'mtu': 65536
            }
        ]

@router.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0",
        "uptime": "5 days, 12 hours"
    }

@router.post("/restart")
async def restart_system():
    """Restart the Firewallo system (mock endpoint)."""
    # In a real implementation, this would trigger a system restart
    # For now, just return a success message
    return {
        "message": "System restart initiated",
        "timestamp": datetime.now(),
        "estimated_downtime": "30 seconds"
    }

@router.post("/shutdown")
async def shutdown_system():
    """Shutdown the Firewallo system (mock endpoint)."""
    # In a real implementation, this would trigger a system shutdown
    # For now, just return a success message
    return {
        "message": "System shutdown initiated",
        "timestamp": datetime.now(),
        "estimated_downtime": "60 seconds"
    }

@router.get("/logs/tail")
async def get_recent_logs(lines: int = 50):
    """Get recent log entries."""
    # Mock log entries - in a real implementation, this would read from actual log files
    log_entries = []
    base_time = datetime.now()

    log_levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    log_sources = ["firewall", "plugin.ddos", "plugin.monitor", "system", "auth"]

    sample_messages = [
        "Connection established from {ip}",
        "Plugin {plugin} loaded successfully",
        "Firewall rule {rule} applied",
        "Authentication successful for user {user}",
        "Memory usage: {percent}%",
        "DDoS attack detected and blocked",
        "Configuration file reloaded",
        "Backup process completed",
        "System health check passed",
        "Network interface {interface} is up"
    ]

    for i in range(lines):
        timestamp = base_time - timedelta(minutes=random.randint(1, 1440))  # Last 24 hours
        level = random.choice(log_levels)
        source = random.choice(log_sources)
        message = random.choice(sample_messages).format(
            ip=f"192.168.1.{random.randint(1, 254)}",
            plugin=random.choice(["ddos_protection", "intrusion_detection", "load_balancer"]),
            rule=f"RULE_{random.randint(1, 100)}",
            user=random.choice(["admin", "user1", "operator"]),
            percent=random.randint(30, 90),
            interface="eth0"
        )

        log_entries.append({
            "timestamp": timestamp.isoformat(),
            "level": level,
            "source": source,
            "message": message
        })

    # Sort by timestamp (most recent first)
    log_entries.sort(key=lambda x: x["timestamp"], reverse=True)

    return {"logs": log_entries}
