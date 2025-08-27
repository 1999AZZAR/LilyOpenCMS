"""
Routes for Albums Management System
Handles CRUD operations for albums, chapters, and analytics
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import func, and_, desc, case
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from urllib.parse import urlencode
import json
import logging

from models import db, Album, AlbumChapter, News, Category, User, UserRole
from routes.common_imports import *

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
albums_bp = Blueprint('albums', __name__, url_prefix='/admin/albums')

# Admin check function
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin_tier():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.settings_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# DASHBOARD
# =============================================================================

@albums_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Album management dashboard with overview stats and quick actions"""
    try:
        # Get basic stats
        total_albums = Album.query.count()
        visible_albums = Album.query.filter_by(is_visible=True).count()
        premium_albums = Album.query.filter_by(is_premium=True).count()
        
        # Get chapter stats
        total_chapters = db.session.query(func.count(AlbumChapter.id)).scalar()
        
        # Get album status stats
        completed_albums = Album.query.filter_by(is_completed=True).count()
        hiatus_albums = Album.query.filter_by(is_hiatus=True).count()
        archived_albums = Album.query.filter_by(is_archived=True).count()
        
        # Calculate average chapters per album
        avg_chapters_per_album = total_chapters / total_albums if total_albums > 0 else 0
        
        # Get recent albums
        recent_albums = Album.query.order_by(Album.created_at.desc()).limit(10).all()
        
        # Get category stats
        category_stats = db.session.query(
            Category.name,
            func.count(Album.id).label('count')
        ).join(Album, Category.id == Album.category_id)\
         .group_by(Category.id, Category.name)\
         .order_by(desc('count'))\
         .limit(10).all()
        
        # Get recent activities (simplified for now)
        recent_activities = [
            {
                'icon': 'plus',
                'message': f'Album "{recent_albums[0].title}" created' if recent_albums else 'No recent activity',
                'timestamp': '2 hours ago'
            }
        ]
        
        return render_template('admin/albums/dashboard.html',
                             total_albums=total_albums,
                             visible_albums=visible_albums,
                             premium_albums=premium_albums,
                             total_chapters=total_chapters,
                             completed_albums=completed_albums,
                             hiatus_albums=hiatus_albums,
                             archived_albums=archived_albums,
                             avg_chapters_per_album=avg_chapters_per_album,
                             recent_albums=recent_albums,
                             category_stats=category_stats,
                             recent_activities=recent_activities)
    
    except Exception as e:
        logger.error(f"Error loading album dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin.dashboard'))


# =============================================================================
# ALBUMS LIST
# =============================================================================

@albums_bp.route('/list')
@login_required
@admin_required
def list_albums():
    """List all albums with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Build query with filters
        query = Album.query
        
        # Search filter
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(Album.title.ilike(f'%{search}%'))
        
        # Category filter
        category_id = request.args.get('category', type=int)
        if category_id:
            query = query.filter(Album.category_id == category_id)
        
        # Status filter
        status = request.args.get('status', '')
        if status == 'visible':
            query = query.filter(Album.is_visible == True)
        elif status == 'hidden':
            query = query.filter(Album.is_visible == False)
        elif status == 'archived':
            query = query.filter(Album.is_archived == True)
        
        # Type filter
        album_type = request.args.get('type', '')
        if album_type == 'premium':
            query = query.filter(Album.is_premium == True)
        elif album_type == 'regular':
            query = query.filter(Album.is_premium == False)
        
        # Get total count for pagination
        total_albums = query.count()
        
        # Paginate results
        albums = query.order_by(Album.created_at.desc())\
                     .offset((page - 1) * per_page)\
                     .limit(per_page)\
                     .all()
        
        # Get categories for filter dropdown
        categories = Category.query.order_by(Category.name).all()
        
        # Calculate pagination info
        total_pages = (total_albums + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        prev_page = page - 1 if has_prev else None
        next_page = page + 1 if has_next else None
        
        # Build query string for pagination links (preserve filters, replace page only)
        current_params = request.args.to_dict(flat=True)
        if 'page' in current_params:
            current_params.pop('page')
        query_string = urlencode(current_params)

        return render_template('admin/albums/list.html',
                             albums=albums,
                             categories=categories,
                             total_albums=total_albums,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             has_prev=has_prev,
                             has_next=has_next,
                             prev_page=prev_page,
                             next_page=next_page,
                             query_string=query_string)
    
    except Exception as e:
        logger.error(f"Error loading albums list: {e}")
        flash('Error loading albums', 'error')
        return redirect(url_for('albums.dashboard'))


# =============================================================================
# ALBUM DETAIL
# =============================================================================

@albums_bp.route('/<int:album_id>')
@login_required
@admin_required
def album_detail(album_id):
    """Detailed view of a single album"""
    try:
        album = Album.query.get_or_404(album_id)
        
        # Get chapters with news information
        chapters = AlbumChapter.query.filter_by(album_id=album_id)\
                                   .order_by(AlbumChapter.chapter_number)\
                                   .all()
        
        # Get recent activities (simplified)
        recent_activities = [
            {
                'icon': 'edit',
                'message': f'Album "{album.title}" updated',
                'timestamp': '1 hour ago'
            }
        ]
        
        return render_template('admin/albums/detail.html',
                             album=album,
                             chapters=chapters,
                             recent_activities=recent_activities)
    
    except Exception as e:
        logger.error(f"Error loading album detail: {e}")
        flash('Error loading album details', 'error')
        return redirect(url_for('albums.list_albums'))


# =============================================================================
# ALBUM CRUD
# =============================================================================

@albums_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_album():
    """Create a new album"""
    if request.method == 'GET':
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/albums/form.html', 
                             album=None, 
                             categories=categories,
                             action='create')
    
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
            user_id=current_user.id,
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
        logger.error(f"Error creating album: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error creating album'})


@albums_bp.route('/<int:album_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_album(album_id):
    """Edit an existing album"""
    album = Album.query.get_or_404(album_id)
    
    if request.method == 'GET':
        categories = Category.query.order_by(Category.name).all()
        return render_template('admin/albums/form.html', 
                             album=album, 
                             categories=categories,
                             action='edit')
    
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
        album.is_premium = data.get('is_premium', album.is_premium)
        album.is_completed = data.get('is_completed', album.is_completed)
        album.is_hiatus = data.get('is_hiatus', album.is_hiatus)
        album.is_visible = data.get('is_visible', album.is_visible)
        album.cover_image_id = data.get('cover_image_id', album.cover_image_id)
        if age_rating:
            album.age_rating = age_rating
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Album updated successfully'})
    
    except Exception as e:
        logger.error(f"Error updating album: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating album'})


@albums_bp.route('/<int:album_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_album(album_id):
    """Delete an album"""
    try:
        album = Album.query.get_or_404(album_id)
        
        # Delete associated chapters first
        AlbumChapter.query.filter_by(album_id=album_id).delete()
        
        # Delete album
        db.session.delete(album)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Album deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting album: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error deleting album'})


# =============================================================================
# ALBUM ACTIONS
# =============================================================================

@albums_bp.route('/<int:album_id>/toggle-visibility', methods=['POST'])
@login_required
@admin_required
def toggle_album_visibility(album_id):
    """Toggle album visibility"""
    try:
        album = Album.query.get_or_404(album_id)
        album.is_visible = not album.is_visible
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Visibility updated successfully'})
    
    except Exception as e:
        logger.error(f"Error toggling album visibility: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating visibility'})


@albums_bp.route('/<int:album_id>/toggle-type', methods=['POST'])
@login_required
@admin_required
def toggle_album_type(album_id):
    """Toggle album premium status"""
    try:
        album = Album.query.get_or_404(album_id)
        album.is_premium = not album.is_premium
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Type updated successfully'})
    
    except Exception as e:
        logger.error(f"Error toggling album type: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating type'})


@albums_bp.route('/<int:album_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_album(album_id):
    """Archive/unarchive an album"""
    try:
        album = Album.query.get_or_404(album_id)
        album.is_archived = not album.is_archived
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Archive status updated successfully'})
    
    except Exception as e:
        logger.error(f"Error archiving album: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating archive status'})


# =============================================================================
# BULK ACTIONS
# =============================================================================

@albums_bp.route('/bulk/toggle-visibility', methods=['POST'])
@login_required
@admin_required
def bulk_toggle_visibility():
    """Bulk toggle album visibility"""
    try:
        data = request.get_json()
        album_ids = data.get('album_ids', [])
        
        albums = Album.query.filter(Album.id.in_(album_ids)).all()
        for album in albums:
            album.is_visible = not album.is_visible
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Updated {len(albums)} albums'})
    
    except Exception as e:
        logger.error(f"Error bulk toggling visibility: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating albums'})


@albums_bp.route('/bulk/toggle-type', methods=['POST'])
@login_required
@admin_required
def bulk_toggle_type():
    """Bulk toggle album premium status"""
    try:
        data = request.get_json()
        album_ids = data.get('album_ids', [])
        
        albums = Album.query.filter(Album.id.in_(album_ids)).all()
        for album in albums:
            album.is_premium = not album.is_premium
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Updated {len(albums)} albums'})
    
    except Exception as e:
        logger.error(f"Error bulk toggling type: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating albums'})


@albums_bp.route('/bulk/archive', methods=['POST'])
@login_required
@admin_required
def bulk_archive():
    """Bulk archive albums"""
    try:
        data = request.get_json()
        album_ids = data.get('album_ids', [])
        
        albums = Album.query.filter(Album.id.in_(album_ids)).all()
        for album in albums:
            album.is_archived = True
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Archived {len(albums)} albums'})
    
    except Exception as e:
        logger.error(f"Error bulk archiving: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error archiving albums'})


# =============================================================================
# CHAPTERS MANAGEMENT
# =============================================================================

@albums_bp.route('/<int:album_id>/chapters')
@login_required
@admin_required
def manage_chapters(album_id):
    """Manage chapters for a specific album"""
    try:
        album = Album.query.get_or_404(album_id)
        # Ensure the chapters relationship is loaded
        chapters = album.chapters
        
        # Get available news articles for adding as chapters
        available_news = News.query.filter_by(is_visible=True)\
                                  .filter(~News.id.in_([c.news_id for c in chapters if c.news_id]))\
                                  .order_by(News.created_at.desc())\
                                  .limit(50).all()
        
        return render_template('admin/albums/chapters.html',
                             album=album,
                             chapters=chapters,
                             available_news=available_news)
    
    except Exception as e:
        logger.error(f"Error loading chapters management: {e}")
        flash('Error loading chapters', 'error')
        return redirect(url_for('albums.list_albums'))


@albums_bp.route('/<int:album_id>/chapters/add', methods=['POST'])
@login_required
@admin_required
def add_chapter(album_id):
    """Add a chapter to an album"""
    try:
        data = request.get_json()
        news_id = data.get('news_id')
        chapter_title = data.get('chapter_title')
        chapter_number = data.get('chapter_number')
        
        if not all([news_id, chapter_title, chapter_number]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Check if chapter number already exists
        existing = AlbumChapter.query.filter_by(
            album_id=album_id, 
            chapter_number=chapter_number
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Chapter number already exists'})
        
        # Create chapter
        chapter = AlbumChapter(
            album_id=album_id,
            news_id=news_id,
            chapter_title=chapter_title,
            chapter_number=chapter_number
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        # Update album's total_chapters count
        album = Album.query.get(album_id)
        if album:
            # Refresh the album to ensure we have the latest data
            db.session.refresh(album)
            album.update_chapter_count()
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter added successfully'})
    
    except Exception as e:
        logger.error(f"Error adding chapter: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error adding chapter'})


@albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_chapter(album_id, chapter_id):
    """Edit a chapter"""
    try:
        data = request.get_json()
        chapter_title = data.get('chapter_title')
        chapter_number = data.get('chapter_number')
        
        if not all([chapter_title, chapter_number]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        chapter = AlbumChapter.query.filter_by(
            album_id=album_id, 
            id=chapter_id
        ).first_or_404()
        
        # Check if new chapter number conflicts
        existing = AlbumChapter.query.filter_by(
            album_id=album_id, 
            chapter_number=chapter_number
        ).filter(AlbumChapter.id != chapter_id).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Chapter number already exists'})
        
        # Update chapter
        chapter.chapter_title = chapter_title
        chapter.chapter_number = chapter_number
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter updated successfully'})
    
    except Exception as e:
        logger.error(f"Error editing chapter: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating chapter'})


@albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_chapter(album_id, chapter_id):
    """Remove a chapter from an album"""
    try:
        chapter = AlbumChapter.query.filter_by(
            album_id=album_id, 
            id=chapter_id
        ).first_or_404()
        
        db.session.delete(chapter)
        db.session.commit()
        
        # Update album's total_chapters count
        album = Album.query.get(album_id)
        if album:
            # Refresh the album to ensure we have the latest data
            db.session.refresh(album)
            album.update_chapter_count()
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Chapter removed successfully'})
    
    except Exception as e:
        logger.error(f"Error removing chapter: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error removing chapter'})


@albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/move', methods=['POST'])
@login_required
@admin_required
def move_chapter(album_id, chapter_id):
    """Move a chapter up or down in order"""
    try:
        data = request.get_json()
        direction = data.get('direction')
        
        if direction not in ['up', 'down']:
            return jsonify({'success': False, 'message': 'Invalid direction'})
        
        chapter = AlbumChapter.query.filter_by(
            album_id=album_id, 
            id=chapter_id
        ).first_or_404()
        
        if direction == 'up':
            # Find the previous chapter
            prev_chapter = AlbumChapter.query.filter_by(
                album_id=album_id
            ).filter(
                AlbumChapter.chapter_number < chapter.chapter_number
            ).order_by(desc(AlbumChapter.chapter_number)).first()
            
            if prev_chapter:
                # Swap chapter numbers
                temp_number = chapter.chapter_number
                chapter.chapter_number = prev_chapter.chapter_number
                prev_chapter.chapter_number = temp_number
                db.session.commit()
                return jsonify({'success': True, 'message': 'Chapter moved up successfully'})
            else:
                return jsonify({'success': False, 'message': 'Chapter is already at the top'})
        
        else:  # down
            # Find the next chapter
            next_chapter = AlbumChapter.query.filter_by(
                album_id=album_id
            ).filter(
                AlbumChapter.chapter_number > chapter.chapter_number
            ).order_by(AlbumChapter.chapter_number).first()
            
            if next_chapter:
                # Swap chapter numbers
                temp_number = chapter.chapter_number
                chapter.chapter_number = next_chapter.chapter_number
                next_chapter.chapter_number = temp_number
                db.session.commit()
                return jsonify({'success': True, 'message': 'Chapter moved down successfully'})
            else:
                return jsonify({'success': False, 'message': 'Chapter is already at the bottom'})
    
    except Exception as e:
        logger.error(f"Error moving chapter: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error moving chapter'})


# =============================================================================
# ANALYTICS
# =============================================================================

@albums_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """Album analytics dashboard"""
    try:
        # Get basic analytics
        total_albums = Album.query.count()
        total_chapters = db.session.query(func.count(AlbumChapter.id)).scalar()
        total_views = db.session.query(func.sum(Album.total_views)).scalar() or 0
        total_reads = db.session.query(func.sum(Album.total_reads)).scalar() or 0
        
        # Get top performing albums
        top_albums = Album.query.order_by(desc(Album.total_reads)).limit(10).all()
        
        # Get category performance
        category_performance = db.session.query(
            Category.name,
            func.count(Album.id).label('album_count'),
            func.sum(Album.total_reads).label('total_reads')
        ).join(Album, Category.id == Album.category_id)\
         .group_by(Category.id, Category.name)\
         .order_by(desc('total_reads'))\
         .limit(10).all()
        
        # Calculate additional analytics
        visible_albums = Album.query.filter_by(is_visible=True).count()
        hidden_albums = Album.query.filter_by(is_visible=False).count()
        premium_albums = Album.query.filter_by(is_premium=True).count()
        completed_albums = Album.query.filter_by(is_completed=True).count()
        hiatus_albums = Album.query.filter_by(is_hiatus=True).count()
        
        # Calculate averages
        avg_chapters_per_album = total_chapters / total_albums if total_albums > 0 else 0
        avg_views_per_album = total_views / total_albums if total_albums > 0 else 0
        avg_reads_per_album = total_reads / total_albums if total_albums > 0 else 0
        read_to_view_ratio = (total_reads / total_views * 100) if total_views > 0 else 0
        
        # Get additional stats
        max_chapters_in_album = db.session.query(func.max(Album.total_chapters)).scalar() or 0
        single_chapter_albums = Album.query.filter_by(total_chapters=1).count()
        multi_chapter_albums = Album.query.filter(Album.total_chapters >= 5).count()
        most_viewed_album_views = db.session.query(func.max(Album.total_views)).scalar() or 0
        
        # Get recent activities (simplified)
        recent_activities = [
            {
                'icon': 'chart-bar',
                'message': 'Analytics dashboard accessed',
                'timestamp': 'Just now'
            }
        ]
        
        return render_template('admin/albums/analytics.html',
                             total_albums=total_albums,
                             total_chapters=total_chapters,
                             total_views=total_views,
                             total_reads=total_reads,
                             visible_albums=visible_albums,
                             hidden_albums=hidden_albums,
                             premium_albums=premium_albums,
                             completed_albums=completed_albums,
                             hiatus_albums=hiatus_albums,
                             avg_chapters_per_album=avg_chapters_per_album,
                             avg_views_per_album=avg_views_per_album,
                             avg_reads_per_album=avg_reads_per_album,
                             read_to_view_ratio=read_to_view_ratio,
                             max_chapters_in_album=max_chapters_in_album,
                             single_chapter_albums=single_chapter_albums,
                             multi_chapter_albums=multi_chapter_albums,
                             most_viewed_album_views=most_viewed_album_views,
                             top_albums=top_albums,
                             category_performance=category_performance,
                             recent_activities=recent_activities)
    
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        flash('Error loading analytics', 'error')
        return redirect(url_for('albums.dashboard'))


# =============================================================================
# API ENDPOINTS
# =============================================================================

@albums_bp.route('/api/search-news')
@login_required
@admin_required
def search_news():
    """Search news articles for adding as chapters"""
    try:
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        news_query = News.query.filter_by(is_visible=True)
        
        if query:
            news_query = news_query.filter(News.title.ilike(f'%{query}%'))
        
        news = news_query.order_by(News.created_at.desc())\
                        .offset((page - 1) * per_page)\
                        .limit(per_page)\
                        .all()
        
        results = []
        for article in news:
            results.append({
                'id': article.id,
                'title': article.title,
                'created_at': article.created_at.strftime('%Y-%m-%d') if article.created_at else '',
                'category': article.category.name if article.category else 'Uncategorized'
            })
        
        return jsonify({'success': True, 'results': results})
    
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        return jsonify({'success': False, 'message': 'Error searching news'})


@albums_bp.route('/api/album-stats/<int:album_id>')
@login_required
@admin_required
def album_stats(album_id):
    """Get album statistics"""
    try:
        album = Album.query.get_or_404(album_id)
        
        stats = {
            'total_chapters': album.total_chapters or 0,
            'total_views': album.total_views or 0,
            'total_reads': album.total_reads or 0,
            'average_rating': float(album.average_rating or 0)
        }
        
        return jsonify({'success': True, 'stats': stats})
    
    except Exception as e:
        logger.error(f"Error getting album stats: {e}")
        return jsonify({'success': False, 'message': 'Error getting stats'})


@albums_bp.route('/<int:album_id>/data')
@login_required
@admin_required
def get_album_data(album_id):
    """Get album data for editing"""
    try:
        album = Album.query.get_or_404(album_id)
        
        album_data = {
            'id': album.id,
            'title': album.title,
            'description': album.description,
            'category_id': album.category_id,
            'is_premium': album.is_premium,
            'is_visible': album.is_visible,
            'is_completed': album.is_completed,
            'is_hiatus': album.is_hiatus
        }
        
        return jsonify({'success': True, 'album': album_data})
    
    except Exception as e:
        logger.error(f"Error getting album data: {e}")
        return jsonify({'success': False, 'message': 'Error getting album data'})


@albums_bp.route('/<int:album_id>/chapters/data')
@login_required
@admin_required
def get_chapters_data(album_id):
    """Get chapters data for the modal"""
    try:
        album = Album.query.get_or_404(album_id)
        # Ensure the chapters relationship is loaded
        chapters = album.chapters
        
        chapters_data = []
        for chapter in chapters:
            chapters_data.append({
                'id': chapter.id,
                'chapter_number': chapter.chapter_number,
                'chapter_title': chapter.chapter_title,
                'news_title': chapter.news.title if chapter.news else None,
                'news_id': chapter.news_id
            })
        
        return jsonify({'success': True, 'chapters': chapters_data})
    
    except Exception as e:
        logger.error(f"Error getting chapters data: {e}")
        return jsonify({'success': False, 'message': 'Error getting chapters data'})


@albums_bp.route('/<int:album_id>/chapters/<int:chapter_id>/edit')
@login_required
@admin_required
def edit_chapter_page(album_id, chapter_id):
    """Redirect to the full chapter management page for editing"""
    return redirect(url_for('albums.manage_chapters', album_id=album_id))


 