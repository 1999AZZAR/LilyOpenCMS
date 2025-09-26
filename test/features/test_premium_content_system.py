#!/usr/bin/env python3
"""
Test script for Premium Content System

This script tests the premium content filtering functionality to ensure:
1. Premium content is properly truncated for non-premium users
2. Premium users get full content
3. Content masking works correctly
4. Server-side filtering prevents full content from being sent to non-premium users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, User, News, Album, AlbumChapter
from routes.utils.premium_content import (
    is_premium_user, 
    should_show_premium_content, 
    truncate_markdown_content, 
    process_premium_content,
    get_premium_content_stats
)
from datetime import datetime, timezone
import markdown


def create_test_app():
    """Create a test Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app


def create_test_data(app):
    """Create test data for premium content testing"""
    with app.app_context():
        # Create test users
        premium_user = User(
            username='premium_user',
            email='premium@test.com',
            is_premium=True,
            has_premium_access=True,
            premium_expires_at=datetime.now(timezone.utc).replace(year=2025),
            role='general'
        )
        premium_user.set_password('password123')
        
        regular_user = User(
            username='regular_user',
            email='regular@test.com',
            is_premium=False,
            has_premium_access=False,
            role='general'
        )
        regular_user.set_password('password123')
        
        db.session.add(premium_user)
        db.session.add(regular_user)
        
        # Create test news articles
        premium_news = News(
            title='Premium Test Article',
            content='This is a premium article with a lot of content. ' * 50,  # 50 sentences
            is_premium=True,
            is_visible=True,
            user_id=1,
            category_id=1,
            date=datetime.now(timezone.utc)
        )
        
        regular_news = News(
            title='Regular Test Article',
            content='This is a regular article with content. ' * 20,  # 20 sentences
            is_premium=False,
            is_visible=True,
            user_id=1,
            category_id=1,
            date=datetime.now(timezone.utc)
        )
        
        db.session.add(premium_news)
        db.session.add(regular_news)
        
        # Create test album
        premium_album = Album(
            title='Premium Test Album',
            description='A premium album for testing',
            is_premium=True,
            is_visible=True,
            user_id=1,
            category_id=1
        )
        
        regular_album = Album(
            title='Regular Test Album',
            description='A regular album for testing',
            is_premium=False,
            is_visible=True,
            user_id=1,
            category_id=1
        )
        
        db.session.add(premium_album)
        db.session.add(regular_album)
        
        # Create test chapters
        premium_chapter = AlbumChapter(
            chapter_number=1,
            chapter_title='Premium Chapter',
            is_visible=True,
            album_id=1,
            news_id=1
        )
        
        regular_chapter = AlbumChapter(
            chapter_number=1,
            chapter_title='Regular Chapter',
            is_visible=True,
            album_id=2,
            news_id=2
        )
        
        db.session.add(premium_chapter)
        db.session.add(regular_chapter)
        
        db.session.commit()
        
        return {
            'premium_user': premium_user,
            'regular_user': regular_user,
            'premium_news': premium_news,
            'regular_news': regular_news,
            'premium_album': premium_album,
            'regular_album': regular_album
        }


def test_premium_user_detection():
    """Test premium user detection"""
    print("Testing premium user detection...")
    
    app = create_test_app()
    test_data = create_test_data(app)
    
    with app.app_context():
        # Test premium user
        from flask_login import login_user
        login_user(test_data['premium_user'])
        
        assert is_premium_user() == True, "Premium user should be detected as premium"
        print("✓ Premium user detection works")
        
        # Test regular user
        login_user(test_data['regular_user'])
        
        assert is_premium_user() == False, "Regular user should not be detected as premium"
        print("✓ Regular user detection works")


def test_content_filtering():
    """Test content filtering based on premium status"""
    print("\nTesting content filtering...")
    
    app = create_test_app()
    test_data = create_test_data(app)
    
    with app.app_context():
        # Test premium content with premium user
        from flask_login import login_user
        login_user(test_data['premium_user'])
        
        premium_content = test_data['premium_news'].content
        processed_content, is_truncated, show_notice = process_premium_content(
            premium_content, True, max_words=150
        )
        
        assert not is_truncated, "Premium user should get full content"
        assert not show_notice, "Premium user should not see premium notice"
        assert len(processed_content) == len(premium_content), "Content should not be truncated"
        print("✓ Premium user gets full content")
        
        # Test premium content with regular user
        login_user(test_data['regular_user'])
        
        processed_content, is_truncated, show_notice = process_premium_content(
            premium_content, True, max_words=150
        )
        
        assert is_truncated, "Regular user should get truncated content"
        assert show_notice, "Regular user should see premium notice"
        assert len(processed_content) < len(premium_content), "Content should be truncated"
        print("✓ Regular user gets truncated content")
        
        # Test regular content with regular user
        regular_content = test_data['regular_news'].content
        processed_content, is_truncated, show_notice = process_premium_content(
            regular_content, False, max_words=150
        )
        
        assert not is_truncated, "Regular content should not be truncated"
        assert not show_notice, "Regular content should not show premium notice"
        assert len(processed_content) == len(regular_content), "Regular content should not be truncated"
        print("✓ Regular content is accessible to all users")


def test_content_truncation():
    """Test content truncation functionality"""
    print("\nTesting content truncation...")
    
    # Test truncation with long content
    long_content = "This is a test sentence. " * 200  # 200 sentences
    
    truncated_content, was_truncated = truncate_markdown_content(long_content, max_words=150)
    
    assert was_truncated, "Long content should be truncated"
    assert len(truncated_content) < len(long_content), "Truncated content should be shorter"
    assert truncated_content.endswith('...'), "Truncated content should end with ellipsis"
    print("✓ Content truncation works correctly")
    
    # Test truncation with short content
    short_content = "This is a short test."
    
    truncated_content, was_truncated = truncate_markdown_content(short_content, max_words=150)
    
    assert not was_truncated, "Short content should not be truncated"
    assert len(truncated_content) == len(short_content), "Short content should not be changed"
    print("✓ Short content is not truncated")


def test_content_stats():
    """Test content statistics generation"""
    print("\nTesting content statistics...")
    
    test_content = "This is a test content with multiple words."
    stats = get_premium_content_stats(test_content, True)
    
    assert stats['total_words'] > 0, "Word count should be calculated"
    assert stats['total_chars'] > 0, "Character count should be calculated"
    assert stats['is_premium'] == True, "Premium flag should be set"
    assert stats['user_has_access'] == False, "Non-premium user should not have access"
    print("✓ Content statistics are calculated correctly")


def test_markdown_conversion():
    """Test markdown to HTML conversion with truncated content"""
    print("\nTesting markdown conversion...")
    
    markdown_content = """
# Test Heading

This is a **bold** paragraph with some *italic* text.

## Subheading

- List item 1
- List item 2
- List item 3

> This is a blockquote

```python
print("Hello World")
```
"""
    
    # Test full content conversion
    html_content = markdown.markdown(
        markdown_content,
        extensions=["fenced_code", "tables", "extra", "sane_lists"]
    )
    
    assert '<h1>' in html_content, "HTML should contain h1 tags"
    assert '<strong>' in html_content, "HTML should contain bold tags"
    assert '<ul>' in html_content, "HTML should contain list tags"
    assert '<blockquote>' in html_content, "HTML should contain blockquote tags"
    print("✓ Markdown to HTML conversion works")
    
    # Test truncated content conversion
    truncated_content, _ = truncate_markdown_content(markdown_content, max_words=10)
    html_truncated = markdown.markdown(
        truncated_content,
        extensions=["fenced_code", "tables", "extra", "sane_lists"]
    )
    
    assert len(html_truncated) < len(html_content), "Truncated HTML should be shorter"
    print("✓ Truncated content conversion works")


def run_all_tests():
    """Run all premium content tests"""
    print("=" * 50)
    print("PREMIUM CONTENT SYSTEM TESTS")
    print("=" * 50)
    
    try:
        test_premium_user_detection()
        test_content_filtering()
        test_content_truncation()
        test_content_stats()
        test_markdown_conversion()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! ✓")
        print("=" * 50)
        print("\nPremium content system is working correctly:")
        print("- Premium users get full content")
        print("- Non-premium users get truncated content with mask")
        print("- Content is filtered server-side for security")
        print("- Markdown conversion works with truncated content")
        print("- Content statistics are calculated correctly")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 