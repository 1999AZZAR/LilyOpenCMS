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

def generate_schema_markup(page_identifier, page_name, meta_description=None):
    """Generate JSON-LD structured data for the page."""
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page_name,
        "description": meta_description or f"Welcome to {page_name}",
        "url": f"https://lilycms.com/{page_identifier}",
        "inLanguage": "id"
    }
    
    # Add organization info
    schema["publisher"] = {
        "@type": "Organization",
        "name": "LilyOpenCMS",
        "url": "https://lilycms.com"
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
                    "item": "https://lilycms.com"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": page_name,
                    "item": f"https://lilycms.com/{page_identifier}"
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

def generate_meta_title(page_identifier, page_name):
    """Generate meta title for the page."""
    base_title = "LilyOpenCMS"
    
    if page_identifier == "home":
        return f"{base_title} - Modern Content Management System"
    elif page_identifier == "about":
        return f"About Us - {base_title}"
    elif page_identifier == "news":
        return f"Latest News - {base_title}"
    elif page_identifier == "albums":
        return f"Albums & Stories - {base_title}"
    elif page_identifier == "videos":
        return f"Videos - {base_title}"
    elif page_identifier == "gallery":
        return f"Image Gallery - {base_title}"
    elif page_identifier == "contact":
        return f"Contact Us - {base_title}"
    else:
        return f"{page_name} - {base_title}"

def generate_meta_description(page_identifier, page_name):
    """Generate meta description for the page."""
    descriptions = {
        "home": "LilyOpenCMS is a modern content management system for news, stories, and digital content. Discover our platform for managing articles, albums, and multimedia content.",
        "about": "Learn about LilyOpenCMS, our mission, team, and commitment to providing modern content management solutions for digital publishers and content creators.",
        "news": "Stay updated with the latest news, articles, and current events. Browse our comprehensive collection of news content and stay informed.",
        "albums": "Explore our collection of albums, stories, and serialized content. Discover novels, comics, and creative works from talented authors.",
        "videos": "Watch our curated collection of videos, tutorials, and multimedia content. Discover engaging video content across various topics.",
        "gallery": "Browse our image gallery featuring photos, artwork, and visual content. Discover stunning visuals and creative imagery.",
        "contact": "Get in touch with the LilyOpenCMS team. Find our contact information, support details, and ways to reach us.",
        "search": "Search through our comprehensive content library. Find articles, albums, videos, and more with our powerful search functionality.",
        "login": "Access your LilyOpenCMS account. Login to manage content, view analytics, and access administrative features.",
        "register": "Join LilyOpenCMS and start creating content. Register for an account to begin publishing and managing your digital content."
    }
    
    return descriptions.get(page_identifier, f"Explore {page_name} on LilyOpenCMS - your modern content management platform.")

def generate_meta_keywords(page_identifier, page_name):
    """Generate meta keywords for the page."""
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
    
    return keyword_sets.get(page_identifier, f"{page_name.lower()}, content, digital, lilycms")

def generate_open_graph_data(page_identifier, page_name, meta_description):
    """Generate Open Graph data for the page."""
    og_title = f"{page_name} - LilyOpenCMS"
    
    if page_identifier == "home":
        og_title = "LilyOpenCMS - Modern Content Management System"
    
    og_description = meta_description or generate_meta_description(page_identifier, page_name)
    
    # Default OG image - can be customized per page
    og_image = "https://lilycms.com/static/pic/logo.png"
    
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

def inject_root_seo():
    """Inject root SEO data for website pages."""
    print("🎯 LilyOpenCMS Root SEO Injector")
    print("=" * 50)
    
    with app.app_context():
        # Get brand identity for default values
        brand_info = BrandIdentity.query.first()
        brand_name = brand_info.brand_name if brand_info else "LilyOpenCMS"
        
        # Get default pages
        default_pages = get_default_pages()
        print(f"📄 Found {len(default_pages)} default pages to process")
        
        # Track statistics
        created_count = 0
        updated_count = 0
        skipped_count = 0
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
                    print(f"   ⏭️ Skipping - already exists")
                    skipped_count += 1
                    continue
                
                # Generate SEO data
                print(f"   🔧 Generating SEO data...")
                
                # Generate meta title
                meta_title = generate_meta_title(page_identifier, page_name)
                
                # Generate meta description
                meta_description = generate_meta_description(page_identifier, page_name)
                
                # Generate meta keywords
                meta_keywords = generate_meta_keywords(page_identifier, page_name)
                
                # Generate Open Graph data
                og_title, og_description, og_image = generate_open_graph_data(page_identifier, page_name, meta_description)
                
                # Generate canonical URL
                canonical_url = f"https://lilycms.com/{page_identifier}"
                
                # Generate schema markup
                schema_markup = generate_schema_markup(page_identifier, page_name, meta_description)
                
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
                    og_type="website",
                    twitter_card="summary_large_image",
                    twitter_title=og_title,
                    twitter_description=og_description,
                    twitter_image=og_image,
                    canonical_url=canonical_url,
                    meta_author=brand_name,
                    meta_language="id",
                    meta_robots="index, follow",
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
        print(f"✅ Successfully created: {created_count} pages")
        print(f"⏭️ Skipped (already exists): {skipped_count} pages")
        print(f"❌ Errors: {error_count} pages")
        print(f"📄 Total pages processed: {len(default_pages)}")
        
        if created_count > 0:
            print(f"\n🎉 Successfully created root SEO data for {created_count} pages!")
        elif skipped_count > 0:
            print(f"\nℹ️ All pages already have root SEO data ({skipped_count} pages)")
        else:
            print(f"\n⚠️ No pages were created due to errors")

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
                    root_seo.meta_title = generate_meta_title(root_seo.page_identifier, root_seo.page_name)
                    print(f"   ✅ Added meta title")
                    updated = True
                
                if not root_seo.meta_description:
                    root_seo.meta_description = generate_meta_description(root_seo.page_identifier, root_seo.page_name)
                    print(f"   ✅ Added meta description")
                    updated = True
                
                if not root_seo.meta_keywords:
                    root_seo.meta_keywords = generate_meta_keywords(root_seo.page_identifier, root_seo.page_name)
                    print(f"   ✅ Added meta keywords")
                    updated = True
                
                if not root_seo.og_title:
                    root_seo.og_title = generate_open_graph_data(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description)[0]
                    print(f"   ✅ Added OG title")
                    updated = True
                
                if not root_seo.og_description:
                    root_seo.og_description = generate_open_graph_data(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description)[1]
                    print(f"   ✅ Added OG description")
                    updated = True
                
                if not root_seo.schema_markup:
                    root_seo.schema_markup = generate_schema_markup(root_seo.page_identifier, root_seo.page_name, root_seo.meta_description)
                    print(f"   ✅ Added schema markup")
                    updated = True
                
                # Set default values if missing
                if not root_seo.meta_language:
                    root_seo.meta_language = "id"
                    updated = True
                
                if not root_seo.meta_robots:
                    root_seo.meta_robots = "index, follow"
                    updated = True
                
                if not root_seo.twitter_card:
                    root_seo.twitter_card = "summary_large_image"
                    updated = True
                
                if not root_seo.og_type:
                    root_seo.og_type = "website"
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