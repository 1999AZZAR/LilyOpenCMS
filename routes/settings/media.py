"""
Media Routes

This module handles categories and YouTube management routes.
"""

from routes import main_blueprint
from .common_imports import *


@main_blueprint.route("/settings/categories")
@login_required
def settings_categories():
    # Allow access only to admin-tier users
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    return render_template('admin/settings/categories_management.html')


@main_blueprint.route("/settings/youtube")
@login_required
def settings_youtube():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    videos = YouTubeVideo.query.all()
    return render_template('admin/settings/youtube_management.html', videos=videos)