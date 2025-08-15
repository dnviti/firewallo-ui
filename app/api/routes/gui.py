from __future__ import annotations
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.auth.models import current_active_user, User
from app.auth.sessions import get_session_manager

# Get the absolute path to the app directory
app_dir = Path(__file__).parent.parent.parent
templates_dir = app_dir / "templates"

# Ensure templates directory exists
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(tags=["gui"])

# Authentication check using persistent sessions
async def get_current_web_user(request: Request) -> User:
    """Get current authenticated user for web interface."""
    try:
        from app.auth.models import get_current_user
        user_data = await get_current_user(request)
        return User(user_data)
    except HTTPException:
        # Not authenticated, redirect to login
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Redirecting to login",
            headers={"Location": "/login"}
        )

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Redirect root to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the main dashboard"""
    try:
        context = {
            "request": request,
            "page_title": "Dashboard",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/plugins", response_class=HTMLResponse, include_in_schema=False)
async def plugins_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the plugins management page"""
    try:
        context = {
            "request": request,
            "page_title": "Plugin Management",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("plugins.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/rules", response_class=HTMLResponse, include_in_schema=False)
async def rules_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the firewall rules page"""
    try:
        context = {
            "request": request,
            "page_title": "Firewall Rules",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        # For now, use the dashboard template as placeholder
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
async def logs_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the logs page"""
    try:
        context = {
            "request": request,
            "page_title": "System Logs",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        # For now, use the dashboard template as placeholder
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/firewall", response_class=HTMLResponse, include_in_schema=False)
async def firewall_status_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the firewall status page"""
    try:
        context = {
            "request": request,
            "page_title": "Firewall Status",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/monitoring", response_class=HTMLResponse, include_in_schema=False)
async def monitoring_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the monitoring page"""
    try:
        context = {
            "request": request,
            "page_title": "System Monitoring",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/system", response_class=HTMLResponse, include_in_schema=False)
async def system_info_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the system information page"""
    try:
        context = {
            "request": request,
            "page_title": "System Information",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/backup", response_class=HTMLResponse, include_in_schema=False)
async def backup_page(request: Request, current_user: User = Depends(get_current_web_user)):
    """Serve the backup page"""
    try:
        context = {
            "request": request,
            "page_title": "Backup & Restore",
            "user": {
                "username": current_user.username,
                "email": current_user.email,
                "is_superuser": current_user.is_superuser
            }
        }
        return templates.TemplateResponse("dashboard.html", context)
    except HTTPException as e:
        if e.status_code == status.HTTP_302_FOUND:
            return RedirectResponse(url="/login", status_code=302)
        raise
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

@router.get("/logout", include_in_schema=False)
async def logout(request: Request, response: Response):
    """Handle logout and destroy session"""
    from app.auth.sessions import get_session_manager
    session_manager = get_session_manager()

    # Get session ID from cookie and destroy it
    session_id = request.cookies.get("session_id")
    if session_id:
        session_manager.destroy_session(session_id)

    # Create redirect response and clear cookies
    redirect_response = RedirectResponse(url="/login", status_code=302)
    redirect_response.delete_cookie("session_id")
    redirect_response.delete_cookie("access_token")

    return redirect_response

# Specific routes for common paths to avoid interfering with plugin routes
@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_redirect(request: Request):
    """Redirect settings to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/users", response_class=HTMLResponse, include_in_schema=False)
async def users_redirect(request: Request):
    """Redirect users to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/network", response_class=HTMLResponse, include_in_schema=False)
async def network_redirect(request: Request):
    """Redirect network to dashboard"""
    return RedirectResponse(url="/dashboard", status_code=302)

# Note: Plugin routes at /plugins/* are handled by plugin routers registered during startup
# No catch-all route to avoid conflicts with plugin paths
