from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import desc, or_, and_, func
from models import db, User, UserProfile, UserStats, News, Album, AlbumChapter, Image, Category, UserLibrary, ReadingHistory, Comment, UserRole, CustomRole, WriteAccessRequest, UserActivity
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash
import json

# Create blueprint for user APIs
user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/user')

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

def _check_permission(user, action, resource=None):
    """Check if user has permission for action."""
    if not user:
        return False
    
    # Admin tier users have all permissions
    if user.is_admin_tier():
        return True
    
    # Check specific permissions
    if action == 'view_own_profile':
        return True
    elif action == 'edit_own_profile':
        return True
    elif action == 'create_content':
        return user.write_access or user.is_admin_tier()
    elif action == 'manage_own_content':
        return True
    elif action == 'view_user_stats':
        return True
    
    return False

# =============================
# USER MANAGEMENT APIs
# =============================

@user_api_bp.route('/list', methods=['GET'])
@login_required
def list_users():
    """List users with pagination and filtering (admin only)."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
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
        
        # Pagination
        pagination = query.order_by(desc(User.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = [_user_to_dict(user, include_sensitive=True) for user in pagination.items]
        
        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'search': search,
                'role': role_filter,
                'status': status_filter,
                'verification': verification_filter,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing users: {e}")
        return jsonify({'error': 'Failed to list users'}), 500

@user_api_bp.route('/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Get user details."""
    user = User.query.get_or_404(user_id)
    
    # Check permissions
    if not current_user.is_admin_tier() and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    include_sensitive = current_user.is_admin_tier()
    
    return jsonify({
        'success': True,
        'user': _user_to_dict(user, include_sensitive=include_sensitive)
    })

@user_api_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Update user information."""
    user = User.query.get_or_404(user_id)
    
    # Check permissions
    if not current_user.is_admin_tier() and current_user.id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update basic fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'bio' in data:
            user.bio = data['bio']
        if 'birthdate' in data:
            if data['birthdate']:
                try:
                    user.birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid birthdate format'}), 400
            else:
                user.birthdate = None
        
        # Admin-only fields
        if current_user.is_admin_tier():
            if 'email' in data:
                user.email = data['email']
            if 'role' in data:
                try:
                    user.role = UserRole(data['role'])
                except ValueError:
                    return jsonify({'error': 'Invalid role'}), 400
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            if 'verified' in data:
                user.verified = bool(data['verified'])
            if 'is_premium' in data:
                user.is_premium = bool(data['is_premium'])
            if 'write_access' in data:
                user.write_access = bool(data['write_access'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': _user_to_dict(user, include_sensitive=current_user.is_admin_tier())
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({'error': 'Failed to update user'}), 500

@user_api_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """Delete user (admin only)."""
    if not current_user.is_admin_tier():
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Cannot delete superusers unless you are a superuser
    if user.role == UserRole.SUPERUSER and not current_user.is_owner():
        return jsonify({'error': 'Cannot delete superuser'}), 403
    
    # Cannot delete yourself
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 403
    
    try:
        # Transfer owned content to current admin
        transfer_user_id = current_user.id
        
        # Update ownership of content
        News.query.filter_by(user_id=user_id).update({'user_id': transfer_user_id})
        Album.query.filter_by(user_id=user_id).update({'user_id': transfer_user_id})
        Image.query.filter_by(user_id=user_id).update({'user_id': transfer_user_id})
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

# =============================
# USER PROFILE APIs
# =============================

@user_api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile."""
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

@user_api_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update current user's profile."""
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
        current_app.logger.error(f"Error updating profile: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@user_api_bp.route('/profile/username', methods=['PATCH'])
@login_required
def change_username():
    """Change username."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        new_username = data.get('username', '').strip()
        current_password = data.get('current_password', '')
        
        if not new_username or not current_password:
            return jsonify({'error': 'Username and current password are required'}), 400
        
        # Validate username format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', new_username):
            return jsonify({'error': 'Username must be 3-20 characters long and can only contain letters, numbers, underscores, and hyphens'}), 400
        
        # Check if username is already taken
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'error': 'Username already in use'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update username
        old_username = current_user.username
        current_user.username = new_username
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Username updated successfully',
            'old_username': old_username,
            'new_username': new_username,
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing username: {e}")
        return jsonify({'error': 'Failed to change username'}), 500

@user_api_bp.route('/profile/password', methods=['PATCH'])
@login_required
def change_password():
    """Change password."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Failed to change password'}), 500

# =============================
# USER CONTENT APIs
# =============================

@user_api_bp.route('/content/stories', methods=['GET'])
@login_required
def get_user_stories():
    """Get user's stories."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', 'all')  # all, published, draft
        
        query = News.query.filter_by(user_id=current_user.id)
        
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        pagination = query.order_by(desc(News.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        stories = [_news_to_dict(story) for story in pagination.items]
        
        return jsonify({
            'success': True,
            'stories': stories,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'status': status,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user stories: {e}")
        return jsonify({'error': 'Failed to get stories'}), 500

@user_api_bp.route('/content/albums', methods=['GET'])
@login_required
def get_user_albums():
    """Get user's albums."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', 'all')  # all, published, draft
        
        query = Album.query.filter_by(user_id=current_user.id)
        
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        pagination = query.order_by(desc(Album.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        albums = [_album_to_dict(album) for album in pagination.items]
        
        return jsonify({
            'success': True,
            'albums': albums,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'status': status,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user albums: {e}")
        return jsonify({'error': 'Failed to get albums'}), 500

@user_api_bp.route('/content/images', methods=['GET'])
@login_required
def get_user_images():
    """Get user's images."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        visibility = request.args.get('visibility', 'all')  # all, visible, hidden
        
        query = Image.query.filter_by(user_id=current_user.id)
        
        if visibility == 'visible':
            query = query.filter_by(is_visible=True)
        elif visibility == 'hidden':
            query = query.filter_by(is_visible=False)
        
        pagination = query.order_by(desc(Image.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        images = []
        for img in pagination.items:
            images.append({
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
            'images': images,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'visibility': visibility,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user images: {e}")
        return jsonify({'error': 'Failed to get images'}), 500

# =============================
# USER LIBRARY APIs
# =============================

@user_api_bp.route('/library', methods=['GET'])
@login_required
def get_library():
    """Get user's library (saved content)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        content_type = request.args.get('type', 'all')  # all, news, album
        
        query = UserLibrary.query.filter_by(user_id=current_user.id)
        
        if content_type == 'news':
            query = query.filter_by(content_type='news')
        elif content_type == 'album':
            query = query.filter_by(content_type='album')
        
        pagination = query.order_by(desc(UserLibrary.added_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        library_items = []
        for item in pagination.items:
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
                library_items.append({
                    'id': item.id,
                    'content_type': item.content_type,
                    'content_id': item.content_id,
                    'content': content_data,
                    'added_at': _safe_datetime(item.added_at),
                })
        
        return jsonify({
            'success': True,
            'library_items': library_items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'type': content_type,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting library: {e}")
        return jsonify({'error': 'Failed to get library'}), 500

@user_api_bp.route('/library', methods=['POST'])
@login_required
def add_to_library():
    """Add content to library."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        
        if not content_type or not content_id:
            return jsonify({'error': 'content_type and content_id are required'}), 400
        
        if content_type not in ['news', 'album']:
            return jsonify({'error': 'Invalid content_type'}), 400
        
        # Check if already in library
        existing = UserLibrary.query.filter_by(
            user_id=current_user.id,
            content_type=content_type,
            content_id=content_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Content already in library'}), 400
        
        # Add to library
        library_item = UserLibrary(
            user_id=current_user.id,
            content_type=content_type,
            content_id=content_id
        )
        
        db.session.add(library_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Added to library successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding to library: {e}")
        return jsonify({'error': 'Failed to add to library'}), 500

@user_api_bp.route('/library/<int:item_id>', methods=['DELETE'])
@login_required
def remove_from_library(item_id):
    """Remove content from library."""
    try:
        library_item = UserLibrary.query.filter_by(
            id=item_id,
            user_id=current_user.id
        ).first()
        
        if not library_item:
            return jsonify({'error': 'Library item not found'}), 404
        
        db.session.delete(library_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Removed from library successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing from library: {e}")
        return jsonify({'error': 'Failed to remove from library'}), 500

@user_api_bp.route('/reading-history', methods=['GET'])
@login_required
def get_reading_history():
    """Get user's reading history."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        content_type = request.args.get('type', 'all')  # all, news, album
        
        query = ReadingHistory.query.filter_by(user_id=current_user.id)
        
        if content_type == 'news':
            query = query.filter_by(content_type='news')
        elif content_type == 'album':
            query = query.filter_by(content_type='album')
        
        pagination = query.order_by(desc(ReadingHistory.last_read_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        history_items = []
        for item in pagination.items:
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
                history_items.append({
                    'id': item.id,
                    'content_type': item.content_type,
                    'content_id': item.content_id,
                    'content': content_data,
                    'read_count': item.read_count,
                    'last_read_at': _safe_datetime(item.last_read_at),
                })
        
        return jsonify({
            'success': True,
            'history_items': history_items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
            'filters': {
                'type': content_type,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting reading history: {e}")
        return jsonify({'error': 'Failed to get reading history'}), 500

# =============================
# USER STATISTICS APIs
# =============================

@user_api_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics."""
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
        
        # Get recent activity
        recent_activities = UserActivity.query.filter_by(user_id=current_user.id)\
            .order_by(desc(UserActivity.created_at))\
            .limit(10).all()
        
        activities = []
        for activity in recent_activities:
            activities.append({
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'created_at': _safe_datetime(activity.created_at),
            })
        
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
            },
            'recent_activities': activities
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user stats: {e}")
        return jsonify({'error': 'Failed to get user stats'}), 500

# =============================
# USER SOCIAL APIs
# =============================

@user_api_bp.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    """Follow or unfollow a user."""
    if current_user.id == user_id:
        return jsonify({'error': 'You cannot follow yourself'}), 400
    
    user_to_follow = User.query.get(user_id)
    if not user_to_follow:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already following
    is_following = current_user.following.filter_by(id=user_id).first() is not None
    
    if is_following:
        # Unfollow
        current_user.following.remove(user_to_follow)
        action = 'unfollowed'
    else:
        # Follow
        current_user.following.append(user_to_follow)
        action = 'followed'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'action': action,
        'follower_count': user_to_follow.followers.count()
    })

@user_api_bp.route('/following', methods=['GET'])
@login_required
def get_following():
    """Get users that current user is following."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = current_user.following.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        following = [_user_to_dict(user) for user in pagination.items]
        
        return jsonify({
            'success': True,
            'following': following,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting following: {e}")
        return jsonify({'error': 'Failed to get following'}), 500

@user_api_bp.route('/followers', methods=['GET'])
@login_required
def get_followers():
    """Get users that follow current user."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = current_user.followers.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        followers = [_user_to_dict(user) for user in pagination.items]
        
        return jsonify({
            'success': True,
            'followers': followers,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting followers: {e}")
        return jsonify({'error': 'Failed to get followers'}), 500

# =============================
# USER WRITE ACCESS APIs
# =============================

@user_api_bp.route('/write-access/request', methods=['POST'])
@login_required
def request_write_access():
    """Request write access."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        reason = data.get('reason', '').strip()
        if not reason:
            return jsonify({'error': 'Reason is required'}), 400
        
        # Check if user already has write access
        if current_user.write_access:
            return jsonify({'error': 'You already have write access'}), 400
        
        # Check if user already has a pending request
        existing_request = WriteAccessRequest.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_request:
            return jsonify({'error': 'You already have a pending request'}), 400
        
        # Create new request
        new_request = WriteAccessRequest(
            user_id=current_user.id,
            request_reason=reason,
            portfolio_links=data.get('portfolio_links', ''),
            experience_description=data.get('experience', '')
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Write access request submitted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting write access: {e}")
        return jsonify({'error': 'Failed to submit request'}), 500

@user_api_bp.route('/write-access/status', methods=['GET'])
@login_required
def get_write_access_status():
    """Get write access status."""
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
        current_app.logger.error(f"Error getting write access status: {e}")
        return jsonify({'error': 'Failed to get write access status'}), 500

# =============================
# USER ACCOUNT MANAGEMENT APIs
# =============================

@user_api_bp.route('/account/delete', methods=['POST'])
@login_required
def request_account_deletion():
    """Request account deletion."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        password = data.get('password', '')
        if not password:
            return jsonify({'error': 'Password is required'}), 400
        
        # Verify password
        if not current_user.check_password(password):
            return jsonify({'error': 'Incorrect password'}), 400
        
        # Check if user is admin tier
        if current_user.is_admin_tier():
            return jsonify({'error': 'Admin accounts cannot be deleted through this endpoint'}), 403
        
        # Set user to inactive and mark for deletion
        current_user.is_active = False
        current_user.deletion_requested_at = datetime.utcnow()
        current_user.deletion_requested = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account deletion request submitted successfully. Your account has been deactivated and is pending admin approval.'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error requesting account deletion: {e}")
        return jsonify({'error': 'Failed to submit deletion request'}), 500

# =============================
# TRANSLATION ENDPOINTS FOR UI COMPATIBILITY
# =============================

@user_api_bp.route('/xlate/profile', methods=['GET'])
@login_required
def xlate_profile():
    """Translation endpoint for profile data (UI compatibility)."""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    return jsonify({
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

@user_api_bp.route('/xlate/stats', methods=['GET'])
@login_required
def xlate_stats():
    """Translation endpoint for user stats (UI compatibility)."""
    stats = UserStats.query.filter_by(user_id=current_user.id).first()
    if not stats:
        stats = UserStats(user_id=current_user.id)
        db.session.add(stats)
        db.session.commit()
    
    stats.update_stats()
    db.session.commit()
    
    return jsonify({
        'stats': {
            'user_id': stats.user_id,
            'total_views': stats.total_views,
            'total_likes': stats.total_likes,
            'total_comments': stats.total_comments,
            'total_shares': stats.total_shares,
            'created_at': _safe_datetime(stats.created_at),
            'updated_at': _safe_datetime(stats.updated_at),
        }
    })

@user_api_bp.route('/xlate/content', methods=['GET'])
@login_required
def xlate_content():
    """Translation endpoint for user content (UI compatibility)."""
    content_type = request.args.get('type', 'stories')
    status = request.args.get('status', 'all')
    
    if content_type == 'stories':
        query = News.query.filter_by(user_id=current_user.id)
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        items = query.order_by(desc(News.created_at)).all()
        return jsonify({
            'stories': [_news_to_dict(story) for story in items]
        })
    
    elif content_type == 'albums':
        query = Album.query.filter_by(user_id=current_user.id)
        if status == 'published':
            query = query.filter_by(is_visible=True)
        elif status == 'draft':
            query = query.filter_by(is_visible=False)
        
        items = query.order_by(desc(Album.created_at)).all()
        return jsonify({
            'albums': [_album_to_dict(album) for album in items]
        })
    
    return jsonify({'error': 'Invalid content type'}), 400
