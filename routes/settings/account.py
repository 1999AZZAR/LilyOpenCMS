"""
Account Management Routes

This module handles user account management and user administration routes.
"""

from routes import main_blueprint
from .common_imports import *


@main_blueprint.route("/settings/account")
@login_required
def user_account():
    # Allow access to GENERAL, ADMIN, and SUPERUSER
    if current_user.role not in [UserRole.GENERAL, UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)  # Only allowed roles can access this page
    
    # Redirect general users to their dedicated account page
    if current_user.role == UserRole.GENERAL:
        return redirect(url_for("main.user_account_settings"))
    
    # Admin and superuser use the admin account management
    return render_template('admin/settings/account_management.html')


@main_blueprint.route("/account/settings")
@login_required
def user_account_settings():
    # Only general users can access this page
    if current_user.role != UserRole.GENERAL:
        abort(403)
    
    return render_template('public/settings/user_account_settings.html')


# API endpoints for user account management
@main_blueprint.route("/api/user/profile", methods=["POST"])
@login_required
def update_user_profile():
    """Update user profile information"""
    if current_user.role != UserRole.GENERAL:
        return jsonify({"message": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        
        # Update user profile fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({"message": "Email sudah digunakan"}), 400
            current_user.email = data['email']
        if 'bio' in data:
            current_user.bio = data['bio']
        
        db.session.commit()
        return jsonify({"message": "Profil berhasil diperbarui"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Gagal memperbarui profil"}), 500


@main_blueprint.route("/api/user/change-password", methods=["POST"])
@login_required
def change_user_password():
    """Change user password"""
    if current_user.role != UserRole.GENERAL:
        return jsonify({"message": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({"message": "Kata sandi saat ini dan kata sandi baru diperlukan"}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({"message": "Kata sandi saat ini salah"}), 400
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({"message": "Kata sandi baru minimal 6 karakter"}), 400
        
        # Set new password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({"message": "Kata sandi berhasil diubah"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Gagal mengubah kata sandi"}), 500


@main_blueprint.route("/api/user/preferences", methods=["POST"])
@login_required
def update_user_preferences():
    """Update user preferences"""
    if current_user.role != UserRole.GENERAL:
        return jsonify({"message": "Unauthorized"}), 403
    
    try:
        data = request.get_json()
        
        # Update ad preferences
        if 'ad_preferences' in data:
            current_prefs = current_user.ad_preferences or {}
            current_prefs.update(data['ad_preferences'])
            current_user.ad_preferences = current_prefs
        
        db.session.commit()
        return jsonify({"message": "Preferensi berhasil disimpan"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Gagal menyimpan preferensi"}), 500


@main_blueprint.route("/api/user/delete-account", methods=["POST"])
@login_required
def delete_user_account():
    """Delete user account"""
    if current_user.role != UserRole.GENERAL:
        return jsonify({"message": "Unauthorized"}), 403
    
    try:
        # Delete user and all associated data
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({"message": "Akun berhasil dihapus"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Gagal menghapus akun"}), 500


@main_blueprint.route("/settings/users")
@login_required
def settings_users():
    # Allow access to ADMIN and SUPERUSER
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)  # Only admins and superusers can access this page
    return render_template('admin/settings/users_management.html')