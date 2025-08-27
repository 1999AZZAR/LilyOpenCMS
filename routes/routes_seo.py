from routes import main_blueprint
from .common_imports import *
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime, timezone

# SEO Management Routes for Comprehensive SEO Management

@main_blueprint.route("/api/seo/articles", methods=["GET"])
@login_required
def get_articles_seo():
    """
    GET: Fetch articles with SEO data for comprehensive SEO management.
    Supports filtering by search, status, SEO status, and category.
    """
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    seo_status = request.args.get("seo_status", "")
    category = request.args.get("category", "")

    # Build base query
    query = db.session.query(
        News.id,
        News.title,
        News.writer,
        News.meta_description,
        News.meta_keywords,
        News.og_title,
        News.og_description,
        News.seo_score,
        News.is_visible,
        News.is_archived,
        News.created_at,
        Category.name.label('category_name')
    ).join(Category, News.category_id == Category.id)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                News.title.ilike(f"%{search}%"),
                News.content.ilike(f"%{search}%"),
                News.writer.ilike(f"%{search}%")
            )
        )

    if status:
        if status == "published":
            query = query.filter(News.is_visible == True, News.is_archived == False)
        elif status == "draft":
            query = query.filter(News.is_visible == False, News.is_archived == False)
        elif status == "archived":
            query = query.filter(News.is_archived == True)

    if category:
        query = query.filter(Category.id == category)

    # Apply SEO status filter
    if seo_status:
        if seo_status == "complete":
            query = query.filter(
                and_(
                    News.meta_description.isnot(None),
                    News.meta_description != "",
                    News.meta_keywords.isnot(None),
                    News.meta_keywords != "",
                    News.og_title.isnot(None),
                    News.og_title != ""
                )
            )
        elif seo_status == "incomplete":
            query = query.filter(
                or_(
                    News.meta_description.is_(None),
                    News.meta_description == "",
                    News.meta_keywords.is_(None),
                    News.meta_keywords == "",
                    News.og_title.is_(None),
                    News.og_title == ""
                )
            )
        elif seo_status == "missing":
            query = query.filter(
                and_(
                    News.meta_description.is_(None),
                    News.meta_keywords.is_(None),
                    News.og_title.is_(None)
                )
            )

    # Get total count for pagination
    total_count = query.count()

    # Apply pagination
    query = query.order_by(desc(News.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    results = query.all()

    # Process results
    articles = []
    for result in results:
        # Calculate SEO status
        seo_fields = [
            result.meta_description,
            result.meta_keywords,
            result.og_title,
            result.og_description
        ]
        
        filled_fields = sum(1 for field in seo_fields if field and field.strip())
        if filled_fields == len(seo_fields):
            seo_status = "complete"
        elif filled_fields == 0:
            seo_status = "missing"
        else:
            seo_status = "incomplete"

        articles.append({
            "id": result.id,
            "title": result.title,
            "writer": result.writer,
            "category_name": result.category_name,
            "meta_description": result.meta_description,
            "meta_keywords": result.meta_keywords,
            "og_title": result.og_title,
            "og_description": result.og_description,
            "seo_status": seo_status,
            "seo_score": result.seo_score or 0,
            "is_visible": result.is_visible,
            "is_archived": result.is_archived,
            "created_at": result.created_at.isoformat() if result.created_at else None
        })

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    pagination = {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next
    }

    return jsonify({
        "articles": articles,
        "pagination": pagination
    })

@main_blueprint.route("/api/seo/articles/<int:article_id>", methods=["GET"])
@login_required
def get_article_seo_detail(article_id):
    """GET: Fetch detailed SEO data for a specific article."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    article = News.query.get_or_404(article_id)
    
    return jsonify({
        "id": article.id,
        "title": article.title,
        "category": article.category.name if article.category else "N/A",
        "meta_description": article.meta_description,
        "meta_keywords": article.meta_keywords,
        "og_title": article.og_title,
        "og_description": article.og_description,
        "og_image": article.og_image,
        "canonical_url": article.canonical_url,
        "seo_slug": article.seo_slug,
        "twitter_card": article.twitter_card,
        "twitter_title": article.twitter_title,
        "twitter_description": article.twitter_description,
        "twitter_image": article.twitter_image,
        "meta_author": article.meta_author,
        "meta_language": article.meta_language or "id",
        "meta_robots": article.meta_robots or "index, follow",
        "structured_data_type": article.structured_data_type or "Article",
        "seo_score": article.seo_score or 0
    })

@main_blueprint.route("/api/seo/articles/<int:article_id>", methods=["PUT"])
@login_required
def update_article_seo(article_id):
    """PUT: Update SEO data for a specific article."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    article = News.query.get_or_404(article_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update SEO fields
    seo_fields = [
        'meta_description', 'meta_keywords', 'og_title', 'og_description',
        'og_image', 'canonical_url', 'seo_slug', 'twitter_card',
        'twitter_title', 'twitter_description', 'twitter_image',
        'meta_author', 'meta_language', 'meta_robots', 'structured_data_type'
    ]

    for field in seo_fields:
        if field in data:
            setattr(article, field, data[field])

    # Recalculate SEO score
    article.seo_score = article.calculate_seo_score()
    article.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return jsonify({"message": "SEO data updated successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating article SEO: {e}")
        return jsonify({"error": "Failed to update SEO data"}), 500

@main_blueprint.route("/api/seo/albums", methods=["GET"])
@login_required
def get_albums_seo():
    """
    GET: Fetch albums with SEO data for comprehensive SEO management.
    Supports filtering by search, status, SEO status, and category.
    """
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    seo_status = request.args.get("seo_status", "")
    category = request.args.get("category", "")

    # Build base query
    query = db.session.query(
        Album.id,
        Album.title,
        Album.description,
        Album.meta_description,
        Album.meta_keywords,
        Album.og_title,
        Album.og_description,
        Album.seo_score,
        Album.is_visible,
        Album.is_archived,
        Album.created_at,
        Category.name.label('category_name')
    ).join(Category, Album.category_id == Category.id)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                Album.title.ilike(f"%{search}%"),
                Album.description.ilike(f"%{search}%")
            )
        )

    if status:
        if status == "published":
            query = query.filter(Album.is_visible == True, Album.is_archived == False)
        elif status == "draft":
            query = query.filter(Album.is_visible == False, Album.is_archived == False)
        elif status == "archived":
            query = query.filter(Album.is_archived == True)

    if category:
        query = query.filter(Category.id == category)

    # Apply SEO status filter
    if seo_status:
        if seo_status == "complete":
            query = query.filter(
                and_(
                    Album.meta_description.isnot(None),
                    Album.meta_description != "",
                    Album.meta_keywords.isnot(None),
                    Album.meta_keywords != "",
                    Album.og_title.isnot(None),
                    Album.og_title != ""
                )
            )
        elif seo_status == "incomplete":
            query = query.filter(
                or_(
                    Album.meta_description.is_(None),
                    Album.meta_description == "",
                    Album.meta_keywords.is_(None),
                    Album.meta_keywords == "",
                    Album.og_title.is_(None),
                    Album.og_title == ""
                )
            )
        elif seo_status == "missing":
            query = query.filter(
                and_(
                    Album.meta_description.is_(None),
                    Album.meta_keywords.is_(None),
                    Album.og_title.is_(None)
                )
            )

    # Get total count for pagination
    total_count = query.count()

    # Apply pagination
    query = query.order_by(desc(Album.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    results = query.all()

    # Process results
    albums = []
    for result in results:
        # Calculate SEO status
        seo_fields = [
            result.meta_description,
            result.meta_keywords,
            result.og_title,
            result.og_description
        ]
        
        filled_fields = sum(1 for field in seo_fields if field and field.strip())
        if filled_fields == len(seo_fields):
            seo_status = "complete"
        elif filled_fields == 0:
            seo_status = "missing"
        else:
            seo_status = "incomplete"

        albums.append({
            "id": result.id,
            "title": result.title,
            "category_name": result.category_name,
            "meta_description": result.meta_description,
            "meta_keywords": result.meta_keywords,
            "og_title": result.og_title,
            "og_description": result.og_description,
            "seo_status": seo_status,
            "seo_score": result.seo_score or 0,
            "is_visible": result.is_visible,
            "is_archived": result.is_archived,
            "created_at": result.created_at.isoformat() if result.created_at else None
        })

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    pagination = {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next
    }

    return jsonify({
        "albums": albums,
        "pagination": pagination
    })

@main_blueprint.route("/api/seo/albums/<int:album_id>", methods=["GET"])
@login_required
def get_album_seo_detail(album_id):
    """GET: Fetch detailed SEO data for a specific album."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    album = Album.query.get_or_404(album_id)
    
    return jsonify({
        "id": album.id,
        "title": album.title,
        "category": album.category.name if album.category else "N/A",
        "meta_description": album.meta_description,
        "meta_keywords": album.meta_keywords,
        "og_title": album.og_title,
        "og_description": album.og_description,
        "og_image": album.og_image,
        "canonical_url": album.canonical_url,
        "seo_slug": album.seo_slug,
        "twitter_card": album.twitter_card,
        "twitter_title": album.twitter_title,
        "twitter_description": album.twitter_description,
        "twitter_image": album.twitter_image,
        "meta_author": album.meta_author,
        "meta_language": album.meta_language or "id",
        "meta_robots": album.meta_robots or "index, follow",
        "structured_data_type": album.structured_data_type or "Book",
        "seo_score": album.seo_score or 0
    })

@main_blueprint.route("/api/seo/albums/<int:album_id>", methods=["PUT"])
@login_required
def update_album_seo(album_id):
    """PUT: Update SEO data for a specific album."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    album = Album.query.get_or_404(album_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update SEO fields
    seo_fields = [
        'meta_description', 'meta_keywords', 'og_title', 'og_description',
        'og_image', 'canonical_url', 'seo_slug', 'twitter_card',
        'twitter_title', 'twitter_description', 'twitter_image',
        'meta_author', 'meta_language', 'meta_robots', 'structured_data_type'
    ]

    for field in seo_fields:
        if field in data:
            setattr(album, field, data[field])

    # Recalculate SEO score
    album.seo_score = album.calculate_seo_score()
    album.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return jsonify({"message": "SEO data updated successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating album SEO: {e}")
        return jsonify({"error": "Failed to update SEO data"}), 500

# Additional API endpoints for albums management SEO tab
@main_blueprint.route("/api/seo/albums-management", methods=["GET"])
@login_required
def get_albums_seo_management():
    """
    GET: Fetch albums with SEO data specifically for albums management page.
    This endpoint is used by the albums management SEO tab.
    """
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    seo_status = request.args.get("seo_status", "")
    category = request.args.get("category", "")

    # Build base query
    query = db.session.query(
        Album.id,
        Album.title,
        Album.description,
        Album.meta_description,
        Album.meta_keywords,
        Album.og_title,
        Album.og_description,
        Album.seo_score,
        Album.is_visible,
        Album.is_archived,
        Album.created_at,
        Category.name.label('category_name')
    ).join(Category, Album.category_id == Category.id)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                Album.title.ilike(f"%{search}%"),
                Album.description.ilike(f"%{search}%")
            )
        )

    if status:
        if status == "visible":
            query = query.filter(Album.is_visible == True, Album.is_archived == False)
        elif status == "hidden":
            query = query.filter(Album.is_visible == False, Album.is_archived == False)
        elif status == "archived":
            query = query.filter(Album.is_archived == True)

    if category:
        query = query.filter(Category.id == category)

    # Apply SEO status filter
    if seo_status:
        if seo_status == "complete":
            query = query.filter(
                and_(
                    Album.meta_description.isnot(None),
                    Album.meta_description != "",
                    Album.meta_keywords.isnot(None),
                    Album.meta_keywords != "",
                    Album.og_title.isnot(None),
                    Album.og_title != ""
                )
            )
        elif seo_status == "incomplete":
            query = query.filter(
                or_(
                    Album.meta_description.is_(None),
                    Album.meta_description == "",
                    Album.meta_keywords.is_(None),
                    Album.meta_keywords == "",
                    Album.og_title.is_(None),
                    Album.og_title == ""
                )
            )
        elif seo_status == "missing":
            query = query.filter(
                and_(
                    Album.meta_description.is_(None),
                    Album.meta_keywords.is_(None),
                    Album.og_title.is_(None)
                )
            )

    # Get total count for pagination
    total_count = query.count()

    # Apply pagination
    query = query.order_by(desc(Album.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    results = query.all()

    # Process results
    albums = []
    for result in results:
        # Calculate SEO status
        seo_fields = [
            result.meta_description,
            result.meta_keywords,
            result.og_title,
            result.og_description
        ]
        
        filled_fields = sum(1 for field in seo_fields if field and field.strip())
        if filled_fields == len(seo_fields):
            seo_status = "complete"
        elif filled_fields == 0:
            seo_status = "missing"
        else:
            seo_status = "incomplete"

        albums.append({
            "id": result.id,
            "title": result.title,
            "category_name": result.category_name,
            "meta_description": result.meta_description,
            "meta_keywords": result.meta_keywords,
            "og_title": result.og_title,
            "og_description": result.og_description,
            "seo_status": seo_status,
            "seo_score": result.seo_score or 0,
            "is_visible": result.is_visible,
            "is_archived": result.is_archived,
            "created_at": result.created_at.isoformat() if result.created_at else None
        })

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    pagination = {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next
    }

    return jsonify({
        "albums": albums,
        "pagination": pagination
    })

@main_blueprint.route("/api/seo/root", methods=["GET"])
@login_required
def get_root_seo():
    """
    GET: Fetch root pages with SEO data for comprehensive SEO management.
    Supports filtering by search, status, and SEO status.
    """
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    # Get query parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "")
    seo_status = request.args.get("seo_status", "")

    # Build base query
    query = RootSEO.query

    # Apply filters
    if search:
        query = query.filter(
            or_(
                RootSEO.page_name.ilike(f"%{search}%"),
                RootSEO.page_identifier.ilike(f"%{search}%")
            )
        )

    if status:
        if status == "active":
            query = query.filter(RootSEO.is_active == True)
        elif status == "inactive":
            query = query.filter(RootSEO.is_active == False)

    # Apply SEO status filter
    if seo_status:
        if seo_status == "complete":
            query = query.filter(
                and_(
                    RootSEO.meta_title.isnot(None),
                    RootSEO.meta_title != "",
                    RootSEO.meta_description.isnot(None),
                    RootSEO.meta_description != "",
                    RootSEO.og_title.isnot(None),
                    RootSEO.og_title != ""
                )
            )
        elif seo_status == "incomplete":
            query = query.filter(
                or_(
                    RootSEO.meta_title.is_(None),
                    RootSEO.meta_title == "",
                    RootSEO.meta_description.is_(None),
                    RootSEO.meta_description == "",
                    RootSEO.og_title.is_(None),
                    RootSEO.og_title == ""
                )
            )
        elif seo_status == "missing":
            query = query.filter(
                and_(
                    RootSEO.meta_title.is_(None),
                    RootSEO.meta_description.is_(None),
                    RootSEO.og_title.is_(None)
                )
            )

    # Get total count for pagination
    total_count = query.count()

    # Apply pagination
    query = query.order_by(asc(RootSEO.page_identifier))
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    results = query.all()

    # Process results
    root_entries = []
    for result in results:
        # Calculate SEO score
        seo_score = result.calculate_seo_score()

        root_entries.append({
            "id": result.id,
            "page_identifier": result.page_identifier,
            "page_name": result.page_name,
            "is_active": result.is_active,
            "meta_title": result.meta_title,
            "meta_description": result.meta_description,
            "meta_keywords": result.meta_keywords,
            "og_title": result.og_title,
            "og_description": result.og_description,
            "og_image": result.og_image,
            "canonical_url": result.canonical_url,
            "seo_score": seo_score,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None
        })

    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages

    pagination = {
        "current_page": page,
        "per_page": per_page,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next
    }

    return jsonify({
        "root_entries": root_entries,
        "pagination": pagination
    })

@main_blueprint.route("/api/seo/root/<int:root_id>", methods=["GET"])
@login_required
def get_root_seo_detail(root_id):
    """GET: Fetch detailed SEO data for a specific root page."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    root_seo = RootSEO.query.get_or_404(root_id)
    
    return jsonify({
        "id": root_seo.id,
        "title": root_seo.page_name,
        "category": "Root Page",
        "page_identifier": root_seo.page_identifier,
        "meta_title": root_seo.meta_title,
        "meta_description": root_seo.meta_description,
        "meta_keywords": root_seo.meta_keywords,
        "og_title": root_seo.og_title,
        "og_description": root_seo.og_description,
        "og_image": root_seo.og_image,
        "og_type": root_seo.og_type,
        "canonical_url": root_seo.canonical_url,
        "twitter_card": root_seo.twitter_card,
        "twitter_title": root_seo.twitter_title,
        "twitter_description": root_seo.twitter_description,
        "twitter_image": root_seo.twitter_image,
        "meta_author": root_seo.meta_author,
        "meta_language": root_seo.meta_language or "id",
        "meta_robots": root_seo.meta_robots or "index, follow",
        "structured_data_type": root_seo.structured_data_type or "WebPage",
        "seo_score": root_seo.calculate_seo_score()
    })

@main_blueprint.route("/api/seo/root/<int:root_id>", methods=["PUT"])
@login_required
def update_root_seo(root_id):
    """PUT: Update SEO data for a specific root page."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    root_seo = RootSEO.query.get_or_404(root_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Update SEO fields
    seo_fields = [
        'meta_title', 'meta_description', 'meta_keywords', 'og_title', 
        'og_description', 'og_image', 'og_type', 'canonical_url',
        'twitter_card', 'twitter_title', 'twitter_description', 'twitter_image',
        'meta_author', 'meta_language', 'meta_robots', 'structured_data_type'
    ]

    for field in seo_fields:
        if field in data:
            setattr(root_seo, field, data[field])

    root_seo.updated_at = datetime.now(timezone.utc)
    root_seo.updated_by = current_user.id

    try:
        db.session.commit()
        return jsonify({"message": "SEO data updated successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating root SEO: {e}")
        return jsonify({"error": "Failed to update SEO data"}), 500

@main_blueprint.route("/api/seo/root", methods=["POST"])
@login_required
def create_root_seo():
    """POST: Create a new root page SEO entry."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    if not data.get('page_identifier'):
        return jsonify({"error": "Page identifier is required"}), 400
    if not data.get('page_name'):
        return jsonify({"error": "Page name is required"}), 400

    # Check if page identifier already exists
    existing = RootSEO.query.filter_by(page_identifier=data['page_identifier']).first()
    if existing:
        return jsonify({"error": "Page identifier already exists"}), 400

    # Create new root SEO entry
    root_seo = RootSEO(
        page_identifier=data['page_identifier'],
        page_name=data['page_name'],
        is_active=data.get('is_active', True),
        meta_title=data.get('meta_title'),
        meta_description=data.get('meta_description'),
        meta_keywords=data.get('meta_keywords'),
        og_title=data.get('og_title'),
        og_description=data.get('og_description'),
        og_image=data.get('og_image'),
        og_type=data.get('og_type', 'website'),
        canonical_url=data.get('canonical_url'),
        twitter_card=data.get('twitter_card', 'summary_large_image'),
        twitter_title=data.get('twitter_title'),
        twitter_description=data.get('twitter_description'),
        twitter_image=data.get('twitter_image'),
        meta_author=data.get('meta_author'),
        meta_language=data.get('meta_language', 'id'),
        meta_robots=data.get('meta_robots', 'index, follow'),
        structured_data_type=data.get('structured_data_type', 'WebPage'),
        created_by=current_user.id,
        updated_by=current_user.id
    )

    try:
        db.session.add(root_seo)
        db.session.commit()
        return jsonify({
            "message": "Root SEO entry created successfully",
            "id": root_seo.id
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating root SEO: {e}")
        return jsonify({"error": "Failed to create SEO entry"}), 500

# SEO Injector Routes
@main_blueprint.route("/api/seo/inject", methods=["POST"])
@login_required
def run_seo_injection():
    """POST: Run SEO injection for specified content type."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    data = request.get_json() or {}
    injection_type = data.get('type', 'all')
    
    # Validate injection type
    valid_types = ['news', 'albums', 'chapters', 'root', 'all']
    if injection_type not in valid_types:
        return jsonify({"error": f"Invalid injection type. Must be one of: {valid_types}"}), 400

    try:
        # Import the SEO injector
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'seo_injector'))
        
        from seo_injector import run_seo_injection as run_injection
        
        # Run the injection
        result = run_injection(injection_type)
        
        return jsonify({
            "message": "SEO injection completed",
            "type": injection_type,
            "result": result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error running SEO injection: {e}")
        return jsonify({
            "error": "Failed to run SEO injection",
            "details": str(e)
        }), 500

@main_blueprint.route("/api/seo/stats", methods=["GET"])
@login_required
def get_seo_statistics():
    """GET: Get SEO statistics for all content types."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        # Import the SEO injector
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'seo_injector'))
        
        from seo_injector import get_seo_statistics as get_stats
        
        # Get the statistics
        result = get_stats()
        
        return jsonify({
            "message": "SEO statistics retrieved",
            "result": result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting SEO statistics: {e}")
        return jsonify({
            "error": "Failed to get SEO statistics",
            "details": str(e)
        }), 500

@main_blueprint.route("/api/seo/inject/status", methods=["GET"])
@login_required
def get_seo_injection_status():
    """GET: Get the status of SEO injection operations."""
    if not current_user.verified:
        return jsonify({"error": "Account not verified"}), 403

    try:
        # Import the SEO injector
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'seo_injector'))
        
        from seo_injector import get_seo_statistics as get_stats
        
        # Get current statistics
        stats_result = get_stats()
        
        # Calculate overall SEO health
        total_items = 0
        items_with_seo = 0
        
        if stats_result['status'] == 'success':
            stats_text = stats_result['stats']
            
            # Parse the stats text to get counts
            for content_type, stats in stats_text.items():
                lines = stats.split('\n')
                for line in lines:
                    if 'Total' in line and ':' in line:
                        try:
                            count = int(line.split(':')[1].strip().split()[0])
                            total_items += count
                        except:
                            pass
                    elif 'With meta description:' in line:
                        try:
                            count = int(line.split(':')[1].strip().split()[0])
                            items_with_seo += count
                        except:
                            pass
        
        seo_health_percentage = (items_with_seo / total_items * 100) if total_items > 0 else 0
        
        return jsonify({
            "message": "SEO status retrieved",
            "total_items": total_items,
            "items_with_seo": items_with_seo,
            "seo_health_percentage": round(seo_health_percentage, 1),
            "stats": stats_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting SEO status: {e}")
        return jsonify({
            "error": "Failed to get SEO status",
            "details": str(e)
        }), 500 