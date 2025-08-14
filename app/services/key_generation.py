"""Key generation service for WireGuard."""
from __future__ import annotations

from dataclasses import dataclass
from app.services import wireguard


@dataclass
class WireGuardKeys:
    """Container for WireGuard key triplet."""
    private_key: str
    public_key: str
    preshared_key: str


class KeyGenerationService:
    """Service for generating WireGuard cryptographic keys."""
    
    @staticmethod
    def generate_key_triplet() -> WireGuardKeys:
        """Generate a complete set of keys for a WireGuard peer."""
        private_key = wireguard.generate_private_key()
        public_key = wireguard.generate_public_key(private_key)
        preshared_key = wireguard.generate_preshared_key()
        
        return WireGuardKeys(
            private_key=private_key,
            public_key=public_key,
            preshared_key=preshared_key
        )
    
    @staticmethod
    def generate_server_keys() -> tuple[str, str]:
        """Generate private and public keys for a WireGuard server."""
        private_key = wireguard.generate_private_key()
        public_key = wireguard.generate_public_key(private_key)
        return private_key, public_key
