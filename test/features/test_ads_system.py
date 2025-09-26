#!/usr/bin/env python3
"""
Test script for Ads System
Tests ads injection, API endpoints, and system functionality
"""

import sys
import os
import requests
import json
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ads_api_endpoints():
    """Test ads API endpoints"""
    print("🧪 Testing Ads API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test 1: Basic API call
    print("  📡 Testing ads API...")
    try:
        response = requests.post(f"{base_url}/ads/api/serve", json={
            "page_type": "home",
            "section": "content",
            "position": "after_n_items",
            "position_value": 3,
            "device_type": "desktop",
            "max_ads": 1
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                ads = data.get('ads', [])
                print(f"    ✅ API working: {len(ads)} ads found")
                for ad in ads:
                    print(f"      - Ad ID: {ad['ad_id']}")
            else:
                print(f"    ❌ API error: {data.get('error', 'Unknown error')}")
        else:
            print(f"    ❌ HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Request failed: {e}")
    
    # Test 2: Check ads dashboard
    print("  🗄️ Testing ads dashboard...")
    try:
        response = requests.get(f"{base_url}/ads/dashboard", timeout=5)
        if response.status_code == 200:
            print("    ✅ Ads dashboard accessible")
        else:
            print(f"    ❌ Dashboard error: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Dashboard request failed: {e}")

def test_ads_injection_system():
    """Test the ads injection system across different pages"""
    print("🧪 Testing Ads Injection System...")
    
    base_url = "http://localhost:5000"
    
    # Test pages to check
    test_pages = [
        "/",
        "/news",
        "/albums"
    ]
    
    for page in test_pages:
        print(f"  📄 Testing page: {page}")
        
        try:
            # Test ads API directly
            response = requests.post(f"{base_url}/ads/api/serve", json={
                "page_type": "home" if page == "/" else page[1:],
                "section": "content",
                "position": "after_n_items",
                "position_value": 3,
                "device_type": "desktop",
                "max_ads": 2
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    ads = data.get('ads', [])
                    print(f"    ✅ API Response: {len(ads)} ads found")
                    for ad in ads:
                        print(f"      - Ad ID: {ad['ad_id']}, Position: {ad['position']}")
                else:
                    print(f"    ❌ API Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"    ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"    ❌ Request failed: {e}")

def test_ads_campaigns():
    """Test ads campaigns functionality"""
    print("🧪 Testing Ads Campaigns...")
    
    base_url = "http://localhost:5000"
    
    # Test campaigns endpoint
    print("  🎯 Testing campaigns endpoint...")
    try:
        response = requests.get(f"{base_url}/ads/campaigns", timeout=5)
        if response.status_code == 200:
            print("    ✅ Campaigns page accessible")
        else:
            print(f"    ❌ Campaigns error: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Campaigns request failed: {e}")
    
    # Test ads management endpoint
    print("  📢 Testing ads management...")
    try:
        response = requests.get(f"{base_url}/ads/ads", timeout=5)
        if response.status_code == 200:
            print("    ✅ Ads management page accessible")
        else:
            print(f"    ❌ Ads management error: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Ads management request failed: {e}")

def test_ads_placements():
    """Test ads placements functionality"""
    print("🧪 Testing Ads Placements...")
    
    base_url = "http://localhost:5000"
    
    # Test placements endpoint
    print("  📍 Testing placements endpoint...")
    try:
        response = requests.get(f"{base_url}/ads/placements", timeout=5)
        if response.status_code == 200:
            print("    ✅ Placements page accessible")
        else:
            print(f"    ❌ Placements error: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Placements request failed: {e}")
    
    # Test analytics endpoint
    print("  📊 Testing analytics endpoint...")
    try:
        response = requests.get(f"{base_url}/ads/analytics", timeout=5)
        if response.status_code == 200:
            print("    ✅ Analytics page accessible")
        else:
            print(f"    ❌ Analytics error: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Analytics request failed: {e}")

def test_ads_performance():
    """Test ads performance and response times"""
    print("🧪 Testing Ads Performance...")
    
    base_url = "http://localhost:5000"
    
    # Test response time
    print("  ⚡ Testing response time...")
    try:
        start_time = time.time()
        response = requests.post(f"{base_url}/ads/api/serve", json={
            "page_type": "home",
            "section": "content",
            "position": "after_n_items",
            "position_value": 3,
            "device_type": "desktop",
            "max_ads": 1
        }, timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        if response.status_code == 200:
            print(f"    ✅ API response time: {response_time:.3f}s")
            if response_time < 1.0:
                print("    ✅ Response time is acceptable (< 1s)")
            else:
                print("    ⚠️ Response time is slow (> 1s)")
        else:
            print(f"    ❌ API failed: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Performance test failed: {e}")

def test_ads_error_handling():
    """Test ads error handling"""
    print("🧪 Testing Ads Error Handling...")
    
    base_url = "http://localhost:5000"
    
    # Test invalid page type
    print("  ⚠️ Testing invalid page type...")
    try:
        response = requests.post(f"{base_url}/ads/api/serve", json={
            "page_type": "invalid_page",
            "section": "content",
            "position": "after_n_items",
            "position_value": 3,
            "device_type": "desktop",
            "max_ads": 1
        }, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print("    ✅ Invalid page type properly handled")
            else:
                print("    ⚠️ Invalid page type not properly handled")
        else:
            print(f"    ✅ Invalid page type returned error: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Error handling test failed: {e}")
    
    # Test missing parameters
    print("  ⚠️ Testing missing parameters...")
    try:
        response = requests.post(f"{base_url}/ads/api/serve", json={}, timeout=5)
        
        if response.status_code == 400:
            print("    ✅ Missing parameters properly handled")
        else:
            print(f"    ⚠️ Missing parameters returned: {response.status_code}")
            
    except Exception as e:
        print(f"    ❌ Missing parameters test failed: {e}")

def main():
    """Run all ads system tests"""
    print("🚀 Starting Ads System Tests")
    print("=" * 50)
    
    test_ads_api_endpoints()
    print()
    test_ads_injection_system()
    print()
    test_ads_campaigns()
    print()
    test_ads_placements()
    print()
    test_ads_performance()
    print()
    test_ads_error_handling()
    print()
    
    print("✅ All ads system tests completed!")
    print("\n📋 Test Summary:")
    print("  - API Endpoints: Basic ads API functionality")
    print("  - Injection System: Ads injection across different pages")
    print("  - Campaigns: Campaign management functionality")
    print("  - Placements: Placement management and analytics")
    print("  - Performance: Response time and performance testing")
    print("  - Error Handling: Invalid inputs and error scenarios")
    print("\n🌐 Manual Testing Instructions:")
    print("  1. Visit http://localhost:5000 and refresh multiple times")
    print("  2. Check browser console (F12) for ads injection logs")
    print("  3. Look for ads in different positions and sections")
    print("  4. Test on different devices (mobile/desktop)")
    print("  5. Visit /ads/dashboard for admin interface")
    print("  6. Visit /ads/analytics for performance metrics")
    print("\n🎉 Ads system is ready for testing!")

if __name__ == "__main__":
    main() 