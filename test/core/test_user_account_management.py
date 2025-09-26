"""
Test User Account Management

This module tests the user account management functionality for general users.
"""

import pytest
from flask import Flask
from flask_login import LoginManager
from models import db, User, UserRole
from routes.settings.account import user_account_settings, update_user_profile, change_user_password, update_user_preferences, delete_user_account
import json


class TestUserAccountManagement:
    """Test cases for user account management functionality"""
    
    def test_user_account_settings_route_access(self, client, general_user):
        """Test that general users can access their account settings page"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        response = client.get('/account/settings')
        assert response.status_code == 200
        assert b'Pengaturan Akun' in response.data
    
    def test_user_account_settings_route_denied_for_admin(self, client, admin_user):
        """Test that admin users cannot access general user account settings"""
        with client.session_transaction() as sess:
            sess['_user_id'] = admin_user.id
        
        response = client.get('/account/settings')
        assert response.status_code == 403
    
    def test_update_user_profile_success(self, client, general_user):
        """Test successful profile update"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'bio': 'Test bio'
        }
        
        response = client.post('/api/user/profile', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert b'Profil berhasil diperbarui' in response.data
        
        # Verify the user was updated in database
        updated_user = User.query.get(general_user.id)
        assert updated_user.first_name == 'John'
        assert updated_user.last_name == 'Doe'
        assert updated_user.email == 'john.doe@example.com'
        assert updated_user.bio == 'Test bio'
    
    def test_update_user_profile_duplicate_email(self, client, general_user, another_user):
        """Test profile update with duplicate email"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        # Set another user's email
        another_user.email = 'existing@example.com'
        db.session.commit()
        
        data = {
            'email': 'existing@example.com'
        }
        
        response = client.post('/api/user/profile', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'Email sudah digunakan' in response.data
    
    def test_change_password_success(self, client, general_user):
        """Test successful password change"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        # Set initial password
        general_user.set_password('oldpassword')
        db.session.commit()
        
        data = {
            'current_password': 'oldpassword',
            'new_password': 'newpassword123'
        }
        
        response = client.post('/api/user/change-password', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert b'Kata sandi berhasil diubah' in response.data
        
        # Verify password was changed
        updated_user = User.query.get(general_user.id)
        assert updated_user.check_password('newpassword123')
    
    def test_change_password_wrong_current(self, client, general_user):
        """Test password change with wrong current password"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpassword123'
        }
        
        response = client.post('/api/user/change-password', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'Kata sandi saat ini salah' in response.data
    
    def test_change_password_too_short(self, client, general_user):
        """Test password change with too short new password"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        general_user.set_password('oldpassword')
        db.session.commit()
        
        data = {
            'current_password': 'oldpassword',
            'new_password': '123'
        }
        
        response = client.post('/api/user/change-password', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 400
        assert b'Kata sandi baru minimal 6 karakter' in response.data
    
    def test_update_preferences_success(self, client, general_user):
        """Test successful preferences update"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        data = {
            'ad_preferences': {
                'show_ads': False
            }
        }
        
        response = client.post('/api/user/preferences', 
                             data=json.dumps(data),
                             content_type='application/json')
        
        assert response.status_code == 200
        assert b'Preferensi berhasil disimpan' in response.data
        
        # Verify preferences were updated
        updated_user = User.query.get(general_user.id)
        assert updated_user.ad_preferences['show_ads'] == False
    
    def test_delete_account_success(self, client, general_user):
        """Test successful account deletion"""
        with client.session_transaction() as sess:
            sess['_user_id'] = general_user.id
        
        user_id = general_user.id
        
        response = client.post('/api/user/delete-account', 
                             content_type='application/json')
        
        assert response.status_code == 200
        assert b'Akun berhasil dihapus' in response.data
        
        # Verify user was deleted
        deleted_user = User.query.get(user_id)
        assert deleted_user is None


# Fixtures for testing
@pytest.fixture
def general_user():
    """Create a general user for testing"""
    user = User(
        username='testuser',
        role=UserRole.GENERAL,
        email='test@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


@pytest.fixture
def admin_user():
    """Create an admin user for testing"""
    user = User(
        username='adminuser',
        role=UserRole.ADMIN,
        email='admin@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()


@pytest.fixture
def another_user():
    """Create another user for testing"""
    user = User(
        username='anotheruser',
        role=UserRole.GENERAL,
        email='another@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    yield user
    db.session.delete(user)
    db.session.commit()
