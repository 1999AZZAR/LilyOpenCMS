"""
Common imports for settings routes

This module provides all the necessary imports for the settings route modules.
"""

from flask import render_template, request, redirect, url_for, abort, current_app, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import (
    db, User, News, Category, Album, AlbumChapter, PrivacyPolicy, MediaGuideline, VisiMisi, 
    PedomanHak, Penyangkalan, ContactDetail, TeamMember, YouTubeVideo, UserRole, RootSEO
)