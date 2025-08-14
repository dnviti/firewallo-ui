from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
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
    if not repo.get_server(server_interface):
        raise HTTPException(status_code=404, detail="Server not found")
    private_key = wireguard.generate_private_key()
    public_key = wireguard.generate_public_key(private_key)
    preshared_key = wireguard.generate_preshared_key()
    if not is_ip_valid(peer.allowed_ips) or not is_ip_valid(peer.private_ip):
        raise HTTPException(status_code=400, detail="IP error")
    doc = PeerDoc(server_interface=server_interface, username=peer.username, private_ip=peer.private_ip, private_key=private_key, public_key=public_key, allowed_ips=peer.allowed_ips, endpoint=peer.endpoint, group=peer.group, persistent_keepalive=peer.persistent_keepalive, preshared_key=preshared_key)
    try:
        repo.create_peer(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.PeerCreateResponse(username=doc.username, server_interface=doc.server_interface, private_ip=doc.private_ip, allowed_ips=doc.allowed_ips, endpoint=doc.endpoint or "", group=doc.group or "", persistent_keepalive=doc.persistent_keepalive, public_key=doc.public_key, preshared_key=doc.preshared_key, private_key=private_key)

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
        raise HTTPException(status_code=400, detail="IP error")
    updated = repo.update_peer(existing.server_interface, username, allowed_ips=allowed_ips)
    return schemas.Peer(username=updated.username, server_interface=updated.server_interface, private_ip=updated.private_ip, allowed_ips=updated.allowed_ips, endpoint=updated.endpoint or "", group=updated.group or "", persistent_keepalive=updated.persistent_keepalive, public_key=updated.public_key, preshared_key=updated.preshared_key)

@router.get("/next_ip")
def next_ips(server_interface: Optional[str] = None, user: models.User = Depends(current_active_user)):
    peers = repo.list_peers(server_interface)
    ip_list = [p.private_ip.split('/')[0] for p in peers]
    if not ip_list:
        return ""
    ordered_ips = sorted(ip_list, key=ipaddress.ip_address)
    ip_max = ipaddress.ip_address(ordered_ips[-1])
    next_ip = ip_max + 1
    while str(next_ip).endswith('.0') or str(next_ip).endswith('.1') or str(next_ip).endswith('.255'):
        next_ip += 1
    return str(next_ip)
