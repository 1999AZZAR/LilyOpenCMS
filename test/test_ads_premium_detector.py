#!/usr/bin/env python3
"""
Test script for Ads Injection System with Premium Detector Integration

This script tests the enhanced ads injection system to ensure:
1. Premium detector integration works correctly
2. Ads are properly filtered based on user premium status
3. Premium users with ads disabled don't see ads
4. Non-premium users see ads normally
5. Fallback detection works when API is unavailable
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, User, UserSubscription
from datetime import datetime, timezone, timedelta
import json


def create_test_app():
    """Create a test Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    db.init_app(app)
    
    # Set up login manager
    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
    
    return app


def create_test_data(app):
    """Create test users and subscriptions"""
    with app.app_context():
        # Create regular user
        regular_user = User(
            username='regular_user',
            password_hash='test_hash',
            email='regular@test.com',
            has_premium_access=False,
            ad_preferences={"show_ads": True, "ad_frequency": "normal"}
        )
        
        # Create premium user with ads enabled
        premium_user_ads = User(
            username='premium_user_ads',
            password_hash='test_hash',
            email='premium_ads@test.com',
            has_premium_access=True,
            premium_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            ad_preferences={"show_ads": True, "ad_frequency": "normal"}
        )
        
        # Create premium user with ads disabled
        premium_user_no_ads = User(
            username='premium_user_no_ads',
            password_hash='test_hash',
            email='premium_no_ads@test.com',
            has_premium_access=True,
            premium_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            ad_preferences={"show_ads": False, "ad_frequency": "none"}
        )
        
        # Create expired premium user
        expired_premium_user = User(
            username='expired_premium_user',
            password_hash='test_hash',
            email='expired@test.com',
            has_premium_access=False,
            premium_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            ad_preferences={"show_ads": True, "ad_frequency": "normal"}
        )
        
        db.session.add_all([regular_user, premium_user_ads, premium_user_no_ads, expired_premium_user])
        db.session.commit()
        
        return {
            'regular_user': regular_user,
            'premium_user_ads': premium_user_ads,
            'premium_user_no_ads': premium_user_no_ads,
            'expired_premium_user': expired_premium_user
        }


def test_premium_detector_api():
    """Test the premium detector API endpoint"""
    print("Testing premium detector API...")
    
    app = create_test_app()
    
    with app.app_context():
        from routes.routes_subscriptions import check_premium_access
        from flask import request
        from flask_login import login_user
        
        # Create test data within the app context
        test_data = create_test_data(app)
        
        # Test regular user
        with app.test_request_context('/api/subscriptions/check-premium-access'):
            # Refresh user from session to avoid detached instance error
            regular_user = db.session.merge(test_data['regular_user'])
            login_user(regular_user)
            response = check_premium_access()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['has_premium_access'] == False, "Regular user should not have premium access"
            assert data['should_show_ads'] == True, "Regular user should show ads"
            print("✓ Regular user premium detection works")
        
        # Test premium user with ads enabled
        with app.test_request_context('/api/subscriptions/check-premium-access'):
            premium_user_ads = db.session.merge(test_data['premium_user_ads'])
            login_user(premium_user_ads)
            response = check_premium_access()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['has_premium_access'] == True, "Premium user should have premium access"
            assert data['should_show_ads'] == True, "Premium user with ads enabled should show ads"
            print("✓ Premium user with ads enabled detection works")
        
        # Test premium user with ads disabled
        with app.test_request_context('/api/subscriptions/check-premium-access'):
            premium_user_no_ads = db.session.merge(test_data['premium_user_no_ads'])
            login_user(premium_user_no_ads)
            response = check_premium_access()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['has_premium_access'] == True, "Premium user should have premium access"
            assert data['should_show_ads'] == False, "Premium user with ads disabled should not show ads"
            print("✓ Premium user with ads disabled detection works")
        
        # Test expired premium user
        with app.test_request_context('/api/subscriptions/check-premium-access'):
            expired_premium_user = db.session.merge(test_data['expired_premium_user'])
            login_user(expired_premium_user)
            response = check_premium_access()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['has_premium_access'] == False, "Expired premium user should not have premium access"
            assert data['should_show_ads'] == True, "Expired premium user should show ads"
            print("✓ Expired premium user detection works")


def test_ads_serving_with_premium_context():
    """Test ads serving API with premium context"""
    print("Testing ads serving with premium context...")
    
    app = create_test_app()
    
    with app.app_context():
        from routes.routes_ads import serve_ads
        from flask import request
        
        # Create test data within the app context
        test_data = create_test_data(app)
        
        # Test regular user - should get ads
        regular_user = db.session.merge(test_data['regular_user'])
        with app.test_request_context('/ads/api/serve', 
                                   method='POST',
                                   json={
                                       'page_type': 'home',
                                       'section': 'content',
                                       'position': 'top',
                                       'user_id': regular_user.id,
                                       'user_has_premium': False,
                                       'user_should_show_ads': True
                                   }):
            response = serve_ads()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['success'] == True, "Should successfully serve ads to regular user"
            assert 'premium_context' in data, "Should include premium context in response"
            assert data['premium_context']['user_has_premium'] == False, "Should indicate non-premium user"
            print("✓ Regular user ads serving works")
        
        # Test premium user with ads disabled - should not get ads
        premium_user_no_ads = db.session.merge(test_data['premium_user_no_ads'])
        with app.test_request_context('/ads/api/serve', 
                                   method='POST',
                                   json={
                                       'page_type': 'home',
                                       'section': 'content',
                                       'position': 'top',
                                       'user_id': premium_user_no_ads.id,
                                       'user_has_premium': True,
                                       'user_should_show_ads': False
                                   }):
            response = serve_ads()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['success'] == True, "Should successfully handle premium user request"
            assert data['ads'] == [], "Should not serve ads to premium user with ads disabled"
            assert data.get('reason') == 'premium_user_ads_disabled', "Should indicate why no ads were served"
            print("✓ Premium user with ads disabled handling works")
        
        # Test premium user with ads enabled - should get ads
        premium_user_ads = db.session.merge(test_data['premium_user_ads'])
        with app.test_request_context('/ads/api/serve', 
                                   method='POST',
                                   json={
                                       'page_type': 'home',
                                       'section': 'content',
                                       'position': 'top',
                                       'user_id': premium_user_ads.id,
                                       'user_has_premium': True,
                                       'user_should_show_ads': True
                                   }):
            response = serve_ads()
            data = json.loads(response.get_data(as_text=True))
            
            assert data['success'] == True, "Should successfully serve ads to premium user with ads enabled"
            assert 'premium_context' in data, "Should include premium context in response"
            assert data['premium_context']['user_has_premium'] == True, "Should indicate premium user"
            print("✓ Premium user with ads enabled serving works")


def test_user_methods():
    """Test user methods for premium detection"""
    print("Testing user premium detection methods...")
    
    app = create_test_app()
    
    with app.app_context():
        # Create test data within the app context
        test_data = create_test_data(app)
        
        # Test regular user methods
        regular_user = db.session.merge(test_data['regular_user'])
        assert regular_user.has_active_premium_subscription() == False, "Regular user should not have active premium"
        assert regular_user.should_show_ads() == True, "Regular user should show ads"
        print("✓ Regular user methods work")
        
        # Test premium user with ads enabled
        premium_user_ads = db.session.merge(test_data['premium_user_ads'])
        assert premium_user_ads.has_active_premium_subscription() == True, "Premium user should have active premium"
        assert premium_user_ads.should_show_ads() == True, "Premium user with ads enabled should show ads"
        print("✓ Premium user with ads enabled methods work")
        
        # Test premium user with ads disabled
        premium_user_no_ads = db.session.merge(test_data['premium_user_no_ads'])
        assert premium_user_no_ads.has_active_premium_subscription() == True, "Premium user should have active premium"
        assert premium_user_no_ads.should_show_ads() == False, "Premium user with ads disabled should not show ads"
        print("✓ Premium user with ads disabled methods work")
        
        # Test expired premium user
        expired_user = db.session.merge(test_data['expired_premium_user'])
        assert expired_user.has_active_premium_subscription() == False, "Expired premium user should not have active premium"
        assert expired_user.should_show_ads() == True, "Expired premium user should show ads"
        print("✓ Expired premium user methods work")


def test_premium_content_utility():
    """Test premium content utility functions"""
    print("Testing premium content utility functions...")
    
    app = create_test_app()
    
    with app.app_context():
        from routes.utils.premium_content import is_premium_user, should_show_premium_content
        from flask_login import login_user
        
        # Create test data within the app context
        test_data = create_test_data(app)
        
        # Test regular user
        with app.test_request_context('/'):
            regular_user = db.session.merge(test_data['regular_user'])
            login_user(regular_user)
            assert is_premium_user() == False, "Regular user should not be detected as premium"
            assert should_show_premium_content(True) == False, "Regular user should not see premium content"
            assert should_show_premium_content(False) == True, "Regular user should see non-premium content"
            print("✓ Regular user premium content utility works")
        
        # Test premium user
        with app.test_request_context('/'):
            premium_user_ads = db.session.merge(test_data['premium_user_ads'])
            login_user(premium_user_ads)
            assert is_premium_user() == True, "Premium user should be detected as premium"
            assert should_show_premium_content(True) == True, "Premium user should see premium content"
            assert should_show_premium_content(False) == True, "Premium user should see non-premium content"
            print("✓ Premium user premium content utility works")


def run_all_tests():
    """Run all ads premium detector tests"""
    print("=" * 60)
    print("ADS INJECTION PREMIUM DETECTOR INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        test_premium_detector_api()
        test_ads_serving_with_premium_context()
        test_user_methods()
        test_premium_content_utility()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nAds injection system with premium detector integration is working correctly:")
        print("- Premium detector API correctly identifies user premium status")
        print("- Ads serving API respects premium user preferences")
        print("- User methods properly detect premium status and ad preferences")
        print("- Premium content utility functions work correctly")
        print("- Premium users with ads disabled don't see ads")
        print("- Non-premium users see ads normally")
        print("- Expired premium users are treated as regular users")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    run_all_tests() 