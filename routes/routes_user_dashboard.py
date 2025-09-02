from routes import main_blueprint
from .common_imports import *


@main_blueprint.route("/dashboard")
@login_required
def user_dashboard():
    # Redirect to the new user profile system
    return redirect(url_for("user_profile.user_profile", username=current_user.username))


