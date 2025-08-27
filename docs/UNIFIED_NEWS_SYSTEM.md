# Unified News System

## Overview

The unified news system consolidates all news-related pages (`hypes.html`, `articles.html`, `utama.html`, and `news.html`) into a single, dynamic template that can handle different content types through URL parameters and AJAX loading.

## Key Features

### 1. Single Template Approach
- **One template**: `templates/public/news.html` handles all news content types
- **Dynamic content**: Content type is determined by URL parameters
- **AJAX loading**: Similar to `albums.html` for better user experience
- **Search integration**: Uses existing search functionality from `base.html`

### 2. Content Types
- **General** (`/news`): All news articles
- **Hypes** (`/news?type=hypes`): Popular content based on shares and reads
- **Articles** (`/news?type=articles`): Non-news articles only
- **Utama** (`/news?type=utama`): Main/featured news

### 3. Filtering Options
- **Search**: Text search in title and content
- **Category**: Filter by category ID
- **Tags**: Filter by tag names
- **Sorting**: Newest, oldest, popular, least popular

### 4. URL Structure
```
/news                           # General news
/news?type=hypes               # Popular content
/news?type=articles            # Articles only
/news?type=utama              # Main news
/news?q=search&category=1     # Search with filters
/news?tag=technology          # Tag filtering
```

## Implementation Details

### Backend Changes

#### 1. New API Endpoint
```python
@main_blueprint.route("/api/search/news", methods=["GET"])
def search_news_api():
    """Unified API endpoint for news search with content type filtering."""
```

**Features:**
- Content type filtering (hypes, articles, utama, general)
- Search query support
- Category and tag filtering
- Multiple sorting options
- Pagination support
- Share count calculation for hypes

#### 2. Updated Routes
- `/hypes` → redirects to `/news?type=hypes`
- `/articles` → redirects to `/news?type=articles`
- `/utama` → redirects to `/news?type=utama`
- `/search` → redirects to `/news` with search parameters

### Frontend Changes

#### 1. Unified Template (`news.html`)
**Features:**
- Content type tabs for easy switching
- AJAX-based dynamic loading
- Real-time search and filtering
- URL state management
- Responsive design
- Project's thumbnailing mechanism

#### 2. JavaScript Functionality
- **Content type switching**: Tab-based navigation
- **Search debouncing**: 300ms delay for better performance
- **URL synchronization**: Browser back/forward support
- **Pagination**: Dynamic page loading
- **Error handling**: User-friendly error messages

### 3. Removed Templates
- `templates/public/hypes.html` (deleted)
- `templates/public/articles.html` (deleted)
- `templates/public/utama.html` (deleted)

## Benefits

### 1. Maintainability
- **Single template**: Easier to maintain and update
- **Consistent UI**: Unified user experience across all news types
- **Reduced code duplication**: DRY principle applied

### 2. Performance
- **AJAX loading**: Faster page transitions
- **Debounced search**: Reduced server load
- **Lazy loading**: Better image loading performance

### 3. User Experience
- **Seamless navigation**: No page reloads for filtering
- **URL sharing**: Direct links to filtered results
- **Responsive design**: Works on all devices
- **Search highlighting**: Matched terms are highlighted

### 4. Backward Compatibility
- **Existing URLs work**: All old links redirect properly
- **Search functionality**: Maintains existing search from `base.html`
- **Index page**: No changes needed to `index.html`

## API Response Format

```json
{
  "success": true,
  "news": [
    {
      "id": 1,
      "title": "News Title",
      "content": "News content...",
      "excerpt": "News excerpt...",
      "category": "Technology",
      "url": "/news/1/news-title",
      "date": "2024-01-01T00:00:00Z",
      "read_count": 100,
      "is_news": true,
      "is_premium": false,
      "is_main_news": false,
      "total_share": 25
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 9,
    "pages": 5,
    "total": 45,
    "has_prev": false,
    "has_next": true,
    "prev_num": null,
    "next_num": 2
  },
  "search_info": {
    "total_count": 45,
    "query": "search term",
    "category": "1",
    "tag": "technology",
    "sort": "newest",
    "type": "general"
  }
}
```

## Usage Examples

### 1. Direct URL Access
```bash
# General news
curl "http://localhost:5000/news"

# Popular content
curl "http://localhost:5000/news?type=hypes"

# Articles only
curl "http://localhost:5000/news?type=articles"

# Search with filters
curl "http://localhost:5000/news?q=technology&category=1&sort=popular"
```

### 2. API Access
```bash
# Get popular content
curl "http://localhost:5000/api/search/news?type=hypes"

# Search with category filter
curl "http://localhost:5000/api/search/news?q=AI&category=1"

# Get articles with tag filter
curl "http://localhost:5000/api/search/news?type=articles&tag=technology"
```

## Testing

A test script (`test_unified_news.py`) is provided to verify:
- API endpoint functionality
- URL redirects
- Content type filtering
- Search and filtering
- Error handling

Run the test:
```bash
python test_unified_news.py
```

## Future Enhancements

1. **Advanced filtering**: Date range, author filtering
2. **Saved searches**: User preference storage
3. **Analytics**: Track popular searches and filters
4. **Caching**: Redis-based caching for better performance
5. **Real-time updates**: WebSocket for live content updates

## Conclusion

The unified news system successfully consolidates four separate templates into one dynamic, maintainable solution while preserving all existing functionality and improving user experience through AJAX loading and enhanced filtering options. 