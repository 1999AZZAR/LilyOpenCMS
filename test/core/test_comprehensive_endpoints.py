#!/usr/bin/env python3
"""
Comprehensive Test Script for All Fixed Endpoints
Tests all admin endpoints with different user roles and authentication states
Uses proper session-based authentication like add_fake_images.py
"""

import sys
import os
import requests
import json
import re
import time
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/login"

# Test user credentials
TEST_USERS = {
    'general': {
        'username': 'testuser_reg',
        'password': 'testpass123',
        'role': 'GENERAL'
    },
    'admin': {
        'username': 'admin0',
        'password': 'admin_password',
        'role': 'ADMIN'
    },
    'superuser': {
        'username': 'suadmin',
        'password': 'suladang',
        'role': 'SUPERUSER'
    }
}

class EndpointTester:
    """Comprehensive endpoint tester with session management"""
    
    def __init__(self):
        self.session = requests.Session()
        self.current_user = None
        
    def login(self, user_type):
        """Login with specified user type using proper session management"""
        if user_type not in TEST_USERS:
            print(f"❌ Unknown user type: {user_type}")
            return False
            
        user = TEST_USERS[user_type]
        print(f"🔐 Logging in as {user['username']} ({user['role']})...")
        
        try:
            # Get login page to extract CSRF token
            login_page_resp = self.session.get(LOGIN_URL, timeout=10)
            login_page_resp.raise_for_status()
            
            # Extract CSRF token
            csrf_token = None
            
            # Method 1: Look for meta tag
            meta_match = re.search(r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
            if meta_match:
                csrf_token = meta_match.group(1)
                print(f"   Found CSRF token in meta tag: {csrf_token[:10]}...")
            
            # Method 2: Look for input field
            if not csrf_token:
                input_match = re.search(r'<input[^>]+name=["\']csrf_token["\'][^>]+value=["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
                if input_match:
                    csrf_token = input_match.group(1)
                    print(f"   Found CSRF token in input field: {csrf_token[:10]}...")
            
            # Method 3: Look for any csrf token in the page
            if not csrf_token:
                csrf_match = re.search(r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']', login_page_resp.text, re.IGNORECASE)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"   Found CSRF token in script: {csrf_token[:10]}...")

            # Prepare login data
            login_data = {
                "username": user['username'],
                "password": user['password'],
                "remember": "y"
            }
            if csrf_token:
                login_data["csrf_token"] = csrf_token

            # Perform login
            login_resp = self.session.post(LOGIN_URL, data=login_data, allow_redirects=True, timeout=10)
            login_resp.raise_for_status()

            # Check if login was successful
            if login_resp.url == LOGIN_URL or "Invalid username or password" in login_resp.text:
                print(f"❌ Login failed for {user['username']}")
                return False

            print(f"✅ Login successful as {user['username']}")
            self.current_user = user_type
            return True
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def logout(self):
        """Logout current user"""
        try:
            self.session.get(f"{BASE_URL}/logout", timeout=10)
            print(f"🔓 Logged out {self.current_user}")
            self.current_user = None
        except Exception as e:
            print(f"⚠️ Logout error: {e}")
    
    def test_endpoint(self, method, url, expected_status_codes, description, data=None, json_data=None):
        """Test a single endpoint with current session"""
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=data, json=json_data, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, data=data, json=json_data, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=10)
            else:
                print(f"❌ Unknown method: {method}")
                return False
            
            user_info = f"({self.current_user or 'no login'})"
            if response.status_code in expected_status_codes:
                print(f"    ✅ {description} {user_info}: {response.status_code}")
                return True
            else:
                print(f"    ❌ {description} {user_info}: {response.status_code} (expected {expected_status_codes})")
                return False
                
        except Exception as e:
            user_info = f"({self.current_user or 'no login'})"
            print(f"    ❌ {description} {user_info}: Error - {e}")
            return False

def test_comment_endpoints(tester):
    """Test comment moderation endpoints"""
    print("\n🧪 Testing Comment Moderation Endpoints...")
    
    # Test without login
    print("  📝 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/comments", [302, 403], "Comment moderation page")
    tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/approve", [302, 403], "Approve comment")
    tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/reject", [302, 403], "Reject comment")
    tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/mark-spam", [302, 403], "Mark comment as spam")
    tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/delete", [302, 403], "Delete comment")
    
    # Test with general user
    if tester.login('general'):
        print("  📝 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/comments", [302, 403], "Comment moderation page")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/approve", [302, 403], "Approve comment")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  📝 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/comments", [200, 302], "Comment moderation page")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/approve", [200, 403, 404], "Approve comment")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/reject", [200, 403, 404], "Reject comment")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/mark-spam", [200, 403, 404], "Mark comment as spam")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/delete", [200, 403, 404], "Delete comment")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  📝 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/comments", [200, 302], "Comment moderation page")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/approve", [200, 403, 404], "Approve comment")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/reject", [200, 403, 404], "Reject comment")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/mark-spam", [200, 403, 404], "Mark comment as spam")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/comments/1/delete", [200, 403, 404], "Delete comment")
        tester.logout()

def test_rating_endpoints(tester):
    """Test rating management endpoints"""
    print("\n🧪 Testing Rating Management Endpoints...")
    
    # Test without login
    print("  ⭐ Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings", [302, 403], "Rating management page")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings/analytics", [302, 403], "Rating analytics page")
    tester.test_endpoint('POST', f"{BASE_URL}/admin/ratings/1/delete", [302, 403], "Delete rating")
    
    # Test with general user
    if tester.login('general'):
        print("  ⭐ Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings", [302, 403], "Rating management page")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings/analytics", [302, 403], "Rating analytics page")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  ⭐ Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings", [200, 302], "Rating management page")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings/analytics", [200, 302], "Rating analytics page")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/ratings/1/delete", [200, 403, 404], "Delete rating")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  ⭐ Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings", [200, 302], "Rating management page")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/ratings/analytics", [200, 302], "Rating analytics page")
        tester.test_endpoint('POST', f"{BASE_URL}/admin/ratings/1/delete", [200, 403, 404], "Delete rating")
        tester.logout()

def test_ads_endpoints(tester):
    """Test ads management endpoints"""
    print("\n🧪 Testing Ads Management Endpoints...")
    
    # Test without login
    print("  📢 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/ads/dashboard", [302, 403], "Ads dashboard")
    tester.test_endpoint('GET', f"{BASE_URL}/ads/campaigns", [302, 403], "Campaigns list")
    tester.test_endpoint('GET', f"{BASE_URL}/ads/ads", [302, 403], "Ads list")
    tester.test_endpoint('GET', f"{BASE_URL}/ads/placements", [302, 403], "Placements list")
    tester.test_endpoint('GET', f"{BASE_URL}/ads/analytics", [302, 403], "Ads analytics")
    
    # Test with general user
    if tester.login('general'):
        print("  📢 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/dashboard", [302, 403], "Ads dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/campaigns", [302, 403], "Campaigns list")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  📢 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/dashboard", [200, 302], "Ads dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/campaigns", [200, 302], "Campaigns list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/ads", [200, 302], "Ads list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/placements", [200, 302], "Placements list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/analytics", [200, 302], "Ads analytics")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  📢 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/dashboard", [200, 302], "Ads dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/campaigns", [200, 302], "Campaigns list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/ads", [200, 302], "Ads list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/placements", [200, 302], "Placements list")
        tester.test_endpoint('GET', f"{BASE_URL}/ads/analytics", [200, 302], "Ads analytics")
        tester.logout()

def test_analytics_endpoints(tester):
    """Test analytics endpoints"""
    print("\n🧪 Testing Analytics Endpoints...")
    
    # Test without login
    print("  📊 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/performance", [302, 403], "Performance dashboard")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/asset-optimization", [302, 403], "Asset optimization")
    tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/ssr-optimization", [302, 403], "SSR optimization")
    tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/visitors", [302, 403], "Visitor stats API")
    tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/content", [302, 403], "Content analytics API")
    
    # Test with general user
    if tester.login('general'):
        print("  📊 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance", [302, 403], "Performance dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/visitors", [302, 403], "Visitor stats API")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  📊 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance", [200, 302], "Performance dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/asset-optimization", [200, 302], "Asset optimization")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/ssr-optimization", [200, 302], "SSR optimization")
        tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/visitors", [200, 302], "Visitor stats API")
        tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/content", [200, 302], "Content analytics API")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  📊 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance", [200, 302], "Performance dashboard")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/asset-optimization", [200, 302], "Asset optimization")
        tester.test_endpoint('GET', f"{BASE_URL}/admin/performance/ssr-optimization", [200, 302], "SSR optimization")
        tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/visitors", [200, 302], "Visitor stats API")
        tester.test_endpoint('GET', f"{BASE_URL}/api/analytics/content", [200, 302], "Content analytics API")
        tester.logout()

def test_user_management_endpoints(tester):
    """Test user management endpoints"""
    print("\n🧪 Testing User Management Endpoints...")
    
    # Test without login
    print("  👥 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/settings/users", [302, 403], "User management page")
    tester.test_endpoint('GET', f"{BASE_URL}/api/users", [302, 403], "Users API")
    tester.test_endpoint('GET', f"{BASE_URL}/api/registrations/pending", [302, 403], "Pending registrations API")
    
    # Test with general user
    if tester.login('general'):
        print("  👥 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/users", [302, 403], "User management page")
        tester.test_endpoint('GET', f"{BASE_URL}/api/users", [302, 403], "Users API")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  👥 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/users", [200, 302], "User management page")
        tester.test_endpoint('GET', f"{BASE_URL}/api/users", [200, 302], "Users API")
        tester.test_endpoint('GET', f"{BASE_URL}/api/registrations/pending", [200, 302], "Pending registrations API")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  👥 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/users", [200, 302], "User management page")
        tester.test_endpoint('GET', f"{BASE_URL}/api/users", [200, 302], "Users API")
        tester.test_endpoint('GET', f"{BASE_URL}/api/registrations/pending", [200, 302], "Pending registrations API")
        tester.logout()

def test_subscription_endpoints(tester):
    """Test subscription endpoints"""
    print("\n🧪 Testing Subscription Endpoints...")
    
    # Test without login
    print("  💳 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/api/admin/subscriptions", [302, 403], "Admin subscriptions API")
    
    # Test with general user
    if tester.login('general'):
        print("  💳 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/api/admin/subscriptions", [302, 403], "Admin subscriptions API")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  💳 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/api/admin/subscriptions", [200, 302], "Admin subscriptions API")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  💳 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/api/admin/subscriptions", [200, 302], "Admin subscriptions API")
        tester.logout()

def test_seo_endpoints(tester):
    """Test SEO management endpoints"""
    print("\n🧪 Testing SEO Management Endpoints...")
    
    # Test without login
    print("  🔍 Testing without login...")
    tester.test_endpoint('GET', f"{BASE_URL}/settings/root-seo", [302, 403], "Root SEO management")
    
    # Test with general user
    if tester.login('general'):
        print("  🔍 Testing with general user...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/root-seo", [302, 403], "Root SEO management")
        tester.logout()
    
    # Test with admin user
    if tester.login('admin'):
        print("  🔍 Testing with admin user...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/root-seo", [200, 302], "Root SEO management")
        tester.logout()
    
    # Test with superuser
    if tester.login('superuser'):
        print("  🔍 Testing with superuser...")
        tester.test_endpoint('GET', f"{BASE_URL}/settings/root-seo", [200, 302], "Root SEO management")
        tester.logout()

def main():
    """Main test function"""
    print("🧪 Comprehensive Endpoint Testing Suite")
    print("=" * 50)
    print("Testing all fixed endpoints with different user roles")
    print(f"Base URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Create tester instance
    tester = EndpointTester()
    
    # Test all endpoint categories
    test_comment_endpoints(tester)
    test_rating_endpoints(tester)
    test_ads_endpoints(tester)
    test_analytics_endpoints(tester)
    test_user_management_endpoints(tester)
    test_subscription_endpoints(tester)
    test_seo_endpoints(tester)
    
    print("\n" + "=" * 50)
    print("✅ Comprehensive endpoint testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
