#!/usr/bin/env python3
"""
Add sample social media links for the footer.
"""

import sys
import os
# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at beginning to prioritize local imports

# Import app and db from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app
db = main.db

from models import SocialMedia, User
from datetime import datetime, timezone

def add_social_media():
    """Add sample social media links."""
    print("📱 Adding Social Media Links")
    print("=" * 50)
    
    # Get the first admin user for created_by/updated_by
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User.query.filter_by(role='superuser').first()
    
    if not admin_user:
        print("⚠️  Warning: No admin user found. Social media links will be created without user attribution.")
        admin_user_id = None
    else:
        admin_user_id = admin_user.id
        print(f"✅ Using admin user: {admin_user.username}")
    
    # Clear existing social media links
    SocialMedia.query.delete()
    print("🗑️  Cleared existing social media links")
    
    # Sample social media links with realistic URLs
    social_links = [
        {
            "name": "Facebook",
            "url": "https://facebook.com/lilycms",
        },
        {
            "name": "Twitter",
            "url": "https://twitter.com/lilycms",
        },
        {
            "name": "Instagram",
            "url": "https://instagram.com/lilycms",
        },
        {
            "name": "YouTube",
            "url": "https://youtube.com/@lilycms",
        },
        {
            "name": "LinkedIn",
            "url": "https://linkedin.com/company/lilycms",
        },
        {
            "name": "TikTok",
            "url": "https://tiktok.com/@lilycms",
        },
        {
            "name": "WhatsApp",
            "url": "https://wa.me/6281234567890",
        },
        {
            "name": "Telegram",
            "url": "https://t.me/lilycms",
        },
        {
            "name": "Discord",
            "url": "https://discord.gg/lilycms",
        },
    ]
    
    created_count = 0
    for link in social_links:
        try:
            record = SocialMedia(
                name=link["name"],
                url=link["url"],
                created_by=admin_user_id,
                updated_by=admin_user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(record)
            print(f"✅ Added: {link['name']} - {link['url']}")
            created_count += 1
        except Exception as e:
            print(f"❌ Error adding {link['name']}: {str(e)}")
    
    try:
        db.session.commit()
        print("-" * 50)
        print(f"✅ Successfully added {created_count} social media links!")
        print("\n📋 Added Platforms:")
        for link in social_links[:created_count]:
            print(f"   • {link['name']}")
        
        print(f"\n🔗 Test the footer by visiting your website!")
        print("   The social media icons should now appear in the footer.")
        
    except Exception as e:
        print(f"❌ Error committing social media links: {str(e)}")
        db.session.rollback()

def add_custom_social_media():
    """Add custom social media links with user input."""
    print("📱 Adding Custom Social Media Links")
    print("=" * 50)
    
    # Get the first admin user for created_by/updated_by
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        admin_user = User.query.filter_by(role='superuser').first()
    
    if not admin_user:
        print("⚠️  Warning: No admin user found. Social media links will be created without user attribution.")
        admin_user_id = None
    else:
        admin_user_id = admin_user.id
        print(f"✅ Using admin user: {admin_user.username}")
    
    print("\nEnter social media links (press Enter with empty name to finish):")
    
    created_count = 0
    while True:
        print(f"\n--- Social Media Link #{created_count + 1} ---")
        name = input("Platform name (e.g., Facebook, Twitter): ").strip()
        
        if not name:
            break
            
        url = input("URL: ").strip()
        
        if not url:
            print("❌ URL is required. Skipping this entry.")
            continue
            
        # Validate URL format
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
            print(f"🔧 Added https:// prefix: {url}")
        
        try:
            record = SocialMedia(
                name=name,
                url=url,
                created_by=admin_user_id,
                updated_by=admin_user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.session.add(record)
            print(f"✅ Added: {name} - {url}")
            created_count += 1
        except Exception as e:
            print(f"❌ Error adding {name}: {str(e)}")
    
    if created_count > 0:
        try:
            db.session.commit()
            print("-" * 50)
            print(f"✅ Successfully added {created_count} custom social media links!")
            print(f"\n🔗 Test the footer by visiting your website!")
        except Exception as e:
            print(f"❌ Error committing social media links: {str(e)}")
            db.session.rollback()
    else:
        print("ℹ️  No social media links were added.")

def show_existing_social_media():
    """Show existing social media links."""
    print("📱 Existing Social Media Links")
    print("=" * 50)
    
    social_links = SocialMedia.query.order_by(SocialMedia.name).all()
    
    if not social_links:
        print("ℹ️  No social media links found.")
        return
    
    print(f"Found {len(social_links)} social media links:\n")
    
    for link in social_links:
        creator_name = link.creator.username if link.creator else "Unknown"
        print(f"• {link.name}")
        print(f"  URL: {link.url}")
        print(f"  Created by: {creator_name}")
        print(f"  Created: {link.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    """Main function with menu options."""
    print("📱 Social Media Links Helper")
    print("=" * 50)
    print("1. Add sample social media links")
    print("2. Add custom social media links")
    print("3. Show existing social media links")
    print("4. Clear all social media links")
    print("0. Exit")
    print("-" * 50)
    
    while True:
        try:
            choice = input("Choose an option (0-4): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                add_social_media()
                break
            elif choice == "2":
                add_custom_social_media()
                break
            elif choice == "3":
                show_existing_social_media()
                break
            elif choice == "4":
                confirm = input("⚠️  Are you sure you want to clear ALL social media links? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    SocialMedia.query.delete()
                    db.session.commit()
                    print("✅ All social media links have been cleared.")
                else:
                    print("❌ Operation cancelled.")
                break
            else:
                print("❌ Invalid choice. Please enter 0-4.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    with app.app_context():
        main()
