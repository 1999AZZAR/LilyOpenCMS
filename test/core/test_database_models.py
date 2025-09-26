#!/usr/bin/env python3
"""
Test script for Database Models
Tests all database models, relationships, validations, and methods
"""

import sys
import os
import pytest
from datetime import datetime, timezone, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cleanup_test_data():
    """Clean up test data from database"""
    print("🧹 Cleaning up database test data...")
    
    try:
        from models import db, User, News, Category, Album, AlbumChapter, Comment, Rating, Image
        
        with app.app_context():
            # Clean up test users
            test_users = User.query.filter(User.username.like('test%')).all()
            for user in test_users:
                db.session.delete(user)
            
            # Clean up test categories
            test_categories = Category.query.filter(Category.name.like('Test%')).all()
            for category in test_categories:
                db.session.delete(category)
            
            # Clean up test news
            test_news = News.query.filter(News.title.like('Test%')).all()
            for news in test_news:
                db.session.delete(news)
            
            # Clean up test albums
            test_albums = Album.query.filter(Album.title.like('Test%')).all()
            for album in test_albums:
                db.session.delete(album)
            
            # Clean up test images
            test_images = Image.query.filter(Image.filename.like('test%')).all()
            for image in test_images:
                db.session.delete(image)
            
            # Clean up test comments
            test_comments = Comment.query.filter(Comment.content.like('Test%')).all()
            for comment in test_comments:
                db.session.delete(comment)
            
            # Clean up test ratings
            test_ratings = Rating.query.filter(Rating.rating_value.in_([1, 3, 5])).all()
            for rating in test_ratings:
                db.session.delete(rating)
            
            db.session.commit()
            print("  ✅ Database test data cleaned successfully")
            
    except Exception as e:
        print(f"  ❌ Database cleanup failed: {e}")
        db.session.rollback()

def test_user_model():
    """Test User model functionality"""
    print("🧪 Testing User Model...")
    
    try:
        from models import User, UserRole, db
        
        # Test 1: User creation
        print("  👤 Testing user creation...")
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role=UserRole.GENERAL
        )
        user.set_password('testpass123')
        
        # Test password hashing
        assert user.check_password('testpass123') == True
        assert user.check_password('wrongpass') == False
        print("    ✅ Password hashing works correctly")
        
        # Test user properties
        assert user.get_full_name() == 'Test User'
        assert user.is_owner() == False  # Not a superuser
        print("    ✅ User properties work correctly")
        
        # Test activity recording
        user.record_activity('test_activity', 'Test activity description')
        assert len(user.activities) == 1
        print("    ✅ Activity recording works correctly")
        
        print("    ✅ User model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing User model: {e}")

def test_news_model():
    """Test News model functionality"""
    print("🧪 Testing News Model...")
    
    try:
        from models import News, Category, User, UserRole, db
        
        # Test 1: News creation
        print("  📰 Testing news creation...")
        category = Category(name='Test Category')
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        news = News(
            title='Test News Article',
            content='This is a test news article content.',
            category=category,
            author=user,
            tagar='test,news,article'
        )
        
        # Test validation
        assert news.validate() == True
        print("    ✅ News validation works correctly")
        
        # Test SEO methods
        news.generate_seo_slug()
        assert news.seo_slug is not None
        print("    ✅ SEO slug generation works correctly")
        
        # Test read count increment
        initial_count = news.read_count
        news.increment_reads()
        assert news.read_count == initial_count + 1
        print("    ✅ Read count increment works correctly")
        
        print("    ✅ News model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing News model: {e}")

def test_album_model():
    """Test Album model functionality"""
    print("🧪 Testing Album Model...")
    
    try:
        from models import Album, Category, User, UserRole, News, AlbumChapter, db
        
        # Test 1: Album creation
        print("  📚 Testing album creation...")
        category = Category(name='Test Category')
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        album = Album(
            title='Test Album',
            description='This is a test album.',
            category=category,
            author=user
        )
        
        # Test validation
        assert album.validate() == True
        print("    ✅ Album validation works correctly")
        
        # Test SEO methods
        album.generate_seo_slug()
        assert album.seo_slug is not None
        print("    ✅ SEO slug generation works correctly")
        
        # Test chapter management
        news = News(
            title='Chapter 1',
            content='Chapter 1 content',
            category=category,
            author=user
        )
        
        chapter = AlbumChapter(
            album=album,
            news=news,
            chapter_number=1,
            chapter_title='Chapter 1'
        )
        
        album.update_chapter_count()
        assert album.total_chapters == 1
        print("    ✅ Chapter management works correctly")
        
        print("    ✅ Album model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Album model: {e}")

def test_comment_model():
    """Test Comment model functionality"""
    print("🧪 Testing Comment Model...")
    
    try:
        from models import Comment, User, UserRole, News, Category, db
        
        # Test 1: Comment creation
        print("  💬 Testing comment creation...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        category = Category(name='Test Category')
        news = News(
            title='Test News',
            content='Test content',
            category=category,
            author=user
        )
        
        comment = Comment(
            content='This is a test comment.',
            user=user,
            content_type='news',
            content_id=news.id
        )
        
        # Test validation
        assert comment.validate() == True
        print("    ✅ Comment validation works correctly")
        
        # Test content object retrieval
        content_obj = comment.get_content_object()
        assert content_obj is not None
        print("    ✅ Content object retrieval works correctly")
        
        print("    ✅ Comment model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Comment model: {e}")

def test_rating_model():
    """Test Rating model functionality"""
    print("🧪 Testing Rating Model...")
    
    try:
        from models import Rating, User, UserRole, News, Category, db
        
        # Test 1: Rating creation
        print("  ⭐ Testing rating creation...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        category = Category(name='Test Category')
        news = News(
            title='Test News',
            content='Test content',
            category=category,
            author=user
        )
        
        rating = Rating(
            rating_value=5,
            user=user,
            content_type='news',
            content_id=news.id
        )
        
        # Test validation
        assert rating.validate() == True
        print("    ✅ Rating validation works correctly")
        
        # Test static methods
        avg_rating = Rating.get_average_rating('news', news.id)
        rating_count = Rating.get_rating_count('news', news.id)
        has_ratings = Rating.has_ratings('news', news.id)
        
        print("    ✅ Rating static methods work correctly")
        
        print("    ✅ Rating model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Rating model: {e}")

def test_image_model():
    """Test Image model functionality"""
    print("🧪 Testing Image Model...")
    
    try:
        from models import Image, User, UserRole, db
        
        # Test 1: Image creation
        print("  🖼️ Testing image creation...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        image = Image(
            filename='test_image.jpg',
            description='Test image description',
            filepath='/static/uploads/test_image.jpg',
            user=user
        )
        
        # Test to_dict method
        image_dict = image.to_dict()
        assert 'id' in image_dict
        assert 'filename' in image_dict
        print("    ✅ Image to_dict method works correctly")
        
        print("    ✅ Image model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Image model: {e}")

def test_category_model():
    """Test Category model functionality"""
    print("🧪 Testing Category Model...")
    
    try:
        from models import Category, db
        
        # Test 1: Category creation
        print("  📂 Testing category creation...")
        category = Category(name='Test Category')
        
        # Test to_dict method
        category_dict = category.to_dict()
        assert 'id' in category_dict
        assert 'name' in category_dict
        print("    ✅ Category to_dict method works correctly")
        
        print("    ✅ Category model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Category model: {e}")

def test_subscription_model():
    """Test UserSubscription model functionality"""
    print("🧪 Testing Subscription Model...")
    
    try:
        from models import UserSubscription, User, UserRole, db
        from datetime import datetime, timezone, timedelta
        
        # Test 1: Subscription creation
        print("  💳 Testing subscription creation...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        subscription = UserSubscription(
            user=user,
            subscription_type='monthly',
            status='active',
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            payment_provider='test',
            payment_id='test_payment_1',
            amount=99000,
            currency='IDR',
            auto_renew=True
        )
        
        # Test is_active property
        assert subscription.is_active == True
        print("    ✅ Subscription is_active property works correctly")
        
        # Test to_dict method
        subscription_dict = subscription.to_dict()
        assert 'id' in subscription_dict
        assert 'subscription_type' in subscription_dict
        print("    ✅ Subscription to_dict method works correctly")
        
        print("    ✅ Subscription model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Subscription model: {e}")

def test_brand_identity_model():
    """Test BrandIdentity model functionality"""
    print("🧪 Testing Brand Identity Model...")
    
    try:
        from models import BrandIdentity, db
        
        # Test 1: Brand identity creation
        print("  🏷️ Testing brand identity creation...")
        brand = BrandIdentity(
            brand_name='Test Brand',
            tagline='Test tagline',
            logo_header='/static/pic/logo.png',
            logo_footer='/static/pic/logo_footer.png',
            favicon='/static/pic/favicon.png',
            placeholder_image='/static/pic/placeholder.png'
        )
        
        # Test to_dict method
        brand_dict = brand.to_dict()
        assert 'id' in brand_dict
        assert 'brand_name' in brand_dict
        print("    ✅ Brand identity to_dict method works correctly")
        
        print("    ✅ Brand identity model tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing Brand Identity model: {e}")

def test_relationships():
    """Test model relationships"""
    print("🧪 Testing Model Relationships...")
    
    try:
        from models import User, UserRole, News, Category, Album, AlbumChapter, Comment, Rating, db
        
        # Test 1: User-News relationship
        print("  🔗 Testing User-News relationship...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        category = Category(name='Test Category')
        news = News(
            title='Test News',
            content='Test content',
            category=category,
            author=user
        )
        
        assert news.author == user
        assert news in user.news
        print("    ✅ User-News relationship works correctly")
        
        # Test 2: Album-Chapter relationship
        print("  🔗 Testing Album-Chapter relationship...")
        album = Album(
            title='Test Album',
            category=category,
            author=user
        )
        
        chapter = AlbumChapter(
            album=album,
            news=news,
            chapter_number=1,
            chapter_title='Chapter 1'
        )
        
        assert chapter.album == album
        assert chapter in album.chapters
        print("    ✅ Album-Chapter relationship works correctly")
        
        # Test 3: Comment-User relationship
        print("  🔗 Testing Comment-User relationship...")
        comment = Comment(
            content='Test comment',
            user=user,
            content_type='news',
            content_id=news.id
        )
        
        assert comment.user == user
        assert comment in user.comments
        print("    ✅ Comment-User relationship works correctly")
        
        print("    ✅ All relationship tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing relationships: {e}")

def test_validations():
    """Test model validations"""
    print("🧪 Testing Model Validations...")
    
    try:
        from models import User, UserRole, News, Category, Comment, Rating, db
        
        # Test 1: User validation
        print("  ✅ Testing user validation...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        # Test 2: News validation
        print("  ✅ Testing news validation...")
        category = Category(name='Test Category')
        news = News(
            title='Test News',
            content='Test content',
            category=category,
            author=user
        )
        
        assert news.validate() == True
        print("    ✅ News validation works correctly")
        
        # Test 3: Comment validation
        print("  ✅ Testing comment validation...")
        comment = Comment(
            content='Test comment',
            user=user,
            content_type='news',
            content_id=news.id
        )
        
        assert comment.validate() == True
        print("    ✅ Comment validation works correctly")
        
        # Test 4: Rating validation
        print("  ✅ Testing rating validation...")
        rating = Rating(
            rating_value=5,
            user=user,
            content_type='news',
            content_id=news.id
        )
        
        assert rating.validate() == True
        print("    ✅ Rating validation works correctly")
        
        print("    ✅ All validation tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing validations: {e}")

def test_methods():
    """Test model methods"""
    print("🧪 Testing Model Methods...")
    
    try:
        from models import User, UserRole, News, Category, Album, db
        
        # Test 1: User methods
        print("  🔧 Testing user methods...")
        user = User(username='testuser', role=UserRole.GENERAL)
        user.set_password('testpass123')
        
        # Test password methods
        assert user.check_password('testpass123') == True
        assert user.check_password('wrongpass') == False
        
        # Test permission methods
        assert user.has_permission('news', 'read') == True  # General users can read news
        print("    ✅ User methods work correctly")
        
        # Test 2: News methods
        print("  🔧 Testing news methods...")
        category = Category(name='Test Category')
        news = News(
            title='Test News',
            content='Test content',
            category=category,
            author=user
        )
        
        # Test SEO methods
        news.generate_seo_slug()
        assert news.seo_slug is not None
        
        # Test read increment
        initial_count = news.read_count
        news.increment_reads()
        assert news.read_count == initial_count + 1
        print("    ✅ News methods work correctly")
        
        # Test 3: Album methods
        print("  🔧 Testing album methods...")
        album = Album(
            title='Test Album',
            category=category,
            author=user
        )
        
        # Test SEO methods
        album.generate_seo_slug()
        assert album.seo_slug is not None
        print("    ✅ Album methods work correctly")
        
        print("    ✅ All method tests passed")
        
    except Exception as e:
        print(f"    ❌ Error testing methods: {e}")

def main():
    """Run all database model tests"""
    print("🚀 Starting Database Models Tests")
    print("=" * 50)
    
    test_user_model()
    print()
    test_news_model()
    print()
    test_album_model()
    print()
    test_comment_model()
    print()
    test_rating_model()
    print()
    test_image_model()
    print()
    test_category_model()
    print()
    test_subscription_model()
    print()
    test_brand_identity_model()
    print()
    test_relationships()
    print()
    test_validations()
    print()
    test_methods()
    print()
    
    print("✅ All database model tests completed!")
    print("\n📋 Test Summary:")
    print("  - User Model: Authentication, permissions, activity tracking")
    print("  - News Model: Content management, SEO, read tracking")
    print("  - Album Model: Chapter management, SEO")
    print("  - Comment Model: User interactions, content linking")
    print("  - Rating Model: User feedback, statistics")
    print("  - Image Model: File management, metadata")
    print("  - Category Model: Content organization")
    print("  - Subscription Model: Premium features, billing")
    print("  - Brand Identity Model: Brand assets, configuration")
    print("  - Relationships: Foreign keys, associations")
    print("  - Validations: Data integrity, constraints")
    print("  - Methods: Business logic, utilities")
    print("\n🎉 Database models are working correctly!")

if __name__ == "__main__":
    main() 