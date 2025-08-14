from __future__ import annotations
from typing import Optional
import ipaddress
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.wireguard_manager.repository import repo, PeerDoc
from app.auth.models import current_active_user
from app.wireguard_manager.repository import UserDoc
from app.services import wireguard
from app.services.validation import ValidationService

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(tags=["gui"])

@router.get("/modify_allowed_ips")
def get_modify_allowed_ips_form(request: Request, user: UserDoc = Depends(current_active_user)):
    return templates.TemplateResponse("modify_allowed_ips.html", {"request": request})

@router.post("/modify_allowed_ips")
def modify_allowed_ips(request: Request, username: str = Form(...), server_interface: str = Form(...), user: UserDoc = Depends(current_active_user)):
    peer = repo.get_peer(server_interface, username)
    if not peer:
        return templates.TemplateResponse("modify_allowed_ips.html", {"request": request, "error": "Peer not found", "username": username, "server_interface": server_interface})
    return templates.TemplateResponse("edit_allowed_ips.html", {"request": request, "peer": peer})

@router.post("/update_allowed_ips")
def update_allowed_ips(request: Request, username: str = Form(...), server_interface: str = Form(...), allowed_ips: str = Form(...), user: UserDoc = Depends(current_active_user)):
    peer = repo.get_peer(server_interface, username)
    if not peer:
        return templates.TemplateResponse("edit_allowed_ips.html", {"request": request, "error": "Peer not found", "peer": peer})
    
    if not ValidationService.validate_ip_address(allowed_ips):
        return templates.TemplateResponse("edit_allowed_ips.html", {"request": request, "error": "Invalid allowed IPs", "peer": peer})
    
    try:
        repo.update_peer(server_interface, username, allowed_ips=allowed_ips)
    except ValueError:
        return templates.TemplateResponse("edit_allowed_ips.html", {"request": request, "error": "Peer not found", "peer": peer})
    
    return RedirectResponse(url="/peers_list", status_code=303)

@router.get("/peers_list")
def list_peers(request: Request, user: UserDoc = Depends(current_active_user)):
    peers = repo.list_peers()
    return templates.TemplateResponse("peers_list.html", {"request": request, "peers": peers})

@router.get("/delete_peer")
def delete_peer_confirmation(username: str, server_interface: str, user: UserDoc = Depends(current_active_user)):
    try:
        repo.delete_peer(server_interface, username)
    except ValueError:
        pass
    return RedirectResponse(url="/peers_list", status_code=303)

@router.get("/add_peer")
def get_add_peer_form(request: Request, user: UserDoc = Depends(current_active_user)):
    servers = repo.list_servers()
    return templates.TemplateResponse("add_peer.html", {"request": request, "servers": servers})

@router.post("/add_peer")
def add_peer(request: Request, username: str = Form(...), server_interface: str = Form(...), allowed_ips: str = Form(...), endpoint: Optional[str] = Form(None), group: Optional[str] = Form(None), persistent_keepalive: Optional[int] = Form(None), user: UserDoc = Depends(current_active_user)):
    server_doc = repo.get_server(server_interface)
    if not server_doc:
        return templates.TemplateResponse("add_peer.html", {"request": request, "error": "Server not found", "servers": repo.list_servers()})
    existing_ips = [ipaddress.IPv4Address(p.private_ip.split('/')[0]) for p in repo.list_peers(server_interface)]
    network = ipaddress.IPv4Network(server_doc.address, strict=False)
    available_ip = None
    for ip in network.hosts():
        if ip not in existing_ips:
            available_ip = str(ip) + '/' + str(network.prefixlen)
            break
    if not available_ip:
        return templates.TemplateResponse("add_peer.html", {"request": request, "error": "No available IP addresses", "servers": repo.list_servers()})
    private_key = wireguard.generate_private_key()
    public_key = wireguard.generate_public_key(private_key)
    preshared_key = wireguard.generate_preshared_key()
    peer_doc = PeerDoc(server_interface=server_interface, username=username, private_ip=available_ip, private_key=private_key, public_key=public_key, allowed_ips=allowed_ips, endpoint=endpoint, group=group, persistent_keepalive=persistent_keepalive, preshared_key=preshared_key)
    try:
        repo.create_peer(peer_doc)
    except ValueError as e:
        return templates.TemplateResponse("add_peer.html", {"request": request, "error": str(e), "servers": repo.list_servers()})
    return RedirectResponse(url="/peers_list", status_code=303)

# SPA entry routes (React front-end). Multiple paths serve the same shell enabling deep links.
@router.get("/", include_in_schema=False)
@router.get("/login", include_in_schema=False)
# Legacy wireguard paths (backward compatibility)
@router.get("/peers", include_in_schema=False)
@router.get("/peers/{rest:path}", include_in_schema=False)
# New plugin namespace for WireGuard UI
@router.get("/plugins/wireguard", include_in_schema=False)
@router.get("/plugins/wireguard/{rest:path}", include_in_schema=False)
def spa_index(request: Request, rest: str | None = None):  # auth handled client side via JWT; API still enforces auth
    return templates.TemplateResponse("index.html", {"request": request})

@router.get('/favicon.ico', include_in_schema=False)
def favicon():
    """Serve favicon from static files."""
    return FileResponse('app/static/favicon.ico', media_type='image/x-icon')
