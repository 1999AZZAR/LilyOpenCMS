# SEO Leveling – Comprehensive Design and Implementation

## 1) Executive Summary

- Purpose: Ensure content-specific SEO (news, albums, chapters) takes precedence over root SEO, with sensible brand/root fallbacks, consolidated into one reference.
- Outcome: Unified `seo_data` context used across templates; correct OG/Twitter/Schema per content type; no DB changes.

## 2) Architecture Overview

| Layer | Component | Purpose |
|------|-----------|---------|
| Context | `inject_seo_data()` in `main.py` | Build unified SEO data with proper priority and URL-based detection |
| Models | `RootSEO`, `News`, `Album`, `AlbumChapter` | Hold SEO fields for root and content types |
| Templates | `templates/base.html`, content templates | Render meta/OG/Twitter/schema via `seo_data` with overrides |

## 3) Priority Hierarchy

1. Content-specific SEO (highest)
2. Root SEO (fallback)
3. Brand defaults (lowest)

## 4) Unified SEO Data Shape

```python
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
    'schema_markup': None,
}
```

## 5) URL Pattern Detection

- News: `/news/<id>/<title>` → use `News` SEO; OG type `article`.
- Album: `/album/<id>/<title>` → use `Album` SEO; OG type `book`.
- Chapter: `/album/<album_id>/chapter/<chapter_id>/<title>` → use `AlbumChapter`; OG type `article`.
- Other pages: use `RootSEO` by `page_identifier` (first path segment or `home`).

## 6) Context Processor Logic (condensed)

- Initialize `seo_data` with None/defaults.
- Load `RootSEO` by `page_identifier` and apply as base values (fallbacks).
- Detect content type by URL and fetch content record.
- If found, override fields in `seo_data` with content SEO values and set OG type + URL.
- Return `seo_data` (and `root_seo` for optional template use).

## 7) Template Integration

### Base Template (`templates/base.html`)
- Replace legacy `root_seo` usage with `seo_data`:
```html
<meta name="description" content="{% if seo_data.meta_description %}{{ seo_data.meta_description }}{% else %}{{ brand_info.tagline|default('Modern content management for the digital age') }}{% endif %}">
```

### Content Templates
- Provide block overrides using content fields, e.g. reader and album detail templates:
```html
{% block og_title %}
  {% if news.og_title %}{{ news.og_title }}{% else %}{{ news.title|e }}{% endif %}
{% endblock %}
```

## 8) Supported Fields

- Core Meta: title, description, keywords, author, language, robots, canonical.
- Open Graph: title, description, image, type, url.
- Twitter: card, title, description, image.
- Structured Data: `schema_markup` (JSON-LD).

## 9) Benefits

- Content-specific optimization; correct SEO per page type.
- Robust fallback to root/brand defaults.
- Centralized, maintainable logic; easy to extend to chapters/categories.
- Backward compatible; no migrations required.

## 10) Files Touched

- `main.py` (adds `inject_seo_data` with leveling logic)
- `templates/base.html` (switch to `seo_data`)
- `templates/public/reader.html`, `templates/public/album_detail.html` (override blocks)

## 11) Testing

- Validates:
  - Root pages use `RootSEO` defaults
  - News pages use news SEO and OG type `article`
  - Album pages use album SEO and OG type `book`
  - Unknown pages fall back to root
- See `test/test_seo_leveling.py`.

## 12) Usage Examples

```python
# News SEO
news = News.query.get(1)
news.meta_title = "Custom Article Title"
news.meta_description = "Custom article description"
news.og_title = "Custom OG Title"

# Album SEO
a = Album.query.get(1)
a.meta_title = "Custom Album Title"
a.meta_description = "Custom album description"
a.og_type = "book"
```

## 13) Future Enhancements

- Add explicit Chapter SEO, Category SEO.
- Dynamic OG image generation.
- SEO analytics per content type.
- Bulk SEO operations in admin.

## 14) Migration Notes

- No database changes.
- Backward compatible; root SEO remains fallback.

---

This document consolidates and supersedes: `SEO_LEVELING_IMPLEMENTATION.md` and `seo_leveling_system.md`. Use this as the single reference for SEO leveling.
