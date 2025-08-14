from __future__ import annotations
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

# Get the absolute path to the app directory
app_dir = Path(__file__).parent.parent.parent
templates_dir = app_dir / "templates"
static_dir = app_dir / "static"

# Initialize Jinja2 templates
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(tags=["gui"])

# Mock authentication check - replace with real auth logic
async def get_current_user(request: Request):
    """Mock authentication - replace with real implementation"""
    # For now, just check if there's a token in localStorage (handled client-side)
    # or session. In a real app, you'd validate JWT tokens here.
    return {"username": "admin", "email": "admin@firewallo.local"}

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Redirect root to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Serve the main dashboard"""
    # In a real app, you'd check authentication here
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Dashboard",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/plugins", response_class=HTMLResponse, include_in_schema=False)
async def plugins_page(request: Request):
    """Serve the plugins management page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Plugin Management",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("plugins.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/rules", response_class=HTMLResponse, include_in_schema=False)
async def rules_page(request: Request):
    """Serve the firewall rules page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Firewall Rules",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        # For now, use the dashboard template as placeholder
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_page(request: Request):
    """Serve the logs page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "System Logs",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        # For now, use the dashboard template as placeholder
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/firewall", response_class=HTMLResponse, include_in_schema=False)
async def firewall_status_page(request: Request):
    """Serve the firewall status page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Firewall Status",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/monitoring", response_class=HTMLResponse, include_in_schema=False)
async def monitoring_page(request: Request):
    """Serve the monitoring page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "System Monitoring",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/system", response_class=HTMLResponse, include_in_schema=False)
async def system_info_page(request: Request):
    """Serve the system information page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "System Information",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/backup", response_class=HTMLResponse, include_in_schema=False)
async def backup_page(request: Request):
    """Serve the backup page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Backup & Restore",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/updates", response_class=HTMLResponse, include_in_schema=False)
async def updates_page(request: Request):
    """Serve the updates page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "System Updates",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/profile", response_class=HTMLResponse, include_in_schema=False)
async def profile_page(request: Request):
    """Serve the user profile page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "User Profile",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    """Serve the settings page"""
    try:
        # user = await get_current_user(request)
        context = {
            "request": request,
            "page_title": "Settings",
            "user": {"username": "admin", "email": "admin@firewallo.local"}
        }
        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/logout", response_class=HTMLResponse, include_in_schema=False)
async def logout(request: Request):
    """Handle logout and redirect to login"""
    # In a real app, you'd clear the session/token here
    response = RedirectResponse(url="/login", status_code=302)
    # Clear any cookies if using cookie-based auth
    response.delete_cookie("access_token")
    return response

# Catch-all route for any unhandled paths - redirect to dashboard or login
@router.get("/{path:path}", response_class=HTMLResponse, include_in_schema=False)
async def catch_all(request: Request, path: str):
    """Handle all other routes - redirect to dashboard or login"""
    # List of paths that don't require authentication
    public_paths = ["/login", "/api"]

    if any(path.startswith(p.lstrip("/")) for p in public_paths):
        return RedirectResponse(url="/login", status_code=302)

    # For authenticated routes, redirect to dashboard
    return RedirectResponse(url="/dashboard", status_code=302)
