from __future__ import annotations
import subprocess
from dataclasses import dataclass
from typing import Iterable

def generate_private_key() -> str:
    # Execute without shell for safety
    return subprocess.check_output(["wg", "genkey"]).decode().strip()

def generate_public_key(private_key: str) -> str:
    # Pipe private key to wg pubkey without invoking a shell
    proc = subprocess.Popen(["wg", "pubkey"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate(input=private_key.encode())
    return stdout.decode().strip()

def generate_preshared_key() -> str:
    return subprocess.check_output(["wg", "genpsk"]).decode().strip()

@dataclass
class PeerConfigLite:
    public_key: str
    private_ip: str
    preshared_key: str | None
    persistent_keepalive: int | None

@dataclass
class ServerConfigLite:
    address: str
    listen_port: int
    private_key: str
    mtu: int
    peers: Iterable[PeerConfigLite]

def render_server_config(server: ServerConfigLite) -> str:
    lines: list[str] = []
    lines.append("[Interface]")
    lines.append(f"Address = {server.address}")
    lines.append(f"ListenPort = {server.listen_port}")
    lines.append(f"PrivateKey = {server.private_key}")
    lines.append(f"MTU = {server.mtu}")
    for p in server.peers:
        lines.append("\n[Peer]")
        lines.append(f"PublicKey = {p.public_key}")
        lines.append(f"AllowedIPs = {p.private_ip}")
        lines.append(f"PresharedKey = {p.preshared_key}")
        if p.persistent_keepalive is not None:
            lines.append(f"PersistentKeepalive = {p.persistent_keepalive}")
    return "\n".join(lines)

@dataclass
class ServerRefLite:
    public_key: str
    mtu: int

@dataclass
class PeerFullConfigLite:
    private_ip: str
    private_key: str
    server: ServerRefLite
    endpoint: str | None
    allowed_ips: str
    preshared_key: str | None
    persistent_keepalive: int | None

def render_peer_config(peer: PeerFullConfigLite) -> str:
    lines: list[str] = []
    lines.append("[Interface]")
    lines.append(f"Address = {peer.private_ip}")
    lines.append(f"PrivateKey = {peer.private_key}")
    lines.append(f"MTU = {peer.server.mtu}")
    lines.append("\n[Peer]")
    lines.append(f"PublicKey = {peer.server.public_key}")
    lines.append(f"Endpoint = {peer.endpoint}")
    lines.append(f"AllowedIPs = {peer.allowed_ips}")
    lines.append(f"PresharedKey = {peer.preshared_key}")
    if peer.persistent_keepalive is not None:
        lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")
    return "\n".join(lines)
