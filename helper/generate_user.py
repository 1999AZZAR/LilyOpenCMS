import sys
import os
from datetime import datetime, timedelta, timezone, date

# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)  # Insert at beginning to prioritize local imports

from models import db, User, UserRole, CustomRole
from werkzeug.security import generate_password_hash

# Import app from the local main module
import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(project_root, "main.py"))
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)
app = main.app

# List of users to create with comprehensive roles
users = [
    # Super Admin - Full system access
    {"username": "suadmin", "role": UserRole.SUPERUSER, "is_premium": True, "custom_role": "Super Admin"},
    
    # System Administrators - Full system access except user deletion
    {"username": "sysadmin1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "System Administrator"},
    {"username": "sysadmin2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "System Administrator"},
    
    # Admins - Full content and user management
    {"username": "admin1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Admin"},
    {"username": "admin2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Admin"},
    {"username": "admin3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Admin"},
    
    # Subadmins - Elevated content management
    {"username": "subadmin1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Subadmin"},
    {"username": "subadmin2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Subadmin"},
    {"username": "subadmin3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Subadmin"},
    
    # Content Editors - Content creation and editing
    {"username": "editor1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Editor"},
    {"username": "editor2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Editor"},
    {"username": "editor3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Editor"},
    {"username": "editor4", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Editor"},
    
    # Content Moderators - Content review and moderation
    {"username": "moderator1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Content Moderator"},
    {"username": "moderator2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Content Moderator"},
    {"username": "moderator3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Content Moderator"},
    
    # Media Managers - Full media management
    {"username": "mediamanager1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Media Manager"},
    {"username": "mediamanager2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Media Manager"},
    
    # User Managers - User management only
    {"username": "usermanager1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "User Manager"},
    {"username": "usermanager2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "User Manager"},
    
    # Ad Managers - Advertisement management
    {"username": "admanager1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Ad Manager"},
    {"username": "admanager2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Ad Manager"},
    
    # SEO Specialists - SEO management
    {"username": "seospecialist1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "SEO Specialist"},
    {"username": "seospecialist2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "SEO Specialist"},
    
    # Legal Managers - Legal content management
    {"username": "legalmanager1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Legal Manager"},
    {"username": "legalmanager2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Legal Manager"},
    
    # Writers - Content creation
    {"username": "writer1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Writer"},
    {"username": "writer2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Writer"},
    {"username": "writer3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Writer"},
    {"username": "writer4", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Writer"},
    {"username": "writer5", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Writer"},
    
    # Readers - Content interaction
    {"username": "reader1", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Reader"},
    {"username": "reader2", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Reader"},
    {"username": "reader3", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Reader"},
    {"username": "reader4", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Reader"},
    {"username": "reader5", "role": UserRole.ADMIN, "is_premium": True, "custom_role": "Reader"},
    
    # Guests - Basic access
    {"username": "guest1", "role": UserRole.ADMIN, "is_premium": False, "custom_role": "Guest"},
    {"username": "guest2", "role": UserRole.ADMIN, "is_premium": False, "custom_role": "Guest"},
    {"username": "guest3", "role": UserRole.ADMIN, "is_premium": False, "custom_role": "Guest"},
    
    # General users - No custom role
    {"username": "general1", "role": UserRole.GENERAL, "is_premium": False},
    {"username": "general2", "role": UserRole.GENERAL, "is_premium": False},
    {"username": "general3", "role": UserRole.GENERAL, "is_premium": False},
    {"username": "general4", "role": UserRole.GENERAL, "is_premium": False},
    {"username": "general5", "role": UserRole.GENERAL, "is_premium": False},
]

import random

# Passwords for different roles
role_passwords = {
    UserRole.SUPERUSER: generate_password_hash("suladang"),
    UserRole.ADMIN: generate_password_hash("admin_password"),
    UserRole.GENERAL: generate_password_hash("general_password")
}

def make_birthdate(min_age: int, max_age: int) -> date:
    """Generate a safe random birthdate ensuring age between bounds."""
    today = date.today()
    age = random.randint(min_age, max_age)
    year = today.year - age
    month = random.randint(1, 12)
    # Use safe day to avoid month length issues
    day = random.randint(1, 28)
    return date(year, month, day)

# Insert users into the database
with app.app_context():
    print("👥 LilyOpenCMS Comprehensive User Generator")
    print("=" * 60)
    
    # Create tables if they don't exist (ensures the 'user' table is present)
    db.create_all()
    
    added_count = 0
    skipped_count = 0
    updated_count = 0
    
    for user_data in users:
        existing_user = User.query.filter_by(username=user_data["username"]).first()
        if not existing_user:
            # Set premium status
            is_premium = user_data.get("is_premium", False)
            has_premium_access = is_premium
            premium_expires_at = None
            
            if is_premium:
                # Set premium to expire in 1 year from now
                premium_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
            
            # Ensure adults for admins and superuser; mixed for others
            if user_data["role"] in (UserRole.SUPERUSER, UserRole.ADMIN):
                user_birthdate = make_birthdate(30, 55)
            else:
                user_birthdate = make_birthdate(16, 45)

            new_user = User(
                username=user_data["username"],
                password_hash=role_passwords[user_data["role"]],
                role=user_data["role"],
                verified=True,
                is_active=True,
                is_premium=is_premium,
                has_premium_access=has_premium_access,
                premium_expires_at=premium_expires_at,
                birthdate=user_birthdate,
            )
            db.session.add(new_user)
            db.session.flush()  # Flush to get the user ID
            
            # Assign custom role if specified
            if "custom_role" in user_data:
                custom_role_name = user_data["custom_role"]
                custom_role = CustomRole.query.filter_by(name=custom_role_name).first()
                if custom_role:
                    new_user.custom_role = custom_role
                    premium_tag = " (Premium)" if is_premium else ""
                    print(f"  ✅ Created user: {user_data['username']} ({user_data['role'].value}){premium_tag} - Assigned to {custom_role_name}")
                else:
                    print(f"  ⚠️ Warning: Custom role '{custom_role_name}' not found for {user_data['username']}")
                    premium_tag = " (Premium)" if is_premium else ""
                    print(f"  ✅ Created user: {user_data['username']} ({user_data['role'].value}){premium_tag}")
            else:
                premium_status = " (Premium)" if is_premium else ""
                print(f"  ✅ Created user: {user_data['username']} ({user_data['role'].value}){premium_status}")
            
            added_count += 1
        else:
            # Update existing superuser to be premium and assign custom role if not already
            updated = False
            if user_data["username"] == "suadmin":
                if not existing_user.is_premium:
                    existing_user.is_premium = True
                    existing_user.has_premium_access = True
                    existing_user.premium_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
                    updated = True
                # Ensure adult birthdate for superuser
                if not existing_user.birthdate:
                    existing_user.birthdate = make_birthdate(35, 55)
                    updated = True
                
                # Assign Super Admin role if not already assigned
                if "custom_role" in user_data and not existing_user.custom_role:
                    custom_role_name = user_data["custom_role"]
                    custom_role = CustomRole.query.filter_by(name=custom_role_name).first()
                    if custom_role:
                        existing_user.custom_role = custom_role
                        updated = True
                        print(f"  🔄 Updated existing user: {user_data['username']} (now Premium + {custom_role_name})")
                    else:
                        print(f"  ⚠️ Warning: Custom role '{custom_role_name}' not found for {user_data['username']}")
                        if updated:
                            print(f"  🔄 Updated existing user: {user_data['username']} (now Premium)")
                elif updated:
                    print(f"  🔄 Updated existing user: {user_data['username']} (now Premium)")
                
                if updated:
                    updated_count += 1
                else:
                    print(f"  ⏭️ Skipped existing user: {user_data['username']}")
                    skipped_count += 1
            else:
                print(f"  ⏭️ Skipped existing user: {user_data['username']}")
                skipped_count += 1
    
    db.session.commit()
    print("-" * 60)
    print(f"✅ User generation complete!")
    print(f"   Added: {added_count} users")
    print(f"   Updated: {updated_count} users")
    if skipped_count > 0:
        print(f"   Skipped: {skipped_count} existing users")
    print("")
    print("🔐 Default Passwords:")
    print("   Superuser (suladang): suladang")
    print("   Admin: admin_password")
    print("   General: general_password")
    print("")
    print("💎 Premium Status:")
    print("   All admin users: Premium (1 year)")
    print("   Guest users: Standard")
    print("   General users: Standard")
    print("")
    print("👑 Role Distribution:")
    print("   Super Admin: 1 user (suadmin)")
    print("   System Administrator: 2 users")
    print("   Admin: 3 users")
    print("   Subadmin: 3 users")
    print("   Editor: 4 users")
    print("   Content Moderator: 3 users")
    print("   Media Manager: 2 users")
    print("   User Manager: 2 users")
    print("   Ad Manager: 2 users")
    print("   SEO Specialist: 2 users")
    print("   Legal Manager: 2 users")
    print("   Writer: 5 users")
    print("   Reader: 5 users")
    print("   Guest: 3 users")
    print("   General: 5 users")
    print("")
    print("🎯 Testing Coverage:")
    print("   All permission levels covered")
    print("   All custom roles represented")
    print("   Premium and standard users included")
    print("   Ready for comprehensive permission testing")
