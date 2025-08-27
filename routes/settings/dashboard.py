"""
Dashboard Routes

This module handles the main settings dashboard and analytics routes.
"""

from routes import main_blueprint
from .common_imports import *
from optimizations import monitor_ssr_render


@main_blueprint.route("/settings")
@login_required
@monitor_ssr_render("settings_dashboard")
def settings_dashboard():
    # Allow access only to admin-tier users
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    return render_template('admin/settings/settings_management.html')


@main_blueprint.route("/settings/analytics")
@login_required
@monitor_ssr_render("settings_analytics")
def settings_analytics():
    # Allow access only to admin-tier users
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    return render_template('admin/settings/analytics_dashboard.html')