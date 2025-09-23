# User API Reference

A comprehensive reference for all user-related API endpoints in LilyOpenCMS, designed for both external applications and UI compatibility.

## Overview

This document covers two main API sets:
1. **User API** (`/api/user/*`) - Complete JSON APIs for external applications
2. **User Translation API** (`/api/xlate/user/*`) - Translation endpoints for UI compatibility

## Authentication

### Session-Based Authentication (UI)
- Uses Flask-Login sessions
- Required for UI endpoints
- Automatically handled by browser cookies

### Token-Based Authentication (External Apps)
- Uses Bearer tokens from `/api/auth/login`
- Required for external application endpoints
- Include `Authorization: Bearer <token>` header

## User API Endpoints (`/api/user/*`)

### User Management APIs

#### List Users (Admin Only)
```http
GET /api/user/list
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `search` (string): Search term for username, email, first_name, last_name
- `role` (string): Filter by role (GENERAL, ADMIN, SUPERUSER)
- `status` (string): Filter by status (active, inactive, suspended)
- `verification` (string): Filter by verification (verified, unverified)

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "bio": "User bio",
      "role": "GENERAL",
      "custom_role": null,
      "is_active": true,
      "is_premium": false,
      "verified": true,
      "is_suspended": false,
      "write_access": false,
      "created_at": "2024-01-01T00:00:00Z",
      "last_login": "2024-01-15T10:30:00Z",
      "login_count": 25,
      "birthdate": "1990-01-01",
      "age": 34,
      "suspension_reason": null,
      "suspension_until": null,
      "premium_expires_at": null,
      "has_premium_access": false
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "filters": {
    "search": "",
    "role": "",
    "status": "",
    "verification": ""
  }
}
```

#### Get User Details
```http
GET /api/user/{user_id}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "bio": "User bio",
    "role": "GENERAL",
    "custom_role": null,
    "is_active": true,
    "is_premium": false,
    "verified": true,
    "is_suspended": false,
    "write_access": false,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "login_count": 25,
    "birthdate": "1990-01-01",
    "age": 34
  }
}
```

#### Update User
```http
PUT /api/user/{user_id}
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Updated bio",
  "birthdate": "1990-01-01"
}
```

**Admin-Only Fields:**
```json
{
  "email": "newemail@example.com",
  "role": "ADMIN",
  "is_active": true,
  "verified": true,
  "is_premium": false,
  "write_access": true
}
```

#### Delete User (Admin Only)
```http
DELETE /api/user/{user_id}
```

### User Profile APIs

#### Get Current User Profile
```http
GET /api/user/profile
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "bio": "User bio",
    "role": "GENERAL",
    "custom_role": null,
    "is_active": true,
    "is_premium": false,
    "verified": true,
    "is_suspended": false,
    "write_access": false,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z",
    "login_count": 25,
    "birthdate": "1990-01-01",
    "age": 34
  },
  "profile": {
    "pronouns": "he/him",
    "short_bio": "Short bio",
    "location": "Jakarta, Indonesia",
    "website": "https://johndoe.com",
    "social_links": {
      "twitter": "@johndoe",
      "instagram": "@johndoe"
    },
    "show_email": false,
    "show_birthdate": true
  }
}
```

#### Update Profile
```http
PUT /api/user/profile
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Updated bio",
  "birthdate": "1990-01-01",
  "pronouns": "he/him",
  "short_bio": "Updated short bio",
  "location": "Jakarta, Indonesia",
  "website": "https://johndoe.com",
  "social_links": {
    "twitter": "@johndoe",
    "instagram": "@johndoe"
  },
  "show_email": false,
  "show_birthdate": true
}
```

#### Change Username
```http
PATCH /api/user/profile/username
```

**Request Body:**
```json
{
  "username": "new_username",
  "current_password": "current_password"
}
```

#### Change Password
```http
PATCH /api/user/profile/password
```

**Request Body:**
```json
{
  "current_password": "old_password",
  "new_password": "new_password",
  "confirm_password": "new_password"
}
```

### User Content APIs

#### Get User Stories
```http
GET /api/user/content/stories
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `status` (string): Filter by status (all, published, draft)

**Response:**
```json
{
  "success": true,
  "stories": [
    {
      "id": 1,
      "title": "Story Title",
      "content": "Story content...",
      "excerpt": "Story excerpt...",
      "category": {
        "id": 1,
        "name": "Fiction"
      },
      "author": {
        "id": 1,
        "username": "john_doe",
        "full_name": "John Doe"
      },
      "is_premium": false,
      "is_news": false,
      "is_main_news": false,
      "is_visible": true,
      "read_count": 150,
      "share_count": 25,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "image": {
        "id": 1,
        "url": "/static/images/story1.jpg",
        "alt_text": "Story image"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "filters": {
    "status": "all"
  }
}
```

#### Get User Albums
```http
GET /api/user/content/albums
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `status` (string): Filter by status (all, published, draft)

#### Get User Images
```http
GET /api/user/content/images
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `visibility` (string): Filter by visibility (all, visible, hidden)

### User Library APIs

#### Get Library
```http
GET /api/user/library
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `type` (string): Filter by content type (all, news, album)

#### Add to Library
```http
POST /api/user/library
```

**Request Body:**
```json
{
  "content_type": "news",
  "content_id": 123
}
```

#### Remove from Library
```http
DELETE /api/user/library/{item_id}
```

#### Get Reading History
```http
GET /api/user/reading-history
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)
- `type` (string): Filter by content type (all, news, album)

### User Statistics APIs

#### Get User Stats
```http
GET /api/user/stats
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "user_id": 1,
    "total_stories": 25,
    "published_stories": 20,
    "draft_stories": 5,
    "total_albums": 10,
    "published_albums": 8,
    "draft_albums": 2,
    "total_images": 50,
    "library_items": 100,
    "reading_history_items": 200,
    "total_views": 5000,
    "total_likes": 250,
    "total_comments": 150,
    "total_shares": 75,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "recent_activities": [
    {
      "id": 1,
      "activity_type": "story_created",
      "description": "Created new story",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### User Social APIs

#### Follow/Unfollow User
```http
POST /api/user/follow/{user_id}
```

**Response:**
```json
{
  "success": true,
  "action": "followed",
  "follower_count": 150
}
```

#### Get Following List
```http
GET /api/user/following
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)

#### Get Followers List
```http
GET /api/user/followers
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (max: 100, default: 20)

### User Write Access APIs

#### Request Write Access
```http
POST /api/user/write-access/request
```

**Request Body:**
```json
{
  "reason": "I want to create content",
  "portfolio_links": "https://myportfolio.com",
  "experience": "I have experience in writing"
}
```

#### Get Write Access Status
```http
GET /api/user/write-access/status
```

**Response:**
```json
{
  "success": true,
  "has_write_access": false,
  "pending_request": {
    "id": 1,
    "request_reason": "I want to create content",
    "requested_at": "2024-01-15T10:30:00Z"
  }
}
```

### User Account Management APIs

#### Request Account Deletion
```http
POST /api/user/account/delete
```

**Request Body:**
```json
{
  "password": "current_password"
}
```

## User Translation API Endpoints (`/api/xlate/user/*`)

These endpoints provide the same functionality as the User API but with simplified responses for UI compatibility.

### Profile Translation Endpoints

#### Get Profile (UI Compatible)
```http
GET /api/xlate/user/profile
```

#### Update Profile (UI Compatible)
```http
PUT /api/xlate/user/profile
```

### Stats Translation Endpoints

#### Get Stats (UI Compatible)
```http
GET /api/xlate/user/stats
```

### Content Translation Endpoints

#### Get Stories (UI Compatible)
```http
GET /api/xlate/user/content/stories
```

#### Get Albums (UI Compatible)
```http
GET /api/xlate/user/content/albums
```

#### Get Images (UI Compatible)
```http
GET /api/xlate/user/content/images
```

### Library Translation Endpoints

#### Get Library (UI Compatible)
```http
GET /api/xlate/user/library
```

#### Get Reading History (UI Compatible)
```http
GET /api/xlate/user/reading-history
```

### Social Translation Endpoints

#### Get Following (UI Compatible)
```http
GET /api/xlate/user/following
```

#### Get Followers (UI Compatible)
```http
GET /api/xlate/user/followers
```

#### Get Write Access Status (UI Compatible)
```http
GET /api/xlate/user/write-access/status
```

### Admin Translation Endpoints

#### Get Users List (Admin UI Compatible)
```http
GET /api/xlate/user/admin/list
```

#### Get Admin Stats (Admin UI Compatible)
```http
GET /api/xlate/user/admin/stats
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error message",
  "success": false
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict
- `500` - Internal Server Error

## Usage Examples

### External Application (Token Authentication)

```javascript
// Login to get token
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'john_doe',
    password: 'password123'
  })
});

const { access_token } = await loginResponse.json();

// Use token for API calls
const profileResponse = await fetch('/api/user/profile', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});

const profile = await profileResponse.json();
```

### UI Application (Session Authentication)

```javascript
// Session-based authentication (automatic with cookies)
const profileResponse = await fetch('/api/xlate/user/profile');
const profile = await profileResponse.json();
```

## Migration Guide

### For Existing UI Code

Replace existing user API calls with translation endpoints:

**Before:**
```javascript
fetch('/api/users/profile')
```

**After:**
```javascript
fetch('/api/xlate/user/profile')
```

### For New External Applications

Use the comprehensive User API endpoints:

```javascript
// Get user profile
fetch('/api/user/profile')

// Get user stories
fetch('/api/user/content/stories')

// Get user library
fetch('/api/user/library')
```

## Notes

1. **Pagination**: All list endpoints support pagination with consistent parameters
2. **Filtering**: Most endpoints support filtering with query parameters
3. **Permissions**: Admin-only endpoints require admin-tier user roles
4. **Rate Limiting**: Consider implementing rate limiting for production use
5. **Caching**: Responses can be cached for better performance
6. **Versioning**: API versioning can be added by prefixing endpoints with `/v1/`

This comprehensive API system provides everything needed for external applications while maintaining full compatibility with existing UI components.
