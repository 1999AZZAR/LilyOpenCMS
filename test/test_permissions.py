#!/usr/bin/env python3
"""
Test script to verify the new permission system for news and albums CRUD operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models import db, User, UserRole, CustomRole, Permission
from routes.utils.permission_manager import (
    can_create_news, can_edit_news, can_delete_news, can_publish_news,
    can_create_albums, can_edit_albums, can_delete_albums, can_publish_albums,
    can_manage_news, can_manage_albums, can_access_content_creation
)

def test_permission_system():
    """Test the permission system with different user roles."""
    
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test permissions
        news_permissions = [
            Permission(name="news_read", description="View news articles", resource="news", action="read"),
            Permission(name="news_create", description="Create news articles", resource="news", action="create"),
            Permission(name="news_update", description="Update news articles", resource="news", action="update"),
            Permission(name="news_delete", description="Delete news articles", resource="news", action="delete"),
            Permission(name="news_publish", description="Publish/unpublish news", resource="news", action="publish"),
        ]
        
        album_permissions = [
            Permission(name="albums_read", description="View albums", resource="albums", action="read"),
            Permission(name="albums_create", description="Create albums", resource="albums", action="create"),
            Permission(name="albums_update", description="Update albums", resource="albums", action="update"),
            Permission(name="albums_delete", description="Delete albums", resource="albums", action="delete"),
            Permission(name="albums_publish", description="Publish/unpublish albums", resource="albums", action="publish"),
        ]
        
        for perm in news_permissions + album_permissions:
            db.session.add(perm)
        
        # Create test roles
        writer_role = CustomRole(name="Writer", description="Can create content")
        writer_role.permissions = [p for p in news_permissions + album_permissions if p.action in ["read", "create"]]
        
        editor_role = CustomRole(name="Editor", description="Can create and edit content")
        editor_role.permissions = [p for p in news_permissions + album_permissions if p.action in ["read", "create", "update"]]
        
        db.session.add(writer_role)
        db.session.add(editor_role)
        
        # Create test users
        general_user = User(
            username="general_user",
            email="general@test.com",
            password_hash="test",
            role=UserRole.GENERAL,
            verified=True
        )
        
        writer_user = User(
            username="writer_user",
            email="writer@test.com",
            password_hash="test",
            role=UserRole.GENERAL,
            verified=True,
            custom_role=writer_role
        )
        
        editor_user = User(
            username="editor_user",
            email="editor@test.com",
            password_hash="test",
            role=UserRole.GENERAL,
            verified=True,
            custom_role=editor_role
        )
        
        admin_user = User(
            username="admin_user",
            email="admin@test.com",
            password_hash="test",
            role=UserRole.ADMIN,
            verified=True
        )
        
        superuser = User(
            username="superuser",
            email="super@test.com",
            password_hash="test",
            role=UserRole.SUPERUSER,
            verified=True
        )
        
        db.session.add_all([general_user, writer_user, editor_user, admin_user, superuser])
        db.session.commit()
        
        # Test results
        print("=== Permission System Test Results ===")
        print()
        
        test_users = [
            ("General User", general_user),
            ("Writer User", writer_user),
            ("Editor User", editor_user),
            ("Admin User", admin_user),
            ("Superuser", superuser)
        ]
        
        for user_name, user in test_users:
            print(f"--- {user_name} ---")
            print(f"Role: {user.role.value}")
            if user.custom_role:
                print(f"Custom Role: {user.custom_role.name}")
            
            # Test news permissions
            print("News Permissions:")
            print(f"  Create: {can_create_news(user)}")
            print(f"  Edit: {can_edit_news(user)}")
            print(f"  Delete: {can_delete_news(user)}")
            print(f"  Publish: {can_publish_news(user)}")
            print(f"  Manage: {can_manage_news(user)}")
            
            # Test album permissions
            print("Album Permissions:")
            print(f"  Create: {can_create_albums(user)}")
            print(f"  Edit: {can_edit_albums(user)}")
            print(f"  Delete: {can_delete_albums(user)}")
            print(f"  Publish: {can_publish_albums(user)}")
            print(f"  Manage: {can_manage_albums(user)}")
            
            # Test content creation access
            print(f"Content Creation Access: {can_access_content_creation(user)}")
            print()
        
        print("=== Expected Results ===")
        print("General User: Should have no permissions")
        print("Writer User: Should have create permissions for news and albums")
        print("Editor User: Should have create and edit permissions for news and albums")
        print("Admin User: Should have all permissions")
        print("Superuser: Should have all permissions")
        print()
        
        # Clean up
        db.session.remove()
        db.drop_all()

if __name__ == "__main__":
    test_permission_system()
