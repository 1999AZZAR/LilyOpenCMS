from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from enum import Enum
import os
from flask import url_for, current_app, request
import json
import re
import unicodedata
import logging
import random

db = SQLAlchemy()


# Helper function for timezone-aware default timestamp
def default_utcnow():
    return datetime.now(timezone.utc)


# Enums for consistent role and category values
class UserRole(Enum):
    SUPERUSER = "su"
    ADMIN = "admin"
    GENERAL = "general"


# Custom Role and Permission System
class Permission(db.Model):
    __tablename__ = "permission"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    resource = db.Column(db.String(100), nullable=False)  # e.g., 'news', 'users', 'images'
    action = db.Column(db.String(50), nullable=False)     # e.g., 'create', 'read', 'update', 'delete'
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    
    # Many-to-many relationship with roles
    roles = db.relationship(
        "CustomRole",
        secondary="role_permission",
        back_populates="permissions",
        lazy="dynamic"
    )
    
    def __repr__(self):
        return f"<Permission {self.name}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CustomRole(db.Model):
    __tablename__ = "custom_role"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Many-to-many relationship with permissions
    permissions = db.relationship(
        "Permission",
        secondary="role_permission",
        back_populates="roles",
        lazy="dynamic"
    )
    
    # Relationship with users
    users = db.relationship("User", back_populates="custom_role", lazy=True)
    
    def __repr__(self):
        return f"<CustomRole {self.name}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "permissions": [p.to_dict() for p in self.permissions],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Association table for role-permission many-to-many relationship
role_permission = db.Table(
    "role_permission",
    db.Column("role_id", db.Integer, db.ForeignKey("custom_role.id", ondelete="CASCADE"), primary_key=True),
    db.Column("permission_id", db.Integer, db.ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True)
)


# Association table for Editor ↔ Writer self-referential many-to-many
editor_writer = db.Table(
    "editor_writer",
    db.Column("editor_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("writer_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.UniqueConstraint("editor_id", "writer_id", name="uq_editor_writer_pair")
)


class UserActivity(db.Model):
    __tablename__ = "user_activity"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)  # e.g., 'login', 'create_news', 'update_user'
    description = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    
    # Relationship
    user = db.relationship("User", back_populates="activities")
    
    def __repr__(self):
        return f"<UserActivity {self.activity_type} by {self.user_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.activity_type,  # Map activity_type to action for frontend compatibility
            "description": self.description,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.GENERAL)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_premium = db.Column(db.Boolean, default=False, nullable=False)
    tier = db.Column(db.Integer, default=0, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # New fields for enhanced user management
    email = db.Column(db.String(255), unique=True, nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    social_links = db.Column(db.JSON, nullable=True)  # Store social media links as JSON
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0, nullable=False)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)
    suspension_reason = db.Column(db.Text, nullable=True)
    suspension_until = db.Column(db.DateTime, nullable=True)
    # Birthdate for age-based access control
    birthdate = db.Column(db.Date, nullable=True, index=True)
    
    # Use timezone-aware default
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False
    )

    # Foreign key for custom role
    custom_role_id = db.Column(db.Integer, db.ForeignKey("custom_role.id"), nullable=True)
    
    # Subscription-related fields
    has_premium_access = db.Column(db.Boolean, default=False, nullable=False)
    premium_expires_at = db.Column(db.DateTime)
    ad_preferences = db.Column(db.JSON, default=lambda: {"show_ads": True, "ad_frequency": "normal"})
    
    # Relationships - Use back_populates for bidirectional links
    news = db.relationship(
        "News",
        back_populates="author",  # Links to News.author
        lazy=True,
        cascade="all, delete-orphan",
    )
    subscriptions = db.relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan")
    images = db.relationship(
        "Image",
        backref=db.backref(
            "user", lazy=True
        ),  # Keep simple backref if Image doesn't link back explicitly
        lazy=True,
        cascade="all, delete-orphan",
    )
    youtube_videos = db.relationship(
        "YouTubeVideo",
        backref=db.backref(
            "uploader", lazy=True
        ),  # Keep simple backref if YouTubeVideo doesn't link back explicitly
        lazy=True,
        cascade="all, delete-orphan",
    )
    # Use back_populates for SocialMedia creator/updater
    created_social_media = db.relationship(
        "SocialMedia",
        foreign_keys="SocialMedia.created_by",
        back_populates="creator",  # Links to SocialMedia.creator
        lazy=True,
    )
    updated_social_media = db.relationship(
        "SocialMedia",
        foreign_keys="SocialMedia.updated_by",
        back_populates="updater",  # Links to SocialMedia.updater
        lazy=True,
    )
    
    # New relationships for enhanced user management
    custom_role = db.relationship("CustomRole", back_populates="users", lazy=True)
    activities = db.relationship("UserActivity", back_populates="user", lazy=True, cascade="all, delete-orphan")
    # Reader features
    reading_history = db.relationship("ReadingHistory", back_populates="user", lazy=True, cascade="all, delete-orphan")
    library_items = db.relationship("UserLibrary", back_populates="user", lazy=True, cascade="all, delete-orphan")
    # Content relationships with cascade delete
    comments = db.relationship("Comment", back_populates="user", lazy=True, cascade="all, delete-orphan")
    ratings = db.relationship("Rating", back_populates="user", lazy=True, cascade="all, delete-orphan")
    comment_likes = db.relationship("CommentLike", back_populates="user", lazy=True, cascade="all, delete-orphan")
    comment_reports = db.relationship("CommentReport", foreign_keys="CommentReport.user_id", back_populates="user", lazy=True, cascade="all, delete-orphan")
    resolved_reports = db.relationship("CommentReport", foreign_keys="CommentReport.resolved_by", back_populates="resolver", lazy=True)

    # --- Editor ↔ Writer assignments (many-to-many self-referential) ---
    assigned_writers = db.relationship(
        "User",
        secondary=editor_writer,
        primaryjoin=(id == editor_writer.c.editor_id),
        secondaryjoin=(id == editor_writer.c.writer_id),
        backref=db.backref("assigned_editors", lazy="dynamic"),
        lazy="dynamic"
    )

    def set_password(self, password):
        """Hashes and sets the user's password."""
        if not password or len(password.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the user's hashed password."""
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def is_owner(self):
        """Checks if the user is a superuser."""
        return self.role == UserRole.SUPERUSER
    
    def is_admin_tier(self) -> bool:
        """Return True if the user should access the admin dashboard.

        Admin-tier includes SUPERUSER, ADMIN, and anyone assigned an active custom role
        (e.g., writer/editor/subadmin) with elevated permissions.
        """
        if self.role in [UserRole.SUPERUSER, UserRole.ADMIN]:
            return True
        if self.custom_role and self.custom_role.is_active:
            return True
        return False
    
    # ---- Premium helpers ----
    def has_active_premium_subscription(self) -> bool:
        """Check if user has an active premium subscription/access."""
        if not self.has_premium_access:
            return False
        if self.premium_expires_at is None:
            return True
        # Ensure timezone-aware comparison
        expires = self.premium_expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires > datetime.now(timezone.utc)

    def should_show_ads(self) -> bool:
        """Return True if ads should be shown for this user."""
        if self.has_active_premium_subscription():
            return False
        try:
            prefs = self.ad_preferences or {}
            return bool(prefs.get("show_ads", True))
        except Exception:
            return True

    def get_full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    # ---- Age helpers ----
    def get_age(self) -> int:
        """Return the user's age in whole years, or -1 if unknown."""
        if not self.birthdate:
            return -1
        try:
            today = datetime.now(timezone.utc).date()
            years = today.year - self.birthdate.year
            # Adjust if birthday has not occurred yet this year
            if (today.month, today.day) < (self.birthdate.month, self.birthdate.day):
                years -= 1
            return max(years, 0)
        except Exception:
            return -1

    @staticmethod
    def min_age_for_rating(age_rating: str) -> int:
        """Map content rating string to minimum age requirement (years).

        Known values: SU,P,A,3+,7+,13+,17+,18+,21+
        - SU/P/A default to 0
        """
        if not age_rating:
            return 0
        normalized = age_rating.upper().replace(" ", "")
        if normalized in {"R/13+", "R13+"}:
            normalized = "13+"
        if normalized in {"D/17+", "D17+"}:
            normalized = "17+"
        mapping = {
            "SU": 0,
            "P": 0,
            "A": 0,
            "3+": 3,
            "7+": 7,
            "13+": 13,
            "17+": 17,
            "18+": 18,
            "21+": 21,
        }
        return mapping.get(normalized, 0)

    def can_access_age_rating(self, age_rating: str) -> bool:
        """Return True if user's age satisfies the rating requirement.

        If birthdate unknown, return False for restrictive ratings (>=13+), True for SU/P/A.
        """
        min_age = self.min_age_for_rating(age_rating)
        if min_age <= 0:
            return True
        age = self.get_age()
        if age < 0:
            # Unknown age: conservative default
            return False
        return age >= min_age

    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "role": self.role.value if self.role else None,
            "is_verified": self.verified,
            "is_suspended": self.is_suspended,
            "is_premium": self.is_premium,
            "custom_role_id": self.custom_role_id,
            "custom_role": self.custom_role.to_dict() if self.custom_role else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "suspension_reason": self.suspension_reason,
            "suspension_until": self.suspension_until.isoformat() if self.suspension_until else None,
            "has_premium_access": self.has_premium_access,
            "premium_expires_at": self.premium_expires_at.isoformat() if self.premium_expires_at else None,
            "ad_preferences": self.ad_preferences,
            "birthdate": self.birthdate.isoformat() if self.birthdate else None,
            "age": self.get_age(),
        }


class ReadingHistory(db.Model):
    __tablename__ = "reading_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = db.Column(db.String(20), nullable=False)  # 'news' | 'album'
    content_id = db.Column(db.Integer, nullable=False)
    read_count = db.Column(db.Integer, default=1, nullable=False)
    first_read_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    last_read_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)

    user = db.relationship("User", back_populates="reading_history")

    __table_args__ = (
        db.UniqueConstraint("user_id", "content_type", "content_id", name="uq_user_content_reading"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "read_count": self.read_count,
            "first_read_at": self.first_read_at.isoformat() if self.first_read_at else None,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
        }


class UserLibrary(db.Model):
    __tablename__ = "user_library"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = db.Column(db.String(20), nullable=False)  # 'news' | 'album'
    content_id = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)

    user = db.relationship("User", back_populates="library_items")

    __table_args__ = (
        db.UniqueConstraint("user_id", "content_type", "content_id", name="uq_user_content_library"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }
    
    def has_permission(self, resource, action):
        """Check if user has permission for a specific resource and action."""
        # Superusers have all permissions
        if self.role == UserRole.SUPERUSER:
            return True
        
        # Check custom role permissions
        if self.custom_role and self.custom_role.is_active:
            for permission in self.custom_role.permissions:
                if permission.resource == resource and permission.action == action:
                    return True
        
        # Check built-in role permissions
        if self.role == UserRole.ADMIN:
            # Admins can do most things except superuser operations
            if resource == "users" and action in ["delete", "suspend"]:
                return False
            # Explicitly allow ratings and comments for admin
            if resource in ["ratings", "comments"] and action in ["read", "create", "update", "delete"]:
                return True
            return True
        
        # General users have read-only permissions
        if self.role == UserRole.GENERAL:
            if resource == "news" and action in ["read"]:
                return True
            if resource == "images" and action in ["read"]:
                return True
            if resource == "comments" and action in ["read"]:
                return True
            if resource == "ratings" and action in ["read"]:
                return True
            return False
        
        return False
    
    def is_suspended_now(self):
        """Check if user is currently suspended."""
        if not self.is_suspended:
            return False
        if self.suspension_until and self.suspension_until < datetime.now(timezone.utc):
            # Suspension has expired, reactivate user
            self.is_suspended = False
            self.suspension_reason = None
            self.suspension_until = None
            return False
        return True
    
    def get_full_name(self):
        """Get user's full name or username if no name is set."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def record_activity(self, activity_type, description=None, ip_address=None, user_agent=None):
        """Record a user activity."""
        activity = UserActivity(
            user_id=self.id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        # Don't commit here - let the calling function handle the commit
    
    def update_login_info(self, ip_address=None, user_agent=None):
        """Update user's login information."""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1
        self.record_activity("login", "User logged in", ip_address, user_agent)
        db.session.commit()
    
    def has_active_premium_subscription(self):
        """Check if user has an active premium subscription."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        if not self.has_premium_access:
            return False
        
        if self.premium_expires_at:
            # Ensure premium_expires_at is timezone-aware
            if self.premium_expires_at.tzinfo is None:
                # If naive, assume UTC
                premium_expires = self.premium_expires_at.replace(tzinfo=timezone.utc)
            else:
                premium_expires = self.premium_expires_at
            
            if premium_expires < now:
                # Subscription expired, update user status
                self.has_premium_access = False
                self.premium_expires_at = None
                db.session.commit()
                return False
        
        return True
    
    def get_active_subscription(self):
        """Get the user's active subscription if any."""
        if not self.subscriptions:
            return None
        
        active_subscription = None
        for subscription in self.subscriptions:
            if subscription.is_active:
                active_subscription = subscription
                break
        
        return active_subscription
    
    def should_show_ads(self):
        """Check if ads should be shown to this user based on their preferences."""
        if not self.ad_preferences:
            return True
        
        # Premium users with ad-free preference
        if self.has_active_premium_subscription() and self.ad_preferences.get("show_ads") == False:
            return False
        
        return self.ad_preferences.get("show_ads", True)

    def to_dict(self):
        """Converts the user object to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_premium": self.is_premium,
            "tier": self.tier,
            "verified": self.verified,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "profile_picture": self.profile_picture,
            "social_links": self.social_links,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "login_count": self.login_count,
            "is_suspended": self.is_suspended,
            "suspension_reason": self.suspension_reason,
            "suspension_until": self.suspension_until.isoformat() if self.suspension_until else None,
            "custom_role": self.custom_role.to_dict() if self.custom_role else None,
            "has_premium_access": self.has_premium_access,
            "premium_expires_at": self.premium_expires_at.isoformat() if self.premium_expires_at else None,
            "ad_preferences": self.ad_preferences,
            "active_subscription": self.get_active_subscription().to_dict() if self.get_active_subscription() else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.username}>"


class PrivacyPolicy(db.Model):
    __tablename__ = "privacy_policy"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class MediaGuideline(db.Model):
    __tablename__ = "media_guideline"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class VisiMisi(db.Model):
    __tablename__ = "visi_misi"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Penyangkalan(db.Model):
    __tablename__ = "penyangkalan"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class PedomanHak(db.Model):
    __tablename__ = "pedoman_hak"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Image(db.Model):
    __tablename__ = "image"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    filepath = db.Column(db.String(255), nullable=True, unique=True)  # For file uploads
    url = db.Column(db.String(255), nullable=True, unique=True)  # For direct links
    is_visible = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    # Foreign Keys
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # Relationship defined via backref in User.images

    def to_dict(self):
        """Converts the image object to a dictionary."""
        file_url = None
        if self.filepath:
            try:
                # Generate URL relative to static folder
                static_path = (
                    self.filepath.split("static/", 1)[1]
                    if "static/" in self.filepath
                    else self.filepath
                )
                file_url = url_for("static", filename=static_path, _external=True)
            except Exception:
                file_url = self.filepath

        return {
            "id": self.id,
            "filename": self.filename,
            "description": self.description,
            "filepath": self.filepath,
            "file_url": file_url,
            "url": self.url,
            "is_visible": self.is_visible,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
        }

    def delete_file(self):
        """Deletes the associated file from the filesystem."""
        try:
            if self.filepath and os.path.exists(self.filepath):
                os.remove(self.filepath)
        except (OSError, IOError) as e:
            # Log the error but don't raise it
            print(f"Error deleting file {self.filepath}: {e}")


class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    # Relationship back to News using back_populates
    news = db.relationship("News", back_populates="category", lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tagar = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=default_utcnow, nullable=False, index=True)
    read_count = db.Column(db.Integer, default=0, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_main_news = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_news = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Renamed from premium
    is_premium = db.Column(db.Boolean, default=False, nullable=False, index=True)  # New field for membership
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)  # Added for archiving
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )
    writer = db.Column(db.String(100), nullable=True)
    external_source = db.Column(db.String(255), nullable=True)
    # Indonesian content age rating (e.g., SU, 13+, 17+, 21+)
    age_rating = db.Column(db.String(10), nullable=True, index=True)

    # SEO Fields
    meta_description = db.Column(db.String(500), nullable=True)  # Meta description for search engines
    meta_keywords = db.Column(db.String(500), nullable=True)    # Meta keywords for search engines
    og_title = db.Column(db.String(200), nullable=True)         # Open Graph title for social media
    og_description = db.Column(db.String(500), nullable=True)   # Open Graph description for social media
    og_image = db.Column(db.String(255), nullable=True)         # Open Graph image URL for social media
    canonical_url = db.Column(db.String(255), nullable=True)    # Canonical URL to prevent duplicate content
    seo_slug = db.Column(db.String(255), nullable=True, unique=True, index=True)  # SEO-friendly URL slug
    
    # Advanced SEO Fields
    schema_markup = db.Column(db.Text, nullable=True)          # JSON-LD structured data
    twitter_card = db.Column(db.String(50), nullable=True)     # Type of Twitter card (summary, summary_large_image, etc.)
    twitter_title = db.Column(db.String(200), nullable=True)   # Twitter-specific title
    twitter_description = db.Column(db.String(500), nullable=True)  # Twitter-specific description
    twitter_image = db.Column(db.String(255), nullable=True)   # Twitter-specific image URL
    meta_author = db.Column(db.String(100), nullable=True)     # Article author for meta tags
    meta_language = db.Column(db.String(10), nullable=True)    # Content language (en, id, etc.)
    meta_robots = db.Column(db.String(50), nullable=True)      # Robots meta tag (index, noindex, etc.)
    structured_data_type = db.Column(db.String(50), nullable=True)  # Type of structured data (Article, NewsArticle, etc.)
    seo_score = db.Column(db.Integer, nullable=True)           # Calculated SEO score (0-100)
    last_seo_audit = db.Column(db.DateTime, nullable=True)     # Last SEO audit timestamp
    is_seo_lock = db.Column(db.Boolean, default=False, nullable=False)  # Lock SEO fields from automatic updates

    # Foreign Keys with explicit names
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", name="fk_news_category_id"),
        nullable=False,
    )
    # Use back_populates to link back to Category.news
    category = db.relationship("Category", back_populates="news")

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_news_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Use back_populates and rename to 'author' to link back to User.news
    author = db.relationship("User", back_populates="news")
    album_chapters = db.relationship("AlbumChapter", back_populates="news", cascade="all, delete-orphan")

    # Add image_id to connect news to an image (nullable)
    image_id = db.Column(
        db.Integer,
        db.ForeignKey("image.id", name="fk_news_image_id"),
        nullable=True,
    )
    # Keep simple backref if Image doesn't link back explicitly
    image = db.relationship("Image", backref="news")

    def __init__(self, **kwargs):
        super(News, self).__init__(**kwargs)
        # Validation removed from __init__, call it explicitly before adding to session if needed
        # self.validate()

    def validate(self):
        """Validate the news object before saving to the database."""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Title is required")
        if len(self.title) > 200:
            raise ValueError("Title must be less than 200 characters")
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Content is required")
        if self.tagar and len(self.tagar) > 255:
            raise ValueError("Tags must be less than 255 characters")
        if not self.category_id:
            raise ValueError("Category is required")
        if not self.user_id:
            raise ValueError("User (author) is required")
        
        # SEO validation
        if self.meta_description and len(self.meta_description) > 500:
            raise ValueError("Meta description must be less than 500 characters")
        if self.meta_keywords and len(self.meta_keywords) > 500:
            raise ValueError("Meta keywords must be less than 500 characters")
        if self.og_title and len(self.og_title) > 200:
            raise ValueError("Open Graph title must be less than 200 characters")
        if self.og_description and len(self.og_description) > 500:
            raise ValueError("Open Graph description must be less than 500 characters")
        if self.canonical_url and len(self.canonical_url) > 255:
            raise ValueError("Canonical URL must be less than 255 characters")
        if self.seo_slug and len(self.seo_slug) > 255:
            raise ValueError("SEO slug must be less than 255 characters")
        
        # Advanced SEO validation
        if self.twitter_title and len(self.twitter_title) > 200:
            raise ValueError("Twitter title must be less than 200 characters")
        if self.twitter_description and len(self.twitter_description) > 500:
            raise ValueError("Twitter description must be less than 500 characters")
        if self.twitter_image and len(self.twitter_image) > 255:
            raise ValueError("Twitter image URL must be less than 255 characters")
        if self.meta_author and len(self.meta_author) > 100:
            raise ValueError("Meta author must be less than 100 characters")
        if self.meta_language and len(self.meta_language) > 10:
            raise ValueError("Meta language must be less than 10 characters")
        if self.meta_robots and len(self.meta_robots) > 50:
            raise ValueError("Meta robots must be less than 50 characters")
        if self.structured_data_type and len(self.structured_data_type) > 50:
            raise ValueError("Structured data type must be less than 50 characters")
        if self.seo_score and (self.seo_score < 0 or self.seo_score > 100):
            raise ValueError("SEO score must be between 0 and 100")

    def calculate_seo_score(self):
        """Calculate SEO score based on completeness of SEO fields."""
        score = 0
        total_fields = 10  # Total number of SEO fields to check
        
        # Basic SEO fields (40 points)
        if self.meta_description and len(self.meta_description.strip()) > 0:
            score += 8
        if self.meta_keywords and len(self.meta_keywords.strip()) > 0:
            score += 4
        if self.seo_slug and len(self.seo_slug.strip()) > 0:
            score += 4
        if self.canonical_url and len(self.canonical_url.strip()) > 0:
            score += 4
        
        # Open Graph fields (30 points)
        if self.og_title and len(self.og_title.strip()) > 0:
            score += 10
        if self.og_description and len(self.og_description.strip()) > 0:
            score += 10
        if self.og_image and len(self.og_image.strip()) > 0:
            score += 10
        
        # Twitter fields (20 points)
        if self.twitter_title and len(self.twitter_title.strip()) > 0:
            score += 5
        if self.twitter_description and len(self.twitter_description.strip()) > 0:
            score += 5
        if self.twitter_image and len(self.twitter_image.strip()) > 0:
            score += 5
        if self.twitter_card and len(self.twitter_card.strip()) > 0:
            score += 5
        
        # Advanced fields (10 points)
        if self.schema_markup and len(self.schema_markup.strip()) > 0:
            score += 5
        if self.structured_data_type and len(self.structured_data_type.strip()) > 0:
            score += 5
        
        return min(score, 100)  # Cap at 100

    def generate_schema_markup(self):
        """Generate JSON-LD structured data for the news article."""
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle" if self.is_news else "Article",
            "headline": self.title,
            "description": self.meta_description or self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "author": {
                "@type": "Person",
                "name": self.writer or self.author.username
            },
            "datePublished": self.date.isoformat(),
            "dateModified": self.updated_at.isoformat(),
            "publisher": {
                "@type": "Organization",
                "name": "LilyOpenCMS",
                "logo": {
                    "@type": "ImageObject",
                    "url": url_for('static', filename='pic/logo.png', _external=True)
                }
            }
        }
        
        if self.image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": self.image.to_dict()["file_url"],
                "width": 1200,
                "height": 630
            }
        
        if self.category:
            schema["articleSection"] = self.category.name
        
        return json.dumps(schema, ensure_ascii=False)

    def generate_seo_slug(self):
        """Generate SEO-friendly slug from title."""
        if not self.title:
            return None
        
        # Convert to lowercase and replace spaces with hyphens
        slug = self.title.lower()
        # Remove special characters except hyphens and underscores
        slug = re.sub(r'[^a-z0-9\s\-_]', '', slug)
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Remove leading and trailing hyphens
        slug = slug.strip('-')
        
        # Ensure uniqueness by appending ID if needed
        if self.id:
            base_slug = slug
            counter = 1
            while News.query.filter_by(seo_slug=slug).filter(News.id != self.id).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
        
        return slug

    def update_seo_fields(self):
        """Update SEO-related fields automatically."""
        if not self.seo_slug:
            self.seo_slug = self.generate_seo_slug()
        
        if not self.schema_markup:
            self.schema_markup = self.generate_schema_markup()
        
        if not self.meta_author:
            self.meta_author = self.writer or self.author.username
        
        if not self.meta_language:
            self.meta_language = "id"  # Indonesian
        
        if not self.meta_robots:
            self.meta_robots = "index, follow"
        
        if not self.structured_data_type:
            self.structured_data_type = "NewsArticle" if self.is_news else "Article"
        
        # Calculate SEO score
        self.seo_score = self.calculate_seo_score()
        self.last_seo_audit = datetime.now(timezone.utc)

    def increment_reads(self):
        """Increment the read count for this news article."""
        self.read_count += 1
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error incrementing read count for news {self.id}: {e}")
            db.session.rollback()

    def to_dict(self):
        """Converts the news object to a dictionary."""
        # Get share data if available
        share_data = None
        if hasattr(self, 'share_log') and self.share_log:
            share_data = self.share_log.to_dict()
        
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "tagar": self.tagar,
            "date": self.date.isoformat(),
            "read_count": self.read_count,
            "is_visible": self.is_visible,
            "is_main_news": self.is_main_news,
            "is_news": self.is_news,
            "is_premium": self.is_premium,
            "is_archived": self.is_archived,
            "writer": self.writer,
            "external_source": self.external_source,
            "age_rating": self.age_rating,
            "category": self.category.to_dict() if self.category else None,
            "author": self.author.to_dict() if self.author else None,
            "image": self.image.to_dict() if self.image else None,
            "share_data": share_data,
            "seo_score": self.seo_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<News {self.title}>"


class Album(db.Model):
    """Model for grouping news articles into albums/chapters like a novel."""
    __tablename__ = "album"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_image_id = db.Column(db.Integer, db.ForeignKey("image.id"), nullable=True)
    is_visible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_premium = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_hiatus = db.Column(db.Boolean, default=False, nullable=False, index=True)
    total_chapters = db.Column(db.Integer, default=0, nullable=False)
    total_reads = db.Column(db.Integer, default=0, nullable=False)
    total_views = db.Column(db.Integer, default=0, nullable=False)
    average_rating = db.Column(db.Float, default=0.0, nullable=False)
    # Indonesian content age rating (e.g., SU, 13+, 17+, 21+)
    age_rating = db.Column(db.String(10), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    # SEO Fields
    meta_description = db.Column(db.String(500), nullable=True)  # Meta description for search engines
    meta_keywords = db.Column(db.String(500), nullable=True)    # Meta keywords for search engines
    og_title = db.Column(db.String(200), nullable=True)         # Open Graph title for social media
    og_description = db.Column(db.String(500), nullable=True)   # Open Graph description for social media
    og_image = db.Column(db.String(255), nullable=True)         # Open Graph image URL for social media
    canonical_url = db.Column(db.String(255), nullable=True)    # Canonical URL to prevent duplicate content
    seo_slug = db.Column(db.String(255), nullable=True, unique=True, index=True)  # SEO-friendly URL slug
    
    # Advanced SEO Fields
    schema_markup = db.Column(db.Text, nullable=True)          # JSON-LD structured data
    twitter_card = db.Column(db.String(50), nullable=True)     # Type of Twitter card (summary, summary_large_image, etc.)
    twitter_title = db.Column(db.String(200), nullable=True)   # Twitter-specific title
    twitter_description = db.Column(db.String(500), nullable=True)  # Twitter-specific description
    twitter_image = db.Column(db.String(255), nullable=True)   # Twitter-specific image URL
    meta_author = db.Column(db.String(100), nullable=True)     # Album author for meta tags
    meta_language = db.Column(db.String(10), nullable=True)    # Content language (en, id, etc.)
    meta_robots = db.Column(db.String(50), nullable=True)      # Robots meta tag (index, noindex, etc.)
    structured_data_type = db.Column(db.String(50), nullable=True)  # Type of structured data (Book, CreativeWork, etc.)
    seo_score = db.Column(db.Integer, nullable=True)           # Calculated SEO score (0-100)
    last_seo_audit = db.Column(db.DateTime, nullable=True)     # Last SEO audit timestamp
    is_seo_lock = db.Column(db.Boolean, default=False, nullable=False)  # Lock SEO fields from automatic updates

    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_album_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", name="fk_album_category_id"),
        nullable=False,
    )

    # Relationships
    author = db.relationship("User", backref="albums")
    category = db.relationship("Category", backref="albums")
    cover_image = db.relationship("Image", backref="album_covers")
    chapters = db.relationship("AlbumChapter", back_populates="album", order_by="AlbumChapter.chapter_number", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super(Album, self).__init__(**kwargs)

    def validate(self):
        """Validate the album object before saving to the database."""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Title is required")
        if len(self.title) > 200:
            raise ValueError("Title must be less than 200 characters")
        if not self.category_id:
            raise ValueError("Category is required")
        if not self.user_id:
            raise ValueError("User (author) is required")

    def update_chapter_count(self):
        """Update the total chapter count."""
        self.total_chapters = len(self.chapters)
        self.total_reads = sum(chapter.news.read_count for chapter in self.chapters if chapter.news)

    def increment_views(self):
        """Increment the view count for this album."""
        self.total_views += 1
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error incrementing view count for album {self.id}: {e}")
            db.session.rollback()

    def calculate_seo_score(self):
        """Calculate SEO score for the album (0-100)."""
        score = 0
        
        # Basic SEO elements (40 points)
        if self.title and len(self.title.strip()) > 0:
            score += 10
        if self.description and len(self.description.strip()) > 0:
            score += 10
        if self.meta_description and len(self.meta_description.strip()) > 0:
            score += 10
        if self.meta_keywords and len(self.meta_keywords.strip()) > 0:
            score += 10
        
        # Social media optimization (30 points)
        if self.og_title and len(self.og_title.strip()) > 0:
            score += 10
        if self.og_description and len(self.og_description.strip()) > 0:
            score += 10
        if self.og_image and len(self.og_image.strip()) > 0:
            score += 10
        
        # Advanced SEO elements (30 points)
        if self.seo_slug and len(self.seo_slug.strip()) > 0:
            score += 10
        if self.canonical_url and len(self.canonical_url.strip()) > 0:
            score += 10
        if self.schema_markup and len(self.schema_markup.strip()) > 0:
            score += 10
        
        return min(score, 100)

    def generate_schema_markup(self):
        """Generate JSON-LD structured data for the album."""
        import json
        from datetime import datetime
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Book" if self.is_completed else "CreativeWork",
            "name": self.title,
            "description": self.description or self.title,
            "author": {
                "@type": "Person",
                "name": self.author.get_full_name() if self.author else "Unknown Author"
            },
            "publisher": {
                "@type": "Organization",
                "name": "LilyOpenCMS"
            },
            "datePublished": self.created_at.isoformat() if self.created_at else None,
            "dateModified": self.updated_at.isoformat() if self.updated_at else None,
            "numberOfPages": self.total_chapters,
            "isAccessibleForFree": not self.is_premium,
            "inLanguage": self.meta_language or "id",
            "genre": self.category.name if self.category else None,
            "url": self.canonical_url or f"/album/{self.id}",
        }
        
        # Add book-specific properties if completed
        if self.is_completed:
            schema["bookFormat"] = "Digital"
            schema["isbn"] = f"ALBUM-{self.id:06d}"
        
        # Add image if available
        if self.cover_image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": self.cover_image.url or self.cover_image.filepath,
                "width": 800,
                "height": 600
            }
        
        return json.dumps(schema, ensure_ascii=False)

    def generate_seo_slug(self):
        """Generate SEO-friendly slug from title."""
        import re
        import unicodedata
        
        if not self.title:
            return None
        
        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', self.title)
        
        # Convert to lowercase and replace spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-').lower()
        
        # Limit length
        if len(slug) > 50:
            slug = slug[:50]
        
        return slug

    def update_seo_fields(self):
        """Update SEO-related fields automatically."""
        from datetime import datetime
        
        # Generate SEO slug if not set
        if not self.seo_slug:
            self.seo_slug = self.generate_seo_slug()
        
        # Generate schema markup
        self.schema_markup = self.generate_schema_markup()
        
        # Set default meta author if not set
        if not self.meta_author and self.author:
            self.meta_author = self.author.get_full_name()
        
        # Set default language if not set
        if not self.meta_language:
            self.meta_language = "id"
        
        # Set default robots if not set
        if not self.meta_robots:
            self.meta_robots = "index, follow"
        
        # Set default Twitter card if not set
        if not self.twitter_card:
            self.twitter_card = "summary_large_image"
        
        # Calculate SEO score
        self.seo_score = self.calculate_seo_score()
        
        # Update last SEO audit timestamp
        self.last_seo_audit = datetime.utcnow()

    def to_dict(self):
        """Converts the album object to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "cover_image": self.cover_image.to_dict() if self.cover_image else None,
            "is_visible": self.is_visible,
            "is_premium": self.is_premium,
            "is_archived": self.is_archived,
            "is_completed": self.is_completed,
            "is_hiatus": self.is_hiatus,
            "total_chapters": self.total_chapters,
            "total_reads": self.total_reads,
            "total_views": self.total_views,
            "average_rating": self.average_rating,
            "age_rating": self.age_rating,
            "category": self.category.to_dict() if self.category else None,
            "author": self.author.to_dict() if self.author else None,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # SEO Fields
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "og_title": self.og_title,
            "og_description": self.og_description,
            "og_image": self.og_image,
            "canonical_url": self.canonical_url,
            "seo_slug": self.seo_slug,
            "schema_markup": self.schema_markup,
            "twitter_card": self.twitter_card,
            "twitter_title": self.twitter_title,
            "twitter_description": self.twitter_description,
            "twitter_image": self.twitter_image,
            "meta_author": self.meta_author,
            "meta_language": self.meta_language,
            "meta_robots": self.meta_robots,
            "structured_data_type": self.structured_data_type,
            "seo_score": self.seo_score,
            "last_seo_audit": self.last_seo_audit.isoformat() if self.last_seo_audit else None,
        }

    def get_chapter_ratings(self):
        """Get all chapter ratings for this album with their weights."""
        from datetime import datetime
        
        chapter_ratings = []
        
        # First, collect all chapters with ratings
        chapters_with_ratings = []
        for chapter in self.chapters:
            if not chapter.news:
                continue
            if not Rating.has_ratings('news', chapter.news.id):
                continue
            chapters_with_ratings.append(chapter)
        
        # Calculate max_read_count only from chapters with ratings
        if chapters_with_ratings:
            max_read_count = max([c.news.read_count for c in chapters_with_ratings])
            if max_read_count == 0:
                max_read_count = 1  # fallback, but should not happen
        else:
            max_read_count = 1  # fallback, but should not happen
        
        for chapter in chapters_with_ratings:
            chapter_avg_rating = Rating.get_average_rating('news', chapter.news.id)
            chapter_rating_count = Rating.get_rating_count('news', chapter.news.id)
            popularity_multiplier = 1 + (chapter.news.read_count / max_read_count) * 0.5
            chapter_ratings.append({
                'chapter_number': chapter.chapter_number,
                'chapter_title': chapter.chapter_title,
                'news_id': chapter.news.id,
                'rating': chapter_avg_rating,
                'rating_count': chapter_rating_count,
                'read_count': chapter.news.read_count,
                'weight': popularity_multiplier
            })
        
        return chapter_ratings

    def calculate_weighted_rating(self):
        """Calculate weighted rating based on chapter ratings and popularity."""
        chapter_ratings = self.get_chapter_ratings()
        
        if not chapter_ratings:
            return 0.0
        
        total_weighted_rating = 0.0
        total_weight = 0.0
        
        for chapter_data in chapter_ratings:
            weighted_rating = chapter_data['rating'] * chapter_data['weight']
            total_weighted_rating += weighted_rating
            total_weight += chapter_data['weight']
        
        if total_weight == 0:
            return 0.0
        
        return round(total_weighted_rating / total_weight, 2)

    def get_weighted_rating_stats(self):
        """Get comprehensive weighted rating statistics for the album."""
        chapter_ratings = self.get_chapter_ratings()
        
        # Get direct album ratings
        direct_album_ratings = Rating.query.filter_by(
            content_type='album',
            content_id=self.id
        ).all()
        
        direct_album_count = len(direct_album_ratings)
        direct_album_avg = None
        if direct_album_count > 0:
            direct_album_avg = sum(r.rating_value for r in direct_album_ratings) / direct_album_count
        
        # Calculate weighted average from chapters
        weighted_average = self.calculate_weighted_rating() if chapter_ratings else 0.0
        
        # Calculate total ratings across all chapters
        total_chapter_ratings = sum(chapter['rating_count'] for chapter in chapter_ratings)
        
        # Total ratings = chapter ratings + direct album ratings
        total_ratings = total_chapter_ratings + direct_album_count
        
        # Calculate rating distribution across all chapters
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for chapter_data in chapter_ratings:
            chapter_distribution = Rating.get_rating_distribution('news', chapter_data['news_id'])
            for rating, count in chapter_distribution.items():
                rating_distribution[rating] += count
        
        # Add direct album ratings to distribution
        for rating in direct_album_ratings:
            rating_distribution[rating.rating_value] += 1
        
        # Calculate overall average (weighted chapter average + direct album average)
        overall_average = 0.0
        if total_ratings > 0:
            if chapter_ratings and direct_album_count > 0:
                # Combine weighted chapter average with direct album average
                chapter_weight = total_chapter_ratings / total_ratings
                album_weight = direct_album_count / total_ratings
                overall_average = (weighted_average * chapter_weight) + (direct_album_avg * album_weight)
            elif chapter_ratings:
                overall_average = weighted_average
            else:
                overall_average = direct_album_avg
        
        # Debug logging to help identify issues
        logging.info(f"Album {self.id} ({self.title}) rating stats:")
        logging.info(f"  - Chapter ratings: {len(chapter_ratings)} chapters with ratings")
        logging.info(f"  - Direct album ratings: {direct_album_count}")
        logging.info(f"  - Total ratings: {total_ratings}")
        logging.info(f"  - Overall average: {overall_average}")
        
        return {
            'weighted_average': round(overall_average, 2),
            'total_chapters_rated': len(chapter_ratings),
            'total_ratings': total_ratings,
            'chapter_breakdown': chapter_ratings,
            'rating_distribution': rating_distribution,
            'direct_album_ratings': direct_album_count,
            'direct_album_average': round(direct_album_avg, 2) if direct_album_avg else None,
            'chapter_weighted_average': round(weighted_average, 2) if chapter_ratings else 0.0
        }

    def __repr__(self):
        return f"<Album {self.title}>"


class AlbumChapter(db.Model):
    """Model for individual chapters within an album."""
    __tablename__ = "album_chapter"

    id = db.Column(db.Integer, primary_key=True)
    chapter_number = db.Column(db.Integer, nullable=False)
    chapter_title = db.Column(db.String(200), nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    # SEO Fields
    meta_description = db.Column(db.String(500), nullable=True)  # Meta description for search engines
    meta_keywords = db.Column(db.String(500), nullable=True)    # Meta keywords for search engines
    og_title = db.Column(db.String(200), nullable=True)         # Open Graph title for social media
    og_description = db.Column(db.String(500), nullable=True)   # Open Graph description for social media
    og_image = db.Column(db.String(255), nullable=True)         # Open Graph image URL for social media
    canonical_url = db.Column(db.String(255), nullable=True)    # Canonical URL to prevent duplicate content
    seo_slug = db.Column(db.String(255), nullable=True, unique=True, index=True)  # SEO-friendly URL slug
    
    # Advanced SEO Fields
    schema_markup = db.Column(db.Text, nullable=True)          # JSON-LD structured data
    twitter_card = db.Column(db.String(50), nullable=True)     # Type of Twitter card (summary, summary_large_image, etc.)
    twitter_title = db.Column(db.String(200), nullable=True)   # Twitter-specific title
    twitter_description = db.Column(db.String(500), nullable=True)  # Twitter-specific description
    twitter_image = db.Column(db.String(255), nullable=True)   # Twitter-specific image URL
    meta_author = db.Column(db.String(100), nullable=True)     # Chapter author for meta tags
    meta_language = db.Column(db.String(10), nullable=True)    # Content language (en, id, etc.)
    meta_robots = db.Column(db.String(50), nullable=True)      # Robots meta tag (index, noindex, etc.)
    structured_data_type = db.Column(db.String(50), nullable=True)  # Type of structured data (Chapter, CreativeWork, etc.)
    seo_score = db.Column(db.Integer, nullable=True)           # Calculated SEO score (0-100)
    last_seo_audit = db.Column(db.DateTime, nullable=True)     # Last SEO audit timestamp
    is_seo_lock = db.Column(db.Boolean, default=False, nullable=False)  # Lock SEO fields from automatic updates

    # Foreign Keys
    album_id = db.Column(
        db.Integer,
        db.ForeignKey("album.id", name="fk_album_chapter_album_id", ondelete="CASCADE"),
        nullable=False,
    )
    news_id = db.Column(
        db.Integer,
        db.ForeignKey("news.id", name="fk_album_chapter_news_id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    album = db.relationship("Album", back_populates="chapters")
    news = db.relationship("News", back_populates="album_chapters")

    def __init__(self, **kwargs):
        super(AlbumChapter, self).__init__(**kwargs)

    def validate(self):
        """Validate the album chapter object before saving to the database."""
        if not self.chapter_title or len(self.chapter_title.strip()) == 0:
            raise ValueError("Chapter title is required")
        if len(self.chapter_title) > 200:
            raise ValueError("Chapter title must be less than 200 characters")
        if not self.album_id:
            raise ValueError("Album is required")
        if not self.news_id:
            raise ValueError("News article is required")
        if self.chapter_number < 1:
            raise ValueError("Chapter number must be at least 1")

    def to_dict(self):
        """Converts the album chapter object to a dictionary."""
        return {
            "id": self.id,
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "is_visible": self.is_visible,
            "news": self.news.to_dict() if self.news else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f"<AlbumChapter {self.chapter_number}: {self.chapter_title}>"


class YouTubeVideo(db.Model):
    __tablename__ = "youtube_video"

    id = db.Column(db.Integer, primary_key=True)
    youtube_id = db.Column(db.String(11), unique=True, nullable=False, index=True)
    link = db.Column(db.String(255), unique=True, nullable=False)
    # metadata fields fetched from YouTube
    title = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # length in seconds
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    # Foreign Key
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_youtube_video_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Relationship defined via backref in User.youtube_videos

    def __init__(self, **kwargs):
        super(YouTubeVideo, self).__init__(**kwargs)
        # Validation removed from __init__, call it explicitly before adding to session if needed
        # self.validate()

    def validate(self):
        """Validate the YouTube video object before saving."""
        if not self.youtube_id or len(self.youtube_id.strip()) != 11:
            raise ValueError("YouTube ID must be exactly 11 characters")
        if not self.link or (
            "youtube.com" not in self.link.lower()
            and "youtu.be" not in self.link.lower()
        ):
            raise ValueError("Valid YouTube or YouTu.be URL is required")
        if not self.user_id:
            raise ValueError("Uploader user ID is required")

    def to_dict(self):
        """Converts the YouTube video object to a dictionary."""
        return {
            "id": self.id,
            "youtube_id": self.youtube_id,
            "title": self.title,
            "duration": self.duration,
            "link": self.link,
            "is_visible": self.is_visible,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
            "uploader": self.uploader.username if self.uploader else "Unknown",
        }

    def __repr__(self):
        return f"<YouTubeVideo {self.youtube_id}>"


class ShareLog(db.Model):
    __tablename__ = "share_log"

    id = db.Column(db.Integer, primary_key=True)
    news_id = db.Column(
        db.Integer,
        db.ForeignKey("news.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    whatsapp_count = db.Column(db.Integer, default=0, nullable=False)
    facebook_count = db.Column(db.Integer, default=0, nullable=False)
    twitter_count = db.Column(db.Integer, default=0, nullable=False)
    instagram_count = db.Column(db.Integer, default=0, nullable=False)
    bluesky_count = db.Column(db.Integer, default=0, nullable=False)
    clipboard_count = db.Column(db.Integer, default=0, nullable=False)
    first_shared_at = db.Column(db.DateTime, nullable=True)
    latest_shared_at = db.Column(db.DateTime, nullable=True)

    # Relationship to the News table
    news = db.relationship("News", backref=db.backref("share_log", uselist=False))

    def to_dict(self):
        """Converts the ShareLog object to a dictionary."""
        return {
            "id": self.id,
            "news_id": self.news_id,
            "whatsapp_count": self.whatsapp_count,
            "facebook_count": self.facebook_count,
            "twitter_count": self.twitter_count,
            "instagram_count": self.instagram_count,
            "bluesky_count": self.bluesky_count,
            "clipboard_count": self.clipboard_count,
            "first_shared_at": self.first_shared_at.isoformat()
            if self.first_shared_at
            else None,
            "latest_shared_at": self.latest_shared_at.isoformat()
            if self.latest_shared_at
            else None,
            # Optionally include total count
            "total_shares": (
                self.whatsapp_count
                + self.facebook_count
                + self.twitter_count
                + self.instagram_count
                + self.bluesky_count
                + self.clipboard_count
            ),
        }


class SocialMedia(db.Model):
    __tablename__ = "social_media"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,  # Allow user deletion without deleting social media link
    )
    updated_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,  # Allow user deletion without deleting social media link
    )

    # Define relationships using back_populates
    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_social_media",  # Links to User.created_social_media
        lazy=True,
    )
    updater = db.relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="updated_social_media",  # Links to User.updated_social_media
        lazy=True,
    )

    def to_dict(self):
        """Converts the social media object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "creator_name": self.creator.username if self.creator else None,
            "updater_name": self.updater.username if self.updater else None,
        }

    def __repr__(self):
        return f"<SocialMedia {self.name}>"


class ContactDetail(db.Model):
    __tablename__ = "contact_detail"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    section_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    icon_class = db.Column(db.String(100), nullable=True)  # e.g. 'envelope'
    link = db.Column(db.String(255), nullable=True)  # e.g. 'mailto:you@example.com'
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "section_order": self.section_order,
            "is_active": self.is_active,
            "icon_class": self.icon_class,
            "link": self.link,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TeamMember(db.Model):
    __tablename__ = "team_member"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)  # Role or position
    group = db.Column(
        db.String(50), nullable=False
    )  # e.g.: leadership, editorial, news, video, sales
    member_order = db.Column(db.Integer, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False
    )

    @property
    def initials(self):
        parts = [p for p in self.name.split() if p]
        return "".join(p[0].upper() for p in parts)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "group": self.group,
            "member_order": self.member_order,
            "is_active": self.is_active,
            "initials": self.initials,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class BrandIdentity(db.Model):
    """
    Stores brand identity information including name, tagline, and asset URLs.
    Each image field always points to a fixed file in static/pic/:
      - logo_header: /static/pic/logo.png
      - logo_footer: /static/pic/logo_footer.png
      - favicon: /static/pic/favicon.png
      - placeholder_image: /static/pic/placeholder.png
    """
    __tablename__ = "brand_identity"
    id = db.Column(db.Integer, primary_key=True)
    
    # Brand Information
    brand_name = db.Column(db.String(100), nullable=True, default="LilyOpenCMS")  # Brand name
    tagline = db.Column(db.String(255), nullable=True, default="Modern content management for the digital age")  # Brand tagline
    
    # Homepage Design Preference
    homepage_design = db.Column(db.String(50), nullable=True, default="news")  # 'news' or 'albums'
    
    # Categories Display Location
    categories_display_location = db.Column(db.String(50), nullable=True, default="body")  # 'body' or 'navbar'
    
    # News Card Design Preference
    card_design = db.Column(db.String(50), nullable=True, default="classic")  # 'classic', 'modern', 'minimal', 'featured'
    
    # Brand Assets
    logo_header = db.Column(db.String(255), nullable=True)  # Always /static/pic/logo.png
    logo_footer = db.Column(db.String(255), nullable=True)  # Always /static/pic/logo_footer.png
    favicon = db.Column(db.String(255), nullable=True)      # Always /static/pic/favicon.png
    placeholder_image = db.Column(db.String(255), nullable=True)  # Always /static/pic/placeholder.png
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)

    # Display settings (site-wide feature toggles)
    enable_comments = db.Column(db.Boolean, nullable=False, default=True)
    enable_ratings = db.Column(db.Boolean, nullable=False, default=True)
    enable_ads = db.Column(db.Boolean, nullable=False, default=True)
    enable_campaigns = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "brand_name": self.brand_name,
            "tagline": self.tagline,
            "homepage_design": self.homepage_design,
            "categories_display_location": getattr(self, 'categories_display_location', None) or "body",
            "card_design": getattr(self, 'card_design', None) or "classic",
            "logo_header": self.logo_header,
            "logo_footer": self.logo_footer,
            "favicon": self.favicon,
            "placeholder_image": self.placeholder_image,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "enable_comments": self.enable_comments,
            "enable_ratings": self.enable_ratings,
            "enable_ads": self.enable_ads,
            "enable_campaigns": self.enable_campaigns,
        }




class UserSubscription(db.Model):
    __tablename__ = "user_subscriptions"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)  # 'monthly', 'yearly'
    status = db.Column(db.String(50), nullable=False, default='active')  # 'active', 'cancelled', 'expired'
    start_date = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    payment_provider = db.Column(db.String(50))  # 'stripe', 'paypal', etc.
    payment_id = db.Column(db.String(255))  # External payment ID
    amount = db.Column(db.Numeric(10, 2), nullable=False)  # Subscription amount
    currency = db.Column(db.String(3), default='IDR')
    auto_renew = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationship
    user = db.relationship("User", back_populates="subscriptions")
    
    def to_dict(self):
        """Converts the UserSubscription object to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "subscription_type": self.subscription_type,
            "status": self.status,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "payment_provider": self.payment_provider,
            "payment_id": self.payment_id,
            "amount": float(self.amount) if self.amount else None,
            "currency": self.currency,
            "auto_renew": self.auto_renew,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @property
    def is_active(self):
        """Return True if the subscription is currently active."""
        now = datetime.now(timezone.utc)
        if self.status != 'active':
            return False
        if self.end_date is None:
            return True
        end = self.end_date
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        return end > now


class Comment(db.Model):
    """Model for user comments on news articles and albums."""
    __tablename__ = "comment"
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_spam = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Polymorphic fields for content type
    content_type = db.Column(db.String(50), nullable=False, index=True)  # 'news' or 'album'
    content_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_comment_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("comment.id", name="fk_comment_parent_id", ondelete="CASCADE"),
        nullable=True,
    )
    
    # Relationships
    user = db.relationship("User", back_populates="comments")
    parent = db.relationship("Comment", remote_side=[id], backref="replies")
    likes = db.relationship("CommentLike", back_populates="comment", cascade="all, delete-orphan")
    reports = db.relationship("CommentReport", back_populates="comment", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
    
    def validate(self):
        """Validate the comment before saving."""
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Comment content cannot be empty")
        
        if len(self.content) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")
        
        if self.content_type not in ['news', 'album']:
            raise ValueError("Content type must be 'news' or 'album'")
    
    def get_content_object(self):
        """Get the content object (News or Album) that this comment belongs to."""
        if self.content_type == 'news':
            return News.query.get(self.content_id)
        elif self.content_type == 'album':
            return Album.query.get(self.content_id)
        return None
    
    def get_likes_count(self):
        """Get the number of likes for this comment."""
        return CommentLike.query.filter_by(
            comment_id=self.id, 
            is_like=True, 
            is_deleted=False
        ).count()
    
    def get_dislikes_count(self):
        """Get the number of dislikes for this comment."""
        return CommentLike.query.filter_by(
            comment_id=self.id, 
            is_like=False, 
            is_deleted=False
        ).count()
    
    def is_liked_by_user(self, user_id):
        """Check if a user has liked this comment."""
        like = CommentLike.query.filter_by(
            comment_id=self.id,
            user_id=user_id,
            is_like=True,
            is_deleted=False
        ).first()
        return like is not None
    
    def is_disliked_by_user(self, user_id):
        """Check if a user has disliked this comment."""
        dislike = CommentLike.query.filter_by(
            comment_id=self.id,
            user_id=user_id,
            is_like=False,
            is_deleted=False
        ).first()
        return dislike is not None
    
    def to_dict(self):
        """Converts the Comment object to a dictionary."""
        user_data = None
        if self.user is not None:
            try:
                user_data = {
                    "id": self.user.id,
                    "username": self.user.username,
                    "first_name": getattr(self.user, "first_name", None),
                    "last_name": getattr(self.user, "last_name", None),
                    "profile_picture": getattr(self.user, "profile_picture", None),
                    "role": getattr(self.user.role, "value", None),
                }
            except Exception:
                user_data = {"id": self.user_id}

        return {
            "id": self.id,
            "content": self.content,
            "is_approved": self.is_approved,
            "is_spam": self.is_spam,
            "is_deleted": self.is_deleted,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "parent_id": self.parent_id,
            "user_id": self.user_id,
            "user": user_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "likes_count": self.get_likes_count(),
            "dislikes_count": self.get_dislikes_count(),
            "replies_count": len([r for r in self.replies if not r.is_deleted]),
        }
    
    def __repr__(self):
        return f"<Comment {self.id} by User {self.user_id} on {self.content_type} {self.content_id}>"


class Rating(db.Model):
    """Model for user ratings on news articles and albums."""
    __tablename__ = "rating"
    
    id = db.Column(db.Integer, primary_key=True)
    rating_value = db.Column(db.Integer, nullable=False)  # 1-5 stars
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Polymorphic fields for content type
    content_type = db.Column(db.String(50), nullable=False, index=True)  # 'news' or 'album'
    content_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_rating_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    user = db.relationship("User", back_populates="ratings")
    
    # Unique constraint to prevent duplicate ratings
    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_type', 'content_id', name='uq_user_content_rating'),
    )
    
    def __init__(self, **kwargs):
        super(Rating, self).__init__(**kwargs)
    
    def validate(self):
        """Validate the rating before saving."""
        if not self.rating_value or self.rating_value < 1 or self.rating_value > 5:
            raise ValueError("Rating value must be between 1 and 5")
        
        if self.content_type not in ['news', 'album']:
            raise ValueError("Content type must be 'news' or 'album'")
    
    def get_content_object(self):
        """Get the content object (News or Album) that this rating belongs to."""
        if self.content_type == 'news':
            return News.query.get(self.content_id)
        elif self.content_type == 'album':
            return Album.query.get(self.content_id)
        return None
    
    @staticmethod
    def get_average_rating(content_type, content_id):
        """Get the average rating for a specific content."""
        result = db.session.query(db.func.avg(Rating.rating_value)).filter_by(
            content_type=content_type,
            content_id=content_id
        ).scalar()
        return round(result, 2) if result is not None else None
    
    @staticmethod
    def has_ratings(content_type, content_id):
        """Check if a content has any ratings."""
        return Rating.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).count() > 0
    
    @staticmethod
    def get_rating_count(content_type, content_id):
        """Get the total number of ratings for a specific content."""
        return Rating.query.filter_by(
            content_type=content_type,
            content_id=content_id
        ).count()
    
    @staticmethod
    def get_rating_distribution(content_type, content_id):
        """Get the distribution of ratings (how many 1-star, 2-star, etc.)."""
        distribution = {}
        for i in range(1, 6):
            count = Rating.query.filter_by(
                content_type=content_type,
                content_id=content_id,
                rating_value=i
            ).count()
            distribution[i] = count
        return distribution
    
    def to_dict(self):
        """Converts the Rating object to a dictionary."""
        user_data = None
        if self.user is not None:
            try:
                user_data = {
                    "id": self.user.id,
                    "username": self.user.username,
                    "first_name": getattr(self.user, "first_name", None),
                    "last_name": getattr(self.user, "last_name", None),
                    "profile_picture": getattr(self.user, "profile_picture", None),
                    "role": getattr(self.user.role, "value", None),
                }
            except Exception:
                user_data = {"id": self.user_id}

        return {
            "id": self.id,
            "rating_value": self.rating_value,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "user_id": self.user_id,
            "user": user_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<Rating {self.rating_value} stars by User {self.user_id} on {self.content_type} {self.content_id}>"


class CommentLike(db.Model):
    """Model for comment likes and dislikes."""
    __tablename__ = "comment_like"
    
    id = db.Column(db.Integer, primary_key=True)
    is_like = db.Column(db.Boolean, nullable=False)  # True for like, False for dislike
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_comment_like_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    comment_id = db.Column(
        db.Integer,
        db.ForeignKey("comment.id", name="fk_comment_like_comment_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    user = db.relationship("User", back_populates="comment_likes")
    comment = db.relationship("Comment", back_populates="likes")
    
    # Unique constraint to prevent duplicate likes/dislikes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_like'),
    )
    
    def __init__(self, **kwargs):
        super(CommentLike, self).__init__(**kwargs)
    
    def validate(self):
        """Validate the comment like before saving."""
        if self.is_like not in [True, False]:
            raise ValueError("is_like must be True or False")
    
    def to_dict(self):
        """Converts the CommentLike object to a dictionary."""
        return {
            "id": self.id,
            "is_like": self.is_like,
            "is_deleted": self.is_deleted,
            "user_id": self.user_id,
            "comment_id": self.comment_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        like_type = "like" if self.is_like else "dislike"
        return f"<CommentLike {like_type} by User {self.user_id} on Comment {self.comment_id}>"


class CommentReport(db.Model):
    """Model for comment reports (spam, inappropriate content, etc.)."""
    __tablename__ = "comment_report"
    
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(100), nullable=False)  # 'spam', 'inappropriate', 'harassment', etc.
    description = db.Column(db.Text, nullable=True)  # Additional details
    is_resolved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_comment_report_resolved_by"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_comment_report_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    comment_id = db.Column(
        db.Integer,
        db.ForeignKey("comment.id", name="fk_comment_report_comment_id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Relationships
    user = db.relationship("User", foreign_keys=[user_id], back_populates="comment_reports")
    comment = db.relationship("Comment", back_populates="reports")
    resolver = db.relationship("User", foreign_keys=[resolved_by], back_populates="resolved_reports")
    
    def __init__(self, **kwargs):
        super(CommentReport, self).__init__(**kwargs)
    
    def validate(self):
        """Validate the comment report before saving."""
        valid_reasons = ['spam', 'inappropriate', 'harassment', 'offensive', 'other']
        if self.reason not in valid_reasons:
            raise ValueError(f"Reason must be one of: {', '.join(valid_reasons)}")
    
    def resolve(self, resolved_by_user_id):
        """Mark the report as resolved."""
        self.is_resolved = True
        self.resolved_by = resolved_by_user_id
        self.resolved_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Converts the CommentReport object to a dictionary."""
        return {
            "id": self.id,
            "reason": self.reason,
            "description": self.description,
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "user_id": self.user_id,
            "comment_id": self.comment_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<CommentReport {self.reason} by User {self.user_id} on Comment {self.comment_id}>"


class NavigationLink(db.Model):
    __tablename__ = "navigation_link"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Display name
    url = db.Column(db.String(255), nullable=False)   # URL path
    location = db.Column(db.String(50), nullable=False)  # 'navbar' or 'footer'
    order = db.Column(db.Integer, nullable=False, default=0)  # Display order
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_external = db.Column(db.Boolean, default=False, nullable=False)  # External link
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=default_utcnow,
        onupdate=default_utcnow,
        nullable=False,
    )

    # Foreign key to user who created/updated
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_navigation_link_user_id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self):
        return f"<NavigationLink {self.name} ({self.location})>"

    def to_dict(self):
        """Converts the NavigationLink object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "location": self.location,
            "order": self.order,
            "is_active": self.is_active,
            "is_external": self.is_external,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "user_id": self.user_id,
        }


class RootSEO(db.Model):
    """Model for managing SEO settings for root website pages."""
    __tablename__ = "root_seo"

    id = db.Column(db.Integer, primary_key=True)
    page_identifier = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., 'home', 'about', 'news'
    page_name = db.Column(db.String(100), nullable=False)  # Display name for the page
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    # Basic SEO Fields
    meta_title = db.Column(db.String(200), nullable=True)  # Page title for search engines
    meta_description = db.Column(db.String(500), nullable=True)  # Meta description for search engines
    meta_keywords = db.Column(db.String(500), nullable=True)    # Meta keywords for search engines
    
    # Open Graph Fields
    og_title = db.Column(db.String(200), nullable=True)         # Open Graph title for social media
    og_description = db.Column(db.String(500), nullable=True)   # Open Graph description for social media
    og_image = db.Column(db.String(255), nullable=True)         # Open Graph image URL for social media
    og_type = db.Column(db.String(50), nullable=True, default='website')  # Open Graph type
    
    # Twitter Card Fields
    twitter_card = db.Column(db.String(50), nullable=True, default='summary_large_image')  # Type of Twitter card
    twitter_title = db.Column(db.String(200), nullable=True)   # Twitter-specific title
    twitter_description = db.Column(db.String(500), nullable=True)  # Twitter-specific description
    twitter_image = db.Column(db.String(255), nullable=True)   # Twitter-specific image URL
    
    # Advanced SEO Fields
    canonical_url = db.Column(db.String(255), nullable=True)    # Canonical URL to prevent duplicate content
    meta_author = db.Column(db.String(100), nullable=True)     # Page author for meta tags
    meta_language = db.Column(db.String(10), nullable=True, default='id')    # Content language (en, id, etc.)
    meta_robots = db.Column(db.String(50), nullable=True, default='index, follow')      # Robots meta tag
    structured_data_type = db.Column(db.String(50), nullable=True)  # Type of structured data (WebSite, Organization, etc.)
    schema_markup = db.Column(db.Text, nullable=True)          # JSON-LD structured data
    
    # Analytics and Tracking
    google_analytics_id = db.Column(db.String(50), nullable=True)  # Google Analytics ID for this page
    facebook_pixel_id = db.Column(db.String(50), nullable=True)    # Facebook Pixel ID for this page
    
    # Timestamps and User Tracking
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_root_seo")
    updater = db.relationship("User", foreign_keys=[updated_by], backref="updated_root_seo")
    
    def __init__(self, **kwargs):
        super(RootSEO, self).__init__(**kwargs)
    
    def validate(self):
        """Validate the root SEO object before saving to the database."""
        if not self.page_identifier or len(self.page_identifier.strip()) == 0:
            raise ValueError("Page identifier is required")
        if len(self.page_identifier) > 50:
            raise ValueError("Page identifier must be less than 50 characters")
        if not self.page_name or len(self.page_name.strip()) == 0:
            raise ValueError("Page name is required")
        if len(self.page_name) > 100:
            raise ValueError("Page name must be less than 100 characters")
        
        # SEO validation
        if self.meta_title and len(self.meta_title) > 200:
            raise ValueError("Meta title must be less than 200 characters")
        if self.meta_description and len(self.meta_description) > 500:
            raise ValueError("Meta description must be less than 500 characters")
        if self.meta_keywords and len(self.meta_keywords) > 500:
            raise ValueError("Meta keywords must be less than 500 characters")
        if self.og_title and len(self.og_title) > 200:
            raise ValueError("Open Graph title must be less than 200 characters")
        if self.og_description and len(self.og_description) > 500:
            raise ValueError("Open Graph description must be less than 500 characters")
        if self.canonical_url and len(self.canonical_url) > 255:
            raise ValueError("Canonical URL must be less than 255 characters")
    
    def calculate_seo_score(self):
        """Calculate SEO score based on completeness of SEO fields."""
        score = 0
        total_fields = 8  # Number of important SEO fields
        
        if self.meta_title:
            score += 1
        if self.meta_description:
            score += 1
        if self.meta_keywords:
            score += 1
        if self.og_title:
            score += 1
        if self.og_description:
            score += 1
        if self.og_image:
            score += 1
        if self.canonical_url:
            score += 1
        if self.schema_markup:
            score += 1
        
        return int((score / total_fields) * 100)
    
    def generate_schema_markup(self):
        """Generate JSON-LD structured data for the page."""
        if not self.schema_markup:
            schema = {
                "@context": "https://schema.org",
                "@type": self.structured_data_type or "WebPage",
                "name": self.page_name,
                "description": self.meta_description,
                "url": self.canonical_url or f"https://{request.host}{request.path}",
                "inLanguage": self.meta_language or "id"
            }
            
            if self.meta_author:
                schema["author"] = {
                    "@type": "Person",
                    "name": self.meta_author
                }
            
            self.schema_markup = json.dumps(schema, ensure_ascii=False)
        
        return self.schema_markup
    
    def update_seo_fields(self):
        """Update SEO-related fields and calculate score."""
        self.seo_score = self.calculate_seo_score()
        self.last_seo_audit = datetime.utcnow()
        
        # Generate schema markup if not present
        if not self.schema_markup:
            self.generate_schema_markup()
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "page_identifier": self.page_identifier,
            "page_name": self.page_name,
            "is_active": self.is_active,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "og_title": self.og_title,
            "og_description": self.og_description,
            "og_image": self.og_image,
            "og_type": self.og_type,
            "twitter_card": self.twitter_card,
            "twitter_title": self.twitter_title,
            "twitter_description": self.twitter_description,
            "twitter_image": self.twitter_image,
            "canonical_url": self.canonical_url,
            "meta_author": self.meta_author,
            "meta_language": self.meta_language,
            "meta_robots": self.meta_robots,
            "structured_data_type": self.structured_data_type,
            "schema_markup": self.schema_markup,
            "google_analytics_id": self.google_analytics_id,
            "facebook_pixel_id": self.facebook_pixel_id,
            "seo_score": self.calculate_seo_score(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }
    
    def __repr__(self):
        return f"<RootSEO {self.page_identifier}: {self.page_name}>"

# Event listeners
@event.listens_for(Image, "after_delete")
def delete_image_file(mapper, connection, target):
    """Deletes the file from filesystem after the Image record is deleted."""
    target.delete_file()


# Indexes (can be used with Flask-Migrate)
# Note: Defining indexes here is informational.
# Actual creation/management is handled by safe_migrate.py
def create_indexes():
    """Creates database indexes for better query performance. (Run via migrations)"""
    # Example index commands (adjust dialect if not PostgreSQL/SQLite)
    # Use IF NOT EXISTS for safety
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_news_category_date ON news (category_id, date DESC);"
        )
    )
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_news_is_news_date ON news (is_news, date DESC);"
        )
    )
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_news_is_premium_date ON news (is_premium, date DESC);"
        )
    )
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_news_visible_date ON news (is_visible, date DESC);"
        )
    )
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_news_main_date ON news (is_main_news, date DESC);"
        )
    )
    # user.username is already indexed by unique=True, but explicit index can be added if needed
    # db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_user_username ON \"user\" (username);")) # Use quotes for reserved words like user
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_youtube_video_created_at ON youtube_video (created_at DESC);"
        )
    )
    # Add index for youtube_id if frequently queried directly
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS idx_youtube_video_youtube_id ON youtube_video (youtube_id);"
        )
    )
    # Add index for share_log news_id (already unique, but index helps lookups)
    db.session.execute(
        text("CREATE INDEX IF NOT EXISTS idx_share_log_news_id ON share_log (news_id);")
    )
    try:
        db.session.commit()
        print("Indexes checked/created (if supported by DB and migrations).")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error creating indexes: {e}")

# =============================================================================
# ADS SYSTEM MODELS
# =============================================================================

class AdCampaign(db.Model):
    """Model for organizing ads into campaigns."""
    __tablename__ = "ad_campaign"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    budget = db.Column(db.Numeric(10, 2), nullable=True)  # Campaign budget
    currency = db.Column(db.String(3), default='IDR')
    target_audience = db.Column(db.JSON, nullable=True)  # Audience targeting criteria
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_ad_campaigns")
    updater = db.relationship("User", foreign_keys=[updated_by], backref="updated_ad_campaigns")
    ads = db.relationship("Ad", back_populates="campaign", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate campaign data."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
    
    def is_active_now(self):
        """Check if campaign is currently active."""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "is_active_now": self.is_active_now(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "budget": float(self.budget) if self.budget else None,
            "currency": self.currency,
            "target_audience": self.target_audience,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "ads_count": len(self.ads) if self.ads else 0
        }
    
    def __repr__(self):
        return f"<AdCampaign {self.name}>"

    @property
    def ads_count(self) -> int:
        """Number of ads in this campaign (for Jinja templates)."""
        try:
            return len(self.ads) if self.ads is not None else 0
        except Exception:
            return 0


class Ad(db.Model):
    """Model for individual ads (both internal and external)."""
    __tablename__ = "ad"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ad_type = db.Column(db.String(50), nullable=False, index=True)  # 'internal', 'external'
    content_type = db.Column(db.String(50), nullable=False)  # 'image', 'text', 'html', 'google_ads'
    
    # Content fields
    image_url = db.Column(db.String(500), nullable=True)  # For image ads
    image_alt = db.Column(db.String(200), nullable=True)
    text_content = db.Column(db.Text, nullable=True)  # For text ads
    html_content = db.Column(db.Text, nullable=True)  # For HTML ads
    target_url = db.Column(db.String(500), nullable=True)  # Click destination
    
    # External ads (Google Ads, etc.)
    external_ad_code = db.Column(db.Text, nullable=True)  # Google Ads code
    external_ad_client = db.Column(db.String(100), nullable=True)  # e.g., 'ca-pub-123456789'
    external_ad_slot = db.Column(db.String(100), nullable=True)  # e.g., '1234567890'
    
    # Display settings
    width = db.Column(db.Integer, nullable=True)  # Ad width in pixels
    height = db.Column(db.Integer, nullable=True)  # Ad height in pixels
    css_classes = db.Column(db.String(500), nullable=True)  # Custom CSS classes
    inline_styles = db.Column(db.Text, nullable=True)  # Custom inline styles
    
    # Status and scheduling
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.Integer, default=0, nullable=False)  # Higher number = higher priority
    
    # Performance tracking
    impressions = db.Column(db.Integer, default=0, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)
    ctr = db.Column(db.Float, default=0.0, nullable=False)  # Click-through rate
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    campaign_id = db.Column(db.Integer, db.ForeignKey("ad_campaign.id", ondelete="SET NULL"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    campaign = db.relationship("AdCampaign", back_populates="ads")
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_ads")
    updater = db.relationship("User", foreign_keys=[updated_by], backref="updated_ads")
    placements = db.relationship("AdPlacement", back_populates="ad", cascade="all, delete-orphan")
    stats = db.relationship("AdStats", back_populates="ad", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate ad data."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date cannot be after end date")
        
        if self.ad_type not in ['internal', 'external']:
            raise ValueError("Ad type must be 'internal' or 'external'")
        
        if self.content_type not in ['image', 'text', 'html', 'google_ads']:
            raise ValueError("Content type must be 'image', 'text', 'html', or 'google_ads'")
    
    def is_active_now(self):
        """Check if ad is currently active."""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True
    
    def record_impression(self):
        """Record an ad impression."""
        self.impressions += 1
        self.update_ctr()
    
    def record_click(self):
        """Record an ad click."""
        self.clicks += 1
        self.update_ctr()
    
    def update_ctr(self):
        """Update click-through rate."""
        if self.impressions > 0:
            self.ctr = (self.clicks / self.impressions) * 100
        else:
            self.ctr = 0.0
    
    def get_rendered_html(self, page_context=None):
        """Get the rendered HTML for this ad based on its type and content."""
        if self.ad_type == 'external' and self.content_type == 'google_ads':
            return self.get_google_ads_html()
        elif self.ad_type == 'internal':
            return self.get_internal_ad_html(page_context)
        else:
            return self.get_fallback_html()
    
    def get_google_ads_html(self):
        """Generate Google Ads HTML."""
        if not self.external_ad_code:
            return self.get_fallback_html()
        
        return f"""
        <div class="ad-container google-ads-container" data-ad-id="{self.id}">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
            {self.external_ad_code}
        </div>
        """
    
    def get_internal_ad_html(self, page_context=None):
        """Generate internal ad HTML with page context styling."""
        css_classes = self.css_classes or "ad-container internal-ad"
        inline_styles = self.inline_styles or ""
        
        if page_context and page_context.get('card_style'):
            # Adapt to page card styling
            card_style = page_context['card_style']
            css_classes += f" {card_style}"
        
        content = ""
        if self.content_type == 'image':
            content = f"""
            <div class="ad-image-container">
                <img src="{self.image_url}" alt="{self.image_alt or self.title}" 
                     class="ad-image" style="max-width: 100%; height: auto;">
            </div>
            """
        elif self.content_type == 'text':
            content = f"""
            <div class="ad-text-content">
                <h3 class="ad-title">{self.title}</h3>
                <p class="ad-description">{self.text_content}</p>
            </div>
            """
        elif self.content_type == 'html':
            # Sanitize internal HTML creatives to mitigate XSS risks
            sanitized = self.html_content or ""
            try:
                import bleach
                allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union({
                    'img','video','iframe','div','span','p','a','h1','h2','h3','h4','h5','h6','ul','ol','li','strong','em','br'
                })
                allowed_attrs = {
                    '*': ['class', 'style'],
                    'a': ['href', 'target', 'rel'],
                    'img': ['src', 'alt', 'width', 'height'],
                    'iframe': ['src', 'width', 'height', 'allow', 'allowfullscreen', 'frameborder', 'referrerpolicy']
                }
                sanitized = bleach.clean(sanitized, tags=list(allowed_tags), attributes=allowed_attrs, strip=True)
            except Exception:
                # If sanitization fails for any reason, fallback to raw but contained content
                pass
            content = sanitized
        
        return f"""
        <div class="{css_classes}" data-ad-id="{self.id}" style="{inline_styles}">
            <div class="ad-content">
                {content}
                <div class="ad-label">Advertisement</div>
            </div>
        </div>
        """
    
    def get_fallback_html(self):
        """Generate fallback HTML for ads that can't be rendered."""
        return f"""
        <div class="ad-container ad-fallback" data-ad-id="{self.id}">
            <div class="ad-placeholder">
                <p class="text-gray-400">Advertisement</p>
            </div>
        </div>
        """
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ad_type": self.ad_type,
            "content_type": self.content_type,
            "image_url": self.image_url,
            "image_alt": self.image_alt,
            "text_content": self.text_content,
            "html_content": self.html_content,
            "target_url": self.target_url,
            "external_ad_code": self.external_ad_code,
            "external_ad_client": self.external_ad_client,
            "external_ad_slot": self.external_ad_slot,
            "width": self.width,
            "height": self.height,
            "css_classes": self.css_classes,
            "inline_styles": self.inline_styles,
            "is_active": self.is_active,
            "is_active_now": self.is_active_now(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "priority": self.priority,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ctr": self.ctr,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "campaign_id": self.campaign_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }
    
    def __repr__(self):
        return f"<Ad {self.title} ({self.ad_type})>"


class AdPlacement(db.Model):
    """Model for defining where ads should appear on the site."""
    __tablename__ = "ad_placement"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Placement targeting
    page_type = db.Column(db.String(100), nullable=False, index=True)  # 'home', 'news', 'album', 'category', etc.
    page_specific = db.Column(db.String(200), nullable=True)  # Specific page identifier
    section = db.Column(db.String(100), nullable=False)  # 'header', 'sidebar', 'content', 'footer', etc.
    position = db.Column(db.String(100), nullable=False)  # 'top', 'middle', 'bottom', 'after_n_items'
    position_value = db.Column(db.Integer, nullable=True)  # For 'after_n_items', the number
    
    # Display settings
    max_ads_per_page = db.Column(db.Integer, default=1, nullable=False)
    rotation_type = db.Column(db.String(50), default='random', nullable=False)  # 'random', 'sequential', 'weighted'
    display_frequency = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0 (percentage of page loads)
    
    # Targeting criteria
    user_type = db.Column(db.String(50), nullable=True)  # 'all', 'premium', 'non_premium', 'guest'
    device_type = db.Column(db.String(50), nullable=True)  # 'all', 'desktop', 'mobile', 'tablet'
    location_targeting = db.Column(db.JSON, nullable=True)  # Geographic targeting
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id", ondelete="CASCADE"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    ad = db.relationship("Ad", back_populates="placements")
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_ad_placements")
    updater = db.relationship("User", foreign_keys=[updated_by], backref="updated_ad_placements")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate placement data."""
        if self.display_frequency < 0.0 or self.display_frequency > 1.0:
            raise ValueError("Display frequency must be between 0.0 and 1.0")
        
        if self.rotation_type not in ['random', 'sequential', 'weighted']:
            raise ValueError("Rotation type must be 'random', 'sequential', or 'weighted'")
    
    def should_display(self, user=None, device_type=None, location=None):
        """Check if this placement should display based on targeting criteria."""
        if not self.is_active:
            return False
        
        # Check display frequency
        if random.random() > self.display_frequency:
            return False
        
        # Check user type targeting
        if self.user_type and user:
            if self.user_type == 'premium' and not user.has_active_premium_subscription():
                return False
            elif self.user_type == 'non_premium' and user.has_active_premium_subscription():
                return False
        
        # Check device type targeting
        if self.device_type and device_type:
            if self.device_type != 'all' and self.device_type != device_type:
                return False
        
        # Check location targeting
        if self.location_targeting and location:
            # Implement location-based targeting logic here
            pass
        
        return True
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "page_type": self.page_type,
            "page_specific": self.page_specific,
            "section": self.section,
            "position": self.position,
            "position_value": self.position_value,
            "max_ads_per_page": self.max_ads_per_page,
            "rotation_type": self.rotation_type,
            "display_frequency": self.display_frequency,
            "user_type": self.user_type,
            "device_type": self.device_type,
            "location_targeting": self.location_targeting,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ad_id": self.ad_id,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }
    
    def __repr__(self):
        return f"<AdPlacement {self.name} ({self.page_type}/{self.section})>"


class AdStats(db.Model):
    """Model for tracking detailed ad performance statistics."""
    __tablename__ = "ad_stats"
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    hour = db.Column(db.Integer, nullable=True)  # 0-23 for hourly stats
    
    # Performance metrics
    impressions = db.Column(db.Integer, default=0, nullable=False)
    clicks = db.Column(db.Integer, default=0, nullable=False)
    viewable_impressions = db.Column(db.Integer, default=0, nullable=False)
    revenue = db.Column(db.Numeric(10, 4), default=0, nullable=False)  # Revenue in currency
    
    # User metrics
    unique_users = db.Column(db.Integer, default=0, nullable=False)
    returning_users = db.Column(db.Integer, default=0, nullable=False)
    
    # Device metrics
    desktop_impressions = db.Column(db.Integer, default=0, nullable=False)
    mobile_impressions = db.Column(db.Integer, default=0, nullable=False)
    tablet_impressions = db.Column(db.Integer, default=0, nullable=False)
    
    # Geographic metrics (if available)
    country_impressions = db.Column(db.JSON, nullable=True)  # {country_code: count}
    city_impressions = db.Column(db.JSON, nullable=True)  # {city: count}
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    ad = db.relationship("Ad", back_populates="stats")
    
    # Unique constraint to prevent duplicate stats for same ad/date/hour
    __table_args__ = (
        db.UniqueConstraint('ad_id', 'date', 'hour', name='uq_ad_stats_ad_date_hour'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate stats data."""
        if self.hour is not None and (self.hour < 0 or self.hour > 23):
            raise ValueError("Hour must be between 0 and 23")
    
    @property
    def ctr(self):
        """Calculate click-through rate."""
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0.0
    
    @property
    def cpm(self):
        """Calculate cost per mille (cost per 1000 impressions)."""
        if self.impressions > 0:
            return (float(self.revenue) / self.impressions) * 1000
        return 0.0
    
    @property
    def cpc(self):
        """Calculate cost per click."""
        if self.clicks > 0:
            return float(self.revenue) / self.clicks
        return 0.0
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "hour": self.hour,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "revenue": float(self.revenue) if self.revenue else 0.0,
            "unique_users": self.unique_users,
            "returning_users": self.returning_users,
            "desktop_impressions": self.desktop_impressions,
            "mobile_impressions": self.mobile_impressions,
            "tablet_impressions": self.tablet_impressions,
            "country_impressions": self.country_impressions,
            "city_impressions": self.city_impressions,
            "ctr": self.ctr,
            "cpm": self.cpm,
            "cpc": self.cpc,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ad_id": self.ad_id
        }
    
    def __repr__(self):
        return f"<AdStats {self.ad_id} {self.date} {self.hour}>"

# Add missing indexes and optimizations at the end of the file

# =============================================================================
# DATABASE OPTIMIZATIONS AND INDEXES
# =============================================================================

# Add missing indexes for better query performance
def add_missing_indexes():
    """Add missing indexes for optimal database performance."""
    try:
        # News table optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_category_date_visible 
            ON news (category_id, date DESC, is_visible) 
            WHERE is_visible = 1
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_author_date 
            ON news (user_id, date DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_news_premium_visible 
            ON news (is_premium, is_visible, date DESC)
        """))
        
        # Album table optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_album_author_visible 
            ON album (user_id, is_visible, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_album_category_visible 
            ON album (category_id, is_visible, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_album_premium_visible 
            ON album (is_premium, is_visible, created_at DESC)
        """))
        
        # Album chapter optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_album_chapter_album_number 
            ON album_chapter (album_id, chapter_number)
        """))
        
        # User optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_role_active 
            ON "user" (role, is_active) 
            WHERE is_active = 1
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_premium_expires 
            ON "user" (has_premium_access, premium_expires_at)
        """))
        
        # Comment optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_comment_content_approved 
            ON comment (content_type, content_id, is_approved, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_comment_user_created 
            ON comment (user_id, created_at DESC)
        """))
        
        # Rating optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_rating_content_created 
            ON rating (content_type, content_id, created_at DESC)
        """))
        
        # Reading history optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reading_history_user_content 
            ON reading_history (user_id, content_type, content_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_reading_history_last_read 
            ON reading_history (user_id, last_read_at DESC)
        """))
        
        # User library optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_library_user_content 
            ON user_library (user_id, content_type, content_id)
        """))
        
        # Ad optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ad_active_priority 
            ON ad (is_active, priority DESC, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ad_campaign_active 
            ON ad (campaign_id, is_active)
        """))
        
        # Ad placement optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ad_placement_page_section 
            ON ad_placement (page_type, section, is_active)
        """))
        
        # Ad stats optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ad_stats_ad_date 
            ON ad_stats (ad_id, date DESC)
        """))
        
        # Brand identity optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_brand_identity_updated 
            ON brand_identity (updated_at DESC)
        """))
        
        # Root SEO optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_root_seo_identifier_active 
            ON root_seo (page_identifier, is_active)
        """))
        
        # Navigation link optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_navigation_link_location_order 
            ON navigation_link (location, "order", is_active)
        """))
        
        # YouTube video optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_youtube_video_visible_created 
            ON youtube_video (is_visible, created_at DESC)
        """))
        
        # Social media optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_social_media_updated 
            ON social_media (updated_at DESC)
        """))
        
        # Contact detail optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contact_detail_order_active 
            ON contact_detail (section_order, is_active)
        """))
        
        # Team member optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_team_member_group_order 
            ON team_member ("group", member_order, is_active)
        """))
        
        # Policy/guideline optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_policy_order_active 
            ON privacy_policy (section_order, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_guideline_order_active 
            ON media_guideline (section_order, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_visimisi_order_active 
            ON visi_misi (section_order, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_penyangkalan_order_active 
            ON penyangkalan (section_order, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pedomanhak_order_active 
            ON pedoman_hak (section_order, is_active)
        """))
        
        # Image optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_image_visible_created 
            ON image (is_visible, created_at DESC)
        """))
        
        # Category optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_category_name 
            ON category (name)
        """))
        
        # User subscription optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_subscription_user_status 
            ON user_subscriptions (user_id, status)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_subscription_end_date 
            ON user_subscriptions (end_date, status)
        """))
        
        # Comment like optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_comment_like_comment_user 
            ON comment_like (comment_id, user_id, is_like)
        """))
        
        # Comment report optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_comment_report_resolved 
            ON comment_report (is_resolved, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_comment_report_comment 
            ON comment_report (comment_id, is_resolved)
        """))
        
        # User activity optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_activity_user_type 
            ON user_activity (user_id, activity_type, created_at DESC)
        """))
        
        # Permission optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_permission_resource_action 
            ON permission (resource, action)
        """))
        
        # Custom role optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_custom_role_active 
            ON custom_role (is_active, created_at DESC)
        """))
        
        db.session.commit()
        print("✅ All database indexes created successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating indexes: {e}")


# =============================================================================
# DATABASE HEALTH CHECK AND OPTIMIZATION FUNCTIONS
# =============================================================================

def check_database_health():
    """Check database health and provide optimization recommendations."""
    try:
        # Check table sizes
        tables = [
            'news', 'album', 'user', 'comment', 'rating', 'image', 
            'reading_history', 'user_library', 'ad', 'ad_stats'
        ]
        
        print("🔍 Database Health Check")
        print("=" * 50)
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"📊 {table}: {count:,} records")
            except Exception as e:
                print(f"❌ Error checking {table}: {e}")
        
        # Check for orphaned records
        print("\n🔍 Checking for orphaned records...")
        
        # Check orphaned comments
        orphaned_comments = db.session.execute(text("""
            SELECT COUNT(*) FROM comment c 
            LEFT JOIN news n ON c.content_type = 'news' AND c.content_id = n.id
            LEFT JOIN album a ON c.content_type = 'album' AND c.content_id = a.id
            WHERE n.id IS NULL AND a.id IS NULL
        """)).scalar()
        
        if orphaned_comments > 0:
            print(f"⚠️ Found {orphaned_comments} orphaned comments")
        
        # Check orphaned ratings
        orphaned_ratings = db.session.execute(text("""
            SELECT COUNT(*) FROM rating r 
            LEFT JOIN news n ON r.content_type = 'news' AND r.content_id = n.id
            LEFT JOIN album a ON r.content_type = 'album' AND r.content_id = a.id
            WHERE n.id IS NULL AND a.id IS NULL
        """)).scalar()
        
        if orphaned_ratings > 0:
            print(f"⚠️ Found {orphaned_ratings} orphaned ratings")
        
        # Check for duplicate entries
        print("\n🔍 Checking for potential duplicates...")
        
        # Check duplicate usernames (should be prevented by unique constraint)
        duplicate_usernames = db.session.execute(text("""
            SELECT username, COUNT(*) FROM "user" 
            GROUP BY username HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_usernames:
            print(f"⚠️ Found {len(duplicate_usernames)} duplicate usernames")
        
        # Check for expired premium subscriptions
        expired_subscriptions = db.session.execute(text("""
            SELECT COUNT(*) FROM "user" 
            WHERE has_premium_access = 1 
            AND premium_expires_at IS NOT NULL 
            AND premium_expires_at < datetime('now')
        """)).scalar()
        
        if expired_subscriptions > 0:
            print(f"⚠️ Found {expired_subscriptions} expired premium subscriptions")
        
        print("\n✅ Database health check completed!")
        
    except Exception as e:
        print(f"❌ Error during health check: {e}")


def optimize_database():
    """Perform database optimization tasks."""
    try:
        print("🔧 Database Optimization")
        print("=" * 50)
        
        # Analyze tables for better query planning
        db.session.execute(text("ANALYZE"))
        print("✅ Table analysis completed")
        
        # Vacuum database to reclaim space
        db.session.execute(text("VACUUM"))
        print("✅ Database vacuum completed")
        
        # Reindex for better performance
        db.session.execute(text("REINDEX"))
        print("✅ Database reindex completed")
        
        db.session.commit()
        print("✅ Database optimization completed!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error during optimization: {e}")


def cleanup_orphaned_data():
    """Clean up orphaned data to maintain database integrity."""
    try:
        print("🧹 Cleaning up orphaned data...")
        
        # Clean up orphaned comments
        orphaned_comments = db.session.execute(text("""
            DELETE FROM comment 
            WHERE content_type = 'news' 
            AND content_id NOT IN (SELECT id FROM news)
        """))
        
        orphaned_comments_album = db.session.execute(text("""
            DELETE FROM comment 
            WHERE content_type = 'album' 
            AND content_id NOT IN (SELECT id FROM album)
        """))
        
        # Clean up orphaned ratings
        orphaned_ratings = db.session.execute(text("""
            DELETE FROM rating 
            WHERE content_type = 'news' 
            AND content_id NOT IN (SELECT id FROM news)
        """))
        
        orphaned_ratings_album = db.session.execute(text("""
            DELETE FROM rating 
            WHERE content_type = 'album' 
            AND content_id NOT IN (SELECT id FROM album)
        """))
        
        # Clean up orphaned reading history
        orphaned_reading = db.session.execute(text("""
            DELETE FROM reading_history 
            WHERE content_type = 'news' 
            AND content_id NOT IN (SELECT id FROM news)
        """))
        
        orphaned_reading_album = db.session.execute(text("""
            DELETE FROM reading_history 
            WHERE content_type = 'album' 
            AND content_id NOT IN (SELECT id FROM album)
        """))
        
        # Clean up orphaned user library
        orphaned_library = db.session.execute(text("""
            DELETE FROM user_library 
            WHERE content_type = 'news' 
            AND content_id NOT IN (SELECT id FROM news)
        """))
        
        orphaned_library_album = db.session.execute(text("""
            DELETE FROM user_library 
            WHERE content_type = 'album' 
            AND content_id NOT IN (SELECT id FROM album)
        """))
        
        # Clean up expired premium subscriptions
        expired_subscriptions = db.session.execute(text("""
            UPDATE "user" 
            SET has_premium_access = 0, premium_expires_at = NULL
            WHERE has_premium_access = 1 
            AND premium_expires_at IS NOT NULL 
            AND premium_expires_at < datetime('now')
        """))
        
        db.session.commit()
        print("✅ Orphaned data cleanup completed!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error during cleanup: {e}")


# =============================================================================
# DATABASE MIGRATION HELPERS
# =============================================================================

def get_all_models():
    """Get all model classes for migration purposes."""
    return [
        Permission, CustomRole, UserActivity, User, ReadingHistory, UserLibrary,
        PrivacyPolicy, MediaGuideline, VisiMisi, Penyangkalan, PedomanHak,
        Image, Category, News, Album, AlbumChapter, YouTubeVideo, ShareLog,
        SocialMedia, ContactDetail, TeamMember, BrandIdentity, UserSubscription,
        Comment, Rating, CommentLike, CommentReport, NavigationLink, RootSEO,
        AdCampaign, Ad, AdPlacement, AdStats
    ]


def create_all_tables():
    """Create all database tables."""
    try:
        print("🔧 Creating all database tables...")
        db.create_all()
        print("✅ All tables created successfully!")
        
        # Add indexes after table creation
        add_missing_indexes()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")


def drop_all_tables():
    """Drop all database tables (USE WITH CAUTION!)."""
    try:
        print("⚠️ Dropping all database tables...")
        db.drop_all()
        print("✅ All tables dropped successfully!")
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")


# =============================================================================
# DATABASE PERFORMANCE MONITORING
# =============================================================================

def get_database_stats():
    """Get database statistics for monitoring."""
    try:
        stats = {}
        
        # Get table sizes
        tables = [
            'news', 'album', 'user', 'comment', 'rating', 'image', 
            'reading_history', 'user_library', 'ad', 'ad_stats'
        ]
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                stats[f"{table}_count"] = result.scalar()
            except Exception:
                stats[f"{table}_count"] = 0
        
        # Get database size
        try:
            result = db.session.execute(text("""
                SELECT page_count * page_size as size_bytes 
                FROM pragma_page_count(), pragma_page_size()
            """))
            stats['database_size_bytes'] = result.scalar()
        except Exception:
            stats['database_size_bytes'] = 0
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return {}


# =============================================================================
# INITIALIZATION
# =============================================================================

if __name__ == "__main__":
    # This allows running models.py directly for database operations
    print("🚀 LilyOpenCMS Database Models")
    print("=" * 50)
    print("Available functions:")
    print("- create_all_tables()")
    print("- add_missing_indexes()")
    print("- check_database_health()")
    print("- optimize_database()")
    print("- cleanup_orphaned_data()")
    print("- get_database_stats()")
    print("=" * 50)
