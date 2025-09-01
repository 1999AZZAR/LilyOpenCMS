# Achievement System Guide

## Overview

The achievement system is a comprehensive gamification feature that tracks user activities and awards achievements based on various milestones and streaks. It includes:

- **Login Streaks**: Daily login consistency
- **Activity Streaks**: Daily activity engagement
- **Reading Streaks**: Content consumption consistency
- **Contributions**: Content creation (news, albums, images)
- **Exploration**: Content engagement (comments, ratings, reading)
- **Community**: Social interactions (likes, comments)
- **Milestones**: Level progression and point accumulation

## Database Models

### Core Models

1. **AchievementCategory**: Organizes achievements into categories
2. **Achievement**: Defines individual achievements with criteria
3. **UserAchievement**: Tracks user progress on achievements
4. **AchievementProgress**: Detailed progress history
5. **UserStreak**: Tracks various user streaks
6. **UserPoints**: Manages user points and levels
7. **PointTransaction**: Records point earning/spending

### Achievement Types

- **Streak**: Based on consecutive days of activity
- **Count**: Based on total number of actions
- **Milestone**: Special one-time achievements
- **Special**: Custom achievements

### Criteria Types

- `login_streak`: Daily login consistency
- `activity_streak`: Daily activity engagement
- `reading_streak`: Daily content reading
- `news_articles`: Number of published articles
- `albums_created`: Number of created albums
- `images_uploaded`: Number of uploaded images
- `comments_made`: Number of comments posted
- `ratings_given`: Number of ratings given
- `articles_read`: Number of articles read
- `albums_read`: Number of albums read
- `comment_likes_given`: Number of comment likes given
- `comment_likes_received`: Number of likes received on comments
- `user_level`: User's current level
- `total_points`: Total points earned

## Setup Instructions

### 1. Create Database Tables

Run the database migration to create the achievement tables:

```bash
python -c "from models import create_all_tables; create_all_tables()"
```

### 2. Initialize Achievement System

Run the initialization script to create default categories and achievements:

```bash
python helper/init_achievement_system.py
```

This will create:
- 7 achievement categories
- 40+ default achievements
- Proper categorization and point rewards

### 3. Add Indexes

Create database indexes for optimal performance:

```bash
python -c "from models import add_missing_indexes; add_missing_indexes()"
```

## Integration Guide

### 1. Import Achievement Tracker

```python
from helper.achievement_tracker import AchievementTracker
```

### 2. Track User Activities

#### Login Tracking

```python
# In your login route
@app.route('/login', methods=['POST'])
def login():
    # After successful login
    user_id = current_user.id
    result = AchievementTracker.track_login(
        user_id, 
        request.remote_addr, 
        request.user_agent.string
    )
    
    if result and result["completed_achievements"]:
        # Show achievement notifications
        for achievement_data in result["completed_achievements"]:
            achievement = achievement_data["achievement"]
            flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")
```

#### Content Reading

```python
# In your news/album view route
@app.route('/news/<int:news_id>')
def view_news(news_id):
    # After user views the content
    if current_user.is_authenticated:
        result = AchievementTracker.track_reading(
            current_user.id, 
            "news", 
            news_id
        )
        
        if result and result["completed_achievements"]:
            # Show achievement notifications
            for achievement_data in result["completed_achievements"]:
                achievement = achievement_data["achievement"]
                flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")
```

#### Content Creation

```python
# In your news creation route
@app.route('/news/create', methods=['POST'])
def create_news():
    # After successfully creating news
    news = News(...)
    db.session.add(news)
    db.session.commit()
    
    result = AchievementTracker.track_news_creation(
        current_user.id, 
        news.id
    )
    
    if result and result["completed_achievements"]:
        # Show achievement notifications
        for achievement_data in result["completed_achievements"]:
            achievement = achievement_data["achievement"]
            flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")
```

#### Comments and Ratings

```python
# In your comment creation route
@app.route('/comment/create', methods=['POST'])
def create_comment():
    # After creating comment
    comment = Comment(...)
    db.session.add(comment)
    db.session.commit()
    
    result = AchievementTracker.track_comment_creation(
        current_user.id, 
        comment.id
    )
    
    if result and result["completed_achievements"]:
        # Show achievement notifications
        for achievement_data in result["completed_achievements"]:
            achievement = achievement_data["achievement"]
            flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")

# In your rating creation route
@app.route('/rating/create', methods=['POST'])
def create_rating():
    # After creating rating
    rating = Rating(...)
    db.session.add(rating)
    db.session.commit()
    
    result = AchievementTracker.track_rating_creation(
        current_user.id, 
        rating.id
    )
    
    if result and result["completed_achievements"]:
        # Show achievement notifications
        for achievement_data in result["completed_achievements"]:
            achievement = achievement_data["achievement"]
            flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")
```

#### Comment Likes

```python
# In your comment like route
@app.route('/comment/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    # After liking comment
    like = CommentLike(...)
    db.session.add(like)
    db.session.commit()
    
    # Track like given
    result_given = AchievementTracker.track_comment_like(
        current_user.id, 
        comment_id, 
        is_like=True
    )
    
    # Track like received by comment author
    result_received = AchievementTracker.track_comment_like_received(comment_id)
    
    # Show achievement notifications
    for result in [result_given, result_received]:
        if result and result["completed_achievements"]:
            for achievement_data in result["completed_achievements"]:
                achievement = achievement_data["achievement"]
                flash(f"🎉 Achievement unlocked: {achievement.name}!", "success")
```

### 3. Display User Achievements

#### Get User Achievement Summary

```python
@app.route('/profile/achievements')
def user_achievements():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    summary = AchievementTracker.get_user_achievements_summary(current_user.id)
    
    return render_template('achievements.html', summary=summary)
```

#### Achievement Summary Data Structure

```python
{
    "total_achievements": 40,
    "completed_achievements": 15,
    "completion_rate": 37.5,
    "total_points": 1250,
    "current_level": 8,
    "streaks": {
        "login": {...},
        "activity": {...},
        "reading": {...}
    },
    "points": {
        "total_points": 1250,
        "current_level": 8,
        "level_progress": 75.5
    },
    "recent_achievements": [...],
    "in_progress_achievements": [...]
}
```

## Achievement Categories

### 1. Login Streaks
- **First Steps**: Login for the first time (10 points)
- **Week Warrior**: 7-day login streak (50 points)
- **Fortnight Fighter**: 14-day login streak (100 points)
- **Monthly Master**: 30-day login streak (200 points)
- **Century Club**: 100-day login streak (500 points)

### 2. Activity Streaks
- **Active Beginner**: 3-day activity streak (25 points)
- **Active Explorer**: 7-day activity streak (75 points)
- **Active Enthusiast**: 21-day activity streak (150 points)
- **Active Master**: 60-day activity streak (300 points)

### 3. Reading Streaks
- **First Reader**: 3-day reading streak (30 points)
- **Dedicated Reader**: 7-day reading streak (80 points)
- **Bookworm**: 30-day reading streak (200 points)
- **Literary Legend**: 100-day reading streak (500 points)

### 4. Contributions
- **First Article**: Publish first article (100 points)
- **Article Writer**: Publish 5 articles (250 points)
- **Content Creator**: Publish 25 articles (500 points)
- **First Album**: Create first album (150 points)
- **Album Creator**: Create 3 albums (300 points)
- **Image Uploader**: Upload 10 images (100 points)
- **Media Master**: Upload 50 images (250 points)

### 5. Exploration
- **First Comment**: Leave first comment (20 points)
- **Commenter**: Leave 10 comments (100 points)
- **First Rating**: Rate first content (15 points)
- **Critic**: Rate 25 pieces of content (150 points)
- **Content Explorer**: Read 50 articles (200 points)
- **Book Explorer**: Read 10 albums (300 points)

### 6. Community
- **First Like**: Like first comment (10 points)
- **Supportive**: Like 20 comments (100 points)
- **Popular Comment**: Receive 5 likes on comment (50 points)
- **Viral Comment**: Receive 25 likes on comment (200 points)

### 7. Milestones
- **Level 5**: Reach level 5 (100 points)
- **Level 10**: Reach level 10 (250 points)
- **Level 25**: Reach level 25 (500 points)
- **Level 50**: Reach level 50 (1000 points)
- **1000 Points**: Earn 1000 total points (100 points)
- **5000 Points**: Earn 5000 total points (500 points)

## Points and Leveling System

### Level Progression
- Level 1: 0-99 points
- Level 2: 100-199 points
- Level 3: 200-299 points
- And so on...

### Point Rewards
- Common achievements: 10-100 points
- Rare achievements: 100-250 points
- Epic achievements: 200-500 points
- Legendary achievements: 500-1000 points

## Maintenance

### Cleanup Old Data

Run periodic cleanup to maintain database performance:

```python
# Run monthly or quarterly
result = AchievementTracker.cleanup_old_activity_data()
print(f"Cleaned up {result['old_activities_removed']} old activities")
```

### Database Health Check

```python
from models import check_database_health
check_database_health()
```

### Optimize Database

```python
from models import optimize_database
optimize_database()
```

## Customization

### Adding New Achievement Categories

```python
# In helper/init_achievement_system.py
def create_custom_category():
    category = AchievementCategory(
        name="Custom Category",
        description="Custom achievements",
        icon_class="fas fa-star",
        color="#ff6b6b",
        display_order=8
    )
    db.session.add(category)
    db.session.commit()
```

### Adding New Achievements

```python
# In helper/init_achievement_system.py
def create_custom_achievements(categories):
    custom_category = categories["Custom Category"]
    
    achievement = Achievement(
        name="Custom Achievement",
        description="Custom achievement description",
        achievement_type="milestone",
        criteria_type="custom_criteria",
        criteria_value=1,
        criteria_operator=">=",
        points_reward=50,
        rarity="rare",
        category_id=custom_category.id
    )
    db.session.add(achievement)
    db.session.commit()
```

### Custom Criteria Types

To add new criteria types, you'll need to:

1. Add the criteria type to the achievement creation
2. Implement tracking logic in `AchievementTracker`
3. Update the achievement checking logic

## Best Practices

### 1. Performance
- Use database indexes for optimal query performance
- Clean up old data regularly
- Batch achievement checks when possible

### 2. User Experience
- Show achievement notifications immediately
- Provide progress indicators for in-progress achievements
- Display achievement summaries in user profiles

### 3. Data Integrity
- Always use transactions for achievement updates
- Validate achievement criteria before awarding
- Handle edge cases (e.g., duplicate achievements)

### 4. Monitoring
- Track achievement completion rates
- Monitor system performance
- Log achievement-related errors

## Troubleshooting

### Common Issues

1. **Achievements not being awarded**
   - Check if user is authenticated
   - Verify achievement criteria are met
   - Check database transaction status

2. **Performance issues**
   - Run database optimization
   - Clean up old data
   - Check database indexes

3. **Duplicate achievements**
   - Check unique constraints
   - Verify achievement checking logic
   - Review transaction handling

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## API Reference

### AchievementManager

- `get_or_create_user_achievement(user_id, achievement_id)`
- `get_or_create_user_streak(user_id, streak_type)`
- `get_or_create_user_points(user_id)`
- `check_achievements(user_id, criteria_type, current_value, source, context_data)`
- `update_streak(user_id, streak_type, activity_date)`
- `get_user_achievements_summary(user_id)`

### AchievementTracker

- `track_login(user_id, ip_address, user_agent)`
- `track_activity(user_id, activity_type, description, context_data)`
- `track_reading(user_id, content_type, content_id)`
- `track_news_creation(user_id, news_id)`
- `track_album_creation(user_id, album_id)`
- `track_image_upload(user_id, image_id)`
- `track_comment_creation(user_id, comment_id)`
- `track_rating_creation(user_id, rating_id)`
- `track_comment_like(user_id, comment_id, is_like)`
- `track_comment_like_received(comment_id)`
- `update_user_level_achievements(user_id)`
- `get_user_achievements_summary(user_id)`
- `cleanup_old_activity_data()`

## Conclusion

The achievement system provides a comprehensive gamification framework that can significantly enhance user engagement. By tracking various user activities and awarding achievements, you can encourage desired behaviors and create a more engaging user experience.

Remember to:
- Integrate tracking calls in your routes
- Display achievement progress to users
- Maintain the system regularly
- Monitor performance and user engagement

For additional support or customization, refer to the source code in `models.py` and the helper scripts in the `helper/` directory.
