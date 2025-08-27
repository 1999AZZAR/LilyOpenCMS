# Album View Count Implementation

## Overview

This document describes the implementation of the album view counting mechanism in the LilyOpenCMS system. The view count tracks how many times an album detail page has been visited, separate from the read count which tracks actual chapter reads.

## Implementation Details

### 1. Database Schema

The `album` table already includes a `total_views` column:
```sql
total_views INTEGER DEFAULT 0 NOT NULL
```

### 2. Model Changes

#### Album Model (`models.py`)

Added the `increment_views()` method to the Album model:

```python
def increment_views(self):
    """Increment the view count for this album."""
    self.total_views += 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Error incrementing view count for album {self.id}: {e}")
        db.session.rollback()
```

Updated the `to_dict()` method to include `total_views` and `average_rating`:
```python
def to_dict(self):
    return {
        # ... existing fields ...
        "total_views": self.total_views,
        "average_rating": self.average_rating,
        # ... rest of fields ...
    }
```

### 3. Route Changes

#### Album Detail Route (`routes/routes_public.py`)

Updated the `album_detail()` function to increment view count when the page is accessed:

```python
@main_blueprint.route("/album/<int:album_id>/<path:album_title>")
@monitor_ssr_render("album_detail")
def album_detail(album_id, album_title):
    album = Album.query.get_or_404(album_id)
    
    # Check if album is visible
    if not album.is_visible or album.is_archived:
        abort(404)
    
    # Increment view count for this album
    try:
        album.increment_views()
    except Exception as e:
        current_app.logger.error(f"Failed to increment view count for album ID {album_id}: {e}")
    
    # ... rest of the function ...
```

### 4. Template Updates

#### Album Detail Template (`templates/public/album_detail.html`)

Added view count display in the hero section:
```html
<span class="flex items-center">
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 mr-2">
    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
  {{ album.total_views }} dilihat
</span>
```

#### Admin Templates

Updated admin templates to display view counts:
- `templates/admin/albums/list.html` - Added view count in album list
- `templates/admin/albums/detail.html` - Added view count in album stats

#### Public Templates

Updated public templates to show view counts:
- `templates/public/index.html` - Added view count in featured albums
- `templates/public/index_albums.html` - Added view count in album cards

### 5. JavaScript Updates

Updated JavaScript files to include view counts in dynamic content:
- `static/js/albums-search.js` - Added view count in search results
- `static/js/albums-management.js` - Added view count in admin interface

## How It Works

1. **View Count Increment**: When a user visits an album detail page (`/album/<id>/<title>`), the `increment_views()` method is called automatically.

2. **Database Update**: The view count is incremented by 1 and immediately committed to the database.

3. **Display**: The view count is displayed alongside other album statistics (chapters, reads, etc.) in various templates.

4. **API Integration**: The view count is included in the album's `to_dict()` method, making it available in API responses.

## Testing

A test script is available at `test/test_album_view_count.py` that verifies:
- View count increments correctly
- Multiple increments work properly
- The `to_dict()` method includes view counts
- Database persistence works correctly

Run the test with:
```bash
python test/test_album_view_count.py
```

## Analytics Integration

The view count is used in various analytics dashboards:
- Album analytics dashboard shows total views across all albums
- Individual album stats include view counts
- Performance metrics can compare views vs reads

## Future Enhancements

Potential improvements for the view counting system:
1. **Rate Limiting**: Prevent rapid-fire view count increments from the same user
2. **Session Tracking**: Track unique views vs total page loads
3. **Time-based Analytics**: Track views over time periods
4. **Geographic Tracking**: Track views by location (if needed)

## Notes

- View counts are incremented on every page load (no rate limiting currently)
- View counts are separate from read counts (which track actual chapter reads)
- The system is designed to be lightweight and not impact page load performance
- Error handling ensures that view count failures don't break the page display
