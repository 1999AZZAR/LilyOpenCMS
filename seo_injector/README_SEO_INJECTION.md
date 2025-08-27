# SEO Injection Scripts

This directory contains comprehensive SEO injection scripts for LilyOpenCMS that automatically generate SEO metadata for news articles, albums, and chapters.

## Overview

The SEO injection scripts are designed to:
- **Force clean injection**: Remove existing SEO data before generating new data
- **Better content parsing**: Clean markdown formatting and extract meaningful content
- **Smart image handling**: Handle internal vs external image URLs correctly
- **SEO locking**: Prevent automatic updates with the `is_seo_lock` field
- **Comprehensive SEO fields**: Generate all necessary SEO metadata

## Scripts

### 1. `inject_news_seo.py` - News Articles SEO
Generates SEO data for news articles (which represent articles in the system).

**Features:**
- Cleans markdown content for better SEO extraction
- Extracts images from content and normalizes URLs
- Generates meta descriptions from content
- Creates keyword-rich meta keywords
- Generates Open Graph data for social media
- Creates JSON-LD structured data
- Calculates SEO scores (0-100)

**Usage:**
```bash
# Run SEO injection
python helper/inject_news_seo.py

# Show statistics only
python helper/inject_news_seo.py --stats
```

### 2. `inject_album_seo.py` - Albums SEO
Generates SEO data for albums (collections of chapters/stories).

**Features:**
- Content-based SEO generation
- Album-specific structured data
- Premium/exclusive content handling
- Chapter count integration
- Author and category integration

**Usage:**
```bash
# Run SEO injection
python helper/inject_album_seo.py

# Show statistics only
python helper/inject_album_seo.py --stats
```

### 3. `inject_chapter_seo.py` - Chapters SEO
Generates SEO data for individual chapters within albums.

**Features:**
- Chapter-specific structured data
- Integration with album and news content
- Position-based SEO (chapter numbers)
- Hierarchical content relationships
- Image inheritance from album/news

**Usage:**
```bash
# Run SEO injection
python helper/inject_chapter_seo.py

# Show statistics only
python helper/inject_chapter_seo.py --stats
```

### 4. `inject_root_seo.py` - Website Pages SEO
Generates SEO data for root website pages (home, about, contact, etc.).

**Features:**
- Page-specific SEO templates
- Breadcrumb generation
- Organization structured data
- Multi-language support

**Usage:**
```bash
# Run SEO injection
python helper/inject_root_seo.py

# Show statistics only
python helper/inject_root_seo.py --stats

# Update existing SEO data
python helper/inject_root_seo.py --update
```

## Key Features

### 1. Force Clean Injection
All scripts clear existing SEO data before generating new data:
```python
def clear_existing_seo(item):
    """Clear all existing SEO data from item."""
    item.meta_description = None
    item.meta_keywords = None
    item.og_title = None
    # ... clear all SEO fields
    item.is_seo_lock = False  # Reset lock to false
```

### 2. Better Markdown Parsing
Advanced content cleaning for better SEO extraction:
```python
def clean_markdown_content(content):
    """Clean markdown content and extract plain text for SEO."""
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Remove markdown formatting
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Bold
    content = re.sub(r'\*(.*?)\*', r'\1', content)      # Italic
    content = re.sub(r'`(.*?)`', r'\1', content)        # Code
    # ... more cleaning rules
```

### 3. Smart Image Handling
Correctly handles internal vs external image URLs:
```python
def normalize_image_url(image_url, base_url="https://lilycms.com"):
    """Normalize image URL to handle internal vs external links."""
    if image_url.startswith(('http://', 'https://')):
        return image_url  # External URL
    elif image_url.startswith('/'):
        return urljoin(base_url, image_url)  # Internal absolute path
    else:
        return urljoin(base_url, '/' + image_url)  # Internal relative path
```

### 4. SEO Locking
Prevents automatic updates with the `is_seo_lock` field:
```python
# Check if SEO is locked
if item.is_seo_lock:
    print(f"   🔒 Skipping - SEO is locked")
    locked_count += 1
    continue
```

### 5. Content-Based SEO Generation
Generates SEO data from actual content:
- **Meta descriptions**: Extracted from cleaned content (160 chars max)
- **Meta keywords**: Generated from title, content, and category
- **Open Graph data**: Based on content and available images
- **Structured data**: JSON-LD with proper schema types

## Database Schema Updates

The scripts require the following database fields to be added:

### News Model
```python
# Add to News model
is_seo_lock = db.Column(db.Boolean, default=False, nullable=False)
```

### AlbumChapter Model
```python
# Add to AlbumChapter model
# SEO Fields
meta_description = db.Column(db.String(500), nullable=True)
meta_keywords = db.Column(db.String(500), nullable=True)
og_title = db.Column(db.String(200), nullable=True)
og_description = db.Column(db.String(500), nullable=True)
og_image = db.Column(db.String(255), nullable=True)
canonical_url = db.Column(db.String(255), nullable=True)
seo_slug = db.Column(db.String(255), nullable=True, unique=True, index=True)

# Advanced SEO Fields
schema_markup = db.Column(db.Text, nullable=True)
twitter_card = db.Column(db.String(50), nullable=True)
twitter_title = db.Column(db.String(200), nullable=True)
twitter_description = db.Column(db.String(500), nullable=True)
twitter_image = db.Column(db.String(255), nullable=True)
meta_author = db.Column(db.String(100), nullable=True)
meta_language = db.Column(db.String(10), nullable=True)
meta_robots = db.Column(db.String(50), nullable=True)
structured_data_type = db.Column(db.String(50), nullable=True)
seo_score = db.Column(db.Integer, nullable=True)
last_seo_audit = db.Column(db.DateTime, nullable=True)
is_seo_lock = db.Column(db.Boolean, default=False, nullable=False)
```

## SEO Score Calculation

Each script calculates an SEO score (0-100) based on:

**Basic SEO Elements (40 points):**
- Title presence and quality
- Meta description presence
- Meta keywords presence
- SEO slug presence

**Social Media Optimization (30 points):**
- Open Graph title
- Open Graph description
- Open Graph image

**Advanced SEO Elements (30 points):**
- Canonical URL
- Schema markup
- Content quality and length

## Usage Examples

### Run All SEO Injections
```bash
# News articles
python helper/inject_news_seo.py

# Albums
python helper/inject_album_seo.py

# Chapters
python helper/inject_chapter_seo.py

# Root pages
python helper/inject_root_seo.py
```

### Check Statistics
```bash
# News SEO stats
python helper/inject_news_seo.py --stats

# Album SEO stats
python helper/inject_album_seo.py --stats

# Chapter SEO stats
python helper/inject_chapter_seo.py --stats

# Root SEO stats
python helper/inject_root_seo.py --stats
```

## Output Examples

### Successful Injection
```
🎯 LilyOpenCMS News SEO Injector
==================================================
📰 Found 25 news articles in database

🔍 Analyzing news articles for SEO injection...

📰 [1/25] Processing: Breaking News: Major Update
   🗑️ Clearing existing SEO data...
   🔧 Generating SEO data...
   ✅ Generated SEO slug: breaking-news-major-update
   ✅ Generated meta description: Breaking news about major update...
   ✅ Generated meta keywords: breaking, news, major, update
   ✅ Generated OG title: Breaking News: Major Update - LilyOpenCMS
   ✅ Generated OG description: Breaking news about major update...
   ✅ Set OG image: https://lilycms.com/static/uploads/image.jpg
   ✅ Generated schema markup
   📊 SEO Score: 85/100
   ✅ Successfully updated SEO data

==================================================
📊 NEWS SEO INJECTION SUMMARY
==================================================
✅ Successfully updated: 25 news articles
🔒 Skipped (SEO locked): 0 news articles
❌ Errors: 0 news articles
📰 Total news articles processed: 25

🎉 Successfully injected SEO data for 25 news articles!
```

### Statistics Output
```
📊 News SEO Statistics
==============================
📰 Total news articles: 25
📝 With meta description: 25
🏷️ With meta keywords: 25
🔗 With SEO slug: 25
📱 With OG title: 25
🏗️ With schema markup: 25
🔒 SEO locked: 0

📊 Percentages:
   Meta description: 100.0%
   Meta keywords: 100.0%
   SEO slug: 100.0%
   OG title: 100.0%
   Schema markup: 100.0%
   SEO locked: 0.0%
```

## Best Practices

1. **Run regularly**: Execute scripts after content updates
2. **Monitor locked items**: Check for items with `is_seo_lock=True`
3. **Review generated data**: Verify meta descriptions and keywords
4. **Update images**: Ensure proper image URLs for social sharing
5. **Test structured data**: Validate JSON-LD markup

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure the Flask app is properly configured
2. **Import errors**: Check that all required models are imported
3. **Permission errors**: Ensure write access to the database
4. **Memory issues**: Process large datasets in batches

### Debug Mode

Add debug output to scripts:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Batch processing**: Handle large datasets more efficiently
- **Content analysis**: AI-powered keyword extraction
- **Image optimization**: Automatic image resizing and optimization
- **Performance metrics**: Track SEO score improvements over time
- **API integration**: Connect with external SEO tools 