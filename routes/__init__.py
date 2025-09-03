from .common_imports import *

from .routes_auth import *
from .routes_chategories import *
from .routes_comments import *
from .routes_helper import *
from .routes_images import *
from .routes_infos import *
from .routes_news import *
from .routes_public import *
from .routes_ratings import *
from .settings import *
from .routes_socialmedia import *
from .routes_subscriptions import *
from .routes_users import *
from .routes_roles import *
from .routes_analytics import *
from .routes_video import *
from .routes_albums import *
from .routes_seo import *
from .routes_user_dashboard import *
from .routes_library import *
from .routes_public_api import *
from .routes_api_xlate import *

__all__ = [
    "main_blueprint",
    "routes_auth",
    "routes_chategories",
    "routes_comments",
    "routes_helper",
    "routes_images",
    "routes_infos",
    "routes_news",
    "routes_public",
    "routes_ratings",
    "settings",
    "routes_socialmedia",
    "routes_users",
    "routes_roles",
    "routes_analytics",
    "routes_video",
    "routes_albums",
    "routes_seo",
    "routes_user_dashboard",
    "routes_library",
    "routes_public_api",
    "routes_api_xlate",
]