from routes import main_blueprint
from .common_imports import *
from flask import g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import wraps
from .routes_auth import _find_user_by_username_or_email
from models import UserLibrary, Comment, CommentLike, CommentReport, User, Rating


# Token configuration - Refined for better security and UX
ACCESS_TOKEN_SALT = "external-access-token"
REFRESH_TOKEN_SALT = "external-refresh-token"
ACCESS_TOKEN_TTL_SECONDS = 60 * 30  # 30 minutes - shorter for security
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days - reasonable refresh period

# Token refresh configuration
TOKEN_REFRESH_THRESHOLD_SECONDS = 60 * 5  # Refresh if token expires within 5 minutes
SLIDING_REFRESH_WINDOW_SECONDS = 60 * 60 * 24 * 30  # 30 days sliding window for refresh


def _safe_log(level: str, message: str, *args):
    """Safely log a message without causing exceptions."""
    try:
        logger = getattr(current_app.logger, level, None)
        if logger:
            logger(message.format(*args) if args else message)
    except:
        pass

def _get_serializer(salt: str) -> URLSafeTimedSerializer:
    """Get JWT serializer with fallback for missing app context."""
    try:
        secret_key = current_app.config.get("SECRET_KEY", "change-me")
        return URLSafeTimedSerializer(secret_key or "change-me", salt=salt)
    except:
        return URLSafeTimedSerializer("change-me", salt=salt)

def _validate_jwt_token(token: str) -> tuple:
    """Validate JWT token and return (user, token_data) or (None, None)."""
    try:
        # Validate token format
        parts = token.split('.')
        if len(parts) != 3:
            _safe_log("warning", "Invalid JWT token format: {} parts instead of 3", len(parts))
            return None, None

        # Decode and validate token
        data = _get_serializer(ACCESS_TOKEN_SALT).loads(token, max_age=ACCESS_TOKEN_TTL_SECONDS)

        # Get user from database
        try:
            user = User.query.get(data.get("user_id"))
        except Exception as db_error:
            _safe_log("warning", "Database query failed: {}", db_error)
            return None, None

        return user, data
    except Exception as token_error:
        _safe_log("warning", "JWT token validation failed: {}", token_error)
        return None, None


def _issue_tokens(user) -> dict:
    access = _get_serializer(ACCESS_TOKEN_SALT).dumps({
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value if user.role else None,
        "is_premium": user.is_premium,
    })
    refresh = _get_serializer(REFRESH_TOKEN_SALT).dumps({
        "user_id": user.id,
        "username": user.username,
    })
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
        "user": user.to_safe_dict() if hasattr(user, "to_safe_dict") else user.to_dict_safe() if hasattr(user, "to_dict_safe") else {
            "id": user.id,
            "username": user.username,
            "role": user.role.value if user.role else None,
            "is_premium": user.is_premium,
            "verified": user.verified,
        },
    }


def auth_required(f):
    """Combined authentication decorator that accepts both session and JWT tokens."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # First try JWT authentication
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            if token:
                try:
                    # Load token with max age
                    data = _get_serializer(ACCESS_TOKEN_SALT).loads(token, max_age=ACCESS_TOKEN_TTL_SECONDS)
                    user = User.query.get(data.get("user_id"))
                    if user:
                        if not user.is_active:
                            return jsonify({
                                "error": "Account inactive",
                                "message": "Your account is pending approval or has been deactivated",
                                "code": "AUTH_ACCOUNT_INACTIVE"
                            }), 403

                        if user.is_suspended:
                            return jsonify({
                                "error": "Account suspended",
                                "message": "Your account has been suspended. Please contact support.",
                                "code": "AUTH_ACCOUNT_SUSPENDED"
                            }), 403

                        g.api_user = user
                        g.token_data = data
                        return f(*args, **kwargs)
                except Exception as e:
                    current_app.logger.warning(f"JWT authentication failed: {e}")

        # Fall back to session authentication (Flask-Login)
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        # No valid authentication found
        return jsonify({
            "error": "Authentication required",
            "message": "Please provide valid authentication (JWT token or session)",
            "code": "AUTH_REQUIRED"
        }), 401

    return decorated


def token_required(f):
    """JWT-only authentication decorator (for backward compatibility)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Authorization header missing or invalid",
                "message": "Please provide a valid Bearer token in the Authorization header",
                "code": "AUTH_MISSING_TOKEN"
            }), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({
                "error": "Token missing in Authorization header",
                "message": "Please provide a valid Bearer token",
                "code": "AUTH_EMPTY_TOKEN"
            }), 401

        try:
            # Load token with max age
            data = _get_serializer(ACCESS_TOKEN_SALT).loads(token, max_age=ACCESS_TOKEN_TTL_SECONDS)
            user = User.query.get(data.get("user_id"))
            if not user:
                return jsonify({
                    "error": "User not found",
                    "message": "The user associated with this token no longer exists",
                    "code": "AUTH_USER_NOT_FOUND"
                }), 401

            if not user.is_active:
                return jsonify({
                    "error": "Account inactive",
                    "message": "Your account is pending approval or has been deactivated",
                    "code": "AUTH_ACCOUNT_INACTIVE"
                }), 403

            if user.is_suspended:
                return jsonify({
                    "error": "Account suspended",
                    "message": "Your account has been suspended. Please contact support.",
                    "code": "AUTH_ACCOUNT_SUSPENDED"
                }), 403

            g.api_user = user
            g.token_data = data

        except SignatureExpired:
            return jsonify({
                "error": "Token expired",
                "message": "Your access token has expired. Please refresh your token or login again.",
                "code": "AUTH_TOKEN_EXPIRED",
                "expires_in": ACCESS_TOKEN_TTL_SECONDS
            }), 401
        except BadSignature:
            return jsonify({
                "error": "Invalid token",
                "message": "The provided token is malformed or invalid",
                "code": "AUTH_TOKEN_INVALID"
            }), 401
        except Exception as e:
            current_app.logger.error(f"Token validation error: {e}")
            return jsonify({
                "error": "Token validation failed",
                "message": "An error occurred while validating your token",
                "code": "AUTH_TOKEN_VALIDATION_ERROR"
            }), 500

        return f(*args, **kwargs)
    return decorated


@main_blueprint.route("/api/auth/register", methods=["POST"])
def external_register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip() or None
    first_name = (data.get("first_name") or "").strip() or None
    last_name = (data.get("last_name") or "").strip() or None

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "username already exists"}), 409
    if email and User.query.filter_by(email=email).first():
        return jsonify({"error": "email already exists"}), 409

    new_user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
        verified=False,
        role=UserRole.GENERAL,
    )
    try:
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "message": "Registration successful. Account pending approval.",
            "user_id": new_user.id,
            "status": "pending_approval",
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"External register failed: {e}")
        return jsonify({"error": "registration failed"}), 500


@main_blueprint.route("/api/auth/login", methods=["POST"])
def external_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username/email and password are required"}), 400

    # Find user by username or email
    user = _find_user_by_username_or_email(username)

    if not user or not user.check_password(password):
        return jsonify({"error": "invalid username/email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "account pending approval"}), 403
    if user.is_suspended:
        return jsonify({"error": "account suspended"}), 403

    # Update login info
    try:
        user.update_login_info(request.remote_addr, request.headers.get("User-Agent"))
    except Exception:
        # Fallback if helper not available
        user.last_login = datetime.now(timezone.utc)
        user.login_count = (user.login_count or 0) + 1
        db.session.commit()

    return jsonify(_issue_tokens(user))


@main_blueprint.route("/api/auth/refresh", methods=["POST"])
def external_refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token") or ""

    if not refresh_token:
        return jsonify({
            "error": "refresh_token is required",
            "message": "Please provide your refresh token to get a new access token",
            "code": "AUTH_REFRESH_TOKEN_MISSING"
        }), 400

    try:
        # Load refresh token with max age
        payload = _get_serializer(REFRESH_TOKEN_SALT).loads(refresh_token, max_age=REFRESH_TOKEN_TTL_SECONDS)
        user = User.query.get(payload.get("user_id"))

        if not user:
            return jsonify({
                "error": "User not found",
                "message": "The user associated with this refresh token no longer exists",
                "code": "AUTH_REFRESH_USER_NOT_FOUND"
            }), 401

        if not user.is_active:
            return jsonify({
                "error": "Account inactive",
                "message": "Your account is pending approval or has been deactivated",
                "code": "AUTH_REFRESH_ACCOUNT_INACTIVE"
            }), 403

        if user.is_suspended:
            return jsonify({
                "error": "Account suspended",
                "message": "Your account has been suspended. Please contact support.",
                "code": "AUTH_REFRESH_ACCOUNT_SUSPENDED"
            }), 403

        # Check if refresh token is within sliding window
        token_age = datetime.now(timezone.utc) - datetime.fromtimestamp(payload.get("iat", 0), tz=timezone.utc)
        if token_age.total_seconds() > SLIDING_REFRESH_WINDOW_SECONDS:
            return jsonify({
                "error": "Refresh token expired",
                "message": "Your refresh token has exceeded the maximum lifetime. Please login again.",
                "code": "AUTH_REFRESH_TOKEN_SLIDING_WINDOW_EXCEEDED",
                "max_lifetime_days": SLIDING_REFRESH_WINDOW_SECONDS // (60 * 60 * 24)
            }), 401

        # Issue new tokens
        tokens = _issue_tokens(user)

        # Log refresh activity
        current_app.logger.info(f"Token refreshed for user {user.username} (ID: {user.id})")

        return jsonify({
            **tokens,
            "message": "Token refreshed successfully",
            "refresh_window_days": SLIDING_REFRESH_WINDOW_SECONDS // (60 * 60 * 24)
        })

    except SignatureExpired:
        return jsonify({
            "error": "Refresh token expired",
            "message": "Your refresh token has expired. Please login again.",
            "code": "AUTH_REFRESH_TOKEN_EXPIRED",
            "max_lifetime_days": REFRESH_TOKEN_TTL_SECONDS // (60 * 60 * 24)
        }), 401
    except BadSignature:
        return jsonify({
            "error": "Invalid refresh token",
            "message": "The provided refresh token is malformed or invalid",
            "code": "AUTH_REFRESH_TOKEN_INVALID"
        }), 401
    except Exception as e:
        current_app.logger.error(f"Refresh token validation error: {e}")
        return jsonify({
            "error": "Refresh token validation failed",
            "message": "An error occurred while validating your refresh token",
            "code": "AUTH_REFRESH_TOKEN_VALIDATION_ERROR"
        }), 500


@main_blueprint.route("/api/auth/logout", methods=["POST"])
def external_logout():
    # Stateless tokens cannot be revoked server-side without a store/denylist.
    # Clients should discard tokens. We respond success for consistency.
    return jsonify({"message": "logged out"})


@main_blueprint.route("/api/auth/me", methods=["GET"])
@token_required
def external_me():
    user = getattr(g, "api_user", None)
    if not user:
        return jsonify({"error": "not authenticated"}), 401
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value if user.role else None,
        "is_premium": user.is_premium,
        "verified": user.verified,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    })


# =============================
# External Profile & Account API
# =============================


def _get_or_create_user_profile(user):
    try:
        from models import UserProfile
    except Exception:
        UserProfile = None
    if not UserProfile:
        return None
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
    return profile


@main_blueprint.route("/api/auth/profile", methods=["GET"])
@token_required
def external_get_profile():
    user = g.api_user
    profile = _get_or_create_user_profile(user)
    profile_dict = profile.to_dict() if hasattr(profile, "to_dict") and profile else {}
    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birthdate": user.birthdate.isoformat() if getattr(user, "birthdate", None) else None,
            "bio": user.bio,
            "role": user.role.value if user.role else None,
        },
        "profile": profile_dict,
    })


@main_blueprint.route("/api/auth/profile", methods=["PUT"])
@token_required
def external_update_profile():
    user = g.api_user
    data = request.get_json(silent=True) or {}

    # Update user fields
    for field in ["first_name", "last_name", "email", "bio"]:
        if field in data:
            setattr(user, field, (data.get(field) or None))

    if "birthdate" in data:
        birthdate_value = data.get("birthdate")
        if birthdate_value:
            try:
                if "T" in birthdate_value:
                    birthdate_value = birthdate_value.split("T", 1)[0]
                user.birthdate = datetime.strptime(birthdate_value, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid birthdate format, expected YYYY-MM-DD"}), 400
        else:
            user.birthdate = None

    # Update profile fields
    profile = _get_or_create_user_profile(user)
    if profile:
        profile_updates = {}
        for field in ["pronouns", "short_bio", "location", "website"]:
            if field in data:
                profile_updates[field] = data.get(field)
        if "social_links" in data and isinstance(data.get("social_links"), dict):
            profile_updates["social_links"] = data.get("social_links")
        for k, v in profile_updates.items():
            setattr(profile, k, v)

    db.session.commit()

    return jsonify({
        "message": "Profile updated",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "birthdate": user.birthdate.isoformat() if getattr(user, "birthdate", None) else None,
            "bio": user.bio,
        },
        "profile": (profile.to_dict() if hasattr(profile, "to_dict") and profile else {}),
    })


@main_blueprint.route("/api/auth/profile/privacy", methods=["PATCH"])
@token_required
def external_update_privacy():
    user = g.api_user
    data = request.get_json(silent=True) or {}
    profile = _get_or_create_user_profile(user)
    if not profile:
        return jsonify({"error": "Profile not available"}), 400

    for flag in ["show_email", "show_birthdate"]:
        if flag in data:
            setattr(profile, flag, bool(data.get(flag)))

    db.session.commit()

    return jsonify({
        "message": "Privacy updated",
        "profile": profile.to_dict() if hasattr(profile, "to_dict") else {
            "show_email": getattr(profile, "show_email", False),
            "show_birthdate": getattr(profile, "show_birthdate", False),
        }
    })


@main_blueprint.route("/api/auth/profile/username", methods=["PATCH"])
@token_required
def external_change_username():
    user = g.api_user
    data = request.get_json(silent=True) or {}
    new_username = (data.get("username") or "").strip()
    current_password = data.get("current_password") or ""

    if not new_username or not current_password:
        return jsonify({"error": "username and current_password are required"}), 400
    # Validate format
    import re
    if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", new_username):
        return jsonify({"error": "invalid username format"}), 400
    # Check password
    if not user.check_password(current_password):
        return jsonify({"error": "current password is incorrect"}), 400
    # Uniqueness
    if User.query.filter(User.username == new_username, User.id != user.id).first():
        return jsonify({"error": "username already taken"}), 409

    old_username = user.username
    user.username = new_username
    db.session.commit()

    return jsonify({
        "message": "Username updated",
        "old_username": old_username,
        "new_username": new_username,
    })


@main_blueprint.route("/api/auth/account/change-password", methods=["POST"])
@token_required
def external_change_password():
    user = g.api_user
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 400
    if not new_password or new_password != confirm_password:
        return jsonify({"error": "New passwords do not match"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200


@main_blueprint.route("/api/auth/account", methods=["DELETE"])
@token_required
def external_delete_account():
    user = g.api_user
    try:
        # Best-effort cascade similar to internal endpoint
        try:
            from models import News
            News.query.filter_by(user_id=user.id).delete()
        except Exception:
            pass
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# =============================
# JWT-BASED LIBRARY ENDPOINTS
# =============================

# =============================
# JWT-BASED USER LIBRARY ENDPOINTS (for backward compatibility)
# =============================

# =============================
# JWT-BASED AUTH LIBRARY ENDPOINTS (for direct JWT API calls)
# =============================

@main_blueprint.route("/api/auth/library", methods=["POST"])
@token_required
def external_add_to_library():
    """Add content to library using JWT authentication."""
    user = g.api_user
    data = request.get_json(silent=True) or {}

    content_type = data.get("content_type")
    content_id = data.get("content_id")

    if not content_type or not content_id:
        return jsonify({"error": "content_type and content_id are required"}), 400

    if content_type not in ("news", "album"):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    if not isinstance(content_id, int):
        return jsonify({"error": "content_id must be an integer"}), 400

    try:
        # Check if already in library
        existing = UserLibrary.query.filter_by(
            user_id=user.id,
            content_type=content_type,
            content_id=content_id
        ).first()

        if existing:
            return jsonify({
                "success": True,
                "message": "Content already in library",
                "library_item": {
                    "id": existing.id,
                    "content_type": existing.content_type,
                    "content_id": existing.content_id,
                    "added_at": existing.added_at.isoformat() if existing.added_at else None
                }
            }), 200

        # Add to library
        library_item = UserLibrary(
            user_id=user.id,
            content_type=content_type,
            content_id=content_id
        )

        db.session.add(library_item)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Added to library successfully",
            "library_item": {
                "id": library_item.id,
                "content_type": library_item.content_type,
                "content_id": library_item.content_id,
                "added_at": library_item.added_at.isoformat() if library_item.added_at else None
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding to library: {e}")
        return jsonify({"error": "Failed to add to library", "details": str(e)}), 500


@main_blueprint.route("/api/auth/library", methods=["DELETE"])
@token_required
def external_remove_from_library():
    """Remove content from library using JWT authentication (direct API endpoint)."""
    user = g.api_user
    data = request.get_json(silent=True) or {}

    content_type = data.get("content_type")
    content_id = data.get("content_id")

    if not content_type or not content_id:
        return jsonify({"error": "content_type and content_id are required"}), 400

    if content_type not in ("news", "album"):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    if not isinstance(content_id, int):
        return jsonify({"error": "content_id must be an integer"}), 400

    try:
        # Find library item
        library_item = UserLibrary.query.filter_by(
            user_id=user.id,
            content_type=content_type,
            content_id=content_id
        ).first()

        if not library_item:
            return jsonify({"error": "Content not found in library"}), 404

        db.session.delete(library_item)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Removed from library successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing from library: {e}")
        return jsonify({"error": "Failed to remove from library", "details": str(e)}), 500


@main_blueprint.route("/api/auth/library/check", methods=["GET"])
@token_required
def external_check_in_library():
    """Check if content is in user's library using JWT authentication (direct API endpoint)."""
    user = g.api_user

    content_type = request.args.get("content_type")
    content_id = request.args.get("content_id", type=int)

    if not content_type or not content_id:
        return jsonify({"error": "content_type and content_id are required"}), 400

    if content_type not in ("news", "album"):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    try:
        # Check if in library
        exists = UserLibrary.query.filter_by(
            user_id=user.id,
            content_type=content_type,
            content_id=content_id
        ).first() is not None

        return jsonify({
            "success": True,
            "in_library": exists,
            "content_type": content_type,
            "content_id": content_id
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error checking library status: {e}")
        return jsonify({"error": "Failed to check library status", "details": str(e)}), 500


# =============================
# JWT-BASED COMMENT ENDPOINTS
# =============================

@main_blueprint.route("/api/auth/comments/<type>/<int:id>", methods=["POST"])
def external_post_comment(type, id):
    """Post a comment using JWT authentication."""
    try:
        from flask_login import current_user
        from flask import g

        # Combined authentication logic (both JWT and session)
        auth_header = request.headers.get("Authorization", "")
        user = None

        if auth_header.startswith("Bearer "):
            # Try JWT authentication
            token = auth_header.split(" ", 1)[1].strip()
            if token:
                # Validate JWT token format first
                parts = token.split('.')
                if len(parts) != 3:
                    _safe_log("warning", "Invalid JWT token format: {} parts instead of 3", len(parts))
                    return

                user, token_data = _validate_jwt_token(token)
                if user:
                    if not user.is_active:
                        return jsonify({"error": "Account inactive"}), 403
                    if user.is_suspended:
                        return jsonify({"error": "Account suspended"}), 403
                    # Token is valid and user is active
                    g.api_user = user
                    g.token_data = token_data
                    # Don't return here - continue processing the POST request

        # Fall back to session authentication
        if not user:
            if current_user.is_authenticated:
                user = current_user

        if not user:
            return jsonify({"error": "Authentication required"}), 401

        # Set user in g object for consistency with other endpoints
        g.api_user = user

        data = request.get_json(silent=True) or {}

        if type not in ('news', 'album'):
            return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

        content = data.get('content', '').strip()
        rating = data.get('rating')
        parent_id = data.get('parent_comment_id')

        if not content:
            return jsonify({"error": "Comment content is required"}), 400

        # Validate parent comment if provided
        if parent_id:
            parent_comment = Comment.query.filter_by(id=parent_id, content_type=type, content_id=id).first()
            if not parent_comment:
                return jsonify({"error": "Parent comment not found"}), 404
            if parent_comment.is_deleted:
                return jsonify({"error": "Cannot reply to deleted comment"}), 400

        # Create comment
        comment = Comment(
            content=content,
            content_type=type,
            content_id=id,
            user_id=user.id,
            parent_id=parent_id,
            is_approved=True,  # Auto-approve for authenticated users
            is_deleted=False
        )

        # If rating is provided, create a separate Rating record
        if rating is not None:
            rating_obj = Rating(
                rating_value=rating,
                content_type=type,
                content_id=id,
                user_id=user.id
            )
            db.session.add(rating_obj)

        # Validate comment before saving
        comment.validate()

        db.session.add(comment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Comment posted successfully",
            "comment": comment.to_dict()
        }), 201

    except ValueError as ve:
        _safe_log("error", "Comment validation error: {}", ve)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({"error": "Comment validation failed", "details": str(ve)}), 400
    except Exception as e:
        _safe_log("error", "Error posting comment: {}", e)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({"error": "Failed to post comment", "details": str(e)}), 500


@main_blueprint.route("/api/auth/comments/<type>/<int:id>/rate", methods=["POST"])
def external_rate_content(type, id):
    """Rate content using JWT authentication."""
    from flask_login import current_user
    from flask import g

    # Combined authentication logic (both JWT and session)
    auth_header = request.headers.get("Authorization", "")
    user = None

    if auth_header.startswith("Bearer "):
        # Try JWT authentication
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                # Validate JWT token format first
                parts = token.split('.')
                if len(parts) != 3:
                    _safe_log("warning", "Invalid JWT token format: {} parts instead of 3", len(parts))
                    return
                else:
                    user, token_data = _validate_jwt_token(token)
                    if user:
                        if not user.is_active:
                            return jsonify({"error": "Account inactive"}), 403
                        if user.is_suspended:
                            return jsonify({"error": "Account suspended"}), 403
                        # Token is valid and user is active
                        g.api_user = user
                        g.token_data = token_data
                        # Don't return here - continue processing the POST request
            except Exception as jwt_error:
                _safe_log("warning", "JWT authentication failed: {}", jwt_error)

        # Fall back to session authentication
    if not user:
        if current_user.is_authenticated:
            user = current_user

    if not user:
        return jsonify({"error": "Authentication required"}), 401

    # Set user in g object for consistency
    g.api_user = user

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No data provided"}), 400

    if type not in ('news', 'album'):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    rating_value = data.get('rating')

    if not rating_value or rating_value < 1 or rating_value > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    try:
        # Check if user already rated this content
        existing_rating = Rating.query.filter_by(
            user_id=user.id,
            content_type=type,
            content_id=id
        ).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating_value = rating_value
            message = "Rating updated successfully"
        else:
            # Create new rating
            rating_obj = Rating(
                user_id=user.id,
                content_type=type,
                content_id=id,
                rating_value=rating_value
            )
            db.session.add(rating_obj)
            message = "Rating submitted successfully"

        db.session.commit()

        return jsonify({
            "success": True,
            "message": message,
            "rating": {
                "id": existing_rating.id if existing_rating else rating_obj.id,
                "rating": rating,
                "review": review,
                "user_id": user.id,
                "content_type": content_type,
                "content_id": content_id
            }
        }), 201 if not existing_rating else 200

    except Exception as e:
        _safe_log("error", "Error rating content: {}", e)
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({"error": "Failed to rate content", "details": str(e)}), 500


@main_blueprint.route("/api/auth/comments/<type>/<int:id>", methods=["GET"])
def external_get_comments(type, id):
    """Get comments for content using JWT authentication."""
    from flask_login import current_user
    from flask import g

    # Combined authentication logic (both JWT and session)
    auth_header = request.headers.get("Authorization", "")
    user = None

    if auth_header.startswith("Bearer "):
        # Try JWT authentication
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                # Validate JWT token format first
                parts = token.split('.')
                if len(parts) != 3:
                    _safe_log("warning", "Invalid JWT token format: {} parts instead of 3", len(parts))
                    return
                else:
                    user, token_data = _validate_jwt_token(token)
                    if user:
                        if not user.is_active:
                            return jsonify({"error": "Account inactive"}), 403
                        if user.is_suspended:
                            return jsonify({"error": "Account suspended"}), 403
                        # Token is valid and user is active
                        g.api_user = user
                        g.token_data = token_data
                        # Don't return here - continue processing the GET request
            except Exception as jwt_error:
                _safe_log("warning", "JWT authentication failed: {}", jwt_error)

    # Fall back to session authentication
    if not user:
        if current_user.is_authenticated:
            user = current_user

    if not user:
        return jsonify({"error": "Authentication required"}), 401

    # Set user in g object for consistency
    g.api_user = user

    if type not in ('news', 'album'):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)

    try:
        # Get comments with replies
        comments_query = Comment.query.filter_by(
            content_type=type,
            content_id=id,
            is_approved=True,
            is_deleted=False,
            parent_id=None  # Only top-level comments
        ).order_by(Comment.created_at.desc())

        comments_pagination = comments_query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        comments_data = []
        for comment in comments_pagination.items:
            comment_dict = comment.to_dict()

            # Add user's like/dislike status
            comment_dict['user_liked'] = comment.is_liked_by_user(user.id)
            comment_dict['user_disliked'] = comment.is_disliked_by_user(user.id)
            comment_dict['like_count'] = comment.get_likes_count()
            comment_dict['dislike_count'] = comment.get_dislikes_count()

            # Get replies if requested
            include_replies = request.args.get('include_replies', 'false').lower() == 'true'
            if include_replies:
                replies = Comment.query.filter_by(
                    parent_id=comment.id,
                    is_approved=True,
                    is_deleted=False
                ).order_by(Comment.created_at.asc()).all()

                replies_data = []
                for reply in replies:
                    reply_dict = reply.to_dict()
                    reply_dict['user_liked'] = reply.is_liked_by_user(user.id)
                    reply_dict['user_disliked'] = reply.is_disliked_by_user(user.id)
                    reply_dict['like_count'] = reply.get_likes_count()
                    reply_dict['dislike_count'] = reply.get_dislikes_count()
                    replies_data.append(reply_dict)

                comment_dict['replies'] = replies_data

            comments_data.append(comment_dict)

        return jsonify({
            "success": True,
            "comments": comments_data,
            "pagination": {
                "page": comments_pagination.page,
                "per_page": comments_pagination.per_page,
                "total": comments_pagination.total,
                "pages": comments_pagination.pages,
                "has_next": comments_pagination.has_next,
                "has_prev": comments_pagination.has_prev
            }
        }), 200

    except Exception as e:
        _safe_log("error", "Error getting comments: {}", e)
        return jsonify({"error": "Failed to get comments", "details": str(e)}), 500


# =============================
# JWT-BASED COMMENT ENDPOINTS (backward compatibility)
# =============================

@main_blueprint.route("/api/auth/comments", methods=["POST"])
@token_required
def jwt_create_comment():
    """Create a new comment using JWT authentication."""
    user = g.api_user
    data = request.get_json(silent=True) or {}

    content_type = data.get('content_type')
    content_id = data.get('content_id')
    content = data.get('content', '').strip()
    rating = data.get('rating')
    parent_id = data.get('parent_comment_id')

    if not content_type or not content_id or not content:
        return jsonify({"error": "content_type, content_id, and content are required"}), 400

    if content_type not in ('news', 'album'):
        return jsonify({"error": "Invalid content_type. Must be 'news' or 'album'"}), 400

    if not isinstance(content_id, int):
        return jsonify({"error": "content_id must be an integer"}), 400

    # Validate parent comment if provided
    if parent_id:
        parent_comment = Comment.query.filter_by(id=parent_id, content_type=content_type, content_id=content_id).first()
        if not parent_comment:
            return jsonify({"error": "Parent comment not found"}), 404
        if parent_comment.is_deleted:
            return jsonify({"error": "Cannot reply to deleted comment"}), 400

    try:
        # Create comment
        comment = Comment(
            content=content,
            content_type=content_type,
            content_id=content_id,
            user_id=user.id,
            parent_id=parent_id,
            rating=rating,
            is_approved=True,  # Auto-approve for authenticated users
            is_deleted=False
        )

        db.session.add(comment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Comment created successfully",
            "comment": comment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating comment: {e}")
        return jsonify({"error": "Failed to create comment", "details": str(e)}), 500


@main_blueprint.route("/api/auth/comments/<int:comment_id>", methods=["PUT"])
@token_required
def jwt_update_comment(comment_id):
    """Update comment using JWT authentication."""
    user = g.api_user
    data = request.get_json(silent=True) or {}

    content = data.get('content', '').strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    try:
        comment = Comment.query.filter_by(id=comment_id, user_id=user.id).first()
        if not comment:
            return jsonify({"error": "Comment not found or not owned by user"}), 404

        if comment.is_deleted:
            return jsonify({"error": "Cannot update deleted comment"}), 400

        comment.content = content
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Comment updated successfully",
            "comment": comment.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating comment: {e}")
        return jsonify({"error": "Failed to update comment", "details": str(e)}), 500


@main_blueprint.route("/api/auth/comments/<int:comment_id>", methods=["DELETE"])
@token_required
def jwt_delete_comment(comment_id):
    """Delete comment using JWT authentication."""
    user = g.api_user

    try:
        comment = Comment.query.filter_by(id=comment_id, user_id=user.id).first()
        if not comment:
            return jsonify({"error": "Comment not found or not owned by user"}), 404

        if comment.is_deleted:
            return jsonify({"error": "Comment already deleted"}), 400

        # Soft delete
        comment.is_deleted = True
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Comment deleted successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting comment: {e}")
        return jsonify({"error": "Failed to delete comment", "details": str(e)}), 500


@main_blueprint.route("/api/auth/comments/<int:comment_id>/like", methods=["POST"])
@token_required
def jwt_like_comment(comment_id):
    """Like/dislike comment using JWT authentication."""
    user = g.api_user
    data = request.get_json(silent=True) or {}

    is_like = data.get('is_like', True)

    try:
        comment = Comment.query.filter_by(id=comment_id, is_deleted=False).first()
        if not comment:
            return jsonify({"error": "Comment not found"}), 404

        # Check if user already liked/disliked this comment
        existing_like = CommentLike.query.filter_by(
            comment_id=comment_id,
            user_id=user.id
        ).first()

        if existing_like:
            if existing_like.is_like == is_like:
                # User is trying to do the same action again, remove the like/dislike
                db.session.delete(existing_like)
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Reaction removed successfully",
                    "is_like": is_like,
                    "like_count": comment.get_likes_count(),
                    "dislike_count": comment.get_dislikes_count()
                }), 200
            else:
                # User is changing from like to dislike or vice versa
                existing_like.is_like = is_like
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": "Reaction updated successfully",
                    "is_like": is_like,
                    "like_count": comment.get_likes_count(),
                    "dislike_count": comment.get_dislikes_count()
                }), 200
        else:
            # Create new like/dislike
            new_like = CommentLike(
                comment_id=comment_id,
                user_id=user.id,
                is_like=is_like
            )
            db.session.add(new_like)
            db.session.commit()
            return jsonify({
                "success": True,
                "message": "Reaction added successfully",
                "is_like": is_like,
                "like_count": comment.get_like_count(),
                "dislike_count": comment.get_dislike_count()
            }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error handling comment reaction: {e}")
        return jsonify({"error": "Failed to process reaction", "details": str(e)}), 500


