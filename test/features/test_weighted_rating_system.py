"""
Test for the weighted rating system for albums
"""
import pytest
from models import db, Album, News, Rating, AlbumChapter, User, Category, UserRole
from datetime import datetime, timezone


class TestWeightedRatingSystem:
    """Test cases for the weighted rating system"""
    
    def test_album_weighted_rating_calculation(self, app):
        """Test that album weighted rating is calculated correctly"""
        with app.app_context():
            # Create test data
            user = User(username='testuser', password_hash='test')
            category = Category(name='Test Category')
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create album
            album = Album(
                title='Test Album',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(album)
            db.session.commit()
            
            # Create news articles (chapters)
            news1 = News(
                title='Chapter 1',
                content='Content 1',
                user_id=user.id,
                category_id=category.id,
                read_count=100
            )
            news2 = News(
                title='Chapter 2', 
                content='Content 2',
                user_id=user.id,
                category_id=category.id,
                read_count=200  # More popular
            )
            db.session.add_all([news1, news2])
            db.session.commit()
            
            # Create album chapters
            chapter1 = AlbumChapter(
                album_id=album.id,
                news_id=news1.id,
                chapter_number=1,
                chapter_title='Chapter 1'
            )
            chapter2 = AlbumChapter(
                album_id=album.id,
                news_id=news2.id,
                chapter_number=2,
                chapter_title='Chapter 2'
            )
            db.session.add_all([chapter1, chapter2])
            db.session.commit()
            
            # Add ratings to chapters
            rating1 = Rating(
                rating_value=4,
                content_type='news',
                content_id=news1.id,
                user_id=user.id
            )
            rating2 = Rating(
                rating_value=5,
                content_type='news', 
                content_id=news2.id,
                user_id=user.id
            )
            db.session.add_all([rating1, rating2])
            db.session.commit()
            
            # Test weighted rating calculation
            weighted_stats = album.get_weighted_rating_stats()
            
            # Verify results
            assert weighted_stats['weighted_average'] > 0
            assert weighted_stats['total_chapters_rated'] == 2
            assert weighted_stats['total_ratings'] == 2
            assert len(weighted_stats['chapter_breakdown']) == 2
            
            # Chapter 2 should have higher weight due to more reads
            chapter2_data = next(c for c in weighted_stats['chapter_breakdown'] if c['chapter_number'] == 2)
            chapter1_data = next(c for c in weighted_stats['chapter_breakdown'] if c['chapter_number'] == 1)
            
            assert chapter2_data['weight'] > chapter1_data['weight']
            assert chapter2_data['read_count'] == 200
            assert chapter1_data['read_count'] == 100
            
            # Cleanup
            db.session.delete(album)
            db.session.delete(news1)
            db.session.delete(news2)
            db.session.delete(user)
            db.session.delete(category)
            db.session.commit()
    
    def test_album_no_ratings(self, app):
        """Test album with no chapter ratings returns zero"""
        with app.app_context():
            # Create test data
            user = User(username='testuser', password_hash='test')
            category = Category(name='Test Category')
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create album
            album = Album(
                title='Test Album',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(album)
            db.session.commit()
            
            # Test weighted rating with no ratings
            weighted_stats = album.get_weighted_rating_stats()
            
            assert weighted_stats['weighted_average'] == 0.0
            assert weighted_stats['total_chapters_rated'] == 0
            assert weighted_stats['total_ratings'] == 0
            
            # Cleanup
            db.session.delete(album)
            db.session.delete(user)
            db.session.delete(category)
            db.session.commit()
    
    def test_weighted_rating_formula(self, app):
        """Test the weighted rating formula calculation"""
        with app.app_context():
            # Create test data
            user = User(username='testuser', password_hash='test')
            category = Category(name='Test Category')
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create album
            album = Album(
                title='Test Album',
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(album)
            db.session.commit()
            
            # Create news with specific read counts
            news1 = News(
                title='Chapter 1',
                content='Content 1',
                user_id=user.id,
                category_id=category.id,
                read_count=50
            )
            news2 = News(
                title='Chapter 2',
                content='Content 2', 
                user_id=user.id,
                category_id=category.id,
                read_count=100  # Max read count
            )
            db.session.add_all([news1, news2])
            db.session.commit()
            
            # Create chapters
            chapter1 = AlbumChapter(
                album_id=album.id,
                news_id=news1.id,
                chapter_number=1,
                chapter_title='Chapter 1'
            )
            chapter2 = AlbumChapter(
                album_id=album.id,
                news_id=news2.id,
                chapter_number=2,
                chapter_title='Chapter 2'
            )
            db.session.add_all([chapter1, chapter2])
            db.session.commit()
            
            # Add ratings
            rating1 = Rating(
                rating_value=3,
                content_type='news',
                content_id=news1.id,
                user_id=user.id
            )
            rating2 = Rating(
                rating_value=5,
                content_type='news',
                content_id=news2.id,
                user_id=user.id
            )
            db.session.add_all([rating1, rating2])
            db.session.commit()
            
            # Calculate expected weights
            # Chapter 1: weight = 1 + (50/100) * 0.5 = 1.25
            # Chapter 2: weight = 1 + (100/100) * 0.5 = 1.5
            
            # Expected weighted average:
            # (3 * 1.25 + 5 * 1.5) / (1.25 + 1.5) = (3.75 + 7.5) / 2.75 = 4.09
            
            weighted_stats = album.get_weighted_rating_stats()
            expected_rating = round((3 * 1.25 + 5 * 1.5) / (1.25 + 1.5), 2)
            
            assert abs(weighted_stats['weighted_average'] - expected_rating) < 0.01
            
            # Cleanup
            db.session.delete(album)
            db.session.delete(news1)
            db.session.delete(news2)
            db.session.delete(user)
            db.session.delete(category)
            db.session.commit()

    def test_rating_detection_logic(self, app):
        """Test that the rating system correctly distinguishes between no ratings and zero average ratings."""
        with app.app_context():
            # Create test data
            user = User(username="testuser", role=UserRole.GENERAL)
            category = Category(name="Test Category")
            db.session.add_all([user, category])
            db.session.commit()
            
            # Create album with chapters
            album = Album(
                title="Test Album",
                user_id=user.id,
                category_id=category.id
            )
            db.session.add(album)
            db.session.commit()
            
            # Create news articles for chapters
            news1 = News(
                title="Chapter 1",
                content="Content 1",
                user_id=user.id,
                category_id=category.id
            )
            news2 = News(
                title="Chapter 2", 
                content="Content 2",
                user_id=user.id,
                category_id=category.id
            )
            db.session.add_all([news1, news2])
            db.session.commit()
            
            # Create chapters
            chapter1 = AlbumChapter(
                album_id=album.id,
                news_id=news1.id,
                chapter_number=1,
                chapter_title="Chapter 1"
            )
            chapter2 = AlbumChapter(
                album_id=album.id,
                news_id=news2.id,
                chapter_number=2,
                chapter_title="Chapter 2"
            )
            db.session.add_all([chapter1, chapter2])
            db.session.commit()
            
            # Test 1: No ratings at all
            assert not Rating.has_ratings('news', news1.id)
            assert Rating.get_average_rating('news', news1.id) is None
            assert Rating.get_rating_count('news', news1.id) == 0
            
            # Test 2: Add a zero rating
            rating1 = Rating(
                rating_value=1,  # 1-star rating
                content_type='news',
                content_id=news1.id,
                user_id=user.id
            )
            db.session.add(rating1)
            db.session.commit()
            
            # Now there should be ratings
            assert Rating.has_ratings('news', news1.id)
            assert Rating.get_average_rating('news', news1.id) == 1.0
            assert Rating.get_rating_count('news', news1.id) == 1
            
            # Test 3: Add another rating to make average 0.5
            rating2 = Rating(
                rating_value=1,  # Another 1-star rating
                content_type='news',
                content_id=news1.id,
                user_id=user.id + 1  # Different user
            )
            db.session.add(rating2)
            db.session.commit()
            
            # Should still have ratings
            assert Rating.has_ratings('news', news1.id)
            assert Rating.get_average_rating('news', news1.id) == 1.0
            assert Rating.get_rating_count('news', news1.id) == 2
            
            # Test 4: Album weighted rating with mixed ratings
            # Add a 5-star rating to news2
            rating3 = Rating(
                rating_value=5,
                content_type='news',
                content_id=news2.id,
                user_id=user.id
            )
            db.session.add(rating3)
            db.session.commit()
            
            # Get album weighted stats
            weighted_stats = album.get_weighted_rating_stats()
            
            # Should include both chapters since both have ratings
            assert weighted_stats['total_chapters_rated'] == 2
            assert weighted_stats['total_ratings'] == 3  # 2 from news1 + 1 from news2
            assert weighted_stats['weighted_average'] > 0  # Should be weighted average of 1.0 and 5.0


if __name__ == '__main__':
    pytest.main([__file__]) 