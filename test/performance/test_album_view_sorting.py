#!/usr/bin/env python3
"""
Test script to verify album view-based sorting functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models import db, Album, User, Category, UserRole

def test_album_view_sorting():
    """Test the album view-based sorting functionality"""
    print("🧪 Testing Album View-Based Sorting...")
    
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
                category = Category(name='Test Category', description='Test category for sorting')
                db.session.add(category)
                db.session.commit()
            
            # Create test albums with different view counts
            test_albums = []
            for i in range(3):
                album = Album(
                    title=f'ViewSortTest Album {i+1}',
                    description=f'ViewSortTest album description {i+1}',
                    user_id=user.id,
                    category_id=category.id,
                    is_visible=True,
                    is_archived=False,
                    total_views=100 - i*30,  # 100, 70, 40 views
                    total_reads=200 - i*50,  # 200, 150, 100 reads
                    total_chapters=5
                )
                db.session.add(album)
                test_albums.append(album)
            
            db.session.commit()
            
            # Test most-viewed sorting
            print("  📊 Testing 'most-viewed' sorting...")
            with app.test_client() as client:
                response = client.get('/api/search/albums?sort=most-viewed&q=ViewSortTest')
                data = response.get_json()
                
                if data['success'] and len(data['albums']) >= 3:
                    # Find our test albums by title
                    test_albums_found = [album for album in data['albums'] if 'ViewSortTest' in album['title']]
                    if len(test_albums_found) >= 3:
                        views = [album['total_views'] for album in test_albums_found[:3]]
                        titles = [album['title'] for album in test_albums_found[:3]]
                        print(f"    📊 Found albums: {titles}")
                        print(f"    📊 View counts: {views}")
                        # Check if the sorting is correct (descending order)
                        if views[0] >= views[1] >= views[2]:
                            print("    ✅ 'most-viewed' sorting works correctly")
                        else:
                            print(f"    ❌ 'most-viewed' sorting failed. Expected descending order, got {views}")
                            return False
                    else:
                        print(f"    ❌ Only found {len(test_albums_found)} test albums")
                        return False
                else:
                    print("    ❌ Failed to get albums for most-viewed sorting")
                    return False
            
            # Test least-viewed sorting
            print("  📊 Testing 'least-viewed' sorting...")
            with app.test_client() as client:
                response = client.get('/api/search/albums?sort=least-viewed&q=ViewSortTest')
                data = response.get_json()
                
                if data['success'] and len(data['albums']) >= 3:
                    # Find our test albums by title
                    test_albums_found = [album for album in data['albums'] if 'ViewSortTest' in album['title']]
                    if len(test_albums_found) >= 3:
                        views = [album['total_views'] for album in test_albums_found[:3]]
                        titles = [album['title'] for album in test_albums_found[:3]]
                        print(f"    📊 Found albums: {titles}")
                        print(f"    📊 View counts: {views}")
                        # Check if the sorting is correct (ascending order)
                        if views[0] <= views[1] <= views[2]:
                            print("    ✅ 'least-viewed' sorting works correctly")
                        else:
                            print(f"    ❌ 'least-viewed' sorting failed. Expected ascending order, got {views}")
                            return False
                    else:
                        print(f"    ❌ Only found {len(test_albums_found)} test albums")
                        return False
                else:
                    print("    ❌ Failed to get albums for least-viewed sorting")
                    return False
            
            # Test that total_views is included in API response
            print("  📊 Testing total_views field in API response...")
            with app.test_client() as client:
                response = client.get('/api/search/albums')
                data = response.get_json()
                
                if data['success'] and len(data['albums']) > 0:
                    album = data['albums'][0]
                    if 'total_views' in album:
                        print("    ✅ total_views field is included in API response")
                    else:
                        print("    ❌ total_views field is missing from API response")
                        return False
                else:
                    print("    ❌ Failed to get albums for API response test")
                    return False
            
            # Clean up test data
            for album in test_albums:
                db.session.delete(album)
            db.session.commit()
            db.session.delete(category)
            db.session.delete(user)
            db.session.commit()
            
            print("🎉 All album view-based sorting tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False

if __name__ == "__main__":
    success = test_album_view_sorting()
    sys.exit(0 if success else 1)
