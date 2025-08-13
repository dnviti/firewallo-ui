# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Server(Base):
    __tablename__ = "servers"

    interface = Column(String, primary_key=True)
    private_key = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    listen_port = Column(Integer, nullable=False)
    mtu = Column(Integer, nullable=False)
    address = Column(String, nullable=False)  # e.g., "10.0.0.1/24"

    peers = relationship("Peer", back_populates="server", cascade="all, delete-orphan")

class Peer(Base):
    __tablename__ = "peers"

    username = Column(String, primary_key=True)
    server_interface = Column(Integer, ForeignKey("servers.interface"))
    private_ip = Column(String, nullable=False)
    private_key = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
    allowed_ips = Column(String, nullable=False)
    endpoint = Column(String, nullable=False)
    preshared_key = Column(String, nullable=True)
    group = Column(String, nullable=True)
    persistent_keepalive = Column(Integer, nullable=True)

    server = relationship("Server", back_populates="peers")