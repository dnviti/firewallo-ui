"""LiteDB backend implementation for WireGuard repository."""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import List, Optional

from app.wireguard_manager.repository import ServerDoc, PeerDoc, UserDoc


class LiteDBBackend:
    """Local JSON file backend for WireGuard metadata."""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
    
    def _read(self):
        """Read data from JSON file."""
        with open(self.db_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        """Write data to JSON file."""
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # Server operations
    def get_server(self, interface: str) -> Optional[ServerDoc]:
        """Get a server by interface name."""
        data = self._read()
        servers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("servers", [])
        for s in servers:
            if s["interface"] == interface:
                return ServerDoc(**s)
        return None

    def list_servers(self) -> List[ServerDoc]:
        """List all servers."""
        data = self._read()
        servers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("servers", [])
        return [ServerDoc(**s) for s in servers]

    def create_server(self, server: ServerDoc):
        """Create a new server."""
        data = self._read()
        # Ensure the structure exists
        if "plugins" not in data:
            data["plugins"] = {}
        if "vpn" not in data["plugins"]:
            data["plugins"]["vpn"] = {}
        if "wireguard" not in data["plugins"]["vpn"]:
            data["plugins"]["vpn"]["wireguard"] = {"servers": [], "peers": []}
        
        servers = data["plugins"]["vpn"]["wireguard"]["servers"]
        if any(s["interface"] == server.interface for s in servers):
            raise ValueError("Server already exists")
        servers.append(asdict(server))
        self._write(data)

    def update_server(self, interface: str, listen_port: int, address: str, mtu: int) -> ServerDoc:
        """Update server configuration."""
        data = self._read()
        servers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("servers", [])
        for s in servers:
            if s["interface"] == interface:
                s["listen_port"] = listen_port
                s["address"] = address
                s["mtu"] = mtu
                self._write(data)
                return ServerDoc(**s)
        raise ValueError("Server not found")

    def delete_server(self, interface: str):
        """Delete a server and cascade delete its peers."""
        data = self._read()
        servers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("servers", [])
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        
        new_servers = [s for s in servers if s["interface"] != interface]
        if len(new_servers) == len(servers):
            raise ValueError("Server not found")
        
        # cascade delete peers
        data["plugins"]["vpn"]["wireguard"]["servers"] = new_servers
        data["plugins"]["vpn"]["wireguard"]["peers"] = [p for p in peers if p["server_interface"] != interface]
        self._write(data)

    # Peer operations
    def list_peers(self, server_interface: Optional[str] = None) -> List[PeerDoc]:
        """List peers, optionally filtered by server interface."""
        data = self._read()
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        if server_interface:
            peers = [p for p in peers if p["server_interface"] == server_interface]
        return [PeerDoc(**p) for p in peers]

    def get_peer(self, server_interface: str, username: str) -> Optional[PeerDoc]:
        """Get a peer by server interface and username."""
        data = self._read()
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        for p in peers:
            if p["server_interface"] == server_interface and p["username"] == username:
                return PeerDoc(**p)
        return None

    def get_peer_by_username(self, username: str) -> Optional[PeerDoc]:
        """Get a peer by username only."""
        data = self._read()
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        for p in peers:
            if p["username"] == username:
                return PeerDoc(**p)
        return None

    def create_peer(self, peer: PeerDoc):
        """Create a new peer."""
        data = self._read()
        # Ensure the structure exists
        if "plugins" not in data:
            data["plugins"] = {}
        if "vpn" not in data["plugins"]:
            data["plugins"]["vpn"] = {}
        if "wireguard" not in data["plugins"]["vpn"]:
            data["plugins"]["vpn"]["wireguard"] = {"servers": [], "peers": []}
        
        servers = data["plugins"]["vpn"]["wireguard"]["servers"]
        peers = data["plugins"]["vpn"]["wireguard"]["peers"]
        
        if not any(s["interface"] == peer.server_interface for s in servers):
            raise ValueError("Server not found")
        if any(p["username"] == peer.username and p["server_interface"] == peer.server_interface for p in peers):
            raise ValueError("Peer already exists")
        peers.append(asdict(peer))
        self._write(data)
        return peer

    def update_peer(self, server_interface: str, username: str, **fields) -> PeerDoc:
        """Update peer configuration."""
        data = self._read()
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        for p in peers:
            if p["server_interface"] == server_interface and p["username"] == username:
                p.update({k: v for k, v in fields.items() if v is not None})
                self._write(data)
                return PeerDoc(**p)
        raise ValueError("Peer not found")

    def delete_peer(self, server_interface: str, username: str):
        """Delete a peer."""
        data = self._read()
        peers = data.get("plugins", {}).get("vpn", {}).get("wireguard", {}).get("peers", [])
        new_peers = [p for p in peers if not (p["server_interface"] == server_interface and p["username"] == username)]
        if len(new_peers) == len(peers):
            raise ValueError("Peer not found")
        data["plugins"]["vpn"]["wireguard"]["peers"] = new_peers
        self._write(data)

    # User operations  
    def list_users(self) -> List[UserDoc]:
        """List all users."""
        data = self._read()
        users = data.get("auth", {}).get("users", [])
        return [UserDoc(**u) for u in users]

    def get_user_by_username(self, username: str) -> Optional[UserDoc]:
        """Get a user by username."""
        data = self._read()
        users = data.get("auth", {}).get("users", [])
        for u in users:
            if u["username"] == username:
                return UserDoc(**u)
        return None

    def get_user_by_email(self, email: str) -> Optional[UserDoc]:
        """Get a user by email."""
        data = self._read()
        users = data.get("auth", {}).get("users", [])
        for u in users:
            if u["email"] == email:
                return UserDoc(**u)
        return None

    def create_user(self, user: UserDoc):
        """Create a new user."""
        data = self._read()
        # Ensure the structure exists
        if "auth" not in data:
            data["auth"] = {"users": [], "rbac": {"roles": [], "permissions": [], "assignments": []}}
        if "users" not in data["auth"]:
            data["auth"]["users"] = []
        
        users = data["auth"]["users"]
        if any(u["username"] == user.username for u in users):
            raise ValueError("User already exists")
        if any(u["email"] == user.email for u in users):
            raise ValueError("Email already exists")
        users.append(asdict(user))
        self._write(data)
        return user

    def update_user(self, username: str, **fields) -> UserDoc:
        """Update user configuration."""
        data = self._read()
        users = data.get("auth", {}).get("users", [])
        for u in users:
            if u["username"] == username:
                u.update({k: v for k, v in fields.items() if v is not None})
                self._write(data)
                return UserDoc(**u)
        raise ValueError("User not found")

    def delete_user(self, username: str):
        """Delete a user."""
        data = self._read()
        users = data.get("auth", {}).get("users", [])
        new_users = [u for u in users if u["username"] != username]
        if len(new_users) == len(users):
            raise ValueError("User not found")
        data["auth"]["users"] = new_users
        self._write(data)
