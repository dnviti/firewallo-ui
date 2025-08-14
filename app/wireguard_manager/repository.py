"""Repository abstraction for metadata (servers, peers & users).

Provides a uniform synchronous API used by the FastAPI routes regardless of
whether the underlying storage is MongoDB (async) or LiteDB (local JSON).

Design choices:
- Public repository methods are synchronous for minimal intrusion into existing
  route code (which expects sync interactions).
- If MongoDB backend is selected, we run async Motor calls via asyncio.run()
  wrappers. For production you might migrate routes to async and await these
  calls directly, but this keeps diff small now.
- LiteDB is a simple read/modify/write JSON pattern adequate for low write
  volume metadata.

Document shapes:
Server: {interface, private_key, public_key, listen_port, mtu, address}
Peer: {username, server_interface, private_ip, private_key, public_key,
       allowed_ips, endpoint, preshared_key, group, persistent_keepalive}
User: {email, username, hashed_password, is_active, is_superuser, created_at}

Database Structure:
The database follows a modular structure with sections:
- plugins.vpn.wireguard: WireGuard VPN plugin data (servers, peers)
- core.*: Core application functions and configuration
- auth.users: User authentication data
- auth.rbac: Role-based access control (roles, permissions, assignments)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from typing import List, Optional

from .database import DATABASE_TYPE, mongo_db, LITE_DB_FILE

# ------------------ Data Models ------------------
@dataclass
class ServerDoc:
    interface: str
    private_key: str
    public_key: str
    listen_port: int
    address: str
    mtu: int

@dataclass
class PeerDoc:
    username: str
    server_interface: str
    private_ip: str
    private_key: str
    public_key: str
    allowed_ips: str
    endpoint: Optional[str]
    group: Optional[str]
    persistent_keepalive: Optional[int]
    preshared_key: Optional[str]

@dataclass  
class UserDoc:
    email: str
    username: str
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[str] = None

# ------------------ LiteDB implementation ------------------
from .backends.litedb import LiteDBBackend as _LiteDBBackend

class LiteDBBackend(_LiteDBBackend):
    """Wrapper to maintain compatibility with existing repository interface."""
    def __init__(self):
        super().__init__(str(LITE_DB_FILE))

# ------------------ Mongo implementation ------------------
class MongoBackend:
    def __init__(self):
        self.servers = mongo_db["servers"]
        self.peers = mongo_db["peers"]

    # Helper to run async functions in sync context
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    # Servers
    def get_server(self, interface: str) -> Optional[ServerDoc]:
        doc = self._run(self.servers.find_one({"interface": interface}))
        return ServerDoc(**doc) if doc else None

    def list_servers(self) -> List[ServerDoc]:
        docs = self._run(self.servers.find({}).to_list(length=1000))
        return [ServerDoc(**d) for d in docs]

    def create_server(self, server: ServerDoc):
        if self.get_server(server.interface):
            raise ValueError("Server already exists")
        self._run(self.servers.insert_one(asdict(server)))

    def update_server(self, interface: str, listen_port: int, address: str, mtu: int) -> ServerDoc:
        res = self._run(self.servers.find_one_and_update(
            {"interface": interface},
            {"$set": {"listen_port": listen_port, "address": address, "mtu": mtu}},
            return_document=True,
        ))
        if not res:
            raise ValueError("Server not found")
        return ServerDoc(**res)

    def delete_server(self, interface: str):
        self._run(self.peers.delete_many({"server_interface": interface}))
        res = self._run(self.servers.delete_one({"interface": interface}))
        if res.deleted_count == 0:
            raise ValueError("Server not found")

    # Peers
    def list_peers(self, server_interface: Optional[str] = None) -> List[PeerDoc]:
        query = {"server_interface": server_interface} if server_interface else {}
        docs = self._run(self.peers.find(query).to_list(length=5000))
        return [PeerDoc(**d) for d in docs]

    def get_peer(self, server_interface: str, username: str) -> Optional[PeerDoc]:
        doc = self._run(self.peers.find_one({"server_interface": server_interface, "username": username}))
        return PeerDoc(**doc) if doc else None

    def get_peer_by_username(self, username: str) -> Optional[PeerDoc]:
        doc = self._run(self.peers.find_one({"username": username}))
        return PeerDoc(**doc) if doc else None

    def create_peer(self, peer: PeerDoc):
        if not self.get_server(peer.server_interface):
            raise ValueError("Server not found")
        if self.get_peer(peer.server_interface, peer.username):
            raise ValueError("Peer already exists")
        self._run(self.peers.insert_one(asdict(peer)))
        return peer

    def update_peer(self, server_interface: str, username: str, **fields) -> PeerDoc:
        update_fields = {k: v for k, v in fields.items() if v is not None}
        res = self._run(self.peers.find_one_and_update(
            {"server_interface": server_interface, "username": username},
            {"$set": update_fields},
            return_document=True,
        ))
        if not res:
            raise ValueError("Peer not found")
        return PeerDoc(**res)

    def delete_peer(self, server_interface: str, username: str):
        res = self._run(self.peers.delete_one({"server_interface": server_interface, "username": username}))
        if res.deleted_count == 0:
            raise ValueError("Peer not found")

    # Users
    def get_user_by_username(self, username: str) -> Optional[UserDoc]:
        if not hasattr(self, 'users'):
            self.users = mongo_db["users"]
        doc = self._run(self.users.find_one({"username": username}))
        return UserDoc(**doc) if doc else None

    def get_user_by_email(self, email: str) -> Optional[UserDoc]:
        if not hasattr(self, 'users'):
            self.users = mongo_db["users"]
        doc = self._run(self.users.find_one({"email": email}))
        return UserDoc(**doc) if doc else None

    def create_user(self, user: UserDoc):
        if not hasattr(self, 'users'):
            self.users = mongo_db["users"]
        if self.get_user_by_username(user.username):
            raise ValueError("User already exists")
        if self.get_user_by_email(user.email):
            raise ValueError("Email already registered")
        self._run(self.users.insert_one(asdict(user)))
        return user

    def list_users(self) -> List[UserDoc]:
        if not hasattr(self, 'users'):
            self.users = mongo_db["users"]
        docs = self._run(self.users.find({}).to_list(length=1000))
        return [UserDoc(**d) for d in docs]

# ------------------ Public factory ------------------
if DATABASE_TYPE == "mongodb":
    repo = MongoBackend()
else:
    repo = LiteDBBackend()

__all__ = ["repo", "ServerDoc", "PeerDoc", "UserDoc"]
