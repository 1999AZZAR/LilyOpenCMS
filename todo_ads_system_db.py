class ApiKey(db.Model):
    """Model for managing API keys for external app access."""
    __tablename__ = "api_key"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Human-readable name for the API key
    key_value = db.Column(db.String(255), unique=True, nullable=False, index=True)  # The actual API key
    description = db.Column(db.Text, nullable=True)  # Description of what this key is for
    
    # Access permissions
    permissions = db.Column(db.JSON, nullable=True)  # List of permissions: ['read_ads', 'track_impressions', 'track_clicks']
    rate_limit_per_hour = db.Column(db.Integer, default=1000, nullable=False)  # Rate limit per hour
    
    # Status and tracking
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # External app information
    app_name = db.Column(db.String(200), nullable=True)  # Name of the external app
    app_version = db.Column(db.String(50), nullable=True)  # Version of the external app
    contact_email = db.Column(db.String(255), nullable=True)  # Contact email for the app developer
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiration date
    
    # Foreign Keys
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_api_keys")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate API key data."""
        if self.rate_limit_per_hour < 0:
            raise ValueError("Rate limit must be non-negative")
        if self.expires_at and self.expires_at <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
    
    def is_valid(self):
        """Check if the API key is valid and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= datetime.utcnow():
            return False
        return True
    
    def update_usage(self):
        """Update usage statistics."""
        self.last_used_at = datetime.utcnow()
        self.usage_count += 1
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "contact_email": self.contact_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f"<ApiKey {self.name} ({self.app_name})>"


class AdImage(db.Model):
    """Model for managing ad images separately from the main Image model."""
    __tablename__ = "ad_image"
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    filepath = db.Column(db.String(500), nullable=False, unique=True)  # Full path to the image
    file_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    mime_type = db.Column(db.String(100), nullable=True)  # MIME type of the image
    
    # Image dimensions
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    
    # Ad-specific metadata
    ad_type = db.Column(db.String(50), nullable=True)  # 'banner', 'display', 'mobile', 'thumbnail'
    alt_text = db.Column(db.String(255), nullable=True)  # Alt text for accessibility
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id", ondelete="CASCADE"), nullable=True)  # Optional link to specific ad
    uploaded_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    ad = db.relationship("Ad", backref="ad_images")
    uploader = db.relationship("User", foreign_keys=[uploaded_by], backref="uploaded_ad_images")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate ad image data."""
        if self.width and self.width <= 0:
            raise ValueError("Width must be positive")
        if self.height and self.height <= 0:
            raise ValueError("Height must be positive")
        if self.file_size and self.file_size <= 0:
            raise ValueError("File size must be positive")
    
    def get_url(self):
        """Get the URL for this ad image."""
        return f"/static/uploads/ads/{self.filename}"
    
    def get_thumbnail_url(self):
        """Get the thumbnail URL for this ad image."""
        name, ext = os.path.splitext(self.filename)
        return f"/static/uploads/ads/thumbnails/{name}_thumb{ext}"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "ad_type": self.ad_type,
            "alt_text": self.alt_text,
            "is_active": self.is_active,
            "url": self.get_url(),
            "thumbnail_url": self.get_thumbnail_url(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ad_id": self.ad_id,
            "uploaded_by": self.uploaded_by
        }
    
    def __repr__(self):
        return f"<AdImage {self.filename}>"


class AdTargeting(db.Model):
    """Model for advanced ad targeting criteria."""
    __tablename__ = "ad_targeting"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Geographic targeting
    countries = db.Column(db.JSON, nullable=True)  # List of country codes: ['US', 'CA', 'GB']
    cities = db.Column(db.JSON, nullable=True)  # List of cities: ['New York', 'London']
    regions = db.Column(db.JSON, nullable=True)  # List of regions/states
    
    # Device targeting
    device_types = db.Column(db.JSON, nullable=True)  # ['desktop', 'mobile', 'tablet']
    operating_systems = db.Column(db.JSON, nullable=True)  # ['windows', 'macos', 'android', 'ios']
    browsers = db.Column(db.JSON, nullable=True)  # ['chrome', 'firefox', 'safari', 'edge']
    
    # User targeting
    user_types = db.Column(db.JSON, nullable=True)  # ['new', 'returning', 'premium', 'guest']
    age_groups = db.Column(db.JSON, nullable=True)  # ['18-24', '25-34', '35-44', '45-54', '55+']
    interests = db.Column(db.JSON, nullable=True)  # List of interest categories
    
    # Content targeting
    categories = db.Column(db.JSON, nullable=True)  # List of content categories
    tags = db.Column(db.JSON, nullable=True)  # List of content tags
    
    # Time-based targeting
    time_zones = db.Column(db.JSON, nullable=True)  # List of time zones
    hours_of_day = db.Column(db.JSON, nullable=True)  # List of hours: [9, 10, 11, 14, 15, 16]
    days_of_week = db.Column(db.JSON, nullable=True)  # List of days: [1, 2, 3, 4, 5] (Monday-Friday)
    
    # Frequency capping
    max_impressions_per_user = db.Column(db.Integer, nullable=True)  # Max impressions per user per day
    max_impressions_per_session = db.Column(db.Integer, nullable=True)  # Max impressions per session
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id", ondelete="CASCADE"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    ad = db.relationship("Ad", backref="targeting")
    creator = db.relationship("User", foreign_keys=[created_by], backref="created_ad_targeting")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate targeting data."""
        if self.max_impressions_per_user and self.max_impressions_per_user <= 0:
            raise ValueError("Max impressions per user must be positive")
        if self.max_impressions_per_session and self.max_impressions_per_session <= 0:
            raise ValueError("Max impressions per session must be positive")
    
    def matches_user(self, user=None, device_type=None, location=None, time_info=None):
        """Check if targeting criteria matches a user."""
        # This would contain the actual targeting logic
        # For now, return True (no targeting restrictions)
        return True
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "countries": self.countries,
            "cities": self.cities,
            "regions": self.regions,
            "device_types": self.device_types,
            "operating_systems": self.operating_systems,
            "browsers": self.browsers,
            "user_types": self.user_types,
            "age_groups": self.age_groups,
            "interests": self.interests,
            "categories": self.categories,
            "tags": self.tags,
            "time_zones": self.time_zones,
            "hours_of_day": self.hours_of_day,
            "days_of_week": self.days_of_week,
            "max_impressions_per_user": self.max_impressions_per_user,
            "max_impressions_per_session": self.max_impressions_per_session,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ad_id": self.ad_id
        }
    
    def __repr__(self):
        return f"<AdTargeting {self.ad_id}>"


class AdApproval(db.Model):
    """Model for managing ad approval workflow."""
    __tablename__ = "ad_approval"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Approval status
    status = db.Column(db.String(50), nullable=False, index=True)  # 'pending', 'approved', 'rejected', 'needs_revision'
    notes = db.Column(db.Text, nullable=True)  # Admin notes about the approval
    
    # Review information
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Revision tracking
    revision_count = db.Column(db.Integer, default=0, nullable=False)
    last_revision_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=default_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=default_utcnow, onupdate=default_utcnow, nullable=False)
    
    # Foreign Keys
    ad_id = db.Column(db.Integer, db.ForeignKey("ad.id", ondelete="CASCADE"), nullable=False)
    submitted_by = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    ad = db.relationship("Ad", backref="approval")
    reviewer = db.relationship("User", foreign_keys=[reviewed_by], backref="reviewed_ads")
    submitter = db.relationship("User", foreign_keys=[submitted_by], backref="submitted_ads")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()
    
    def validate(self):
        """Validate approval data."""
        valid_statuses = ['pending', 'approved', 'rejected', 'needs_revision']
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        if self.revision_count < 0:
            raise ValueError("Revision count must be non-negative")
    
    def approve(self, reviewer_id, notes=None):
        """Approve the ad."""
        self.status = 'approved'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer_id
        if notes:
            self.notes = notes
    
    def reject(self, reviewer_id, notes=None):
        """Reject the ad."""
        self.status = 'rejected'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer_id
        if notes:
            self.notes = notes
    
    def request_revision(self, reviewer_id, notes=None):
        """Request revision of the ad."""
        self.status = 'needs_revision'
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer_id
        self.revision_count += 1
        self.last_revision_at = datetime.utcnow()
        if notes:
            self.notes = notes
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "status": self.status,
            "notes": self.notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "revision_count": self.revision_count,
            "last_revision_at": self.last_revision_at.isoformat() if self.last_revision_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ad_id": self.ad_id,
            "submitted_by": self.submitted_by
        }
    
    def __repr__(self):
        return f"<AdApproval {self.ad_id} {self.status}>"


# Add missing indexes and optimizations at the end of the file