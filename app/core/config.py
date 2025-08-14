from __future__ import annotations
import json, os
from json import JSONDecodeError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def build_cors_list() -> list[str]:
    raw = os.environ.get("CORS_LIST") or '["http://127.0.0.1","http://10.255.10.1","http://127.0.0.1:11811"]'
    try:
        return json.loads(raw)
    except JSONDecodeError:
        return ["*"]

def create_app() -> FastAPI:
    app = FastAPI(
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=build_cors_list(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
