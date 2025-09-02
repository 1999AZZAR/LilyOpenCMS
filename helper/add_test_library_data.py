#!/usr/bin/env python3
"""
Add test library data for users.
This script adds some sample library items and reading history for testing.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import app
from models import db, User, UserLibrary, ReadingHistory, News, Album
from datetime import datetime, timedelta
import random

def add_test_library_data():
    """Add test library data for users."""
    
    with app.app_context():
        print("📚 Adding test library data...")
        
        # Get some users (any role, not just general)
        users = User.query.limit(5).all()
        if not users:
            print("❌ No general users found!")
            return
        
        # Get some news and albums
        news_items = News.query.filter_by(is_visible=True).limit(10).all()
        albums = Album.query.filter_by(is_visible=True).limit(10).all()
        
        if not news_items and not albums:
            print("❌ No content found!")
            return
        
        print(f"👤 Found {len(users)} users")
        print(f"📰 Found {len(news_items)} news items")
        print(f"📚 Found {len(albums)} albums")
        
        # Add library items
        library_count = 0
        for user in users:
            # Add 2-4 random news items to library
            for _ in range(random.randint(2, 4)):
                if news_items:
                    news = random.choice(news_items)
                    
                    # Check if already in library
                    existing = UserLibrary.query.filter_by(
                        user_id=user.id,
                        content_type='news',
                        content_id=news.id
                    ).first()
                    
                    if not existing:
                        library_item = UserLibrary(
                            user_id=user.id,
                            content_type='news',
                            content_id=news.id,
                            added_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                        )
                        db.session.add(library_item)
                        library_count += 1
            
            # Add 1-3 random albums to library
            for _ in range(random.randint(1, 3)):
                if albums:
                    album = random.choice(albums)
                    
                    # Check if already in library
                    existing = UserLibrary.query.filter_by(
                        user_id=user.id,
                        content_type='album',
                        content_id=album.id
                    ).first()
                    
                    if not existing:
                        library_item = UserLibrary(
                            user_id=user.id,
                            content_type='album',
                            content_id=album.id,
                            added_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                        )
                        db.session.add(library_item)
                        library_count += 1
        
        # Add reading history
        history_count = 0
        for user in users:
            # Add reading history for some news items
            for _ in range(random.randint(3, 6)):
                if news_items:
                    news = random.choice(news_items)
                    
                    # Check if already in reading history
                    existing = ReadingHistory.query.filter_by(
                        user_id=user.id,
                        content_type='news',
                        content_id=news.id
                    ).first()
                    
                    if not existing:
                        history_item = ReadingHistory(
                            user_id=user.id,
                            content_type='news',
                            content_id=news.id,
                            read_count=random.randint(1, 5),
                            first_read_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                            last_read_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                        )
                        db.session.add(history_item)
                        history_count += 1
            
            # Add reading history for some albums
            for _ in range(random.randint(2, 4)):
                if albums:
                    album = random.choice(albums)
                    
                    # Check if already in reading history
                    existing = ReadingHistory.query.filter_by(
                        user_id=user.id,
                        content_type='album',
                        content_id=album.id
                    ).first()
                    
                    if not existing:
                        history_item = ReadingHistory(
                            user_id=user.id,
                            content_type='album',
                            content_id=album.id,
                            read_count=random.randint(1, 3),
                            first_read_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                            last_read_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                        )
                        db.session.add(history_item)
                        history_count += 1
        
        try:
            db.session.commit()
            print(f"✅ Added {library_count} library items")
            print(f"✅ Added {history_count} reading history items")
            print("🎉 Test library data added successfully!")
        except Exception as e:
            print(f"❌ Error adding test data: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_test_library_data()
