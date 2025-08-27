# Weighted Rating System for Albums

## Overview

The weighted rating system calculates album ratings based on the individual ratings of their chapters, with popularity-based weighting to give more importance to chapters that are more widely read.

## Algorithm

### Weighted Rating Formula

```
Weighted Rating = Σ(Chapter Rating × Chapter Weight) / Σ(Chapter Weights)
```

### Chapter Weight Calculation

```
Chapter Weight = 1 + (chapter_read_count / max_read_count_in_album) × 0.5
```

This means:
- All chapters start with a base weight of 1.0
- The most popular chapter gets a weight of 1.5 (50% bonus)
- Less popular chapters get proportional weights between 1.0 and 1.5

## Implementation Details

### Album Model Methods

#### `get_chapter_ratings()`
Returns all chapter ratings for an album with their calculated weights.

**Returns:**
```python
[
    {
        'chapter_number': 1,
        'chapter_title': 'Chapter 1',
        'news_id': 123,
        'rating': 4.5,
        'rating_count': 10,
        'read_count': 100,
        'weight': 1.25
    },
    # ... more chapters
]
```

#### `calculate_weighted_rating()`
Calculates the weighted average rating for the album.

**Returns:** `float` - The weighted average rating (0.0 if no ratings)

#### `get_weighted_rating_stats()`
Returns comprehensive statistics including weighted average, chapter breakdown, and rating distribution.

**Returns:**
```python
{
    'weighted_average': 4.2,
    'total_chapters_rated': 3,
    'total_ratings': 25,
    'chapter_breakdown': [...],
    'rating_distribution': {1: 2, 2: 3, 3: 5, 4: 8, 5: 7}
}
```

### API Endpoints

#### GET `/api/ratings/album/{album_id}/weighted`
Returns detailed weighted rating statistics for an album.

**Response:**
```json
{
    "album_id": 123,
    "album_title": "My Album",
    "weighted_average": 4.2,
    "total_ratings": 25,
    "total_chapters_rated": 3,
    "rating_distribution": {...},
    "chapter_breakdown": [...],
    "user_rating": 5,
    "algorithm_info": {
        "description": "Weighted rating based on chapter popularity",
        "formula": "Weighted Rating = Σ(Chapter Rating × Chapter Weight) / Σ(Chapter Weights)",
        "weight_calculation": "Chapter Weight = 1 + (chapter_read_count / max_read_count_in_album) * 0.5"
    }
}
```

### Frontend Integration

The rating system JavaScript automatically uses weighted ratings for albums:

```javascript
// For albums, uses weighted endpoint
if (this.contentType === 'album') {
    url = `/api/ratings/album/${this.contentId}/weighted`;
}
```

Chapter breakdown is displayed showing:
- Chapter number and title
- Individual chapter rating
- Weight multiplier
- Popularity percentage

## Example Calculation

Consider an album with 2 chapters:

**Chapter 1:**
- Rating: 3.0 stars
- Read count: 50
- Weight: 1 + (50/100) × 0.5 = 1.25

**Chapter 2:**
- Rating: 5.0 stars  
- Read count: 100 (maximum)
- Weight: 1 + (100/100) × 0.5 = 1.5

**Weighted Average:**
```
(3.0 × 1.25 + 5.0 × 1.5) / (1.25 + 1.5) = 4.09
```

## Benefits

1. **Popularity-Based**: More popular chapters have greater influence
2. **Fair Representation**: Reflects actual user engagement
3. **Transparent**: Clear formula and weight calculation
4. **Backward Compatible**: Existing direct album ratings still work
5. **Detailed Analytics**: Shows chapter-by-chapter breakdown

## Testing

Run the test suite to verify the weighted rating system:

```bash
python -m pytest test/test_weighted_rating_system.py -v
```

## Analytics Integration

The rating analytics dashboard now includes:
- Weighted album average
- Number of albums with weighted ratings
- Detailed breakdown of weighted album statistics
- Comparison between regular and weighted averages

## Future Enhancements

Potential improvements to consider:
- Time-based weighting (newer chapters get more weight)
- Chapter order weighting (later chapters get more weight)
- User engagement weighting (comments, shares, etc.)
- Configurable weight multipliers
- Caching for performance optimization 