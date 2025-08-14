from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from typing import List, Optional
import ipaddress
from app.wireguard_manager import models, schemas
from app.wireguard_manager.repository import repo, PeerDoc
from app.users.users import current_active_user
from app.services import wireguard
from app.core.validators import is_ip_valid

router = APIRouter(tags=["peers"])

@router.post("/servers/{server_interface}/peers/", response_model=schemas.PeerCreateResponse)
def create_peer_for_server(server_interface: str, peer: schemas.PeerCreate, user: models.User = Depends(current_active_user)):
    """Create a peer.
    If peer.private_ip is blank or the literal 'auto', the next available IP within the server network is assigned.
    'allowed_ips' may use 0.0.0.0/0 but private_ip cannot.
    """
    server_doc = repo.get_server(server_interface)
    if not server_doc:
        raise HTTPException(status_code=404, detail="Server not found")

    private_key, public_key, preshared_key = _generate_keys()
    desired_private_ip = _resolve_private_ip(server_doc, server_interface, peer.private_ip)
    _validate_peer_ips(desired_private_ip, peer.allowed_ips)

    doc = PeerDoc(server_interface=server_interface, username=peer.username, private_ip=desired_private_ip, private_key=private_key, public_key=public_key, allowed_ips=peer.allowed_ips, endpoint=peer.endpoint, group=peer.group, persistent_keepalive=peer.persistent_keepalive, preshared_key=preshared_key)
    try:
        repo.create_peer(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.PeerCreateResponse(username=doc.username, server_interface=doc.server_interface, private_ip=doc.private_ip, allowed_ips=doc.allowed_ips, endpoint=doc.endpoint or "", group=doc.group or "", persistent_keepalive=doc.persistent_keepalive, public_key=doc.public_key, preshared_key=doc.preshared_key, private_key=private_key)


def _generate_keys():
    private_key = wireguard.generate_private_key()
    public_key = wireguard.generate_public_key(private_key)
    preshared_key = wireguard.generate_preshared_key()
    return private_key, public_key, preshared_key


def _resolve_private_ip(server_doc, server_interface: str, requested: str) -> str:
    requested = (requested or '').strip()
    if requested and requested.lower() != 'auto':
        return requested
    try:
        network = ipaddress.ip_network(server_doc.address, strict=False)
    except ValueError:
        raise HTTPException(status_code=500, detail="Server address invalid; cannot allocate IP")
    existing_ips = {p.private_ip.split('/')[0] for p in repo.list_peers(server_interface)}
    for host in network.hosts():
        if str(host) not in existing_ips:
            return f"{host}/{network.prefixlen}"
    raise HTTPException(status_code=409, detail="No available private IPs in server network")


def _validate_peer_ips(private_ip: str, allowed_ips: str) -> None:
    errors = []
    if not is_ip_valid(private_ip):
        errors.append("private_ip is invalid (expected IPv4 address optionally with /CIDR 1-32, e.g. 10.0.0.5/32)")
    else:
        if '/' in private_ip:
            try:
                m = int(private_ip.split('/')[1])
                if m == 0:
                    errors.append("private_ip mask /0 not allowed; use 1-32")
            except ValueError:
                errors.append("private_ip CIDR mask invalid")
    if not is_ip_valid(allowed_ips):
        errors.append("allowed_ips is invalid (expected comma-separated IPv4 or IPv4/CIDR entries, e.g. 10.0.0.5/32,10.0.0.0/24,0.0.0.0/0)")
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

@router.put("/servers/{server_interface}/peers/{peer_username}", response_model=schemas.Peer)
def update_peer(server_interface: str, peer_username: str, peer: schemas.PeerUpdate, user: models.User = Depends(current_active_user)):
    try:
        updated = repo.update_peer(server_interface, peer_username, allowed_ips=peer.allowed_ips, endpoint=peer.endpoint, persistent_keepalive=peer.persistent_keepalive)
    except ValueError:
        raise HTTPException(status_code=404, detail="Peer not found")
    return schemas.Peer(username=updated.username, server_interface=updated.server_interface, private_ip=updated.private_ip, allowed_ips=updated.allowed_ips, endpoint=updated.endpoint or "", group=updated.group or "", persistent_keepalive=updated.persistent_keepalive, public_key=updated.public_key, preshared_key=updated.preshared_key)

@router.delete("/servers/{server_interface}/peers/{peer_username}")
def delete_peer(server_interface: str, peer_username: str, user: models.User = Depends(current_active_user)):
    try:
        repo.delete_peer(server_interface, peer_username)
    except ValueError:
        raise HTTPException(status_code=404, detail="Peer not found")
    return {"detail": "Peer deleted"}

@router.post("/peers/{peer_username}/persist")
def persist_peer_config(peer_username: str, custom_allowed_ips: Optional[str] = None, user: models.User = Depends(current_active_user)):
    wg_peer = repo.get_peer_by_username(peer_username)
    if not wg_peer:
        raise HTTPException(status_code=404, detail="Server not found")
    if custom_allowed_ips:
        wg_peer.allowed_ips = custom_allowed_ips
    srv = repo.get_server(wg_peer.server_interface)
    if not srv:
        raise HTTPException(status_code=404, detail="Server not found")
    peer_struct = wireguard.PeerFullConfigLite(private_ip=wg_peer.private_ip, private_key=wg_peer.private_key, server=wireguard.ServerRefLite(public_key=srv.public_key, mtu=srv.mtu), endpoint=wg_peer.endpoint, allowed_ips=wg_peer.allowed_ips, preshared_key=wg_peer.preshared_key, persistent_keepalive=wg_peer.persistent_keepalive)
    conf_content = wireguard.render_peer_config(peer_struct)
    filename = f"{peer_username}.conf"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(conf_content)
    return FileResponse(filename, media_type="text/plain", filename=filename)

@router.get("/peers", response_model=List[schemas.Peer])
def get_peers(server_interface: Optional[str] = None, user: models.User = Depends(current_active_user)):
    peers = repo.list_peers(server_interface)
    return [schemas.Peer(username=p.username, server_interface=p.server_interface, private_ip=p.private_ip, allowed_ips=p.allowed_ips, endpoint=p.endpoint or "", group=p.group or "", persistent_keepalive=p.persistent_keepalive, public_key=p.public_key, preshared_key=p.preshared_key) for p in peers]

@router.put("/peers/{username}/allowed_ips", response_model=schemas.Peer)
def update_peer_allowed_ips(username: str, allowed_ips: str, user: models.User = Depends(current_active_user)):
    existing = repo.get_peer_by_username(username)
    if not existing:
        raise HTTPException(status_code=404, detail="Peer not found")
    if not is_ip_valid(allowed_ips):
        raise HTTPException(status_code=400, detail="allowed_ips is invalid (expected comma-separated IPv4 or IPv4/CIDR entries 0-32, e.g. 10.0.0.5/32,10.0.0.0/24,0.0.0.0/0)")
    updated = repo.update_peer(existing.server_interface, username, allowed_ips=allowed_ips)
    return schemas.Peer(username=updated.username, server_interface=updated.server_interface, private_ip=updated.private_ip, allowed_ips=updated.allowed_ips, endpoint=updated.endpoint or "", group=updated.group or "", persistent_keepalive=updated.persistent_keepalive, public_key=updated.public_key, preshared_key=updated.preshared_key)

@router.get("/next_ip")
def next_ips(server_interface: Optional[str] = None, user: models.User = Depends(current_active_user)):
    peers = repo.list_peers(server_interface)
    used_ips = {p.private_ip.split('/')[0] for p in peers}
    if not used_ips:
        return PlainTextResponse(_first_ip_when_empty(server_interface))
    return PlainTextResponse(_increment_ip(used_ips))


def _first_ip_when_empty(server_interface: Optional[str]) -> str:
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
        if h == server_ip or h.endswith('.0') or h.endswith('.255'):
            continue
        return h
    return ""


def _increment_ip(used_ips: set[str]) -> str:
    ordered = sorted(used_ips, key=ipaddress.ip_address)
    ip_max = ipaddress.ip_address(ordered[-1])
    next_ip = ip_max + 1
    while str(next_ip).endswith('.0') or str(next_ip).endswith('.1') or str(next_ip).endswith('.255'):
        next_ip += 1
    return str(next_ip)
