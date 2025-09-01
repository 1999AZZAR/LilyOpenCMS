import sys
import os
from datetime import datetime, timezone
import json
import re
import unicodedata

# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at beginning to prioritize local imports

# Import app and db from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app
db = main.db

from models import RootSEO, BrandIdentity
from sqlalchemy import text

def get_seo_injection_settings():
    """Get SEO injection settings from the database."""
    try:
        result = db.session.execute(text('SELECT website_name, website_url, website_description, website_language, organization_name, organization_logo, organization_description FROM seo_injection_settings LIMIT 1'))
        row = result.fetchone()
        if row:
            return {
                'website_name': row[0] or 'LilyOpenCMS',
                'website_url': row[1] or 'https://lilycms.com',
                'website_description': row[2] or '',
                'website_language': row[3] or 'id',
                'organization_name': row[4] or 'LilyOpenCMS',
                'organization_logo': row[5] or '',
                'organization_description': row[6] or ''
            }
    except Exception as e:
        print(f"Warning: Could not load SEO injection settings: {e}")
    
    # Fallback to default values
    return {
        'website_name': 'LilyOpenCMS',
        'website_url': 'https://lilycms.com',
        'website_description': '',
        'website_language': 'id',
        'organization_name': 'LilyOpenCMS',
        'organization_logo': '',
        'organization_description': ''
    }

def generate_schema_markup(page_identifier, page_name, meta_description=None, brand_info=None, website_url=None):
    """Generate JSON-LD structured data for the page."""
    # Get actual settings from database
    settings = get_seo_injection_settings()
    actual_website_url = website_url or settings['website_url']
    actual_website_name = settings['website_name']
    actual_language = settings['website_language']
    
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_name,
        "description": meta_description or f"Welcome to {page_name}",
        "url": f"{actual_website_url}/{page_identifier}",
        "inLanguage": actual_language
    }
    
    # Add organization info with actual brand data
    brand_name = brand_info.brand_name if brand_info else actual_website_name
    schema["publisher"] = {
        "@type": "Organization",
        "name": brand_name,
        "url": actual_website_url
    }
    
    # Add logo if available
    if brand_info and brand_info.logo_header:
        schema["publisher"]["logo"] = {
            "@type": "ImageObject",
            "url": f"{actual_website_url}{brand_info.logo_header}"
        }
    elif settings['organization_logo']:
        schema["publisher"]["logo"] = {
            "@type": "ImageObject",
            "url": settings['organization_logo']
        }
    
    # Add breadcrumb for nested pages
    if page_identifier != "home":
        schema["breadcrumb"] = {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": actual_website_url
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": page_name,
                    "item": f"{actual_website_url}/{page_identifier}"
                }
            ]
        }
    
    return json.dumps(schema, ensure_ascii=False)

def calculate_seo_score(root_seo):
    """Calculate SEO score based on completeness of SEO fields."""
    score = 0
    total_fields = 8  # Number of important SEO fields
    
    if root_seo.meta_title:
        score += 1
    if root_seo.meta_description:
        score += 1
    if root_seo.meta_keywords:
        score += 1
    if root_seo.og_title:
        score += 1
    if root_seo.og_description:
        score += 1
    if root_seo.og_image:
        score += 1
    if root_seo.canonical_url:
        score += 1
    if root_seo.schema_markup:
        score += 1
    
    return int((score / total_fields) * 100)

def generate_meta_title(page_identifier, page_name, brand_info=None, settings=None):
    """Generate meta title for the page."""
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    brand_name = brand_info.brand_name if brand_info else seo_settings['website_name']
    
    # Check if we have custom settings for this page
    if settings:
        if page_identifier == "home" and settings.get("home_meta_title"):
            return settings["home_meta_title"].replace("{brand_name}", brand_name)
        elif page_identifier == "about" and settings.get("about_meta_title"):
            return settings["about_meta_title"].replace("{brand_name}", brand_name)
        elif page_identifier == "news" and settings.get("news_meta_title"):
            return settings["news_meta_title"].replace("{brand_name}", brand_name)
        elif page_identifier == "albums" and settings.get("albums_meta_title"):
            return settings["albums_meta_title"].replace("{brand_name}", brand_name)
    
    # Default templates
    if page_identifier == "home":
        return f"{brand_name} - Modern Content Management System"
    elif page_identifier == "about":
        return f"About Us - {brand_name}"
    elif page_identifier == "news":
        return f"Latest News - {brand_name}"
    elif page_identifier == "albums":
        return f"Albums & Stories - {brand_name}"
    elif page_identifier == "videos":
        return f"Videos - {brand_name}"
    elif page_identifier == "gallery":
        return f"Image Gallery - {brand_name}"
    elif page_identifier == "contact":
        return f"Contact Us - {brand_name}"
    else:
        return f"{page_name} - {brand_name}"

def generate_meta_description(page_identifier, page_name, brand_info=None, settings=None):
    """Generate meta description for the page."""
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    brand_name = brand_info.brand_name if brand_info else seo_settings['website_name']
    tagline = brand_info.tagline if brand_info else "Modern content management for the digital age"
    
    # Check if we have custom settings for this page
    if settings:
        if page_identifier == "home" and settings.get("home_meta_description"):
            return settings["home_meta_description"].replace("{brand_name}", brand_name).replace("{tagline}", tagline)
        elif page_identifier == "about" and settings.get("about_meta_description"):
            return settings["about_meta_description"].replace("{brand_name}", brand_name).replace("{tagline}", tagline)
        elif page_identifier == "news" and settings.get("news_meta_description"):
            return settings["news_meta_description"].replace("{brand_name}", brand_name).replace("{tagline}", tagline)
        elif page_identifier == "albums" and settings.get("albums_meta_description"):
            return settings["albums_meta_description"].replace("{brand_name}", brand_name).replace("{tagline}", tagline)
    
    # Default descriptions
    descriptions = {
        "home": f"{brand_name} is a modern content management system for news, stories, and digital content. {tagline}",
        "about": f"Learn about {brand_name}, our mission, team, and commitment to providing modern content management solutions for digital publishers and content creators.",
        "news": "Stay updated with the latest news, articles, and current events. Browse our comprehensive collection of news content and stay informed.",
        "albums": "Explore our collection of albums, stories, and serialized content. Discover novels, comics, and creative works from talented authors.",
        "videos": "Watch our curated collection of videos, tutorials, and multimedia content. Discover engaging video content across various topics.",
        "gallery": "Browse our image gallery featuring photos, artwork, and visual content. Discover stunning visuals and creative imagery.",
        "contact": f"Get in touch with the {brand_name} team. Find our contact information, support details, and ways to reach us.",
        "search": "Search through our comprehensive content library. Find articles, albums, videos, and more with our powerful search functionality.",
        "login": f"Access your {brand_name} account. Login to manage content, view analytics, and access administrative features.",
        "register": f"Join {brand_name} and start creating content. Register for an account to begin publishing and managing your digital content."
    }
    
    return descriptions.get(page_identifier, f"Explore {page_name} on {brand_name} - your modern content management platform.")

def generate_meta_keywords(page_identifier, page_name, brand_info=None, settings=None):
    """Generate meta keywords for the page."""
    brand_name = brand_info.brand_name if brand_info else "LilyOpenCMS"
    
    # Check if we have custom settings for this page
    if settings:
        if page_identifier == "home" and settings.get("home_meta_keywords"):
            return settings["home_meta_keywords"].replace("{brand_name}", brand_name.lower())
        elif page_identifier == "about" and settings.get("about_meta_keywords"):
            return settings["about_meta_keywords"].replace("{brand_name}", brand_name.lower())
        elif page_identifier == "news" and settings.get("news_meta_keywords"):
            return settings["news_meta_keywords"].replace("{brand_name}", brand_name.lower())
        elif page_identifier == "albums" and settings.get("albums_meta_keywords"):
            return settings["albums_meta_keywords"].replace("{brand_name}", brand_name.lower())
    
    # Default keyword sets
    keyword_sets = {
        "home": "content management, CMS, digital publishing, news, articles, stories, multimedia",
        "about": "about us, team, mission, company, organization, digital content",
        "news": "news, articles, current events, latest updates, breaking news, journalism",
        "albums": "albums, stories, novels, comics, creative works, serialized content",
        "videos": "videos, multimedia, tutorials, visual content, streaming",
        "gallery": "gallery, images, photos, artwork, visual content, photography",
        "contact": "contact, support, help, customer service, get in touch",
        "search": "search, find, discover, browse, content discovery",
        "login": "login, sign in, account, user access, authentication",
        "register": "register, sign up, create account, join, membership"
    }
    
    return keyword_sets.get(page_identifier, f"{page_name.lower()}, content, digital, {brand_name.lower()}")

def generate_open_graph_data(page_identifier, page_name, meta_description, brand_info=None, settings=None, website_url=None):
    """Generate Open Graph data for the page."""
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    actual_website_url = website_url or seo_settings['website_url']
    brand_name = brand_info.brand_name if brand_info else seo_settings['website_name']
    
    og_title = f"{page_name} - {brand_name}"
    
    if page_identifier == "home":
        og_title = f"{brand_name} - Modern Content Management System"
    
    og_description = meta_description or generate_meta_description(page_identifier, page_name, brand_info, settings)
    
    # Get OG image from settings or brand info
    og_image = f"{actual_website_url}/static/pic/logo.png"  # Default
    
    if settings and settings.get("default_og_image"):
        og_image = settings["default_og_image"]
    elif brand_info and brand_info.logo_header:
        og_image = f"{actual_website_url}{brand_info.logo_header}"
    elif seo_settings['organization_logo']:
        og_image = seo_settings['organization_logo']
    
    return og_title, og_description, og_image

def get_default_pages():
    """Get the default pages that should have SEO data."""
    return [
        {"identifier": "home", "name": "Home", "description": "Main homepage"},
        {"identifier": "about", "name": "About", "description": "About us page"},
        {"identifier": "news", "name": "News", "description": "News listing page"},
        {"identifier": "albums", "name": "Albums", "description": "Albums listing page"},
        {"identifier": "videos", "name": "Videos", "description": "Videos listing page"},
        {"identifier": "gallery", "name": "Gallery", "description": "Image gallery page"},
        {"identifier": "contact", "name": "Contact", "description": "Contact page"},
        {"identifier": "search", "name": "Search", "description": "Search results page"},
        {"identifier": "login", "name": "Login", "description": "Login page"},
        {"identifier": "register", "name": "Register", "description": "Registration page"},
        {"identifier": "privacy", "name": "Privacy Policy", "description": "Privacy policy page"},
        {"identifier": "terms", "name": "Terms of Service", "description": "Terms of service page"},
        {"identifier": "help", "name": "Help & Support", "description": "Help and support page"},
        {"identifier": "sitemap", "name": "Sitemap", "description": "Sitemap page"},
        {"identifier": "robots", "name": "Robots", "description": "Robots.txt page"}
    ]

def load_root_seo_settings():
    """Load root SEO settings from brand identity."""
    try:
        brand_info = BrandIdentity.query.first()
        settings = {}
        
        if brand_info and brand_info.seo_settings:
            # Load settings from the dedicated seo_settings field
            if isinstance(brand_info.seo_settings, dict):
                settings = brand_info.seo_settings
            else:
                # Handle case where it might be stored as JSON string
                try:
                    settings = json.loads(brand_info.seo_settings) if isinstance(brand_info.seo_settings, str) else {}
                except:
                    settings = {}
        
        return settings
    except Exception as e:
        print(f"Warning: Could not load root SEO settings: {e}")
        return {}

def get_website_url(brand_info=None, settings=None):
    """Get website URL from brand info, settings, or use default."""
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    
    # First check settings
    if settings and settings.get("website_url"):
        return settings["website_url"]
    
    # Then check brand info website_url field
    if brand_info and brand_info.website_url:
        return brand_info.website_url
    
    # Use SEO injection settings
    if seo_settings['website_url']:
        return seo_settings['website_url']
    
    # Default fallback
    return "https://lilycms.com"

def inject_root_seo():
    """Inject root SEO data for website pages."""
    print("🎯 LilyOpenCMS Root SEO Injector")
    print("=" * 50)
    
    with app.app_context():
        # Get brand identity for default values
        brand_info = BrandIdentity.query.first()
        brand_name = brand_info.brand_name if brand_info else "LilyOpenCMS"
        
        # Load root SEO settings
        settings = load_root_seo_settings()
        website_url = get_website_url(brand_info, settings)
        
        print(f"🏷️ Brand: {brand_name}")
        print(f"🌐 Website: {website_url}")
        if settings:
            print(f"⚙️ Using custom SEO settings")
        else:
            print(f"⚙️ Using default SEO settings")
        
        # Get default pages
        default_pages = get_default_pages()
        print(f"📄 Found {len(default_pages)} default pages to process")
        
        # Track statistics
        created_count = 0
        error_count = 0
        
        print(f"\n🔍 Processing root SEO data...")
        
        for i, page_info in enumerate(default_pages, 1):
            page_identifier = page_info["identifier"]
            page_name = page_info["name"]
            
            print(f"\n📄 [{i}/{len(default_pages)}] Processing: {page_name} ({page_identifier})")
            
            try:
                # Check if root SEO entry already exists
                existing_seo = RootSEO.query.filter_by(page_identifier=page_identifier).first()
                
                if existing_seo:
                    print(f"   🔄 Updating existing SEO data...")
                    # Update existing record instead of skipping
                    update_existing = True
                else:
                    update_existing = False
                
                # Generate SEO data
                print(f"   🔧 Generating SEO data...")
                
                # Generate meta title
                meta_title = generate_meta_title(page_identifier, page_name, brand_info, settings)
                
                # Generate meta description
                meta_description = generate_meta_description(page_identifier, page_name, brand_info, settings)
                
                # Generate meta keywords
                meta_keywords = generate_meta_keywords(page_identifier, page_name, brand_info, settings)
                
                # Generate Open Graph data
                og_title, og_description, og_image = generate_open_graph_data(page_identifier, page_name, meta_description, brand_info, settings, website_url)
                
                # Generate canonical URL
                canonical_url = f"{website_url}/{page_identifier}"
                
                # Generate schema markup
                schema_markup = generate_schema_markup(page_identifier, page_name, meta_description, brand_info, website_url)
                
                # Get default values from settings
                og_type = settings.get("default_og_type", "website") if settings else "website"
                twitter_card = settings.get("default_twitter_card", "summary_large_image") if settings else "summary_large_image"
                twitter_image = settings.get("default_twitter_image", og_image) if settings else og_image
                meta_language = settings.get("default_language", "id") if settings else "id"
                meta_robots = settings.get("default_meta_robots", "index, follow") if settings else "index, follow"
                
                if update_existing:
                    # Update existing record
                    existing_seo.meta_title = meta_title
                    existing_seo.meta_description = meta_description
                    existing_seo.meta_keywords = meta_keywords
                    existing_seo.og_title = og_title
                    existing_seo.og_description = og_description
                    existing_seo.og_image = og_image
                    existing_seo.og_type = og_type
                    existing_seo.twitter_card = twitter_card
                    existing_seo.twitter_title = og_title
                    existing_seo.twitter_description = og_description
                    existing_seo.twitter_image = twitter_image
                    existing_seo.canonical_url = canonical_url
                    existing_seo.meta_author = brand_name
                    existing_seo.meta_language = meta_language
                    existing_seo.meta_robots = meta_robots
                    existing_seo.structured_data_type = "WebPage"
                    existing_seo.schema_markup = schema_markup
                    existing_seo.updated_by = 1
                    existing_seo.updated_at = datetime.now(timezone.utc)
                    
                    # Calculate SEO score
                    existing_seo.seo_score = calculate_seo_score(existing_seo)
                    existing_seo.last_seo_audit = datetime.now(timezone.utc)
                    
                    # Save to database
                    db.session.commit()
                    
                    print(f"   ✅ Updated SEO data for {page_name}")
                    print(f"   📊 SEO Score: {existing_seo.seo_score}/100")
                    created_count += 1
                else:
                    # Create new root SEO entry
                    root_seo = RootSEO(
                        page_identifier=page_identifier,
                        page_name=page_name,
                        is_active=True,
                        meta_title=meta_title,
                        meta_description=meta_description,
                        meta_keywords=meta_keywords,
                        og_title=og_title,
                        og_description=og_description,
                        og_image=og_image,
                        og_type=og_type,
                        twitter_card=twitter_card,
                        twitter_title=og_title,
                        twitter_description=og_description,
                        twitter_image=twitter_image,
                        canonical_url=canonical_url,
                        meta_author=brand_name,
                        meta_language=meta_language,
                        meta_robots=meta_robots,
                        structured_data_type="WebPage",
                        schema_markup=schema_markup,
                        google_analytics_id=None,  # Can be set later
                        facebook_pixel_id=None,    # Can be set later
                        created_by=1,  # Default to first admin user
                        updated_by=1   # Default to first admin user
                    )
                    
                    # Calculate SEO score
                    root_seo.seo_score = calculate_seo_score(root_seo)
                    root_seo.last_seo_audit = datetime.now(timezone.utc)
                    
                    # Save to database
                    db.session.add(root_seo)
                    db.session.commit()
                    
                    print(f"   ✅ Created SEO data for {page_name}")
                    print(f"   📊 SEO Score: {root_seo.seo_score}/100")
                    created_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {page_name}: {e}")
                db.session.rollback()
                error_count += 1
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 ROOT SEO INJECTION SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully processed: {created_count} pages")
        print(f"❌ Errors: {error_count} pages")
        print(f"📄 Total pages processed: {len(default_pages)}")
        
        if created_count > 0:
            print(f"\n🎉 Successfully processed root SEO data for {created_count} pages!")
        else:
            print(f"\n⚠️ No pages were processed due to errors")

def show_root_seo_stats():
    """Show statistics about root SEO data."""
    print("📊 Root SEO Statistics")
    print("=" * 30)
    
    with app.app_context():
        total_pages = RootSEO.query.count()
        active_pages = RootSEO.query.filter_by(is_active=True).count()
        
        # Count pages with different SEO fields
        with_meta_title = RootSEO.query.filter(RootSEO.meta_title.isnot(None)).count()
        with_meta_desc = RootSEO.query.filter(RootSEO.meta_description.isnot(None)).count()
        with_meta_keywords = RootSEO.query.filter(RootSEO.meta_keywords.isnot(None)).count()
        with_og_title = RootSEO.query.filter(RootSEO.og_title.isnot(None)).count()
        with_schema = RootSEO.query.filter(RootSEO.schema_markup.isnot(None)).count()
        
        print(f"📄 Total pages: {total_pages}")
        print(f"✅ Active pages: {active_pages}")
        print(f"📝 With meta title: {with_meta_title}")
        print(f"📝 With meta description: {with_meta_desc}")
        print(f"🏷️ With meta keywords: {with_meta_keywords}")
        print(f"📱 With OG title: {with_og_title}")
        print(f"🏗️ With schema markup: {with_schema}")
        
        # Show page identifiers
        if total_pages > 0:
            print(f"\n📋 Page Identifiers:")
            pages = RootSEO.query.all()
            for page in pages:
                status = "✅" if page.is_active else "❌"
                print(f"   {status} {page.page_identifier} - {page.page_name}")
        
        # Calculate percentages
        if total_pages > 0:
            print(f"\n📊 Percentages:")
            print(f"   Active pages: {(active_pages/total_pages)*100:.1f}%")
            print(f"   Meta title: {(with_meta_title/total_pages)*100:.1f}%")
            print(f"   Meta description: {(with_meta_desc/total_pages)*100:.1f}%")
            print(f"   Meta keywords: {(with_meta_keywords/total_pages)*100:.1f}%")
            print(f"   OG title: {(with_og_title/total_pages)*100:.1f}%")
            print(f"   Schema markup: {(with_schema/total_pages)*100:.1f}%")

def update_existing_seo():
    """Update existing root SEO entries with missing fields."""
    print("🔄 LilyOpenCMS Root SEO Updater")
    print("=" * 50)
    
    with app.app_context():
        # Get brand identity and settings
        brand_info = BrandIdentity.query.first()
        settings = load_root_seo_settings()
        website_url = get_website_url(brand_info, settings)
        
        print(f"🏷️ Brand: {brand_info.brand_name if brand_info else 'LilyOpenCMS'}")
        print(f"🌐 Website: {website_url}")
        
        # Get all existing root SEO entries
        existing_seo = RootSEO.query.all()
        print(f"📄 Found {len(existing_seo)} existing root SEO entries")
        
        if not existing_seo:
            print("❌ No root SEO entries found")
            return
        
        # Track statistics
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔍 Updating existing root SEO data...")
        
        for i, root_seo in enumerate(existing_seo, 1):
            print(f"\n📄 [{i}/{len(existing_seo)}] Processing: {root_seo.page_name} ({root_seo.page_identifier})")
            
            try:
                updated = False
                
                # Update missing fields
                if not root_seo.meta_title:
                    root_seo.meta_title = generate_meta_title(root_seo.page_identifier, root_seo.page_name, brand_info, settings)
                    print(f"   ✅ Added meta title")
                    updated = True
                
                if not root_seo.meta_description:
                    root_seo.meta_description = generate_meta_description(root_seo.page_identifier, root_seo.page_name, brand_info, settings)
                    print(f"   ✅ Added meta description")
                    updated = True
                
                if not root_seo.meta_keywords:
                    root_seo.meta_keywords = generate_meta_keywords(root_seo.page_identifier, root_seo.page_name, brand_info, settings)
                    print(f"   ✅ Added meta keywords")
                    updated = True
                
                if not root_seo.og_title:
                    og_title, _, _ = generate_open_graph_data(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description, brand_info, settings, website_url)
                    root_seo.og_title = og_title
                    print(f"   ✅ Added OG title")
                    updated = True
                
                if not root_seo.og_description:
                    _, og_description, _ = generate_open_graph_data(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description, brand_info, settings, website_url)
                    root_seo.og_description = og_description
                    print(f"   ✅ Added OG description")
                    updated = True
                
                if not root_seo.schema_markup:
                    root_seo.schema_markup = generate_schema_markup(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description, brand_info, website_url)
                    print(f"   ✅ Added schema markup")
                    updated = True
                
                # Set default values if missing
                if not root_seo.meta_language:
                    root_seo.meta_language = settings.get("default_language", "id") if settings else "id"
                    updated = True
                
                if not root_seo.meta_robots:
                    root_seo.meta_robots = settings.get("default_meta_robots", "index, follow") if settings else "index, follow"
                    updated = True
                
                if not root_seo.twitter_card:
                    root_seo.twitter_card = settings.get("default_twitter_card", "summary_large_image") if settings else "summary_large_image"
                    updated = True
                
                if not root_seo.og_type:
                    root_seo.og_type = settings.get("default_og_type", "website") if settings else "website"
                    updated = True
                
                # Recalculate SEO score
                old_score = root_seo.seo_score
                root_seo.seo_score = calculate_seo_score(root_seo)
                root_seo.last_seo_audit = datetime.now(timezone.utc)
                
                if updated:
                    db.session.commit()
                    print(f"   📊 SEO Score: {old_score} → {root_seo.seo_score}/100")
                    updated_count += 1
                else:
                    print(f"   ⏭️ No updates needed")
                    skipped_count += 1
                
            except Exception as e:
                print(f"   ❌ Error updating {root_seo.page_name}: {e}")
                db.session.rollback()
                error_count += 1
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 ROOT SEO UPDATE SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully updated: {updated_count} pages")
        print(f"⏭️ Skipped (no updates needed): {skipped_count} pages")
        print(f"❌ Errors: {error_count} pages")
        print(f"📄 Total pages processed: {len(existing_seo)}")

def main():
    """Main function to run the root SEO injector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inject root SEO data for website pages")
    parser.add_argument("--stats", action="store_true", help="Show SEO statistics only")
    parser.add_argument("--update", action="store_true", help="Update existing root SEO entries")
    
    args = parser.parse_args()
    
    if args.stats:
        show_root_seo_stats()
    elif args.update:
        update_existing_seo()
    else:
        inject_root_seo()

if __name__ == "__main__":
    main() 