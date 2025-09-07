from routes import main_blueprint
from .common_imports import *
from flask import g
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from functools import wraps


# Token configuration
ACCESS_TOKEN_SALT = "external-access-token"
REFRESH_TOKEN_SALT = "external-refresh-token"
ACCESS_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour
REFRESH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 14  # 14 days


def _get_serializer(salt: str) -> URLSafeTimedSerializer:
    secret_key = current_app.config.get("SECRET_KEY", "change-me")
    return URLSafeTimedSerializer(secret_key, salt=salt)


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


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        try:
            data = _get_serializer(ACCESS_TOKEN_SALT).loads(token, max_age=ACCESS_TOKEN_TTL_SECONDS)
            user = User.query.get(data.get("user_id"))
            if not user:
                return jsonify({"error": "User not found"}), 401
            if not user.is_active or user.is_suspended:
                return jsonify({"error": "Account inactive or suspended"}), 403
            g.api_user = user
        except SignatureExpired:
            return jsonify({"error": "Token expired"}), 401
        except BadSignature:
            return jsonify({"error": "Invalid token"}), 401
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
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401
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
        return jsonify({"error": "refresh_token is required"}), 400
    try:
        payload = _get_serializer(REFRESH_TOKEN_SALT).loads(refresh_token, max_age=REFRESH_TOKEN_TTL_SECONDS)
        user = User.query.get(payload.get("user_id"))
        if not user:
            return jsonify({"error": "User not found"}), 401
        if not user.is_active or user.is_suspended:
            return jsonify({"error": "Account inactive or suspended"}), 403
        tokens = _issue_tokens(user)
        return jsonify(tokens)
    except SignatureExpired:
        return jsonify({"error": "refresh token expired"}), 401
    except BadSignature:
        return jsonify({"error": "invalid refresh token"}), 401


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


