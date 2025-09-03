#!/usr/bin/env python3
"""
Test script for the new public API endpoints.
Run this script to verify that all endpoints are working correctly.
"""

import requests
import json
import sys
from urllib.parse import urljoin

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your server runs on a different port
API_BASE = urljoin(BASE_URL, "/api/public/")

def test_endpoint(endpoint, description, expected_status=200):
    """Test a single API endpoint."""
    url = urljoin(API_BASE, endpoint)
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            print(f"   ✅ PASSED")
            if response.headers.get('content-type', '').startswith('application/json'):
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'error' in data:
                        print(f"   ⚠️  Response contains error: {data['error']}")
                    else:
                        print(f"   📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                except json.JSONDecodeError:
                    print(f"   ⚠️  Response is not valid JSON")
            else:
                print(f"   ⚠️  Response is not JSON: {response.headers.get('content-type')}")
        else:
            print(f"   ❌ FAILED - Expected {expected_status}, got {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
        
        return response.status_code == expected_status
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILED - Request error: {e}")
        return False

def test_search_endpoint():
    """Test the search endpoint with a query parameter."""
    url = urljoin(API_BASE, "search")
    params = {"q": "test"}
    
    print(f"\n🔍 Testing: Search API with query parameter")
    print(f"   URL: {url}")
    print(f"   Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ PASSED")
            try:
                data = response.json()
                print(f"   📊 Response keys: {list(data.keys())}")
                print(f"   🔍 Search query: {data.get('query')}")
                print(f"   📊 Total results: {data.get('total_results')}")
            except json.JSONDecodeError:
                print(f"   ⚠️  Response is not valid JSON")
        else:
            print(f"   ❌ FAILED - Expected 200, got {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ FAILED - Request error: {e}")
        return False

def main():
    """Run all API endpoint tests."""
    print("🚀 Testing Public API Endpoints")
    print("=" * 50)
    
    # Test results tracking
    passed = 0
    total = 0
    
    # Test endpoints that should return 200 (or 404 for non-existent resources)
    endpoints = [
        ("news", "News List API", 200),
        ("news/999999", "News Detail API (Non-existent)", 404),
        ("albums", "Albums List API", 200),
        ("albums/999999", "Album Detail API (Non-existent)", 404),
        ("albums/999999/chapters/999999", "Chapter Detail API (Non-existent)", 404),
        ("user/nonexistentuser", "User Profile API (Non-existent)", 404),
        ("user/nonexistentuser/stats", "User Stats API (Non-existent)", 404),
        ("user/nonexistentuser/library", "User Library API (Non-existent)", 404),
        ("categories", "Categories API", 200),
        ("tags", "Tags API", 200),
        ("comments/news/999999", "Comments API (Non-existent news)", 404),
    ]
    
    # Test each endpoint
    for endpoint, description, expected_status in endpoints:
        if test_endpoint(endpoint, description, expected_status):
            passed += 1
        total += 1
    
    # Test search endpoint separately
    if test_search_endpoint():
        passed += 1
    total += 1
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The public API endpoints are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())