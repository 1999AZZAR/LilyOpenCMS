from routes import main_blueprint
from .common_imports import *
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from routes.utils.email_service import email_service


def _get_serializer():
    secret_key = current_app.config.get("SECRET_KEY", "change-me")
    return URLSafeTimedSerializer(secret_key, salt="email-verify")

def _find_user_by_username_or_email(identifier):
    """Find user by username or email"""
    if '@' in identifier:
        # Input is email
        return User.query.filter_by(email=identifier).first()
    else:
        # Input is username
        return User.query.filter_by(username=identifier).first()

def _send_verification_email(user):
    try:
        current_app.logger.info(f"🔍 Starting verification email process for user: {user.username} (email: {user.email})")

        s = _get_serializer()
        token = s.dumps({"user_id": user.id, "email": user.email or ""})
        current_app.logger.info(f"🔍 Generated verification token for user {user.username}")

        # Send actual email using email service
        if user.email:
            current_app.logger.info(f"🔍 Attempting to send verification email to {user.email}")
            success = email_service.send_verification_email(user, token)
            if success:
                current_app.logger.info(f"✅ Verification email sent successfully to {user.email}")
            else:
                current_app.logger.warning(f"⚠️ Failed to send verification email to {user.email}")
        else:
            # Fallback to logging if no email
            verify_url = url_for("main.verify_email", token=token, _external=True)
            current_app.logger.info(f"📧 Verification link for {user.username} (no email): {verify_url}")

        user.last_verification_sent_at = datetime.now(timezone.utc)
        db.session.commit()
        current_app.logger.info(f"✅ Verification email process completed for {user.username}")
    except Exception as e:
        current_app.logger.error(f"❌ Failed to send verification email: {e}")
        import traceback
        current_app.logger.error(f"❌ Stack trace: {traceback.format_exc()}")

def _send_password_reset_email(user):
    try:
        current_app.logger.info(f"🔍 Starting password reset email process for user: {user.username} (email: {user.email})")

        s = _get_serializer()
        token = s.dumps({"user_id": user.id, "email": user.email or ""})
        current_app.logger.info(f"🔍 Generated password reset token for user {user.username}")

        # Send actual email using email service
        if user.email:
            current_app.logger.info(f"🔍 Attempting to send password reset email to {user.email}")
            success = email_service.send_password_reset_email(user, token)
            if success:
                current_app.logger.info(f"✅ Password reset email sent successfully to {user.email}")
            else:
                current_app.logger.warning(f"⚠️ Failed to send password reset email to {user.email}")
        else:
            # Fallback to logging if no email
            reset_url = url_for("main.reset_password", token=token, _external=True)
            current_app.logger.info(f"📧 Password reset link for {user.username} (no email): {reset_url}")

        current_app.logger.info(f"✅ Password reset email process completed for {user.username}")
    except Exception as e:
        current_app.logger.error(f"❌ Failed to send password reset email: {e}")
        import traceback
        current_app.logger.error(f"❌ Stack trace: {traceback.format_exc()}")

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
            # Send verification email/log link
            if new_user.email:
                _send_verification_email(new_user)
            
            flash("Registration successful! Your account is pending approval.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            return render_template("public/login.html")

    return render_template("public/login.html")


@main_blueprint.route("/verify-email")
def verify_email():
    token = request.args.get("token", "")
    if not token:
        flash("Invalid verification link.", "error")
        return redirect(url_for("main.login"))
    try:
        s = _get_serializer()
        data = s.loads(token, max_age=60*60*24*3)  # 3 days
        user = User.query.get(data.get("user_id"))
        if not user:
            flash("Invalid verification token.", "error")
            return redirect(url_for("main.login"))
        if not user.verified:
            user.verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            # Hybrid policy: auto-approve verified low-risk users; leave others pending
            try:
                from routes.utils.risk_policy import should_auto_approve
                if should_auto_approve(user):
                    user.is_active = True
            except Exception as _e:
                current_app.logger.info(f"Risk policy unavailable or errored: {_e}")
            db.session.commit()
        flash("Email verified successfully.", "success")
        return redirect(url_for("main.login"))
    except SignatureExpired:
        flash("Verification link has expired.", "error")
        return redirect(url_for("main.login"))
    except BadSignature:
        flash("Invalid verification token.", "error")
        return redirect(url_for("main.login"))


@main_blueprint.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email_or_username = request.form.get("email_or_username", "").strip()

        if not email_or_username:
            flash("Please enter your email address or username", "error")
            return render_template("public/forgot_password.html")

        # Find user by email or username
        user = _find_user_by_username_or_email(email_or_username)

        if not user:
            # Don't reveal if user exists or not for security
            flash("If an account with that email/username exists, you will receive a password reset link.", "info")
            return render_template("public/forgot_password.html")

        if not user.email:
            flash("This account doesn't have an email address associated with it.", "error")
            return render_template("public/forgot_password.html")

        try:
            # Clear any existing reset tokens
            user.password_reset_token = None
            user.password_reset_expires_at = None
            db.session.commit()

            # Send password reset email
            _send_password_reset_email(user)

            flash("If an account with that email/username exists, you will receive a password reset link.", "info")
            return render_template("public/forgot_password.html")

        except Exception as e:
            current_app.logger.error(f"❌ Error sending password reset email: {e}")
            flash("An error occurred while sending the password reset email. Please try again later.", "error")
            return render_template("public/forgot_password.html")

    return render_template("public/forgot_password.html")


@main_blueprint.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token", "")
    if not token:
        flash("Invalid password reset link.", "error")
        return redirect(url_for("main.login"))

    try:
        s = _get_serializer()
        data = s.loads(token, max_age=60*60)  # 1 hour
        user = User.query.get(data.get("user_id"))

        if not user:
            flash("Invalid password reset token.", "error")
            return redirect(url_for("main.login"))

        if not user.email:
            flash("This account doesn't have an email address.", "error")
            return redirect(url_for("main.login"))

        if request.method == "POST":
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")

            if not new_password or not confirm_password:
                flash("Both password fields are required.", "error")
                return render_template("public/reset_password.html", token=token)

            if new_password != confirm_password:
                flash("Passwords do not match.", "error")
                return render_template("public/reset_password.html", token=token)

            if len(new_password) < 6:
                flash("Password must be at least 6 characters long.", "error")
                return render_template("public/reset_password.html", token=token)

            try:
                # Update password
                user.set_password(new_password)

                # Clear reset token
                user.password_reset_token = None
                user.password_reset_expires_at = None

                # Invalidate all sessions on password change
                try:
                    from routes.utils.session_security import get_session_security_manager
                    session_manager = get_session_security_manager()
                    session_manager.invalidate_user_sessions(user.id, "Password reset")
                except Exception as e:
                    current_app.logger.warning(f"Session invalidation failed during password reset: {e}")

                db.session.commit()

                flash("Password reset successfully. Please log in with your new password.", "success")
                return redirect(url_for("main.login"))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"❌ Error resetting password: {e}")
                flash("An error occurred while resetting your password. Please try again.", "error")
                return render_template("public/reset_password.html", token=token)

        return render_template("public/reset_password.html", token=token)

    except SignatureExpired:
        flash("Password reset link has expired. Please request a new one.", "error")
        return redirect(url_for("main.forgot_password"))
    except BadSignature:
        flash("Invalid password reset token.", "error")
        return redirect(url_for("main.forgot_password"))


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
        # Maintenance mode check (block general users when enabled)
        try:
            import os, json
            settings_path = os.path.join(current_app.instance_path, 'app_settings.json')
            maintenance_enabled = False
            maintenance_message = 'Situs dalam mode perawatan. Silakan coba lagi nanti.'
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    m = data.get('maintenance', {}) if isinstance(data, dict) else {}
                    maintenance_enabled = bool(m.get('enabled', False))
                    maintenance_message = m.get('message') or maintenance_message
        except Exception:
            maintenance_enabled = False

        username_or_email = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username_or_email or not password:
            flash("Username/email and password are required", "error")
            return render_template("public/login.html")

        # Find user by username or email
        user = _find_user_by_username_or_email(username_or_email)

        if user and user.check_password(password):
            # If maintenance is enabled, allow only SUPERUSER
            if maintenance_enabled and user.role != UserRole.SUPERUSER:
                flash(maintenance_message, "error")
                return render_template("public/login.html")
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

            # Create enhanced session tracking
            try:
                from routes.utils.session_security import get_session_security_manager
                session_manager = get_session_security_manager()

                # Invalidate existing sessions if rotation is enabled
                if current_app.config.get('SESSION_ROTATION_ENABLED', False):
                    session_manager.invalidate_user_sessions(user.id, "Login session rotation")

                # Create new session
                session_id = session_manager.create_user_session(user)

                # Enforce concurrent session limit
                session_manager.enforce_concurrent_session_limit(user.id)

                # Record login activity
                session_manager.record_user_activity(
                    user.id,
                    "login",
                    f"Successful login from {request.remote_addr}",
                    request.remote_addr,
                    request.headers.get("User-Agent")
                )

                current_app.logger.info(f"Enhanced session {session_id} created for user {user.username}")

            except Exception as e:
                current_app.logger.warning(f"Session security features failed: {e}")
                # Continue with login even if session security fails

            login_user(user)
            next_page = request.args.get("next")
            # Role-based redirect: admins to settings, general users to user profile
            if next_page:
                return redirect(next_page)
            if user.role in [UserRole.ADMIN, UserRole.SUPERUSER] or user.is_owner():
                return redirect(url_for("main.settings_dashboard"))
            return redirect(url_for("user_profile.user_profile", username=user.username))

        # Record failed login attempt for security monitoring
        try:
            if user:  # Valid user but wrong password
                from routes.utils.session_security import get_session_security_manager
                session_manager = get_session_security_manager()
                session_manager.record_user_activity(
                    user.id,
                    "login_failed",
                    f"Failed login attempt from {request.remote_addr}",
                    request.remote_addr,
                    request.headers.get("User-Agent")
                )
                current_app.logger.warning(f"Failed login attempt for user {user.username} from {request.remote_addr}")
        except Exception as e:
            current_app.logger.warning(f"Could not record failed login attempt: {e}")

        flash("Invalid username/email or password", "error")
        return render_template("public/login.html")

    return render_template("public/login.html")

@main_blueprint.route("/logout")
@login_required
def logout():
    # Enhanced session invalidation
    try:
        from routes.utils.session_security import get_session_security_manager
        session_manager = get_session_security_manager()

        # Invalidate current session
        session_id = session.get('session_id')
        if session_id:
            session_manager.invalidate_session(session_id, "User logout")

        # Record logout activity
        session_manager.record_user_activity(
            current_user.id,
            "logout",
            f"User logout from {request.remote_addr}",
            request.remote_addr,
            request.headers.get("User-Agent")
        )

        current_app.logger.info(f"Session {session_id} invalidated for user {current_user.username}")

    except Exception as e:
        current_app.logger.warning(f"Session security features failed during logout: {e}")

    logout_user()
    session.clear()
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

    # Enhanced security: invalidate all sessions on password change
    try:
        from routes.utils.session_security import get_session_security_manager
        session_manager = get_session_security_manager()

        # Invalidate all sessions for this user
        session_manager.invalidate_user_sessions(current_user.id, "Password changed")

        # Record password change activity
        session_manager.record_user_activity(
            current_user.id,
            "password_change",
            f"Password changed from {request.remote_addr}",
            request.remote_addr,
            request.headers.get("User-Agent")
        )

        current_app.logger.info(f"All sessions invalidated for user {current_user.username} due to password change")

    except Exception as e:
        current_app.logger.warning(f"Session invalidation failed during password change: {e}")

    db.session.commit()
    return jsonify({"message": "Password changed successfully. Please log in again."}), 200


@main_blueprint.route("/api/account/delete", methods=["DELETE"])
@login_required
def delete_account():
    News.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({"message": "Account deleted successfully"}), 200


@main_blueprint.route("/api/account/stats", methods=["GET"])
@login_required
def account_stats():
    """Get comprehensive account statistics for the current user."""
    try:
        from models import News, Album, AlbumChapter, Comment, Rating
        
        # Get user's news/articles
        user_news = News.query.filter_by(user_id=current_user.id).all()
        total_articles = len(user_news)
        visible_articles = len([n for n in user_news if n.is_visible])
        total_reads = sum(n.read_count or 0 for n in user_news)
        
        # Get user's albums/books
        user_albums = Album.query.filter_by(user_id=current_user.id).all()
        total_albums = len(user_albums)
        
        # Get total chapters from user's albums
        album_ids = [album.id for album in user_albums]
        total_chapters = AlbumChapter.query.filter(AlbumChapter.album_id.in_(album_ids)).count() if album_ids else 0
        
        # Get user's comments
        total_comments = Comment.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            "total_articles": total_articles,
            "visible_articles": visible_articles,
            "total_reads": total_reads,
            "total_albums": total_albums,
            "total_chapters": total_chapters,
            "total_comments": total_comments
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/api/account/albums", methods=["GET"])
@login_required
def account_albums():
    """Get user's albums with pagination and filtering."""
    try:
        from models import Album, Category
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        album_type = request.args.get('type', '').strip()
        
        # Base query for user's albums
        query = Album.query.filter_by(user_id=current_user.id)
        
        # Apply filters
        if search:
            query = query.filter(Album.title.ilike(f'%{search}%'))
        
        if status:
            if status == 'visible':
                query = query.filter(Album.is_visible == True)
            elif status == 'hidden':
                query = query.filter(Album.is_visible == False)
            elif status == 'archived':
                query = query.filter(Album.is_archived == True)
        
        if album_type:
            if album_type == 'premium':
                query = query.filter(Album.is_premium == True)
            elif album_type == 'regular':
                query = query.filter(Album.is_premium == False)
        
        # Get paginated results
        pagination = query.order_by(Album.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        albums_data = []
        for album in pagination.items:
            albums_data.append({
                'id': album.id,
                'title': album.title,
                'category': album.category.name if album.category else 'Uncategorized',
                'is_visible': album.is_visible,
                'is_premium': album.is_premium,
                'is_archived': album.is_archived,
                'total_chapters': album.total_chapters or 0,
                'created_at': album.created_at.strftime('%Y-%m-%d') if album.created_at else None
            })
        
        return jsonify({
            'albums': albums_data,
            'total': pagination.total,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/api/account/comments", methods=["GET"])
@login_required
def account_comments():
    """Get user's recent comments."""
    try:
        from models import Comment, News
        
        # Get user's recent comments
        comments = Comment.query.filter_by(user_id=current_user.id)\
            .order_by(Comment.created_at.desc())\
            .limit(10)\
            .all()
        
        comments_data = []
        for comment in comments:
            # Get the article title
            article_title = "Unknown Article"
            if comment.content_type == 'news' and comment.content_id:
                article = News.query.get(comment.content_id)
                if article:
                    article_title = article.title
            
            comments_data.append({
                'id': comment.id,
                'content': comment.content,
                'article_title': article_title,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M') if comment.created_at else None,
                'is_approved': comment.is_approved
            })
        
        return jsonify({
            'comments': comments_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/api/account/activity", methods=["GET"])
@login_required
def account_activity():
    """Get user's recent activity."""
    try:
        from models import UserActivity, News, Album
        
        # Get user's recent activities
        activities = UserActivity.query.filter_by(user_id=current_user.id)\
            .order_by(UserActivity.created_at.desc())\
            .limit(10)\
            .all()
        
        activities_data = []
        for activity in activities:
            # Create human-readable descriptions
            description = activity.description or activity.activity_type
            
            # Add more context based on activity type
            if activity.activity_type == 'create_news':
                description = f"Membuat artikel: {activity.description}"
            elif activity.activity_type == 'update_news':
                description = f"Mengupdate artikel: {activity.description}"
            elif activity.activity_type == 'create_album':
                description = f"Membuat buku/seri: {activity.description}"
            elif activity.activity_type == 'update_album':
                description = f"Mengupdate buku/seri: {activity.description}"
            elif activity.activity_type == 'login':
                description = "Login ke sistem"
            elif activity.activity_type == 'logout':
                description = "Logout dari sistem"
            
            activities_data.append({
                'id': activity.id,
                'action': activity.activity_type.replace('_', ' ').title(),
                'description': description,
                'created_at': activity.created_at.strftime('%Y-%m-%d %H:%M') if activity.created_at else None
            })
        
        return jsonify({
            'activities': activities_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_user_dashboard_url(user):
    """Get the appropriate dashboard URL based on user role."""
    if user.role in [UserRole.ADMIN, UserRole.SUPERUSER] or user.is_owner():
        return url_for("main.settings_dashboard")
    return url_for("user_profile.user_profile", username=user.username)

@main_blueprint.route("/api/account/profile", methods=["GET"])
@login_required
def account_profile():
    """Get current user's profile data."""
    try:
        return jsonify({
            'username': current_user.username,
            'email': current_user.email,
            'full_name': current_user.get_full_name(),
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'birthdate': current_user.birthdate.isoformat() if current_user.birthdate else None,
            'age': current_user.get_age() if current_user.birthdate else None,
            'role': current_user.role.value if current_user.role else None,
            'custom_role_name': current_user.custom_role.name if current_user.custom_role else None,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/api/account/profile/<username>", methods=["GET"])
def get_user_profile_by_username(username):
    """Get a specific user's profile data by username."""
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'birthdate': user.birthdate.isoformat() if user.birthdate else None,
            'age': user.get_age() if user.birthdate else None,
            'role': user.role.value if user.role else None,
            'custom_role_name': user.custom_role.name if user.custom_role else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/api/account/profile", methods=["PUT"])
@login_required
def update_account_profile():
    """Update current user's profile data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update allowed fields
        if 'full_name' in data:
            full_name = data['full_name'].strip()
            # Split full name into first and last name
            name_parts = full_name.split(' ', 1)
            if len(name_parts) > 1:
                current_user.first_name = name_parts[0].strip()
                current_user.last_name = name_parts[1].strip()
            else:
                current_user.first_name = full_name
                current_user.last_name = None
        
        if 'birthdate' in data:
            if data['birthdate']:
                try:
                    # Handle both ISO format and YYYY-MM-DD format
                    birthdate_str = data['birthdate']
                    if 'T' in birthdate_str:
                        birthdate_str = birthdate_str.split('T', 1)[0]
                    current_user.birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
                except ValueError:
                    return jsonify({"error": "Invalid birthdate format, expected YYYY-MM-DD"}), 400
            else:
                current_user.birthdate = None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': {
                'username': current_user.username,
                'email': current_user.email,
                'full_name': current_user.get_full_name(),
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'birthdate': current_user.birthdate.isoformat() if current_user.birthdate else None,
                'age': current_user.get_age() if current_user.birthdate else None,
                'role': current_user.role.value if current_user.role else None,
                'custom_role_name': current_user.custom_role.name if current_user.custom_role else None
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/settings/pending-registrations")
@login_required
def pending_registrations():
    """Pending registrations management page for admins."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    return render_template('admin/settings/pending_registrations.html', current_user=current_user)