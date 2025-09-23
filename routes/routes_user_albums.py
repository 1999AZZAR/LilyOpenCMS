"""
Routes for User Album Management System
Handles CRUD operations for user's own albums
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, and_, desc, case, or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from urllib.parse import urlencode
import json
import logging

from models import db, Album, AlbumChapter, News, Category, User, UserRole
from routes.common_imports import *
from routes.utils.permission_decorators import (
    require_album_manage, require_album_create, require_album_edit, 
    require_album_delete, require_content_creation
)
from optimizations import cache_frontend_critical, cache_public_content, cache_user_dashboard

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
user_albums_bp = Blueprint('user_albums', __name__, url_prefix='/user/albums')

# =============================================================================
# USER ALBUM MANAGEMENT
# =============================================================================

@user_albums_bp.route('/')
@login_required
def list_albums():
    """List user's albums with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Build base query for user's albums only
        base_query = Album.query.filter(
            or_(
                Album.user_id == current_user.id,  # Albums created by user
                Album.owner_id == current_user.id   # Albums owned by user
            )
        )
        
        # Filters
        search = request.args.get('search', '').strip()
        if search:
            base_query = base_query.filter(Album.title.ilike(f'%{search}%'))
        
        category_id = request.args.get('category', type=int)
        if category_id:
            base_query = base_query.filter(Album.category_id == category_id)

        album_type = request.args.get('type', '')
        if album_type == 'premium':
            base_query = base_query.filter(Album.is_premium == True)
        elif album_type == 'regular':
            base_query = base_query.filter(Album.is_premium == False)

        # Build grouped lists (published vs draft). Archived albums are excluded from both groups here.
        published_albums = base_query.filter(Album.is_visible == True, Album.is_archived == False) \
            .order_by(Album.created_at.desc()).all()
        draft_albums = base_query.filter(Album.is_visible == False, Album.is_archived == False) \
            .order_by(Album.created_at.desc()).all()

        # Optional status filter narrows visible set shown in UI (tabs still computed above)
        status = request.args.get('status', '')
        if status == 'visible':
            draft_albums = []
        elif status == 'hidden':
            published_albums = []
        elif status == 'archived':
            # Show archived albums only (not grouped in tabs); compute separately
            archived_albums = base_query.filter(Album.is_archived == True) \
                .order_by(Album.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
            published_albums = []
            draft_albums = archived_albums.items

        total_albums = len(published_albums) + len(draft_albums)

        # Categories for filter dropdown
        categories = Category.query.all()
        
        # Build query string for pagination links
        query_params = {}
        if search:
            query_params['search'] = search
        if category_id:
            query_params['category'] = category_id
        if status:
            query_params['status'] = status
        if album_type:
            query_params['type'] = album_type
        query_string = urlencode(query_params)
        
        return render_template(
            'public/user/profile_list.html',
                             user=current_user,
            published_albums=published_albums,
            draft_albums=draft_albums,
                             categories=categories,
                             total_albums=total_albums,
                             page=page,
            total_pages=1,
            has_prev=False,
            has_next=False,
            prev_page=None,
            next_page=None,
            query_string=query_string,
        )
    
    except Exception as e:
        logger.error(f"Error listing user albums: {str(e)}")
        flash('Error loading albums', 'error')
        return redirect(url_for('user_profile.user_profile', username=current_user.username, tab='list'))


@user_albums_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_album():
    """Create a new album"""
    # Check if user has write access (same as story creation)
    if not current_user.is_admin_tier() and not current_user.write_access:
        flash('Write access required to create albums', 'error')
        return redirect(url_for('user_profile.write_access_request'))
    if request.method == 'GET':
        categories = Category.query.all()
        return render_template('public/user/album_form.html', 
                             album=None, 
                             action='create',
                             categories=categories)
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'success': False, 'message': 'Title is required'})
        
        # Normalize and validate age_rating
        age_rating = (data.get('age_rating') or '').strip()
        if age_rating:
            normalized = age_rating.upper().replace(' ', '')
            if normalized in {'R/13+','R13+'}:
                normalized = '13+'
            if normalized in {'D/17+','D17+'}:
                normalized = '17+'
            allowed = {"SU","P","A","3+","7+","13+","17+","18+","21+"}
            if normalized not in allowed:
                return jsonify({'success': False, 'message': f'Invalid age_rating: {age_rating}'}), 400
            age_rating = normalized

        # Create album
        album = Album(
            title=data['title'],
            description=data.get('description', ''),
            category_id=data.get('category_id'),
            user_id=current_user.id,  # Creator is always the current user
            owner_id=current_user.id,  # Owner is also the current user for user albums
            author=current_user.username,  # Set author to current user's username
            is_premium=data.get('is_premium', False),
            is_completed=data.get('is_completed', False),
            is_hiatus=data.get('is_hiatus', False),
            is_visible=data.get('is_visible', True),
            cover_image_id=data.get('cover_image_id'),
            age_rating=age_rating or None
        )
        
        db.session.add(album)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Album created successfully', 'album_id': album.id})
    
    except Exception as e:
        logger.error(f"Error creating album: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error creating album'})


@user_albums_bp.route('/<int:album_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_album(album_id):
    """Edit an existing album"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        flash('Access denied. You can only edit your own albums.', 'error')
        return redirect(url_for('user_albums.list_albums'))
    
    # Check if user has write access (same as story creation)
    if not current_user.is_admin_tier() and not current_user.write_access:
        flash('Write access required to edit albums', 'error')
        return redirect(url_for('user_profile.write_access_request'))
    
    if request.method == 'GET':
        categories = Category.query.all()
        return render_template('public/user/album_form.html', 
                             album=album, 
                             action='edit',
                             categories=categories)
    
    try:
        data = request.get_json()
        
        # Normalize and validate age_rating
        age_rating = (data.get('age_rating') or '').strip()
        if age_rating:
            normalized = age_rating.upper().replace(' ', '')
            if normalized in {'R/13+','R13+'}:
                normalized = '13+'
            if normalized in {'D/17+','D17+'}:
                normalized = '17+'
            allowed = {"SU","P","A","3+","7+","13+","17+","18+","21+"}
            if normalized not in allowed:
                return jsonify({'success': False, 'message': f'Invalid age_rating: {age_rating}'}), 400
            age_rating = normalized

        # Update album
        album.title = data.get('title', album.title)
        album.description = data.get('description', album.description)
        album.category_id = data.get('category_id', album.category_id)
        album.author = data.get('author', album.author)
        album.is_premium = data.get('is_premium', album.is_premium)
        album.is_completed = data.get('is_completed', album.is_completed)
        album.is_hiatus = data.get('is_hiatus', album.is_hiatus)
        album.is_visible = data.get('is_visible', album.is_visible)
        album.cover_image_id = data.get('cover_image_id', album.cover_image_id)
        album.age_rating = age_rating or None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Album updated successfully'})
    
    except Exception as e:
        logger.error(f"Error updating album: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating album'})


@user_albums_bp.route('/<int:album_id>')
@login_required
def album_detail(album_id):
    """View album details"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        flash('Access denied. You can only view your own albums.', 'error')
        return redirect(url_for('user_albums.list_albums'))
    
    # Get album chapters
    chapters = AlbumChapter.query.filter_by(album_id=album_id).order_by(AlbumChapter.chapter_number).all()
    
    return render_template('public/user/album_detail.html',
                         album=album,
                         chapters=chapters)


@user_albums_bp.route('/<int:album_id>/chapters')
@login_required
def album_chapters(album_id):
    """Manage album chapters"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        flash('Access denied. You can only manage your own albums.', 'error')
        return redirect(url_for('user_albums.list_albums'))
    
    # Get album chapters
    chapters = AlbumChapter.query.filter_by(album_id=album_id).order_by(AlbumChapter.chapter_number).all()
    
    # Build query for available articles (owned by the current user)
    news_query = News.query.filter(News.user_id == current_user.id)

    # Exclude articles already used as chapters in this album
    news_query = news_query.filter(~News.id.in_([c.news_id for c in chapters if c.news_id]))

    # Apply search filter
    search_query = request.args.get('search', '').strip()
    if search_query:
        news_query = news_query.filter(News.title.ilike(f'%{search_query}%'))

    # Apply category filter (by category name, matching admin behavior)
    category_filter = request.args.get('category', '').strip()
    if category_filter:
        news_query = news_query.join(Category, News.category_id == Category.id).filter(Category.name == category_filter)

    # Pagination params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    per_page = max(1, min(per_page, 100))

    # Execute pagination
    available_pagination = news_query.order_by(News.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    available_news = available_pagination.items

    # Categories for filter dropdown (only categories that have user's news)
    available_categories = (
        db.session.query(Category)
        .join(News, Category.id == News.category_id)
        .filter(News.user_id == current_user.id)
        .distinct()
        .all()
    )
    for category in available_categories:
        # Count user's news in this category
        category.news_count = News.query.filter(
            News.user_id == current_user.id,
            News.category_id == category.id
        ).count()

    return render_template(
        'public/user/album_chapters.html',
                         album=album,
                         chapters=chapters,
                         available_news=available_news,
        available_categories=available_categories,
        available_pagination=available_pagination,
    )


@user_albums_bp.route('/<int:album_id>/publish', methods=['POST'])
@login_required
def publish_album(album_id):
    """Publish a draft album"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        album.is_visible = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Album published successfully'})
    
    except Exception as e:
        logger.error(f"Error publishing album: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error publishing album'})


@user_albums_bp.route('/<int:album_id>/request-deletion', methods=['POST'])
@login_required
def request_album_deletion(album_id):
    """Request album deletion"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        album.deletion_requested = True
        album.deletion_requested_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Deletion request submitted successfully'})
    
    except Exception as e:
        logger.error(f"Error requesting album deletion: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error requesting deletion'})


@user_albums_bp.route('/<int:album_id>/toggle-visibility', methods=['POST'])
@login_required
def toggle_album_visibility(album_id):
    """Toggle album visibility"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        album.is_visible = not album.is_visible
        db.session.commit()
        
        status = 'visible' if album.is_visible else 'hidden'
        return jsonify({'success': True, 'message': f'Album is now {status}'})
    
    except Exception as e:
        logger.error(f"Error toggling album visibility: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating visibility'})


@user_albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/edit')
@login_required
def edit_chapter(album_id, chapter_id):
    """Edit a chapter (redirect to news edit page)"""
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if user owns this album and chapter
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        flash('Access denied. You can only edit your own albums.', 'error')
        return redirect(url_for('user_albums.list_albums'))
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        flash('Write access required to edit chapters', 'error')
        return redirect(url_for('user_profile.write_access_request'))
    
    if chapter.album_id != album_id:
        flash('Chapter not found in this album.', 'error')
        return redirect(url_for('user_albums.album_detail', album_id=album_id))
    
    # Redirect to the user story edit page for the associated article
    return redirect(url_for('user_profile.create_user_story', username=current_user.username, news_id=chapter.news_id))


@user_albums_bp.route('/<int:album_id>/chapters/add', methods=['POST'])
@login_required
def add_chapter(album_id):
    """Add a new chapter to an album"""
    album = Album.query.get_or_404(album_id)
    
    # Check if user owns this album
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('news_id') or not data.get('chapter_title') or not data.get('chapter_number'):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Check if the news article belongs to the user
        news = News.query.get(data['news_id'])
        if not news or news.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Article not found or access denied'})
        
        # Check if this article is already a chapter in this album
        existing = AlbumChapter.query.filter_by(album_id=album_id, news_id=data['news_id']).first()
        if existing:
            return jsonify({'success': False, 'message': 'This article is already a chapter in this album'})
        
        # Create new chapter
        chapter = AlbumChapter(
            album_id=album_id,
            news_id=data['news_id'],
            chapter_number=data['chapter_number'],
            chapter_title=data['chapter_title'],
            is_visible=True
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        # Update album's chapter count
        album = Album.query.get(album_id)
        if album:
            album.update_chapter_count()
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter added successfully'})
    
    except Exception as e:
        logger.error(f"Error adding chapter: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding chapter'})


@user_albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/edit', methods=['POST'])
@login_required
def edit_chapter_api(album_id, chapter_id):
    """Edit a chapter via API"""
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if user owns this album and chapter
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if chapter.album_id != album_id:
        return jsonify({'success': False, 'message': 'Chapter not found in this album'}), 404
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('chapter_title') or not data.get('chapter_number'):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Update chapter
        chapter.chapter_title = data['chapter_title']
        chapter.chapter_number = data['chapter_number']
        chapter.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter updated successfully'})
    
    except Exception as e:
        logger.error(f"Error updating chapter: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating chapter'})


@user_albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/remove', methods=['POST'])
@login_required
def remove_chapter(album_id, chapter_id):
    """Remove a chapter from an album"""
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if user owns this album and chapter
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if chapter.album_id != album_id:
        return jsonify({'success': False, 'message': 'Chapter not found in this album'}), 404
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        album_id = chapter.album_id
        db.session.delete(chapter)
        db.session.commit()
        
        # Update album's chapter count
        album = Album.query.get(album_id)
        if album:
            album.update_chapter_count()
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter removed successfully'})
    
    except Exception as e:
        logger.error(f"Error removing chapter: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error removing chapter'})


@user_albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/toggle-visibility', methods=['POST'])
@login_required
def toggle_chapter_visibility(album_id, chapter_id):
    """Toggle chapter visibility"""
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if user owns this album and chapter
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if chapter.album_id != album_id:
        return jsonify({'success': False, 'message': 'Chapter not found in this album'}), 404
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        data = request.get_json()
        chapter.is_visible = data.get('is_visible', not chapter.is_visible)
        chapter.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = 'visible' if chapter.is_visible else 'hidden'
        return jsonify({'success': True, 'message': f'Chapter is now {status}'})
    
    except Exception as e:
        logger.error(f"Error toggling chapter visibility: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating chapter visibility'})


@user_albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/move', methods=['POST'])
@login_required
def move_chapter(album_id, chapter_id):
    """Move a chapter up or down in order"""
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if user owns this album and chapter
    if not (album.user_id == current_user.id or album.owner_id == current_user.id):
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    if chapter.album_id != album_id:
        return jsonify({'success': False, 'message': 'Chapter not found in this album'}), 404
    
    # Check if user has write access
    if not current_user.is_admin_tier() and not current_user.write_access:
        return jsonify({'success': False, 'message': 'Write access required'}), 403
    
    try:
        data = request.get_json()
        direction = data.get('direction')
        
        if direction == 'up':
            # Find the previous chapter
            prev_chapter = AlbumChapter.query.filter_by(album_id=album_id).filter(
                AlbumChapter.chapter_number < chapter.chapter_number
            ).order_by(desc(AlbumChapter.chapter_number)).first()
            
            if prev_chapter:
                # Swap chapter numbers
                temp_number = chapter.chapter_number
                chapter.chapter_number = prev_chapter.chapter_number
                prev_chapter.chapter_number = temp_number
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Chapter moved up'})
            else:
                return jsonify({'success': False, 'message': 'Chapter is already at the top'})
        
        elif direction == 'down':
            # Find the next chapter
            next_chapter = AlbumChapter.query.filter_by(album_id=album_id).filter(
                AlbumChapter.chapter_number > chapter.chapter_number
            ).order_by(AlbumChapter.chapter_number).first()
            
            if next_chapter:
                # Swap chapter numbers
                temp_number = chapter.chapter_number
                chapter.chapter_number = next_chapter.chapter_number
                next_chapter.chapter_number = temp_number
                
                db.session.commit()
                return jsonify({'success': True, 'message': 'Chapter moved down'})
            else:
                return jsonify({'success': False, 'message': 'Chapter is already at the bottom'})
        
        else:
            return jsonify({'success': False, 'message': 'Invalid direction'})
    
    except Exception as e:
        logger.error(f"Error moving chapter: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error moving chapter'})
