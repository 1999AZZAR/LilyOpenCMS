"""
Advanced Session Security Management for LilyOpenCMS

This module provides robust session security features including:
- Session invalidation on security events
- Concurrent session management
- Session activity monitoring
- Session rate limiting
- Session blacklisting
- Device tracking
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from flask import request, current_app, session
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
import uuid
import hashlib
import json
import base64
import secrets
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from functools import wraps
from models import db, UserSession, UserActivity

logger = logging.getLogger(__name__)

class SessionSecurityManager:
    """Manages advanced session security features."""

    def __init__(self, app):
        self.app = app
        self._init_session_store()
        self._init_encryption()

    def _init_session_store(self):
        """Initialize session store for tracking user sessions."""
        try:
            if not hasattr(current_app, 'session_store'):
                current_app.session_store = {}
        except RuntimeError:
            # Working outside of application context (during migration)
            # Create a minimal session store
            if not hasattr(self, '_session_store'):
                self._session_store = {}

    def _init_encryption(self):
        """Initialize encryption for sensitive session data."""
        # Generate or retrieve encryption key
        encryption_key = os.getenv('SESSION_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate a secure key if not exists
            encryption_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            # Store in environment for persistence
            os.environ['SESSION_ENCRYPTION_KEY'] = encryption_key
            logger.warning("Generated new session encryption key. Store SESSION_ENCRYPTION_KEY in environment variables for persistence.")

        # Create KDF for additional security
        salt = b'static_salt_for_session_encryption'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Derive key using KDF
        derived_key = base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))
        self.fernet = Fernet(derived_key)

    def encrypt_session_data(self, data):
        """Encrypt sensitive session data."""
        try:
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()
            else:
                data = str(data).encode()

            encrypted_data = self.fernet.encrypt(data)
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt session data: {e}")
            return None

    def decrypt_session_data(self, encrypted_data):
        """Decrypt sensitive session data."""
        try:
            if not encrypted_data:
                return None

            # Handle base64 encoded data
            if isinstance(encrypted_data, str):
                encrypted_data = base64.b64decode(encrypted_data)
            elif isinstance(encrypted_data, bytes):
                encrypted_data = base64.b64decode(encrypted_data)

            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except (InvalidToken, json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to decrypt session data: {e}")
            return None

    def _init_session_store(self):
        """Initialize session store for tracking user sessions."""
        try:
            if not hasattr(current_app, 'session_store'):
                current_app.session_store = {}
        except RuntimeError:
            # Working outside of application context (during migration)
            # Create a minimal session store
            if not hasattr(self, '_session_store'):
                self._session_store = {}

    def generate_device_fingerprint(self):
        """Generate a fingerprint for the current device/browser."""
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr or 'unknown'
        accept_language = request.headers.get('Accept-Language', '')

        # Create a hash of user agent, IP, and accept language
        fingerprint_data = f"{user_agent}|{ip_address}|{accept_language}"
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()

        return fingerprint_hash

    def create_user_session(self, user):
        """Create a new user session with enhanced tracking."""
        try:
            # Generate unique session ID
            session_id = str(uuid.uuid4())

            # Get device fingerprint
            device_fingerprint = self.generate_device_fingerprint()

            # Get user agent and IP
            user_agent = request.headers.get('User-Agent', '')
            ip_address = request.remote_addr or 'unknown'

            # Create session record
            user_session = UserSession(
                session_id=session_id,
                user_id=user.id,
                device_fingerprint=device_fingerprint,
                user_agent=user_agent,
                ip_address=ip_address,
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_active=True
            )

            db.session.add(user_session)
            db.session.commit()

            # Store session info in Flask session
            session['session_id'] = session_id
            session['device_fingerprint'] = device_fingerprint
            session['user_id'] = user.id

            logger.info(f"Created new session {session_id} for user {user.username}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            db.session.rollback()
            raise

    def invalidate_user_sessions(self, user_id, reason="Security event"):
        """Invalidate all sessions for a specific user."""
        try:
            # Invalidate database sessions
            sessions = UserSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            for user_session in sessions:
                user_session.is_active = False
                user_session.invalidated_at = datetime.now(timezone.utc)
                user_session.invalidation_reason = reason

                # Record session invalidation activity
                try:
                    self.record_user_activity(
                        user_id,
                        "session_invalidated",
                        f"Session {user_session.session_id} invalidated: {reason}",
                        user_session.ip_address,
                        user_session.user_agent
                    )
                except Exception as e:
                    logger.warning(f"Could not record session invalidation activity: {e}")

            db.session.commit()
            logger.info(f"Invalidated {len(sessions)} sessions for user {user_id}")

            return len(sessions)

        except Exception as e:
            logger.error(f"Failed to invalidate sessions for user {user_id}: {e}")
            db.session.rollback()
            raise

    def validate_session(self):
        """Validate current session security."""
        if not current_user.is_authenticated:
            return False

        try:
            session_id = session.get('session_id')
            if not session_id:
                return False

            # Check if session is blacklisted
            if self.is_session_blacklisted(session_id):
                logger.warning(f"Blacklisted session {session_id} attempted access for user {current_user.id}")
                return False

            # Check if session exists in database and is active
            user_session = UserSession.query.filter_by(
                session_id=session_id,
                user_id=current_user.id,
                is_active=True
            ).first()

            if not user_session:
                logger.warning(f"Session {session_id} not found or inactive for user {current_user.id}")
                return False

            # Check session age
            session_age = datetime.now(timezone.utc) - user_session.created_at
            max_session_age = timedelta(hours=current_app.config.get('PERMANENT_SESSION_LIFETIME', 7200) / 3600)

            if session_age > max_session_age:
                logger.warning(f"Session {session_id} expired due to age for user {current_user.id}")
                self.invalidate_session(session_id, "Session expired")
                return False

            # Check inactivity timeout
            inactivity_timeout = current_app.config.get('SESSION_INACTIVE_TIMEOUT', 1800)
            last_activity_age = datetime.now(timezone.utc) - user_session.last_activity

            if last_activity_age > timedelta(seconds=inactivity_timeout):
                logger.warning(f"Session {session_id} expired due to inactivity for user {current_user.id}")
                self.invalidate_session(session_id, "Inactivity timeout")
                return False

            # Detect suspicious activity
            is_suspicious, reason = self.detect_suspicious_activity(current_user.id)
            if is_suspicious:
                logger.warning(f"Suspicious activity detected for user {current_user.id}: {reason}")
                self.blacklist_session(session_id, f"Suspicious activity: {reason}")
                return False

            # Check rate limits for sensitive operations
            if self.check_rate_limit(current_user.id, "sensitive_operations", 50, 3600):
                logger.warning(f"Rate limit exceeded for user {current_user.id}")
                # Don't immediately invalidate, just log for now
                pass

            # Update last activity
            user_session.last_activity = datetime.now(timezone.utc)
            db.session.commit()

            return True

        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False

    def invalidate_session(self, session_id, reason="Manual invalidation"):
        """Invalidate a specific session."""
        try:
            user_session = UserSession.query.filter_by(session_id=session_id).first()

            if user_session:
                user_session.is_active = False
                user_session.invalidated_at = datetime.now(timezone.utc)
                user_session.invalidation_reason = reason
                db.session.commit()

                # Record activity
                try:
                    self.record_user_activity(
                        user_session.user_id,
                        "session_invalidated",
                        f"Session {session_id} invalidated: {reason}",
                        user_session.ip_address,
                        user_session.user_agent
                    )
                except Exception as e:
                    logger.warning(f"Could not record session invalidation activity: {e}")

                logger.info(f"Invalidated session {session_id}")
            else:
                logger.warning(f"Session {session_id} not found for invalidation")

        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            db.session.rollback()

    def enforce_concurrent_session_limit(self, user_id):
        """Enforce maximum concurrent sessions per user."""
        try:
            max_sessions = current_app.config.get('MAX_CONCURRENT_SESSIONS', 5)

            # Get active sessions count
            active_sessions_count = UserSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).count()

            if active_sessions_count >= max_sessions:
                # Get oldest session to invalidate
                oldest_session = UserSession.query.filter_by(
                    user_id=user_id,
                    is_active=True
                ).order_by(UserSession.created_at).first()

                if oldest_session:
                    self.invalidate_session(
                        oldest_session.session_id,
                        "Concurrent session limit exceeded"
                    )
                    logger.info(f"Invalidated oldest session for user {user_id} to enforce limit")

        except Exception as e:
            logger.error(f"Failed to enforce concurrent session limit for user {user_id}: {e}")

    def record_user_activity(self, user_id, activity_type, description=None,
                           ip_address=None, user_agent=None):
        """Record user activity for audit trail."""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                description=description,
                ip_address=ip_address or (request.remote_addr if request else 'unknown'),
                user_agent=user_agent or (request.headers.get('User-Agent') if request else 'unknown'),
                created_at=datetime.now(timezone.utc)
            )

            db.session.add(activity)
            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to record user activity: {e}")
            db.session.rollback()

    def get_user_sessions(self, user_id):
        """Get all sessions for a user."""
        try:
            sessions = UserSession.query.filter_by(user_id=user_id)\
                .order_by(UserSession.created_at.desc())\
                .all()

            return sessions

        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []

    def cleanup_expired_sessions(self):
        """Clean up expired sessions from database."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

            expired_sessions = UserSession.query.filter(
                UserSession.created_at < cutoff_time,
                UserSession.is_active == True
            ).all()

            for user_session in expired_sessions:
                user_session.is_active = False
                user_session.invalidated_at = datetime.now(timezone.utc)
                user_session.invalidation_reason = "Expired during cleanup"

            db.session.commit()

            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            db.session.rollback()
            return 0

    def rotate_session(self):
        """Rotate the current session ID for security."""
        try:
            old_session_id = session.get('session_id')
            if old_session_id:
                # Invalidate old session
                self.invalidate_session(old_session_id, "Session rotation")

            # Create new session
            new_session_id = self.create_user_session(current_user)

            logger.info(f"Rotated session from {old_session_id} to {new_session_id} for user {current_user.id}")
            return new_session_id

        except Exception as e:
            logger.error(f"Failed to rotate session: {e}")
            raise

    def check_rate_limit(self, user_id, action="general", limit=100, window_seconds=3600):
        """Check if user has exceeded rate limit for a specific action."""
        try:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)

            # Count activities in the time window
            activity_count = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type=action
            ).filter(
                UserActivity.created_at >= window_start
            ).count()

            return activity_count >= limit

        except Exception as e:
            logger.error(f"Failed to check rate limit for user {user_id}: {e}")
            return False

    def detect_suspicious_activity(self, user_id):
        """Detect suspicious activity patterns."""
        try:
            now = datetime.now(timezone.utc)
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(days=1)

            # Check for rapid login attempts (more than 5 failed logins in 1 hour)
            failed_logins = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type="login_failed"
            ).filter(
                UserActivity.created_at >= one_hour_ago
            ).count()

            if failed_logins >= 5:
                return True, f"Multiple failed login attempts ({failed_logins} in 1 hour)"

            # Check for login from multiple countries/IPs in short time
            recent_logins = UserActivity.query.filter_by(
                user_id=user_id,
                activity_type="login"
            ).filter(
                UserActivity.created_at >= one_day_ago
            ).all()

            # Get unique IP addresses
            ip_addresses = set()
            for login in recent_logins:
                if login.ip_address:
                    ip_addresses.add(login.ip_address)

            if len(ip_addresses) > 10:  # More than 10 different IPs in a day
                return True, f"Login from {len(ip_addresses)} different IP addresses in 24 hours"

            # Check for unusual login times (if we have historical data)
            if len(recent_logins) > 20:
                # Get the most recent successful login
                last_login = UserActivity.query.filter_by(
                    user_id=user_id,
                    activity_type="login"
                ).order_by(UserActivity.created_at.desc()).first()

                if last_login:
                    # If last login was more than 30 days ago, this could be suspicious
                    thirty_days_ago = now - timedelta(days=30)
                    if last_login.created_at < thirty_days_ago:
                        return True, "Account accessed after long period of inactivity"

            return False, None

        except Exception as e:
            logger.error(f"Failed to detect suspicious activity for user {user_id}: {e}")
            return False, str(e)

    def blacklist_session(self, session_id, reason="Suspicious activity"):
        """Blacklist a session to prevent further use."""
        try:
            # Invalidate the session
            self.invalidate_session(session_id, reason)

            # Store in a blacklist (could be Redis or database table)
            blacklist_key = f"session_blacklist:{session_id}"
            blacklist_data = {
                'session_id': session_id,
                'reason': reason,
                'blacklisted_at': datetime.now(timezone.utc).isoformat(),
                'user_agent': request.headers.get('User-Agent') if request else 'unknown'
            }

            # Store in application cache for quick lookup
            try:
                current_app.session_store[blacklist_key] = blacklist_data
            except RuntimeError:
                # Working outside of application context
                if not hasattr(self, '_session_store'):
                    self._session_store = {}
                self._session_store[blacklist_key] = blacklist_data

            logger.info(f"Blacklisted session {session_id} for reason: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to blacklist session {session_id}: {e}")
            return False

    def is_session_blacklisted(self, session_id):
        """Check if a session is blacklisted."""
        blacklist_key = f"session_blacklist:{session_id}"
        try:
            return blacklist_key in current_app.session_store
        except RuntimeError:
            # Working outside of application context
            return blacklist_key in getattr(self, '_session_store', {})


# Global session security manager instance
session_security_manager = None

def init_session_security(app):
    """Initialize the session security manager."""
    global session_security_manager

    # Check if we're in an application context
    try:
        from flask import has_app_context
        if has_app_context():
            session_security_manager = SessionSecurityManager(app)
        else:
            # If no app context, create a minimal instance for migration
            session_security_manager = SessionSecurityManager(app)
    except ImportError:
        # Flask version doesn't have has_app_context
        try:
            from flask import _app_ctx_stack
            if _app_ctx_stack.top is not None:
                session_security_manager = SessionSecurityManager(app)
            else:
                # Create minimal instance for migration purposes
                session_security_manager = SessionSecurityManager(app)
        except:
            # Fallback for migration context
            session_security_manager = SessionSecurityManager(app)

    # Register cleanup task only if we have a proper app context
    try:
        @app.before_first_request
        def setup_session_cleanup():
            # Clean up expired sessions on startup
            if session_security_manager:
                session_security_manager.cleanup_expired_sessions()
    except Exception as e:
        # Ignore if we're not in a proper Flask context (during migration)
        pass


def init_session_security_for_migration(app):
    """Initialize session security manager specifically for migration context."""
    global session_security_manager

    # Create a minimal instance that won't trigger Flask context errors
    try:
        session_security_manager = SessionSecurityManager(app)
        logger.info("✅ Session security manager initialized for migration")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize session security manager for migration: {e}")
        # Create a minimal stub if full initialization fails
        class MigrationStub:
            def cleanup_expired_sessions(self):
                logger.info("⏭️ Session cleanup skipped during migration")
        session_security_manager = MigrationStub()

def get_session_security_manager():
    """Get the global session security manager instance."""
    return session_security_manager

# Security decorators
def require_session_validation(f):
    """Decorator to require session validation before executing function."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session_security_manager.validate_session():
            from flask import jsonify, redirect, url_for
            from flask_login import logout_user

            # Logout user and clear session
            logout_user()
            session.clear()

            # Return appropriate response
            if request.path.startswith('/api/') or request.accept_mimetypes.accept_json:
                return jsonify({
                    "error": "Session invalid or expired",
                    "message": "Please log in again",
                    "code": "SESSION_INVALID",
                    "status": 401
                }), 401
            else:
                from flask import flash
                flash('Your session has expired. Please log in again.', 'error')
                return redirect(url_for('main.login'))

        return f(*args, **kwargs)
    return decorated_function
