from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, or_, and_, func
from models import db, User, UserProfile, UserStats, News, Album, AlbumChapter, Image, Category, UserLibrary, ReadingHistory, Comment, UserRole, CustomRole, WriteAccessRequest, UserActivity
from datetime import datetime, timedelta, timezone
import json

# Create blueprint for user translation APIs
user_xlate_bp = Blueprint('user_xlate', __name__, url_prefix='/api/xlate/user')

def _safe_datetime(dt):
    """Safely convert datetime to ISO string."""
    return dt.isoformat() if dt else None

def _user_to_dict(user, include_sensitive=False):
    """Convert user object to dictionary with optional sensitive data."""
    if not user:
        return None
    
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email if include_sensitive else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() if hasattr(user, 'get_full_name') else f"{user.first_name or ''} {user.last_name or ''}".strip(),
        'bio': user.bio,
        'role': user.role.value if user.role else None,
        'custom_role': user.custom_role.name if user.custom_role else None,
        'is_active': user.is_active,
        'is_premium': user.is_premium,
        'verified': user.verified,
        'is_suspended': user.is_suspended,
        'write_access': user.write_access,
        'created_at': _safe_datetime(user.created_at),
        'last_login': _safe_datetime(user.last_login),
        'login_count': user.login_count,
        'birthdate': user.birthdate.isoformat() if user.birthdate else None,
        'age': user.get_age() if hasattr(user, 'get_age') else None,
    }
    
    if include_sensitive:
        data.update({
            'suspension_reason': user.suspension_reason,
            'suspension_until': _safe_datetime(user.suspension_until),
            'premium_expires_at': _safe_datetime(user.premium_expires_at),
            'has_premium_access': user.has_premium_access,
        })
    
    return data

def _news_to_dict(news):
    """Convert news object to dictionary."""
    if not news:
        return None
    
    return {
        'id': news.id,
        'title': news.title,
        'content': news.content,
        'excerpt': news.excerpt or (news.content[:200] + '...' if news.content and len(news.content) > 200 else news.content),
        'category': {
            'id': news.category.id,
            'name': news.category.name,
        } if news.category else None,
        'author': _user_to_dict(news.user),
        'is_premium': news.is_premium,
        'is_news': news.is_news,
        'is_main_news': news.is_main_news,
        'is_visible': news.is_visible,
        'read_count': news.read_count,
        'share_count': news.share_count,
        'created_at': _safe_datetime(news.created_at),
        'updated_at': _safe_datetime(news.updated_at),
        'image': {
            'id': news.image.id,
            'url': news.image.file_url if hasattr(news.image, 'file_url') else None,
            'alt_text': news.image.alt_text,
        } if news.image else None,
    }

def _album_to_dict(album):
    """Convert album object to dictionary."""
    if not album:
        return None
    
    return {
        'id': album.id,
        'title': album.title,
        'description': album.description,
        'author': album.author,
        'category': {
            'id': album.category.id,
            'name': album.category.name,
        } if album.category else None,
        'is_premium': album.is_premium,
        'is_completed': album.is_completed,
        'is_hiatus': album.is_hiatus,
        'is_visible': album.is_visible,
        'total_chapters': album.total_chapters,
        'total_views': album.total_views,
        'created_at': _safe_datetime(album.created_at),
        'updated_at': _safe_datetime(album.updated_at),
        'cover_image': {
            'id': album.image.id,
            'url': album.image.file_url if hasattr(album.image, 'file_url') else None,
            'alt_text': album.image.alt_text,
        } if album.image else None,
    }

# =============================
# USER TRANSLATION ENDPOINTS
# =============================

@user_xlate_bp.route('/profile', methods=['GET'])
@login_required
def get_profile_xlate():
    """Translation endpoint for user profile (UI compatibility)."""
    try:
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'user': _user_to_dict(current_user),
            'profile': {
                'pronouns': profile.pronouns,
                'short_bio': profile.short_bio,
                'location': profile.location,
                'website': profile.website,
                'social_links': profile.social_links,
                'show_email': profile.show_email,
                'show_birthdate': profile.show_birthdate,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting profile xlate: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@user_xlate_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile_xlate():
    """Translation endpoint for updating user profile (UI compatibility)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update user fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'bio' in data:
            current_user.bio = data['bio']
        if 'birthdate' in data:
            if data['birthdate']:
                try:
                    current_user.birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid birthdate format'}), 400
            else:
                current_user.birthdate = None
        
        # Update profile fields
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)
        
        if 'pronouns' in data:
            profile.pronouns = data['pronouns']
        if 'short_bio' in data:
            profile.short_bio = data['short_bio']
        if 'location' in data:
            profile.location = data['location']
        if 'website' in data:
            profile.website = data['website']
        if 'social_links' in data:
            profile.social_links = data['social_links']
        if 'show_email' in data:
            profile.show_email = bool(data['show_email'])
        if 'show_birthdate' in data:
            profile.show_birthdate = bool(data['show_birthdate'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': _user_to_dict(current_user),
            'profile': {
                'pronouns': profile.pronouns,
                'short_bio': profile.short_bio,
                'location': profile.location,
                'website': profile.website,
                'social_links': profile.social_links,
                'show_email': profile.show_email,
                'show_birthdate': profile.show_birthdate,
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile xlate: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@user_xlate_bp.route('/stats', methods=['GET'])
@login_required
def get_stats_xlate():
    """Translation endpoint for user stats (UI compatibility)."""
    try:
        # Get or create user stats
        stats = UserStats.query.filter_by(user_id=current_user.id).first()
        if not stats:
            stats = UserStats(user_id=current_user.id)
            db.session.add(stats)
            db.session.commit()
        
        # Update stats
        stats.update_stats()
        db.session.commit()
        
        # Get content counts
        stories_count = News.query.filter_by(user_id=current_user.id).count()
        published_stories = News.query.filter_by(user_id=current_user.id, is_visible=True).count()
        draft_stories = News.query.filter_by(user_id=current_user.id, is_visible=False).count()
        
        albums_count = Album.query.filter_by(user_id=current_user.id).count()
        published_albums = Album.query.filter_by(user_id=current_user.id, is_visible=True).count()
        draft_albums = Album.query.filter_by(user_id=current_user.id, is_visible=False).count()
        
        images_count = Image.query.filter_by(user_id=current_user.id).count()
        
        library_count = UserLibrary.query.filter_by(user_id=current_user.id).count()
        history_count = ReadingHistory.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'user_id': stats.user_id,
                'total_stories': stories_count,
                'published_stories': published_stories,
                'draft_stories': draft_stories,
                'total_albums': albums_count,
                'published_albums': published_albums,
                'draft_albums': draft_albums,
                'total_images': images_count,
                'library_items': library_count,
                'reading_history_items': history_count,
                'total_views': stats.total_views,
                'total_likes': stats.total_likes,
                'total_comments': stats.total_comments,
                'total_shares': stats.total_shares,
                'created_at': _safe_datetime(stats.created_at),
                'updated_at': _safe_datetime(stats.updated_at),
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting stats xlate: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

@user_xlate_bp.route('/content/stories', methods=['GET'])
@login_required
def get_stories_xlate():
    """Translation endpoint for user stories (UI compatibility)."""
    try:
        status = request.args.get('status', 'all')  # all, published, draft
        
        query = News.query.filter_by(user_id=current_user.id)
        
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        stories = query.order_by(desc(News.created_at)).all()
        
        return jsonify({
            'success': True,
            'stories': [_news_to_dict(story) for story in stories],
            'filters': {
                'status': status,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting stories xlate: {e}")
        return jsonify({'error': 'Failed to get stories'}), 500

@user_xlate_bp.route('/content/albums', methods=['GET'])
@login_required
def get_albums_xlate():
    """Translation endpoint for user albums (UI compatibility)."""
    try:
        status = request.args.get('status', 'all')  # all, published, draft
        
        query = Album.query.filter_by(user_id=current_user.id)
        
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        albums = query.order_by(desc(Album.created_at)).all()
        
        return jsonify({
            'success': True,
            'albums': [_album_to_dict(album) for album in albums],
            'filters': {
                'status': status,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting albums xlate: {e}")
        return jsonify({'error': 'Failed to get albums'}), 500

@user_xlate_bp.route('/content/images', methods=['GET'])
@login_required
def get_images_xlate():
    """Translation endpoint for user images (UI compatibility)."""
    try:
        visibility = request.args.get('visibility', 'all')  # all, visible, hidden
        
        query = Image.query.filter_by(user_id=current_user.id)
        
        if visibility == 'visible':
            query = query.filter_by(is_visible=True)
        elif visibility == 'hidden':
            query = query.filter_by(is_visible=False)
        
        images = query.order_by(desc(Image.created_at)).all()
        
        image_list = []
        for img in images:
            image_list.append({
                'id': img.id,
                'filename': img.filename,
                'url': img.file_url if hasattr(img, 'file_url') else None,
                'description': img.description,
                'alt_text': img.alt_text,
                'is_visible': img.is_visible,
                'created_at': _safe_datetime(img.created_at),
                'updated_at': _safe_datetime(img.updated_at),
            })
        
        return jsonify({
            'success': True,
            'images': image_list,
            'filters': {
                'visibility': visibility,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting images xlate: {e}")
        return jsonify({'error': 'Failed to get images'}), 500

@user_xlate_bp.route('/library', methods=['GET'])
@login_required
def get_library_xlate():
    """Translation endpoint for user library (UI compatibility)."""
    try:
        content_type = request.args.get('type', 'all')  # all, news, album
        
        query = UserLibrary.query.filter_by(user_id=current_user.id)
        
        if content_type == 'news':
            query = query.filter_by(content_type='news')
        elif content_type == 'album':
            query = query.filter_by(content_type='album')
        
        library_items = query.order_by(desc(UserLibrary.added_at)).all()
        
        items = []
        for item in library_items:
            content_data = None
            if item.content_type == 'news':
                news = News.query.get(item.content_id)
                if news:
                    content_data = _news_to_dict(news)
            elif item.content_type == 'album':
                album = Album.query.get(item.content_id)
                if album:
                    content_data = _album_to_dict(album)
            
            if content_data:
                items.append({
                    'id': item.id,
                    'content_type': item.content_type,
                    'content_id': item.content_id,
                    'content': content_data,
                    'added_at': _safe_datetime(item.added_at),
                })
        
        return jsonify({
            'success': True,
            'library_items': items,
            'filters': {
                'type': content_type,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting library xlate: {e}")
        return jsonify({'error': 'Failed to get library'}), 500

@user_xlate_bp.route('/reading-history', methods=['GET'])
@login_required
def get_reading_history_xlate():
    """Translation endpoint for reading history (UI compatibility)."""
    try:
        content_type = request.args.get('type', 'all')  # all, news, album
        
        query = ReadingHistory.query.filter_by(user_id=current_user.id)
        
        if content_type == 'news':
            query = query.filter_by(content_type='news')
        elif content_type == 'album':
            query = query.filter_by(content_type='album')
        
        history_items = query.order_by(desc(ReadingHistory.last_read_at)).all()
        
        items = []
        for item in history_items:
            content_data = None
            if item.content_type == 'news':
                news = News.query.get(item.content_id)
                if news:
                    content_data = _news_to_dict(news)
            elif item.content_type == 'album':
                album = Album.query.get(item.content_id)
                if album:
                    content_data = _album_to_dict(album)
            
            if content_data:
                items.append({
                    'id': item.id,
                    'content_type': item.content_type,
                    'content_id': item.content_id,
                    'content': content_data,
                    'read_count': item.read_count,
                    'last_read_at': _safe_datetime(item.last_read_at),
                })
        
        return jsonify({
            'success': True,
            'history_items': items,
            'filters': {
                'type': content_type,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting reading history xlate: {e}")
        return jsonify({'error': 'Failed to get reading history'}), 500

@user_xlate_bp.route('/following', methods=['GET'])
@login_required
def get_following_xlate():
    """Translation endpoint for following list (UI compatibility)."""
    try:
        following = current_user.following.all()
        
        return jsonify({
            'success': True,
            'following': [_user_to_dict(user) for user in following]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting following xlate: {e}")
        return jsonify({'error': 'Failed to get following'}), 500

@user_xlate_bp.route('/followers', methods=['GET'])
@login_required
def get_followers_xlate():
    """Translation endpoint for followers list (UI compatibility)."""
    try:
        followers = current_user.followers.all()
        
        return jsonify({
            'success': True,
            'followers': [_user_to_dict(user) for user in followers]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting followers xlate: {e}")
        return jsonify({'error': 'Failed to get followers'}), 500

@user_xlate_bp.route('/write-access/status', methods=['GET'])
@login_required
def get_write_access_status_xlate():
    """Translation endpoint for write access status (UI compatibility)."""
    try:
        # Check if user has write access
        has_write_access = current_user.write_access or current_user.is_admin_tier()
        
        # Get pending request if any
        pending_request = WriteAccessRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        return jsonify({
            'success': True,
            'has_write_access': has_write_access,
            'pending_request': {
                'id': pending_request.id,
                'request_reason': pending_request.request_reason,
                'requested_at': _safe_datetime(pending_request.requested_at),
            } if pending_request else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting write access status xlate: {e}")
        return jsonify({'error': 'Failed to get write access status'}), 500

# =============================
# ADMIN TRANSLATION ENDPOINTS
# =============================

@user_xlate_bp.route('/admin/list', methods=['GET'])
@login_required
def get_users_admin_xlate():
    """Translation endpoint for admin user list (UI compatibility)."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        search = request.args.get('search', '').strip()
        role_filter = request.args.get('role', '').strip()
        status_filter = request.args.get('status', '').strip()
        verification_filter = request.args.get('verification', '').strip()
        
        query = User.query
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            ))
        
        if role_filter:
            try:
                query = query.filter(User.role == UserRole(role_filter))
            except ValueError:
                pass
        
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        elif status_filter == 'suspended':
            query = query.filter(User.is_suspended == True)
        
        if verification_filter == 'verified':
            query = query.filter(User.verified == True)
        elif verification_filter == 'unverified':
            query = query.filter(User.verified == False)
        
        users = query.order_by(desc(User.created_at)).all()
        
        return jsonify({
            'success': True,
            'users': [_user_to_dict(user, include_sensitive=True) for user in users],
            'filters': {
                'search': search,
                'role': role_filter,
                'status': status_filter,
                'verification': verification_filter,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting users admin xlate: {e}")
        return jsonify({'error': 'Failed to get users'}), 500

@user_xlate_bp.route('/admin/stats', methods=['GET'])
@login_required
def get_admin_stats_xlate():
    """Translation endpoint for admin user stats (UI compatibility)."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        # Get basic counts
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        premium_users = User.query.filter_by(is_premium=True).count()
        pending_users = User.query.filter_by(verified=False).count()
        
        # Get role distribution
        role_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        role_distribution = {role.value: count for role, count in role_counts}
        
        # Get recent registrations (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_registrations = User.query.filter(User.created_at >= thirty_days_ago).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'premium_users': premium_users,
                'pending_users': pending_users,
                'role_distribution': role_distribution,
                'recent_registrations': recent_registrations
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting admin stats xlate: {e}")
        return jsonify({'error': 'Failed to get admin stats'}), 500
