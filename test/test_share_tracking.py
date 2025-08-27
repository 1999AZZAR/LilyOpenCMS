#!/usr/bin/env python3
"""
Test script for share tracking functionality.
This script tests the share tracking API endpoints and verifies that share counts are updated correctly.
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"

def test_news_share_tracking():
    """Test share tracking for news articles."""
    print("Testing news share tracking...")
    
    # Use a known news ID for testing (you can change this to a valid news ID)
    news_id = 1  # Assuming news ID 1 exists
    print(f"Testing with news ID: {news_id}")
    
    try:
        # Test share data endpoint
        response = requests.get(f"{BASE_URL}/api/news/{news_id}/share-data")
        if response.status_code != 200:
            print(f"Failed to get share data: {response.status_code}")
            return False
        
        share_data = response.json()
        print(f"Initial share data: {share_data}")
        
        # Test tracking a share
        test_platform = "whatsapp"
        response = requests.post(
            f"{BASE_URL}/api/news/{news_id}/track-share",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'platform': test_platform})
        )
        
        if response.status_code != 200:
            print(f"Failed to track share: {response.status_code}")
            return False
        
        print(f"Share tracking response: {response.json()}")
        
        # Wait a moment and check if share count was updated
        time.sleep(1)
        
        response = requests.get(f"{BASE_URL}/api/news/{news_id}/share-data")
        if response.status_code != 200:
            print(f"Failed to get updated share data: {response.status_code}")
            return False
        
        updated_share_data = response.json()
        print(f"Updated share data: {updated_share_data}")
        
        # Verify that the share count increased
        initial_count = share_data.get(f'{test_platform}_count', 0)
        updated_count = updated_share_data.get(f'{test_platform}_count', 0)
        
        if updated_count > initial_count:
            print(f"✅ Share tracking working: {test_platform} count increased from {initial_count} to {updated_count}")
            return True
        else:
            print(f"❌ Share tracking failed: {test_platform} count did not increase")
            return False
            
    except Exception as e:
        print(f"Error testing news share tracking: {e}")
        return False

def test_album_share_tracking():
    """Test share tracking for albums."""
    print("\nTesting album share tracking...")
    
    # Use a known album ID for testing (you can change this to a valid album ID)
    album_id = 1  # Assuming album ID 1 exists
    print(f"Testing with album ID: {album_id}")
    
    try:
        
        # Test share data endpoint
        response = requests.get(f"{BASE_URL}/api/albums/{album_id}/share-data")
        if response.status_code != 200:
            print(f"Failed to get album share data: {response.status_code}")
            return False
        
        share_data = response.json()
        print(f"Initial album share data: {share_data}")
        
        # Test tracking a share
        test_platform = "facebook"
        response = requests.post(
            f"{BASE_URL}/api/albums/{album_id}/track-share",
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'platform': test_platform})
        )
        
        if response.status_code != 200:
            print(f"Failed to track album share: {response.status_code}")
            return False
        
        print(f"Album share tracking response: {response.json()}")
        
        # Wait a moment and check if share count was updated
        time.sleep(1)
        
        response = requests.get(f"{BASE_URL}/api/albums/{album_id}/share-data")
        if response.status_code != 200:
            print(f"Failed to get updated album share data: {response.status_code}")
            return False
        
        updated_share_data = response.json()
        print(f"Updated album share data: {updated_share_data}")
        
        # Verify that the share count increased
        initial_count = share_data.get(f'{test_platform}_count', 0)
        updated_count = updated_share_data.get(f'{test_platform}_count', 0)
        
        if updated_count > initial_count:
            print(f"✅ Album share tracking working: {test_platform} count increased from {initial_count} to {updated_count}")
            return True
        else:
            print(f"❌ Album share tracking failed: {test_platform} count did not increase")
            return False
            
    except Exception as e:
        print(f"Error testing album share tracking: {e}")
        return False

def main():
    """Run all share tracking tests."""
    print("🧪 Testing Share Tracking System")
    print("=" * 50)
    
    # Test news share tracking
    news_success = test_news_share_tracking()
    
    # Test album share tracking
    album_success = test_album_share_tracking()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"News Share Tracking: {'✅ PASS' if news_success else '❌ FAIL'}")
    print(f"Album Share Tracking: {'✅ PASS' if album_success else '❌ FAIL'}")
    
    if news_success and album_success:
        print("\n🎉 All share tracking tests passed!")
        return True
    else:
        print("\n⚠️  Some share tracking tests failed!")
        return False

if __name__ == "__main__":
    main() 