"""IP allocation service for WireGuard peers."""
from __future__ import annotations

import ipaddress
from typing import Optional, Set
from fastapi import HTTPException

from app.wireguard_manager.repository import repo


class IPAllocationService:
    """Service for managing IP address allocation for WireGuard peers."""
    
    @staticmethod
    def get_next_available_ip(server_interface: str, server_address: str) -> str:
        """Get the next available IP address for a peer in the server network."""
        try:
            network = ipaddress.ip_network(server_address, strict=False)
        except ValueError:
            raise HTTPException(
                status_code=500, 
                detail="Server address invalid; cannot allocate IP"
            )
        
        existing_ips = {
            p.private_ip.split('/')[0] 
            for p in repo.list_peers(server_interface)
        }
        
        for host in network.hosts():
            if str(host) not in existing_ips:
                return f"{host}/{network.prefixlen}"
        
        raise HTTPException(
            status_code=409, 
            detail="No available private IPs in server network"
        )
    
    @staticmethod
    def get_first_ip_when_empty(server_interface: Optional[str]) -> str:
        """Get the first available IP when no peers exist."""
        if not server_interface:
            return ""
        
        srv = repo.get_server(server_interface)
        if not srv:
            return ""
        
        try:
            net = ipaddress.ip_network(srv.address, strict=False)
            server_ip = srv.address.split('/')[0]
        except ValueError:
            return ""
        
        for host in net.hosts():
            h = str(host)
            # Skip server IP and common reserved addresses
            if h == server_ip or h.endswith('.0') or h.endswith('.255'):
                continue
            return h
        
        return ""
    
    @staticmethod
    def increment_ip(used_ips: Set[str]) -> str:
        """Get the next sequential IP after the highest used IP."""
        ordered = sorted(used_ips, key=ipaddress.ip_address)
        ip_max = ipaddress.ip_address(ordered[-1])
        next_ip = ip_max + 1
        
        # Skip common reserved addresses
        while str(next_ip).endswith(('.0', '.1', '.255')):
            next_ip += 1
        
        return str(next_ip)
