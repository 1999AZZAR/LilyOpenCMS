#!/usr/bin/env python3
"""
Test script for ads system functionality
"""

import os
import sys
from datetime import datetime
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ads_system():
    """Test the ads system functionality"""
    print("🧪 Testing Ads System")
    print("="*50)

    base_url = 'http://localhost:5000'
    session = requests.Session()

    # 1. Test Login
    print("\n1. Testing Login...")
    login_url = f'{base_url}/login'
    login_data = {
        'username': 'suadmin',
        'password': 'suladang'
    }

    try:
        response = session.post(login_url, data=login_data, allow_redirects=False)
        print(f"   Login Status: {response.status_code}")

        if response.status_code == 302:
            print("   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {response.text[:100]}")
            return False

    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False

    # 2. Test Ads Dashboard
    print("\n2. Testing Ads Dashboard...")
    dashboard_url = f'{base_url}/ads/dashboard'

    try:
        response = session.get(dashboard_url)
        print(f"   Dashboard Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Dashboard accessible")
        else:
            print(f"   ❌ Dashboard error: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Dashboard connection error: {e}")
        return False

    # 3. Test Ads API Endpoints
    print("\n3. Testing Ads API Endpoints...")

    # Test serve ads endpoint
    serve_url = f'{base_url}/ads/api/serve'
    serve_data = {
        'page_type': 'home',
        'section': 'sidebar',
        'position': 'top',
        'max_ads': 1
    }

    try:
        response = session.post(serve_url, json=serve_data)
        print(f"   Serve Ads Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("   ✅ Serve ads working")
            print(f"   Response: {data}")
        else:
            print(f"   ❌ Serve ads error: {response.text}")

    except Exception as e:
        print(f"   ❌ Serve ads connection error: {e}")

    # 4. Test Analytics Dashboard
    print("\n4. Testing Analytics Dashboard...")
    analytics_url = f'{base_url}/ads/analytics'

    try:
        response = session.get(analytics_url)
        print(f"   Analytics Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✅ Analytics dashboard accessible")
        else:
            print(f"   ❌ Analytics error: {response.status_code}")

    except Exception as e:
        print(f"   ❌ Analytics connection error: {e}")

    print("\n" + "="*50)
    print("🧪 Testing completed")
    return True

if __name__ == "__main__":
    test_ads_system()
