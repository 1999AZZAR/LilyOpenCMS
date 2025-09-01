import sys
import os
from datetime import datetime, timezone
import random
import json
import re
import unicodedata
import html
from urllib.parse import urlparse, urljoin

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

from models import Album, Category, User, BrandIdentity
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

def clean_markdown_content(content):
    """Clean markdown content and extract plain text for SEO with enhanced filtering."""
    if not content:
        return ""
    
    # Remove HTML tags completely
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove markdown formatting with better patterns
    # Headers (all levels)
    content = re.sub(r'^#{1,6}\s+(.*?)$', r'\1', content, flags=re.MULTILINE)
    
    # Bold and italic (handle nested cases)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
    content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic (but not if it's part of bold)
    content = re.sub(r'__(.*?)__', r'\1', content)      # Bold underscore
    content = re.sub(r'_(.*?)_', r'\1', content)        # Italic underscore
    
    # Code blocks and inline code
    content = re.sub(r'```[\s\S]*?```', '', content)    # Code blocks
    content = re.sub(r'`([^`]+)`', r'\1', content)      # Inline code
    
    # Links (extract text only)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Markdown links
    content = re.sub(r'<([^>]+)>', r'\1', content)              # HTML links
    
    # Images (remove completely)
    content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)    # Markdown images
    content = re.sub(r'<img[^>]+>', '', content)                # HTML images
    
    # Strikethrough
    content = re.sub(r'~~(.*?)~~', r'\1', content)      # Strikethrough
    
    # Lists (remove markers)
    content = re.sub(r'^\s*[-*+]\s+', '', content, flags=re.MULTILINE)  # Unordered lists
    content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)  # Ordered lists
    
    # Blockquotes
    content = re.sub(r'^\s*>\s+', '', content, flags=re.MULTILINE)       # Blockquotes
    
    # Horizontal rules
    content = re.sub(r'^[-*_]{3,}$', '', content, flags=re.MULTILINE)    # Horizontal rules
    
    # Tables (simplify to text)
    content = re.sub(r'\|[^|]*\|', '', content)                          # Table rows
    content = re.sub(r'^\s*[-|:]+\s*$', '', content, flags=re.MULTILINE) # Table separators
    
    # Footnotes
    content = re.sub(r'\[\^([^\]]+)\]', '', content)                     # Footnotes
    
    # Escaped characters
    content = re.sub(r'\\([\\`*_{}\[\]()#+\-!])', r'\1', content)       # Escaped markdown chars
    
    # Clean up whitespace and formatting
    content = re.sub(r'\n\s*\n', '\n', content)  # Multiple newlines to single
    content = re.sub(r'\n{3,}', '\n\n', content) # More than 2 newlines to 2
    content = re.sub(r'\s+', ' ', content)       # Multiple spaces to single
    content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)  # Trim lines
    content = content.strip()
    
    # Remove any remaining markdown artifacts
    content = re.sub(r'^\s*[#*\-+`~]\s*', '', content, flags=re.MULTILINE)
    
    return content

def normalize_image_url(image_url, base_url=None):
    """Normalize image URL to handle internal vs external links."""
    if not image_url:
        return None
    
    # Get actual settings from database
    if base_url is None:
        seo_settings = get_seo_injection_settings()
        base_url = seo_settings['website_url']
    
    # If it's already a full URL
    if image_url.startswith(('http://', 'https://')):
        return image_url
    
    # If it's a relative path starting with /
    if image_url.startswith('/'):
        return urljoin(base_url, image_url)
    
    # If it's a relative path without /
    if not image_url.startswith('/'):
        return urljoin(base_url, '/' + image_url)
    
    return image_url

def get_seo_settings():
    """Get SEO settings from BrandIdentity."""
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
        print(f"Warning: Could not load SEO settings: {e}")
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

def get_best_image_for_seo(album):
    """Get the best image for SEO from album."""
    # Check if album has a cover image
    if album.cover_image:
        if album.cover_image.url:
            return normalize_image_url(album.cover_image.url)
        elif album.cover_image.filepath:
            return normalize_image_url(album.cover_image.filepath)
    
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    base_url = seo_settings['website_url']
    
    # Default image
    return f"{base_url}/static/pic/placeholder.png"

def generate_seo_slug(title):
    """Generate SEO-friendly slug from title."""
    if not title:
        return None
    
    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)
    
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-').lower()
    
    # Limit length
    if len(slug) > 50:
        slug = slug[:50]
    
    return slug

def generate_schema_markup(album):
    """Generate JSON-LD structured data for the album."""
    # Get actual settings from database
    seo_settings = get_seo_injection_settings()
    website_url = seo_settings['website_url']
    organization_name = seo_settings['organization_name']
    
    schema = {
        "@context": "https://schema.org",
        "@type": "Book" if album.is_completed else "CreativeWork",
        "name": album.title,
        "description": album.description or album.title,
        "author": {
            "@type": "Person",
            "name": album.author.get_full_name() if album.author else "Unknown Author"
        },
        "publisher": {
            "@type": "Organization",
            "name": organization_name,
            "url": website_url
        },
        "datePublished": album.created_at.isoformat() if album.created_at else None,
        "dateModified": album.updated_at.isoformat() if album.updated_at else None,
        "numberOfPages": album.total_chapters,
        "isAccessibleForFree": not album.is_premium,
        "inLanguage": seo_settings['website_language'],
        "genre": album.category.name if album.category else None,
        "url": f"{website_url}/album/{album.id}",
    }
    
    # Add book-specific properties if completed
    if album.is_completed:
        schema["bookFormat"] = "Digital"
        schema["isbn"] = f"ALBUM-{album.id:06d}"
    
    # Add image if available
    image_url = get_best_image_for_seo(album)
    if image_url:
        schema["image"] = {
            "@type": "ImageObject",
            "url": image_url,
            "width": 800,
            "height": 600
        }
    
    return json.dumps(schema, ensure_ascii=False)

def calculate_seo_score(album):
    """Calculate SEO score for the album (0-100)."""
    score = 0
    
    # Basic SEO elements (40 points)
    if album.title and len(album.title.strip()) > 0:
        score += 10
    if album.description and len(album.description.strip()) > 0:
        score += 10
    if album.meta_description and len(album.meta_description.strip()) > 0:
        score += 10
    if album.meta_keywords and len(album.meta_keywords.strip()) > 0:
        score += 10
    
    # Social media optimization (30 points)
    if album.og_title and len(album.og_title.strip()) > 0:
        score += 10
    if album.og_description and len(album.og_description.strip()) > 0:
        score += 10
    if album.og_image and len(album.og_image.strip()) > 0:
        score += 10
    
    # Advanced SEO elements (30 points)
    if album.seo_slug and len(album.seo_slug.strip()) > 0:
        score += 10
    if album.canonical_url and len(album.canonical_url.strip()) > 0:
        score += 10
    if album.schema_markup and len(album.schema_markup.strip()) > 0:
        score += 10
    
    return min(score, 100)

def generate_meta_description(album):
    """Generate meta description from album content."""
    if album.description:
        # Use description if available, limit to 160 characters
        desc = album.description.strip()
        if len(desc) > 160:
            desc = desc[:157] + "..."
        return desc
    else:
        # Generate from title and category
        parts = [album.title]
        if album.category:
            parts.append(f"Category: {album.category.name}")
        if album.total_chapters > 0:
            parts.append(f"{album.total_chapters} chapters")
        
        desc = " - ".join(parts)
        if len(desc) > 160:
            desc = desc[:157] + "..."
        return desc

def generate_meta_keywords(album):
    """Generate meta keywords from album content."""
    keywords = []
    
    # Add title words
    if album.title:
        title_words = [word.lower() for word in album.title.split() if len(word) > 2]
        keywords.extend(title_words[:5])
    
    # Add category
    if album.category:
        keywords.append(album.category.name.lower())
    
    # Add content type
    if album.is_completed:
        keywords.extend(["completed", "finished"])
    else:
        keywords.extend(["ongoing", "in-progress"])
    
    # Add premium status
    if album.is_premium:
        keywords.append("premium")
    
    # Add genre-related keywords
    if album.category:
        category_keywords = {
            "Novel": ["novel", "fiction", "story"],
            "Comic": ["comic", "manga", "graphic"],
            "Poetry": ["poetry", "poem", "verse"],
            "Article": ["article", "blog", "content"],
            "News": ["news", "current", "update"]
        }
        keywords.extend(category_keywords.get(album.category.name, []))
    
    # Remove duplicates and limit
    unique_keywords = list(dict.fromkeys(keywords))[:10]
    return ", ".join(unique_keywords)

def generate_open_graph_data(album):
    """Generate Open Graph data for the album."""
    og_title = album.og_title or album.title
    og_description = album.og_description or generate_meta_description(album)
    og_image = album.og_image
    
    if not og_image:
        og_image = get_best_image_for_seo(album)
    
    return og_title, og_description, og_image

def clear_existing_seo(album):
    """Clear all existing SEO data from album."""
    print(f"   🗑️ Clearing existing SEO data...")
    
    # Clear all SEO fields
    album.meta_description = None
    album.meta_keywords = None
    album.og_title = None
    album.og_description = None
    album.og_image = None
    album.canonical_url = None
    album.seo_slug = None
    album.schema_markup = None
    album.twitter_card = None
    album.twitter_title = None
    album.twitter_description = None
    album.twitter_image = None
    album.meta_author = None
    album.meta_language = None
    album.meta_robots = None
    album.structured_data_type = None
    album.seo_score = None
    album.last_seo_audit = None
    album.is_seo_lock = False  # Reset lock to false

def inject_album_seo():
    """Inject SEO data for albums that don't have SEO fields populated."""
    print("🎯 LilyOpenCMS Album SEO Injector")
    print("=" * 50)
    
    with app.app_context():
        # Get all albums
        albums = Album.query.all()
        print(f"📚 Found {len(albums)} albums in database")
        
        if not albums:
            print("❌ No albums found in database")
            return
        
        # Track statistics
        updated_count = 0
        skipped_count = 0
        error_count = 0
        locked_count = 0
        
        print(f"\n🔍 Analyzing albums for SEO injection...")
        
        for i, album in enumerate(albums, 1):
            print(f"\n📖 [{i}/{len(albums)}] Processing: {album.title}")
            
            try:
                # Check if SEO is locked
                if album.is_seo_lock:
                    print(f"   🔒 Skipping - SEO is locked")
                    locked_count += 1
                    continue
                
                # Clear existing SEO data first (force clean injection)
                clear_existing_seo(album)
                
                # Generate SEO data
                print(f"   🔧 Generating SEO data...")
                
                # Generate SEO slug
                album.seo_slug = generate_seo_slug(album.title)
                print(f"   ✅ Generated SEO slug: {album.seo_slug}")
                
                # Generate meta description
                album.meta_description = generate_meta_description(album)
                print(f"   ✅ Generated meta description: {album.meta_description[:50]}...")
                
                # Generate meta keywords
                album.meta_keywords = generate_meta_keywords(album)
                print(f"   ✅ Generated meta keywords: {album.meta_keywords}")
                
                # Generate Open Graph data
                og_title, og_description, og_image = generate_open_graph_data(album)
                
                album.og_title = og_title
                print(f"   ✅ Generated OG title: {album.og_title}")
                
                album.og_description = og_description
                print(f"   ✅ Generated OG description: {album.og_description[:50]}...")
                
                album.og_image = og_image
                print(f"   ✅ Set OG image: {album.og_image}")
                
                # Generate schema markup
                album.schema_markup = generate_schema_markup(album)
                print(f"   ✅ Generated schema markup")
                
                # Get website URL for canonical URL
                brand_info = BrandIdentity.query.first()
                seo_settings = get_seo_settings()
                website_url = get_website_url(brand_info, seo_settings)
                
                # Set default values
                album.meta_author = album.author.get_full_name() if album.author else "Unknown Author"
                album.meta_language = "id"
                album.meta_robots = "index, follow"
                album.twitter_card = "summary_large_image"
                album.structured_data_type = "Book" if album.is_completed else "CreativeWork"
                album.canonical_url = f"{website_url}/album/{album.id}"
                
                # Calculate SEO score
                album.seo_score = calculate_seo_score(album)
                album.last_seo_audit = datetime.now(timezone.utc)
                
                print(f"   📊 SEO Score: {album.seo_score}/100")
                
                # Save to database
                db.session.commit()
                print(f"   ✅ Successfully updated SEO data")
                updated_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing album: {e}")
                db.session.rollback()
                error_count += 1
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 ALBUM SEO INJECTION SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully updated: {updated_count} albums")
        print(f"🔒 Skipped (SEO locked): {locked_count} albums")
        print(f"❌ Errors: {error_count} albums")
        print(f"📚 Total albums processed: {len(albums)}")
        
        if updated_count > 0:
            print(f"\n🎉 Successfully injected SEO data for {updated_count} albums!")
        elif locked_count > 0:
            print(f"\nℹ️ All albums have locked SEO ({locked_count} albums)")
        else:
            print(f"\n⚠️ No albums were updated due to errors")

def show_album_seo_stats():
    """Show statistics about album SEO data."""
    print("📊 Album SEO Statistics")
    print("=" * 30)
    
    with app.app_context():
        total_albums = Album.query.count()
        
        # Count albums with different SEO fields
        with_meta_desc = Album.query.filter(Album.meta_description.isnot(None)).count()
        with_meta_keywords = Album.query.filter(Album.meta_keywords.isnot(None)).count()
        with_seo_slug = Album.query.filter(Album.seo_slug.isnot(None)).count()
        with_og_title = Album.query.filter(Album.og_title.isnot(None)).count()
        with_schema = Album.query.filter(Album.schema_markup.isnot(None)).count()
        locked_seo = Album.query.filter_by(is_seo_lock=True).count()
        
        print(f"📚 Total albums: {total_albums}")
        print(f"📝 With meta description: {with_meta_desc}")
        print(f"🏷️ With meta keywords: {with_meta_keywords}")
        print(f"🔗 With SEO slug: {with_seo_slug}")
        print(f"📱 With OG title: {with_og_title}")
        print(f"🏗️ With schema markup: {with_schema}")
        print(f"🔒 SEO locked: {locked_seo}")
        
        # Calculate percentages
        if total_albums > 0:
            print(f"\n📊 Percentages:")
            print(f"   Meta description: {(with_meta_desc/total_albums)*100:.1f}%")
            print(f"   Meta keywords: {(with_meta_keywords/total_albums)*100:.1f}%")
            print(f"   SEO slug: {(with_seo_slug/total_albums)*100:.1f}%")
            print(f"   OG title: {(with_og_title/total_albums)*100:.1f}%")
            print(f"   Schema markup: {(with_schema/total_albums)*100:.1f}%")
            print(f"   SEO locked: {(locked_seo/total_albums)*100:.1f}%")

def main():
    """Main function to run the SEO injector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inject SEO data for albums")
    parser.add_argument("--stats", action="store_true", help="Show SEO statistics only")
    parser.add_argument("--force", action="store_true", help="Force update even if SEO data exists")
    
    args = parser.parse_args()
    
    if args.stats:
        show_album_seo_stats()
    else:
        inject_album_seo()

if __name__ == "__main__":
    main() 