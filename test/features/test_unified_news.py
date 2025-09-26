#!/usr/bin/env python3
"""
Test script for the unified news system
"""

import requests
import json

def test_unified_news_api():
    """Test the unified news API endpoint"""
    
    base_url = "http://localhost:5000"
    
    # Test cases
    test_cases = [
        {
            "name": "General news",
            "params": {},
            "expected_type": "general"
        },
        {
            "name": "Hypes (popular content)",
            "params": {"type": "hypes"},
            "expected_type": "hypes"
        },
        {
            "name": "Articles only",
            "params": {"type": "articles"},
            "expected_type": "articles"
        },
        {
            "name": "Utama (main news)",
            "params": {"type": "utama"},
            "expected_type": "utama"
        },
        {
            "name": "Search with query",
            "params": {"q": "test"},
            "expected_type": "general"
        },
        {
            "name": "Category filter",
            "params": {"category": "1"},
            "expected_type": "general"
        },
        {
            "name": "Tag filter",
            "params": {"tag": "technology"},
            "expected_type": "general"
        },
        {
            "name": "Sort by popularity",
            "params": {"sort": "popular"},
            "expected_type": "general"
        }
    ]
    
    print("Testing unified news API...")
    print("=" * 50)
    
    for test_case in test_cases:
        try:
            response = requests.get(f"{base_url}/api/search/news", params=test_case["params"])
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ {test_case['name']}: PASSED")
                    print(f"   - Type: {data['search_info']['type']}")
                    print(f"   - Total count: {data['search_info']['total_count']}")
                    print(f"   - Results: {len(data['news'])}")
                else:
                    print(f"❌ {test_case['name']}: FAILED - API returned error")
                    print(f"   - Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ {test_case['name']}: FAILED - HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {test_case['name']}: FAILED - Could not connect to server")
        except Exception as e:
            print(f"❌ {test_case['name']}: FAILED - {str(e)}")
        
        print()
    
    print("Testing URL redirects...")
    print("=" * 50)
    
    redirect_tests = [
        {"url": "/hypes", "expected_redirect": "/news?type=hypes"},
        {"url": "/articles", "expected_redirect": "/news?type=articles"},
        {"url": "/utama", "expected_redirect": "/news?type=utama"},
        {"url": "/search?q=test", "expected_redirect": "/news?q=test"},
        {"url": "/search?category=tech", "expected_redirect": "/news?category=tech"},
        {"url": "/search?tag=news", "expected_redirect": "/news?tag=news"},
    ]
    
    for test in redirect_tests:
        try:
            response = requests.get(f"{base_url}{test['url']}", allow_redirects=False)
            
            if response.status_code in [301, 302]:
                redirect_url = response.headers.get('Location', '')
                if test['expected_redirect'] in redirect_url:
                    print(f"✅ Redirect {test['url']}: PASSED")
                    print(f"   - Redirects to: {redirect_url}")
                else:
                    print(f"❌ Redirect {test['url']}: FAILED")
                    print(f"   - Expected: {test['expected_redirect']}")
                    print(f"   - Got: {redirect_url}")
            else:
                print(f"❌ Redirect {test['url']}: FAILED - No redirect (status {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Redirect {test['url']}: FAILED - Could not connect to server")
        except Exception as e:
            print(f"❌ Redirect {test['url']}: FAILED - {str(e)}")
        
        print()

if __name__ == "__main__":
    test_unified_news_api() 