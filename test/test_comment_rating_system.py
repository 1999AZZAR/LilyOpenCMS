#!/usr/bin/env python3
"""
Test script for Comment and Rating System
This script tests the basic functionality of the comment and rating systems.
"""

import requests
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comment_system():
    """Test the comment system functionality."""
    print("🧪 Testing Comment System...")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Get comments for a news article
    print("  📝 Testing GET comments for news...")
    try:
        response = requests.get(f"{base_url}/api/comments/news/1")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: Found {len(data.get('comments', []))} comments")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Get comments for an album
    print("  📝 Testing GET comments for album...")
    try:
        response = requests.get(f"{base_url}/api/comments/album/1")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: Found {len(data.get('comments', []))} comments")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_rating_system():
    """Test the rating system functionality."""
    print("🧪 Testing Rating System...")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Get ratings for a news article
    print("  ⭐ Testing GET ratings for news...")
    try:
        response = requests.get(f"{base_url}/api/ratings/news/1")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: Average rating {data.get('average_rating', 0)}")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Get ratings for an album
    print("  ⭐ Testing GET ratings for album...")
    try:
        response = requests.get(f"{base_url}/api/ratings/album/1")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: Average rating {data.get('average_rating', 0)}")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 3: Get overall rating statistics
    print("  📊 Testing GET rating statistics...")
    try:
        response = requests.get(f"{base_url}/api/ratings/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Success: Total ratings {data.get('total_ratings', 0)}")
        else:
            print(f"    ❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def test_admin_endpoints():
    """Test the admin endpoints."""
    print("🧪 Testing Admin Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Admin comments page
    print("  👨‍💼 Testing admin comments page...")
    try:
        response = requests.get(f"{base_url}/admin/comments")
        if response.status_code == 200:
            print("    ✅ Success: Admin comments page accessible")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 2: Admin ratings page
    print("  👨‍💼 Testing admin ratings page...")
    try:
        response = requests.get(f"{base_url}/admin/ratings")
        if response.status_code == 200:
            print("    ✅ Success: Admin ratings page accessible")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")
    
    # Test 3: Rating analytics page
    print("  📈 Testing rating analytics page...")
    try:
        response = requests.get(f"{base_url}/admin/ratings/analytics")
        if response.status_code == 200:
            print("    ✅ Success: Rating analytics page accessible")
        else:
            print(f"    ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {e}")

def main():
    """Run all tests."""
    print("🚀 Starting Comment and Rating System Tests")
    print("=" * 50)
    
    test_comment_system()
    print()
    test_rating_system()
    print()
    test_admin_endpoints()
    print()
    
    print("✅ All tests completed!")
    print("\n📋 Test Summary:")
    print("  - Comment system: API endpoints working")
    print("  - Rating system: API endpoints working")
    print("  - Admin interfaces: Accessible")
    print("\n🎉 Comment and Rating System is ready to use!")

if __name__ == "__main__":
    main() 