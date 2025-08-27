#!/usr/bin/env python3
"""
Test script to verify album view counting mechanism
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import db, Album, User, Category, UserRole

def test_album_view_count():
    """Test the album view counting functionality"""
    print("🧪 Testing Album View Count Mechanism...")
    
    with app.app_context():
        try:
            # Get or create test data
            user = User.query.filter_by(username='testuser').first()
            if not user:
                user = User(username='testuser', role=UserRole.GENERAL)
                user.set_password('testpass123')
                db.session.add(user)
                db.session.commit()
            
            category = Category.query.filter_by(name='Test Category').first()
            if not category:
                category = Category(name='Test Category')
                db.session.add(category)
                db.session.commit()
            
            # Create a test album
            album = Album.query.filter_by(title='Test Album for View Count').first()
            if not album:
                album = Album(
                    title='Test Album for View Count',
                    description='Test album for view counting',
                    user_id=user.id,
                    category_id=category.id,
                    total_views=0,
                    total_reads=0
                )
                db.session.add(album)
                db.session.commit()
                print(f"✅ Created test album: {album.title}")
            
            # Test initial state
            initial_views = album.total_views
            print(f"📊 Initial view count: {initial_views}")
            
            # Test increment_views method
            print("🔄 Testing increment_views() method...")
            album.increment_views()
            
            # Refresh from database
            db.session.refresh(album)
            new_views = album.total_views
            
            print(f"📊 New view count: {new_views}")
            
            if new_views == initial_views + 1:
                print("✅ View count incremented successfully!")
            else:
                print(f"❌ View count not incremented correctly. Expected: {initial_views + 1}, Got: {new_views}")
                return False
            
            # Test multiple increments
            print("🔄 Testing multiple increments...")
            for i in range(5):
                album.increment_views()
            
            db.session.refresh(album)
            final_views = album.total_views
            expected_views = new_views + 5
            
            print(f"📊 Final view count: {final_views}")
            print(f"📊 Expected view count: {expected_views}")
            
            if final_views == expected_views:
                print("✅ Multiple view increments work correctly!")
            else:
                print(f"❌ Multiple increments failed. Expected: {expected_views}, Got: {final_views}")
                return False
            
            # Test to_dict method includes total_views
            print("🔄 Testing to_dict() method includes total_views...")
            album_dict = album.to_dict()
            
            if 'total_views' in album_dict:
                print(f"✅ total_views included in to_dict(): {album_dict['total_views']}")
            else:
                print("❌ total_views not included in to_dict()")
                return False
            
            print("🎉 All album view count tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_album_view_count()
    sys.exit(0 if success else 1)
