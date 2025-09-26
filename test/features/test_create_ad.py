#!/usr/bin/env python3
"""
Simple script to create test ads in the database
Run this with: python test/test_create_ad.py
"""

import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_test_ad():
    """Create a test ad in the database"""
    print("🧪 Creating Test Ad")
    print("="*30)

    try:
        from flask import Flask
        from models import db, User, AdCampaign, Ad, AdPlacement, UserRole, default_utcnow

        # Create test app
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/LilyOpenCms.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize database
        db.init_app(app)

        with app.app_context():
            print("🔧 Connecting to database...")

            # Check if we have the superuser
            suadmin = User.query.filter_by(username='suadmin').first()
            if not suadmin:
                print("❌ Superuser 'suadmin' not found")
                print("📝 Please ensure the database is initialized with the superuser")
                return False

            print(f"✅ Found superuser: {suadmin.username}")

            # Create a test campaign
            print("📢 Creating test campaign...")
            campaign = AdCampaign(
                name="Test API Campaign",
                description="Campaign created for API testing",
                is_active=True,
                budget=5000.00,
                currency='IDR',
                created_by=suadmin.id,
                updated_by=suadmin.id
            )
            db.session.add(campaign)
            db.session.flush()

            print(f"✅ Campaign created: ID {campaign.id}")

            # Create a test ad
            print("📰 Creating test ad...")
            ad = Ad(
                title="Test API Ad",
                description="Sample advertisement for API testing",
                ad_type="internal",
                content_type="text",
                text_content="🚀 This is a test ad created via Python script! 🚀",
                target_url="https://example.com/test-ad",
                is_active=True,
                priority=1,
                campaign_id=campaign.id
            )
            db.session.add(ad)
            db.session.flush()

            print(f"✅ Ad created: ID {ad.id}")

            # Create a test placement
            print("📍 Creating test placement...")
            placement = AdPlacement(
                name="Home Sidebar",
                description="Sidebar placement on home page",
                page_type="home",
                section="sidebar",
                position="top",
                max_ads_per_page=1,
                rotation_type="random",
                display_frequency=1.0,
                is_active=True
            )
            db.session.add(placement)
            db.session.flush()

            print(f"✅ Placement created: ID {placement.id}")

            # Commit all changes
            db.session.commit()

            print("\n🎉 SUCCESS! Test data created:")
            print(f"   📊 Campaign ID: {campaign.id}")
            print(f"   📰 Ad ID: {ad.id}")
            print(f"   📍 Placement ID: {placement.id}")
            print("\n📡 Now you can test the API with:")
            print(f"curl -X POST http://localhost:5000/ads/api/serve \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  -d '{{\"page_type\": \"home\", \"section\": \"sidebar\", \"position\": \"top\"}}'")

            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_test_ad()
    sys.exit(0 if success else 1)
