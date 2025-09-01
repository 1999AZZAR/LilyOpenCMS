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

from models import News, Category, User, Image, BrandIdentity
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

def extract_images_from_content(content):
    """Extract image URLs from markdown content."""
    if not content:
        return []
    
    images = []
    
    # Find markdown image syntax: ![alt](url)
    markdown_images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
    for alt, url in markdown_images:
        images.append({
            'url': url.strip(),
            'alt': alt.strip(),
            'type': 'markdown'
        })
    
    # Find HTML img tags
    html_images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content)
    for url in html_images:
        images.append({
            'url': url.strip(),
            'alt': '',
            'type': 'html'
        })
    
    return images

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

def get_best_image_for_seo(news_item):
    """Get the best image for SEO from news item."""
    # First check if news has a direct image
    if news_item.image:
        if news_item.image.url:
            return normalize_image_url(news_item.image.url)
        elif news_item.image.filepath:
            return normalize_image_url(news_item.image.filepath)
    
    # Extract images from content
    content_images = extract_images_from_content(news_item.content)
    if content_images:
        # Use the first image found
        return normalize_image_url(content_images[0]['url'])
    
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

def generate_schema_markup(news_item):
    """Generate JSON-LD structured data for the news article."""
    # Get website URL
    brand_info = BrandIdentity.query.first()
    seo_settings = get_seo_settings()
    website_url = get_website_url(brand_info, seo_settings)
    
    # Get actual settings from database
    seo_injection_settings = get_seo_injection_settings()
    brand_name = brand_info.brand_name if brand_info else seo_injection_settings['website_name']
    
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": news_item.title,
        "description": news_item.meta_description or clean_markdown_content(news_item.content)[:200],
        "author": {
            "@type": "Person",
            "name": news_item.author.get_full_name() if news_item.author else "Unknown Author"
        },
        "publisher": {
            "@type": "Organization",
            "name": brand_name,
            "url": website_url
        },
        "datePublished": news_item.date.isoformat() if news_item.date else None,
        "dateModified": news_item.updated_at.isoformat() if news_item.updated_at else None,
        "inLanguage": "id",
        "genre": news_item.category.name if news_item.category else None,
        "url": f"{website_url}/news/{news_item.id}",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": f"{website_url}/news/{news_item.id}"
        }
    }
    
    # Add image if available
    image_url = get_best_image_for_seo(news_item)
    if image_url:
        schema["image"] = {
            "@type": "ImageObject",
            "url": image_url,
            "width": 800,
            "height": 600
        }
    
    # Add article body
    clean_content = clean_markdown_content(news_item.content)
    if clean_content:
        schema["articleBody"] = clean_content
    
    return json.dumps(schema, ensure_ascii=False)

def calculate_seo_score(news_item):
    """Calculate SEO score for the news article (0-100)."""
    score = 0
    
    # Basic SEO elements (40 points)
    if news_item.title and len(news_item.title.strip()) > 0:
        score += 10
    if news_item.meta_description and len(news_item.meta_description.strip()) > 0:
        score += 10
    if news_item.meta_keywords and len(news_item.meta_keywords.strip()) > 0:
        score += 10
    if news_item.seo_slug and len(news_item.seo_slug.strip()) > 0:
        score += 10
    
    # Social media optimization (30 points)
    if news_item.og_title and len(news_item.og_title.strip()) > 0:
        score += 10
    if news_item.og_description and len(news_item.og_description.strip()) > 0:
        score += 10
    if news_item.og_image and len(news_item.og_image.strip()) > 0:
        score += 10
    
    # Advanced SEO elements (30 points)
    if news_item.canonical_url and len(news_item.canonical_url.strip()) > 0:
        score += 10
    if news_item.schema_markup and len(news_item.schema_markup.strip()) > 0:
        score += 10
    if news_item.content and len(clean_markdown_content(news_item.content)) > 100:
        score += 10
    
    return min(score, 100)

def get_seo_settings():
    """Get SEO settings from BrandIdentity."""
    try:
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        if brand_info and brand_info.seo_settings:
            if isinstance(brand_info.seo_settings, dict):
                return brand_info.seo_settings
            else:
                return json.loads(brand_info.seo_settings) if isinstance(brand_info.seo_settings, str) else {}
    except Exception as e:
        print(f"Warning: Could not load SEO settings: {e}")
    return {}

def apply_template(template, variables):
    """Apply variables to a template string."""
    if not template:
        return ""
    
    result = template
    for key, value in variables.items():
        if value:
            result = result.replace(f"{{{key}}}", str(value))
    
    return result

def generate_meta_description(news_item):
    """Generate meta description from news content using templates."""
    if news_item.meta_description:
        # Use existing meta description if available
        desc = news_item.meta_description.strip()
        if len(desc) > 160:
            desc = desc[:157] + "..."
        return desc
    
    # Get SEO settings
    seo_settings = get_seo_settings()
    article_template = seo_settings.get('article_meta_description', '{excerpt} - Read the full article on {brand_name}.')
    
    # Generate excerpt from content
    clean_content = clean_markdown_content(news_item.content)
    excerpt = clean_content[:150] + "..." if len(clean_content) > 150 else clean_content
    
    # Get brand name
    brand_name = "LilyOpenCMS"  # Default
    try:
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        if brand_info and brand_info.brand_name:
            brand_name = brand_info.brand_name
    except:
        pass
    
    # Apply template
    variables = {
        'excerpt': excerpt,
        'title': news_item.title,
        'category': news_item.category.name if news_item.category else '',
        'brand_name': brand_name
    }
    
    desc = apply_template(article_template, variables)
    
    # Fallback if template didn't work
    if not desc or desc == article_template:
        # Generate from content
        if clean_content:
            desc = clean_content[:160]
            if len(clean_content) > 160:
                desc = desc[:157] + "..."
        else:
            # Fallback to title and category
            parts = [news_item.title]
            if news_item.category:
                parts.append(f"Category: {news_item.category.name}")
            desc = " - ".join(parts)
            if len(desc) > 160:
                desc = desc[:157] + "..."
    
    return desc

def generate_meta_keywords(news_item):
    """Generate meta keywords from news content using templates."""
    # Get SEO settings
    seo_settings = get_seo_settings()
    article_template = seo_settings.get('article_meta_keywords', '{category}, {title_keywords}, news, article, {brand_name}')
    
    # Generate title keywords
    title_keywords = []
    if news_item.title:
        title_words = [word.lower() for word in news_item.title.split() if len(word) > 2]
        title_keywords = title_words[:5]
    
    # Get category
    category = news_item.category.name.lower() if news_item.category else ''
    
    # Get brand name
    brand_name = "LilyOpenCMS"  # Default
    try:
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        if brand_info and brand_info.brand_name:
            brand_name = brand_info.brand_name
    except:
        pass
    
    # Apply template
    variables = {
        'category': category,
        'title_keywords': ', '.join(title_keywords),
        'brand_name': brand_name
    }
    
    keywords = apply_template(article_template, variables)
    
    # Fallback if template didn't work
    if not keywords or keywords == article_template:
        # Generate keywords manually
        keywords_list = []
        
        # Add title words
        if news_item.title:
            title_words = [word.lower() for word in news_item.title.split() if len(word) > 2]
            keywords_list.extend(title_words[:5])
        
        # Add category
        if news_item.category:
            keywords_list.append(news_item.category.name.lower())
        
        # Add content keywords
        if news_item.content:
            clean_content = clean_markdown_content(news_item.content)
            # Extract meaningful words (3+ characters)
            content_words = [word.lower() for word in clean_content.split() if len(word) > 3]
            # Get most common words (simple approach)
            word_freq = {}
            for word in content_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Add top 3 most frequent words
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords_list.extend([word for word, freq in sorted_words[:3]])
        
        # Add news-specific keywords
        if news_item.is_main_news:
            keywords_list.extend(["main", "featured", "breaking"])
        if news_item.is_premium:
            keywords_list.extend(["premium", "exclusive"])
        if news_item.is_archived:
            keywords_list.extend(["archived", "historical"])
        
        # Add content type keywords
        keywords_list.extend(["news", "article", "content", "information"])
        
        # Remove duplicates and limit
        unique_keywords = list(dict.fromkeys(keywords_list))[:10]
        keywords = ", ".join(unique_keywords)
    
    return keywords

def generate_open_graph_data(news_item):
    """Generate Open Graph data for the news article using templates."""
    # Get SEO settings
    seo_settings = get_seo_settings()
    article_template = seo_settings.get('article_og_title', '{title} - {brand_name}')
    
    # Get brand name
    brand_name = "LilyOpenCMS"  # Default
    try:
        from models import BrandIdentity
        brand_info = BrandIdentity.query.first()
        if brand_info and brand_info.brand_name:
            brand_name = brand_info.brand_name
    except:
        pass
    
    # Apply template for OG title
    variables = {
        'title': news_item.title,
        'brand_name': brand_name
    }
    
    og_title = apply_template(article_template, variables)
    
    # Fallback if template didn't work
    if not og_title or og_title == article_template:
        og_title = news_item.og_title or news_item.title
    
    og_description = news_item.og_description or generate_meta_description(news_item)
    og_image = news_item.og_image
    
    if not og_image:
        og_image = get_best_image_for_seo(news_item)
    
    return og_title, og_description, og_image

def clear_existing_seo(news_item):
    """Clear all existing SEO data from news item."""
    print(f"   🗑️ Clearing existing SEO data...")
    
    # Clear all SEO fields
    news_item.meta_description = None
    news_item.meta_keywords = None
    news_item.og_title = None
    news_item.og_description = None
    news_item.og_image = None
    news_item.canonical_url = None
    news_item.seo_slug = None
    news_item.schema_markup = None
    news_item.twitter_card = None
    news_item.twitter_title = None
    news_item.twitter_description = None
    news_item.twitter_image = None
    news_item.meta_author = None
    news_item.meta_language = None
    news_item.meta_robots = None
    news_item.structured_data_type = None
    news_item.seo_score = None
    news_item.last_seo_audit = None
    news_item.is_seo_lock = False  # Reset lock to false

def inject_news_seo():
    """Inject SEO data for news articles that don't have SEO fields populated."""
    print("🎯 LilyOpenCMS News SEO Injector")
    print("=" * 50)
    
    with app.app_context():
        # Get all news articles
        news_items = News.query.all()
        print(f"📰 Found {len(news_items)} news articles in database")
        
        if not news_items:
            print("❌ No news articles found in database")
            return
        
        # Track statistics
        updated_count = 0
        skipped_count = 0
        error_count = 0
        locked_count = 0
        
        print(f"\n🔍 Analyzing news articles for SEO injection...")
        
        for i, news_item in enumerate(news_items, 1):
            print(f"\n📰 [{i}/{len(news_items)}] Processing: {news_item.title}")
            
            try:
                # Check if SEO is locked
                if news_item.is_seo_lock:
                    print(f"   🔒 Skipping - SEO is locked")
                    locked_count += 1
                    continue
                
                # Clear existing SEO data first (force clean injection)
                clear_existing_seo(news_item)
                
                # Generate SEO data
                print(f"   🔧 Generating SEO data...")
                
                # Generate SEO slug
                news_item.seo_slug = generate_seo_slug(news_item.title)
                print(f"   ✅ Generated SEO slug: {news_item.seo_slug}")
                
                # Generate meta title using template
                seo_settings = get_seo_settings()
                article_title_template = seo_settings.get('article_meta_title', '{title} - {brand_name}')
                
                # Get brand name
                brand_name = "LilyOpenCMS"  # Default
                try:
                    from models import BrandIdentity
                    brand_info = BrandIdentity.query.first()
                    if brand_info and brand_info.brand_name:
                        brand_name = brand_info.brand_name
                except:
                    pass
                
                # Apply template for meta title
                variables = {
                    'title': news_item.title,
                    'category': news_item.category.name if news_item.category else '',
                    'brand_name': brand_name
                }
                
                news_item.meta_title = apply_template(article_title_template, variables)
                if not news_item.meta_title or news_item.meta_title == article_title_template:
                    news_item.meta_title = f"{news_item.title} - {brand_name}"
                print(f"   ✅ Generated meta title: {news_item.meta_title}")
                
                # Generate meta description
                news_item.meta_description = generate_meta_description(news_item)
                print(f"   ✅ Generated meta description: {news_item.meta_description[:50]}...")
                
                # Generate meta keywords
                news_item.meta_keywords = generate_meta_keywords(news_item)
                print(f"   ✅ Generated meta keywords: {news_item.meta_keywords}")
                
                # Generate Open Graph data
                og_title, og_description, og_image = generate_open_graph_data(news_item)
                
                news_item.og_title = og_title
                print(f"   ✅ Generated OG title: {news_item.og_title}")
                
                news_item.og_description = og_description
                print(f"   ✅ Generated OG description: {news_item.og_description[:50]}...")
                
                news_item.og_image = og_image
                print(f"   ✅ Set OG image: {news_item.og_image}")
                
                # Generate schema markup
                news_item.schema_markup = generate_schema_markup(news_item)
                print(f"   ✅ Generated schema markup")
                
                # Get website URL for canonical URL
                brand_info = BrandIdentity.query.first()
                website_url = get_website_url(brand_info, seo_settings)
                
                # Set default values
                news_item.meta_author = news_item.author.get_full_name() if news_item.author else "Unknown Author"
                news_item.meta_language = "id"
                news_item.meta_robots = "index, follow"
                news_item.twitter_card = "summary_large_image"
                news_item.structured_data_type = "NewsArticle"
                news_item.canonical_url = f"{website_url}/news/{news_item.id}"
                
                # Calculate SEO score
                news_item.seo_score = calculate_seo_score(news_item)
                news_item.last_seo_audit = datetime.now(timezone.utc)
                
                print(f"   📊 SEO Score: {news_item.seo_score}/100")
                
                # Save to database
                db.session.commit()
                print(f"   ✅ Successfully updated SEO data")
                updated_count += 1
                
            except Exception as e:
                print(f"   ❌ Error processing news article: {e}")
                db.session.rollback()
                error_count += 1
        
        # Final summary
        print("\n" + "=" * 50)
        print("📊 NEWS SEO INJECTION SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully updated: {updated_count} news articles")
        print(f"🔒 Skipped (SEO locked): {locked_count} news articles")
        print(f"❌ Errors: {error_count} news articles")
        print(f"📰 Total news articles processed: {len(news_items)}")
        
        if updated_count > 0:
            print(f"\n🎉 Successfully injected SEO data for {updated_count} news articles!")
        elif locked_count > 0:
            print(f"\nℹ️ All news articles have locked SEO ({locked_count} articles)")
        else:
            print(f"\n⚠️ No news articles were updated due to errors")

def show_news_seo_stats():
    """Show statistics about news SEO data."""
    print("📊 News SEO Statistics")
    print("=" * 30)
    
    with app.app_context():
        total_news = News.query.count()
        
        # Count news with different SEO fields
        with_meta_desc = News.query.filter(News.meta_description.isnot(None)).count()
        with_meta_keywords = News.query.filter(News.meta_keywords.isnot(None)).count()
        with_seo_slug = News.query.filter(News.seo_slug.isnot(None)).count()
        with_og_title = News.query.filter(News.og_title.isnot(None)).count()
        with_schema = News.query.filter(News.schema_markup.isnot(None)).count()
        locked_seo = News.query.filter_by(is_seo_lock=True).count()
        
        print(f"📰 Total news articles: {total_news}")
        print(f"📝 With meta description: {with_meta_desc}")
        print(f"🏷️ With meta keywords: {with_meta_keywords}")
        print(f"🔗 With SEO slug: {with_seo_slug}")
        print(f"📱 With OG title: {with_og_title}")
        print(f"🏗️ With schema markup: {with_schema}")
        print(f"🔒 SEO locked: {locked_seo}")
        
        # Calculate percentages
        if total_news > 0:
            print(f"\n📊 Percentages:")
            print(f"   Meta description: {(with_meta_desc/total_news)*100:.1f}%")
            print(f"   Meta keywords: {(with_meta_keywords/total_news)*100:.1f}%")
            print(f"   SEO slug: {(with_seo_slug/total_news)*100:.1f}%")
            print(f"   OG title: {(with_og_title/total_news)*100:.1f}%")
            print(f"   Schema markup: {(with_schema/total_news)*100:.1f}%")
            print(f"   SEO locked: {(locked_seo/total_news)*100:.1f}%")

def main():
    """Main function to run the SEO injector."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inject SEO data for news articles")
    parser.add_argument("--stats", action="store_true", help="Show SEO statistics only")
    parser.add_argument("--force", action="store_true", help="Force update even if SEO data exists")
    
    args = parser.parse_args()
    
    if args.stats:
        show_news_seo_stats()
    else:
        inject_news_seo()

if __name__ == "__main__":
    main() 