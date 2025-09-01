from routes import main_blueprint
from .common_imports import *
from models import Album, AlbumChapter, News, Category, CategoryGroup, Image, User, UserRole, Rating, default_utcnow
from optimizations import cache_with_args, cache_query_result, CACHE_TIMEOUTS
from optimizations import optimize_news_query, optimize_image_query, monitor_ssr_render
from optimizations.cache_config import safe_cache_get, safe_cache_set
import time
import markdown
import re
from sqlalchemy import func, desc

def safe_title(title):
    """Convert title to URL-safe format."""
    if not title:
        return ""
    # Remove special characters and replace spaces with hyphens
    import re
    safe = re.sub(r'[^\w\s-]', '', title.lower())
    safe = re.sub(r'[-\s]+', '-', safe)
    return safe.strip('-')

# Context processor to make navigation links and brand info available to all templates
@main_blueprint.context_processor
def inject_navigation_links():
    """Inject navigation links and brand info into all templates."""
    try:
        navbar_links = NavigationLink.query.filter_by(
            location='navbar', 
            is_active=True
        ).order_by(NavigationLink.order).all()
        
        footer_links = NavigationLink.query.filter_by(
            location='footer', 
            is_active=True
        ).order_by(NavigationLink.order).all()
        
        # Get brand identity info
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        if not brand_info:
            brand_info = BrandIdentity()
            db.session.add(brand_info)
            db.session.commit()
        
        return {
            'navbar_links': navbar_links,
            'footer_links': footer_links,
            'brand_info': brand_info
        }
    except Exception as e:
        # If there's an error (e.g., table doesn't exist yet), return empty lists
        print(f"Warning: Could not load navigation links or brand info: {e}")
        return {
            'navbar_links': [],
            'footer_links': [],
            'brand_info': None
        }

@main_blueprint.route("/force-scaling-test")
def force_scaling_test():
    """Test page for force scaling functionality."""
    return render_template('public/force-scaling-test.html')

@main_blueprint.route("/")
@main_blueprint.route("/beranda")
@main_blueprint.route("/home")
def home():
    # Get main featured news with optimized query
    main_news_query = (
        News.query.filter_by(is_visible=True, is_main_news=True)
        .order_by(News.created_at.desc())
        .limit(5)
    )
    main_news = optimize_news_query(main_news_query).all()
    
    # Get latest articles (is_news=False, articles)
    latest_articles_query = (
        News.query.filter_by(is_visible=True, is_news=False)
        .order_by(News.created_at.desc())
        .limit(5)
    )
    latest_articles = optimize_news_query(latest_articles_query).all()
    
    # Get latest news (is_news=True, news)
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
    
    # Get latest YouTube videos
    latest_videos = (
        YouTubeVideo.query.filter_by(is_visible=True)
        .order_by(YouTubeVideo.created_at.desc())
        .limit(4)  # Fetching 4 videos to display in 4 columns
        .all()
    )

    # ---  QUERY for Latest Images ---
    latest_images_query = (
        Image.query.filter_by(is_visible=True)
        .order_by(Image.created_at.desc())
        .limit(5)  # Fetch the latest 5 images
    )
    latest_images = optimize_image_query(latest_images_query).all()

    # Get featured albums (most popular and highest rated)
    featured_albums_query = (
        Album.query.filter_by(is_visible=True, is_archived=False)
        .join(Category, Album.category_id == Category.id)
        .join(User, Album.user_id == User.id)
        .order_by(Album.total_reads.desc())
        .limit(6)  # Show 6 featured albums
    )
    featured_albums = featured_albums_query.all()

    # Add rating information to news and articles
    for news_list in [main_news, latest_articles, latest_news, popular_news]:
        for news_item in news_list:
            avg_rating = Rating.get_average_rating('news', news_item.id)
            rating_count = Rating.get_rating_count('news', news_item.id)
            news_item.rating = {
                'average': avg_rating,
                'count': rating_count,
                'has_ratings': rating_count > 0
            }

    # Add rating information to albums
    for album in featured_albums:
        avg_rating = Rating.get_average_rating('album', album.id)
        rating_count = Rating.get_rating_count('album', album.id)
        album.rating = {
            'average': avg_rating,
            'count': rating_count,
            'has_ratings': rating_count > 0
        }
    
    # SSR monitoring
    monitor_ssr_render("home")(lambda: None)()
    
    # Get brand info to check homepage design preference
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    homepage_design = brand_info.homepage_design if brand_info else 'news'
    
    # Get additional data for albums design
    latest_albums = None
    popular_albums = None
    best_albums = None
    ongoing_albums = None
    best_completed_albums = None
    categories = None
    
    # Get categories for both designs
    if homepage_design == 'albums':
        # Get latest albums for albums design
        latest_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .join(User, Album.user_id == User.id)
            .order_by(Album.created_at.desc())
            .limit(8)
        )
        latest_albums = latest_albums_query.all()
        
        # Get popular albums for albums design
        popular_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .join(User, Album.user_id == User.id)
            .order_by(Album.total_reads.desc())
            .limit(8)
        )
        popular_albums = popular_albums_query.all()
        
        # Get best albums (highest rated)
        best_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .join(User, Album.user_id == User.id)
            .join(Rating, db.and_(Rating.content_type == 'album', Rating.content_id == Album.id))
            .group_by(Album.id)
            .order_by(db.func.avg(Rating.rating_value).desc())
            .limit(8)
        )
        best_albums = best_albums_query.all()
        
        # Get ongoing albums (not completed, not hiatus)
        ongoing_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .filter(Album.is_completed == False, Album.is_hiatus == False)
            .join(User, Album.user_id == User.id)
            .order_by(Album.total_reads.desc(), Album.created_at.desc())
            .limit(8)
        )
        ongoing_albums = ongoing_albums_query.all()
        
        # Get best completed albums (combination of rating, recency, reads, popularity)
        best_completed_albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False, is_completed=True)
            .join(User, Album.user_id == User.id)
            .join(Rating, db.and_(Rating.content_type == 'album', Rating.content_id == Album.id))
            .group_by(Album.id)
            .order_by(
                db.func.avg(Rating.rating_value).desc(),
                Album.total_reads.desc(),
                Album.created_at.desc()
            )
            .limit(8)
        )
        best_completed_albums = best_completed_albums_query.all()
        
        # Get categories that are actually used by albums with album counts
        categories_with_counts = (
            db.session.query(
                Category,
                db.func.count(Album.id).label('album_count')
            )
            .join(Album, Category.id == Album.category_id)
            .filter(Album.is_visible == True, Album.is_archived == False)
            .group_by(Category.id, Category.name)
            .having(db.func.count(Album.id) > 0)  # Only categories with albums
            .order_by(db.func.count(Album.id).desc())
            .all()
        )
        
        # Convert to list of categories with album_count attribute
        categories = []
        for category, count in categories_with_counts:
            category.album_count = count
            categories.append(category)
        
        # Add rating information to albums
        for album_list in [latest_albums, popular_albums, best_albums, ongoing_albums, best_completed_albums]:
            for album_item in album_list:
                avg_rating = Rating.get_average_rating('album', album_item.id)
                rating_count = Rating.get_rating_count('album', album_item.id)
                album_item.rating = {
                    'average': avg_rating,
                    'count': rating_count,
                    'has_ratings': rating_count > 0
                }
    else:
        # Get categories for news design (pointing to news.html)
        categories_with_counts = (
            db.session.query(
                Category,
                db.func.count(News.id).label('news_count')
            )
            .join(News, Category.id == News.category_id)
            .filter(News.is_visible == True)
            .group_by(Category.id, Category.name)
            .having(db.func.count(News.id) > 0)  # Only categories with news
            .order_by(db.func.count(News.id).desc())
            .all()
        )
        
        # Convert to list of categories with news_count attribute
        categories = []
        for category, count in categories_with_counts:
            category.news_count = count
            categories.append(category)
    
    # Choose template based on design preference
    template_name = 'public/index_albums.html' if homepage_design == 'albums' else 'public/index.html'
    
    return render_template(
        template_name,
        main_news=main_news,
        latest_articles=latest_articles,
        latest_news=latest_news,
        popular_news=popular_news,
        latest_videos=latest_videos,
        latest_images=latest_images,
        featured_albums=featured_albums,
        latest_albums=latest_albums,
        popular_albums=popular_albums,
        best_albums=best_albums,
        ongoing_albums=ongoing_albums,
        best_completed_albums=best_completed_albums,
        categories=categories
    )


@main_blueprint.route("/videos")
def videos():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    query = request.args.get("q", "")

    video_query = YouTubeVideo.query.filter_by(is_visible=True)
    if query:
        video_query = video_query.filter(YouTubeVideo.youtube_id.ilike(f"%{query}%"))

    videos_paginated = video_query.order_by(YouTubeVideo.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Fetch titles using oEmbed with caching
    for video in videos_paginated.items:
        try:
            # Cache oEmbed requests
            cache_key = f"oembed_{video.youtube_id}"
            cached_title = safe_cache_get(cache_key)
            
            if cached_title:
                video.title = cached_title
            else:
                response = requests.get(
                    f"https://www.youtube.com/oembed?url={video.link}&format=json"
                )
                data = response.json()
                video.title = data.get("title", video.youtube_id)
                # Cache for 1 hour
                safe_cache_set(cache_key, video.title, timeout=3600)
        except Exception as e:
            print(f"Error fetching oEmbed for {video.youtube_id}: {e}")
            video.title = video.youtube_id  # Fallback

    return render_template("public/videos.html", videos=videos_paginated, query=query)


@main_blueprint.route("/news")
@cache_with_args(timeout=CACHE_TIMEOUTS['news_list'], key_prefix='news_list')
@monitor_ssr_render("news_list")
def news():
    page = request.args.get("page", 1, type=int)
    per_page = 12
    content_type = request.args.get("type", "general")
    
    # Fetch all visible news articles (is_news=True)
    news_list = (
        News.query.filter_by(is_news=True, is_visible=True)
        .order_by(News.created_at.desc())
        .paginate(page=page, per_page=per_page)
    )

    # Fetch all tags
    tags = get_all_tags()
    
    return render_template(
        "public/news.html",
        news=news_list,
        all_tags=tags,
        query=None,
        category=None,
        tag=None,
        type=content_type,
    )


@main_blueprint.route("/hypes")
@monitor_ssr_render("hypes")
def hypes():
    # Redirect to unified news page with news type
    return redirect(url_for('main.news', type='news'))


@main_blueprint.route("/articles")
@monitor_ssr_render("articles")
def articles():
    # Redirect to unified news page with articles type
    return redirect(url_for('main.news', type='articles'))


@main_blueprint.route("/utama")
def utama():
    # Redirect to unified news page with utama type
    return redirect(url_for('main.news', type='utama'))


@main_blueprint.route("/gallery")
@monitor_ssr_render("gallery")
def gallery():
    """Displays a paginated gallery of visible images."""
    page = request.args.get("page", 1, type=int)
    per_page = 15

    images_query = Image.query.filter_by(is_visible=True).order_by(
        Image.created_at.desc()
    )
    images_paginated = images_query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Fetch categories and tags for the sidebar/context (if your base template needs them)
    # categories = Category.query.all()
    # tags_response = get_tags() # Assuming get_tags returns a Response object
    # tags = tags_response.json if tags_response.status_code == 200 else []
    # If you use a context processor for categories/tags, you might not need them here.

    return render_template(
        "public/gallery.html",
        images=images_paginated,
        # categories=categories, # Pass if needed
        # tags=tags              # Pass if needed
    )


# ----------------------
# 📰 info Routes
# ----------------------


@main_blueprint.route("/about")
def about():
    # Fetch active team members by group
    leadership = (
        TeamMember.query.filter_by(group="leadership", is_active=True)
        .order_by(TeamMember.member_order)
        .all()
    )
    editorial = (
        TeamMember.query.filter_by(group="editorial", is_active=True)
        .order_by(TeamMember.member_order)
        .all()
    )
    news_team = (
        TeamMember.query.filter_by(group="news", is_active=True)
        .order_by(TeamMember.member_order)
        .all()
    )
    video_team = (
        TeamMember.query.filter_by(group="video", is_active=True)
        .order_by(TeamMember.member_order)
        .all()
    )
    sales_team = (
        TeamMember.query.filter_by(group="sales", is_active=True)
        .order_by(TeamMember.member_order)
        .all()
    )
    # Fetch active contact details for Contact section
    contact_details = (
        ContactDetail.query.filter_by(is_active=True)
        .order_by(ContactDetail.section_order)
        .all()
    )
    return render_template(
        "public/about.html",
        leadership=leadership,
        editorial=editorial,
        news_team=news_team,
        video_team=video_team,
        sales_team=sales_team,
        contact_details=contact_details,
    )


@main_blueprint.route("/search", methods=["GET"])
def search():
    """Search for news articles based on query, category, or tags."""
    query = request.args.get("q", "").strip()
    selected_category_name = request.args.get("category", "").strip()
    selected_tag_name = request.args.get("tag", "").strip()
    
    # Build redirect URL with search parameters
    redirect_url = url_for('main.news')
    params = []
    
    if query:
        params.append(f"q={query}")
    if selected_category_name:
        params.append(f"category={selected_category_name}")
    if selected_tag_name:
        params.append(f"tag={selected_tag_name}")
    
    if params:
        redirect_url += "?" + "&".join(params)
    
    return redirect(redirect_url)

# ----------------------
# 📰 News Routes
# ----------------------


@main_blueprint.route("/news/<int:news_id>/<path:news_title>")
@monitor_ssr_render("news_detail")
def news_detail(news_id, news_title):
    from .utils.premium_content import process_premium_content, get_premium_content_stats
    
    news_item = News.query.get_or_404(news_id)

    # Check visibility *before* doing anything else
    # Allow admin access regardless of visibility status
    if not news_item.is_visible:
        # Check if user is admin or accessing from admin context
        is_admin_access = False
        if current_user.is_authenticated:
            # Allow if user is admin/superuser
            if current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
                is_admin_access = True
            # Allow if user is the author
            elif news_item.user_id == current_user.id:
                is_admin_access = True
            # Allow if user has custom role with news permissions
            elif current_user.custom_role and current_user.custom_role.is_active:
                for permission in current_user.custom_role.permissions:
                    if permission.resource == "news" and permission.action in ["read", "update", "delete"]:
                        is_admin_access = True
                        break
        
        # Check if accessing from admin referer
        referer = request.headers.get('Referer', '')
        if '/admin/' in referer or '/settings/' in referer:
            is_admin_access = True
        
        if not is_admin_access:
            current_app.logger.warning(
                f"Attempt to access non-visible news item ID: {news_id}"
            )
            abort(404)

    # --- Premium Content Processing ---
    # Check if content is premium
    is_premium_content = news_item.is_premium
    
    # Process content based on premium status
    processed_content, is_truncated, show_premium_notice = process_premium_content(
        news_item.content or "",
        is_premium_content,
        max_words=150  # Show first 150 words for non-premium users
    )
    
    # Get content statistics
    content_stats = get_premium_content_stats(news_item.content or "", is_premium_content)

    # --- Convert Markdown to HTML ---
    # Use 'extra' for features like footnotes, abbr, def_list, etc.
    # Also include fenced_code and tables explicitly if not covered by 'extra' in your version
    # Add 'sane_lists' for potentially better list handling.
    try:
        html_content = markdown.markdown(
            processed_content,  # Use processed content instead of original
            extensions=["fenced_code", "tables", "extra", "sane_lists"],
        )
        # IMPORTANT: Do NOT modify news_item.content here. Pass the generated HTML
        # separately or add it as a temporary attribute if needed elsewhere in template.
        # Let's pass it separately for clarity.
    except Exception as e:
        current_app.logger.error(
            f"Markdown conversion failed for news ID {news_id}: {e}"
        )
        # Decide how to handle: show raw content, show error, or abort?
        # For now, let's pass empty string, but logging the error is crucial.
        html_content = (
            "<p><em>Error rendering content.</em></p>"
        )  # Provide fallback HTML

    # --- Increment Reads and record reading history ---
    try:
        news_item.increment_reads()
        # Record reading history for logged-in users
        if current_user.is_authenticated:
            from models import ReadingHistory
            history = ReadingHistory.query.filter_by(
                user_id=current_user.id, content_type='news', content_id=news_id
            ).first()
            if history:
                history.read_count = (history.read_count or 0) + 1
            else:
                history = ReadingHistory(
                    user_id=current_user.id,
                    content_type='news',
                    content_id=news_id,
                    read_count=1,
                )
                db.session.add(history)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update read count/history for news ID {news_id}: {e}")

    # --- Fetch Related News ---
    # Fetch related news (same category, excluding the current news)
    related_news_query = (
        News.query.filter(
            News.category_id == news_item.category_id,  # Assuming category_id is the FK
            News.id != news_id,
            News.is_visible == True,
        )
        .order_by(News.created_at.desc())
        .limit(6)
    )  # Order by creation date makes sense
    related_news = related_news_query.all()

    # --- Fetch Popular News (if needed) ---
    needed_more = 6 - len(related_news)
    if needed_more > 0:
        # Calculate popularity score (share count + read count)
        # Ensure NULL counts are treated as 0 using coalesce or func.coalesce
        popularity_score = (
            func.coalesce(ShareLog.whatsapp_count, 0)
            + func.coalesce(ShareLog.facebook_count, 0)
            + func.coalesce(ShareLog.twitter_count, 0)
            + func.coalesce(ShareLog.instagram_count, 0)
            + func.coalesce(ShareLog.bluesky_count, 0)
            + func.coalesce(ShareLog.clipboard_count, 0)
            + func.coalesce(News.read_count, 0)  # Also coalesce read_count
        ).label("popularity_score")

        # Exclude IDs already in related_news
        exclude_ids = [news_id] + [r.id for r in related_news]

        popular_news_items = (
            db.session.query(News, popularity_score)
            .outerjoin(ShareLog, News.id == ShareLog.news_id)
            .filter(
                News.id.notin_(
                    exclude_ids
                ),  # Exclude current and already selected related
                News.is_visible == True,
            )
            .order_by(popularity_score.desc())
            .limit(needed_more)
            .all()
        )

        # Extract just the News objects
        popular_news = [item[0] for item in popular_news_items]
        related_news.extend(popular_news)

    # --- Render Template ---
    # Pass the original news object AND the generated HTML content separately
    return render_template(
        "public/reader.html",
        news=news_item,
        html_content=html_content,
        is_premium_content=is_premium_content,
        is_truncated=is_truncated,
        show_premium_notice=show_premium_notice,
        content_stats=content_stats,
        related_news=related_news,
    )

@main_blueprint.route("/news/<int:news_id>")
def news_detail_legacy(news_id):
    """
    Legacy route that redirects old URLs to new SEO-friendly URLs
    """
    # Fetch the news item to get its title
    news_item = News.query.get_or_404(news_id)
    
    # Check visibility before redirecting
    # Allow admin access regardless of visibility status
    if not news_item.is_visible:
        # Check if user is admin or accessing from admin context
        is_admin_access = False
        if current_user.is_authenticated:
            # Allow if user is admin/superuser
            if current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
                is_admin_access = True
            # Allow if user is the author
            elif news_item.user_id == current_user.id:
                is_admin_access = True
            # Allow if user has custom role with news permissions
            elif current_user.custom_role and current_user.custom_role.is_active:
                for permission in current_user.custom_role.permissions:
                    if permission.resource == "news" and permission.action in ["read", "update", "delete"]:
                        is_admin_access = True
                        break
        
        # Check if accessing from admin referer
        referer = request.headers.get('Referer', '')
        if '/admin/' in referer or '/settings/' in referer:
            is_admin_access = True
        
        if not is_admin_access:
            current_app.logger.warning(
                f"Attempt to access non-visible news item ID: {news_id}"
            )
            abort(404)
    
    # Generate the safe title for the URL using the top-level function
    safe_title_result = safe_title(news_item.title)
    
    # Redirect to the new URL pattern
    return redirect(url_for('main.news_detail', 
                          news_id=news_id, 
                          news_title=safe_title_result), 
                  code=301)  # 301 is permanent redirect, good for SEO


@main_blueprint.route("/api/categories", methods=["GET"])
def get_categories():
    """Fetch all categories."""
    # Check if we want grouped categories or flat list
    grouped = request.args.get('grouped', 'false').lower() == 'true'
    
    if grouped:
        # Fetch categories grouped by their groups
        groups = CategoryGroup.query.filter_by(is_active=True).order_by(CategoryGroup.display_order).all()
        result = []
        
        for group in groups:
            group_categories = Category.query.filter_by(
                group_id=group.id, 
                is_active=True
            ).order_by(Category.display_order).all()
            
            if group_categories:  # Only include groups with categories
                result.append({
                    "group": group.to_dict(),
                    "categories": [cat.to_dict() for cat in group_categories]
                })
        
        return jsonify(result)
    else:
        # Fetch all categories as flat list (for backward compatibility)
        categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
        return jsonify([cat.to_dict() for cat in categories])


def get_all_tags():
    """Fetch all unique tags from the news articles."""
    tags = db.session.query(News.tagar).distinct().all()
    # Flatten the list of tuples and split comma-separated tags
    tag_list = []
    for tag in tags:
        if tag[0]:
            tag_list.extend(tag[0].split(","))
    # Remove duplicates and empty strings
    unique_tags = list(set(tag.strip() for tag in tag_list if tag.strip()))
    return unique_tags

@main_blueprint.route("/api/tags", methods=["GET"])
def get_tags():
    """API endpoint to fetch all unique tags from the news articles."""
    return jsonify(get_all_tags())


@main_blueprint.route("/premium")
def premium():
    """Premium subscription page."""
    return render_template("public/premium.html")


def get_similar_albums(album, limit=6):
    """
    Get similar albums using a multi-factor similarity algorithm.
    
    Factors considered:
    1. Category similarity (40% weight)
    2. Author similarity (30% weight) 
    3. Content similarity based on tags/description (20% weight)
    4. Popularity/read count (10% weight)
    """
    try:
        # Get all visible, non-archived albums excluding the current one
        all_albums = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .filter(Album.id != album.id)
            .all()
        )
        
        if not all_albums:
            return []
        
        # Calculate similarity scores for each album
        album_scores = []
        
        for other_album in all_albums:
            score = 0.0
            
            # 1. Category similarity (40% weight)
            if album.category_id and other_album.category_id:
                if album.category_id == other_album.category_id:
                    score += 0.4
                elif album.category and other_album.category:
                    # Partial category similarity (same category type)
                    if album.category.name == other_album.category.name:
                        score += 0.3
            
            # 2. Author similarity (30% weight)
            if album.user_id == other_album.user_id:
                score += 0.3
            
            # 3. Content similarity based on tags/description (20% weight)
            content_similarity = 0.0
            
            # Compare descriptions
            if album.description and other_album.description:
                # Simple word overlap
                album_words = set(re.findall(r'\w+', album.description.lower()))
                other_words = set(re.findall(r'\w+', other_album.description.lower()))
                
                if album_words and other_words:
                    overlap = len(album_words.intersection(other_words))
                    total = len(album_words.union(other_words))
                    if total > 0:
                        content_similarity = overlap / total
            
            # Compare tags if available
            if hasattr(album, 'tags') and hasattr(other_album, 'tags'):
                if album.tags and other_album.tags:
                    album_tags = set(tag.strip().lower() for tag in album.tags.split(','))
                    other_tags = set(tag.strip().lower() for tag in other_album.tags.split(','))
                    
                    if album_tags and other_tags:
                        tag_overlap = len(album_tags.intersection(other_tags))
                        tag_total = len(album_tags.union(other_tags))
                        if tag_total > 0:
                            content_similarity = max(content_similarity, tag_overlap / tag_total)
            
            score += content_similarity * 0.2
            
            # 4. Popularity/read count (10% weight)
            # Normalize read counts to 0-1 scale
            max_reads = max(album.total_reads or 0, other_album.total_reads or 0, 1)
            popularity_score = (other_album.total_reads or 0) / max_reads
            score += popularity_score * 0.1
            
            # Additional bonus for recent albums (temporal proximity)
            if album.created_at and other_album.created_at:
                days_diff = abs((album.created_at - other_album.created_at).days)
                if days_diff <= 30:  # Within 30 days
                    score += 0.05
                elif days_diff <= 90:  # Within 90 days
                    score += 0.02
            
            album_scores.append((other_album, score))
        
        # Sort by similarity score (descending) and return top results
        album_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [album for album, score in album_scores[:limit]]
        
    except Exception as e:
        current_app.logger.error(f"Error calculating album similarity: {e}")
        # Fallback to simple category-based approach
        return (
            Album.query.filter_by(
                category_id=album.category_id,
                is_visible=True,
                is_archived=False
            )
            .filter(Album.id != album.id)
            .order_by(desc(Album.total_reads))
            .limit(limit)
            .all()
        )


@main_blueprint.route("/test-ssr")
@monitor_ssr_render("test_ssr")
def test_ssr():
    return "SSR Test"


@main_blueprint.route("/settings/navigation")
@login_required
def navigation_management():
    """Navigation links management page."""
    # Define available internal links for the dropdown (PUBLIC ROUTES ONLY)
    internal_links = [
        # Main pages
        {"name": "Beranda", "url": "/"},
        {"name": "Beranda (Alternatif)", "url": "/beranda"},
        {"name": "Berita", "url": "/news"},
        {"name": "Artikel", "url": "/articles"},
        {"name": "Hypes", "url": "/hypes"},
        {"name": "Utama", "url": "/utama"},
        {"name": "Galeri", "url": "/gallery"},
        {"name": "Videos", "url": "/videos"},
        {"name": "Tentang Kami", "url": "/about"},
        {"name": "Premium", "url": "/premium"},
        {"name": "Pencarian", "url": "/search"},
        
        # Album pages
        {"name": "Album Cerita", "url": "/albums"},
        {"name": "Album Detail (Template)", "url": "/album/1/contoh-album"},
        {"name": "Chapter Reader (Template)", "url": "/album/1/chapter/1/contoh-bab"},
        
        # System pages
        {"name": "Sitemap XML", "url": "/sitemap.xml"},
        {"name": "Sitemap News", "url": "/sitemap-news.xml"},
        {"name": "Sitemap Index", "url": "/sitemap-index.xml"},
        {"name": "Robots.txt", "url": "/robots.txt"},
        
        # API endpoints (public only)
        {"name": "API Categories", "url": "/api/categories"},
        {"name": "API Tags", "url": "/api/tags"},
    ]
    
    return render_template('admin/brand/navigation_management.html', internal_links=internal_links)

# Navigation Links API Routes
@main_blueprint.route("/api/navigation-links", methods=["GET"])
@login_required
def get_navigation_links():
    """Get all navigation links."""
    try:
        links = NavigationLink.query.order_by(NavigationLink.location, NavigationLink.order).all()
        return jsonify([link.to_dict() for link in links])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/api/navigation-links", methods=["POST"])
@login_required
def create_navigation_link():
    """Create a new navigation link."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["name", "url", "location"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Field '{field}' is required"}), 400
        
        # Create new navigation link
        new_link = NavigationLink(
            name=data["name"],
            url=data["url"],
            location=data["location"],
            order=data.get("order", 0),
            is_active=data.get("is_active", True),
            is_external=data.get("is_external", False),
            user_id=current_user.id
        )
        
        db.session.add(new_link)
        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify(new_link.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/api/navigation-links/<int:link_id>", methods=["PUT"])
@login_required
def update_navigation_link(link_id):
    """Update a navigation link."""
    try:
        link = NavigationLink.query.get_or_404(link_id)
        data = request.get_json()
        
        # Update fields
        if "name" in data:
            link.name = data["name"]
        if "url" in data:
            link.url = data["url"]
        if "location" in data:
            link.location = data["location"]
        if "order" in data:
            link.order = data["order"]
        if "is_active" in data:
            link.is_active = data["is_active"]
        if "is_external" in data:
            link.is_external = data["is_external"]
        
        link.user_id = current_user.id
        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify(link.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/api/navigation-links/<int:link_id>", methods=["DELETE"])
@login_required
def delete_navigation_link(link_id):
    """Delete a navigation link."""
    try:
        link = NavigationLink.query.get_or_404(link_id)
        db.session.delete(link)
        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify({"message": "Navigation link deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_blueprint.route("/api/navigation-links/bulk-update", methods=["POST"])
@login_required
def bulk_update_navigation_links():
    """Bulk update navigation links order and visibility."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        data = request.get_json()
        if not data or 'links' not in data:
            return jsonify({"error": "Invalid data format"}), 400

        links_data = data['links']
        
        for link_data in links_data:
            link_id = link_data.get('id')
            if not link_id:
                continue
                
            link = NavigationLink.query.get(link_id)
            if link:
                link.order = link_data.get('order', link.order)
                link.is_active = link_data.get('is_active', link.is_active)
                link.updated_at = default_utcnow()

        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify({"message": "Navigation links updated successfully"})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error bulk updating navigation links: {e}")
        return jsonify({"error": "Failed to update navigation links"}), 500


@main_blueprint.route("/api/navigation-links/bulk-status", methods=["PUT"])
@login_required
def bulk_update_navigation_status():
    """Bulk update navigation links status (activate/deactivate)."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        data = request.get_json()
        current_app.logger.info(f"Received bulk update data: {data}")
        
        if not data or 'link_ids' not in data or 'is_active' not in data:
            current_app.logger.error(f"Invalid data format: {data}")
            return jsonify({"error": "Invalid data format"}), 400

        link_ids = data['link_ids']
        is_active = data['is_active']
        current_app.logger.info(f"Processing {len(link_ids)} links, setting is_active to {is_active}")
        
        updated_count = 0
        for link_id in link_ids:
            current_app.logger.info(f"Processing link ID: {link_id}")
            link = NavigationLink.query.get(link_id)
            if link:
                current_app.logger.info(f"Found link: {link.name}, current is_active: {link.is_active}")
                link.is_active = is_active
                link.updated_at = default_utcnow()
                updated_count += 1
                current_app.logger.info(f"Updated link {link.name} to is_active: {is_active}")
            else:
                current_app.logger.warning(f"Link with ID {link_id} not found")

        current_app.logger.info(f"Committing {updated_count} updates to database")
        db.session.commit()
        current_app.logger.info("Database commit successful")
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
            current_app.logger.info("Cache invalidation successful")
        except ImportError:
            current_app.logger.warning("Cache invalidation module not available")
            pass
        
        return jsonify({
            "message": f"Successfully updated {updated_count} navigation links",
            "updated_count": updated_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error bulk updating navigation links status: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to update navigation links: {str(e)}"}), 500


@main_blueprint.route("/api/navigation-links/bulk-delete", methods=["DELETE"])
@login_required
def bulk_delete_navigation_links():
    """Bulk delete navigation links."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        data = request.get_json()
        if not data or 'link_ids' not in data:
            return jsonify({"error": "Invalid data format"}), 400

        link_ids = data['link_ids']
        deleted_count = 0
        
        for link_id in link_ids:
            link = NavigationLink.query.get(link_id)
            if link:
                db.session.delete(link)
                deleted_count += 1

        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify({
            "message": f"Successfully deleted {deleted_count} navigation links",
            "deleted_count": deleted_count
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error bulk deleting navigation links: {e}")
        return jsonify({"error": "Failed to delete navigation links"}), 500


@main_blueprint.route("/api/navigation-links/copy", methods=["POST"])
@login_required
def copy_navigation_links():
    """Copy navigation links from one location to another."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        data = request.get_json()
        if not data or 'from_location' not in data or 'to_location' not in data:
            return jsonify({"error": "Invalid data format"}), 400

        from_location = data['from_location']
        to_location = data['to_location']
        overwrite = data.get('overwrite', False)
        
        # Get source links
        source_links = NavigationLink.query.filter_by(location=from_location).order_by(NavigationLink.order).all()
        
        if not source_links:
            return jsonify({"error": f"No links found in {from_location}"}), 404
        
        # If not overwriting, check for existing links
        if not overwrite:
            existing_links = NavigationLink.query.filter_by(location=to_location).count()
            if existing_links > 0:
                return jsonify({"error": f"Destination {to_location} already has links. Enable overwrite to continue."}), 409
        
        copied_count = 0
        max_order = 0
        
        # Get max order in destination if not overwriting
        if not overwrite:
            max_order_result = db.session.query(db.func.max(NavigationLink.order)).filter_by(location=to_location).scalar()
            max_order = max_order_result or 0
        
        # Delete existing links if overwriting
        if overwrite:
            NavigationLink.query.filter_by(location=to_location).delete()
        
        # Copy links
        for link in source_links:
            new_link = NavigationLink(
                name=link.name,
                url=link.url,
                location=to_location,
                order=max_order + link.order + 1,
                is_active=link.is_active,
                is_external=link.is_external,
                user_id=current_user.id
            )
            db.session.add(new_link)
            copied_count += 1

        db.session.commit()
        
        # Invalidate navigation cache
        try:
            from optimizations import invalidate_cache_pattern
            invalidate_cache_pattern("navigation*")
        except ImportError:
            pass
        
        return jsonify({
            "message": f"Successfully copied {copied_count} links from {from_location} to {to_location}",
            "copied_count": copied_count,
            "from_location": from_location,
            "to_location": to_location
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error copying navigation links: {e}")
        return jsonify({"error": "Failed to copy navigation links"}), 500


# Album Public Routes
@main_blueprint.route("/albums")
@monitor_ssr_render("albums_list")
def albums_list():
    """Public albums listing page."""
    return render_template(
        'public/albums.html'
    )


@main_blueprint.route("/api/search/albums", methods=["GET"])
def search_albums():
    """API endpoint for server-side album search."""
    try:
        # Get search parameters
        query = request.args.get('q', '').strip()
        category_id = request.args.get('category', type=int)
        status = request.args.get('status', '')
        age = request.args.get('age', '').strip()
        rating = request.args.get('rating', type=float)  # Minimum rating filter
        sort = request.args.get('sort', 'newest')  # Default to newest
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # Base query for visible albums
        albums_query = (
            Album.query.filter_by(is_visible=True, is_archived=False)
            .join(Category, Album.category_id == Category.id)
            .join(User, Album.user_id == User.id)
        )
        
        # Apply search filters
        if query:
            # Use SQL LIKE for fuzzy search across multiple fields
            search_term = f"%{query}%"
            albums_query = albums_query.filter(
                db.or_(
                    Album.title.ilike(search_term),
                    Album.description.ilike(search_term),
                    Category.name.ilike(search_term),
                    User.username.ilike(search_term)
                )
            )
        
        # Apply category filter
        if category_id:
            albums_query = albums_query.filter(Album.category_id == category_id)
        
        # Apply status filter
        if status:
            if status == 'completed':
                albums_query = albums_query.filter(Album.is_completed == True)
            elif status == 'ongoing':
                albums_query = albums_query.filter(
                    Album.is_completed == False,
                    Album.is_hiatus == False
                )
            elif status == 'hiatus':
                albums_query = albums_query.filter(Album.is_hiatus == True)

        # Apply age filter
        if age:
            # Normalize values like R/13+ and D/17+ to 13+, 17+
            normalized = age.upper().replace(' ', '')
            if normalized in {'R/13+','R13+'}:
                normalized = '13+'
            if normalized in {'D/17+','D17+'}:
                normalized = '17+'
            albums_query = albums_query.filter(Album.age_rating == normalized)
        
        # Apply rating filter
        if rating:
            # Filter albums with average rating >= specified rating
            albums_query = albums_query.filter(
                db.session.query(db.func.avg(Rating.rating_value))
                .filter(Rating.content_type == 'album')
                .filter(Rating.content_id == Album.id)
                .scalar_subquery() >= rating
            )
        
        # Apply sorting with secondary sort by rating
        if sort == 'newest':
            # Order by creation date (newest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.created_at.desc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        elif sort == 'oldest':
            # Order by creation date (oldest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.created_at.asc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        elif sort == 'popular':
            # Order by read count (highest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.total_reads.desc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        elif sort == 'least-popular':
            # Order by read count (lowest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.total_reads.asc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        elif sort == 'highest-rated':
            # Order by average rating (highest first), then by read count (highest first)
            albums_query = albums_query.order_by(
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc(),
                Album.total_reads.desc()
            )
        elif sort == 'most-viewed':
            # Order by view count (highest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.total_views.desc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        elif sort == 'least-viewed':
            # Order by view count (lowest first), then by average rating (highest first)
            albums_query = albums_query.order_by(
                Album.total_views.asc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        else:
            # Default to newest if invalid sort
            albums_query = albums_query.order_by(
                Album.created_at.desc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        
        # Override sorting for search relevance if query exists
        if query:
            # Order by search relevance (exact matches first, then partial), then by rating
            albums_query = albums_query.order_by(
                db.case(
                    (Album.title.ilike(f"{query}%"), 0),  # Exact start match
                    (Album.title.ilike(f"%{query}%"), 1),  # Contains
                    (Category.name.ilike(f"%{query}%"), 2), # Category match
                    else_=3
                ),
                Album.created_at.desc(),
                db.func.coalesce(
                    db.session.query(db.func.avg(Rating.rating_value))
                    .filter(Rating.content_type == 'album')
                    .filter(Rating.content_id == Album.id)
                    .scalar_subquery(), 0
                ).desc()
            )
        
        # Paginate results
        pagination = albums_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Prepare response data
        albums_data = []
        for album in pagination.items:
            # Get rating information for this album
            avg_rating = Rating.get_average_rating('album', album.id)
            rating_count = Rating.get_rating_count('album', album.id)
            
            album_data = {
                'id': album.id,
                'title': album.title,
                'description': album.description or '',
                'category': {
                    'id': album.category.id,
                    'name': album.category.name
                } if album.category else None,
                'author': {
                    'id': album.author.id,
                    'username': album.author.username
                } if album.author else None,
                'status': 'completed' if album.is_completed else 'hiatus' if album.is_hiatus else 'ongoing',
                'is_premium': album.is_premium,
                'age_rating': album.age_rating,
                'total_chapters': album.total_chapters,
                'total_reads': album.total_reads,
                'total_views': album.total_views,
                'created_at': album.created_at.isoformat(),
                'rating': {
                    'average': avg_rating,
                    'count': rating_count,
                    'has_ratings': rating_count > 0
                },
                'cover_image': {
                    'url': url_for('static', filename=album.cover_image.filepath.split('static/')[-1])
                } if album.cover_image else None,
                'url': url_for('main.album_detail', 
                              album_id=album.id, 
                              album_title=album.title.replace(' ', '-').lower())
            }
            albums_data.append(album_data)
        
        return jsonify({
            'success': True,
            'albums': albums_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            },
            'search_info': {
                'query': query,
                'category_id': category_id,
                'status': status,
                'rating': rating,
                'sort': sort,
                'age': age,
                'results_count': len(albums_data),
                'total_count': pagination.total
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in album search: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An error occurred while searching albums',
            'message': str(e)
        }), 500


@main_blueprint.route("/album/<int:album_id>/<path:album_title>")
@monitor_ssr_render("album_detail")
def album_detail(album_id, album_title):
    """Album detail page showing album info and chapter list."""
    album = Album.query.get_or_404(album_id)
    
    # Check if album is visible
    if not album.is_visible or album.is_archived:
        abort(404)
    
    # Increment view count for this album
    try:
        album.increment_views()
    except Exception as e:
        current_app.logger.error(f"Failed to increment view count for album ID {album_id}: {e}")
    
    # Get chapters for this album
    chapters = (
        AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
        .order_by(AlbumChapter.chapter_number)
        .all()
    )
    
    # Get related albums using refined similarity algorithm
    related_albums = get_similar_albums(album, limit=4)
    
    # Get albums by the same author (excluding current)
    author_albums = (
        Album.query.filter_by(
            user_id=album.user_id,
            is_visible=True,
            is_archived=False
        )
        .filter(Album.id != album_id)
        .order_by(Album.created_at.desc())
        .limit(6)
        .all()
    )
    
    # Record reading history for logged-in users (album)
    try:
        if current_user.is_authenticated:
            from models import ReadingHistory
            history = ReadingHistory.query.filter_by(
                user_id=current_user.id, content_type='album', content_id=album_id
            ).first()
            if history:
                history.read_count = (history.read_count or 0) + 1
            else:
                db.session.add(ReadingHistory(
                    user_id=current_user.id,
                    content_type='album',
                    content_id=album_id,
                    read_count=1,
                ))
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record reading history for album ID {album_id}: {e}")

    return render_template(
        'public/album_detail.html',
        album=album,
        chapters=chapters,
        related_albums=related_albums,
        author_albums=author_albums
    )


@main_blueprint.route("/album/<int:album_id>/chapter/<int:chapter_id>/<path:chapter_title>")
@monitor_ssr_render("chapter_reader")
def chapter_reader(album_id, chapter_id, chapter_title):
    """Chapter reader page within an album."""
    from .utils.premium_content import process_premium_content, get_premium_content_stats
    
    album = Album.query.get_or_404(album_id)
    chapter = AlbumChapter.query.get_or_404(chapter_id)
    
    # Check if album and chapter are visible
    if not album.is_visible or album.is_archived:
        abort(404)
    if not chapter.is_visible or chapter.album_id != album_id:
        abort(404)
    
    # Get the news article for this chapter
    news = chapter.news
    
    # Get all chapters for navigation
    all_chapters = (
        AlbumChapter.query.filter_by(album_id=album_id, is_visible=True)
        .order_by(AlbumChapter.chapter_number)
        .all()
    )
    
    # Find current chapter index and get prev/next chapters
    current_index = None
    prev_chapter = None
    next_chapter = None
    
    for i, ch in enumerate(all_chapters):
        if ch.id == chapter_id:
            current_index = i
            if i > 0:
                prev_chapter = all_chapters[i - 1]
            if i < len(all_chapters) - 1:
                next_chapter = all_chapters[i + 1]
            break
    
    # --- Premium Content Processing ---
    # Check if content is premium (either news or album is premium)
    is_premium_content = news.is_premium or album.is_premium
    
    # Process content based on premium status
    processed_content, is_truncated, show_premium_notice = process_premium_content(
        news.content or "",
        is_premium_content,
        max_words=150  # Show first 150 words for non-premium users
    )
    
    # Get content statistics
    content_stats = get_premium_content_stats(news.content or "", is_premium_content)
    
    # --- Convert Markdown to HTML ---
    try:
        html_content = markdown.markdown(
            processed_content,  # Use processed content instead of original
            extensions=["fenced_code", "tables", "extra", "sane_lists"],
        )
    except Exception as e:
        current_app.logger.error(
            f"Markdown conversion failed for chapter ID {chapter_id}: {e}"
        )
        html_content = "<p><em>Error rendering content.</em></p>"
    
    # Increment read count
    news.increment_reads()
    album.total_reads += 1
    db.session.commit()
    
    return render_template(
        'public/chapter_reader.html',
        album=album,
        chapter=chapter,
        news=news,
        html_content=html_content,
        all_chapters=all_chapters,
        current_index=current_index,
        prev_chapter=prev_chapter,
        next_chapter=next_chapter,
        is_premium_content=is_premium_content,
        is_truncated=is_truncated,
        show_premium_notice=show_premium_notice,
        content_stats=content_stats
    )


@main_blueprint.route("/settings/albums")
@login_required
def albums_management():
    """Album management page."""
    if not current_user.verified:
        return redirect(url_for('main.login'))
    
    return render_template('admin/settings/albums_management.html')


# REMOVED: albums_seo_management route - functionality moved to seo_management
# @main_blueprint.route("/settings/albums-seo")
# @login_required
# def albums_seo_management():
#     """Album SEO management page."""
#     if not current_user.verified:
#         return redirect(url_for('main.login'))
#     
#     return render_template('admin/seo/albums_seo_management.html')


@main_blueprint.route("/api/search/news", methods=["GET"])
def search_news_api():
    """Unified API endpoint for news search with content type filtering."""
    query = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()
    category_name = request.args.get("category_name", "").strip()
    tag = request.args.get("tag", "").strip()
    age = request.args.get("age", "").strip()
    sort = request.args.get("sort", "newest")
    content_type = request.args.get("type", "general")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 12, type=int)

    # Base query
    news_query = News.query.filter_by(is_visible=True, is_archived=False)

    # Apply content type filters
    if content_type == "news":
        # Only news (is_news=True)
        news_query = news_query.filter(News.is_news == True)
    elif content_type == "hypes":
        # Popular content based on shares and reads
        news_query = (
            db.session.query(
                News,
                (
                    func.coalesce(ShareLog.whatsapp_count, 0)
                    + func.coalesce(ShareLog.facebook_count, 0)
                    + func.coalesce(ShareLog.twitter_count, 0)
                    + func.coalesce(ShareLog.instagram_count, 0)
                    + func.coalesce(ShareLog.bluesky_count, 0)
                    + func.coalesce(ShareLog.clipboard_count, 0)
                ).label("total_share"),
            )
            .outerjoin(ShareLog, News.id == ShareLog.news_id)
            .filter(News.is_visible == True, News.read_count > 0)
        )
    elif content_type == "articles":
        # Only articles (is_news=False)
        news_query = news_query.filter(News.is_news == False)
    elif content_type == "utama":
        # Main/featured news
        news_query = news_query.filter(News.is_main_news == True)
    # For "general", no additional filter needed

    # Apply search query
    if query:
        news_query = news_query.filter(
            News.title.ilike(f"%{query}%") | News.content.ilike(f"%{query}%")
        )

    # Apply category filter (by ID or name)
    if category_id:
        try:
            category_id_int = int(category_id)
            news_query = news_query.filter(News.category_id == category_id_int)
        except ValueError:
            return jsonify({"error": "Invalid category ID"}), 400
    elif category_name:
        news_query = news_query.filter(News.category.has(name=category_name))

    # Apply tag filter
    if tag:
        news_query = news_query.filter(News.tagar.ilike(f"%{tag}%"))
    
    # Apply age filter
    if age:
        normalized = age.upper().replace(' ', '')
        if normalized in {'R/13+','R13+'}: normalized = '13+'
        if normalized in {'D/17+','D17+'}: normalized = '17+'
        news_query = news_query.filter(News.age_rating == normalized)

    # Apply sorting
    if content_type == "hypes":
        # For hypes, sort by total shares and reads
        if sort == "popular":
            news_query = news_query.order_by(db.desc("total_share"), db.desc(News.read_count))
        elif sort == "least-popular":
            news_query = news_query.order_by(db.asc("total_share"), db.asc(News.read_count))
        elif sort == "oldest":
            news_query = news_query.order_by(News.created_at.asc())
        else:  # newest
            news_query = news_query.order_by(News.created_at.desc())
    else:
        # For other content types (news, articles, utama, general), use standard sorting
        if sort == "popular":
            news_query = news_query.order_by(News.read_count.desc(), News.created_at.desc())
        elif sort == "least-popular":
            news_query = news_query.order_by(News.read_count.asc(), News.created_at.desc())
        elif sort == "oldest":
            news_query = news_query.order_by(News.created_at.asc())
        else:  # newest
            news_query = news_query.order_by(News.created_at.desc())

    # Paginate results
    try:
        if content_type == "hypes":
            # Handle hypes pagination with total_share
            pagination = news_query.paginate(page=page, per_page=per_page, error_out=False)
            news_list = []
            for news, total_share in pagination.items:
                news.total_share = total_share if total_share is not None else 0
                news_list.append(news)
            pagination.items = news_list
        else:
            # Standard pagination for other content types (news, articles, utama, general)
            pagination = news_query.paginate(page=page, per_page=per_page, error_out=False)
            news_list = pagination.items
    except Exception as e:
        current_app.logger.error(f"Database error in search_news_api: {e}")
        return jsonify({"error": "Database error"}), 500

    # Serialize results
    response_data = []
    for news_item in news_list:
        news_dict = news_item.to_dict()
        news_dict["category"] = news_item.category.name if news_item.category else None
        news_dict["url"] = url_for('main.news_detail', news_id=news_item.id, news_title=safe_title(news_item.title))
        
        # Add excerpt (first 150 characters of content)
        if news_item.content:
            excerpt = news_item.content.replace('\n', ' ').strip()
            if len(excerpt) > 150:
                excerpt = excerpt[:150] + "..."
            news_dict["excerpt"] = excerpt
        
        # Add rating information
        avg_rating = Rating.get_average_rating('news', news_item.id)
        rating_count = Rating.get_rating_count('news', news_item.id)
        news_dict["rating"] = {
            "average": avg_rating,
            "count": rating_count,
            "has_ratings": rating_count > 0
        }
        
        # Add total shares for hypes
        if content_type == "hypes":
            news_dict["total_share"] = getattr(news_item, 'total_share', 0)
        
        # Add tags information
        if news_item.tagar:
            tags_list = [tag.strip() for tag in news_item.tagar.split(',') if tag.strip()]
            news_dict["tags"] = tags_list[:3]  # Limit to 3 tags
        else:
            news_dict["tags"] = []
        
        response_data.append(news_dict)

    # Format pagination info
    pagination_info = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
        "total": pagination.total,
        "has_prev": pagination.has_prev,
        "has_next": pagination.has_next,
        "prev_num": pagination.prev_num,
        "next_num": pagination.next_num
    }

    return jsonify({
        "success": True,
        "news": response_data,
        "pagination": pagination_info,
        "search_info": {
            "total_count": pagination.total,
            "query": query,
            "category": category_id or category_name,
            "tag": tag,
            "sort": sort,
            "type": content_type,
            "age": age
        }
    })


@main_blueprint.route("/api/settings/ads-injection", methods=["POST"])
def update_ads_preferences():
    """API endpoint for updating user's ad preferences."""
    try:
        data = request.get_json()
        show_ads = data.get('show_ads', True)
        
        if current_user.is_authenticated:
            # Update user's ad preferences
            current_user.ad_preferences = {
                'show_ads': show_ads,
                'ad_frequency': data.get('ad_frequency', 'normal')
            }
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ad preferences updated successfully',
                'show_ads': show_ads
            })
        else:
            # For anonymous users, return success but don't store preferences
            return jsonify({
                'success': True,
                'message': 'Ad preferences updated for this session',
                'show_ads': show_ads
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

