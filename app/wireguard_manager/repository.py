"""Repository abstraction for metadata (servers & peers).

Provides a uniform synchronous API used by the FastAPI routes regardless of
whether the underlying storage is MongoDB (async) or LiteDB (local JSON).

Design choices:
- Public repository methods are synchronous for minimal intrusion into existing
  route code (which expects sync SQLAlchemy-like interactions).
- If MongoDB backend is selected, we run async Motor calls via asyncio.run()
  wrappers. For production you might migrate routes to async and await these
  calls directly, but this keeps diff small now.
- LiteDB is a simple read/modify/write JSON pattern adequate for low write
  volume metadata.

Document shapes:
Server: {interface, private_key, public_key, listen_port, mtu, address}
Peer: {username, server_interface, private_ip, private_key, public_key,
       allowed_ips, endpoint, preshared_key, group, persistent_keepalive}
"""
from __future__ import annotations

import asyncio
import json
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

# ------------------ LiteDB implementation ------------------
class LiteDBBackend:
    def _read(self):
        with open(LITE_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(LITE_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # Servers
    def get_server(self, interface: str) -> Optional[ServerDoc]:
        for s in self._read()["servers"]:
            if s["interface"] == interface:
                return ServerDoc(**s)
        return None

    def list_servers(self) -> List[ServerDoc]:
        return [ServerDoc(**s) for s in self._read()["servers"]]

    def create_server(self, server: ServerDoc):
        data = self._read()
        if any(s["interface"] == server.interface for s in data["servers"]):
            raise ValueError("Server already exists")
        data["servers"].append(asdict(server))
        self._write(data)

    def update_server(self, interface: str, listen_port: int, address: str, mtu: int) -> ServerDoc:
        data = self._read()
        for s in data["servers"]:
            if s["interface"] == interface:
                s["listen_port"] = listen_port
                s["address"] = address
                s["mtu"] = mtu
                self._write(data)
                return ServerDoc(**s)
        raise ValueError("Server not found")

    def delete_server(self, interface: str):
        data = self._read()
        new_servers = [s for s in data["servers"] if s["interface"] != interface]
        if len(new_servers) == len(data["servers"]):
            raise ValueError("Server not found")
        # cascade delete peers
        data["servers"] = new_servers
        data["peers"] = [p for p in data["peers"] if p["server_interface"] != interface]
        self._write(data)

    # Peers
    def list_peers(self, server_interface: Optional[str] = None) -> List[PeerDoc]:
        peers = self._read()["peers"]
        if server_interface:
            peers = [p for p in peers if p["server_interface"] == server_interface]
        return [PeerDoc(**p) for p in peers]

    def get_peer(self, server_interface: str, username: str) -> Optional[PeerDoc]:
        for p in self._read()["peers"]:
            if p["server_interface"] == server_interface and p["username"] == username:
                return PeerDoc(**p)
        return None

    def get_peer_by_username(self, username: str) -> Optional[PeerDoc]:
        for p in self._read()["peers"]:
            if p["username"] == username:
                return PeerDoc(**p)
        return None

    def create_peer(self, peer: PeerDoc):
        data = self._read()
        if not any(s["interface"] == peer.server_interface for s in data["servers"]):
            raise ValueError("Server not found")
        if any(p["username"] == peer.username and p["server_interface"] == peer.server_interface for p in data["peers"]):
            raise ValueError("Peer already exists")
        data["peers"].append(asdict(peer))
        self._write(data)
        return peer

    def update_peer(self, server_interface: str, username: str, **fields) -> PeerDoc:
        data = self._read()
        for p in data["peers"]:
            if p["server_interface"] == server_interface and p["username"] == username:
                p.update({k: v for k, v in fields.items() if v is not None})
                self._write(data)
                return PeerDoc(**p)
        raise ValueError("Peer not found")

    def delete_peer(self, server_interface: str, username: str):
        data = self._read()
        new_peers = [p for p in data["peers"] if not (p["server_interface"] == server_interface and p["username"] == username)]
        if len(new_peers) == len(data["peers"]):
            raise ValueError("Peer not found")
        data["peers"] = new_peers
        self._write(data)

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

# ------------------ Public factory ------------------
if DATABASE_TYPE == "mongodb":
    repo = MongoBackend()
else:
    repo = LiteDBBackend()

__all__ = ["repo", "ServerDoc", "PeerDoc"]
