from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    abort,
    Response,
    flash,
    current_app,
    send_file,
)
from flask_login import login_user, logout_user, login_required, current_user

# Create the main blueprint
main_blueprint = Blueprint("main", __name__)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import markdown
import os
import requests
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_ 
import re
from urllib.parse import urlparse
from mimetypes import guess_extension
from PIL import Image as PILImage, ImageOps

from models import (
    db,
    User,
    Image,
    YouTubeVideo,
    News,
    Album,
    AlbumChapter,
    RootSEO,
    PrivacyPolicy,
    MediaGuideline,
    VisiMisi,
    Penyangkalan,
    PedomanHak,
    UserRole,
    Category,
    CategoryGroup,
    ShareLog,
    SocialMedia,
    ContactDetail,
    TeamMember,
    Permission,
    CustomRole,
    UserActivity,
    NavigationLink,
    BrandIdentity,
)

# Import permission management functions
from routes.utils.permission_manager import (
    can_access_admin,
    can_manage_users,
    can_manage_content,
    can_manage_categories,
    can_manage_settings,
    can_manage_roles,
    can_manage_ads,
    can_moderate_comments,
    can_manage_ratings,
    can_access_analytics,
    can_manage_legal,
    can_manage_brand,
    can_manage_seo,
    has_permission,
    has_any_permission,
    has_all_permissions,
    get_user_role_display,
    get_user_permissions_summary,
    is_superuser,
    is_admin,
    is_admin_tier,
    has_custom_role,
    PermissionManager
)
