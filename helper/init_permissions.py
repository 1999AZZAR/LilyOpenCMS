#!/usr/bin/env python3
"""
Initialize default permissions and roles for the enhanced user management system.
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

from models import Permission, CustomRole, UserRole
from datetime import datetime, timezone

def create_default_permissions():
    """Create default permissions for the system."""
    permissions = [
        # User management permissions
        {"name": "users_read", "description": "View user information", "resource": "users", "action": "read"},
        {"name": "users_create", "description": "Create new users", "resource": "users", "action": "create"},
        {"name": "users_update", "description": "Update user information", "resource": "users", "action": "update"},
        {"name": "users_delete", "description": "Delete users", "resource": "users", "action": "delete"},
        {"name": "users_suspend", "description": "Suspend/unsuspend users", "resource": "users", "action": "suspend"},
        {"name": "users_approve", "description": "Approve pending registrations", "resource": "users", "action": "approve"},
        
        # Role management permissions
        {"name": "roles_read", "description": "View roles", "resource": "roles", "action": "read"},
        {"name": "roles_create", "description": "Create new roles", "resource": "roles", "action": "create"},
        {"name": "roles_update", "description": "Update roles", "resource": "roles", "action": "update"},
        {"name": "roles_delete", "description": "Delete roles", "resource": "roles", "action": "delete"},
        {"name": "roles_assign", "description": "Assign roles to users", "resource": "roles", "action": "assign"},
        
        # Permission management permissions
        {"name": "permissions_read", "description": "View permissions", "resource": "permissions", "action": "read"},
        {"name": "permissions_create", "description": "Create new permissions", "resource": "permissions", "action": "create"},
        {"name": "permissions_update", "description": "Update permissions", "resource": "permissions", "action": "update"},
        {"name": "permissions_delete", "description": "Delete permissions", "resource": "permissions", "action": "delete"},
        {"name": "permissions_assign", "description": "Assign permissions to roles", "resource": "permissions", "action": "assign"},
        
        # News management permissions
        {"name": "news_read", "description": "View news articles", "resource": "news", "action": "read"},
        {"name": "news_create", "description": "Create news articles", "resource": "news", "action": "create"},
        {"name": "news_update", "description": "Update news articles", "resource": "news", "action": "update"},
        {"name": "news_delete", "description": "Delete news articles", "resource": "news", "action": "delete"},
        {"name": "news_publish", "description": "Publish/unpublish news", "resource": "news", "action": "publish"},
        {"name": "news_moderate", "description": "Moderate news content", "resource": "news", "action": "moderate"},
        
        # Album management permissions
        {"name": "albums_read", "description": "View albums", "resource": "albums", "action": "read"},
        {"name": "albums_create", "description": "Create albums", "resource": "albums", "action": "create"},
        {"name": "albums_update", "description": "Update albums", "resource": "albums", "action": "update"},
        {"name": "albums_delete", "description": "Delete albums", "resource": "albums", "action": "delete"},
        {"name": "albums_publish", "description": "Publish/unpublish albums", "resource": "albums", "action": "publish"},
        
        # Image management permissions
        {"name": "images_read", "description": "View images", "resource": "images", "action": "read"},
        {"name": "images_create", "description": "Upload images", "resource": "images", "action": "create"},
        {"name": "images_update", "description": "Update image information", "resource": "images", "action": "update"},
        {"name": "images_delete", "description": "Delete images", "resource": "images", "action": "delete"},
        {"name": "images_moderate", "description": "Moderate image content", "resource": "images", "action": "moderate"},
        
        # Video management permissions
        {"name": "videos_read", "description": "View videos", "resource": "videos", "action": "read"},
        {"name": "videos_create", "description": "Add videos", "resource": "videos", "action": "create"},
        {"name": "videos_update", "description": "Update video information", "resource": "videos", "action": "update"},
        {"name": "videos_delete", "description": "Delete videos", "resource": "videos", "action": "delete"},
        {"name": "videos_moderate", "description": "Moderate video content", "resource": "videos", "action": "moderate"},
        
        # Category management permissions
        {"name": "categories_read", "description": "View categories", "resource": "categories", "action": "read"},
        {"name": "categories_create", "description": "Create categories", "resource": "categories", "action": "create"},
        {"name": "categories_update", "description": "Update categories", "resource": "categories", "action": "update"},
        {"name": "categories_delete", "description": "Delete categories", "resource": "categories", "action": "delete"},
        
        # Comments management permissions
        {"name": "comments_read", "description": "View comments", "resource": "comments", "action": "read"},
        {"name": "comments_create", "description": "Create comments", "resource": "comments", "action": "create"},
        {"name": "comments_update", "description": "Update comments", "resource": "comments", "action": "update"},
        {"name": "comments_delete", "description": "Delete comments", "resource": "comments", "action": "delete"},
        {"name": "comments_moderate", "description": "Moderate comments", "resource": "comments", "action": "moderate"},
        {"name": "comments_approve", "description": "Approve/reject comments", "resource": "comments", "action": "approve"},
        
        # Ratings management permissions
        {"name": "ratings_read", "description": "View ratings", "resource": "ratings", "action": "read"},
        {"name": "ratings_create", "description": "Create ratings", "resource": "ratings", "action": "create"},
        {"name": "ratings_update", "description": "Update ratings", "resource": "ratings", "action": "update"},
        {"name": "ratings_delete", "description": "Delete ratings", "resource": "ratings", "action": "delete"},
        {"name": "ratings_moderate", "description": "Moderate ratings", "resource": "ratings", "action": "moderate"},
        
        # Ads management permissions
        {"name": "ads_read", "description": "View ads", "resource": "ads", "action": "read"},
        {"name": "ads_create", "description": "Create ads", "resource": "ads", "action": "create"},
        {"name": "ads_update", "description": "Update ads", "resource": "ads", "action": "update"},
        {"name": "ads_delete", "description": "Delete ads", "resource": "ads", "action": "delete"},
        {"name": "ads_publish", "description": "Publish/unpublish ads", "resource": "ads", "action": "publish"},
        {"name": "ads_place", "description": "Manage ad placements", "resource": "ads", "action": "place"},
        
        # Campaigns management permissions
        {"name": "campaigns_read", "description": "View campaigns", "resource": "campaigns", "action": "read"},
        {"name": "campaigns_create", "description": "Create campaigns", "resource": "campaigns", "action": "create"},
        {"name": "campaigns_update", "description": "Update campaigns", "resource": "campaigns", "action": "update"},
        {"name": "campaigns_delete", "description": "Delete campaigns", "resource": "campaigns", "action": "delete"},
        {"name": "campaigns_publish", "description": "Publish/unpublish campaigns", "resource": "campaigns", "action": "publish"},
        
        # Analytics permissions
        {"name": "analytics_read", "description": "View analytics", "resource": "analytics", "action": "read"},
        {"name": "analytics_export", "description": "Export analytics data", "resource": "analytics", "action": "export"},
        {"name": "analytics_manage", "description": "Manage analytics settings", "resource": "analytics", "action": "manage"},
        
        # SEO permissions
        {"name": "seo_read", "description": "View SEO settings", "resource": "seo", "action": "read"},
        {"name": "seo_update", "description": "Update SEO settings", "resource": "seo", "action": "update"},
        {"name": "seo_manage", "description": "Manage SEO tools", "resource": "seo", "action": "manage"},
        {"name": "sitemap_manage", "description": "Manage sitemaps", "resource": "seo", "action": "sitemap"},
        
        # Settings management permissions
        {"name": "settings_read", "description": "View settings", "resource": "settings", "action": "read"},
        {"name": "settings_update", "description": "Update settings", "resource": "settings", "action": "update"},
        {"name": "settings_manage", "description": "Manage system settings", "resource": "settings", "action": "manage"},
        
        # Brand management permissions
        {"name": "brand_read", "description": "View brand settings", "resource": "brand", "action": "read"},
        {"name": "brand_update", "description": "Update brand settings", "resource": "brand", "action": "update"},
        {"name": "brand_manage", "description": "Manage brand identity", "resource": "brand", "action": "manage"},
        
        # Navigation management permissions
        {"name": "navigation_read", "description": "View navigation", "resource": "navigation", "action": "read"},
        {"name": "navigation_create", "description": "Create navigation items", "resource": "navigation", "action": "create"},
        {"name": "navigation_update", "description": "Update navigation", "resource": "navigation", "action": "update"},
        {"name": "navigation_delete", "description": "Delete navigation items", "resource": "navigation", "action": "delete"},
        
        # Legal content permissions
        {"name": "legal_read", "description": "View legal content", "resource": "legal", "action": "read"},
        {"name": "legal_create", "description": "Create legal content", "resource": "legal", "action": "create"},
        {"name": "legal_update", "description": "Update legal content", "resource": "legal", "action": "update"},
        {"name": "legal_delete", "description": "Delete legal content", "resource": "legal", "action": "delete"},
        {"name": "legal_publish", "description": "Publish legal content", "resource": "legal", "action": "publish"},
        
        # System administration permissions
        {"name": "system_read", "description": "View system information", "resource": "system", "action": "read"},
        {"name": "system_manage", "description": "Manage system settings", "resource": "system", "action": "manage"},
        {"name": "system_maintenance", "description": "Perform system maintenance", "resource": "system", "action": "maintenance"},
        {"name": "system_backup", "description": "Create system backups", "resource": "system", "action": "backup"},
        {"name": "system_restore", "description": "Restore system from backup", "resource": "system", "action": "restore"},
        
        # Performance optimization permissions
        {"name": "performance_read", "description": "View performance metrics", "resource": "performance", "action": "read"},
        {"name": "performance_optimize", "description": "Optimize system performance", "resource": "performance", "action": "optimize"},
        {"name": "performance_monitor", "description": "Monitor system performance", "resource": "performance", "action": "monitor"},
        
        # Content moderation permissions
        {"name": "moderation_read", "description": "View moderation queue", "resource": "moderation", "action": "read"},
        {"name": "moderation_approve", "description": "Approve content", "resource": "moderation", "action": "approve"},
        {"name": "moderation_reject", "description": "Reject content", "resource": "moderation", "action": "reject"},
        {"name": "moderation_manage", "description": "Manage moderation settings", "resource": "moderation", "action": "manage"},
        
        # Premium features permissions
        {"name": "premium_read", "description": "View premium features", "resource": "premium", "action": "read"},
        {"name": "premium_manage", "description": "Manage premium features", "resource": "premium", "action": "manage"},
        {"name": "premium_assign", "description": "Assign premium access", "resource": "premium", "action": "assign"},
    ]
    
    created_permissions = []
    for perm_data in permissions:
        existing = Permission.query.filter_by(name=perm_data["name"]).first()
        if not existing:
            permission = Permission(**perm_data)
            db.session.add(permission)
            created_permissions.append(permission)
            print(f"Created permission: {perm_data['name']}")
        else:
            print(f"Permission already exists: {perm_data['name']}")
    
    db.session.commit()
    print(f"Created {len(created_permissions)} new permissions")
    return created_permissions

def create_default_roles():
    """Create default custom roles."""
    roles = [
        {
            "name": "Guest",
            "description": "Basic read-only access to public content.",
            "permissions": [
                "news_read", "albums_read", "images_read", "videos_read", "categories_read"
            ]
        },
        {
            "name": "Reader",
            "description": "Can read content and interact with comments and ratings.",
            "permissions": [
                "news_read", "albums_read", "images_read", "videos_read", "categories_read",
                "comments_read", "comments_create", "ratings_read", "ratings_create"
            ]
        },
        {
            "name": "Writer",
            "description": "Can create and read content, upload images.",
            "permissions": [
                "news_read", "news_create",
                "albums_read", "albums_create",
                "images_read", "images_create",
                "videos_read", "videos_create",
                "categories_read",
                "comments_read", "comments_create",
                "ratings_read", "ratings_create"
            ]
        },
        {
            "name": "Editor",
            "description": "Can create, edit, and publish content.",
            "permissions": [
                "news_read", "news_create", "news_update", "news_publish",
                "albums_read", "albums_create", "albums_update", "albums_publish",
                "images_read", "images_create", "images_update",
                "videos_read", "videos_create", "videos_update",
                "categories_read", "categories_create", "categories_update",
                "comments_read", "comments_create", "comments_update",
                "ratings_read", "ratings_create", "ratings_update"
            ]
        },
        {
            "name": "Content Moderator",
            "description": "Can review and moderate content",
            "permissions": [
                "news_read", "news_update", "news_publish", "news_moderate",
                "albums_read", "albums_update", "albums_publish",
                "images_read", "images_update", "images_moderate",
                "videos_read", "videos_update", "videos_moderate",
                "categories_read",
                "comments_read", "comments_update", "comments_moderate", "comments_approve",
                "ratings_read", "ratings_update", "ratings_moderate",
                "moderation_read", "moderation_approve", "moderation_reject"
            ]
        },
        {
            "name": "Media Manager",
            "description": "Can manage all media content",
            "permissions": [
                "news_read", "news_create", "news_update", "news_delete", "news_publish",
                "albums_read", "albums_create", "albums_update", "albums_delete", "albums_publish",
                "images_read", "images_create", "images_update", "images_delete", "images_moderate",
                "videos_read", "videos_create", "videos_update", "videos_delete", "videos_moderate",
                "categories_read", "categories_create", "categories_update", "categories_delete"
            ]
        },
        {
            "name": "User Manager",
            "description": "Can manage users but not system settings",
            "permissions": [
                "users_read", "users_create", "users_update", "users_suspend", "users_approve",
                "roles_read", "roles_assign",
                "premium_read", "premium_assign"
            ]
        },
        {
            "name": "Ad Manager",
            "description": "Can manage advertisements and campaigns",
            "permissions": [
                "ads_read", "ads_create", "ads_update", "ads_delete", "ads_publish", "ads_place",
                "campaigns_read", "campaigns_create", "campaigns_update", "campaigns_delete", "campaigns_publish",
                "analytics_read", "analytics_export"
            ]
        },
        {
            "name": "SEO Specialist",
            "description": "Can manage SEO settings and optimization",
            "permissions": [
                "seo_read", "seo_update", "seo_manage", "sitemap_manage",
                "analytics_read", "analytics_export",
                "performance_read", "performance_monitor"
            ]
        },
        {
            "name": "Legal Manager",
            "description": "Can manage legal content and policies",
            "permissions": [
                "legal_read", "legal_create", "legal_update", "legal_delete", "legal_publish",
                "brand_read", "brand_update"
            ]
        },
        {
            "name": "Subadmin",
            "description": "Elevated role below Admin; manage content and media but not users or system settings.",
            "permissions": [
                "news_read", "news_create", "news_update", "news_delete", "news_publish", "news_moderate",
                "albums_read", "albums_create", "albums_update", "albums_delete", "albums_publish",
                "images_read", "images_create", "images_update", "images_delete", "images_moderate",
                "videos_read", "videos_create", "videos_update", "videos_delete", "videos_moderate",
                "categories_read", "categories_create", "categories_update", "categories_delete",
                "comments_read", "comments_create", "comments_update", "comments_delete", "comments_moderate", "comments_approve",
                "ratings_read", "ratings_create", "ratings_update", "ratings_delete", "ratings_moderate",
                "ads_read", "ads_create", "ads_update", "ads_delete", "ads_publish", "ads_place",
                "campaigns_read", "campaigns_create", "campaigns_update", "campaigns_delete", "campaigns_publish",
                "analytics_read", "analytics_export",
                "seo_read", "seo_update",
                "settings_read", "settings_update",
                "brand_read", "brand_update",
                "navigation_read", "navigation_create", "navigation_update", "navigation_delete",
                "legal_read", "legal_create", "legal_update", "legal_delete", "legal_publish",
                "moderation_read", "moderation_approve", "moderation_reject",
                "performance_read", "performance_monitor"
            ]
        },
        {
            "name": "System Administrator",
            "description": "Full system access except user deletion",
            "permissions": [
                "users_read", "users_create", "users_update", "users_suspend", "users_approve",
                "roles_read", "roles_create", "roles_update", "roles_delete", "roles_assign",
                "permissions_read", "permissions_create", "permissions_update", "permissions_delete", "permissions_assign",
                "news_read", "news_create", "news_update", "news_delete", "news_publish", "news_moderate",
                "albums_read", "albums_create", "albums_update", "albums_delete", "albums_publish",
                "images_read", "images_create", "images_update", "images_delete", "images_moderate",
                "videos_read", "videos_create", "videos_update", "videos_delete", "videos_moderate",
                "categories_read", "categories_create", "categories_update", "categories_delete",
                "comments_read", "comments_create", "comments_update", "comments_delete", "comments_moderate", "comments_approve",
                "ratings_read", "ratings_create", "ratings_update", "ratings_delete", "ratings_moderate",
                "ads_read", "ads_create", "ads_update", "ads_delete", "ads_publish", "ads_place",
                "campaigns_read", "campaigns_create", "campaigns_update", "campaigns_delete", "campaigns_publish",
                "analytics_read", "analytics_export", "analytics_manage",
                "seo_read", "seo_update", "seo_manage", "sitemap_manage",
                "settings_read", "settings_update", "settings_manage",
                "brand_read", "brand_update", "brand_manage",
                "navigation_read", "navigation_create", "navigation_update", "navigation_delete",
                "legal_read", "legal_create", "legal_update", "legal_delete", "legal_publish",
                "system_read", "system_manage", "system_maintenance", "system_backup",
                "performance_read", "performance_optimize", "performance_monitor",
                "moderation_read", "moderation_approve", "moderation_reject", "moderation_manage",
                "premium_read", "premium_manage", "premium_assign"
            ]
        },
        {
            "name": "Admin",
            "description": "Can manage all content and media, and users, but not system settings",
            "permissions": [
                "users_read", "users_create", "users_update", "users_suspend", "users_approve",
                "roles_read", "roles_create", "roles_update", "roles_delete", "roles_assign",
                "permissions_read", "permissions_create", "permissions_update", "permissions_delete", "permissions_assign",
                "news_read", "news_create", "news_update", "news_delete", "news_publish", "news_moderate",
                "albums_read", "albums_create", "albums_update", "albums_delete", "albums_publish",
                "images_read", "images_create", "images_update", "images_delete", "images_moderate",
                "videos_read", "videos_create", "videos_update", "videos_delete", "videos_moderate",
                "categories_read", "categories_create", "categories_update", "categories_delete",
                "comments_read", "comments_create", "comments_update", "comments_delete", "comments_moderate", "comments_approve",
                "ratings_read", "ratings_create", "ratings_update", "ratings_delete", "ratings_moderate",
                "ads_read", "ads_create", "ads_update", "ads_delete", "ads_publish", "ads_place",
                "campaigns_read", "campaigns_create", "campaigns_update", "campaigns_delete", "campaigns_publish",
                "analytics_read", "analytics_export", "analytics_manage",
                "seo_read", "seo_update", "seo_manage", "sitemap_manage",
                "settings_read", "settings_update", "settings_manage",
                "brand_read", "brand_update", "brand_manage",
                "navigation_read", "navigation_create", "navigation_update", "navigation_delete",
                "legal_read", "legal_create", "legal_update", "legal_delete", "legal_publish",
                "moderation_read", "moderation_approve", "moderation_reject", "moderation_manage",
                "premium_read", "premium_manage", "premium_assign",
                "performance_read", "performance_monitor"
            ]
        },
        {
            "name": "Super Admin",
            "description": "Complete system access including system administration",
            "permissions": [
                "users_read", "users_create", "users_update", "users_delete", "users_suspend", "users_approve",
                "roles_read", "roles_create", "roles_update", "roles_delete", "roles_assign",
                "permissions_read", "permissions_create", "permissions_update", "permissions_delete", "permissions_assign",
                "news_read", "news_create", "news_update", "news_delete", "news_publish", "news_moderate",
                "albums_read", "albums_create", "albums_update", "albums_delete", "albums_publish",
                "images_read", "images_create", "images_update", "images_delete", "images_moderate",
                "videos_read", "videos_create", "videos_update", "videos_delete", "videos_moderate",
                "categories_read", "categories_create", "categories_update", "categories_delete",
                "comments_read", "comments_create", "comments_update", "comments_delete", "comments_moderate", "comments_approve",
                "ratings_read", "ratings_create", "ratings_update", "ratings_delete", "ratings_moderate",
                "ads_read", "ads_create", "ads_update", "ads_delete", "ads_publish", "ads_place",
                "campaigns_read", "campaigns_create", "campaigns_update", "campaigns_delete", "campaigns_publish",
                "analytics_read", "analytics_export", "analytics_manage",
                "seo_read", "seo_update", "seo_manage", "sitemap_manage",
                "settings_read", "settings_update", "settings_manage",
                "brand_read", "brand_update", "brand_manage",
                "navigation_read", "navigation_create", "navigation_update", "navigation_delete",
                "legal_read", "legal_create", "legal_update", "legal_delete", "legal_publish",
                "system_read", "system_manage", "system_maintenance", "system_backup", "system_restore",
                "performance_read", "performance_optimize", "performance_monitor",
                "moderation_read", "moderation_approve", "moderation_reject", "moderation_manage",
                "premium_read", "premium_manage", "premium_assign"
            ]
        }
    ]
    
    created_roles = []
    for role_data in roles:
        existing = CustomRole.query.filter_by(name=role_data["name"]).first()
        if not existing:
            permissions = Permission.query.filter(Permission.name.in_(role_data["permissions"])).all()
            
            role = CustomRole(
                name=role_data["name"],
                description=role_data["description"],
                is_active=True
            )
            role.permissions = permissions
            
            db.session.add(role)
            created_roles.append(role)
            print(f"Created role: {role_data['name']} with {len(permissions)} permissions")
        else:
            print(f"Role already exists: {role_data['name']}")
    
    db.session.commit()
    print(f"Created {len(created_roles)} new roles")
    return created_roles

def main():
    """Main function to initialize permissions and roles."""
    with app.app_context():
        print("Initializing permissions and roles...")
        
        # Create permissions
        permissions = create_default_permissions()
        
        # Create roles
        roles = create_default_roles()
        
        print("\nInitialization complete!")
        print(f"Total permissions: {Permission.query.count()}")
        print(f"Total roles: {CustomRole.query.count()}")

if __name__ == "__main__":
    main() 