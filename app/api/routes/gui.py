from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["api-only"])

@router.get("/", include_in_schema=False)
def root_redirect():
    """Redirect root to API documentation since there's no frontend."""
    return RedirectResponse(url="/docs")

@router.get("/login", include_in_schema=False)  
def login_redirect():
    """Redirect login to API documentation since there's no frontend."""
    return RedirectResponse(url="/docs")

# All other routes redirect to API docs
@router.get("/{path:path}", include_in_schema=False)
def catch_all_redirect(path: str):
    """Redirect all other paths to API documentation."""
    return RedirectResponse(url="/docs")
