#!/usr/bin/env python3
"""
Achievement Tracker Helper

This script provides functions to track user activities and automatically update achievements.
Use these functions in your routes to track user actions and award achievements.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db
from models import (
    User, UserActivity, ReadingHistory, News, Album, Comment, Rating, 
    CommentLike, Image, AchievementManager, UserStreak, UserPoints
)
from datetime import datetime, timezone, timedelta
from sqlalchemy import func


class AchievementTracker:
    """Class for tracking user activities and updating achievements."""
    
    @staticmethod
    def track_login(user_id, ip_address=None, user_agent=None):
        """Track user login and update login streak achievements."""
        with app.app_context():
            try:
                # Update login streak
                login_streak = AchievementManager.update_streak(user_id, "login")
                
                # Get current login streak count
                current_streak = login_streak.current_streak
                
                # Check login streak achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "login_streak", current_streak, "login"
                )
                
                # Record activity
                user = User.query.get(user_id)
                if user:
                    user.record_activity("login", "User logged in", ip_address, user_agent)
                    user.update_login_info(ip_address, user_agent)
                
                db.session.commit()
                
                return {
                    "login_streak": login_streak.to_dict(),
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking login: {e}")
                return None
    
    @staticmethod
    def track_activity(user_id, activity_type, description=None, context_data=None):
        """Track general user activity and update activity streak achievements."""
        with app.app_context():
            try:
                # Update activity streak
                activity_streak = AchievementManager.update_streak(user_id, "activity")
                
                # Get current activity streak count
                current_streak = activity_streak.current_streak
                
                # Check activity streak achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "activity_streak", current_streak, activity_type, context_data
                )
                
                # Record activity
                user = User.query.get(user_id)
                if user:
                    user.record_activity(activity_type, description)
                
                db.session.commit()
                
                return {
                    "activity_streak": activity_streak.to_dict(),
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking activity: {e}")
                return None
    
    @staticmethod
    def track_reading(user_id, content_type, content_id):
        """Track content reading and update reading streak achievements."""
        with app.app_context():
            try:
                # Update reading history
                reading_history = ReadingHistory.query.filter_by(
                    user_id=user_id,
                    content_type=content_type,
                    content_id=content_id
                ).first()
                
                if reading_history:
                    reading_history.read_count += 1
                    reading_history.last_read_at = datetime.now(timezone.utc)
                else:
                    reading_history = ReadingHistory(
                        user_id=user_id,
                        content_type=content_type,
                        content_id=content_id
                    )
                    db.session.add(reading_history)
                
                # Update reading streak
                reading_streak = AchievementManager.update_streak(user_id, "reading")
                current_streak = reading_streak.current_streak
                
                # Check reading streak achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "reading_streak", current_streak, "reading", 
                    {"content_type": content_type, "content_id": content_id}
                )
                
                # Check articles/albums read achievements
                if content_type == "news":
                    articles_read = ReadingHistory.query.filter_by(
                        user_id=user_id, content_type="news"
                    ).count()
                    
                    articles_achievements = AchievementManager.check_achievements(
                        user_id, "articles_read", articles_read, "reading",
                        {"content_type": content_type, "content_id": content_id}
                    )
                    completed_achievements.extend(articles_achievements)
                
                elif content_type == "album":
                    albums_read = ReadingHistory.query.filter_by(
                        user_id=user_id, content_type="album"
                    ).count()
                    
                    albums_achievements = AchievementManager.check_achievements(
                        user_id, "albums_read", albums_read, "reading",
                        {"content_type": content_type, "content_id": content_id}
                    )
                    completed_achievements.extend(albums_achievements)
                
                db.session.commit()
                
                return {
                    "reading_streak": reading_streak.to_dict(),
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking reading: {e}")
                return None
    
    @staticmethod
    def track_news_creation(user_id, news_id):
        """Track news article creation and update contribution achievements."""
        with app.app_context():
            try:
                # Count user's news articles
                news_count = News.query.filter_by(user_id=user_id).count()
                
                # Check news creation achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "news_articles", news_count, "news_creation",
                    {"news_id": news_id}
                )
                
                # Track activity
                AchievementTracker.track_activity(
                    user_id, "news_creation", f"Created news article #{news_id}"
                )
                
                db.session.commit()
                
                return {
                    "news_count": news_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking news creation: {e}")
                return None
    
    @staticmethod
    def track_album_creation(user_id, album_id):
        """Track album creation and update contribution achievements."""
        with app.app_context():
            try:
                # Count user's albums
                album_count = Album.query.filter_by(user_id=user_id).count()
                
                # Check album creation achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "albums_created", album_count, "album_creation",
                    {"album_id": album_id}
                )
                
                # Track activity
                AchievementTracker.track_activity(
                    user_id, "album_creation", f"Created album #{album_id}"
                )
                
                db.session.commit()
                
                return {
                    "album_count": album_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking album creation: {e}")
                return None
    
    @staticmethod
    def track_image_upload(user_id, image_id):
        """Track image upload and update contribution achievements."""
        with app.app_context():
            try:
                # Count user's images
                image_count = Image.query.filter_by(user_id=user_id).count()
                
                # Check image upload achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "images_uploaded", image_count, "image_upload",
                    {"image_id": image_id}
                )
                
                # Track activity
                AchievementTracker.track_activity(
                    user_id, "image_upload", f"Uploaded image #{image_id}"
                )
                
                db.session.commit()
                
                return {
                    "image_count": image_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking image upload: {e}")
                return None
    
    @staticmethod
    def track_comment_creation(user_id, comment_id):
        """Track comment creation and update exploration achievements."""
        with app.app_context():
            try:
                # Count user's comments
                comment_count = Comment.query.filter_by(user_id=user_id).count()
                
                # Check comment creation achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "comments_made", comment_count, "comment_creation",
                    {"comment_id": comment_id}
                )
                
                # Track activity
                AchievementTracker.track_activity(
                    user_id, "comment_creation", f"Created comment #{comment_id}"
                )
                
                db.session.commit()
                
                return {
                    "comment_count": comment_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking comment creation: {e}")
                return None
    
    @staticmethod
    def track_rating_creation(user_id, rating_id):
        """Track rating creation and update exploration achievements."""
        with app.app_context():
            try:
                # Count user's ratings
                rating_count = Rating.query.filter_by(user_id=user_id).count()
                
                # Check rating creation achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "ratings_given", rating_count, "rating_creation",
                    {"rating_id": rating_id}
                )
                
                # Track activity
                AchievementTracker.track_activity(
                    user_id, "rating_creation", f"Created rating #{rating_id}"
                )
                
                db.session.commit()
                
                return {
                    "rating_count": rating_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking rating creation: {e}")
                return None
    
    @staticmethod
    def track_comment_like(user_id, comment_id, is_like=True):
        """Track comment like/dislike and update community achievements."""
        with app.app_context():
            try:
                if is_like:
                    # Count user's given likes
                    like_count = CommentLike.query.filter_by(
                        user_id=user_id, is_like=True, is_deleted=False
                    ).count()
                    
                    # Check like achievements
                    completed_achievements = AchievementManager.check_achievements(
                        user_id, "comment_likes_given", like_count, "comment_like",
                        {"comment_id": comment_id}
                    )
                    
                    # Track activity
                    AchievementTracker.track_activity(
                        user_id, "comment_like", f"Liked comment #{comment_id}"
                    )
                else:
                    # Count user's given dislikes
                    dislike_count = CommentLike.query.filter_by(
                        user_id=user_id, is_like=False, is_deleted=False
                    ).count()
                    
                    completed_achievements = []
                    
                    # Track activity
                    AchievementTracker.track_activity(
                        user_id, "comment_dislike", f"Disliked comment #{comment_id}"
                    )
                
                db.session.commit()
                
                return {
                    "like_count": like_count if is_like else dislike_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking comment like: {e}")
                return None
    
    @staticmethod
    def track_comment_like_received(comment_id):
        """Track when a comment receives likes and update community achievements."""
        with app.app_context():
            try:
                # Get comment and its author
                comment = Comment.query.get(comment_id)
                if not comment:
                    return None
                
                # Count likes received on this comment
                like_count = CommentLike.query.filter_by(
                    comment_id=comment_id, is_like=True, is_deleted=False
                ).count()
                
                # Check like received achievements for comment author
                completed_achievements = AchievementManager.check_achievements(
                    comment.user_id, "comment_likes_received", like_count, "comment_like_received",
                    {"comment_id": comment_id}
                )
                
                db.session.commit()
                
                return {
                    "comment_author_id": comment.user_id,
                    "like_count": like_count,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error tracking comment like received: {e}")
                return None
    
    @staticmethod
    def update_user_level_achievements(user_id):
        """Update user level achievements based on current points."""
        with app.app_context():
            try:
                user_points = UserPoints.query.filter_by(user_id=user_id).first()
                if not user_points:
                    return None
                
                # Check level achievements
                completed_achievements = AchievementManager.check_achievements(
                    user_id, "user_level", user_points.current_level, "level_up"
                )
                
                # Check total points achievements
                points_achievements = AchievementManager.check_achievements(
                    user_id, "total_points", user_points.total_points, "points_earned"
                )
                
                completed_achievements.extend(points_achievements)
                
                db.session.commit()
                
                return {
                    "current_level": user_points.current_level,
                    "total_points": user_points.total_points,
                    "completed_achievements": completed_achievements
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error updating user level achievements: {e}")
                return None
    
    @staticmethod
    def get_user_achievements_summary(user_id):
        """Get a comprehensive summary of user's achievements and progress."""
        with app.app_context():
            try:
                # Get basic summary
                summary = AchievementManager.get_user_achievements_summary(user_id)
                
                # Get user points
                user_points = UserPoints.query.filter_by(user_id=user_id).first()
                if user_points:
                    summary["points"] = user_points.to_dict()
                
                # Get recent achievements
                recent_achievements = UserAchievement.query.filter_by(
                    user_id=user_id, is_completed=True
                ).order_by(UserAchievement.completed_at.desc()).limit(5).all()
                
                summary["recent_achievements"] = [
                    ua.to_dict() for ua in recent_achievements
                ]
                
                # Get achievement progress
                in_progress_achievements = UserAchievement.query.filter_by(
                    user_id=user_id, is_completed=False
                ).all()
                
                summary["in_progress_achievements"] = [
                    ua.to_dict() for ua in in_progress_achievements
                ]
                
                return summary
                
            except Exception as e:
                print(f"Error getting user achievements summary: {e}")
                return None
    
    @staticmethod
    def cleanup_old_activity_data():
        """Clean up old activity data to maintain database performance."""
        with app.app_context():
            try:
                # Remove activity logs older than 1 year
                one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
                
                old_activities = UserActivity.query.filter(
                    UserActivity.created_at < one_year_ago
                ).delete()
                
                # Remove old achievement progress logs (keep last 100 per user achievement)
                from models import AchievementProgress
                
                # Get all user achievements
                user_achievements = UserAchievement.query.all()
                
                for ua in user_achievements:
                    # Get all progress logs for this user achievement
                    progress_logs = AchievementProgress.query.filter_by(
                        user_achievement_id=ua.id
                    ).order_by(AchievementProgress.created_at.desc()).all()
                    
                    # Keep only the last 100 logs
                    if len(progress_logs) > 100:
                        logs_to_delete = progress_logs[100:]
                        for log in logs_to_delete:
                            db.session.delete(log)
                
                db.session.commit()
                
                return {
                    "old_activities_removed": old_activities,
                    "message": "Cleanup completed successfully"
                }
                
            except Exception as e:
                db.session.rollback()
                print(f"Error during cleanup: {e}")
                return None


# Example usage functions
def example_usage():
    """Example of how to use the AchievementTracker in your routes."""
    
    # In a login route:
    def login_route():
        # After successful login
        user_id = current_user.id
        result = AchievementTracker.track_login(user_id, request.remote_addr, request.user_agent.string)
        
        if result and result["completed_achievements"]:
            # Show achievement notifications
            for achievement_data in result["completed_achievements"]:
                achievement = achievement_data["achievement"]
                print(f"🎉 Achievement unlocked: {achievement.name}!")
    
    # In a news reading route:
    def read_news_route(news_id):
        user_id = current_user.id
        result = AchievementTracker.track_reading(user_id, "news", news_id)
        
        if result and result["completed_achievements"]:
            # Show achievement notifications
            for achievement_data in result["completed_achievements"]:
                achievement = achievement_data["achievement"]
                print(f"🎉 Achievement unlocked: {achievement.name}!")
    
    # In a comment creation route:
    def create_comment_route():
        # After creating comment
        user_id = current_user.id
        comment_id = new_comment.id
        result = AchievementTracker.track_comment_creation(user_id, comment_id)
        
        if result and result["completed_achievements"]:
            # Show achievement notifications
            for achievement_data in result["completed_achievements"]:
                achievement = achievement_data["achievement"]
                print(f"🎉 Achievement unlocked: {achievement.name}!")


if __name__ == "__main__":
    # Example usage
    print("Achievement Tracker Helper")
    print("=" * 50)
    print("This module provides functions to track user activities and update achievements.")
    print("Import and use these functions in your routes to automatically award achievements.")
    print("\nExample usage:")
    example_usage()
