"""Core session management for persistent authentication."""
from __future__ import annotations

import json
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("firewallo.auth.sessions")


class CoreSessionManager:
    """Core session manager for persistent authentication across restarts."""

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize core session manager."""
        self.session_dir = session_dir or Path("data/core/sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(days=7)  # Default 7 days
        self.remember_me_timeout = timedelta(days=30)  # 30 days for remember me
        self._load_sessions()

    def _load_sessions(self):
        """Load existing sessions from storage."""
        session_file = self.session_dir / "sessions.json"
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    # Filter out expired sessions on load
                    now = datetime.now().isoformat()
                    self.sessions = {
                        sid: session for sid, session in data.items()
                        if session.get('expires_at', '') > now
                    }
                logger.info(f"Loaded {len(self.sessions)} active sessions")
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.sessions = {}
        else:
            logger.info("No existing sessions file found, starting fresh")

    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            session_file = self.session_dir / "sessions.json"
            with open(session_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def create_session(
        self,
        username: str,
        user_data: Dict[str, Any],
        remember_me: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Create a new session for user."""
        session_id = secrets.token_urlsafe(32)

        # Set expiration based on remember me option
        if remember_me:
            expires_at = datetime.now() + self.remember_me_timeout
        else:
            expires_at = datetime.now() + self.session_timeout

        self.sessions[session_id] = {
            'username': username,
            'user_data': user_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'last_activity': datetime.now().isoformat(),
            'remember_me': remember_me,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }

        self._save_sessions()
        logger.info(f"Created session for user {username} (remember_me: {remember_me}, expires: {expires_at})")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if valid."""
        if not session_id:
            return None

        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check expiration
        if datetime.fromisoformat(session['expires_at']) < datetime.now():
            self.destroy_session(session_id)
            return None

        # Update last activity
        session['last_activity'] = datetime.now().isoformat()
        self._save_sessions()

        return session

    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        if session_id in self.sessions:
            username = self.sessions[session_id].get('username', 'unknown')
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Destroyed session for user {username}")
            return True
        return False

    def destroy_user_sessions(self, username: str, except_session_id: Optional[str] = None) -> int:
        """Destroy all sessions for a user except the specified one."""
        sessions_to_remove = []
        for session_id, session in self.sessions.items():
            if session.get('username') == username and session_id != except_session_id:
                sessions_to_remove.append(session_id)

        count = 0
        for session_id in sessions_to_remove:
            if self.destroy_session(session_id):
                count += 1

        if count > 0:
            logger.info(f"Destroyed {count} sessions for user {username}")

        return count

    def extend_session(self, session_id: str) -> bool:
        """Extend session expiration."""
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Extend by original timeout period
        if session.get('remember_me', False):
            new_expiry = datetime.now() + self.remember_me_timeout
        else:
            new_expiry = datetime.now() + self.session_timeout

        session['expires_at'] = new_expiry.isoformat()
        session['last_activity'] = datetime.now().isoformat()
        self._save_sessions()

        logger.debug(f"Extended session for user {session.get('username')} until {new_expiry}")
        return True

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        now = datetime.now().isoformat()
        expired = [
            sid for sid, session in self.sessions.items()
            if session.get('expires_at', '') < now
        ]

        count = 0
        for sid in expired:
            if self.destroy_session(sid):
                count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")

        return count

    def get_session_count(self) -> int:
        """Get current active session count."""
        return len(self.sessions)

    def get_user_sessions(self, username: str) -> list:
        """Get all sessions for a specific user."""
        user_sessions = []
        for session_id, session in self.sessions.items():
            if session.get('username') == username:
                user_sessions.append({
                    'session_id': session_id,
                    'created_at': session.get('created_at'),
                    'last_activity': session.get('last_activity'),
                    'expires_at': session.get('expires_at'),
                    'remember_me': session.get('remember_me', False),
                    'ip_address': session.get('ip_address'),
                    'user_agent': session.get('user_agent'),
                })
        return user_sessions

    def validate_session_security(
        self,
        session: Dict[str, Any],
        current_ip: Optional[str] = None,
        current_user_agent: Optional[str] = None
    ) -> bool:
        """Validate session security (IP, user agent, etc.)."""
        # For now, we'll be lenient with IP checking due to NAT/proxy scenarios
        # This can be made more strict in production if needed

        # Basic user agent validation
        if current_user_agent and session.get('user_agent'):
            session_ua = session.get('user_agent', '')
            if session_ua and current_user_agent:
                # Extract basic browser info for comparison
                # This is a simple check - can be enhanced
                try:
                    def extract_browser(ua):
                        ua_lower = ua.lower()
                        if 'chrome' in ua_lower:
                            return 'chrome'
                        elif 'firefox' in ua_lower:
                            return 'firefox'
                        elif 'safari' in ua_lower:
                            return 'safari'
                        elif 'edge' in ua_lower:
                            return 'edge'
                        return 'unknown'

                    session_browser = extract_browser(session_ua)
                    current_browser = extract_browser(current_user_agent)

                    if session_browser != current_browser and session_browser != 'unknown':
                        logger.warning(f"User agent mismatch: {session_browser} vs {current_browser}")
                        # For now, just log but don't block
                        # return False  # Uncomment for stricter security

                except Exception as e:
                    logger.error(f"Error validating user agent: {e}")

        return True


# Global session manager instance
_session_manager: Optional[CoreSessionManager] = None


def get_session_manager() -> CoreSessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = CoreSessionManager()
    return _session_manager


def cleanup_sessions_on_startup():
    """Cleanup expired sessions on application startup."""
    try:
        session_manager = get_session_manager()
        cleaned = session_manager.cleanup_expired_sessions()
        logger.info(f"Startup cleanup: removed {cleaned} expired sessions")
    except Exception as e:
        logger.error(f"Failed to cleanup sessions on startup: {e}")
