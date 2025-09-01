#!/usr/bin/env python3
"""
Achievement System Initialization Script

This script initializes the achievement system with default categories and achievements.
Run this script after creating the database tables to populate the achievement system.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, db
from models import (
    AchievementCategory, Achievement, UserAchievement, UserStreak, UserPoints,
    AchievementManager
)
from datetime import datetime, timezone


def create_achievement_categories():
    """Create default achievement categories."""
    categories = [
        {
            "name": "Login Streaks",
            "description": "Achievements for consistent daily logins",
            "icon_class": "fas fa-calendar-check",
            "color": "#28a745",
            "display_order": 1
        },
        {
            "name": "Activity Streaks",
            "description": "Achievements for daily activity engagement",
            "icon_class": "fas fa-fire",
            "color": "#ff6b35",
            "display_order": 2
        },
        {
            "name": "Reading Streaks",
            "description": "Achievements for consistent content reading",
            "icon_class": "fas fa-book-reader",
            "color": "#6f42c1",
            "display_order": 3
        },
        {
            "name": "Contributions",
            "description": "Achievements for content creation and contributions",
            "icon_class": "fas fa-pen-fancy",
            "color": "#17a2b8",
            "display_order": 4
        },
        {
            "name": "Exploration",
            "description": "Achievements for exploring and engaging with content",
            "icon_class": "fas fa-compass",
            "color": "#fd7e14",
            "display_order": 5
        },
        {
            "name": "Community",
            "description": "Achievements for community engagement and interaction",
            "icon_class": "fas fa-users",
            "color": "#20c997",
            "display_order": 6
        },
        {
            "name": "Milestones",
            "description": "Special milestone achievements",
            "icon_class": "fas fa-trophy",
            "color": "#ffc107",
            "display_order": 7
        }
    ]
    
    created_categories = {}
    
    for cat_data in categories:
        # Check if category already exists
        existing = AchievementCategory.query.filter_by(name=cat_data["name"]).first()
        if existing:
            print(f"Category '{cat_data['name']}' already exists, skipping...")
            created_categories[cat_data["name"]] = existing
            continue
        
        category = AchievementCategory(**cat_data)
        db.session.add(category)
        created_categories[cat_data["name"]] = category
        print(f"Created category: {cat_data['name']}")
    
    db.session.commit()
    return created_categories


def create_login_streak_achievements(categories):
    """Create login streak achievements."""
    login_category = categories["Login Streaks"]
    
    achievements = [
        {
            "name": "First Steps",
            "description": "Login for the first time",
            "achievement_type": "milestone",
            "criteria_type": "login_streak",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 10,
            "rarity": "common",
            "category_id": login_category.id
        },
        {
            "name": "Week Warrior",
            "description": "Maintain a 7-day login streak",
            "achievement_type": "streak",
            "criteria_type": "login_streak",
            "criteria_value": 7,
            "criteria_operator": ">=",
            "points_reward": 50,
            "rarity": "common",
            "category_id": login_category.id
        },
        {
            "name": "Fortnight Fighter",
            "description": "Maintain a 14-day login streak",
            "achievement_type": "streak",
            "criteria_type": "login_streak",
            "criteria_value": 14,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "rare",
            "category_id": login_category.id
        },
        {
            "name": "Monthly Master",
            "description": "Maintain a 30-day login streak",
            "achievement_type": "streak",
            "criteria_type": "login_streak",
            "criteria_value": 30,
            "criteria_operator": ">=",
            "points_reward": 200,
            "rarity": "epic",
            "category_id": login_category.id
        },
        {
            "name": "Century Club",
            "description": "Maintain a 100-day login streak",
            "achievement_type": "streak",
            "criteria_type": "login_streak",
            "criteria_value": 100,
            "criteria_operator": ">=",
            "points_reward": 500,
            "rarity": "legendary",
            "category_id": login_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_activity_streak_achievements(categories):
    """Create activity streak achievements."""
    activity_category = categories["Activity Streaks"]
    
    achievements = [
        {
            "name": "Active Beginner",
            "description": "Be active for 3 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "activity_streak",
            "criteria_value": 3,
            "criteria_operator": ">=",
            "points_reward": 25,
            "rarity": "common",
            "category_id": activity_category.id
        },
        {
            "name": "Active Explorer",
            "description": "Be active for 7 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "activity_streak",
            "criteria_value": 7,
            "criteria_operator": ">=",
            "points_reward": 75,
            "rarity": "common",
            "category_id": activity_category.id
        },
        {
            "name": "Active Enthusiast",
            "description": "Be active for 21 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "activity_streak",
            "criteria_value": 21,
            "criteria_operator": ">=",
            "points_reward": 150,
            "rarity": "rare",
            "category_id": activity_category.id
        },
        {
            "name": "Active Master",
            "description": "Be active for 60 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "activity_streak",
            "criteria_value": 60,
            "criteria_operator": ">=",
            "points_reward": 300,
            "rarity": "epic",
            "category_id": activity_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_reading_streak_achievements(categories):
    """Create reading streak achievements."""
    reading_category = categories["Reading Streaks"]
    
    achievements = [
        {
            "name": "First Reader",
            "description": "Read content for 3 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "reading_streak",
            "criteria_value": 3,
            "criteria_operator": ">=",
            "points_reward": 30,
            "rarity": "common",
            "category_id": reading_category.id
        },
        {
            "name": "Dedicated Reader",
            "description": "Read content for 7 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "reading_streak",
            "criteria_value": 7,
            "criteria_operator": ">=",
            "points_reward": 80,
            "rarity": "common",
            "category_id": reading_category.id
        },
        {
            "name": "Bookworm",
            "description": "Read content for 30 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "reading_streak",
            "criteria_value": 30,
            "criteria_operator": ">=",
            "points_reward": 200,
            "rarity": "rare",
            "category_id": reading_category.id
        },
        {
            "name": "Literary Legend",
            "description": "Read content for 100 consecutive days",
            "achievement_type": "streak",
            "criteria_type": "reading_streak",
            "criteria_value": 100,
            "criteria_operator": ">=",
            "points_reward": 500,
            "rarity": "legendary",
            "category_id": reading_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_contribution_achievements(categories):
    """Create contribution achievements."""
    contribution_category = categories["Contributions"]
    
    achievements = [
        {
            "name": "First Article",
            "description": "Publish your first news article",
            "achievement_type": "milestone",
            "criteria_type": "news_articles",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "common",
            "category_id": contribution_category.id
        },
        {
            "name": "Article Writer",
            "description": "Publish 5 news articles",
            "achievement_type": "count",
            "criteria_type": "news_articles",
            "criteria_value": 5,
            "criteria_operator": ">=",
            "points_reward": 250,
            "rarity": "common",
            "category_id": contribution_category.id
        },
        {
            "name": "Content Creator",
            "description": "Publish 25 news articles",
            "achievement_type": "count",
            "criteria_type": "news_articles",
            "criteria_value": 25,
            "criteria_operator": ">=",
            "points_reward": 500,
            "rarity": "rare",
            "category_id": contribution_category.id
        },
        {
            "name": "First Album",
            "description": "Create your first album",
            "achievement_type": "milestone",
            "criteria_type": "albums_created",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 150,
            "rarity": "common",
            "category_id": contribution_category.id
        },
        {
            "name": "Album Creator",
            "description": "Create 3 albums",
            "achievement_type": "count",
            "criteria_type": "albums_created",
            "criteria_value": 3,
            "criteria_operator": ">=",
            "points_reward": 300,
            "rarity": "rare",
            "category_id": contribution_category.id
        },
        {
            "name": "Image Uploader",
            "description": "Upload 10 images",
            "achievement_type": "count",
            "criteria_type": "images_uploaded",
            "criteria_value": 10,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "common",
            "category_id": contribution_category.id
        },
        {
            "name": "Media Master",
            "description": "Upload 50 images",
            "achievement_type": "count",
            "criteria_type": "images_uploaded",
            "criteria_value": 50,
            "criteria_operator": ">=",
            "points_reward": 250,
            "rarity": "rare",
            "category_id": contribution_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_exploration_achievements(categories):
    """Create exploration achievements."""
    exploration_category = categories["Exploration"]
    
    achievements = [
        {
            "name": "First Comment",
            "description": "Leave your first comment",
            "achievement_type": "milestone",
            "criteria_type": "comments_made",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 20,
            "rarity": "common",
            "category_id": exploration_category.id
        },
        {
            "name": "Commenter",
            "description": "Leave 10 comments",
            "achievement_type": "count",
            "criteria_type": "comments_made",
            "criteria_value": 10,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "common",
            "category_id": exploration_category.id
        },
        {
            "name": "First Rating",
            "description": "Rate your first piece of content",
            "achievement_type": "milestone",
            "criteria_type": "ratings_given",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 15,
            "rarity": "common",
            "category_id": exploration_category.id
        },
        {
            "name": "Critic",
            "description": "Rate 25 pieces of content",
            "achievement_type": "count",
            "criteria_type": "ratings_given",
            "criteria_value": 25,
            "criteria_operator": ">=",
            "points_reward": 150,
            "rarity": "rare",
            "category_id": exploration_category.id
        },
        {
            "name": "Content Explorer",
            "description": "Read 50 different articles",
            "achievement_type": "count",
            "criteria_type": "articles_read",
            "criteria_value": 50,
            "criteria_operator": ">=",
            "points_reward": 200,
            "rarity": "rare",
            "category_id": exploration_category.id
        },
        {
            "name": "Book Explorer",
            "description": "Read 10 different albums",
            "achievement_type": "count",
            "criteria_type": "albums_read",
            "criteria_value": 10,
            "criteria_operator": ">=",
            "points_reward": 300,
            "rarity": "rare",
            "category_id": exploration_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_community_achievements(categories):
    """Create community engagement achievements."""
    community_category = categories["Community"]
    
    achievements = [
        {
            "name": "First Like",
            "description": "Like your first comment",
            "achievement_type": "milestone",
            "criteria_type": "comment_likes_given",
            "criteria_value": 1,
            "criteria_operator": ">=",
            "points_reward": 10,
            "rarity": "common",
            "category_id": community_category.id
        },
        {
            "name": "Supportive",
            "description": "Like 20 comments",
            "achievement_type": "count",
            "criteria_type": "comment_likes_given",
            "criteria_value": 20,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "common",
            "category_id": community_category.id
        },
        {
            "name": "Popular Comment",
            "description": "Receive 5 likes on a comment",
            "achievement_type": "milestone",
            "criteria_type": "comment_likes_received",
            "criteria_value": 5,
            "criteria_operator": ">=",
            "points_reward": 50,
            "rarity": "rare",
            "category_id": community_category.id
        },
        {
            "name": "Viral Comment",
            "description": "Receive 25 likes on a comment",
            "achievement_type": "milestone",
            "criteria_type": "comment_likes_received",
            "criteria_value": 25,
            "criteria_operator": ">=",
            "points_reward": 200,
            "rarity": "epic",
            "category_id": community_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def create_milestone_achievements(categories):
    """Create special milestone achievements."""
    milestone_category = categories["Milestones"]
    
    achievements = [
        {
            "name": "Level 5",
            "description": "Reach level 5",
            "achievement_type": "milestone",
            "criteria_type": "user_level",
            "criteria_value": 5,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "common",
            "category_id": milestone_category.id
        },
        {
            "name": "Level 10",
            "description": "Reach level 10",
            "achievement_type": "milestone",
            "criteria_type": "user_level",
            "criteria_value": 10,
            "criteria_operator": ">=",
            "points_reward": 250,
            "rarity": "rare",
            "category_id": milestone_category.id
        },
        {
            "name": "Level 25",
            "description": "Reach level 25",
            "achievement_type": "milestone",
            "criteria_type": "user_level",
            "criteria_value": 25,
            "criteria_operator": ">=",
            "points_reward": 500,
            "rarity": "epic",
            "category_id": milestone_category.id
        },
        {
            "name": "Level 50",
            "description": "Reach level 50",
            "achievement_type": "milestone",
            "criteria_type": "user_level",
            "criteria_value": 50,
            "criteria_operator": ">=",
            "points_reward": 1000,
            "rarity": "legendary",
            "category_id": milestone_category.id
        },
        {
            "name": "1000 Points",
            "description": "Earn 1000 total points",
            "achievement_type": "milestone",
            "criteria_type": "total_points",
            "criteria_value": 1000,
            "criteria_operator": ">=",
            "points_reward": 100,
            "rarity": "rare",
            "category_id": milestone_category.id
        },
        {
            "name": "5000 Points",
            "description": "Earn 5000 total points",
            "achievement_type": "milestone",
            "criteria_type": "total_points",
            "criteria_value": 5000,
            "criteria_operator": ">=",
            "points_reward": 500,
            "rarity": "epic",
            "category_id": milestone_category.id
        }
    ]
    
    for achievement_data in achievements:
        existing = Achievement.query.filter_by(name=achievement_data["name"]).first()
        if existing:
            print(f"Achievement '{achievement_data['name']}' already exists, skipping...")
            continue
        
        achievement = Achievement(**achievement_data)
        db.session.add(achievement)
        print(f"Created achievement: {achievement_data['name']}")
    
    db.session.commit()


def main():
    """Main function to initialize the achievement system."""
    with app.app_context():
        print("🚀 Initializing Achievement System")
        print("=" * 50)
        
        try:
            # Create achievement categories
            print("📂 Creating achievement categories...")
            categories = create_achievement_categories()
            
            # Create achievements for each category
            print("\n🏆 Creating login streak achievements...")
            create_login_streak_achievements(categories)
            
            print("\n🔥 Creating activity streak achievements...")
            create_activity_streak_achievements(categories)
            
            print("\n📚 Creating reading streak achievements...")
            create_reading_streak_achievements(categories)
            
            print("\n✍️ Creating contribution achievements...")
            create_contribution_achievements(categories)
            
            print("\n🔍 Creating exploration achievements...")
            create_exploration_achievements(categories)
            
            print("\n👥 Creating community achievements...")
            create_community_achievements(categories)
            
            print("\n🏅 Creating milestone achievements...")
            create_milestone_achievements(categories)
            
            print("\n✅ Achievement system initialization completed!")
            print("=" * 50)
            
            # Print summary
            total_categories = AchievementCategory.query.count()
            total_achievements = Achievement.query.count()
            
            print(f"📊 Summary:")
            print(f"   - Categories created: {total_categories}")
            print(f"   - Achievements created: {total_achievements}")
            print("\n🎉 Achievement system is ready to use!")
            
        except Exception as e:
            print(f"❌ Error initializing achievement system: {e}")
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
