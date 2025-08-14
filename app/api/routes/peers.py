from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from typing import List, Optional
from app.wireguard_manager import schemas
from app.wireguard_manager.repository import repo, PeerDoc
from app.auth.models import current_active_user
from app.wireguard_manager.repository import UserDoc
from app.services import wireguard
from app.services.key_generation import KeyGenerationService
from app.services.ip_allocation import IPAllocationService
from app.services.validation import ValidationService

router = APIRouter(tags=["peers"])

@router.post("/servers/{server_interface}/peers/", response_model=schemas.PeerCreateResponse)
def create_peer_for_server(server_interface: str, peer: schemas.PeerCreate, user: UserDoc = Depends(current_active_user)):
    """Create a peer.
    If peer.private_ip is blank or the literal 'auto', the next available IP within the server network is assigned.
    'allowed_ips' may use 0.0.0.0/0 but private_ip cannot.
    """
    server_doc = repo.get_server(server_interface)
    if not server_doc:
        raise HTTPException(status_code=404, detail="Server not found")

    keys = KeyGenerationService.generate_key_triplet()
    desired_private_ip = _resolve_private_ip(server_doc, server_interface, peer.private_ip)
    ValidationService.validate_peer_ips(desired_private_ip, peer.allowed_ips)

    doc = PeerDoc(
        server_interface=server_interface, 
        username=peer.username, 
        private_ip=desired_private_ip, 
        private_key=keys.private_key, 
        public_key=keys.public_key, 
        allowed_ips=peer.allowed_ips, 
        endpoint=peer.endpoint, 
        group=peer.group, 
        persistent_keepalive=peer.persistent_keepalive, 
        preshared_key=keys.preshared_key
    )
    try:
        repo.create_peer(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return schemas.PeerCreateResponse(
        username=doc.username, 
        server_interface=doc.server_interface, 
        private_ip=doc.private_ip, 
        allowed_ips=doc.allowed_ips, 
        endpoint=doc.endpoint or "", 
        group=doc.group or "", 
        persistent_keepalive=doc.persistent_keepalive, 
        public_key=doc.public_key, 
        preshared_key=doc.preshared_key, 
        private_key=keys.private_key
    )


def _resolve_private_ip(server_doc, server_interface: str, requested: str) -> str:
    """Resolve the private IP for a peer, auto-allocating if needed."""
    requested = (requested or '').strip()
    if requested and requested.lower() != 'auto':
        return requested
    
    return IPAllocationService.get_next_available_ip(server_interface, server_doc.address)

@router.put("/servers/{server_interface}/peers/{peer_username}", response_model=schemas.Peer)
def update_peer(server_interface: str, peer_username: str, peer: schemas.PeerUpdate, user: UserDoc = Depends(current_active_user)):
    try:
        updated = repo.update_peer(server_interface, peer_username, allowed_ips=peer.allowed_ips, endpoint=peer.endpoint, persistent_keepalive=peer.persistent_keepalive)
    except ValueError:
        raise HTTPException(status_code=404, detail="Peer not found")
    return schemas.Peer(username=updated.username, server_interface=updated.server_interface, private_ip=updated.private_ip, allowed_ips=updated.allowed_ips, endpoint=updated.endpoint or "", group=updated.group or "", persistent_keepalive=updated.persistent_keepalive, public_key=updated.public_key, preshared_key=updated.preshared_key)

@router.delete("/servers/{server_interface}/peers/{peer_username}")
def delete_peer(server_interface: str, peer_username: str, user: UserDoc = Depends(current_active_user)):
    try:
        repo.delete_peer(server_interface, peer_username)
    except ValueError:
        raise HTTPException(status_code=404, detail="Peer not found")
    return {"detail": "Peer deleted"}

@router.post("/peers/{peer_username}/persist")
def persist_peer_config(peer_username: str, custom_allowed_ips: Optional[str] = None, user: UserDoc = Depends(current_active_user)):
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
def get_peers(server_interface: Optional[str] = None, user: UserDoc = Depends(current_active_user)):
    peers = repo.list_peers(server_interface)
    return [schemas.Peer(username=p.username, server_interface=p.server_interface, private_ip=p.private_ip, allowed_ips=p.allowed_ips, endpoint=p.endpoint or "", group=p.group or "", persistent_keepalive=p.persistent_keepalive, public_key=p.public_key, preshared_key=p.preshared_key) for p in peers]

@router.put("/peers/{username}/allowed_ips", response_model=schemas.Peer)
def update_peer_allowed_ips(username: str, allowed_ips: str, user: UserDoc = Depends(current_active_user)):
    existing = repo.get_peer_by_username(username)
    if not existing:
        raise HTTPException(status_code=404, detail="Peer not found")
    
    ValidationService.validate_allowed_ips_format(allowed_ips)
    updated = repo.update_peer(existing.server_interface, username, allowed_ips=allowed_ips)
    
    return schemas.Peer(
        username=updated.username, 
        server_interface=updated.server_interface, 
        private_ip=updated.private_ip, 
        allowed_ips=updated.allowed_ips, 
        endpoint=updated.endpoint or "", 
        group=updated.group or "", 
        persistent_keepalive=updated.persistent_keepalive, 
        public_key=updated.public_key, 
        preshared_key=updated.preshared_key
    )

@router.get("/next_ip")
def next_ips(server_interface: Optional[str] = None, user: UserDoc = Depends(current_active_user)):
    peers = repo.list_peers(server_interface)
    used_ips = {p.private_ip.split('/')[0] for p in peers}
    
    if not used_ips:
        return PlainTextResponse(IPAllocationService.get_first_ip_when_empty(server_interface))
    
    return PlainTextResponse(IPAllocationService.increment_ip(used_ips))
