from __future__ import annotations
import ipaddress

def is_ip_valid(ip_str: str) -> bool:
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
                if mask > 32 or mask < 1:
                    return False
                ip = ip.split("/")[0]
            ipaddress.ip_address(ip)
    except ValueError:
        return False
    return True
