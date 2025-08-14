from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.wireguard_manager import models, schemas
from app.wireguard_manager.repository import repo, ServerDoc
from app.users.users import current_active_user
from app.services import wireguard
from app.core.validators import is_ip_valid

router = APIRouter(prefix="/servers", tags=["servers"])

@router.post("/", response_model=schemas.ServerCreateResponse)
def create_server(server: schemas.ServerCreate, user: models.User = Depends(current_active_user)):
    existing = repo.get_server(server.interface)
    if existing:
        raise HTTPException(status_code=400, detail="Server already exists")
    private_key = wireguard.generate_private_key()
    public_key = wireguard.generate_public_key(private_key)
    if not is_ip_valid(server.address):
        raise HTTPException(status_code=401, detail="This address is not an IP")
    doc = ServerDoc(interface=server.interface, private_key=private_key, public_key=public_key, listen_port=server.listen_port, address=server.address, mtu=server.mtu)
    try:
        repo.create_server(doc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.ServerCreateResponse(interface=doc.interface, listen_port=doc.listen_port, address=doc.address, mtu=doc.mtu, public_key=doc.public_key, private_key=private_key)

@router.put("/{server_interface}", response_model=schemas.Server)
def update_server(server_interface: str, server: schemas.ServerUpdate, user: models.User = Depends(current_active_user)):
    try:
        updated = repo.update_server(server_interface, server.listen_port, server.address, server.mtu)
    except ValueError:
        raise HTTPException(status_code=404, detail="Server not found")
    return schemas.Server(interface=updated.interface, listen_port=updated.listen_port, address=updated.address, mtu=updated.mtu, public_key=updated.public_key)

@router.delete("/{server_interface}")
def delete_server(server_interface: str, user: models.User = Depends(current_active_user)):
    try:
        repo.delete_server(server_interface)
    except ValueError:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"detail": "Server deleted"}

@router.post("/{server_interface}/persist")
def persist_server_config(server_interface: str, user: models.User = Depends(current_active_user)):
    db_server = repo.get_server(server_interface)
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    peers_docs = repo.list_peers(server_interface)
    peers_lite = [wireguard.PeerConfigLite(public_key=p.public_key, private_ip=p.private_ip, preshared_key=p.preshared_key, persistent_keepalive=p.persistent_keepalive) for p in peers_docs]
    server_lite = wireguard.ServerConfigLite(address=db_server.address, listen_port=db_server.listen_port, private_key=db_server.private_key, mtu=db_server.mtu, peers=peers_lite)
    conf_content = wireguard.render_server_config(server_lite)
    filename = f"{server_interface}.conf"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(conf_content)
    return FileResponse(filename, media_type="text/plain", filename=filename)
