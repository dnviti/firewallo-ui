"""Validation service for network inputs."""
from __future__ import annotations

import ipaddress
from typing import List
from fastapi import HTTPException


class ValidationService:
    """Service for validating network-related inputs."""
    
    @staticmethod
    def validate_ip_address(ip_str: str) -> bool:
        """Validate a single IP address or CIDR notation."""
        try:
            ip_str = ip_str.replace(" ", "")
            for ip in ip_str.split(","):
                if not ip:
                    return False
                if "/" in ip:
                    try:
                        mask = int(ip.split("/")[1])
                    except ValueError:
                        return False
                    if mask > 32 or mask < 0:
                        return False
                    ip = ip.split("/")[0]
                ipaddress.ip_address(ip)
        except ValueError:
            return False
        return True
    
    @staticmethod
    def validate_peer_ips(private_ip: str, allowed_ips: str) -> None:
        """Validate peer IP configuration and raise detailed errors."""
        errors: List[str] = []
        
        # Validate private IP
        if not ValidationService.validate_ip_address(private_ip):
            errors.append(
                "private_ip is invalid (expected IPv4 address optionally with "
                "/CIDR 1-32, e.g. 10.0.0.5/32)"
            )
        else:
            if '/' in private_ip:
                try:
                    mask = int(private_ip.split('/')[1])
                    if mask == 0:
                        errors.append("private_ip mask /0 not allowed; use 1-32")
                except ValueError:
                    errors.append("private_ip CIDR mask invalid")
        
        # Validate allowed IPs
        if not ValidationService.validate_ip_address(allowed_ips):
            errors.append(
                "allowed_ips is invalid (expected comma-separated IPv4 or "
                "IPv4/CIDR entries, e.g. 10.0.0.5/32,10.0.0.0/24,0.0.0.0/0)"
            )
        
        if errors:
            raise HTTPException(status_code=400, detail="; ".join(errors))
    
    @staticmethod
    def validate_allowed_ips_format(allowed_ips: str) -> None:
        """Validate allowed IPs format for updates."""
        if not ValidationService.validate_ip_address(allowed_ips):
            raise HTTPException(
                status_code=400,
                detail=(
                    "allowed_ips is invalid (expected comma-separated IPv4 or "
                    "IPv4/CIDR entries 0-32, e.g. 10.0.0.5/32,10.0.0.0/24,0.0.0.0/0)"
                )
            )
