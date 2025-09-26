#!/usr/bin/env python3
"""
Test script to create and push ads through the API
"""

import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ad_creation():
    """Test creating ads through the API"""
    print("🧪 Testing Ad Creation and API")
    print("="*50)

    try:
        from flask import Flask
        from models import db, User, AdCampaign, Ad, AdPlacement, UserRole, default_utcnow
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create test app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['BASE_URL'] = 'http://localhost:5000'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/LilyOpenCms.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize database
        db.init_app(app)

        with app.app_context():
            print("🔧 Setting up test environment...")

            # Check if we have the superuser
            suadmin = User.query.filter_by(username='suadmin').first()
            if not suadmin:
                print("❌ Superuser 'suadmin' not found in database")
                print("📝 You need to create the superuser first or ensure the database is initialized")
                return False

            print(f"✅ Found superuser: {suadmin.username} (Role: {suadmin.role})")

            # Create a test campaign
            print("\n📢 Creating test campaign...")
            campaign = AdCampaign(
                name="Test Campaign",
                description="A test campaign for API testing",
                is_active=True,
                budget=1000.00,
                currency='IDR',
                created_by=suadmin.id,
                updated_by=suadmin.id
            )
            db.session.add(campaign)
            db.session.flush()  # Get the campaign ID

            print(f"✅ Created campaign: {campaign.name} (ID: {campaign.id})")

            # Create a test ad
            print("\n📰 Creating test ad...")
            ad = Ad(
                title="Test Ad",
                description="A test advertisement",
                ad_type="internal",
                content_type="text",
                text_content="This is a test advertisement created via API",
                target_url="https://example.com",
                is_active=True,
                priority=1,
                campaign_id=campaign.id,
                created_at=default_utcnow(),
                updated_at=default_utcnow()
            )
            db.session.add(ad)
            db.session.flush()  # Get the ad ID

            print(f"✅ Created ad: {ad.title} (ID: {ad.id})")

            # Create a test placement
            print("\n📍 Creating test placement...")
            placement = AdPlacement(
                name="Test Placement",
                description="A test placement for ads",
                page_type="home",
                section="sidebar",
                position="top",
                max_ads_per_page=1,
                rotation_type="random",
                display_frequency=1.0,
                is_active=True,
                created_at=default_utcnow(),
                updated_at=default_utcnow()
            )
            db.session.add(placement)
            db.session.flush()  # Get the placement ID

            print(f"✅ Created placement: {placement.name} (ID: {placement.id})")

            # Commit all changes
            db.session.commit()

            print("
✅ All test data created successfully!"            print(f"   📊 Campaign ID: {campaign.id}")
            print(f"   📰 Ad ID: {ad.id}")
            print(f"   📍 Placement ID: {placement.id}")

            return True

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ad_api():
    """Test the ad serving API"""
    print("\n🌐 Testing Ad API endpoints...")
    print("="*30)

    try:
        import requests

        base_url = 'http://localhost:5000'

        # Test data for API calls
        test_payload = {
            "page_type": "home",
            "section": "sidebar",
            "position": "top",
            "max_ads": 1,
            "device_type": "desktop"
        }

        print("📡 Testing /ads/api/serve endpoint...")
        response = requests.post(f'{base_url}/ads/api/serve', json=test_payload, timeout=10)

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Response: {data}")
            print(f"   📊 Ads returned: {len(data.get('ads', []))}")
            return True
        else:
            print(f"   ❌ API Error: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server - make sure it's running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"   ❌ API test error: {e}")
        return False

def test_login_and_dashboard():
    """Test login and dashboard access"""
    print("\n🔐 Testing Login and Dashboard...")
    print("="*35)

    try:
        import requests

        base_url = 'http://localhost:5000'
        session = requests.Session()

        # Login data
        login_data = {
            'username': 'suadmin',
            'password': 'suladang'
        }

        print("📝 Attempting login...")
        response = session.post(f'{base_url}/login', data=login_data, allow_redirects=False)

        print(f"   Login Status: {response.status_code}")

        if response.status_code == 302:
            print("   ✅ Login successful")

            # Test dashboard access
            print("   📊 Testing dashboard access...")
            dash_response = session.get(f'{base_url}/ads/dashboard')

            print(f"   Dashboard Status: {dash_response.status_code}")

            if dash_response.status_code == 200:
                print("   ✅ Dashboard accessible")
                return True
            else:
                print(f"   ❌ Dashboard error: {dash_response.status_code}")
                return False
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Login test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Ad System Testing Suite")
    print("="*50)

    # Test 1: Database setup and data creation
    print("\n1️⃣ Testing Database and Data Creation")
    db_success = test_ad_creation()

    # Test 2: API endpoints
    print("\n2️⃣ Testing API Endpoints")
    api_success = test_ad_api()

    # Test 3: Login and Dashboard
    print("\n3️⃣ Testing Login and Dashboard")
    login_success = test_login_and_dashboard()

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    print(f"🗄️  Database/Data Creation: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"🌐 API Endpoints: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"🔐 Login/Dashboard: {'✅ PASS' if login_success else '❌ FAIL'}")

    if all([db_success, api_success, login_success]):
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Next Steps:")
        print("1. Start the server: python main.py")
        print("2. Login with: suadmin / suladang")
        print("3. Access dashboard: http://localhost:5000/ads/dashboard")
        print("4. Test API: POST to /ads/api/serve")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

    return all([db_success, api_success, login_success])

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
