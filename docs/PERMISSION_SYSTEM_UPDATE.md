# Permission System Update for News and Albums CRUD Operations

## Overview

The permission system has been updated to allow users with appropriate permissions to perform CRUD (Create, Read, Update, Delete) operations on news articles and albums, rather than restricting access to admin-tier users only.

## New Permission Functions

### News Permissions
- `can_create_news(user)` - Check if user can create news articles
- `can_edit_news(user)` - Check if user can edit news articles
- `can_delete_news(user)` - Check if user can delete news articles
- `can_publish_news(user)` - Check if user can publish/unpublish news articles
- `can_manage_news(user)` - Check if user can perform any news management operation

### Album Permissions
- `can_create_albums(user)` - Check if user can create albums
- `can_edit_albums(user)` - Check if user can edit albums
- `can_delete_albums(user)` - Check if user can delete albums
- `can_publish_albums(user)` - Check if user can publish/unpublish albums
- `can_manage_albums(user)` - Check if user can perform any album management operation

### General Content Permissions
- `can_access_content_creation(user)` - Check if user can create any type of content

## New Permission Decorators

### Route Decorators (for page routes)
- `@require_news_create` - Require permission to create news articles
- `@require_news_edit` - Require permission to edit news articles
- `@require_news_delete` - Require permission to delete news articles
- `@require_news_publish` - Require permission to publish/unpublish news articles
- `@require_news_manage` - Require permission to manage news (any CRUD operation)

- `@require_album_create` - Require permission to create albums
- `@require_album_edit` - Require permission to edit albums
- `@require_album_delete` - Require permission to delete albums
- `@require_album_publish` - Require permission to publish/unpublish albums
- `@require_album_manage` - Require permission to manage albums (any CRUD operation)

- `@require_content_creation` - Require permission to create any type of content

### API Decorators (for API endpoints)
- `@require_api_news_create` - API decorator for news creation
- `@require_api_news_edit` - API decorator for news editing
- `@require_api_news_delete` - API decorator for news deletion

- `@require_api_album_create` - API decorator for album creation
- `@require_api_album_edit` - API decorator for album editing
- `@require_api_album_delete` - API decorator for album deletion

## Usage Examples

### In Routes
```python
from routes.utils.permission_decorators import require_news_create, require_album_edit

@main_blueprint.route("/create-news")
@login_required
@require_news_create
def create_news_page():
    """Page for creating news articles."""
    return render_template('create_news.html')

@albums_bp.route('/<int:album_id>/edit')
@login_required
@require_album_edit
def edit_album(album_id):
    """Edit an existing album."""
    # ... implementation
```

### In API Endpoints
```python
from routes.utils.permission_decorators import require_api_news_create

@main_blueprint.route("/api/news", methods=["POST"])
@login_required
@require_api_news_create
def create_news_api():
    """API endpoint to create a new news article."""
    # ... implementation
```

### In Templates
```html
{% if can_create_news() %}
    <a href="{{ url_for('main.create_news') }}" class="btn btn-primary">
        Create News Article
    </a>
{% endif %}

{% if can_edit_albums() %}
    <a href="{{ url_for('albums.edit_album', album_id=album.id) }}" class="btn btn-secondary">
        Edit Album
    </a>
{% endif %}

{% if can_delete_news() %}
    <button onclick="deleteNews({{ news.id }})" class="btn btn-danger">
        Delete News
    </button>
{% endif %}
```

## Permission Hierarchy

### Built-in Roles
1. **Superuser (SU)**: Has all permissions
2. **Admin**: Has all permissions except superuser-specific operations
3. **General**: No permissions by default

### Custom Roles
- **Writer**: Can create news and albums (read + create permissions)
- **Editor**: Can create and edit news and albums (read + create + update permissions)
- **Subadmin**: Has elevated permissions below Admin level

## Updated Routes

### News Routes
- `create_news_api()` now uses `@require_api_news_create` instead of just checking `current_user.verified`

### Album Routes
- `create_album()` now uses `@require_album_create` instead of `@creator_required`
- `edit_album()` now uses `@require_album_edit` instead of `@admin_required`
- Updated `admin_required` and `creator_required` decorators to use permission system

## Benefits

1. **Granular Control**: Users can have specific permissions without needing admin privileges
2. **Role-Based Access**: Custom roles can be assigned specific permissions
3. **Security**: Proper permission checking prevents unauthorized access
4. **Flexibility**: Easy to add new permissions and roles as needed
5. **User Experience**: Users with appropriate permissions can access features they need

## Testing

A test script has been created at `test/test_permissions.py` that verifies:
- General users have no permissions
- Writer users have create permissions
- Editor users have create and edit permissions
- Admin and Superuser have all permissions

Run the test with:
```bash
python test/test_permissions.py
```

## Migration Notes

- Existing admin-tier users will continue to have access to all features
- General users will need to be assigned appropriate custom roles to access CRUD operations
- The permission system is backward compatible with existing role assignments
