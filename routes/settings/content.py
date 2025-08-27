"""
Content Management Routes

This module handles news creation and management routes.
"""

from routes import main_blueprint
from .common_imports import *


@main_blueprint.route("/settings/create_news")
@login_required
def create_news():
    # Only admin-tier users can create news
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)

    # Optional prefill id
    news_id = request.args.get('news_id', type=int)

    # Pass the current_user object to the template
    return render_template('admin/settings/create_news_management.html', current_user=current_user, news_id=news_id)


# Alias route to support legacy link: /settings/create_news_management -> /settings/create_news (preserve query params)
@main_blueprint.route("/settings/create_news_management")
@login_required
def create_news_management_alias():
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    # Preserve query string
    qs = request.query_string.decode('utf-8')
    target = url_for('main.create_news')
    if qs:
        target = f"{target}?{qs}"
    return redirect(target, code=302)


@main_blueprint.route("/settings/manage_news")
@login_required
def manage_news():
    # Only admin-tier users can manage news
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)

    # Pass the current_user object to the template
    return render_template('admin/settings/manage_news_management.html', current_user=current_user)