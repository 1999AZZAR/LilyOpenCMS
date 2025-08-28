from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Rating, News, Album, User, UserRole
from datetime import datetime, timezone
from sqlalchemy import func

ratings_bp = Blueprint('ratings', __name__)


@ratings_bp.route('/api/ratings/<content_type>/<int:content_id>', methods=['GET'])
def get_ratings(content_type, content_id):
    """Get rating statistics for a specific content (news or album)."""
    try:
        # Pagination params for Recent Ratings on analytics page
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page and per_page > 100:
            per_page = 100
        # Pagination params for Recent Ratings on analytics page
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page and per_page > 100:
            per_page = 100
        # Pagination params for recent ratings
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page > 100:
            per_page = 100
        # Validate content type
        if content_type not in ['news', 'album']:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Check if content exists
        if content_type == 'news':
            content = News.query.get(content_id)
        else:
            content = Album.query.get(content_id)
        
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        # Get rating statistics based on content type
        if content_type == 'album':
            # Use weighted rating for albums
            weighted_stats = content.get_weighted_rating_stats()
            avg_rating = weighted_stats['weighted_average']
            rating_count = weighted_stats['total_ratings']
            rating_distribution = weighted_stats['rating_distribution']
            
            # Add chapter breakdown for albums
            chapter_breakdown = weighted_stats['chapter_breakdown']
            
            # Check if there are any ratings (direct album or chapter ratings)
            has_any_ratings = rating_count > 0
            
            # Add debugging
            current_app.logger.info(f"Album {content_id} rating stats: avg={avg_rating}, count={rating_count}, has_ratings={has_any_ratings}")
        else:
            # Use regular rating for news
            avg_rating = Rating.get_average_rating(content_type, content_id)
            rating_count = Rating.get_rating_count(content_type, content_id)
            rating_distribution = Rating.get_rating_distribution(content_type, content_id)
            chapter_breakdown = None
            has_any_ratings = rating_count > 0
        
        # Handle None average rating (no ratings)
        if avg_rating is None:
            avg_rating = 0.0
        
        # Get user's rating if logged in
        user_rating = None
        if current_user.is_authenticated:
            user_rating_obj = Rating.query.filter_by(
                content_type=content_type,
                content_id=content_id,
                user_id=current_user.id
            ).first()
            if user_rating_obj:
                user_rating = user_rating_obj.rating_value
        
        response_data = {
            'average_rating': avg_rating,
            'rating_count': rating_count,
            'rating_distribution': rating_distribution,
            'user_rating': user_rating
        }
        
        # Add chapter breakdown for albums
        if content_type == 'album' and chapter_breakdown:
            response_data['chapter_breakdown'] = chapter_breakdown
            response_data['total_chapters_rated'] = weighted_stats['total_chapters_rated']
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting ratings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/api/ratings/album/<int:album_id>/weighted', methods=['GET'])
def get_weighted_album_ratings(album_id):
    """Get detailed weighted rating statistics for an album."""
    try:
        # Check if album exists
        album = Album.query.get(album_id)
        if not album:
            return jsonify({'error': 'Album not found'}), 404
        
        # Get weighted rating statistics
        weighted_stats = album.get_weighted_rating_stats()
        
        # Get user's rating if logged in
        user_rating = None
        if current_user.is_authenticated:
            user_rating_obj = Rating.query.filter_by(
                content_type='album',
                content_id=album_id,
                user_id=current_user.id
            ).first()
            if user_rating_obj:
                user_rating = user_rating_obj.rating_value
        
        response_data = {
            'album_id': album_id,
            'album_title': album.title,
            'average_rating': weighted_stats['weighted_average'],  # Changed from weighted_average to average_rating
            'rating_count': weighted_stats['total_ratings'],  # Changed from total_ratings to rating_count
            'total_chapters_rated': weighted_stats['total_chapters_rated'],
            'rating_distribution': weighted_stats['rating_distribution'],
            'chapter_breakdown': weighted_stats['chapter_breakdown'],
            'user_rating': user_rating,
            'algorithm_info': {
                'description': 'Weighted rating based on chapter popularity',
                'formula': 'Weighted Rating = Σ(Chapter Rating × Chapter Weight) / Σ(Chapter Weights)',
                'weight_calculation': 'Chapter Weight = 1 + (chapter_read_count / max_read_count_in_album) * 0.5'
            }
        }
        
        # Add debugging
        current_app.logger.info(f"Weighted album ratings for album {album_id}: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting weighted album ratings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/api/ratings', methods=['POST'])
@login_required
def create_rating():
    """Create or update a rating."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    rating_value = data.get('rating_value')
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    
    # Validation
    if not rating_value or not isinstance(rating_value, int):
        return jsonify({'error': 'Rating value is required and must be an integer'}), 400
    
    if rating_value < 1 or rating_value > 5:
        return jsonify({'error': 'Rating value must be between 1 and 5'}), 400
    
    if content_type not in ['news', 'album']:
        return jsonify({'error': 'Invalid content type'}), 400
    
    # Check if content exists
    if content_type == 'news':
        content_obj = News.query.get(content_id)
    else:
        content_obj = Album.query.get(content_id)
    
    if not content_obj:
        return jsonify({'error': 'Content not found'}), 404
    
    # Check if user is suspended
    if current_user.is_suspended:
        return jsonify({'error': 'Your account is suspended'}), 403
    
    # Check if user already rated this content
    existing_rating = Rating.query.filter_by(
        content_type=content_type,
        content_id=content_id,
        user_id=current_user.id
    ).first()
    
    try:
        if existing_rating:
            # Update existing rating
            existing_rating.rating_value = rating_value
            existing_rating.updated_at = datetime.now(timezone.utc)
            rating = existing_rating
            action = 'updated'
        else:
            # Create new rating
            rating = Rating(
                rating_value=rating_value,
                content_type=content_type,
                content_id=content_id,
                user_id=current_user.id
            )
            db.session.add(rating)
            action = 'created'
        
        # Validate rating
        rating.validate()
        
        db.session.commit()
        
        # Record user activity (with safety check)
        try:
            if hasattr(current_user, 'record_activity'):
                current_user.record_activity(
                    'rate_content',
                    f'{action.title()} rating ({rating_value} stars) on {content_type} {content_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent')
                )
        except Exception as e:
            current_app.logger.warning(f"Could not record user activity: {str(e)}")
        
        # Get updated statistics
        avg_rating = Rating.get_average_rating(content_type, content_id)
        rating_count = Rating.get_rating_count(content_type, content_id)
        rating_distribution = Rating.get_rating_distribution(content_type, content_id)
        
        # Handle None average rating (no ratings)
        if avg_rating is None:
            avg_rating = 0.0
        
        return jsonify({
            'message': f'Rating {action} successfully',
            'rating': rating.to_dict(),
            'average_rating': avg_rating,
            'rating_count': rating_count,
            'rating_distribution': rating_distribution
        }), 201 if action == 'created' else 200
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating rating: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/api/ratings/<content_type>/<int:content_id>', methods=['DELETE'])
@login_required
def delete_rating(content_type, content_id):
    """Delete a user's rating."""
    try:
        # Validate content type
        if content_type not in ['news', 'album']:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Find user's rating
        rating = Rating.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            user_id=current_user.id
        ).first()
        
        if not rating:
            return jsonify({'error': 'Rating not found'}), 404
        
        # Delete rating
        db.session.delete(rating)
        db.session.commit()
        
        # Record user activity (with safety check)
        try:
            if hasattr(current_user, 'record_activity'):
                current_user.record_activity(
                    'delete_rating',
                    f'Deleted rating on {content_type} {content_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent')
                )
        except Exception as e:
            current_app.logger.warning(f"Could not record user activity: {str(e)}")
        
        # Get updated statistics
        avg_rating = Rating.get_average_rating(content_type, content_id)
        rating_count = Rating.get_rating_count(content_type, content_id)
        rating_distribution = Rating.get_rating_distribution(content_type, content_id)
        
        return jsonify({
            'message': 'Rating deleted successfully',
            'average_rating': avg_rating,
            'rating_count': rating_count,
            'rating_distribution': rating_distribution
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting rating: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/api/ratings/stats', methods=['GET'])
def get_rating_stats():
    """Get overall rating statistics."""
    try:
        # Pagination params for Recent Ratings on analytics page
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page and per_page > 100:
            per_page = 100

        # Get overall statistics
        total_ratings = Rating.query.count()
        
        # Get average rating across all content
        avg_rating_result = db.session.query(func.avg(Rating.rating_value)).scalar()
        overall_avg_rating = round(avg_rating_result, 2) if avg_rating_result else 0.0
        
        # Get rating distribution across all content
        overall_distribution = {}
        for i in range(1, 6):
            count = Rating.query.filter_by(rating_value=i).count()
            overall_distribution[i] = count
        
        # Get top rated content
        top_rated_news = db.session.query(
            News.id, News.title, func.avg(Rating.rating_value).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        ).join(Rating, Rating.content_id == News.id).filter(
            Rating.content_type == 'news'
        ).group_by(News.id).having(
            func.count(Rating.id) >= 3  # At least 3 ratings
        ).order_by(func.avg(Rating.rating_value).desc()).limit(10).all()
        
        top_rated_albums = db.session.query(
            Album.id, Album.title, func.avg(Rating.rating_value).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        ).join(Rating, Rating.content_id == Album.id).filter(
            Rating.content_type == 'album'
        ).group_by(Album.id).having(
            func.count(Rating.id) >= 3  # At least 3 ratings
        ).order_by(func.avg(Rating.rating_value).desc()).limit(10).all()
        
        return jsonify({
            'total_ratings': total_ratings,
            'overall_average_rating': overall_avg_rating,
            'overall_distribution': overall_distribution,
            'top_rated_news': [
                {
                    'id': item.id,
                    'title': item.title,
                    'average_rating': round(float(item.avg_rating), 2),
                    'rating_count': item.rating_count
                }
                for item in top_rated_news
            ],
            'top_rated_albums': [
                {
                    'id': item.id,
                    'title': item.title,
                    'average_rating': round(float(item.avg_rating), 2),
                    'rating_count': item.rating_count
                }
                for item in top_rated_albums
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting rating stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/api/ratings/user/<int:user_id>', methods=['GET'])
def get_user_ratings(user_id):
    """Get all ratings by a specific user."""
    try:
        # Check if user exists
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's ratings with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        ratings_query = Rating.query.filter_by(user_id=user_id).order_by(Rating.created_at.desc())
        
        ratings_pagination = ratings_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        ratings_data = []
        for rating in ratings_pagination.items:
            rating_dict = rating.to_dict()
            
            # Get content information
            if rating.content_type == 'news':
                content = News.query.get(rating.content_id)
                if content:
                    rating_dict['content'] = {
                        'id': content.id,
                        'title': content.title,
                        'type': 'news'
                    }
            else:
                content = Album.query.get(rating.content_id)
                if content:
                    rating_dict['content'] = {
                        'id': content.id,
                        'title': content.title,
                        'type': 'album'
                    }
            
            ratings_data.append(rating_dict)
        
        return jsonify({
            'ratings': ratings_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': ratings_pagination.total,
                'pages': ratings_pagination.pages,
                'has_next': ratings_pagination.has_next,
                'has_prev': ratings_pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user ratings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Admin routes for rating management
@ratings_bp.route('/admin/ratings')
@login_required
def admin_ratings():
    """Admin interface for rating management."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('Permission denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get ratings with filters
    page = request.args.get('page', 1, type=int)
    content_type = request.args.get('content_type', '')
    min_rating = request.args.get('min_rating', type=int)
    max_rating = request.args.get('max_rating', type=int)
    
    query = Rating.query
    
    # Apply filters
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    if min_rating:
        query = query.filter(Rating.rating_value >= min_rating)
    
    if max_rating:
        query = query.filter(Rating.rating_value <= max_rating)
    
    # Order by creation date
    query = query.order_by(Rating.created_at.desc())
    
    # Pagination
    ratings = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        'admin/settings/rating_management.html',
        ratings=ratings,
        content_type=content_type,
        min_rating=min_rating,
        max_rating=max_rating
    )


@ratings_bp.route('/admin/ratings/<int:rating_id>/delete', methods=['POST'])
@login_required
def admin_delete_rating(rating_id):
    """Admin delete a rating."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        rating = Rating.query.get_or_404(rating_id)
        
        # Store content info before deletion
        content_type = rating.content_type
        content_id = rating.content_id
        
        db.session.delete(rating)
        db.session.commit()
        
        # Get updated statistics
        avg_rating = Rating.get_average_rating(content_type, content_id)
        rating_count = Rating.get_rating_count(content_type, content_id)
        rating_distribution = Rating.get_rating_distribution(content_type, content_id)
        
        return jsonify({
            'message': 'Rating deleted successfully',
            'average_rating': avg_rating,
            'rating_count': rating_count,
            'rating_distribution': rating_distribution
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting rating: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@ratings_bp.route('/admin/ratings/analytics')
@login_required
def rating_analytics():
    """Admin analytics for ratings."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('Permission denied', 'error')
        return redirect(url_for('main.index'))
    
    try:
        # Pagination params for Recent Ratings on analytics page
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        if per_page and per_page > 100:
            per_page = 100

        # Optional cap for weighted albums to avoid heavy processing
        weighted_albums_limit = request.args.get('wa_limit', default=10, type=int)

        # Get overall statistics
        total_ratings = Rating.query.count()
        
        # Get average rating across all content
        avg_rating_result = db.session.query(func.avg(Rating.rating_value)).scalar()
        overall_avg_rating = round(avg_rating_result, 2) if avg_rating_result else 0.0
        
        # Get rating distribution
        distribution = {}
        for i in range(1, 6):
            count = Rating.query.filter_by(rating_value=i).count()
            distribution[i] = count
        
        # Get ratings by content type
        news_ratings = Rating.query.filter_by(content_type='news').count()
        album_ratings = Rating.query.filter_by(content_type='album').count()
        
        # Get average ratings by content type
        news_avg = db.session.query(func.avg(Rating.rating_value)).filter_by(content_type='news').scalar()
        album_avg = db.session.query(func.avg(Rating.rating_value)).filter_by(content_type='album').scalar()
        
        # Calculate weighted album ratings
        albums_with_chapters = Album.query.filter(Album.chapters.any()).all()
        weighted_album_stats = []
        total_weighted_rating = 0.0
        albums_with_weighted_ratings = 0
        
        for album in albums_with_chapters:
            weighted_stats = album.get_weighted_rating_stats()
            if weighted_stats['weighted_average'] > 0:
                weighted_album_stats.append({
                    'album_id': album.id,
                    'album_title': album.title,
                    'weighted_average': weighted_stats['weighted_average'],
                    'total_ratings': weighted_stats['total_ratings'],
                    'total_chapters_rated': weighted_stats['total_chapters_rated']
                })
                total_weighted_rating += weighted_stats['weighted_average']
                albums_with_weighted_ratings += 1

        # Sort by weighted_average desc and cap the list to reduce payload size
        if weighted_album_stats:
            weighted_album_stats.sort(key=lambda a: a['weighted_average'], reverse=True)
            if weighted_albums_limit and weighted_albums_limit > 0:
                weighted_album_stats = weighted_album_stats[:weighted_albums_limit]
        
        # Calculate average weighted rating
        avg_weighted_album_rating = round(total_weighted_rating / albums_with_weighted_ratings, 2) if albums_with_weighted_ratings > 0 else 0.0
        
        # Get recent ratings (paginated)
        recent_query = Rating.query.order_by(Rating.created_at.desc())
        recent_pagination = recent_query.paginate(page=page, per_page=per_page, error_out=False)
        recent_ratings = recent_pagination.items
        
        analytics_data = {
            'total_ratings': total_ratings,
            'overall_average_rating': overall_avg_rating,
            'distribution': distribution,
            'news_ratings': news_ratings,
            'album_ratings': album_ratings,
            'news_average': round(float(news_avg), 2) if news_avg else 0.0,
            'album_average': round(float(album_avg), 2) if album_avg else 0.0,
            'weighted_album_average': avg_weighted_album_rating,
            'albums_with_weighted_ratings': albums_with_weighted_ratings,
            'weighted_album_stats': weighted_album_stats,
            'recent_ratings': recent_ratings,  # Keep as Rating objects, not dictionaries
            'recent_page': recent_pagination.page,
            'recent_pages': recent_pagination.pages,
            'recent_total': recent_pagination.total
        }
        
        return render_template(
            'admin/settings/rating_analytics.html',
            analytics=analytics_data
        )
        
    except Exception as e:
        current_app.logger.error(f"Error getting rating analytics: {str(e)}")
        flash('Error loading analytics', 'error')
        return redirect(url_for('ratings.admin_ratings')) 