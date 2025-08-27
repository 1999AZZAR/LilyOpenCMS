from routes import main_blueprint
from .common_imports import *

@main_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return render_template("public/login.html")

        # Check if email already exists
        if email and User.query.filter_by(email=email).first():
            flash("Email already exists", "error")
            return render_template("public/login.html")

        # Create new user with approval required
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=False,  # User needs approval to be active
            verified=False,
            role=UserRole.GENERAL
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Record registration activity (disabled - method not available)
            
            flash("Registration successful! Your account is pending approval.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            return render_template("public/login.html")

    return render_template("public/login.html")


@main_blueprint.route("/api/registrations/pending", methods=["GET"])
@login_required
def get_pending_registrations():
    """Get all pending user registrations."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    
    # Get users that are not active (pending approval)
    pending_users = User.query.filter_by(is_active=False).order_by(User.created_at.desc()).all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'bio': user.bio,
        'role': user.role.value if user.role else None,
        'is_verified': user.verified,
        'is_suspended': user.is_suspended,
        'is_premium': user.is_premium,
        'custom_role_id': user.custom_role_id,
        'created_at': user.created_at.isoformat() if user.created_at else None
    } for user in pending_users])


@main_blueprint.route("/api/registrations/<int:user_id>/approve", methods=["POST"])
@login_required
def approve_registration(user_id):
    """Approve a user registration."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    
    if user.is_active:
        return jsonify({"error": "User is already active"}), 400
    
    # Activate the user
    user.is_active = True
    user.verified = True  # Auto-verify approved users
    
    db.session.commit()
    
    # Record approval activity (disabled - method not available)
    
    return jsonify({
        "message": f"Registration approved for {user.username}",
        "user": {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'bio': user.bio,
            'role': user.role.value if user.role else None,
            'is_verified': user.verified,
            'is_suspended': user.is_suspended,
            'is_premium': user.is_premium,
            'custom_role_id': user.custom_role_id,
            'created_at': user.created_at.isoformat() if user.created_at else None
        }
    })


@main_blueprint.route("/api/registrations/<int:user_id>/reject", methods=["POST"])
@login_required
def reject_registration(user_id):
    """Reject a user registration."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    reason = data.get("reason", "Registration rejected")
    
    if user.is_active:
        return jsonify({"error": "Cannot reject active user"}), 400
    
    # Record rejection activity (disabled - method not available)
    
    # Delete the user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        "message": f"Registration rejected for {user.username}",
        "reason": reason
    })


@main_blueprint.route("/api/registrations/bulk/approve", methods=["POST"])
@login_required
def bulk_approve_registrations():
    """Bulk approve user registrations."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    
    data = request.get_json()
    user_ids = data.get("user_ids", [])
    
    if not user_ids:
        return jsonify({"error": "No user IDs provided"}), 400
    
    # Get pending users
    users = User.query.filter(
        User.id.in_(user_ids),
        User.is_active == False
    ).all()
    
    approved_users = []
    for user in users:
        user.is_active = True
        user.verified = True
        approved_users.append(user)
        
        # Record user activity (disabled for now)
        pass
    
    db.session.commit()
    
    # Record bulk approval activity (with safety check)
    usernames = [user.username for user in approved_users]
    try:
        if hasattr(current_user, 'record_activity'):
            current_user.record_activity(
                "bulk_approve_registrations",
                f"Bulk approved registrations for: {', '.join(usernames)}",
                request.remote_addr,
                request.headers.get("User-Agent")
            )
    except Exception as e:
        current_app.logger.warning(f"Could not record user activity: {str(e)}")
    
    return jsonify({
        "message": f"Approved {len(approved_users)} registrations",
        "approved_count": len(approved_users),
        "total_requested": len(user_ids)
    })


@main_blueprint.route("/api/registrations/bulk/reject", methods=["POST"])
@login_required
def bulk_reject_registrations():
    """Bulk reject user registrations."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    
    data = request.get_json()
    user_ids = data.get("user_ids", [])
    reason = data.get("reason", "Bulk rejection")
    
    if not user_ids:
        return jsonify({"error": "No user IDs provided"}), 400
    
    # Get pending users
    users = User.query.filter(
        User.id.in_(user_ids),
        User.is_active == False
    ).all()
    
    # Record rejection activity (disabled - method not available)
    
    # Delete users
    for user in users:
        db.session.delete(user)
    
    db.session.commit()
    
    return jsonify({
        "message": f"Rejected {len(users)} registrations",
        "rejected_count": len(users),
        "total_requested": len(user_ids),
        "reason": reason
    })


@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required", "error")
            return render_template("public/login.html")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account is pending approval. Please wait for administrator approval.", "error")
                return render_template("public/login.html")
            
            if user.is_suspended:
                flash("Your account has been suspended. Please contact an administrator.", "error")
                return render_template("public/login.html")

            # Update login information
            user.last_login = datetime.now(timezone.utc)
            user.login_count += 1
            db.session.commit()
            
            login_user(user)
            next_page = request.args.get("next")
            # Role-based redirect: admins to settings, general users to reader dashboard
            if next_page:
                return redirect(next_page)
            if user.role in [UserRole.ADMIN, UserRole.SUPERUSER] or user.is_owner():
                return redirect(url_for("main.settings_dashboard"))
            return redirect(url_for("main.user_dashboard"))

        flash("Invalid credentials", "error")
        return render_template("public/login.html")

    return render_template("public/login.html")

@main_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@main_blueprint.route("/api/account/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json()
    current_password = data["current_password"]
    new_password = data["new_password"]
    confirm_password = data["confirm_password"]

    if not current_user.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "New passwords do not match"}), 400

    current_user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully"}), 200


@main_blueprint.route("/api/account/delete", methods=["DELETE"])
@login_required
def delete_account():
    News.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({"message": "Account deleted successfully"}), 200