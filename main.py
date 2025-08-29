from flask import (
    Flask,
    jsonify,
    request,
    render_template,
    current_app,
)
import time
from flask_login import LoginManager
from flask_migrate import Migrate
import sys
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from dotenv import load_dotenv
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo

JAKARTA = ZoneInfo("Asia/Jakarta")

from sqlalchemy import func, and_, text
from sqlalchemy.exc import OperationalError

from models import db, User, Category, News, UserRole, default_utcnow

# Import performance optimization modules
from optimizations import (
    init_cache, 
    cache, 
    cache_with_args, 
    cache_query_result,
    create_database_optimizer,
    create_frontend_optimizer,
    create_performance_monitor,
    get_asset_optimizer,
    get_ssr_optimizer,
    monitor_ssr_render
)

load_dotenv()

# ----------------------
# 🔧 Initialize Flask app
# ----------------------
app = Flask(__name__)

# ✅ Apply CORS ONLY for /api/* routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ----------------------
# 🔧 Configuration
# ----------------------
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URI", f"sqlite:///{os.path.join(os.path.dirname(__file__), 'instance', 'LilyOpenCms.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = os.getenv("FLASK_ENV") != "production"

# Performance optimization configuration
app.config["COMPRESS_MIMETYPES"] = [
    'text/html', 'text/css', 'text/xml', 'application/json', 'application/javascript'
]
app.config["COMPRESS_LEVEL"] = 6
app.config["COMPRESS_MIN_SIZE"] = 500

# ----------------------
# 🔗 Initialize Extensions
# ----------------------
db.init_app(app)
migrate = Migrate(app, db)

# Initialize performance optimizations
init_cache(app)
db_optimizer = create_database_optimizer(app)
frontend_optimizer = create_frontend_optimizer(app)
performance_monitor = create_performance_monitor(app)
asset_optimizer = get_asset_optimizer()
ssr_optimizer = get_ssr_optimizer()

# ----------------------
# 🔍 Database Health Check
# ----------------------
def run_database_health_check():
    """Run database health checks on startup."""
    try:
        from config.database_health_checker import DatabaseHealthChecker
        
        # Only run health checks in development or when explicitly enabled
        if app.config.get("DEBUG", False) or os.getenv("RUN_DB_HEALTH_CHECK", "false").lower() == "true":
            app.logger.info("🔍 Running database health checks...")
            
            checker = DatabaseHealthChecker(app.config["SQLALCHEMY_DATABASE_URI"])
            results = checker.run_all_checks()
            
            # Log results
            summary = checker.get_summary()
            app.logger.info(f"📊 Database Health Summary: {summary['passed_checks']}/{summary['total_checks']} checks passed")
            
            # Log critical issues
            critical_issues = [r for r in results if r.severity.value == "critical" and not r.status]
            if critical_issues:
                app.logger.error(f"❌ Critical database issues found: {len(critical_issues)}")
                for issue in critical_issues:
                    app.logger.error(f"  - {issue.name}: {issue.message}")
                    if issue.recommendations:
                        for rec in issue.recommendations:
                            app.logger.error(f"    → {rec}")
            else:
                app.logger.info("✅ Database health checks passed")
                
    except Exception as e:
        app.logger.warning(f"⚠️ Database health check failed: {e}")
        # Don't fail startup for health check errors

# Run health check after app context is available
with app.app_context():
    def _is_migration_cli():
        try:
            argv = " ".join(sys.argv).lower()
            return ("flask" in argv) and any(x in argv for x in ["db", "migrate", "upgrade", "downgrade", "stamp", "revision"])
        except Exception:
            return False
    run_database_health_check()

# Add SSR monitoring to app context
@app.before_request
def start_ssr_monitoring():
    from flask import g
    g.ssr_start_time = time.time()

@app.after_request
def end_ssr_monitoring(response):
    from flask import g
    if hasattr(g, 'ssr_start_time'):
        render_time = time.time() - g.ssr_start_time
        # Record SSR render for the current route
        route_name = request.endpoint or 'unknown'
        try:
            optimizer = get_ssr_optimizer()
            optimizer.record_render(route_name, render_time, cached=False)
        except Exception:
            pass
    return response

# Disable CSRF protection for this application since we use proper authentication
# csrf = CSRFProtect(app)

# ----------------------
# 🔑 Login Management
# ----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "main.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        app.logger.warning(f"Invalid user_id format received: {user_id}")
        return None

# ----------------------
# 🌐 Context Processors with Caching
# ----------------------
@app.context_processor
def inject_permission_functions():
    """Inject permission checking functions into templates."""
    from routes.utils.permission_manager import (
        can_access_admin,
        can_manage_users,
        can_manage_content,
        can_manage_categories,
        can_manage_settings,
        can_manage_roles,
        can_manage_ads,
        can_moderate_comments,
        can_manage_ratings,
        can_access_analytics,
        can_manage_legal,
        can_manage_brand,
        can_manage_seo,
        has_permission,
        has_any_permission,
        has_all_permissions,
        get_user_role_display,
        get_user_permissions_summary,
        is_superuser,
        is_admin,
        is_admin_tier,
        has_custom_role
    )
    
    def get_user_dashboard_url(user):
        """Get the appropriate dashboard URL based on user role."""
        from flask import url_for
        from models import UserRole
        if user.role in [UserRole.ADMIN, UserRole.SUPERUSER] or user.is_owner():
            return url_for("main.settings_dashboard")
        return "/dashboard"
    
    return {
        'can_access_admin': can_access_admin,
        'can_manage_users': can_manage_users,
        'can_manage_content': can_manage_content,
        'can_manage_categories': can_manage_categories,
        'can_manage_settings': can_manage_settings,
        'can_manage_roles': can_manage_roles,
        'can_manage_ads': can_manage_ads,
        'can_moderate_comments': can_moderate_comments,
        'can_manage_ratings': can_manage_ratings,
        'can_access_analytics': can_access_analytics,
        'can_manage_legal': can_manage_legal,
        'can_manage_brand': can_manage_brand,
        'can_manage_seo': can_manage_seo,
        'has_permission': has_permission,
        'has_any_permission': has_any_permission,
        'has_all_permissions': has_all_permissions,
        'get_user_role_display': get_user_role_display,
        'get_user_permissions_summary': get_user_permissions_summary,
        'is_superuser': is_superuser,
        'is_admin': is_admin,
        'is_admin_tier': is_admin_tier,
        'has_custom_role': has_custom_role,
        'get_user_dashboard_url': get_user_dashboard_url
    }

@app.context_processor
def inject_global_search_filters():
    all_categories = []
    unique_sorted_tags = []
    logger = logging.getLogger(__name__)

    try:
        # Use optimized query with caching
        all_categories = Category.query.order_by(Category.name).all()
        tag_strings_tuples = (
            db.session.query(News.tagar)
            .filter(and_(News.tagar.isnot(None), News.tagar != ""))
            .distinct()
            .order_by(News.tagar)
            .all()
        )

        all_tags_list = []
        for tag_string_tuple in tag_strings_tuples:
            tag_string = tag_string_tuple[0]
            tags_in_string = [
                tag.strip().lower() for tag in tag_string.split(",") if tag.strip()
            ]
            all_tags_list.extend(tags_in_string)

        unique_sorted_tags = sorted(list(set(all_tags_list)), key=str.lower)

    except Exception as e:
        logger.error(
            f"❌ Error fetching global filters (categories/tags): {e}", exc_info=True
        )
        all_categories = []
        unique_sorted_tags = []

    current_query = request.args.get("q", "")
    current_category = request.args.get("category", "")
    current_tag = request.args.get("tag", "")

    return dict(
        all_categories=all_categories,
        all_tags=unique_sorted_tags,
        current_query=current_query,
        current_category=current_category,
        current_tag=current_tag,
        UserRole=UserRole,
    )

@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now(JAKARTA).year}

@app.context_processor
def utility_processor():
    def safe_title(title):
        import re
        filtered_title = re.sub(r'\s+', '_', title)
        filtered_title = re.sub(r'[\W]', '', filtered_title)
        max_length = 50
        if len(filtered_title) > max_length:
            filtered_title = filtered_title[:max_length]
        return filtered_title
    
    return dict(safe_title=safe_title)

@app.context_processor
def inject_brand_info():
    """Inject brand information into all templates."""
    try:
        from models import BrandIdentity
        # Force a fresh query to get the latest data
        db.session.expire_all()
        brand_info = BrandIdentity.query.first()
        if brand_info:
            # Ensure we have the latest data
            db.session.refresh(brand_info)
        return {"brand_info": brand_info}
    except Exception as e:
        app.logger.warning(f"Could not load brand info: {e}")
        return {"brand_info": None}

@app.context_processor
def inject_seo_data():
    """Inject SEO data with proper leveling - content SEO takes precedence over root SEO."""
    try:
        from models import RootSEO, News, Album, AlbumChapter
        
        # Initialize SEO data
        seo_data = {
            'meta_title': None,
            'meta_description': None,
            'meta_keywords': None,
            'meta_author': None,
            'meta_language': None,
            'meta_robots': None,
            'canonical_url': None,
            'og_title': None,
            'og_description': None,
            'og_image': None,
            'og_type': None,
            'og_url': None,
            'twitter_card': None,
            'twitter_title': None,
            'twitter_description': None,
            'twitter_image': None,
            'schema_markup': None
        }
        
        # Get root SEO as fallback
        path = request.path.strip('/')
        page_identifier = 'home' if not path else path.split('/')[0]
        root_seo = RootSEO.query.filter_by(
            page_identifier=page_identifier,
            is_active=True
        ).first()
        
        # Apply root SEO as base (fallback values)
        if root_seo:
            seo_data.update({
                'meta_title': root_seo.meta_title,
                'meta_description': root_seo.meta_description,
                'meta_keywords': root_seo.meta_keywords,
                'meta_author': root_seo.meta_author,
                'meta_language': root_seo.meta_language or 'id',
                'meta_robots': root_seo.meta_robots or 'index, follow',
                'canonical_url': root_seo.canonical_url,
                'og_title': root_seo.og_title,
                'og_description': root_seo.og_description,
                'og_image': root_seo.og_image,
                'og_type': root_seo.og_type or 'website',
                'og_url': request.url,
                'twitter_card': root_seo.twitter_card or 'summary_large_image',
                'twitter_title': root_seo.twitter_title,
                'twitter_description': root_seo.twitter_description,
                'twitter_image': root_seo.twitter_image,
                'schema_markup': root_seo.schema_markup
            })
        
        # Check for content-specific SEO (higher priority)
        content_seo = None
        
        # Check if this is a news/article page (URL pattern: /news/<id>/<title>)
        if path.startswith('news/'):
            # Extract news ID from URL
            path_parts = path.split('/')
            if len(path_parts) >= 2:
                try:
                    news_id = int(path_parts[1])
                    news = News.query.filter_by(id=news_id, is_visible=True).first()
                    if news:
                        content_seo = news
                        seo_data['og_type'] = 'article'
                        seo_data['og_url'] = request.url
                except ValueError:
                    pass  # Invalid news ID
        
        # Check if this is an album page (URL pattern: /album/<id>/<title>)
        elif path.startswith('album/'):
            # Extract album ID from URL
            path_parts = path.split('/')
            if len(path_parts) >= 2:
                try:
                    album_id = int(path_parts[1])
                    album = Album.query.filter_by(id=album_id, is_visible=True).first()
                    if album:
                        content_seo = album
                        seo_data['og_type'] = 'book'
                        seo_data['og_url'] = request.url
                except ValueError:
                    pass  # Invalid album ID
        
        # Check if this is a chapter page (URL pattern: /album/<album_id>/chapter/<chapter_id>/<title>)
        elif path.startswith('album/') and 'chapter' in path:
            # Extract album ID and chapter ID from URL
            path_parts = path.split('/')
            if len(path_parts) >= 4:
                try:
                    album_id = int(path_parts[1])
                    chapter_id = int(path_parts[3])
                    chapter = AlbumChapter.query.filter_by(
                        id=chapter_id, 
                        album_id=album_id
                    ).first()
                    if chapter and chapter.album and chapter.album.is_visible:
                        content_seo = chapter
                        seo_data['og_type'] = 'article'
                        seo_data['og_url'] = request.url
                except ValueError:
                    pass  # Invalid album or chapter ID
        
        # Apply content-specific SEO (overrides root SEO)
        if content_seo:
            # Meta tags
            if content_seo.meta_title:
                seo_data['meta_title'] = content_seo.meta_title
            if content_seo.meta_description:
                seo_data['meta_description'] = content_seo.meta_description
            if content_seo.meta_keywords:
                seo_data['meta_keywords'] = content_seo.meta_keywords
            if content_seo.meta_author:
                seo_data['meta_author'] = content_seo.meta_author
            if content_seo.meta_language:
                seo_data['meta_language'] = content_seo.meta_language
            if content_seo.meta_robots:
                seo_data['meta_robots'] = content_seo.meta_robots
            if content_seo.canonical_url:
                seo_data['canonical_url'] = content_seo.canonical_url
            
            # Open Graph
            if content_seo.og_title:
                seo_data['og_title'] = content_seo.og_title
            if content_seo.og_description:
                seo_data['og_description'] = content_seo.og_description
            if content_seo.og_image:
                seo_data['og_image'] = content_seo.og_image
            
            # Twitter
            if content_seo.twitter_card:
                seo_data['twitter_card'] = content_seo.twitter_card
            if content_seo.twitter_title:
                seo_data['twitter_title'] = content_seo.twitter_title
            if content_seo.twitter_description:
                seo_data['twitter_description'] = content_seo.twitter_description
            if content_seo.twitter_image:
                seo_data['twitter_image'] = content_seo.twitter_image
            
            # Schema markup
            if content_seo.schema_markup:
                seo_data['schema_markup'] = content_seo.schema_markup
        
        return {"seo_data": seo_data, "root_seo": root_seo}
    except Exception as e:
        app.logger.warning(f"Could not load SEO data: {e}")
        return {"seo_data": {}, "root_seo": None}

@app.context_processor
def inject_contact_details():
    """Inject contact details into all templates."""
    try:
        from models import ContactDetail
        contact_details = (
            ContactDetail.query.filter_by(is_active=True)
            .order_by(ContactDetail.section_order)
            .all()
        )
        return {"contact_details": contact_details}
    except Exception as e:
        app.logger.warning(f"Could not load contact details: {e}")
        return {"contact_details": []}

# ----------------------
# 📌 Register Blueprints
# ----------------------
try:    
    from routes import main_blueprint
    app.register_blueprint(main_blueprint)
    app.logger.info("✅ Blueprint 'main_blueprint' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'main_blueprint': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during blueprint registration: {e}", exc_info=True)

try:
    from routes.settings.root_seo import root_seo_bp
    app.register_blueprint(root_seo_bp)
    app.logger.info("✅ Blueprint 'root_seo_bp' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'root_seo_bp': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during root_seo blueprint registration: {e}", exc_info=True)

try:
    from routes.routes_comments import comments_bp
    app.register_blueprint(comments_bp)
    app.logger.info("✅ Blueprint 'comments_bp' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'comments_bp': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during comments blueprint registration: {e}", exc_info=True)

try:
    from routes.routes_ratings import ratings_bp
    app.register_blueprint(ratings_bp)
    app.logger.info("✅ Blueprint 'ratings_bp' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'ratings_bp': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during ratings blueprint registration: {e}", exc_info=True)

try:
    from routes.routes_ads import ads_bp
    app.register_blueprint(ads_bp)
    app.logger.info("✅ Blueprint 'ads_bp' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'ads_bp': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during ads blueprint registration: {e}", exc_info=True)

try:
    from routes.routes_albums import albums_bp
    app.register_blueprint(albums_bp)
    app.logger.info("✅ Blueprint 'albums_bp' registered successfully.")
except ImportError as e:
    app.logger.error(f"❌ Failed to import or register blueprint 'albums_bp': {e}")
except Exception as e:
    app.logger.error(f"❌ Unexpected error during albums blueprint registration: {e}", exc_info=True)

# ----------------------
# 🔧 Database Initialization
# ----------------------
def ensure_database_tables():
    """Ensure all database tables exist with correct schema."""
    try:
        # Check if database file exists
        if "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]:
            db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            
            # Create database directory if it doesn't exist
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                app.logger.info(f"📁 Created database directory: {db_dir}")
            
            # Check if database file exists
            if not os.path.exists(db_path):
                app.logger.info("🆕 Creating new database with all tables...")
                db.create_all()
                app.logger.info("✅ Database created and all tables initialized")
                return True
            else:
                # Database exists, check if all tables are present
                app.logger.info("🔍 Checking existing database tables...")
                
                # Get list of existing tables
                result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                existing_tables = [row[0] for row in result.fetchall()]
                
                # Define required tables (all models)
                from models import (
                    User, Category, News, Image, Comment, Rating, 
                    Album, AlbumChapter, ContactDetail, Permission, 
                    CustomRole, UserActivity
                )
                
                required_tables = [
                    'user', 'category', 'news', 'image', 'comment', 
                    'rating', 'album', 'album_chapter', 'contact_detail',
                    'permission', 'custom_role', 'role_permission', 'user_activity'
                ]
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if missing_tables:
                    app.logger.info(f"🔧 Creating missing tables: {missing_tables}")
                    db.create_all()
                    app.logger.info("✅ All missing tables created")
                else:
                    app.logger.info("✅ All required tables exist")
                
                # Check album table structure specifically
                if 'album' in existing_tables:
                    result = db.session.execute(text("PRAGMA table_info(album)"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    required_columns = ['total_views', 'average_rating']
                    missing_columns = [col for col in required_columns if col not in columns]
                    
                    if missing_columns:
                        app.logger.info(f"🔧 Adding missing columns to album table: {missing_columns}")
                        
                        for col in missing_columns:
                            try:
                                if col == 'total_views':
                                    db.session.execute(text("ALTER TABLE album ADD COLUMN total_views INTEGER DEFAULT 0 NOT NULL"))
                                    app.logger.info("✅ Added total_views column")
                                elif col == 'average_rating':
                                    db.session.execute(text("ALTER TABLE album ADD COLUMN average_rating FLOAT DEFAULT 0.0 NOT NULL"))
                                    app.logger.info("✅ Added average_rating column")
                            except Exception as e:
                                app.logger.warning(f"⚠️ Column {col} might already exist: {e}")
                        
                        db.session.commit()
                        app.logger.info("✅ Album table schema updated")
                    else:
                        app.logger.info("✅ Album table has all required columns")
                
                return True
        else:
            # For non-SQLite databases, just create all tables
            db.create_all()
            app.logger.info("✅ Database tables created/verified")
            return True
            
    except Exception as e:
        app.logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
        return False

with app.app_context():
    # Skip database initialization for migration commands
    if not _is_migration_cli():
        ensure_database_tables()
    else:
        app.logger.info("🔄 Migration CLI detected, skipping database initialization")

# ----------------------
# 🩺 Health Check (no CORS needed because it's /health, not /api/health)
# ----------------------
@app.route("/health")
def health_check():
    db_status = "ok"
    db_message = "Database connection successful."
    db_health_details = {}
    
    try:
        db.session.execute(func.now())
        
        # Run comprehensive health check if requested
        if request.args.get("detailed", "false").lower() == "true":
            try:
                from config.database_health_checker import DatabaseHealthChecker
                checker = DatabaseHealthChecker(app.config["SQLALCHEMY_DATABASE_URI"])
                results = checker.run_all_checks()
                summary = checker.get_summary()
                
                db_health_details = {
                    "total_checks": summary.get("total_checks", 0),
                    "passed_checks": summary.get("passed_checks", 0),
                    "failed_checks": summary.get("failed_checks", 0),
                    "success_rate": summary.get("success_rate", 0),
                    "critical_issues": summary.get("critical_issues", 0),
                    "overall_status": summary.get("overall_status", "UNKNOWN")
                }
                
                # Update status based on critical issues
                if summary.get("critical_issues", 0) > 0:
                    db_status = "warning"
                    db_message = f"Database has {summary['critical_issues']} critical issues"
                    
            except Exception as e:
                db_health_details = {"error": str(e)}
                app.logger.warning(f"⚠️ Detailed health check failed: {e}")
                
    except Exception as e:
        db_status = "error"
        db_message = f"Database connection error: {e}"
        app.logger.error(f"❌ Health check DB error: {e}")

    status_code = 200 if db_status == "ok" else 503
    return jsonify(
        {
            "status": "healthy" if db_status == "ok" else "unhealthy",
            "timestamp": datetime.now(JAKARTA).isoformat(),
            "dependencies": {
                "database": {
                    "status": db_status, 
                    "message": db_message,
                    "details": db_health_details
                }
            },
        }
    ), status_code

# ----------------------
# 🛠️ Error Handling
# ----------------------
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"⚠️ 404 Not Found: {request.path}")
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Not found"), 404
    return render_template(
        "error.html", code=404, message="Halaman Tidak Ditemukan"
    ), 404

@app.errorhandler(500)
def internal_server_error(error):
    try:
        db.session.rollback()
        app.logger.info("ℹ️ Database session rolled back due to internal error.")
    except Exception as rollback_err:
        app.logger.error(f"❌ Error during session rollback: {rollback_err}")
    app.logger.error(f"❌ Internal Server Error: {error}", exc_info=True)
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Internal server error"), 500
    return render_template(
        "error.html", code=500, message="Kesalahan Server Internal"
    ), 500

@app.errorhandler(403)
def forbidden_error(error):
    app.logger.warning(f"🚫 403 Forbidden: {request.path}")
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Forbidden"), 403
    return render_template("error.html", code=403, message="Akses Ditolak"), 403

@app.errorhandler(401)
def unauthorized_error(error):
    app.logger.warning(f"🔒 401 Unauthorized: {request.path}")
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(error="Unauthorized"), 401
    return render_template("error.html", code=401, message="Otentikasi Diperlukan"), 401

# ----------------------
# 📝 Logging Configuration
# ----------------------
def setup_logging(app_instance):
    log_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
    if not app_instance.debug:
        if not os.path.exists("logs"):
            try:
                os.mkdir("logs")
            except OSError as e:
                app_instance.logger.error(f"❌ Could not create logs directory: {e}")
        log_file = os.path.join("logs", "database.log")
        try:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=102400, backupCount=10, encoding="utf-8"
            )
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(logging.INFO)
            app_instance.logger.addHandler(file_handler)
            app_instance.logger.setLevel(logging.INFO)
            app_instance.logger.info("📝 File logging configured to INFO level.")
        except Exception as e:
            app_instance.logger.error(f"❌ Failed to setup file logging: {e}")
    else:
        app_instance.logger.setLevel(logging.DEBUG)

# ----------------------
# 🏃🏻‍♂️ Main Loop
# ----------------------
if __name__ == "__main__":
    # Only start development server if not in production mode
    if os.getenv('FLASK_ENV') != 'production':
        setup_logging(app)
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("Production mode detected. Use a WSGI server like Gunicorn or uWSGI.")
