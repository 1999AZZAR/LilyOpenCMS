#!/usr/bin/env python3
"""
Comprehensive Test Ads Generator for LilyOpenCMS
Consolidated script that combines all test ads functionality from multiple files.
Creates sample ads, campaigns, and placements to demonstrate the ads system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
import random

# Import Flask app and database
from main import app, db
from models import User, AdCampaign, Ad, AdPlacement, AdStats

# ============================================================================
# TEST DATA DEFINITIONS
# ============================================================================

# Test Campaigns Data
TEST_CAMPAIGNS = [
    {
        "name": "Premium Content Promotion",
        "description": "Campaign to promote premium content and subscriptions",
        "is_active": True,
        "budget": 5000000,  # 5M IDR
        "currency": "IDR",
        "target_audience": {"user_type": "non_premium", "interests": ["premium_content"]}
    },
    {
        "name": "News Engagement Campaign",
        "description": "Campaign to increase engagement with news articles",
        "is_active": True,
        "budget": 3000000,  # 3M IDR
        "currency": "IDR",
        "target_audience": {"user_type": "all", "interests": ["news", "current_events"]}
    },
    {
        "name": "Album Discovery Campaign",
        "description": "Campaign to promote album discovery and reading",
        "is_active": True,
        "budget": 2000000,  # 2M IDR
        "currency": "IDR",
        "target_audience": {"user_type": "all", "interests": ["stories", "novels"]}
    },
    {
        "name": "Mobile User Campaign",
        "description": "Campaign specifically targeting mobile users",
        "is_active": True,
        "budget": 1500000,  # 1.5M IDR
        "currency": "IDR",
        "target_audience": {"device_type": "mobile", "user_type": "all"}
    },
    {
        'name': 'Mobile Promotions',
        'description': 'Ads specifically for mobile users',
        'is_active': True,
        'budget': 500.00,
        'currency': 'USD',
        'target_audience': 'mobile_users',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'Premium Content Promo',
        'description': 'Promoting premium content features',
        'is_active': True,
        'budget': 300.00,
        'currency': 'USD',
        'target_audience': 'premium_users',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'News Section Ads',
        'description': 'Ads for news page visitors',
        'is_active': True,
        'budget': 400.00,
        'currency': 'USD',
        'target_audience': 'news_readers',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'Homepage Multiple Ads',
        'description': 'Multiple ads for homepage testing',
        'is_active': True,
        'budget': 200.00,
        'currency': 'USD',
        'target_audience': 'homepage_visitors',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'News Page Multiple Ads',
        'description': 'Multiple ads for news page testing',
        'is_active': True,
        'budget': 250.00,
        'currency': 'USD',
        'target_audience': 'news_readers',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'Album Page Multiple Ads',
        'description': 'Multiple ads for album page testing',
        'is_active': True,
        'budget': 150.00,
        'currency': 'USD',
        'target_audience': 'album_readers',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    },
    {
        'name': 'Homepage Test Campaign',
        'description': 'Test ads specifically for homepage',
        'is_active': True,
        'budget': 100.00,
        'currency': 'USD',
        'target_audience': 'homepage_visitors',
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30)
    }
]

# Test Placements Data
TEST_PLACEMENTS = [
    # Homepage placements
    {
        "name": "Homepage Header Ad",
        "description": "Ad displayed in homepage header section",
        "page_type": "home",
        "section": "header",
        "position": "top",
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.8,
        "user_type": "all",
        "device_type": "all"
    },
    {
        "name": "Homepage Sidebar Ad",
        "description": "Ad displayed in homepage sidebar",
        "page_type": "home",
        "section": "sidebar",
        "position": "top",
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 0.9,
        "user_type": "all",
        "device_type": "desktop"
    },
    {
        "name": "Homepage Content Ad",
        "description": "Ad displayed between content sections on homepage",
        "page_type": "home",
        "section": "content",
        "position": "after_n_items",
        "position_value": 3,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.7,
        "user_type": "all",
        "device_type": "all"
    },
    {
        "name": "Homepage Content After 6",
        "description": "Ad displayed after 6th content item on homepage",
        "page_type": "home",
        "section": "content",
        "position": "after_n_items",
        "position_value": 6,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.7,
        "user_type": "all",
        "device_type": "all"
    },
    
    # News page placements
    {
        "name": "News Page Header Ad",
        "description": "Ad displayed in news page header",
        "page_type": "news",
        "section": "header",
        "position": "top",
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.8,
        "user_type": "all",
        "device_type": "all"
    },
    {
        "name": "News Page Content Ad",
        "description": "Ad displayed between news articles",
        "page_type": "news",
        "section": "content",
        "position": "after_n_items",
        "position_value": 2,
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 0.6,
        "user_type": "all",
        "device_type": "all"
    },
    {
        "name": "News After 5 Items",
        "description": "Ad displayed after 5th news item",
        "page_type": "news",
        "section": "content",
        "position": "after_n_items",
        "position_value": 5,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.6,
        "user_type": "all",
        "device_type": "all"
    },
    
    # Album page placements
    {
        "name": "Album Page Sidebar Ad",
        "description": "Ad displayed in album page sidebar",
        "page_type": "album",
        "section": "sidebar",
        "position": "top",
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.8,
        "user_type": "all",
        "device_type": "desktop"
    },
    {
        "name": "Album Page Content Ad",
        "description": "Ad displayed between album chapters",
        "page_type": "album",
        "section": "content",
        "position": "after_n_items",
        "position_value": 1,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.5,
        "user_type": "all",
        "device_type": "all"
    },
    {
        "name": "Album After 3 Items",
        "description": "Ad displayed after 3rd album item",
        "page_type": "album",
        "section": "content",
        "position": "after_n_items",
        "position_value": 3,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.5,
        "user_type": "all",
        "device_type": "all"
    },
    
    # Mobile-specific placements
    {
        "name": "Mobile Homepage Ad",
        "description": "Ad specifically for mobile homepage",
        "page_type": "home",
        "section": "content",
        "position": "middle",
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.9,
        "user_type": "all",
        "device_type": "mobile"
    },
    {
        "name": "Home Mobile Middle",
        "description": "Mobile ads in the middle of homepage content",
        "page_type": "home",
        "section": "content",
        "position": "middle",
        "position_value": None,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "mobile",
        "location_targeting": None,
        "is_active": True
    },
    
    # Premium user targeting
    {
        "name": "Premium Upgrade Ad",
        "description": "Ad targeting non-premium users",
        "page_type": "home",
        "section": "content",
        "position": "bottom",
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 0.8,
        "user_type": "non_premium",
        "device_type": "all"
    },
    
    # Sidebar placements
    {
        "name": "Home Sidebar Top",
        "description": "Desktop sidebar ads on homepage",
        "page_type": "home",
        "section": "sidebar",
        "position": "top",
        "position_value": None,
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "desktop",
        "location_targeting": None,
        "is_active": True
    },
    {
        "name": "News Sidebar Top",
        "description": "Desktop sidebar ads on news page",
        "page_type": "news",
        "section": "sidebar",
        "position": "top",
        "position_value": None,
        "max_ads_per_page": 1,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "desktop",
        "location_targeting": None,
        "is_active": True
    },
    
    # Multiple ads placements
    {
        "name": "Homepage After 3 Items",
        "description": "Ads after 3 content items on homepage",
        "page_type": "home",
        "section": "content",
        "position": "after_n_items",
        "position_value": 3,
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "all",
        "location_targeting": None,
        "is_active": True
    },
    {
        "name": "Homepage After 6 Items",
        "description": "Ads after 6 content items on homepage",
        "page_type": "home",
        "section": "content",
        "position": "after_n_items",
        "position_value": 6,
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "all",
        "location_targeting": None,
        "is_active": True
    },
    {
        "name": "News After 2 Items",
        "description": "Ads after 2 news items",
        "page_type": "news",
        "section": "content",
        "position": "after_n_items",
        "position_value": 2,
        "max_ads_per_page": 3,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "all",
        "location_targeting": None,
        "is_active": True
    },
    {
        "name": "Albums After 1 Item",
        "description": "Ads after 1 album item",
        "page_type": "album",
        "section": "content",
        "position": "after_n_items",
        "position_value": 1,
        "max_ads_per_page": 2,
        "rotation_type": "random",
        "display_frequency": 1.0,
        "user_type": "all",
        "device_type": "all",
        "location_targeting": None,
        "is_active": True
    }
]

# Test Ads Data
TEST_ADS = [
    # Image Ads
    {
        "title": "Premium Content Access",
        "description": "Unlock exclusive premium content and features",
        "ad_type": "internal",
        "content_type": "image",
        "image_url": "/static/pic/placeholder.png",
        "image_alt": "Premium Content Access",
        "target_url": "/premium",
        "width": 300,
        "height": 250,
        "css_classes": "ad-container internal-ad premium-promo",
        "inline_styles": "border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);",
        "priority": 10
    },
    {
        "title": "Latest News Updates",
        "description": "Stay informed with our latest news coverage",
        "ad_type": "internal",
        "content_type": "image",
        "image_url": "/static/pic/placeholder.png",
        "image_alt": "Latest News Updates",
        "target_url": "/news",
        "width": 300,
        "height": 250,
        "css_classes": "ad-container internal-ad news-promo",
        "inline_styles": "border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);",
        "priority": 8
    },
    {
        "title": "Discover Amazing Stories",
        "description": "Explore our collection of captivating albums",
        "ad_type": "internal",
        "content_type": "image",
        "image_url": "/static/pic/placeholder.png",
        "image_alt": "Discover Amazing Stories",
        "target_url": "/albums",
        "width": 300,
        "height": 250,
        "css_classes": "ad-container internal-ad album-promo",
        "inline_styles": "border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);",
        "priority": 7
    },
    
    # Text Ads
    {
        "title": "Upgrade to Premium",
        "description": "Get unlimited access to exclusive content and features",
        "ad_type": "internal",
        "content_type": "text",
        "text_content": "Join thousands of readers who have upgraded to premium. Get unlimited access to exclusive content, ad-free experience, and priority support.",
        "target_url": "/premium",
        "css_classes": "ad-container internal-ad text-ad premium-text",
        "inline_styles": "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px;",
        "priority": 9
    },
    {
        "title": "Breaking News Alert",
        "description": "Never miss important updates",
        "ad_type": "internal",
        "content_type": "text",
        "text_content": "Subscribe to our breaking news alerts and be the first to know about important developments. Stay informed with real-time updates.",
        "target_url": "/news",
        "css_classes": "ad-container internal-ad text-ad news-alert",
        "inline_styles": "background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px;",
        "priority": 6
    },
    
    # HTML Ads
    {
        "title": "Interactive Story Experience",
        "description": "Experience stories like never before",
        "ad_type": "internal",
        "content_type": "html",
        "html_content": """
        <div style="text-align: center; padding: 15px;">
            <h3 style="margin: 0 0 10px 0; color: #333;">Interactive Stories</h3>
            <p style="margin: 0 0 15px 0; color: #666;">Experience our interactive story format with branching narratives and reader choices.</p>
            <button style="background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">Explore Now</button>
        </div>
        """,
        "target_url": "/albums",
        "css_classes": "ad-container internal-ad html-ad interactive-promo",
        "inline_styles": "border: 2px solid #4CAF50; border-radius: 8px; background: #f9f9f9;",
        "priority": 5
    },
    
    # External Google Ads (Mock)
    {
        "title": "Sponsored Content",
        "description": "External sponsored content",
        "ad_type": "external",
        "content_type": "google_ads",
        "external_ad_code": """
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-1234567890123456"
             data-ad-slot="1234567890"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
        """,
        "external_ad_client": "ca-pub-1234567890123456",
        "external_ad_slot": "1234567890",
        "width": 300,
        "height": 250,
        "css_classes": "ad-container external-ad google-ads",
        "priority": 3
    },
    
    # Additional Mobile Ads
    {
        'title': 'Mobile App Download',
        'description': 'Download our mobile app for the best experience!',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/mobile-app',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Premium Features',
        'description': 'Unlock exclusive content with Premium membership',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/premium',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Latest News Alert',
        'description': 'Stay updated with breaking news and updates',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/news',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Special Offer',
        'description': 'Limited time offer - 50% off premium features!',
        'ad_type': 'internal',
        'content_type': 'html',
        'target_url': '/special-offer',
        'image_url': None,
        'html_content': '<div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; padding: 20px; border-radius: 8px; text-align: center;"><h3>🔥 Special Offer!</h3><p>50% off Premium features</p><button style="background: white; color: #ff6b6b; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold;">Claim Now</button></div>',
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    
    # Multiple Ads for Testing
    {
        'title': 'Featured Story',
        'description': 'Check out our latest featured story',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/news',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Premium Membership',
        'description': 'Join our premium membership for exclusive content',
        'ad_type': 'internal',
        'content_type': 'html',
        'target_url': '/premium',
        'image_url': None,
        'html_content': '<div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; text-align: center;"><h3>🌟 Premium Membership</h3><p>Get exclusive access to premium content</p><button style="background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold;">Join Now</button></div>',
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Latest Albums',
        'description': 'Discover our latest album releases',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/albums',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Newsletter Signup',
        'description': 'Stay updated with our newsletter',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/newsletter',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Community Forum',
        'description': 'Join our community discussions',
        'ad_type': 'internal',
        'content_type': 'html',
        'target_url': '/forum',
        'image_url': None,
        'html_content': '<div style="background: linear-gradient(135deg, #4facfe, #00f2fe); color: white; padding: 20px; border-radius: 8px; text-align: center;"><h3>💬 Community Forum</h3><p>Join discussions with other readers</p><button style="background: white; color: #4facfe; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold;">Join Forum</button></div>',
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    
    # Homepage specific ads
    {
        'title': 'Welcome to Our Site!',
        'description': 'Discover amazing content and stories',
        'ad_type': 'internal',
        'content_type': 'text',
        'target_url': '/news',
        'image_url': None,
        'html_content': None,
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    },
    {
        'title': 'Premium Content Available',
        'description': 'Unlock exclusive stories and features',
        'ad_type': 'internal',
        'content_type': 'html',
        'target_url': '/premium',
        'image_url': None,
        'html_content': '<div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; border-radius: 8px; text-align: center;"><h3>🌟 Premium Content</h3><p>Access exclusive stories and features</p><button style="background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold;">Learn More</button></div>',
        'width': 300,
        'height': 250,
        'is_active': True,
        'start_date': datetime.now(),
        'end_date': datetime.now() + timedelta(days=30),
        'impressions': 0,
        'clicks': 0
    }
]# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def create_test_campaigns():
    """Create test campaigns."""
    print("🎯 Creating test campaigns...")
    
    campaigns = []
    for campaign_data in TEST_CAMPAIGNS:
        # Get a random user as creator
        users = User.query.all()
        if not users:
            print("❌ No users found. Please create users first.")
            return []
        
        creator = random.choice(users)
        
        campaign = AdCampaign(
            name=campaign_data["name"],
            description=campaign_data["description"],
            is_active=campaign_data["is_active"],
            budget=campaign_data["budget"],
            currency=campaign_data["currency"],
            target_audience=campaign_data["target_audience"],
            created_by=creator.id,
            updated_by=creator.id
        )
        
        db.session.add(campaign)
        campaigns.append(campaign)
        print(f"  + Created campaign: {campaign.name}")
    
    db.session.commit()
    print(f"✅ Created {len(campaigns)} campaigns")
    return campaigns

def create_test_ads(campaigns):
    """Create test ads."""
    print("📢 Creating test ads...")
    
    ads = []
    for ad_data in TEST_ADS:
        # Get a random user as creator
        users = User.query.all()
        creator = random.choice(users)
        
        # Assign to a random campaign
        campaign = random.choice(campaigns) if campaigns else None
        
        ad = Ad(
            title=ad_data["title"],
            description=ad_data["description"],
            ad_type=ad_data["ad_type"],
            content_type=ad_data["content_type"],
            image_url=ad_data.get("image_url"),
            image_alt=ad_data.get("image_alt"),
            text_content=ad_data.get("text_content"),
            html_content=ad_data.get("html_content"),
            target_url=ad_data.get("target_url"),
            external_ad_code=ad_data.get("external_ad_code"),
            external_ad_client=ad_data.get("external_ad_client"),
            external_ad_slot=ad_data.get("external_ad_slot"),
            width=ad_data.get("width"),
            height=ad_data.get("height"),
            css_classes=ad_data.get("css_classes"),
            inline_styles=ad_data.get("inline_styles"),
            is_active=True,
            priority=ad_data.get("priority", 0),
            campaign_id=campaign.id if campaign else None,
            created_by=creator.id,
            updated_by=creator.id
        )
        
        db.session.add(ad)
        ads.append(ad)
        print(f"  + Created ad: {ad.title} ({ad.ad_type}/{ad.content_type})")
    
    db.session.commit()
    print(f"✅ Created {len(ads)} ads")
    return ads

def create_test_placements(ads):
    """Create test placements."""
    print("📍 Creating test placements...")
    
    placements = []
    for placement_data in TEST_PLACEMENTS:
        # Get a random user as creator
        users = User.query.all()
        creator = random.choice(users)
        
        # Assign to a random ad
        ad = random.choice(ads)
        
        placement = AdPlacement(
            name=placement_data["name"],
            description=placement_data["description"],
            page_type=placement_data["page_type"],
            page_specific=placement_data.get("page_specific"),
            section=placement_data["section"],
            position=placement_data["position"],
            position_value=placement_data.get("position_value"),
            max_ads_per_page=placement_data["max_ads_per_page"],
            rotation_type=placement_data["rotation_type"],
            display_frequency=placement_data["display_frequency"],
            user_type=placement_data.get("user_type"),
            device_type=placement_data.get("device_type"),
            location_targeting=placement_data.get("location_targeting"),
            is_active=True,
            ad_id=ad.id,
            created_by=creator.id,
            updated_by=creator.id
        )
        
        db.session.add(placement)
        placements.append(placement)
        print(f"  + Created placement: {placement.name} ({placement.page_type}/{placement.section})")
    
    db.session.commit()
    print(f"✅ Created {len(placements)} placements")
    return placements

def create_test_stats(ads):
    """Create some test statistics for ads."""
    print("📊 Creating test statistics...")
    
    # Create stats for the last 7 days
    for ad in ads:
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            
            # Generate realistic stats
            impressions = random.randint(100, 1000)
            clicks = random.randint(5, 50)
            revenue = random.uniform(1000, 10000)  # IDR
            
            stat = AdStats(
                date=date,
                impressions=impressions,
                clicks=clicks,
                revenue=revenue,
                unique_users=random.randint(50, impressions),
                returning_users=random.randint(10, 100),
                desktop_impressions=random.randint(impressions//3, impressions//2),
                mobile_impressions=random.randint(impressions//3, impressions//2),
                tablet_impressions=impressions - random.randint(impressions//3, impressions//2) - random.randint(impressions//3, impressions//2),
                ad_id=ad.id
            )
            
            db.session.add(stat)
    
    db.session.commit()
    print("✅ Created test statistics")

def create_simple_test_ads():
    """Create simple test ads for basic testing."""
    print("🎬 Creating simple test ads...")
    
    # Simple test campaign
    users = User.query.all()
    if not users:
        print("❌ No users found. Please create users first.")
        return
    
    creator = users[0]
    
    # Create a simple campaign
    campaign = AdCampaign(
        name="Simple Test Campaign",
        description="Basic test campaign for ads injection system",
        is_active=True,
        budget=1000.00,
        currency="IDR",
        target_audience="all",
        created_by=creator.id,
        updated_by=creator.id
    )
    db.session.add(campaign)
    db.session.commit()
    
    # Create simple test ads
    simple_ads = [
        {
            "title": "Test Ad 1 - Homepage",
            "description": "Test ad for homepage content",
            "ad_type": "internal",
            "content_type": "html",
            "html_content": """
            <div class="test-ad" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 10px 0;">
                <h3 style="margin: 0 0 10px 0; font-size: 18px;">🎯 Test Advertisement</h3>
                <p style="margin: 0 0 15px 0; font-size: 14px;">This is a test ad for the homepage. Click to learn more!</p>
                <a href="#" style="background: white; color: #667eea; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Learn More</a>
            </div>
            """,
            "target_url": "#",
            "width": 300,
            "height": 200,
            "css_classes": "test-ad homepage-ad",
            "is_active": True,
            "priority": 1
        },
        {
            "title": "Test Ad 2 - News",
            "description": "Test ad for news pages",
            "ad_type": "internal",
            "content_type": "html",
            "html_content": """
            <div class="test-ad" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 10px 0;">
                <h3 style="margin: 0 0 10px 0; font-size: 18px;">📰 News Advertisement</h3>
                <p style="margin: 0 0 15px 0; font-size: 14px;">Stay updated with the latest news and stories!</p>
                <a href="#" style="background: white; color: #f093fb; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Read More</a>
            </div>
            """,
            "target_url": "#",
            "width": 300,
            "height": 200,
            "css_classes": "test-ad news-ad",
            "is_active": True,
            "priority": 2
        }
    ]
    
    ads = []
    for ad_data in simple_ads:
        ad = Ad(
            title=ad_data["title"],
            description=ad_data["description"],
            ad_type=ad_data["ad_type"],
            content_type=ad_data["content_type"],
            html_content=ad_data["html_content"],
            target_url=ad_data["target_url"],
            width=ad_data["width"],
            height=ad_data["height"],
            css_classes=ad_data["css_classes"],
            is_active=ad_data["is_active"],
            priority=ad_data["priority"],
            campaign_id=campaign.id,
            created_by=creator.id,
            updated_by=creator.id
        )
        db.session.add(ad)
        ads.append(ad)
    
    db.session.commit()
    print(f"✅ Created {len(ads)} simple test ads")
    return ads

def demo_ads_system():
    """Demonstrate the ads system functionality."""
    print("🎬 LilyOpenCMS Ads System Demonstration")
    print("=" * 50)
    
    with app.app_context():
        # Show campaigns
        campaigns = AdCampaign.query.all()
        print(f"\n📊 Campaigns ({len(campaigns)}):")
        for campaign in campaigns:
            print(f"  - {campaign.name}")
            print(f"    Budget: {campaign.currency} {campaign.budget:,}")
            print(f"    Active: {campaign.is_active_now()}")
            print(f"    Ads: {len(campaign.ads)}")
        
        # Show ads
        ads = Ad.query.all()
        print(f"\n📢 Ads ({len(ads)}):")
        for ad in ads:
            print(f"  - {ad.title}")
            print(f"    Type: {ad.ad_type}/{ad.content_type}")
            print(f"    Active: {ad.is_active_now()}")
            print(f"    Impressions: {ad.impressions}, Clicks: {ad.clicks}")
            print(f"    CTR: {ad.ctr:.2f}%")
        
        # Show placements
        placements = AdPlacement.query.all()
        print(f"\n📍 Placements ({len(placements)}):")
        for placement in placements:
            print(f"  - {placement.name}")
            print(f"    Page: {placement.page_type}/{placement.section}")
            print(f"    Position: {placement.position}")
            print(f"    Frequency: {placement.display_frequency * 100:.0f}%")
            print(f"    Device: {placement.device_type or 'all'}")
            print(f"    User: {placement.user_type or 'all'}")
        
        # Show recent stats
        print(f"\n📈 Recent Statistics:")
        recent_stats = AdStats.query.order_by(AdStats.date.desc()).limit(5).all()
        for stat in recent_stats:
            print(f"  - {stat.date}: {stat.impressions} impressions, {stat.clicks} clicks")
            print(f"    CTR: {stat.ctr:.2f}%, Revenue: {stat.revenue}")
        
        print(f"\n🎯 System Summary:")
        print(f"  - Total Campaigns: {len(campaigns)}")
        print(f"  - Total Ads: {len(ads)}")
        print(f"  - Total Placements: {len(placements)}")
        print(f"  - Active Campaigns: {sum(1 for c in campaigns if c.is_active_now())}")
        print(f"  - Active Ads: {sum(1 for a in ads if a.is_active_now())}")
        print(f"  - Active Placements: {sum(1 for p in placements if p.is_active)}")
        
        print(f"\n🌐 How to Test:")
        print(f"  1. Visit http://localhost:5000 to see ads on homepage")
        print(f"  2. Visit http://localhost:5000/news to see ads on news page")
        print(f"  3. Visit http://localhost:5000/albums to see ads on albums page")
        print(f"  4. Visit http://localhost:5000/ads/dashboard for admin dashboard")
        print(f"  5. Visit http://localhost:5000/ads/analytics for analytics")

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================

def main():
    """Main function to create comprehensive test ads data."""
    print("🎬 LilyOpenCMS Comprehensive Test Ads Generator")
    print("=" * 60)
    
    with app.app_context():
        # Ensure the database is initialized
        db.create_all()
        
        # Check if users exist
        users = User.query.all()
        if not users:
            print("❌ No users found. Please create users first.")
            print("   Run generate_user.py first!")
            return
        
        print(f"✅ Found {len(users)} users")
        
        # Create comprehensive test data
        campaigns = create_test_campaigns()
        ads = create_test_ads(campaigns)
        placements = create_test_placements(ads)
        create_test_stats(ads)
        
        print("\n🎉 Comprehensive test ads data created successfully!")
        print(f"📊 Summary:")
        print(f"   - Campaigns: {len(campaigns)}")
        print(f"   - Ads: {len(ads)}")
        print(f"   - Placements: {len(placements)}")
        print(f"   - Statistics: {len(ads) * 7} daily records")
        
        print("\n🔗 You can now:")
        print("   - Visit /ads/dashboard to see the ads admin dashboard")
        print("   - Visit /ads/campaigns to manage campaigns")
        print("   - Visit /ads/ads to manage ads")
        print("   - Visit /ads/placements to manage placements")
        print("   - Visit /ads/analytics to see analytics")
        print("   - Check public pages to see ads in action")
        
        print("\n🌐 Test the robust ads injection system:")
        print("   1. Visit http://localhost:5000 and refresh multiple times")
        print("   2. Check browser console for debug information")
        print("   3. Look for ads in different positions and sections")
        print("   4. Test on mobile vs desktop for different targeting")
        print("   5. Visit different pages (news, albums) to see page-specific ads")

def create_simple_ads():
    """Create only simple test ads for basic testing."""
    print("🎬 LilyOpenCMS Simple Test Ads Generator")
    print("=" * 50)
    
    with app.app_context():
        # Ensure the database is initialized
        db.create_all()
        
        # Check if users exist
        users = User.query.all()
        if not users:
            print("❌ No users found. Please create users first.")
            print("   Run generate_user.py first!")
            return
        
        print(f"✅ Found {len(users)} users")
        
        # Create simple test data
        ads = create_simple_test_ads()
        
        print("\n🎉 Simple test ads created successfully!")
        print(f"📊 Summary:")
        print(f"   - Ads: {len(ads)}")
        
        print("\n🌐 Test the ads injection system:")
        print("   1. Visit http://localhost:5000 - should see ads after 3rd and 6th content items")
        print("   2. Visit http://localhost:5000/news - should see ads after 2nd and 5th news items")
        print("   3. Visit http://localhost:5000/albums - should see ads after 1st and 3rd album items")
        print("   4. Open browser console (F12) to see ads injection logs")
        print("   5. Refresh pages to see ad rotation")

def demo():
    """Demonstrate the ads system."""
    demo_ads_system()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--simple":
            create_simple_ads()
        elif sys.argv[1] == "--demo":
            demo()
        else:
            print("Usage:")
            print("  python add_test_ads.py          # Create comprehensive test ads")
            print("  python add_test_ads.py --simple # Create simple test ads")
            print("  python add_test_ads.py --demo   # Show ads system demo")
    else:
        main()