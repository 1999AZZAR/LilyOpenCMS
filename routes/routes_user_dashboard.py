from routes import main_blueprint
from .common_imports import *


@main_blueprint.route("/dashboard")
@login_required
def user_dashboard():
    # General users get reader dashboard; admins should use settings dashboard
    if current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER] or current_user.is_owner():
        return redirect(url_for("main.settings_dashboard"))
    return render_template("public/reader_dashboard.html", user=current_user)


