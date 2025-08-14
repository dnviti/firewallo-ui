# schemas.py
from pydantic import BaseModel
from typing import List, Optional

class PeerBase(BaseModel):
    username: str
    allowed_ips: str
    private_ip: str
    endpoint: Optional[str] = None
    group: str
    persistent_keepalive: Optional[int] = None

class PeerCreate(PeerBase):
    pass

class PeerUpdate(PeerBase):
    pass

class Peer(PeerBase):
    server_interface: str
    public_key: str
    preshared_key: Optional[str]
    class Config:
        from_attributes = True

class PeerCreateResponse(Peer):
    private_key: str
    class Config:
        from_attributes = True

class ServerBase(BaseModel):
    interface: str
    listen_port: int
    address: str  # e.g., "10.0.0.1/24"
    mtu: int

class ServerCreate(ServerBase):
    pass

class ServerUpdate(ServerBase):
    pass

class Server(ServerBase):
    public_key: str
    class Config:
        from_attributes = True

class ServerCreateResponse(Server):
    private_key: str
    class Config:
        from_attributes = True