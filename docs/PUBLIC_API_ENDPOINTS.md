# Public API Endpoints Documentation (Consolidated in API_CENTRAL.md)

This content is centralized in `docs/API_CENTRAL.md`. This file remains as a focused reference for public endpoints.

## Overview

The public API endpoints are designed to provide the same data as the HTML pages but in structured JSON format. This enables:
- Mobile applications
- Desktop clients  
- Third-party integrations
- API consumers and automation
- Modern JavaScript frameworks and PWAs

All endpoints are publicly accessible and do not require authentication, though some may return limited information for premium content.

## Base URL

All endpoints are prefixed with `/api/public/`

## Authentication

**No authentication required** - These are public endpoints accessible to all users.

## Response Format

All responses are in JSON format with the following structure:
- Success responses: Direct data or object with data
- Error responses: `{"error": "Error message"}` with appropriate HTTP status codes

## Endpoints

### News API

#### Get Single News Article
```
GET /api/public/news/{news_id}
```

Returns detailed information about a specific news article.

**Response for non-premium content:**
```json
{
  "id": 123,
  "title": "Article Title",
  "content": "Full article content...",
  "excerpt": "Article excerpt...",
  "is_premium": false,
  "category": {
    "id": 1,
    "name": "Technology",
    "description": "Tech-related articles"
  },
  "header_image": {
    "id": 456,
    "url": "/uploads/image.jpg",
    "alt_text": "Image description",
    "caption": "Image caption"
  },
  "author": {
    "id": 789,
    "username": "author_name",
    "display_name": "Author Display Name",
    "avatar_url": "/uploads/avatar.jpg"
  },
  "tags": ["tag1", "tag2"],
  "related_news": [...],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "read_count": 150,
  "share_count": 25,
  "is_news": true
}
```

**Response for premium content:**
```json
{
  "id": 123,
  "title": "Premium Article",
  "excerpt": "Article excerpt...",
  "is_premium": true,
  "category": {
    "id": 1,
    "name": "Technology"
  },
  "message": "Premium content - full access requires authentication"
}
```

#### Get News List
```
GET /api/public/news?page=1&per_page=20&category=1&search=query&sort=latest
```

Returns a paginated list of news articles with filtering options.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 20)
- `category` (optional): Category ID filter
- `search` (optional): Search query
- `sort` (optional): Sort order - "latest", "popular" (default: "latest")

**Response:**
```json
{
  "news": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "filters": {
    "categories": [
      {"id": 1, "name": "Technology"},
      {"id": 2, "name": "Science"}
    ],
    "current_category": 1,
    "current_search": "query",
    "current_sort": "latest"
  }
}
```

### Albums API

#### Get Single Album
```
GET /api/public/albums/{album_id}
```

Returns detailed information about a specific album.

**Response for non-premium content:**
```json
{
  "id": 456,
  "title": "Album Title",
  "description": "Album description...",
  "is_premium": false,
  "category": {
    "id": 1,
    "name": "Fiction",
    "description": "Fictional stories"
  },
  "cover_image": {
    "id": 789,
    "url": "/uploads/cover.jpg",
    "alt_text": "Cover description",
    "caption": "Cover caption"
  },
  "author": {
    "id": 123,
    "username": "author_name",
    "display_name": "Author Display Name",
    "avatar_url": "/uploads/avatar.jpg"
  },
  "tags": ["tag1", "tag2"],
  "chapters": [
    {
      "id": 1,
      "chapter_number": 1,
      "chapter_title": "Chapter 1",
      "is_premium": false,
      "created_at": "2024-01-01T00:00:00Z",
      "view_count": 100
    }
  ],
  "related_albums": [...],
  "status": "ongoing",
  "is_completed": false,
  "is_hiatus": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "view_count": 500
}
```

#### Get Album Chapter
```
GET /api/public/albums/{album_id}/chapters/{chapter_id}
```

Returns detailed information about a specific chapter.

**Response for non-premium content:**
```json
{
  "id": 1,
  "chapter_number": 1,
  "chapter_title": "Chapter 1",
  "content": "Chapter content...",
  "is_premium": false,
  "album": {
    "id": 456,
    "title": "Album Title",
    "description": "Album description",
    "cover_image_url": "/uploads/cover.jpg"
  },
  "news_content": {
    "id": 123,
    "title": "News Title",
    "excerpt": "News excerpt...",
    "is_premium": false
  },
  "navigation": {
    "previous": null,
    "next": {
      "id": 2,
      "chapter_number": 2,
      "chapter_title": "Chapter 2"
    }
  },
  "created_at": "2024-01-01T00:00:00Z",
  "view_count": 100
}
```

#### Get Albums List
```
GET /api/public/albums?page=1&per_page=20&category=1&search=query&status=ongoing&sort=latest
```

Returns a paginated list of albums with filtering options.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 20)
- `category` (optional): Category ID filter
- `search` (optional): Search query
- `status` (optional): Status filter - "completed", "ongoing", "hiatus"
- `sort` (optional): Sort order - "latest", "popular", "oldest", "title" (default: "latest")

**Response:**
```json
{
  "albums": [...],
  "pagination": {...},
  "filters": {
    "categories": [...],
    "current_category": 1,
    "current_search": "query",
    "current_status": "ongoing",
    "current_sort": "latest"
  }
}
```

### User Profile API

#### Get User Profile
```
GET /api/public/user/{username}
```

Returns public information about a user profile.

**Response:**
```json
{
  "id": 123,
  "username": "username",
  "display_name": "Display Name",
  "bio": "User bio...",
  "avatar_url": "/uploads/avatar.jpg",
  "join_date": "2024-01-01T00:00:00Z",
  "last_seen": "2024-01-01T12:00:00Z",
  "is_verified": true,
  "is_admin": false,
  "profile": {
    "bio": "User bio...",
    "website": "https://example.com",
    "location": "City, Country",
    "birth_date": "1990-01-01T00:00:00Z",
    "gender": "prefer_not_to_say",
    "interests": "Reading, Writing"
  },
  "stats": {
    "total_views": 1000,
    "total_likes": 150,
    "total_comments": 75,
    "total_shares": 25,
    "achievement_points": 250
  },
  "social": {
    "followers_count": 50,
    "following_count": 30
  },
  "published_albums": [...],
  "recent_news": [...]
}
```

#### Get User Statistics
```
GET /api/public/user/{username}/stats
```

Returns detailed user statistics.

**Response:**
```json
{
  "user": {
    "id": 123,
    "username": "username",
    "display_name": "Display Name"
  },
  "stats": {
    "total_views": 1000,
    "total_likes": 150,
    "total_comments": 75,
    "total_shares": 25,
    "achievement_points": 250,
    "total_albums": 5,
    "total_news": 10,
    "total_chapters": 25
  },
  "achievements": {
    "current_level": "Level 3",
    "points_to_next_level": 50,
    "total_points": 250
  }
}
```

#### Get User Library
```
GET /api/public/user/{username}/library
```

Returns the user's public content library.

**Response:**
```json
{
  "user": {
    "id": 123,
    "username": "username",
    "display_name": "Display Name"
  },
  "library": {
    "albums": [...],
    "news": [...],
    "total_albums": 5,
    "total_news": 10
  }
}
```

### Categories and Tags API

#### Get Categories
```
GET /api/public/categories
```

Returns all active categories with content counts.

**Response:**
```json
{
  "categories": [
    {
      "id": 1,
      "name": "Technology",
      "description": "Tech-related content",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "content_counts": {
        "news": 25,
        "albums": 10,
        "total": 35
      }
    }
  ],
  "total": 1
}
```

#### Get Tags
```
GET /api/public/tags
```

Returns all active tags with usage counts.

**Response:**
```json
{
  "tags": [
    {
      "name": "technology",
      "album_count": 15,
      "news_count": 30,
      "total_count": 45
    }
  ],
  "total": 1
}
```

### Comments API

#### Get Comments
```
GET /api/public/comments/{content_type}/{content_id}?page=1&per_page=20&sort=newest
```

Returns comments for a specific content item.

**Path Parameters:**
- `content_type`: "news", "album", or "chapter"
- `content_id`: ID of the content item

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 20)
- `sort` (optional): Sort order - "newest", "oldest", "most_liked" (default: "newest")

**Response:**
```json
{
  "content": {
    "type": "news",
    "id": 123,
    "title": "News Title"
  },
  "comments": [
    {
      "id": 1,
      "content": "Comment text...",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "like_count": 5,
      "reply_count": 2,
      "is_edited": false,
      "user": {
        "id": 456,
        "username": "commenter",
        "display_name": "Commenter Name",
        "avatar_url": "/uploads/avatar.jpg",
        "is_verified": true
      },
      "parent_comment": {
        "id": 2,
        "content": "Parent comment...",
        "user": {
          "username": "parent_user",
          "display_name": "Parent User"
        }
      }
    }
  ],
  "pagination": {...},
  "filters": {
    "current_sort": "newest"
  }
}
```

### Search API

#### Unified Search
```
GET /api/public/search?q=query&type=all&page=1&per_page=20
```

Performs unified search across all content types.

**Query Parameters:**
- `q` (required): Search query
- `type` (optional): Content type filter - "all", "news", "albums", "users" (default: "all")
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page, max 100 (default: 20)

**Response:**
```json
{
  "query": "search term",
  "content_type": "all",
  "total_results": 45,
  "results": {
    "news": [...],
    "albums": [...],
    "users": [...]
  },
  "pagination": {
    "page": 1,
    "per_page": 20
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful response
- `400 Bad Request`: Invalid parameters or request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a JSON object with an error message:
```json
{
  "error": "Error description"
}
```

## Rate Limiting

Currently, no rate limiting is implemented on these public endpoints. Consider implementing rate limiting for production use.

## Caching

These endpoints are suitable for caching strategies:
- News and album content can be cached for longer periods
- User profiles and comments may need shorter cache times
- Search results can benefit from query-based caching

## Usage Examples

### JavaScript/Fetch API
```javascript
// Get a news article
fetch('/api/public/news/123')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));

// Search for content
fetch('/api/public/search?q=technology&type=news')
  .then(response => response.json())
  .then(data => console.log(data.results.news))
  .catch(error => console.error('Error:', error));
```

### Python/Requests
```python
import requests

# Get user profile
response = requests.get('http://localhost:5000/api/public/user/username')
user_data = response.json()

# Get albums with filters
response = requests.get('http://localhost:5000/api/public/albums', 
                       params={'category': 1, 'status': 'ongoing', 'sort': 'popular'})
albums_data = response.json()
```

### cURL
```bash
# Get news list
curl "http://localhost:5000/api/public/news?page=1&per_page=10"

# Get album details
curl "http://localhost:5000/api/public/albums/456"

# Search for content
curl "http://localhost:5000/api/public/search?q=technology&type=all"
```

## Future Enhancements

Potential improvements for future versions:
- Authentication for premium content access
- Rate limiting and API key management
- WebSocket support for real-time updates
- GraphQL endpoint for flexible queries
- Bulk operations for multiple resources
- Advanced filtering and sorting options
- Analytics and usage tracking endpoints

## Support

For questions or issues with the public API endpoints, please refer to the main project documentation or create an issue in the project repository.