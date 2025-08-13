from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import subprocess
import ipaddress
import os
import json

# Existing imports...
from wireguard_manager import models, schemas
from wireguard_manager.database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/template")

CORS_list = os.environ.get('CORS_LIST') or '["http://127.0.0.1","http://10.255.10.1","http://127.0.0.1:11811"]'
CORS_list = json.loads(CORS_list)

print(CORS_list)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_list,
 #   allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_private_key() -> str:
    private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    return private_key

def generate_public_key(private_key: str) -> str:
    public_key = subprocess.check_output(f"echo {private_key} | wg pubkey", shell=True).decode().strip()
    return public_key

def generate_preshared_key() -> str:
    preshared_key = subprocess.check_output("wg genpsk", shell=True).decode().strip()
    return preshared_key

# Endpoint to create a new server configuration
@app.post("/servers/", response_model=schemas.ServerCreateResponse)
def create_server(server: schemas.ServerCreate, db: Session = Depends(get_db)):
    db_server = db.query(models.Server).filter(models.Server.interface == server.interface).first()
    if db_server:
        raise HTTPException(status_code=400, detail="Server already exists")

    # Generate server private and public keys
    private_key = generate_private_key()
    public_key = generate_public_key(private_key)

    if not is_ip_valid(server.address):
        raise HTTPException(status_code=401, detail="This address is not an IP")

    new_server = models.Server(
        interface=server.interface,
        private_key=private_key,
        public_key=public_key,
        listen_port=server.listen_port,
        address=server.address,
        mtu = server.mtu
    )
    db.add(new_server)
    db.commit()
    db.refresh(new_server)

    # Return the server with the private key
    return schemas.ServerCreateResponse(
        interface=new_server.interface,
        private_key=new_server.private_key,
        public_key=new_server.public_key,
        listen_port=new_server.listen_port,
        address=new_server.address,
        mtu=new_server.mtu
    )

# Endpoint to update a server configuration
@app.put("/servers/{server_interface}", response_model=schemas.Server)
def update_server(server_interface: str, server: schemas.ServerUpdate, db: Session = Depends(get_db)):
    db_server = db.query(models.Server).filter(models.Server.interface == server_interface).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    db_server.interface = server.interface
    db_server.listen_port = server.listen_port
    db_server.address = server.address
    db.commit()
    db.refresh(db_server)
    return db_server

# Endpoint to delete a server configuration
@app.delete("/servers/{server_interface}")
def delete_server(server_interface: str, db: Session = Depends(get_db)):
    db_server = db.query(models.Server).filter(models.Server.interface == server_interface).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(db_server)
    db.commit()
    return {"detail": "Server deleted"}

# Endpoint to create a new peer for a server
@app.post("/servers/{server_interface}/peers/", response_model=schemas.PeerCreateResponse)
def create_peer_for_server(server_interface: str, peer: schemas.PeerCreate, db: Session = Depends(get_db)):
    db_server = db.query(models.Server).filter(models.Server.interface == server_interface).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Generate peer private and public keys
    private_key = generate_private_key()
    public_key = generate_public_key(private_key)
    preshared_key = generate_preshared_key()

    if not is_ip_valid(peer.allowed_ips):
        raise HTTPException(status_code=400, detail="IP error")

    if not is_ip_valid(peer.private_ip):
        raise HTTPException(status_code=400, detail="IP error")

    new_peer = models.Peer(
        server_interface=server_interface,
        username=peer.username,
        private_ip=peer.private_ip,
        private_key=private_key,
        public_key=public_key,
        allowed_ips=peer.allowed_ips,
        endpoint=peer.endpoint,
        group=peer.group,
        persistent_keepalive=peer.persistent_keepalive,
        preshared_key=preshared_key
    )
    db.add(new_peer)
    db.commit()
    db.refresh(new_peer)

    # Return the peer with the private key
    return schemas.PeerCreateResponse(
        username=new_peer.username,
        server_interface=new_peer.server_interface,
        private_ip=new_peer.private_ip,
        private_key=new_peer.private_key,
        public_key=new_peer.public_key,
        allowed_ips=new_peer.allowed_ips,
        endpoint=new_peer.endpoint,
        group=new_peer.group,
        persistent_keepalive=new_peer.persistent_keepalive,
        preshared_key=new_peer.preshared_key
    )

# Endpoint to update a peer for a server
@app.put("/servers/{server_interface}/peers/{peer_username}", response_model=schemas.Peer)
def update_peer(server_interface: str, peer_username: str, peer: schemas.PeerUpdate, db: Session = Depends(get_db)):
    db_peer = db.query(models.Peer).filter(models.Peer.username == peer_username, models.Peer.server_interface == server_interface).first()
    if not db_peer:
        raise HTTPException(status_code=404, detail="Peer not found")
    db_peer.allowed_ips = peer.allowed_ips
    db_peer.endpoint = peer.endpoint
    db_peer.persistent_keepalive = peer.persistent_keepalive
    db.commit()
    db.refresh(db_peer)
    return db_peer

# Endpoint to delete a peer from a server
@app.delete("/servers/{server_interface}/peers/{peer_username}")
def delete_peer(server_interface: str, peer_username: str, db: Session = Depends(get_db)):
    db_peer = db.query(models.Peer).filter(models.Peer.username == peer_username, models.Peer.server_interface == server_interface).first()
    if not db_peer:
        raise HTTPException(status_code=404, detail="Peer not found")
    db.delete(db_peer)
    db.commit()
    return {"detail": "Peer deleted"}

# Endpoint to persist the configuration to wgx.conf file
@app.post("/servers/{server_interface}/persist")
def persist_server_config(server_interface: str, db: Session = Depends(get_db)):
    db_server = db.query(models.Server).filter(models.Server.interface == server_interface).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Generate the configuration file content
    conf_content = generate_wg_config(db_server)


    #return conf_content
    #return JSONResponse(content={"detail": str(conf_content.replace('\\n',"\n"))})

    # Save file as interface is named
    filename = f"{server_interface}.conf"
    with open(filename, "w") as f:
        f.write(conf_content)

    return FileResponse(filename, media_type="text/plain", filename=f"{filename}")


def generate_wg_config(server: models.Server) -> str:
    # Start building the configuration content
    config_lines = []

    # Add Interface configuration
    config_lines.append("[Interface]")
    config_lines.append(f"Address = {server.address}")
    config_lines.append(f"ListenPort = {server.listen_port}")
    config_lines.append(f"PrivateKey = {server.private_key}")
    config_lines.append(f"MTU = {server.mtu}")

    # Add Peer configurations
    for peer in server.peers:
        config_lines.append("\n[Peer]")
        config_lines.append(f"PublicKey = {peer.public_key}")
        config_lines.append(f"AllowedIPs = {peer.private_ip}")
        config_lines.append(f"PresharedKey = {peer.preshared_key}")

        if peer.persistent_keepalive is not None:
            config_lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

    return '\n'.join(config_lines)


@app.post("/peers/{peer_username}/persist")
def persist_server_config(peer_username: str, custom_allowed_ips: Optional[str] = None, db: Session = Depends(get_db)):
    wg_peer = db.query(models.Peer).filter(models.Peer.username == peer_username).first()
    if not wg_peer:
        raise HTTPException(status_code=404, detail="Server not found")

    if custom_allowed_ips:
        wg_peer.allowed_ips = custom_allowed_ips

    # Generate the configuration file content
    conf_content = generate_wg_peer_config(wg_peer)

    # Save file as interface is named
    filename = f"{peer_username}.conf"
    with open(filename, "w") as f:
        f.write(conf_content)

    return FileResponse(filename, media_type="text/plain", filename=f"{filename}")

    return {"detail": f"Configuration persisted to {filename}"}

def generate_wg_peer_config(peer: models.Peer) -> str:
    # Start building the configuration content
    config_lines = []

    # Add Interface configuration
    config_lines.append("[Interface]")
    config_lines.append(f"Address = {peer.private_ip}")
    config_lines.append(f"PrivateKey = {peer.private_key}")
    config_lines.append(f"MTU = {peer.server.mtu}") # TODO ADD MTU

    config_lines.append("\n[Peer]")
    config_lines.append(f"PublicKey = {peer.server.public_key}")
    config_lines.append(f"Endpoint = {peer.endpoint}")
    config_lines.append(f"AllowedIPs = {peer.allowed_ips}")
    config_lines.append(f"PresharedKey = {peer.preshared_key}")

    if peer.persistent_keepalive is not None:
        config_lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

    return '\n'.join(config_lines)


def is_ip_valid(ip_str: str) -> bool:
    try:
        ip_str = ip_str.replace(" ","")
        for ip in ip_str.split(","):
            if "/" in ip:
                if int(ip.split("/")[1]) > 32 or int(ip.split("/")[1]) < 1: #check netmask
                    return False
                ip = ip.split("/")[0]
            ipaddress.ip_address(ip)
    except Exception as ex:
        print(ex)
        return False    

    return True

@app.get("/peers", response_model=List[schemas.Peer])
def get_peers(server_interface: Optional[str] = None, db: Session = Depends(get_db)):
    if server_interface:
        peers = db.query(models.Peer).filter(models.Peer.server_interface == server_interface).all()
    else:
        peers = db.query(models.Peer).all()
    return peers

############ EXTRA

@app.put("/peers/{username}/allowed_ips", response_model=schemas.Peer)
def update_peer_allowed_ips(username: str, allowed_ips: str, db: Session = Depends(get_db)):
    # Cerca il peer nel database
    peer = db.query(models.Peer).filter(models.Peer.username == username).first()
    if not peer:
        raise HTTPException(status_code=404, detail="Peer not found")

    # Aggiorna il campo allowed_ips
    if not is_ip_valid(allowed_ips):
        raise HTTPException(status_code=400, detail="IP error") 
    peer.allowed_ips = allowed_ips
    db.commit()
    db.refresh(peer)

    return peer

@app.get("/next_ip")
def next_ips(server_interface: Optional[str] = None, db: Session = Depends(get_db)):
    if server_interface:
        ips = db.query(models.Peer.private_ip).filter(models.Peer.server_interface == server_interface).all()
    else:
        ips = db.query(models.Peer.private_ip).all()
    
    ip_list = []
    for ip in ips:
        ip_list.append(str(ip[0]).split("/")[0])

    ordered_ips = sorted(ip_list, key=lambda ip: ipaddress.ip_address(ip))
    ip_max = ipaddress.ip_address(ordered_ips[-1])
    next_ip = ip_max + 1
    while str(next_ip).endswith('.0') or str(next_ip).endswith('.1') or str(next_ip).endswith('.255'):
        next_ip += 1

    print(next_ip)
    return str(next_ip)


######################### GUI ############################

###### modify allowed
# Display form to enter username and server interface
@app.get("/modify_allowed_ips")
def get_modify_allowed_ips_form(request: Request):
    return templates.TemplateResponse("modify_allowed_ips.html", {"request": request})

# Process form and display current allowed IPs for editing
@app.post("/modify_allowed_ips")
def modify_allowed_ips(request: Request, username: str = Form(...), server_interface: str = Form(...)):
    with SessionLocal() as db:
        peer = db.query(models.Peer).filter(models.Peer.username == username,
                                            models.Peer.server_interface == server_interface).first()
        if not peer:
            return templates.TemplateResponse("modify_allowed_ips.html", {
                "request": request,
                "error": "Peer not found",
                "username": username,
                "server_interface": server_interface
            })
        return templates.TemplateResponse("edit_allowed_ips.html", {
            "request": request,
            "peer": peer
        })

# Update allowed IPs # TO BE UPDATED WITH /peers/{username}/allowed_ips
@app.post("/update_allowed_ips")
def update_allowed_ips(request: Request, username: str = Form(...), server_interface: str = Form(...), allowed_ips: str = Form(...)):
    with SessionLocal() as db:
        peer = db.query(models.Peer).filter(models.Peer.username == username,
                                            models.Peer.server_interface == server_interface).first()
        if not peer:
            return templates.TemplateResponse("edit_allowed_ips.html", {
                "request": request,
                "error": "Peer not found",
                "peer": peer
            })
        if not is_ip_valid(allowed_ips):
            return templates.TemplateResponse("edit_allowed_ips.html", {
                "request": request,
                "error": "Invalid allowed IPs",
                "peer": peer
            })
        peer.allowed_ips = allowed_ips
        db.commit()
        return RedirectResponse(url="/peers_list", status_code=303)

##### list peers
@app.get("/peers_list")
def list_peers(request: Request):
    with SessionLocal() as db:
        peers = db.query(models.Peer).all()
    return templates.TemplateResponse("peers_list.html", {"request": request, "peers": peers})


##### Delete peer
@app.get("/delete_peer")
def delete_peer_confirmation(request: Request, username: str, server_interface: str):
    with SessionLocal() as db:
        peer = db.query(models.Peer).filter(models.Peer.username == username, models.Peer.server_interface == server_interface).first()
        if not peer:
            return RedirectResponse(url="/peers_list", status_code=303)
        db.delete(peer)
        db.commit()
    return RedirectResponse(url="/peers_list", status_code=303)


##### add peer
# Display form to add new peer
@app.get("/add_peer")
def get_add_peer_form(request: Request):
    with SessionLocal() as db:
        servers = db.query(models.Server).all()
    return templates.TemplateResponse("add_peer.html", {"request": request, "servers": servers})

# Process form to add new peer
@app.post("/add_peer")
def add_peer(request: Request,
             username: str = Form(...),
             server_interface: str = Form(...),
             allowed_ips: str = Form(...),
             endpoint: Optional[str] = Form(None),
             group: Optional[str] = Form(None),
             persistent_keepalive: Optional[int] = Form(None)):
    with SessionLocal() as db:
        db_server = db.query(models.Server).filter(models.Server.interface == server_interface).first()
        if not db_server:
            return templates.TemplateResponse("add_peer.html", {
                "request": request,
                "error": "Server not found",
                "servers": db.query(models.Server).all()
            })
        # Suggest next available private IP
        existing_ips = [ipaddress.IPv4Address(peer.private_ip.split('/')[0]) for peer in db_server.peers]
        network = ipaddress.IPv4Network(db_server.address, strict=False)
        available_ip = None
        for ip in network.hosts():
            if ip not in existing_ips:
                available_ip = str(ip) + '/' + str(network.prefixlen)
                break
        if not available_ip:
            return templates.TemplateResponse("add_peer.html", {
                "request": request,
                "error": "No available IP addresses",
                "servers": db.query(models.Server).all()
            })
        # Create new peer
        private_key = generate_private_key()
        public_key = generate_public_key(private_key)
        preshared_key = generate_preshared_key()
        new_peer = models.Peer(
            server_interface=server_interface,
            username=username,
            private_ip=available_ip,
            private_key=private_key,
            public_key=public_key,
            allowed_ips=allowed_ips,
            endpoint=endpoint,
            group=group,
            persistent_keepalive=persistent_keepalive,
            preshared_key=preshared_key
        )
        db.add(new_peer)
        db.commit()
        return RedirectResponse(url="/peers_list", status_code=303)