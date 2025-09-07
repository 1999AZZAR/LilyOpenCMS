from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
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

# Association table for user following relationships
user_follow = db.Table(
    "user_follow",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    db.Column("following_id", db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    db.Column("created_at", db.DateTime, default=default_utcnow, nullable=False),
    db.UniqueConstraint("follower_id", "following_id", name="uq_user_follow_pair")
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
    email_verified_at = db.Column(db.DateTime, nullable=True)
    last_verification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # New fields for enhanced user management
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
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
    
    # Account deletion request fields
    deletion_requested = db.Column(db.Boolean, default=False, nullable=False)
    deletion_requested_at = db.Column(db.DateTime, nullable=True)
    
    # Write access for content creation (nullable, admin always has write access)
    write_access = db.Column(db.Boolean, nullable=True)  # None = not requested, True = granted, False = denied
    
    # Relationships - Use back_populates for bidirectional links
    news = db.relationship(
        "News",
        foreign_keys="News.user_id",  # Explicitly specify the foreign key for author relationship
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
    
    # Achievement system relationships
    achievements = db.relationship("UserAchievement", back_populates="user", lazy=True, cascade="all, delete-orphan")
    streaks = db.relationship("UserStreak", back_populates="user", lazy=True, cascade="all, delete-orphan")
    points = db.relationship("UserPoints", back_populates="user", lazy=True, cascade="all, delete-orphan", uselist=False)
    
    # Coin system relationships
    coins = db.relationship("UserCoins", back_populates="user", lazy=True, cascade="all, delete-orphan", uselist=False)
    coin_transactions = db.relationship("CoinTransaction", back_populates="user", lazy=True, cascade="all, delete-orphan")
    
    # Following system relationships
    following = db.relationship(
        "User",
        secondary="user_follow",
        primaryjoin=(id == user_follow.c.follower_id),
        secondaryjoin=(id == user_follow.c.following_id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic"
    )
    
    # Profile and stats relationships
    profile = db.relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    stats = db.relationship("UserStats", back_populates="user", uselist=False, cascade="all, delete-orphan")

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
    
    def is_admin_tier(self):
        """Check if user has admin tier access (admin, superuser, or owner)."""
        return self.role in [UserRole.ADMIN, UserRole.SUPERUSER] or self.tier >= 100
    
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


class CategoryGroup(db.Model):
    __tablename__ = "category_group"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationship to categories
    categories = db.relationship("Category", back_populates="group", lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "categories": [cat.to_dict() for cat in self.categories if cat.is_active]
        }


class Category(db.Model):
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign key to category group
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("category_group.id", name="fk_category_group_id"),
        nullable=True,
    )
    
    # Relationships
    group = db.relationship("CategoryGroup", back_populates="categories")
    news = db.relationship("News", back_populates="category", lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
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
    # Prize in coins for premium content (0 = free, >0 = paid)
    prize = db.Column(db.Integer, default=0, nullable=False, index=True)
    # Coin type for premium content ('achievement', 'topup', 'any')
    prize_coin_type = db.Column(db.String(20), default='any', nullable=False, index=True)
    
    # Content deletion request fields
    deletion_requested = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deletion_requested_at = db.Column(db.DateTime, nullable=True)
    deletion_requested_by = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_news_deletion_requested_by"), nullable=True)

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
    author = db.relationship("User", back_populates="news", foreign_keys=[user_id])
    # Relationship for the user who requested deletion
    deletion_requester = db.relationship("User", foreign_keys=[deletion_requested_by])
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
            "prize": self.prize,
            "prize_coin_type": self.prize_coin_type,
            "category_id": self.category_id,
            "category": self.category.to_dict() if self.category else None,
            "author": self.author.to_dict() if self.author else None,
            "image": self.image.to_dict() if self.image else None,
            "share_data": share_data,
            "seo_score": self.seo_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deletion_requested": self.deletion_requested,
            "deletion_requested_at": self.deletion_requested_at.isoformat() if self.deletion_requested_at else None,
            "deletion_requested_by": self.deletion_requested_by,
        }

    def can_user_access(self, user_id):
        """Check if a user can access this news content."""
        # If not premium content, anyone can access
        if not self.is_premium:
            return True
        
        # If premium content but no prize, premium users can access
        if self.prize == 0:
            user = User.query.get(user_id)
            return user and user.is_premium
        
        # If premium content with prize, check if user can afford it
        return CoinManager.can_afford_content(user_id, self.prize, self.prize_coin_type)
    
    def purchase_access(self, user_id):
        """Purchase access to this premium content."""
        # If not premium content, no purchase needed
        if not self.is_premium:
            return {"success": True, "coins_spent": 0, "message": "Free content"}
        
        # If premium content but no prize, premium users can access
        if self.prize == 0:
            user = User.query.get(user_id)
            if user and user.is_premium:
                return {"success": True, "coins_spent": 0, "message": "Premium user - no coins required"}
            else:
                return {"success": False, "error": "Premium subscription required"}
        
        # If premium content with prize, purchase with coins
        return CoinManager.purchase_content(user_id, self.id, self.prize, self.prize_coin_type)
    
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
    # Author name (can be different from the creator/owner)
    author = db.Column(db.String(100), nullable=True)
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
    
    # Content deletion request fields
    deletion_requested = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deletion_requested_at = db.Column(db.DateTime, nullable=True)
    deletion_requested_by = db.Column(db.Integer, db.ForeignKey("user.id", name="fk_album_deletion_requested_by"), nullable=True)

    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_album_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    # Owner ID (can be different from creator - for admin-created albums)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", name="fk_album_owner_id", ondelete="SET NULL"),
        nullable=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id", name="fk_album_category_id"),
        nullable=False,
    )

    # Relationships
    creator = db.relationship("User", backref="created_albums", foreign_keys=[user_id])  # User who created the album
    owner = db.relationship("User", backref="owned_albums", foreign_keys=[owner_id])    # User who owns the album
    # Relationship for the user who requested deletion
    deletion_requester = db.relationship("User", foreign_keys=[deletion_requested_by])
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
            "author": self.author,
            "category": self.category.to_dict() if self.category else None,
            "creator": self.creator.to_dict() if self.creator else None,
            "owner": self.owner.to_dict() if self.owner else None,
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
    brand_description = db.Column(db.Text, nullable=True, default="LilyOpenCMS is a modern, open-source content management system designed for the digital age. We provide comprehensive tools for managing digital content, from news articles and media files to user interactions and analytics. Our platform empowers content creators and organizations to build engaging digital experiences with ease and efficiency.")  # Brand description
    
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
    
    # SEO Settings
    seo_settings = db.Column(db.JSON, nullable=True)  # Root SEO settings as JSON
    website_url = db.Column(db.String(255), nullable=True, default="https://lilycms.com")  # Website URL for SEO

    def to_dict(self):
        return {
            "brand_name": self.brand_name,
            "tagline": self.tagline,
            "brand_description": self.brand_description,
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
            "seo_settings": self.seo_settings,
            "website_url": self.website_url,
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
    image_url = db.Column(db.String(500), nullable=True)  # For external image URLs
    image_filename = db.Column(db.String(255), nullable=True)  # For uploaded image files
    image_upload_path = db.Column(db.String(500), nullable=True)  # Relative path to uploaded image
    image_alt = db.Column(db.String(200), nullable=True)
    image_width = db.Column(db.Integer, nullable=True)  # Original image width
    image_height = db.Column(db.Integer, nullable=True)  # Original image height
    image_file_size = db.Column(db.Integer, nullable=True)  # File size in bytes
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
        
        # Validate image fields for image content type
        if self.content_type == 'image':
            if not self.image_url and not self.image_filename:
                raise ValueError("Image ads must have either image_url or image_filename")
            
            # Validate image dimensions if provided
            if self.image_width and self.image_width <= 0:
                raise ValueError("Image width must be positive")
            if self.image_height and self.image_height <= 0:
                raise ValueError("Image height must be positive")
            
            # Validate file size if provided
            if self.image_file_size and self.image_file_size <= 0:
                raise ValueError("Image file size must be positive")
    
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
        elif self.ad_type == 'external':
            return self.get_external_ad_html(page_context)
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
            image_url = self.get_image_url()
            if image_url:
                content = f"""
                <div class="ad-image-container">
                    <img src="{image_url}" alt="{self.image_alt or self.title}" 
                         class="ad-image" style="max-width: 100%; height: auto;">
                </div>
                """
            else:
                content = f"""
                <div class="ad-image-container ad-placeholder">
                    <div class="ad-placeholder-content">
                        <p class="text-gray-400">No image available</p>
                    </div>
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
    
    def get_external_ad_html(self, page_context=None):
        """Generate external ad HTML for API consumption."""
        css_classes = self.css_classes or "ad-container external-ad"
        inline_styles = self.inline_styles or ""
        
        content = ""
        if self.content_type == 'image':
            image_url = self.get_image_url()
            if image_url:
                content = f"""
                <div class="ad-image-container">
                    <img src="{image_url}" alt="{self.image_alt or self.title}" 
                         class="ad-image" style="max-width: 100%; height: auto;">
                </div>
                """
            else:
                content = f"""
                <div class="ad-image-container ad-placeholder">
                    <div class="ad-placeholder-content">
                        <p class="text-gray-400">No image available</p>
                    </div>
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
            content = f"""
            <div class="ad-html-content">
                {self.html_content}
            </div>
            """
        
        # Add click tracking for external ads
        click_url = ""
        if self.target_url:
            from itsdangerous import URLSafeSerializer
            from flask import current_app
            s = URLSafeSerializer(current_app.secret_key, salt='ads-click')
            sig = s.dumps({'ad_id': self.id, 'url': self.target_url})
            click_url = f"/ads/click?ad_id={self.id}&url={self.target_url}&sig={sig}"
        
        return f"""
        <div class="{css_classes}" data-ad-id="{self.id}" style="{inline_styles}">
            <div class="ad-content">
                {content}
                <div class="ad-label">Advertisement</div>
            </div>
        </div>
        """
    
    def get_image_url(self):
        """Get the appropriate image URL for the ad."""
        if self.image_upload_path:
            # Return the uploaded image path
            return self.image_upload_path
        elif self.image_url:
            # Return the external image URL
            return self.image_url
        return None
    
    def delete_image_file(self):
        """Delete the uploaded image file if it exists."""
        if self.image_upload_path:
            import os
            from flask import current_app
            
            try:
                # Construct the full file path
                full_path = os.path.join(current_app.static_folder, self.image_upload_path.lstrip('/'))
                if os.path.exists(full_path):
                    os.remove(full_path)
                    # Clear the image fields
                    self.image_filename = None
                    self.image_upload_path = None
                    self.image_width = None
                    self.image_height = None
                    self.image_file_size = None
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error deleting image file: {e}")
    
    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ad_type": self.ad_type,
            "content_type": self.content_type,
            "image_url": self.image_url,
            "image_filename": self.image_filename,
            "image_upload_path": self.image_upload_path,
            "image_alt": self.image_alt,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "image_file_size": self.image_file_size,
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
        
        # Achievement system optimizations
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_achievement_category_active_order 
            ON achievement_category (is_active, display_order)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_achievement_criteria_active 
            ON achievement (criteria_type, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_achievement_category_active 
            ON achievement (category_id, is_active)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_achievement_user_completed 
            ON user_achievement (user_id, is_completed)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_achievement_achievement_completed 
            ON user_achievement (achievement_id, is_completed)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_achievement_progress_user_achievement 
            ON achievement_progress (user_achievement_id, created_at DESC)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_streak_user_type 
            ON user_streak (user_id, streak_type)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_points_user 
            ON user_points (user_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_point_transaction_user_points 
            ON point_transaction (user_points_id, created_at DESC)
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
        AdCampaign, Ad, AdPlacement, AdStats,
        # Achievement system models
        AchievementCategory, Achievement, UserAchievement, AchievementProgress,
        UserStreak, UserPoints, PointTransaction
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

# =============================================================================
# ACHIEVEMENT SYSTEM MODELS
# =============================================================================

class AchievementCategory(db.Model):
    """Model for categorizing achievements."""
    __tablename__ = "achievement_category"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon_class = db.Column(db.String(100), nullable=True)  # CSS icon class
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    achievements = db.relationship("Achievement", back_populates="category", lazy=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon_class": self.icon_class,
            "color": self.color,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<AchievementCategory {self.name}>"


class Achievement(db.Model):
    """Model for defining achievements that users can earn."""
    __tablename__ = "achievement"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    achievement_type = db.Column(db.String(50), nullable=False, index=True)  # 'streak', 'count', 'milestone', 'special'
    
    # Achievement criteria
    criteria_type = db.Column(db.String(50), nullable=False)  # 'login_streak', 'activity_streak', 'reading_streak', 'contribution', 'exploration', etc.
    criteria_value = db.Column(db.Integer, nullable=False)  # Target value to achieve
    criteria_operator = db.Column(db.String(10), default='>=', nullable=False)  # '>=', '=', '>', etc.
    
    # Achievement rewards and display
    points_reward = db.Column(db.Integer, default=0, nullable=False)  # Points awarded
    badge_icon = db.Column(db.String(255), nullable=True)  # Badge image URL
    rarity = db.Column(db.String(20), default='common', nullable=False)  # 'common', 'rare', 'epic', 'legendary'
    is_hidden = db.Column(db.Boolean, default=False, nullable=False)  # Hidden until achieved
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    category_id = db.Column(db.Integer, db.ForeignKey("achievement_category.id", ondelete="SET NULL"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    category = db.relationship("AchievementCategory", back_populates="achievements")
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_achievements")
    user_achievements = db.relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate achievement data."""
        if self.criteria_value < 0:
            raise ValueError("Criteria value cannot be negative")
        
        valid_operators = ['>=', '=', '>', '<', '<=', '!=']
        if self.criteria_operator not in valid_operators:
            raise ValueError(f"Criteria operator must be one of: {', '.join(valid_operators)}")
        
        valid_rarities = ['common', 'rare', 'epic', 'legendary']
        if self.rarity not in valid_rarities:
            raise ValueError(f"Rarity must be one of: {', '.join(valid_rarities)}")
    
    def check_criteria(self, current_value):
        """Check if the current value meets the achievement criteria."""
        if self.criteria_operator == '>=':
            return current_value >= self.criteria_value
        elif self.criteria_operator == '=':
            return current_value == self.criteria_value
        elif self.criteria_operator == '>':
            return current_value > self.criteria_value
        elif self.criteria_operator == '<':
            return current_value < self.criteria_value
        elif self.criteria_operator == '<=':
            return current_value <= self.criteria_value
        elif self.criteria_operator == '!=':
            return current_value != self.criteria_value
        return False
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "achievement_type": self.achievement_type,
            "criteria_type": self.criteria_type,
            "criteria_value": self.criteria_value,
            "criteria_operator": self.criteria_operator,
            "points_reward": self.points_reward,
            "badge_icon": self.badge_icon,
            "rarity": self.rarity,
            "is_hidden": self.is_hidden,
            "is_active": self.is_active,
            "category": self.category.to_dict() if self.category else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Achievement {self.name} ({self.rarity})>"


class UserAchievement(db.Model):
    """Model for tracking user achievements."""
    __tablename__ = "user_achievement"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievement.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Achievement progress and completion
    current_progress = db.Column(db.Integer, default=0, nullable=False)  # Current progress value
    is_completed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)  # When achievement was completed
    points_earned = db.Column(db.Integer, default=0, nullable=False)  # Points actually earned
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="achievements")
    achievement = db.relationship("Achievement", back_populates="user_achievements")
    progress_logs = db.relationship("AchievementProgress", back_populates="user_achievement", cascade="all, delete-orphan")
    
    # Unique constraint to prevent duplicate user achievements
    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def update_progress(self, new_progress, earned_points=0):
        """Update achievement progress and check for completion."""
        self.current_progress = new_progress
        
        # Check if achievement is completed
        if not self.is_completed and self.achievement.check_criteria(new_progress):
            self.is_completed = True
            self.completed_at = datetime.now(timezone.utc)
            self.points_earned = earned_points or self.achievement.points_reward
        
        self.updated_at = datetime.now(timezone.utc)
    
    def get_progress_percentage(self):
        """Get progress as a percentage."""
        if self.achievement.criteria_value == 0:
            return 100 if self.is_completed else 0
        return min(100, (self.current_progress / self.achievement.criteria_value) * 100)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "current_progress": self.current_progress,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "points_earned": self.points_earned,
            "progress_percentage": self.get_progress_percentage(),
            "achievement": self.achievement.to_dict() if self.achievement else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        status = "completed" if self.is_completed else "in_progress"
        return f"<UserAchievement {self.user_id} - {self.achievement_id} ({status})>"


class AchievementProgress(db.Model):
    """Model for tracking detailed achievement progress history."""
    __tablename__ = "achievement_progress"
    
    id = db.Column(db.Integer, primary_key=True)
    user_achievement_id = db.Column(db.Integer, db.ForeignKey("user_achievement.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress details
    progress_type = db.Column(db.String(50), nullable=False)  # 'increment', 'set', 'reset'
    old_value = db.Column(db.Integer, nullable=True)  # Previous progress value
    new_value = db.Column(db.Integer, nullable=False)  # New progress value
    change_amount = db.Column(db.Integer, nullable=True)  # Amount of change
    
    # Context information
    context_data = db.Column(db.JSON, nullable=True)  # Additional context (e.g., content_id, activity_type)
    source = db.Column(db.String(100), nullable=True)  # Source of the progress (e.g., 'login', 'news_creation', 'comment')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    
    # Relationships
    user_achievement = db.relationship("UserAchievement", back_populates="progress_logs")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.old_value is not None and self.new_value is not None:
            self.change_amount = self.new_value - self.old_value
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_achievement_id": self.user_achievement_id,
            "progress_type": self.progress_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_amount": self.change_amount,
            "context_data": self.context_data,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<AchievementProgress {self.progress_type}: {self.old_value} -> {self.new_value}>"


class UserStreak(db.Model):
    """Model for tracking user streaks (login, activity, reading, etc.)."""
    __tablename__ = "user_streak"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    streak_type = db.Column(db.String(50), nullable=False, index=True)  # 'login', 'activity', 'reading', 'contribution'
    
    # Streak tracking
    current_streak = db.Column(db.Integer, default=0, nullable=False)  # Current streak count
    longest_streak = db.Column(db.Integer, default=0, nullable=False)  # Longest streak ever
    last_activity_date = db.Column(db.Date, nullable=True)  # Last activity date
    streak_start_date = db.Column(db.Date, nullable=True)  # When current streak started
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="streaks")
    
    # Unique constraint to prevent duplicate streaks per user and type
    __table_args__ = (
        db.UniqueConstraint('user_id', 'streak_type', name='uq_user_streak'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def update_streak(self, activity_date=None):
        """Update the streak based on new activity."""
        if activity_date is None:
            activity_date = datetime.now(timezone.utc).date()
        
        # If this is the first activity or consecutive day
        if (self.last_activity_date is None or 
            activity_date == self.last_activity_date + timedelta(days=1)):
            self.current_streak += 1
            if self.streak_start_date is None:
                self.streak_start_date = activity_date
        # If same day, no change
        elif activity_date == self.last_activity_date:
            pass
        # If gap in streak, reset
        else:
            self.current_streak = 1
            self.streak_start_date = activity_date
        
        # Update longest streak if current is longer
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_activity_date = activity_date
        self.updated_at = datetime.now(timezone.utc)
    
    def is_streak_active(self):
        """Check if the streak is still active (not broken)."""
        if self.last_activity_date is None:
            return False
        
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        return self.last_activity_date >= yesterday
    
    def get_days_since_last_activity(self):
        """Get the number of days since last activity."""
        if self.last_activity_date is None:
            return None
        
        today = datetime.now(timezone.utc).date()
        return (today - self.last_activity_date).days
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "streak_type": self.streak_type,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "streak_start_date": self.streak_start_date.isoformat() if self.streak_start_date else None,
            "is_active": self.is_streak_active(),
            "days_since_last_activity": self.get_days_since_last_activity(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<UserStreak {self.user_id} - {self.streak_type}: {self.current_streak}>"


class UserPoints(db.Model):
    """Model for tracking user points/XP from achievements and activities."""
    __tablename__ = "user_points"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Points tracking
    total_points = db.Column(db.Integer, default=0, nullable=False)  # Total points earned
    current_level = db.Column(db.Integer, default=1, nullable=False)  # Current user level
    points_to_next_level = db.Column(db.Integer, default=100, nullable=False)  # Points needed for next level
    
    # Level progression
    total_levels_earned = db.Column(db.Integer, default=0, nullable=False)  # Total levels earned
    highest_level_reached = db.Column(db.Integer, default=1, nullable=False)  # Highest level ever reached
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="points")
    point_transactions = db.relationship("PointTransaction", back_populates="user_points", cascade="all, delete-orphan")
    
    # Unique constraint to ensure one points record per user
    __table_args__ = (
        db.UniqueConstraint('user_id', name='uq_user_points'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def add_points(self, points, source="achievement", description=None, context_data=None):
        """Add points and check for level up."""
        if points <= 0:
            return False
        
        old_level = self.current_level
        self.total_points += points
        
        # Check for level up
        while self.total_points >= self.points_to_next_level:
            self.current_level += 1
            self.total_levels_earned += 1
            if self.current_level > self.highest_level_reached:
                self.highest_level_reached = self.current_level
            
            # Calculate points needed for next level (simple progression)
            self.points_to_next_level = self.current_level * 100
        
        self.updated_at = datetime.now(timezone.utc)
        
        # Record transaction
        transaction = PointTransaction(
            user_points_id=self.id,
            points_change=points,
            source=source,
            description=description,
            context_data=context_data
        )
        db.session.add(transaction)
        
        return self.current_level > old_level  # Return True if leveled up
    
    def get_level_progress(self):
        """Get progress towards next level as percentage."""
        if self.points_to_next_level == 0:
            return 100
        
        current_level_points = (self.current_level - 1) * 100
        points_in_current_level = self.total_points - current_level_points
        points_needed_for_level = self.points_to_next_level - current_level_points
        
        return min(100, (points_in_current_level / points_needed_for_level) * 100)
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_points": self.total_points,
            "current_level": self.current_level,
            "points_to_next_level": self.points_to_next_level,
            "total_levels_earned": self.total_levels_earned,
            "highest_level_reached": self.highest_level_reached,
            "level_progress": self.get_level_progress(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<UserPoints {self.user_id}: Level {self.current_level} ({self.total_points} pts)>"


class PointTransaction(db.Model):
    """Model for tracking point transactions (earned/spent)."""
    __tablename__ = "point_transaction"
    
    id = db.Column(db.Integer, primary_key=True)
    user_points_id = db.Column(db.Integer, db.ForeignKey("user_points.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    points_change = db.Column(db.Integer, nullable=False)  # Positive for earned, negative for spent
    source = db.Column(db.String(100), nullable=False)  # 'achievement', 'activity', 'bonus', etc.
    description = db.Column(db.Text, nullable=True)  # Human-readable description
    context_data = db.Column(db.JSON, nullable=True)  # Additional context data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    
    # Relationships
    user_points = db.relationship("UserPoints", back_populates="point_transactions")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def is_positive(self):
        """Check if this is a positive transaction (points earned)."""
        return self.points_change > 0
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_points_id": self.user_points_id,
            "points_change": self.points_change,
            "source": self.source,
            "description": self.description,
            "context_data": self.context_data,
            "is_positive": self.is_positive,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        change_type = "earned" if self.is_positive else "spent"
        return f"<PointTransaction {change_type} {abs(self.points_change)} pts>"


class CoinTransaction(db.Model):
    """Model for tracking coin transactions (achievement coins and top-up coins)."""
    __tablename__ = "coin_transaction"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction details
    coin_type = db.Column(db.String(20), nullable=False, index=True)  # 'achievement', 'topup'
    coins_change = db.Column(db.Integer, nullable=False)  # Positive for earned/purchased, negative for spent
    source = db.Column(db.String(100), nullable=False)  # 'achievement_reward', 'purchase', 'content_purchase', etc.
    description = db.Column(db.Text, nullable=True)  # Human-readable description
    context_data = db.Column(db.JSON, nullable=True)  # Additional context data
    
    # For top-up transactions
    payment_provider = db.Column(db.String(50), nullable=True)  # 'stripe', 'paypal', etc.
    payment_id = db.Column(db.String(255), nullable=True)  # External payment ID
    amount_paid = db.Column(db.Numeric(10, 2), nullable=True)  # Amount paid in real currency
    currency = db.Column(db.String(3), default='IDR', nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="coin_transactions")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @property
    def is_positive(self):
        """Check if this is a positive transaction (coins earned/purchased)."""
        return self.coins_change > 0
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "coin_type": self.coin_type,
            "coins_change": self.coins_change,
            "source": self.source,
            "description": self.description,
            "context_data": self.context_data,
            "payment_provider": self.payment_provider,
            "payment_id": self.payment_id,
            "amount_paid": float(self.amount_paid) if self.amount_paid else None,
            "currency": self.currency,
            "is_positive": self.is_positive,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        change_type = "earned" if self.is_positive else "spent"
        return f"<CoinTransaction {self.user_id}: {change_type} {self.coins_change} {self.coin_type} coins>"


class UserCoins(db.Model):
    """Model for tracking user's coin balances (achievement and top-up coins)."""
    __tablename__ = "user_coins"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Coin balances
    achievement_coins = db.Column(db.Integer, default=0, nullable=False)  # Coins earned from achievements
    topup_coins = db.Column(db.Integer, default=0, nullable=False)  # Coins purchased with real money
    
    # Statistics
    total_achievement_coins_earned = db.Column(db.Integer, default=0, nullable=False)  # Total ever earned
    total_topup_coins_purchased = db.Column(db.Integer, default=0, nullable=False)  # Total ever purchased
    total_coins_spent = db.Column(db.Integer, default=0, nullable=False)  # Total ever spent
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="coins")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def add_coins(self, coins, coin_type, source="achievement", description=None, context_data=None, 
                  payment_provider=None, payment_id=None, amount_paid=None, currency=None):
        """Add coins and record transaction."""
        if coins <= 0:
            return False
        
        # Update balance
        if coin_type == 'achievement':
            self.achievement_coins += coins
            self.total_achievement_coins_earned += coins
        elif coin_type == 'topup':
            self.topup_coins += coins
            self.total_topup_coins_purchased += coins
        
        self.updated_at = datetime.now(timezone.utc)
        
        # Record transaction
        transaction = CoinTransaction(
            user_id=self.user_id,
            coin_type=coin_type,
            coins_change=coins,
            source=source,
            description=description,
            context_data=context_data,
            payment_provider=payment_provider,
            payment_id=payment_id,
            amount_paid=amount_paid,
            currency=currency
        )
        db.session.add(transaction)
        
        return True
    
    def spend_coins(self, coins, coin_type, source="content_purchase", description=None, context_data=None):
        """Spend coins and record transaction."""
        if coins <= 0:
            return False
        
        # Check if user has enough coins
        if coin_type == 'achievement' and self.achievement_coins < coins:
            return False
        elif coin_type == 'topup' and self.topup_coins < coins:
            return False
        elif coin_type == 'any':
            # Try topup coins first, then achievement coins
            if self.topup_coins >= coins:
                coin_type = 'topup'
            elif self.achievement_coins >= coins:
                coin_type = 'achievement'
            else:
                return False
        
        # Update balance
        if coin_type == 'achievement':
            self.achievement_coins -= coins
        elif coin_type == 'topup':
            self.topup_coins -= coins
        
        self.total_coins_spent += coins
        self.updated_at = datetime.now(timezone.utc)
        
        # Record transaction
        transaction = CoinTransaction(
            user_id=self.user_id,
            coin_type=coin_type,
            coins_change=-coins,  # Negative for spending
            source=source,
            description=description,
            context_data=context_data
        )
        db.session.add(transaction)
        
        return True
    
    def get_total_coins(self):
        """Get total available coins (achievement + topup)."""
        return self.achievement_coins + self.topup_coins
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_coins": self.achievement_coins,
            "topup_coins": self.topup_coins,
            "total_coins": self.get_total_coins(),
            "total_achievement_coins_earned": self.total_achievement_coins_earned,
            "total_topup_coins_purchased": self.total_topup_coins_purchased,
            "total_coins_spent": self.total_coins_spent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def __repr__(self):
        return f"<UserCoins {self.user_id}: {self.achievement_coins} achievement + {self.topup_coins} topup = {self.get_total_coins()} total>"


class CoinManager:
    """Manager class for handling coin system operations."""
    
    @staticmethod
    def get_or_create_user_coins(user_id):
        """Get or create a user coins record."""
        user_coins = UserCoins.query.filter_by(user_id=user_id).first()
        
        if not user_coins:
            user_coins = UserCoins(user_id=user_id)
            db.session.add(user_coins)
        
        return user_coins
    
    @staticmethod
    def add_achievement_coins(user_id, coins, source="achievement", description=None, context_data=None):
        """Add achievement coins to user."""
        user_coins = CoinManager.get_or_create_user_coins(user_id)
        success = user_coins.add_coins(coins, 'achievement', source, description, context_data)
        
        if success:
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def add_topup_coins(user_id, coins, payment_provider, payment_id, amount_paid, currency='IDR', description=None, context_data=None):
        """Add top-up coins to user."""
        user_coins = CoinManager.get_or_create_user_coins(user_id)
        success = user_coins.add_coins(
            coins, 'topup', 'purchase', description, context_data,
            payment_provider, payment_id, amount_paid, currency
        )
        
        if success:
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def spend_coins(user_id, coins, coin_type='any', source="content_purchase", description=None, context_data=None):
        """Spend coins from user balance."""
        user_coins = CoinManager.get_or_create_user_coins(user_id)
        success = user_coins.spend_coins(coins, coin_type, source, description, context_data)
        
        if success:
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_user_coin_balance(user_id):
        """Get user's coin balance."""
        user_coins = UserCoins.query.filter_by(user_id=user_id).first()
        if not user_coins:
            return {
                "achievement_coins": 0,
                "topup_coins": 0,
                "total_coins": 0
            }
        return user_coins.to_dict()
    
    @staticmethod
    def can_afford_content(user_id, required_coins, coin_type='any'):
        """Check if user can afford content with specified coin type."""
        # First check if user is premium - premium users bypass coin system
        user = User.query.get(user_id)
        if user and user.is_premium:
            return True
        
        # For non-premium users, check coin balance
        user_coins = UserCoins.query.filter_by(user_id=user_id).first()
        if not user_coins:
            return False
        
        if coin_type == 'achievement':
            return user_coins.achievement_coins >= required_coins
        elif coin_type == 'topup':
            return user_coins.topup_coins >= required_coins
        elif coin_type == 'any':
            return user_coins.get_total_coins() >= required_coins
        
        return False
    
    @staticmethod
    def purchase_content(user_id, news_id, required_coins, coin_type='any', source="content_purchase"):
        """Purchase content with coins. Premium users bypass coin requirement."""
        # First check if user is premium - premium users bypass coin system
        user = User.query.get(user_id)
        if user and user.is_premium:
            # Premium users can access content without spending coins
            return {
                "success": True,
                "coins_spent": 0,
                "coin_type_used": "premium_bypass",
                "message": "Premium user - no coins required"
            }
        
        # For non-premium users, spend coins
        user_coins = CoinManager.get_or_create_user_coins(user_id)
        
        # Determine which coin type to use
        actual_coin_type = coin_type
        if coin_type == 'any':
            # Try topup coins first, then achievement coins
            if user_coins.topup_coins >= required_coins:
                actual_coin_type = 'topup'
            elif user_coins.achievement_coins >= required_coins:
                actual_coin_type = 'achievement'
            else:
                return {
                    "success": False,
                    "error": "Insufficient coins",
                    "required": required_coins,
                    "available": user_coins.get_total_coins()
                }
        
        # Spend the coins
        success = user_coins.spend_coins(
            required_coins, 
            actual_coin_type, 
            source, 
            f"Purchased content (News ID: {news_id})",
            {"news_id": news_id, "original_coin_type": coin_type}
        )
        
        if success:
            db.session.commit()
            return {
                "success": True,
                "coins_spent": required_coins,
                "coin_type_used": actual_coin_type,
                "remaining_balance": user_coins.to_dict()
            }
        else:
            return {
                "success": False,
                "error": "Failed to spend coins",
                "required": required_coins,
                "available": user_coins.to_dict()
            }


def add_achievement_relationships_to_user():
    """Add achievement-related relationships to the User model."""
    # Add these relationships to the User class
    # Coin system relationships are now defined directly in User model
    pass


# Achievement system helper functions
class AchievementManager:
    """Manager class for handling achievement logic."""
    
    @staticmethod
    def get_or_create_user_achievement(user_id, achievement_id):
        """Get or create a user achievement record."""
        user_achievement = UserAchievement.query.filter_by(
            user_id=user_id, 
            achievement_id=achievement_id
        ).first()
        
        if not user_achievement:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id
            )
            db.session.add(user_achievement)
        
        return user_achievement
    
    @staticmethod
    def get_or_create_user_streak(user_id, streak_type):
        """Get or create a user streak record."""
        user_streak = UserStreak.query.filter_by(
            user_id=user_id,
            streak_type=streak_type
        ).first()
        
        if not user_streak:
            user_streak = UserStreak(
                user_id=user_id,
                streak_type=streak_type
            )
            db.session.add(user_streak)
        
        return user_streak
    
    @staticmethod
    def get_or_create_user_points(user_id):
        """Get or create a user points record."""
        user_points = UserPoints.query.filter_by(user_id=user_id).first()
        
        if not user_points:
            user_points = UserPoints(user_id=user_id)
            db.session.add(user_points)
        
        return user_points
    
    @staticmethod
    def check_achievements(user_id, criteria_type, current_value, source="activity", context_data=None):
        """Check and update achievements for a specific criteria type."""
        achievements = Achievement.query.filter_by(
            criteria_type=criteria_type,
            is_active=True
        ).all()
        
        user_points = AchievementManager.get_or_create_user_points(user_id)
        completed_achievements = []
        
        for achievement in achievements:
            user_achievement = AchievementManager.get_or_create_user_achievement(
                user_id, achievement.id
            )
            
            # Update progress
            old_progress = user_achievement.current_progress
            user_achievement.update_progress(current_value)
            
            # Log progress change
            if old_progress != current_value:
                progress_log = AchievementProgress(
                    user_achievement_id=user_achievement.id,
                    progress_type='set',
                    old_value=old_progress,
                    new_value=current_value,
                    source=source,
                    context_data=context_data
                )
                db.session.add(progress_log)
            
            # Check if achievement was just completed
            if user_achievement.is_completed and user_achievement.completed_at:
                # Check if this is a new completion (completed_at was just set)
                if user_achievement.points_earned > 0:
                    leveled_up = user_points.add_points(
                        user_achievement.points_earned,
                        source="achievement",
                        description=f"Achievement: {achievement.name}",
                        context_data={"achievement_id": achievement.id}
                    )
                    completed_achievements.append({
                        "achievement": achievement,
                        "user_achievement": user_achievement,
                        "leveled_up": leveled_up
                    })
        
        return completed_achievements
    
    @staticmethod
    def update_streak(user_id, streak_type, activity_date=None):
        """Update a user's streak."""
        user_streak = AchievementManager.get_or_create_user_streak(user_id, streak_type)
        user_streak.update_streak(activity_date)
        return user_streak
    
    @staticmethod
    def get_user_achievements_summary(user_id):
        """Get a summary of user's achievements."""
        user_achievements = UserAchievement.query.filter_by(user_id=user_id).all()
        user_points = UserPoints.query.filter_by(user_id=user_id).first()
        user_streaks = UserStreak.query.filter_by(user_id=user_id).all()
        
        total_achievements = len(user_achievements)
        completed_achievements = len([ua for ua in user_achievements if ua.is_completed])
        total_points = user_points.total_points if user_points else 0
        current_level = user_points.current_level if user_points else 1
        
        return {
            "total_achievements": total_achievements,
            "completed_achievements": completed_achievements,
            "completion_rate": (completed_achievements / total_achievements * 100) if total_achievements > 0 else 0,
            "total_points": total_points,
            "current_level": current_level,
            "streaks": {streak.streak_type: streak.to_dict() for streak in user_streaks}
        }


# Event listeners

class SEOInjectionSettings(db.Model):
    """Model for managing SEO injection settings and default values."""
    __tablename__ = "seo_injection_settings"

    id = db.Column(db.Integer, primary_key=True)
    
    # Website Information
    website_name = db.Column(db.String(200), nullable=True)
    website_url = db.Column(db.String(255), nullable=True)
    website_description = db.Column(db.Text, nullable=True)
    website_language = db.Column(db.String(10), nullable=True, default='id')
    website_logo = db.Column(db.String(255), nullable=True)
    
    # Organization Information
    organization_name = db.Column(db.String(200), nullable=True)
    organization_logo = db.Column(db.String(255), nullable=True)
    organization_description = db.Column(db.Text, nullable=True)
    organization_type = db.Column(db.String(100), nullable=True)
    
    # Social Media Information
    facebook_url = db.Column(db.String(255), nullable=True)
    twitter_url = db.Column(db.String(255), nullable=True)
    instagram_url = db.Column(db.String(255), nullable=True)
    youtube_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    
    # Contact Information
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    contact_address = db.Column(db.Text, nullable=True)
    
    # Default SEO Templates
    default_meta_description = db.Column(db.Text, nullable=True)
    default_meta_keywords = db.Column(db.Text, nullable=True)
    default_meta_author = db.Column(db.String(100), nullable=True)
    default_meta_robots = db.Column(db.String(50), nullable=True, default='index, follow')
    
    # Default Open Graph Templates
    default_og_title = db.Column(db.String(200), nullable=True)
    default_og_description = db.Column(db.Text, nullable=True)
    default_og_image = db.Column(db.String(255), nullable=True)
    
    # Default Twitter Templates
    default_twitter_card = db.Column(db.String(50), nullable=True, default='summary')
    default_twitter_title = db.Column(db.String(200), nullable=True)
    default_twitter_description = db.Column(db.Text, nullable=True)
    
    # Default Structured Data Templates
    default_structured_data_type = db.Column(db.String(50), nullable=True, default='Article')
    default_canonical_url = db.Column(db.String(255), nullable=True)
    default_meta_language = db.Column(db.String(10), nullable=True, default='id')
    
    # Injection Settings
    auto_inject_news = db.Column(db.Boolean, default=True, nullable=False)
    auto_inject_albums = db.Column(db.Boolean, default=True, nullable=False)
    auto_inject_chapters = db.Column(db.Boolean, default=True, nullable=False)
    auto_inject_root = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        super(SEOInjectionSettings, self).__init__(**kwargs)
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default schema markup templates."""
        if not hasattr(self, '_defaults_loaded'):
            self._defaults_loaded = True
    
    def get_website_info(self):
        """Get website information, with fallback to BrandIdentity."""
        from models import BrandIdentity
        
        brand_info = BrandIdentity.query.first()
        
        return {
            'name': self.website_name or (brand_info.website_name if brand_info else 'LilyOpenCMS'),
            'url': self.website_url or (brand_info.website_url if brand_info else 'https://lilycms.com'),
            'description': self.website_description or (brand_info.website_description if brand_info else ''),
            'language': self.website_language or 'id',
            'logo': self.website_logo or (brand_info.logo_url if brand_info else '')
        }
    
    def get_organization_info(self):
        """Get organization information, with fallback to BrandIdentity."""
        from models import BrandIdentity
        
        brand_info = BrandIdentity.query.first()
        
        return {
            'name': self.organization_name or (brand_info.organization_name if brand_info else ''),
            'logo': self.organization_logo or (brand_info.logo_url if brand_info else ''),
            'description': self.organization_description or (brand_info.organization_description if brand_info else ''),
            'type': self.organization_type or 'Organization'
        }
    
    def get_social_media_info(self):
        """Get social media information."""
        return {
            'facebook': self.facebook_url,
            'twitter': self.twitter_url,
            'instagram': self.instagram_url,
            'youtube': self.youtube_url,
            'linkedin': self.linkedin_url
        }
    
    def get_contact_info(self):
        """Get contact information."""
        return {
            'email': self.contact_email,
            'phone': self.contact_phone,
            'address': self.contact_address
        }
    
    def format_template(self, template, **kwargs):
        """Format a template string with provided values and defaults."""
        from models import BrandIdentity
        
        brand_info = BrandIdentity.query.first()
        
        # Default values
        defaults = {
            'website_name': self.website_name or (brand_info.website_name if brand_info else 'LilyOpenCMS'),
            'website_url': self.website_url or (brand_info.website_url if brand_info else 'https://lilycms.com'),
            'website_description': self.website_description or (brand_info.website_description if brand_info else ''),
            'organization_name': self.organization_name or (brand_info.organization_name if brand_info else ''),
            'organization_logo': self.organization_logo or (brand_info.logo_url if brand_info else ''),
        }
        
        # Merge with provided kwargs
        defaults.update(kwargs)
        
        try:
            return template.format(**defaults)
        except (KeyError, ValueError):
            return template


# ============================================================================
# USER PROFILE SYSTEM MODELS
# ============================================================================


class UserProfile(db.Model):
    """Extended user profile information."""
    __tablename__ = "user_profile"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Profile information
    pronouns = db.Column(db.String(50), nullable=True)  # e.g., "he/him", "she/her", "they/them"
    short_bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Social media links (stored as JSON)
    social_links = db.Column(db.JSON, nullable=True)  # {"twitter": "...", "instagram": "...", etc.}
    
    # Profile preferences
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    show_email = db.Column(db.Boolean, default=False, nullable=False)
    show_birthdate = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile {self.user_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "pronouns": self.pronouns,
            "short_bio": self.short_bio,
            "location": self.location,
            "website": self.website,
            "social_links": self.social_links or {},
            "is_public": self.is_public,
            "show_email": self.show_email,
            "show_birthdate": self.show_birthdate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserStats(db.Model):
    """User statistics and analytics."""
    __tablename__ = "user_stats"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Content statistics
    total_stories = db.Column(db.Integer, default=0, nullable=False)
    total_albums = db.Column(db.Integer, default=0, nullable=False)
    total_views = db.Column(db.Integer, default=0, nullable=False)
    total_likes = db.Column(db.Integer, default=0, nullable=False)
    total_comments = db.Column(db.Integer, default=0, nullable=False)
    
    # Follower statistics
    total_followers = db.Column(db.Integer, default=0, nullable=False)
    total_following = db.Column(db.Integer, default=0, nullable=False)
    
    # Reading statistics
    total_reads = db.Column(db.Integer, default=0, nullable=False)
    total_saved = db.Column(db.Integer, default=0, nullable=False)
    
    # Activity tracking (stored as JSON for flexibility)
    activity_calendar = db.Column(db.JSON, nullable=True)  # {"2024-01-01": 5, "2024-01-02": 3, ...}
    monthly_stats = db.Column(db.JSON, nullable=True)  # {"2024-01": {"stories": 10, "views": 100}, ...}
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Relationships
    user = db.relationship("User", back_populates="stats")
    
    def __repr__(self):
        return f"<UserStats {self.user_id}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_stories": self.total_stories,
            "total_albums": self.total_albums,
            "total_views": self.total_views,
            "total_likes": self.total_likes,
            "total_comments": self.total_comments,
            "total_followers": self.total_followers,
            "total_following": self.total_following,
            "total_reads": self.total_reads,
            "total_saved": self.total_saved,
            "activity_calendar": self.activity_calendar or {},
            "monthly_stats": self.monthly_stats or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_stats(self):
        """Update statistics from actual data."""
        from models import News, Album, UserLibrary, ReadingHistory
        
        # Count user's content
        self.total_stories = News.query.filter_by(user_id=self.user_id, is_visible=True).count()
        self.total_albums = Album.query.filter_by(user_id=self.user_id, is_visible=True).count()
        
        # Count followers/following
        self.total_followers = self.user.followers.count()
        self.total_following = self.user.following.count()
        
        # Count user's library and reading history
        self.total_saved = UserLibrary.query.filter_by(user_id=self.user_id).count()
        self.total_reads = ReadingHistory.query.filter_by(user_id=self.user_id).count()
        
        # Update activity calendar (simplified - can be enhanced later)
        today = datetime.now().date().isoformat()
        if not self.activity_calendar:
            self.activity_calendar = {}
        if today not in self.activity_calendar:
            self.activity_calendar[today] = 0
        self.activity_calendar[today] += 1


# =============================================================================
# WRITE ACCESS REQUEST MODEL
# =============================================================================

class WriteAccessRequest(db.Model):
    """Model for tracking write access requests from users."""
    __tablename__ = 'write_access_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_reason = db.Column(db.Text, nullable=True)  # Why they want write access
    portfolio_links = db.Column(db.Text, nullable=True)  # Links to their work
    experience_description = db.Column(db.Text, nullable=True)  # Their writing experience
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='request_status'), default='pending')
    admin_notes = db.Column(db.Text, nullable=True)  # Notes from admin
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])
    
    def __repr__(self):
        return f'<WriteAccessRequest {self.id}: {self.user.username} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': {
                'username': self.user.username,
                'full_name': self.user.get_full_name(),
                'email': self.user.email
            },
            'request_reason': self.request_reason,
            'portfolio_links': self.portfolio_links,
            'experience_description': self.experience_description,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'reviewed_by': self.reviewed_by.username if self.reviewed_by else None,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }


