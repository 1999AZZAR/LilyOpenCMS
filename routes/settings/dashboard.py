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
    
    # Get user stats server-side
    try:
        from models import News, Album, AlbumChapter, Comment, Image, YouTubeVideo, User
        
        # Get user's news/articles
        user_news = News.query.filter_by(user_id=current_user.id).all()
        total_articles = len(user_news)
        
        # Get user's albums
        user_albums = Album.query.filter_by(user_id=current_user.id).all()
        total_albums = len(user_albums)
        
        # Get user's comments
        total_comments = Comment.query.filter_by(user_id=current_user.id).count()
        
        # Get user's images (with role-based filtering)
        images_query = Image.query
        if not current_user.role in [UserRole.SUPERUSER, UserRole.ADMIN]:
            # Apply same filtering as in the API
            custom_name = (current_user.custom_role.name.lower() if getattr(current_user, 'custom_role', None) and current_user.custom_role.name else "")
            is_admin_tier = current_user.role in [UserRole.SUPERUSER, UserRole.ADMIN] or custom_name == "subadmin"
            if not is_admin_tier:
                images_query = images_query.filter_by(user_id=current_user.id)
        total_images = images_query.count()
        
        # Get total videos (for now, show all videos since API doesn't filter by user)
        total_videos = YouTubeVideo.query.count()
        
        # Get total users (for superadmin only)
        total_users = 0
        if current_user.role == UserRole.SUPERUSER:
            total_users = User.query.count()
        
        user_stats = {
            'total_articles': total_articles,
            'total_albums': total_albums,
            'total_comments': total_comments,
            'total_images': total_images,
            'total_videos': total_videos,
            'total_users': total_users
        }
        
    except Exception as e:
        # Fallback stats in case of error
        user_stats = {
            'total_articles': 0,
            'total_albums': 0,
            'total_comments': 0,
            'total_images': 0,
            'total_videos': 0,
            'total_users': 0
        }
    
    return render_template('admin/settings/settings_management.html', user_stats=user_stats)


@main_blueprint.route("/settings/analytics")
@login_required
@monitor_ssr_render("settings_analytics")
def settings_analytics():
    # Allow access only to admin-tier users
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    return render_template('admin/settings/analytics_dashboard.html')


@main_blueprint.route("/settings/content-deletion-requests")
@login_required
def content_deletion_requests():
    """Content deletion requests management page."""
    # Allow access only to admin-tier users
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    return render_template('admin/settings/content_deletion_requests.html')