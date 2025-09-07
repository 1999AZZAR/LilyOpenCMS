"""
Public API Routes for Multiplatform Access
Provides JSON endpoints for key resources that are currently only available as HTML pages.
This enables mobile apps, desktop clients, and third-party integrations to access the same data.
"""

from routes import main_blueprint
from .common_imports import *
from models import (
    News, Album, AlbumChapter, User, UserProfile, UserStats, 
    Category, Comment, Rating, UserLibrary, ReadingHistory
)
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import json

# Import functions from routes_public.py
from .routes_public import search_albums, search_news_api, get_categories, get_tags, optimize_news_query

# =============================================================================
# NEWS API ENDPOINTS
# =============================================================================

@main_blueprint.route("/api/public/news/<int:news_id>", methods=["GET"])
def get_public_news_api(news_id):
    """
    Public API endpoint to retrieve a single news article in JSON format.
    Returns the same data as the HTML news detail page.
    """
    try:
        # Get the news item
        news_item = News.query.filter_by(id=news_id, is_visible=True).first()
        if not news_item:
            return jsonify({"error": "News article not found"}), 404

        # Check if news is premium and requires authentication
        if news_item.is_premium:
            # For premium content, we might want to return limited info or require auth
            # For now, return basic info but mark as premium
            data = {
                "id": news_item.id,
                "title": news_item.title,
                "excerpt": (news_item.content[:200] + "..." if news_item.content and len(news_item.content) > 200 else news_item.content),
                "is_premium": True,
                "category": {
                    "id": news_item.category.id if news_item.category else None,
                    "name": news_item.category.name if news_item.category else None
                },
                "created_at": news_item.created_at.isoformat() if news_item.created_at else None,
                "updated_at": news_item.updated_at.isoformat() if news_item.updated_at else None,
                "read_count": news_item.read_count,
                
                "is_news": news_item.is_news,
                "message": "Premium content - full access requires authentication"
            }
        else:
            # Full content for non-premium news
            data = news_item.to_dict() if hasattr(news_item, 'to_dict') else {}
            
            # Enrich with category info
            if news_item.category:
                data["category"] = {
                    "id": news_item.category.id,
                    "name": news_item.category.name,
                    "description": news_item.category.description
                }
            
            # Enrich with image info
            if news_item.image:
                data["header_image"] = {
                    "id": news_item.image.id,
                    "url": (news_item.image.to_dict().get("file_url") if hasattr(news_item.image, "to_dict") else None) or news_item.image.url,
                    "description": getattr(news_item.image, "description", None),
                    "filepath": getattr(news_item.image, "filepath", None)
                }
            
            # Add author info
            if news_item.author:
                data["author"] = {
                    "id": news_item.author.id,
                    "username": news_item.author.username,
                    "display_name": news_item.author.get_full_name() if hasattr(news_item.author, 'get_full_name') else news_item.author.username,
                    "avatar_url": news_item.author.avatar_url if hasattr(news_item.author, 'avatar_url') else None
                }
            
            # Add related content
            related_news = News.query.filter(
                and_(
                    News.category_id == news_item.category_id,
                    News.id != news_item.id,
                    News.is_visible == True
                )
            ).order_by(desc(News.created_at)).limit(5).all()
            
            data["related_news"] = [
                {
                    "id": item.id,
                    "title": item.title,
                    "excerpt": (item.content[:200] + "..." if item.content and len(item.content) > 200 else item.content),
                    "created_at": item.created_at.isoformat() if item.created_at else None
                } for item in related_news
            ]

        return jsonify(data)
        
    except Exception as e:
        current_app.logger.error(f"Error in public news API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# =============================================================================
# ADDITIONAL PUBLIC API ENDPOINTS
# =============================================================================

@main_blueprint.route("/api/public/albums/<int:album_id>/detail")
def api_album_detail(album_id):
    """API endpoint for album detail data."""
    try:
        album = Album.query.get_or_404(album_id)
        
        # Check if album is visible
        if (album.is_visible is False) or (album.is_archived is True):
            return jsonify({"error": "Album not found or not visible"}), 404
        
        # Get chapters for this album
        chapters = (
            AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
            .order_by(AlbumChapter.chapter_number)
            .all()
        )
        
        # Prepare response data
        album_data = {
            "id": album.id,
            "title": album.title,
            "description": album.description,
            "is_premium": album.is_premium,
            "is_completed": album.is_completed,
            "is_hiatus": album.is_hiatus,
            "age_rating": album.age_rating,
            "total_chapters": album.total_chapters,
            "total_reads": album.total_reads,
            "total_views": album.total_views,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "updated_at": album.updated_at.isoformat() if album.updated_at else None,
            "cover_image": {
                "id": album.cover_image.id,
                "url": (album.cover_image.to_dict().get("file_url") if hasattr(album.cover_image, "to_dict") else None) or album.cover_image.url,
                "description": getattr(album.cover_image, "description", None),
                "filepath": getattr(album.cover_image, "filepath", None)
            } if album.cover_image else None,
            "chapters": [{
                "id": ch.id,
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
            } for ch in chapters],
        }
        
        return jsonify({
            "success": True,
            "album": album_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_album_detail: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"An error occurred while fetching album details: {str(e)}",
            "debug": {
                "exception_type": str(type(e)),
                "exception_args": str(e.args)
            }
        }), 500

@main_blueprint.route("/api/public/albums/<int:album_id>/chapters/<int:chapter_id>/detail")
def api_chapter_detail(album_id, chapter_id):
    """API endpoint for chapter detail data (by chapter_id)."""
    try:
        album = Album.query.get_or_404(album_id)
        chapter = AlbumChapter.query.get_or_404(chapter_id)
        
        # Check if album and chapter are visible
        if (album.is_visible is False) or (album.is_archived is True):
            return jsonify({"error": "Album not found or not visible"}), 404
        if (chapter.is_visible is False) or chapter.album_id != album_id:
            return jsonify({"error": "Chapter not found or not visible"}), 404
        
        # Get the news article for this chapter
        news = chapter.news
        
        # Prepare response data
        chapter_data = {
            "id": chapter.id,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.chapter_title,
            "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
            "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
            "album": {
                "id": album.id,
                "title": album.title,
                "is_premium": album.is_premium,
            },
            "cover_image": {
                "id": album.cover_image.id,
                "url": (album.cover_image.to_dict().get("file_url") if hasattr(album.cover_image, "to_dict") else None) or album.cover_image.url,
                "description": getattr(album.cover_image, "description", None),
                "filepath": getattr(album.cover_image, "filepath", None)
            } if album.cover_image else None,
            "news_content": {
                "id": news.id,
                "title": news.title,
                "content": news.content,
                "excerpt": news.content[:200] + "..." if news.content and len(news.content) > 200 else news.content,
                "is_premium": news.is_premium,
                "created_at": news.created_at.isoformat() if news.created_at else None,
            } if news else None,
        }
        
        return jsonify({
            "success": True,
            "chapter": chapter_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_chapter_detail: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"An error occurred while fetching chapter details: {str(e)}",
            "debug": {
                "exception_type": str(type(e)),
                "exception_args": str(e.args)
            }
        }), 500

@main_blueprint.route("/api/public/albums/list")
def api_albums_list():
    """API endpoint for albums listing data."""
    try:
        # Use the existing search logic
        return search_albums()
        
    except Exception as e:
        current_app.logger.error(f"Error in api_albums_list: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An error occurred while fetching albums list"
        }), 500

@main_blueprint.route("/api/public/news/<int:news_id>/detail")
def api_news_detail(news_id):
    """API endpoint for news detail data."""
    try:
        news_item = News.query.get_or_404(news_id)
        
        # Check visibility
        if not news_item.is_visible:
            return jsonify({"error": "News not found or not visible"}), 404
        
        # Prepare response data
        news_data = {
            "id": news_item.id,
            "title": news_item.title,
            "content": news_item.content,
            "excerpt": news_item.content[:200] + "..." if news_item.content and len(news_item.content) > 200 else news_item.content,
            "is_premium": news_item.is_premium,
            "is_news": news_item.is_news,
            "is_main_news": news_item.is_main_news,
            "age_rating": news_item.age_rating,
            "read_count": news_item.read_count,
            "created_at": news_item.created_at.isoformat() if news_item.created_at else None,
            "updated_at": news_item.updated_at.isoformat() if news_item.updated_at else None,
        }
        
        return jsonify({
            "success": True,
            "news": news_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_news_detail: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An error occurred while fetching news details"
        }), 500

@main_blueprint.route("/api/public/news/list")
def api_news_list():
    """API endpoint for news listing data."""
    try:
        # Use the existing search logic
        return search_news_api()
        
    except Exception as e:
        current_app.logger.error(f"Error in api_news_list: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An error occurred while fetching news list"
        }), 500

@main_blueprint.route("/api/public/categories")
def api_categories():
    """API endpoint for categories data."""
    try:
        # Use the existing categories logic
        return get_categories()
        
    except Exception as e:
        current_app.logger.error(f"Error in api_categories: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to fetch categories"
        }), 500

@main_blueprint.route("/api/public/tags")
def api_tags():
    """API endpoint for tags data."""
    try:
        # Use the existing tags logic
        return get_tags()
        
    except Exception as e:
        current_app.logger.error(f"Error in api_tags: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to fetch tags"
        }), 500

@main_blueprint.route("/api/public/homepage")
def api_homepage():
    """API endpoint for homepage data."""
    try:
        # Get brand info to check homepage design preference
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        homepage_design = brand_info.homepage_design if brand_info else "news"
        
        # Get main featured news
        main_news_query = (
            News.query.filter_by(is_visible=True, is_main_news=True)
            .order_by(News.created_at.desc())
            .limit(5)
        )
        main_news = optimize_news_query(main_news_query).all()
        
        # Get latest articles
        latest_articles_query = (
            News.query.filter_by(is_visible=True, is_news=False)
            .order_by(News.created_at.desc())
            .limit(5)
        )
        latest_articles = optimize_news_query(latest_articles_query).all()
        
        # Get latest news
        latest_news_query = (
            News.query.filter_by(is_visible=True, is_news=True)
            .order_by(News.created_at.desc())
            .limit(5)
        )
        latest_news = optimize_news_query(latest_news_query).all()
        
        # Get popular news
        popular_news_query = (
            News.query.filter_by(is_visible=True)
            .order_by(News.read_count.desc())
            .limit(7)
        )
        popular_news = optimize_news_query(popular_news_query).all()
        
        # Get featured albums
        featured_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .join(Category, Category.id == Album.category_id)
            .join(User, User.id == Album.user_id)
            .order_by(Album.total_reads.desc())
            .limit(6)
        )
        featured_albums = featured_albums_query.all()
        
        # Get categories
        if homepage_design == "albums":
            categories_with_counts = (
                db.session.query(
                    Category,
                    db.func.count(Album.id).label("album_count")
                )
                .join(Album, Category.id == Album.category_id)
                .filter(Album.is_visible == True, Album.is_archived == False)
                .group_by(Category.id, Category.name)
                .having(db.func.count(Album.id) > 0)
                .order_by(db.func.count(Album.id).desc())
                .all()
            )
            
            categories = []
            for category, count in categories_with_counts:
                category.album_count = count
                categories.append(category)
        else:
            categories_with_counts = (
                db.session.query(
                    Category,
                    db.func.count(News.id).label("news_count")
                )
                .join(News, Category.id == News.category_id)
                .filter(News.is_visible == True)
                .group_by(Category.id, Category.name)
                .having(db.func.count(News.id) > 0)
                .order_by(db.func.count(News.id).desc())
                .all()
            )
            
            categories = []
            for category, count in categories_with_counts:
                category.news_count = count
                categories.append(category)
        
        # Prepare response data
        homepage_data = {
            "design": homepage_design,
            "main_news": [{
                "id": news.id,
                "title": news.title,
                "excerpt": news.content[:150] + "..." if news.content and len(news.content) > 150 else news.content,
                "is_premium": news.is_premium,
                "read_count": news.read_count,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "url": url_for("main.news_detail", 
                              news_id=news.id, 
                              news_title=news.title.replace(" ", "-").lower())
            } for news in main_news],
            "latest_articles": [{
                "id": article.id,
                "title": article.title,
                "excerpt": article.content[:150] + "..." if article.content and len(article.content) > 150 else article.content,
                "is_premium": article.is_premium,
                "read_count": article.read_count,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "url": url_for("main.news_detail", 
                              news_id=article.id, 
                              news_title=article.title.replace(" ", "-").lower())
            } for article in latest_articles],
            "latest_news": [{
                "id": news.id,
                "title": news.title,
                "excerpt": news.content[:150] + "..." if news.content and len(news.content) > 150 else news.content,
                "is_premium": news.is_premium,
                "read_count": news.read_count,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "url": url_for("main.news_detail", 
                              news_id=news.id, 
                              news_title=news.title.replace(" ", "-").lower())
            } for news in latest_news],
            "popular_news": [{
                "id": news.id,
                "title": news.title,
                "excerpt": news.content[:150] + "..." if news.content and len(news.content) > 150 else news.content,
                "is_premium": news.is_premium,
                "read_count": news.read_count,
                "created_at": news.created_at.isoformat() if news.created_at else None,
                "url": url_for("main.news_detail", 
                              news_id=news.id, 
                              news_title=news.title.replace(" ", "-").lower())
            } for news in popular_news],
            "featured_albums": [{
                "id": album.id,
                "title": album.title,
                "description": album.description,
                "is_premium": album.is_premium,
                "total_chapters": album.total_chapters,
                "total_reads": album.total_reads,
                "created_at": album.created_at.isoformat() if album.created_at else None,
                "url": url_for("main.album_detail", 
                              album_id=album.id, 
                              album_title=album.title.replace(" ", "-").lower())
            } for album in featured_albums],
            "categories": [{
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "news_count": getattr(category, "news_count", None),
                "album_count": getattr(category, "album_count", None)
            } for category in categories]
        }
        
        return jsonify({
            "success": True,
            "homepage": homepage_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_homepage: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "An error occurred while fetching homepage data"
        }), 500

# =============================================================================
# SIMPLE PUBLIC API ENDPOINTS (No "public" prefix)
# =============================================================================

@main_blueprint.route("/api/news/<int:news_id>", methods=["GET"])
def get_news_simple(news_id):
    """
    Simple public API endpoint to retrieve a single news article in JSON format.
    No authentication required.
    """
    try:
        # Get the news item
        news_item = News.query.filter_by(id=news_id, is_visible=True).first()
        if not news_item:
            return jsonify({"error": "News article not found"}), 404

        # Check if news is premium and requires authentication
        if news_item.is_premium:
            # For premium content, return limited info
            data = {
                "id": news_item.id,
                "title": news_item.title,
                "excerpt": (news_item.content[:200] + "..." if news_item.content and len(news_item.content) > 200 else news_item.content),
                "is_premium": True,
                "category": {
                    "id": news_item.category.id if news_item.category else None,
                    "name": news_item.category.name if news_item.category else None
                },
                "created_at": news_item.created_at.isoformat() if news_item.created_at else None,
                "updated_at": news_item.updated_at.isoformat() if news_item.updated_at else None,
                "read_count": news_item.read_count,
                
                "is_news": news_item.is_news,
                "message": "Premium content - full access requires authentication"
            }
        else:
            # Full content for non-premium news
            data = {
                "id": news_item.id,
                "title": news_item.title,
                "content": news_item.content,
                "excerpt": news_item.excerpt,
                "is_premium": False,
                "is_news": news_item.is_news,
                "created_at": news_item.created_at.isoformat() if news_item.created_at else None,
                "updated_at": news_item.updated_at.isoformat() if news_item.updated_at else None,
                "read_count": news_item.read_count,
                "share_count": news_item.share_count,
                "category": {
                    "id": news_item.category.id if news_item.category else None,
                    "name": news_item.category.name if news_item.category else None,
                    "description": news_item.category.description if news_item.category else None
                } if news_item.category else None,
                "author": {
                    "id": news_item.author.id if news_item.author else None,
                    "username": news_item.author.username if news_item.author else None,
                    "display_name": news_item.author.get_full_name() if news_item.author else None
                } if news_item.author else None
            }
            
            # Add image info if available
            if news_item.image:
                data["header_image"] = {
                    "id": news_item.image.id,
                    "url": (news_item.image.to_dict().get("file_url") if hasattr(news_item.image, "to_dict") else None) or news_item.image.url,
                    "description": getattr(news_item.image, "description", None),
                    "filepath": getattr(news_item.image, "filepath", None)
                }

        return jsonify(data)

    except Exception as e:
        current_app.logger.error(f"Error in simple news API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/albums/<int:album_id>", methods=["GET"])
def get_album_simple(album_id):
    """
    Simple public API endpoint to retrieve a single album in JSON format.
    No authentication required.
    """
    try:
        album = Album.query.get_or_404(album_id)

        # Check if album is visible
        if not album.is_visible or album.is_archived:
            return jsonify({"error": "Album not found or not visible"}), 404

        # Get chapters for this album
        chapters = (
            AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
            .order_by(AlbumChapter.chapter_number)
            .all()
        )

        # Prepare response data
        album_data = {
            "id": album.id,
            "title": album.title,
            "description": album.description,
            "is_premium": album.is_premium,
            "is_completed": album.is_completed,
            "is_hiatus": album.is_hiatus,
            "age_rating": album.age_rating,
            "total_chapters": album.total_chapters,
            "total_reads": album.total_reads,
            "total_views": album.total_views,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "updated_at": album.updated_at.isoformat() if album.updated_at else None,
            "category": {
                "id": album.category.id if album.category else None,
                "name": album.category.name if album.category else None,
                "description": album.category.description if album.category else None
            } if album.category else None,
            # In models, Album.author is a string (author name). Expose it directly.
            "author": album.author,
            # Also expose owner (User) details if present
            "owner": {
                "id": album.owner.id if album.owner else None,
                "username": album.owner.username if album.owner else None,
                "display_name": album.owner.get_full_name() if album.owner else None
            } if album.owner else None,
            "chapters": [{
                "id": ch.id,
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
                "is_visible": ch.is_visible,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
                "updated_at": ch.updated_at.isoformat() if ch.updated_at else None
            } for ch in chapters]
        }

        # Add cover image if available
        if album.cover_image:
            album_data["cover_image"] = {
                "id": album.cover_image.id,
                "url": (album.cover_image.to_dict().get("file_url") if hasattr(album.cover_image, "to_dict") else None) or album.cover_image.url,
                "description": getattr(album.cover_image, "description", None),
                "filepath": getattr(album.cover_image, "filepath", None)
            }

        return jsonify(album_data)

    except Exception as e:
        current_app.logger.error(f"Error in simple album API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/albums/<int:album_id>/chapters/<int:chapter_id>", methods=["GET"])
def get_chapter_simple(album_id, chapter_id):
    """
    Simple public API endpoint to retrieve a single chapter in JSON format (by chapter_id).
    No authentication required.
    """
    try:
        # Get the chapter
        chapter = AlbumChapter.query.filter_by(
            id=chapter_id, 
            album_id=album_id, 
            is_visible=True
        ).first()
        
        if not chapter:
            return jsonify({"error": "Chapter not found or not visible"}), 404

        # Get the album
        album = Album.query.filter_by(id=album_id, is_visible=True).first()
        if not album:
            return jsonify({"error": "Album not found or not visible"}), 404

        # Get the news content
        news_content = News.query.filter_by(id=chapter.news_id, is_visible=True).first()
        if not news_content:
            return jsonify({"error": "Chapter content not found"}), 404

        # Check if content is premium
        if news_content.is_premium:
            content = (news_content.content[:200] + "..." if news_content.content and len(news_content.content) > 200 else news_content.content)
            is_premium = True
            message = "Premium content - full access requires authentication"
        else:
            content = news_content.content
            is_premium = False
            message = None

        # Get navigation info
        all_chapters = (
            AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
            .order_by(AlbumChapter.chapter_number)
            .all()
        )
        
        current_index = next((i for i, ch in enumerate(all_chapters) if ch.id == chapter_id), -1)
        
        navigation = {}
        if current_index > 0:
            prev_chapter = all_chapters[current_index - 1]
            navigation["previous"] = {
                "id": prev_chapter.id,
                "chapter_number": prev_chapter.chapter_number,
                "chapter_title": prev_chapter.chapter_title
            }
        
        if current_index < len(all_chapters) - 1:
            next_chapter = all_chapters[current_index + 1]
            navigation["next"] = {
                "id": next_chapter.id,
                "chapter_number": next_chapter.chapter_number,
                "chapter_title": next_chapter.chapter_title
            }

        # Prepare response data
        chapter_data = {
            "id": chapter.id,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.chapter_title,
            "is_premium": is_premium,
            "created_at": chapter.created_at.isoformat() if chapter.created_at else None,
            "updated_at": chapter.updated_at.isoformat() if chapter.updated_at else None,
            "album": {
                "id": album.id,
                "title": album.title,
                "is_premium": album.is_premium
            },
            "content": content,
            "navigation": navigation
        }

        if message:
            chapter_data["message"] = message

        return jsonify(chapter_data)

    except Exception as e:
        current_app.logger.error(f"Error in simple chapter API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/categories", methods=["GET"])
def get_categories_simple():
    """
    Simple public API endpoint to retrieve all categories in JSON format.
    No authentication required.
    """
    try:
        categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
        
        categories_data = []
        for category in categories:
            # Count content in this category
            news_count = News.query.filter_by(
                category_id=category.id, 
                is_visible=True
            ).count()
            
            album_count = Album.query.filter_by(
                category_id=category.id, 
                is_visible=True, 
                is_archived=False
            ).count()
            
            category_data = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "display_order": category.display_order,
                "content_counts": {
                    "news": news_count,
                    "albums": album_count,
                    "total": news_count + album_count
                }
            }
            
            if category.group:
                category_data["group"] = {
                    "id": category.group.id,
                    "name": category.group.name,
                    "description": category.group.description
                }
            
            categories_data.append(category_data)
        
        return jsonify(categories_data)

    except Exception as e:
        current_app.logger.error(f"Error in simple categories API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/tags", methods=["GET"])
def get_tags_simple():
    """
    Simple public API endpoint to retrieve all tags in JSON format.
    No authentication required.
    """
    try:
        # Get search query if provided
        search_query = request.args.get('search', '').strip()
        
        # Get all unique tags from news articles
        news_tags = db.session.query(News.tagar).filter(
            News.tagar.isnot(None),
            News.tagar != '',
            News.is_visible == True
        ).distinct().all()
        
        # Combine and process tags
        all_tags = set()
        
        # Process news tags
        for (tag_string,) in news_tags:
            if tag_string:
                tags_list = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                all_tags.update(tags_list)
        
        # Filter by search query if provided
        if search_query:
            all_tags = {tag for tag in all_tags if search_query.lower() in tag.lower()}
        
        # Convert to list and sort
        tags_list = sorted(list(all_tags))
        
        # Count content for each tag
        tags_data = []
        for tag_name in tags_list:
            # Count news with this tag
            news_count = News.query.filter(
                News.tagar.contains(tag_name),
                News.is_visible == True
            ).count()
            
            # Albums currently have no tags field; set to 0 for now
            album_count = 0
            
            tag_data = {
                "name": tag_name,
                "slug": tag_name.lower().replace(' ', '-'),
                "content_counts": {
                    "news": news_count,
                    "albums": album_count,
                    "total": news_count + album_count
                }
            }
            
            tags_data.append(tag_data)
        
        return jsonify(tags_data)

    except Exception as e:
        current_app.logger.error(f"Error in simple tags API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/comments/<string:content_type>/<int:content_id>", methods=["GET"])
def get_comments_simple(content_type, content_id):
    """
    Simple public API endpoint to retrieve comments for content in JSON format.
    No authentication required.
    """
    try:
        # Validate content type
        if content_type not in ['news', 'album', 'chapter']:
            return jsonify({"error": "Invalid content type. Must be 'news', 'album', or 'chapter'"}), 400
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Build query based on content type
        if content_type == 'news':
            # Check if news exists and is visible
            news = News.query.filter_by(id=content_id, is_visible=True).first()
            if not news:
                return jsonify({"error": "News not found or not visible"}), 404
            
            comments_query = Comment.query.filter_by(
                content_type='news',
                content_id=content_id
            ).filter(
                Comment.is_approved == True,
                Comment.is_spam == False,
                Comment.is_deleted == False
            )
            
        elif content_type == 'album':
            # Check if album exists and is visible
            album = Album.query.filter_by(id=content_id, is_visible=True, is_archived=False).first()
            if not album:
                return jsonify({"error": "Album not found or not visible"}), 404
            
            comments_query = Comment.query.filter_by(
                content_type='album',
                content_id=content_id
            ).filter(
                Comment.is_approved == True,
                Comment.is_spam == False,
                Comment.is_deleted == False
            )
            
        elif content_type == 'chapter':
            # Check if chapter exists and is visible
            chapter = AlbumChapter.query.filter_by(id=content_id, is_visible=True).first()
            if not chapter:
                return jsonify({"error": "Chapter not found or not visible"}), 404
            
            # Map chapter comments to underlying news content
            comments_query = Comment.query.filter_by(
                content_type='news',
                content_id=chapter.news_id
            ).filter(
                Comment.is_approved == True,
                Comment.is_spam == False,
                Comment.is_deleted == False
            )
        
        # Get top-level comments only (no parent_id)
        comments_query = comments_query.filter_by(parent_id=None)
        
        # Paginate
        pagination = comments_query.order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        comments_data = []
        for comment in pagination.items:
            # Get user info
            user_data = None
            if comment.user:
                user_data = {
                    "id": comment.user.id,
                    "username": comment.user.username,
                    "display_name": getattr(comment.user, 'get_full_name', lambda: comment.user.username)()
                }
            
            # Count replies
            replies_count = Comment.query.filter_by(
                parent_id=comment.id
            ).filter(
                Comment.is_approved == True,
                Comment.is_spam == False,
                Comment.is_deleted == False
            ).count()
            
            comment_data = {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
                "user": user_data,
                "replies_count": replies_count,
                "likes": comment.get_likes_count(),
                "dislikes": comment.get_dislikes_count()
            }
            
            comments_data.append(comment_data)
        
        # Prepare pagination info
        pagination_info = {
            "page": page,
            "per_page": per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev
        }
        
        return jsonify({
            "comments": comments_data,
            "pagination": pagination_info,
            "content_type": content_type,
            "content_id": content_id
        })

    except Exception as e:
        current_app.logger.error(f"Error in simple comments API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# =============================================================================
# EXISTING PUBLIC API ENDPOINTS (with "public" prefix)
# =============================================================================

@main_blueprint.route("/api/public/albums/<int:album_id>", methods=["GET"])
def get_public_album_api(album_id):
    """
    Public API endpoint to retrieve a single album in JSON format.
    Returns the same data as the HTML album detail page.
    """
    try:
        album = Album.query.get_or_404(album_id)
        
        # Check if album is visible
        if not album.is_visible or album.is_archived:
            return jsonify({"error": "Album not found or not visible"}), 404
        
        # Get chapters for this album
        chapters = (
            AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
            .order_by(AlbumChapter.chapter_number)
            .all()
        )
        
        # Get related albums using refined similarity algorithm
        # Temporarily disabled to avoid import issues
        # from .routes_public import get_similar_albums
        # related_albums = get_similar_albums(album, limit=4)
        related_albums = []
        
        # Get albums by the same author/owner (excluding current)
        # Find albums that match either the author name OR the owner ID
        from sqlalchemy import or_
        
        author_albums = (
            Album.query.filter(
                or_(
                    # Match by author name (if author exists)
                    (Album.author == album.author) if album.author else False,
                    # Match by owner ID (if owner exists)
                    (Album.owner_id == album.owner_id) if album.owner_id else False,
                    # Fallback: match by creator ID
                    (Album.user_id == album.user_id) if not album.author and not album.owner_id else False
                ),
                Album.is_visible == True,
                Album.is_archived == False,
                Album.id != album_id
            )
            .order_by(Album.created_at.desc())
            .limit(6)
            .all()
        )
        
        # Prepare response data
        album_data = {
            "id": album.id,
            "title": album.title,
            "description": album.description,
            "is_premium": album.is_premium,
            "is_completed": album.is_completed,
            "is_hiatus": album.is_hiatus,
            "age_rating": album.age_rating,
            "total_chapters": album.total_chapters,
            "total_reads": album.total_reads,
            "total_views": album.total_views,
            "created_at": album.created_at.isoformat() if album.created_at else None,
            "updated_at": album.updated_at.isoformat() if album.updated_at else None,
            "category": {
                "id": album.category.id if album.category else None,
                "name": album.category.name if album.category else None,
                "description": album.category.description if album.category else None
            } if album.category else None,
            "author": album.author,  # This is now a string field
            "owner": {
                "id": album.owner.id if album.owner else None,
                "username": album.owner.username if album.owner else None,
                "display_name": album.owner.get_full_name() if album.owner else None,
                "avatar_url": album.owner.avatar_url if hasattr(album.owner, 'avatar_url') else None
            } if album.owner else None,
            "chapters": [{
                "id": ch.id,
                "chapter_number": ch.chapter_number,
                "chapter_title": ch.chapter_title,
                "is_visible": ch.is_visible,
                "created_at": ch.created_at.isoformat() if ch.created_at else None,
                "updated_at": ch.updated_at.isoformat() if ch.updated_at else None,
                "url": url_for("main.chapter_reader", 
                              album_id=album_id, 
                              chapter_id=ch.id, 
                              chapter_title=ch.chapter_title.replace(" ", "-").lower())
            } for ch in chapters],
            "related_albums": [{
                "id": rel.id,
                "title": rel.title,
                "description": rel.description,
                "is_premium": rel.is_premium,
                "total_chapters": rel.total_chapters,
                "total_reads": rel.total_reads,
                "cover_image_url": (rel.cover_image.to_dict().get("file_url") if rel.cover_image and hasattr(rel.cover_image, "to_dict") else (rel.cover_image.url if rel.cover_image else None)),
                "url": url_for("main.album_detail", 
                              album_id=rel.id, 
                              album_title=rel.title.replace(" ", "-").lower())
            } for rel in related_albums],
            "author_albums": [{
                "id": auth_album.id,
                "title": auth_album.title,
                "description": auth_album.description,
                "is_premium": auth_album.is_premium,
                "total_chapters": auth_album.total_chapters,
                "total_reads": auth_album.total_reads,
                "cover_image_url": (auth_album.cover_image.to_dict().get("file_url") if auth_album.cover_image and hasattr(auth_album.cover_image, "to_dict") else (auth_album.cover_image.url if auth_album.cover_image else None)),
                "url": url_for("main.album_detail", 
                              album_id=auth_album.id, 
                              album_title=auth_album.title.replace(" ", "-").lower())
            } for auth_album in author_albums]
        }
        
        # Add cover image if available
        if album.cover_image:
            album_data["cover_image"] = {
                "id": album.cover_image.id,
                "url": (album.cover_image.to_dict().get("file_url") if hasattr(album.cover_image, "to_dict") else None) or album.cover_image.url,
                "description": getattr(album.cover_image, "description", None),
                "filepath": getattr(album.cover_image, "filepath", None)
            }
        
        return jsonify(album_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in public album API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/public/news", methods=["GET"])
def get_public_news_list_api():
    """
    Public API endpoint to retrieve a list of news articles in JSON format.
    Returns the same data as the HTML news listing page.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        category_id = request.args.get('category', type=int)
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'latest')  # latest, popular, oldest
        
        # Build query
        query = News.query.filter_by(is_visible=True)
        
        # Apply category filter
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Apply search filter
        if search_query:
            search_filter = or_(
                News.title.ilike(f'%{search_query}%'),
                News.content.ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)
        
        # Apply sorting
        if sort_by == 'popular':
            query = query.order_by(desc(News.read_count))
        else:  # latest
            query = query.order_by(desc(News.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Prepare response data
        news_items = []
        for item in pagination.items:
            news_data = {
                "id": item.id,
                "title": item.title,
                "excerpt": (item.content[:200] + "..." if item.content and len(item.content) > 200 else item.content),
                "is_premium": item.is_premium,
                "is_news": item.is_news,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "read_count": item.read_count,
                
                "category": {
                    "id": item.category.id if item.category else None,
                    "name": item.category.name if item.category else None
                } if item.category else None
            }
            
            # Add image if available
            if item.image:
                news_data["header_image"] = {
                    "url": (item.image.to_dict().get("file_url") if hasattr(item.image, "to_dict") else None) or item.image.url,
                    "description": getattr(item.image, "description", None)
                }
            
            news_items.append(news_data)
        
        # Get categories for filtering
        categories = Category.query.filter_by(is_active=True).all()
        category_options = [
            {"id": cat.id, "name": cat.name} for cat in categories
        ]
        
        response_data = {
            "news": news_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "filters": {
                "categories": category_options,
                "current_category": category_id,
                "current_search": search_query,
                "current_sort": sort_by
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in public news list API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/public/albums", methods=["GET"])
def get_public_albums_list_api():
    """
    Public API endpoint to retrieve a list of albums in JSON format.
    Returns the same data as the HTML albums listing page.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        category_id = request.args.get('category', type=int)
        search_query = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'latest')  # latest, popular, oldest, alphabetical
        status_filter = request.args.get('status', 'all')  # all, ongoing, completed, hiatus
        
        # Build query
        query = Album.query.filter_by(is_visible=True, is_archived=False)
        
        # Apply category filter
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Apply search filter
        if search_query:
            search_filter = or_(
                Album.title.ilike(f'%{search_query}%'),
                Album.description.ilike(f'%{search_query}%')
            )
            query = query.filter(search_filter)
        
        # Apply status filter
        if status_filter == 'ongoing':
            query = query.filter_by(is_completed=False, is_hiatus=False)
        elif status_filter == 'completed':
            query = query.filter_by(is_completed=True)
        elif status_filter == 'hiatus':
            query = query.filter_by(is_hiatus=True)
        
        # Apply sorting
        if sort_by == 'popular':
            query = query.order_by(desc(Album.total_reads))
        elif sort_by == 'alphabetical':
            query = query.order_by(Album.title)
        else:  # latest
            query = query.order_by(desc(Album.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Prepare response data
        albums_data = []
        for album in pagination.items:
            album_data = {
                "id": album.id,
                "title": album.title,
                "description": album.description,
                "is_premium": album.is_premium,
                "is_completed": album.is_completed,
                "is_hiatus": album.is_hiatus,
                "total_chapters": album.total_chapters,
                "total_reads": album.total_reads,
                "total_views": album.total_views,
                "created_at": album.created_at.isoformat() if album.created_at else None,
                "updated_at": album.updated_at.isoformat() if album.updated_at else None,
                "category": {
                    "id": album.category.id if album.category else None,
                    "name": album.category.name if album.category else None
                } if album.category else None,
                # Album.author is a string; expose directly. Include owner details if available.
                "author": album.author,
                "owner": {
                    "id": album.owner.id if album.owner else None,
                    "username": album.owner.username if album.owner else None,
                    "display_name": album.owner.get_full_name() if album.owner else None
                } if album.owner else None
            }
            
            # Add cover image if available
            if album.cover_image:
                album_data["cover_image"] = {
                    "url": (album.cover_image.to_dict().get("file_url") if hasattr(album.cover_image, "to_dict") else None) or album.cover_image.url,
                    "description": getattr(album.cover_image, "description", None)
                }
            
            albums_data.append(album_data)
        
        # Get categories for filtering
        categories = Category.query.filter_by(is_active=True).all()
        category_options = [
            {"id": cat.id, "name": cat.name} for cat in categories
        ]
        
        response_data = {
            "albums": albums_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "filters": {
                "categories": category_options,
                "current_category": category_id,
                "current_search": search_query,
                "current_sort": sort_by,
                "current_status": status_filter
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Error in public albums list API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main_blueprint.route("/api/public/search", methods=["GET"])
def public_search_api():
    """
    Public search API endpoint for searching across news, albums, and users.
    """
    try:
        query = request.args.get('q', '').strip()
        content_type = request.args.get('type', 'all')  # all, news, albums, users
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not query:
            return jsonify({"error": "Search query is required"}), 400
        
        results = {
            "query": query,
            "content_type": content_type,
            "total_results": 0,
            "results": {}
        }
        
        # Search news
        if content_type in ['all', 'news']:
            news_results = News.query.filter(
                and_(
                    News.is_visible == True,
                    or_(
                        News.title.ilike(f'%{query}%'),
                        News.content.ilike(f'%{query}%')
                    )
                )
            ).order_by(desc(News.created_at)).limit(per_page).all()
            
            results["results"]["news"] = [
                {
                    "id": news.id,
                    "title": news.title,
                    "excerpt": (news.content[:200] + "..." if news.content and len(news.content) > 200 else news.content),
                    "created_at": news.created_at.isoformat() if news.created_at else None,
                    "read_count": news.read_count,
                    "is_premium": news.is_premium,
                    "category": {
                        "id": news.category.id if news.category else None,
                        "name": news.category.name if news.category else None
                    } if news.category else None
                } for news in news_results
            ]
            results["total_results"] += len(news_results)
        
        # Search albums
        if content_type in ['all', 'albums']:
            album_results = Album.query.filter(
                and_(
                    Album.is_visible == True,
                    or_(
                        Album.title.ilike(f'%{query}%'),
                        Album.description.ilike(f'%{query}%')
                    )
                )
            ).order_by(desc(Album.created_at)).limit(per_page).all()
            
            results["results"]["albums"] = [
                {
                    "id": album.id,
                    "title": album.title,
                    "description": album.description,
                    "created_at": album.created_at.isoformat() if album.created_at else None,
                    "total_views": album.total_views,
                    "is_completed": album.is_completed,
                    "cover_image_url": (album.cover_image.to_dict().get("file_url") if album.cover_image and hasattr(album.cover_image, "to_dict") else (album.cover_image.url if album.cover_image else None))
                } for album in album_results
            ]
            results["total_results"] += len(album_results)
        
        # Search users
        if content_type in ['all', 'users']:
            user_results = User.query.filter(
                or_(
                    User.username.ilike(f'%{query}%'),
                    User.first_name.ilike(f'%{query}%')
                )
            ).limit(per_page).all()
            
            results["results"]["users"] = [
                {
                    "id": user.id,
                    "username": user.username,
                    "display_name": user.get_full_name() if hasattr(user, 'get_full_name') else user.username,
                    "avatar_url": user.avatar_url if hasattr(user, 'avatar_url') else None,
                    "is_verified": user.verified
                } for user in user_results
            ]
            results["total_results"] += len(user_results)
        
        # Add pagination info
        results["pagination"] = {
            "page": page,
            "per_page": per_page
        }

        return jsonify(results)
        
    except Exception as e:
        current_app.logger.error(f"Error in public search API: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
