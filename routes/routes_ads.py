"""
Routes for Ads Management System
Handles CRUD operations for ads, campaigns, placements, and analytics
"""

from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, and_, desc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json
import logging
import time
import hashlib

from models import db, AdCampaign, Ad, AdPlacement, AdStats, User, UserRole
from itsdangerous import URLSafeSerializer, BadSignature
from urllib.parse import urlencode
from routes.common_imports import *
from optimizations.cache_config import safe_cache_get, safe_cache_set, cache

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
ads_bp = Blueprint('ads', __name__, url_prefix='/ads')


# =============================================================================
# INTERNAL UTILITIES (RATE LIMITING, DEDUP, VALIDATION)
# =============================================================================

def _client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    return forwarded or request.remote_addr or 'unknown'


def _rate_limit_key(prefix: str) -> str:
    return f"rate:{prefix}:{_client_ip()}"


def _increment_window_counter(key: str, window_seconds: int) -> int:
    try:
        redis_client = getattr(cache.cache, '_client', None)
        if not redis_client:
            return 0
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        count, _ = pipe.execute()
        return int(count)
    except Exception as e:
        current_app.logger.debug(f"Rate limit increment failed for {key}: {e}")
        return 0


def rate_limited(prefix: str, limit: int, window_seconds: int) -> bool:
    key = _rate_limit_key(prefix)
    count = _increment_window_counter(key, window_seconds)
    return count > limit


def _dedupe_event(key: str, ttl_seconds: int) -> bool:
    try:
        redis_client = getattr(cache.cache, '_client', None)
        if not redis_client:
            return False
        # SETNX-like behavior using set with NX
        created = redis_client.set(key, '1', ex=ttl_seconds, nx=True)
        return created is False
    except Exception as e:
        current_app.logger.debug(f"Dedupe set failed for {key}: {e}")
        return False


def _validate_serve_payload(data: dict) -> tuple[bool, str]:
    required = ['page_type', 'section', 'position']
    for field in required:
        if not data.get(field):
            return False, f"Missing field: {field}"
    max_ads = data.get('max_ads', 1)
    try:
        max_ads = int(max_ads)
    except Exception:
        return False, "max_ads must be an integer"
    if max_ads < 1 or max_ads > 5:
        return False, "max_ads must be between 1 and 5"
    return True, ""


def _same_origin_ok() -> bool:
    ref = request.referrer or ''
    host = request.host_url
    return ref.startswith(host) or ref == ''


# =============================================================================
# CAMPAIGN MANAGEMENT
# =============================================================================

@ads_bp.route('/campaigns')
@login_required
def campaigns_list():
    """List all ad campaigns."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view ads.', 'error')
        return redirect(url_for('main.index'))
    
    campaigns = AdCampaign.query.order_by(desc(AdCampaign.created_at)).all()
    return render_template('admin/ads/campaigns_list.html', campaigns=campaigns)


@ads_bp.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    """Create a new ad campaign."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to create ads.', 'error')
        return redirect(url_for('ads.campaigns_list'))
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            campaign = AdCampaign(
                name=data['name'],
                description=data.get('description'),
                is_active=data.get('is_active', True),
                start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
                end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
                budget=data.get('budget'),
                currency=data.get('currency', 'IDR'),
                target_audience=data.get('target_audience'),
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            return jsonify({'success': True, 'campaign': campaign.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating campaign: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return render_template('admin/ads/campaign_form.html')


@ads_bp.route('/campaigns/<int:campaign_id>')
@login_required
def view_campaign(campaign_id):
    """View a specific campaign."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view ads.', 'error')
        return redirect(url_for('ads.campaigns_list'))
    
    campaign = AdCampaign.query.get_or_404(campaign_id)
    return render_template('admin/ads/campaign_detail.html', campaign=campaign)


@ads_bp.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Edit a campaign."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to edit ads.', 'error')
        return redirect(url_for('ads.campaigns_list'))
    
    campaign = AdCampaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            campaign.name = data['name']
            campaign.description = data.get('description')
            campaign.is_active = data.get('is_active', True)
            campaign.start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
            campaign.end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None
            campaign.budget = data.get('budget')
            campaign.currency = data.get('currency', 'IDR')
            campaign.target_audience = data.get('target_audience')
            campaign.updated_by = current_user.id
            
            db.session.commit()
            
            return jsonify({'success': True, 'campaign': campaign.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating campaign: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return render_template('admin/ads/campaign_form.html', campaign=campaign)


@ads_bp.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    """Delete a campaign."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        flash('You do not have permission to delete ads.', 'error')
        return redirect(url_for('ads.campaigns_list'))
    
    campaign = AdCampaign.query.get_or_404(campaign_id)
    
    try:
        db.session.delete(campaign)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True})
        flash('Campaign deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting campaign: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash('Error deleting campaign.', 'error')
    
    return redirect(url_for('ads.campaigns_list'))


# =============================================================================
# AD MANAGEMENT
# =============================================================================

@ads_bp.route('/ads')
@login_required
def ads_list():
    """List all ads."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view ads.', 'error')
        return redirect(url_for('main.index'))
    
    ads = Ad.query.order_by(desc(Ad.created_at)).all()
    campaigns = AdCampaign.query.filter_by(is_active=True).all()
    return render_template('admin/ads/ads_list.html', ads=ads, campaigns=campaigns)


@ads_bp.route('/ads/create', methods=['GET', 'POST'])
@login_required
def create_ad():
    """Create a new ad."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to create ads.', 'error')
        return redirect(url_for('ads.ads_list'))
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Handle image upload if present
            image_info = None
            if 'image_file' in request.files:
                image_file = request.files['image_file']
                if image_file and image_file.filename:
                    from routes.utils.ad_image_utils import save_ad_image
                    image_info, errors = save_ad_image(image_file)
                    if errors:
                        return jsonify({'success': False, 'error': '; '.join(errors)}), 400
            
            ad = Ad(
                title=data['title'],
                description=data.get('description'),
                ad_type=data['ad_type'],
                content_type=data['content_type'],
                image_url=data.get('image_url') if not image_info else None,
                image_filename=image_info['filename'] if image_info else None,
                image_upload_path=image_info['upload_path'] if image_info else None,
                image_alt=data.get('image_alt'),
                image_width=image_info['width'] if image_info else None,
                image_height=image_info['height'] if image_info else None,
                image_file_size=image_info['file_size'] if image_info else None,
                text_content=data.get('text_content'),
                html_content=data.get('html_content'),
                target_url=data.get('target_url'),
                external_ad_code=data.get('external_ad_code'),
                external_ad_client=data.get('external_ad_client'),
                external_ad_slot=data.get('external_ad_slot'),
                width=data.get('width'),
                height=data.get('height'),
                css_classes=data.get('css_classes'),
                inline_styles=data.get('inline_styles'),
                is_active=data.get('is_active', True),
                start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
                end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
                priority=data.get('priority', 0),
                campaign_id=data.get('campaign_id'),
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            db.session.add(ad)
            db.session.commit()
            
            return jsonify({'success': True, 'ad': ad.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating ad: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    campaigns = AdCampaign.query.filter_by(is_active=True).all()
    return render_template('admin/ads/ad_form.html', campaigns=campaigns)


@ads_bp.route('/ads/<int:ad_id>')
@login_required
def view_ad(ad_id):
    """View a specific ad."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view ads.', 'error')
        return redirect(url_for('ads.ads_list'))
    
    ad = Ad.query.get_or_404(ad_id)
    return render_template('admin/ads/ad_detail.html', ad=ad)


@ads_bp.route('/ads/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ad(ad_id):
    """Edit an ad."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to edit ads.', 'error')
        return redirect(url_for('ads.ads_list'))
    
    ad = Ad.query.get_or_404(ad_id)
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            # Handle image upload if present
            image_info = None
            if 'image_file' in request.files:
                image_file = request.files['image_file']
                if image_file and image_file.filename:
                    from routes.utils.ad_image_utils import save_ad_image, delete_ad_image
                    
                    # Delete old image if exists
                    if ad.image_upload_path:
                        delete_ad_image(ad.image_upload_path)
                    
                    # Save new image
                    image_info, errors = save_ad_image(image_file)
                    if errors:
                        return jsonify({'success': False, 'error': '; '.join(errors)}), 400
            
            ad.title = data['title']
            ad.description = data.get('description')
            ad.ad_type = data['ad_type']
            ad.content_type = data['content_type']
            
            # Update image fields
            if image_info:
                ad.image_url = None  # Clear external URL if uploading new image
                ad.image_filename = image_info['filename']
                ad.image_upload_path = image_info['upload_path']
                ad.image_width = image_info['width']
                ad.image_height = image_info['height']
                ad.image_file_size = image_info['file_size']
            elif data.get('image_url'):
                # If setting external URL, clear uploaded image fields
                ad.image_url = data.get('image_url')
                ad.image_filename = None
                ad.image_upload_path = None
                ad.image_width = None
                ad.image_height = None
                ad.image_file_size = None
            
            ad.image_alt = data.get('image_alt')
            ad.text_content = data.get('text_content')
            ad.html_content = data.get('html_content')
            ad.target_url = data.get('target_url')
            ad.external_ad_code = data.get('external_ad_code')
            ad.external_ad_client = data.get('external_ad_client')
            ad.external_ad_slot = data.get('external_ad_slot')
            ad.width = data.get('width')
            ad.height = data.get('height')
            ad.css_classes = data.get('css_classes')
            ad.inline_styles = data.get('inline_styles')
            ad.is_active = data.get('is_active', True)
            ad.start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
            ad.end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None
            ad.priority = data.get('priority', 0)
            ad.campaign_id = data.get('campaign_id')
            ad.updated_by = current_user.id
            
            db.session.commit()
            
            return jsonify({'success': True, 'ad': ad.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating ad: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    campaigns = AdCampaign.query.filter_by(is_active=True).all()
    return render_template('admin/ads/ad_form.html', ad=ad, campaigns=campaigns)


@ads_bp.route('/ads/<int:ad_id>/delete', methods=['POST'])
@login_required
def delete_ad(ad_id):
    """Delete an ad."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        flash('You do not have permission to delete ads.', 'error')
        return redirect(url_for('ads.ads_list'))
    
    ad = Ad.query.get_or_404(ad_id)
    
    try:
        # Delete associated image file if exists
        if ad.image_upload_path:
            from routes.utils.ad_image_utils import delete_ad_image
            delete_ad_image(ad.image_upload_path)
        
        db.session.delete(ad)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True})
        flash('Ad deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting ad: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash('Error deleting ad.', 'error')
    
    return redirect(url_for('ads.ads_list'))


# =============================================================================
# PLACEMENT MANAGEMENT
# =============================================================================

@ads_bp.route('/placements')
@login_required
def placements_list():
    """List all ad placements."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view ads.', 'error')
        return redirect(url_for('main.index'))
    
    placements = AdPlacement.query.order_by(desc(AdPlacement.created_at)).all()
    return render_template('admin/ads/placements_list.html', placements=placements)


@ads_bp.route('/placements/create', methods=['GET', 'POST'])
@login_required
def create_placement():
    """Create a new ad placement."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to create ads.', 'error')
        return redirect(url_for('ads.placements_list'))
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            placement = AdPlacement(
                name=data['name'],
                description=data.get('description'),
                page_type=data['page_type'],
                page_specific=data.get('page_specific'),
                section=data['section'],
                position=data['position'],
                position_value=data.get('position_value'),
                max_ads_per_page=data.get('max_ads_per_page', 1),
                rotation_type=data.get('rotation_type', 'random'),
                display_frequency=data.get('display_frequency', 1.0),
                user_type=data.get('user_type'),
                device_type=data.get('device_type'),
                location_targeting=data.get('location_targeting'),
                is_active=data.get('is_active', True),
                ad_id=data['ad_id'],
                created_by=current_user.id,
                updated_by=current_user.id
            )
            
            db.session.add(placement)
            db.session.commit()
            
            return jsonify({'success': True, 'placement': placement.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating placement: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    ads = Ad.query.filter_by(is_active=True).all()
    return render_template('admin/ads/placement_form.html', ads=ads)


@ads_bp.route('/placements/<int:placement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_placement(placement_id):
    """Edit an ad placement."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to edit ads.', 'error')
        return redirect(url_for('ads.placements_list'))
    
    placement = AdPlacement.query.get_or_404(placement_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            placement.name = data['name']
            placement.description = data.get('description')
            placement.page_type = data['page_type']
            placement.page_specific = data.get('page_specific')
            placement.section = data['section']
            placement.position = data['position']
            placement.position_value = data.get('position_value')
            placement.max_ads_per_page = data.get('max_ads_per_page', 1)
            placement.rotation_type = data.get('rotation_type', 'random')
            placement.display_frequency = data.get('display_frequency', 1.0)
            placement.user_type = data.get('user_type')
            placement.device_type = data.get('device_type')
            placement.location_targeting = data.get('location_targeting')
            placement.is_active = data.get('is_active', True)
            placement.ad_id = data['ad_id']
            placement.updated_by = current_user.id
            
            db.session.commit()
            
            return jsonify({'success': True, 'placement': placement.to_dict()})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating placement: {e}")
            return jsonify({'success': False, 'error': str(e)}), 400
    
    ads = Ad.query.filter_by(is_active=True).all()
    return render_template('admin/ads/placement_form.html', placement=placement, ads=ads)


@ads_bp.route('/placements/<int:placement_id>/delete', methods=['POST'])
@login_required
def delete_placement(placement_id):
    """Delete an ad placement."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        if request.is_json:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        flash('You do not have permission to delete ads.', 'error')
        return redirect(url_for('ads.placements_list'))
    
    placement = AdPlacement.query.get_or_404(placement_id)
    
    try:
        db.session.delete(placement)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True})
        flash('Placement deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting placement: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 400
        flash('Error deleting placement.', 'error')
    
    return redirect(url_for('ads.placements_list'))


# =============================================================================
# AD SERVING API
# =============================================================================

@ads_bp.route('/api/serve', methods=['POST'])
def serve_ads():
    """Serve ads for a specific page and context with premium detector integration."""
    try:
        # Global disable gate for ads (BrandIdentity)
        try:
            from models import BrandIdentity
            brand = BrandIdentity.query.first()
            if brand and (not getattr(brand, 'enable_ads', True) or not getattr(brand, 'enable_campaigns', True)):
                return jsonify({'success': True, 'ads': [], 'reason': 'ads_globally_disabled'})
        except Exception:
            pass
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        if not _same_origin_ok():
            return jsonify({'success': False, 'error': 'Invalid origin'}), 400

        data = request.get_json() or {}
        ok, msg = _validate_serve_payload(data)
        if not ok:
            return jsonify({'success': False, 'error': msg}), 400
        page_type = data.get('page_type')
        page_specific = data.get('page_specific')
        section = data.get('section')
        position = data.get('position')
        position_value = data.get('position_value')
        user_id = data.get('user_id')
        device_type = data.get('device_type', 'desktop')
        location = data.get('location')
        max_ads = int(data.get('max_ads', 1))
        
        # Enhanced premium context handling
        user_has_premium = data.get('user_has_premium', False)
        user_should_show_ads = data.get('user_should_show_ads', True)
        
        # Get user if provided
        user = None
        if user_id:
            user = User.query.get(user_id)
            # Override premium status with actual user data if available
            if user:
                user_has_premium = user.has_active_premium_subscription()
                user_should_show_ads = user.should_show_ads()
        
        # Premium user with ads disabled - don't serve ads
        if user_has_premium and not user_should_show_ads:
            return jsonify({
                'success': True,
                'ads': [],
                'reason': 'premium_user_ads_disabled'
            })
        
        # Cache key for serve response
        cache_key_parts = [
            'ads_serve', page_type or '', page_specific or '', section or '', position or '', str(position_value),
            device_type or '', 'prem' if user_has_premium else 'nonprem', 'shads' if user_should_show_ads else 'noads',
        ]
        cache_key = hashlib.md5('|'.join(map(str, cache_key_parts)).encode()).hexdigest()

        cached = safe_cache_get(cache_key)
        if cached:
            return jsonify(cached)
        
        # Find matching placements
        query = AdPlacement.query.filter(
            AdPlacement.is_active == True,
            AdPlacement.page_type == page_type,
            AdPlacement.section == section,
            AdPlacement.position == position
        )
        
        if position_value is not None:
            query = query.filter(AdPlacement.position_value == position_value)
        
        if page_specific:
            query = query.filter(
                (AdPlacement.page_specific == page_specific) | 
                (AdPlacement.page_specific.is_(None))
            )
        else:
            query = query.filter(AdPlacement.page_specific.is_(None))
        
        placements = query.all()
        
        # Filter placements based on targeting and premium status
        valid_placements = []
        for placement in placements:
            # Skip placements for non-premium users if placement is premium-only
            if hasattr(placement, 'premium_only') and placement.premium_only and not user_has_premium:
                continue
                
            # Skip placements for premium users if placement is non-premium-only
            if hasattr(placement, 'non_premium_only') and placement.non_premium_only and user_has_premium:
                continue
                
            if placement.should_display(user, device_type, location):
                valid_placements.append(placement)
        
        # Get ads for valid placements (with rotation)
        ads_to_serve = []
        served_count = 0
        
        # Randomize placements for better rotation
        import random
        random.shuffle(valid_placements)
        
        for placement in valid_placements:
            if served_count >= max_ads:
                break
                
            ad = placement.ad
            if ad and ad.is_active_now():
                # Check ad type access control
                # Internal ads: only serve to same origin (web interface)
                # External ads: only serve to different origin or with API key (external apps)
                is_same_origin = _same_origin_ok()
                has_api_key = request.headers.get('X-API-Key') or data.get('api_key')
                
                if ad.ad_type == 'internal' and not is_same_origin:
                    # Skip internal ads for external API calls
                    continue
                elif ad.ad_type == 'external' and is_same_origin and not has_api_key:
                    # Skip external ads for same origin unless API key is provided
                    continue
                
                # Get page context for styling
                page_context = {
                    'card_style': data.get('card_style', ''),
                    'page_type': page_type,
                    'section': section,
                    'user_has_premium': user_has_premium,
                    'user_should_show_ads': user_should_show_ads,
                    'ad_type': ad.ad_type
                }
                
                ads_to_serve.append({
                    'ad_id': ad.id,
                    'html': ad.get_rendered_html(page_context),
                    'placement_id': placement.id,
                    'position': placement.position,
                    'position_value': placement.position_value,
                    'ad_type': ad.ad_type
                })
                
                served_count += 1
        
        # If no ads matched, return a graceful fallback internal ad when user can see ads
        if not ads_to_serve and user_should_show_ads:
            # Minimal, themed fallback content to avoid blank placements
            fallback_html = (
                '<div class="ad-container internal-ad">'
                '  <div class="ad-content">'
                '    <a href="/about" class="block no-underline">'
                '      <div class="p-4 rounded-md border border-[color:var(--border)] bg-[color:var(--card)]">'
                '        <div class="text-sm text-muted-foreground">Iklan</div>'
                '        <div class="mt-1 font-semibold">Promosikan brand Anda di sini</div>'
                '        <div class="text-sm text-muted-foreground">Hubungi kami untuk memasang iklan</div>'
                '      </div>'
                '    </a>'
                '  </div>'
                '</div>'
            )
            ads_to_serve.append({
                'ad_id': 0,
                'html': fallback_html,
                'placement_id': None,
                'position': position,
                'position_value': position_value,
            })

        response_payload = {
            'success': True,
            'ads': ads_to_serve,
            'premium_context': {
                'user_has_premium': user_has_premium,
                'user_should_show_ads': user_should_show_ads
            }
        }

        safe_cache_set(cache_key, response_payload, timeout=30)
        return jsonify(response_payload)
        
    except Exception as e:
        logger.error(f"Error serving ads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ads_bp.route('/api/serve/batch', methods=['POST'])
def serve_ads_batch():
    """Batch-serve ads for multiple placements in one request."""
    try:
        # Global disable gate for ads (BrandIdentity)
        try:
            from models import BrandIdentity
            brand = BrandIdentity.query.first()
            if brand and (not getattr(brand, 'enable_ads', True) or not getattr(brand, 'enable_campaigns', True)):
                return jsonify({'success': True, 'adsByPlacement': {}, 'reason': 'ads_globally_disabled'})
        except Exception:
            pass
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        if not _same_origin_ok():
            return jsonify({'success': False, 'error': 'Invalid origin'}), 400

        data = request.get_json() or {}
        placements = data.get('placements', [])
        if not isinstance(placements, list) or not placements:
            return jsonify({'success': False, 'error': 'placements array required'}), 400

        user_id = data.get('user_id')
        user_has_premium = data.get('user_has_premium', False)
        user_should_show_ads = data.get('user_should_show_ads', True)
        device_type = data.get('device_type', 'desktop')
        card_style = data.get('card_style', '')
        user = None
        if user_id:
            user = User.query.get(user_id)
            if user:
                user_has_premium = user.has_active_premium_subscription()
                user_should_show_ads = user.should_show_ads()

        if user_has_premium and not user_should_show_ads:
            return jsonify({'success': True, 'adsByPlacement': {}, 'reason': 'premium_user_ads_disabled'})

        ads_by_placement = {}

        for p in placements:
            ok, msg = _validate_serve_payload(p)
            if not ok:
                ads_by_placement[p.get('key') or 'unknown'] = []
                continue
            page_type = p.get('page_type')
            page_specific = p.get('page_specific')
            section = p.get('section')
            position = p.get('position')
            position_value = p.get('position_value')
            max_ads = int(p.get('max_ads', 1))

            query = AdPlacement.query.filter(
                AdPlacement.is_active == True,
                AdPlacement.page_type == page_type,
                AdPlacement.section == section,
                AdPlacement.position == position
            )
            if position_value is not None:
                query = query.filter(AdPlacement.position_value == position_value)
            if page_specific:
                query = query.filter((AdPlacement.page_specific == page_specific) | (AdPlacement.page_specific.is_(None)))
            else:
                query = query.filter(AdPlacement.page_specific.is_(None))

            valid = []
            for placement in query.all():
                if hasattr(placement, 'premium_only') and placement.premium_only and not user_has_premium:
                    continue
                if hasattr(placement, 'non_premium_only') and placement.non_premium_only and user_has_premium:
                    continue
                if placement.should_display(user, device_type, None):
                    valid.append(placement)

            import random
            random.shuffle(valid)
            served = []
            count = 0
            for placement in valid:
                if count >= max_ads:
                    break
                ad = placement.ad
                if ad and ad.is_active_now():
                    # Check ad type access control (same logic as single serve)
                    is_same_origin = _same_origin_ok()
                    has_api_key = request.headers.get('X-API-Key') or data.get('api_key')
                    
                    if ad.ad_type == 'internal' and not is_same_origin:
                        # Skip internal ads for external API calls
                        continue
                    elif ad.ad_type == 'external' and is_same_origin and not has_api_key:
                        # Skip external ads for same origin unless API key is provided
                        continue
                    
                    page_context = {
                        'card_style': card_style,
                        'page_type': page_type,
                        'section': section,
                        'user_has_premium': user_has_premium,
                        'user_should_show_ads': user_should_show_ads,
                        'ad_type': ad.ad_type
                    }
                    served.append({
                        'ad_id': ad.id,
                        'html': ad.get_rendered_html(page_context),
                        'placement_id': placement.id,
                        'position': placement.position,
                        'position_value': placement.position_value,
                        'ad_type': ad.ad_type
                    })
                    count += 1

            ads_by_placement[p.get('key') or f"{section}_{position}_{position_value}"] = served

        return jsonify({'success': True, 'adsByPlacement': ads_by_placement})
    except Exception as e:
        logger.error(f"Error batch serving ads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ads_bp.route('/api/external/serve', methods=['POST'])
def serve_external_ads():
    """Dedicated API endpoint for external apps to access external ads only."""
    try:
        # Check for API key authentication
        api_key = request.headers.get('X-API-Key') or request.get_json().get('api_key') if request.is_json else None
        if not api_key:
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        # TODO: Implement API key validation against database
        # For now, we'll accept any API key (you should implement proper validation)
        
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        
        data = request.get_json() or {}
        
        # Validate required fields
        required_fields = ['page_type', 'section', 'position']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        page_type = data.get('page_type')
        page_specific = data.get('page_specific')
        section = data.get('section')
        position = data.get('position')
        position_value = data.get('position_value')
        max_ads = int(data.get('max_ads', 1))
        device_type = data.get('device_type', 'mobile')  # Default to mobile for external apps
        
        # Find matching placements for external ads only
        query = AdPlacement.query.join(Ad).filter(
            AdPlacement.is_active == True,
            AdPlacement.page_type == page_type,
            AdPlacement.section == section,
            AdPlacement.position == position,
            Ad.ad_type == 'external'  # Only external ads
        )
        
        if position_value is not None:
            query = query.filter(AdPlacement.position_value == position_value)
        
        if page_specific:
            query = query.filter(
                (AdPlacement.page_specific == page_specific) | 
                (AdPlacement.page_specific.is_(None))
            )
        else:
            query = query.filter(AdPlacement.page_specific.is_(None))
        
        placements = query.all()
        
        # Get ads for valid placements
        ads_to_serve = []
        served_count = 0
        
        for placement in placements:
            if served_count >= max_ads:
                break
                
            ad = placement.ad
            if ad and ad.is_active_now():
                # External ads only - no additional filtering needed
                page_context = {
                    'page_type': page_type,
                    'section': section,
                    'device_type': device_type,
                    'ad_type': 'external'
                }
                
                ads_to_serve.append({
                    'ad_id': ad.id,
                    'html': ad.get_rendered_html(page_context),
                    'placement_id': placement.id,
                    'position': placement.position,
                    'position_value': placement.position_value,
                    'ad_type': ad.ad_type,
                    'target_url': ad.target_url,
                    'image_url': ad.get_image_url()
                })
                
                served_count += 1
        
        return jsonify({
            'success': True,
            'ads': ads_to_serve,
            'count': len(ads_to_serve),
            'api_version': '1.0'
        })
        
    except Exception as e:
        logger.error(f"Error serving external ads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ads_bp.route('/click')
def click_redirect():
    """Secure redirect endpoint for external ad clicks with basic URL signing and UTM tagging."""
    try:
        ad_id = request.args.get('ad_id', type=int)
        target = request.args.get('url', type=str)
        sig = request.args.get('sig', type=str)
        event_id = request.args.get('event_id')
        if not ad_id or not target:
            return redirect(url_for('main.index'))

        if sig:
            s = URLSafeSerializer(current_app.secret_key, salt='ads-click')
            try:
                data = s.loads(sig)
                if data.get('ad_id') != ad_id or data.get('url') != target:
                    return redirect(url_for('main.index'))
            except BadSignature:
                return redirect(url_for('main.index'))

        # Append UTM parameters
        try:
            from urllib.parse import urlparse, urlunparse, parse_qsl
            parts = list(urlparse(target))
            qs = dict(parse_qsl(parts[4]))
            qs.setdefault('utm_source', 'exposeur')
            qs.setdefault('utm_medium', 'display')
            qs.setdefault('utm_campaign', f'ad_{ad_id}')
            if event_id:
                qs.setdefault('utm_content', event_id)
            parts[4] = urlencode(qs)
            target = urlunparse(parts)
        except Exception:
            pass

        return redirect(target)
    except Exception:
        return redirect(url_for('main.index'))


@ads_bp.route('/api/layout/recommend', methods=['POST'])
def recommend_layout_positions():
    """Recommend ad placement positions based on backend rules and client-probed counts.

    Expects JSON payload like:
    {
      "page_type": "home|news|album|gallery|videos",
      "sections": [
         {"key": "latest-articles", "selector": "[data-group=\"latest-articles\"] article", "item_count": 10},
         {"key": "popular-news", "selector": "[data-group=\"popular-news\"] article", "item_count": 6},
         {"key": "news-grid", "selector": "#news-grid > *", "item_count": 20}
      ]
    }
    Returns: { success: true, recommendations: { key: { selector, after: [n,...] } } }
    """
    try:
        # Global disable gate for ads (BrandIdentity)
        try:
            from models import BrandIdentity
            brand = BrandIdentity.query.first()
            if brand and not getattr(brand, 'enable_ads', True):
                return jsonify({ 'success': True, 'recommendations': {}, 'reason': 'ads_globally_disabled' })
        except Exception:
            pass
        if not request.is_json:
            return jsonify({ 'success': False, 'error': 'JSON required' }), 400
        data = request.get_json() or {}
        page_type = (data.get('page_type') or '').strip()
        if not page_type:
            return jsonify({ 'success': False, 'error': 'page_type required' }), 400
        sections = data.get('sections') or []

        # Normalize sections map
        key_to_section = {}
        for s in sections:
            key = str(s.get('key') or 'default')
            key_to_section[key] = {
                'selector': s.get('selector') or '',
                'item_count': int(s.get('item_count') or 0)
            }

        # Backend rules per page type
        rules = {}
        if page_type == 'home':
            rules = {
                'latest-articles': { 'after': [3, 6] },
                'popular-news': { 'after': [2, 4] },
            }
        elif page_type == 'news':
            rules = { 'news-grid': { 'after': [3, 7] } }
        elif page_type == 'album':
            rules = { 'albums-grid': { 'after': [4, 9] } }
        elif page_type == 'gallery':
            rules = { 'image-grid': { 'after': [2, 5] } }
        elif page_type == 'videos':
            rules = { 'videos-grid': { 'after': [2, 5] } }

        # Build recommendations filtered by current item_count
        recommendations = {}
        for key, rule in rules.items():
            sec = key_to_section.get(key)
            if not sec:
                # If client didn't provide, try to fall back to a known selector
                fallback_selector = {
                    'latest-articles': '[data-group="latest-articles"] article',
                    'popular-news': '[data-group="popular-news"] article',
                    'news-grid': '#news-grid > *',
                    'albums-grid': '#albums-grid > *',
                    'videos-grid': '#videos-grid > *',
                    'image-grid': '#image-grid-container > *, #latest-image-grid-container > *',
                }.get(key, '')
                sec = { 'selector': fallback_selector, 'item_count': 0 }
            after = [n for n in rule.get('after', []) if n <= max(0, int(sec.get('item_count') or 0))]
            # Always keep the smallest one even if zero count (to allow reservation)
            if not after and rule.get('after'):
                after = [min(rule['after'])]
            recommendations[key] = {
                'selector': sec.get('selector') or '',
                'after': after
            }

        return jsonify({ 'success': True, 'recommendations': recommendations })
    except Exception as e:
        logger.error(f"Error recommending layout positions: {e}")
        return jsonify({ 'success': False, 'error': str(e) }), 500


@ads_bp.route('/api/track-impression', methods=['POST'])
def record_ad_impression():
    """Record an ad impression."""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        if rate_limited('ads_impr', limit=60, window_seconds=60):
            return jsonify({'success': False, 'error': 'rate_limited'}), 429
        data = request.get_json() or {}
        ad_id = data.get('ad_id')
        event_id = data.get('event_id')
        is_viewable = bool(data.get('viewable', False))
        
        if not ad_id:
            return jsonify({'success': False, 'error': 'ad_id required'}), 400
        
        # Find the ad
        ad = Ad.query.get(ad_id)
        if not ad:
            logger.warning(f"Ad with ID {ad_id} not found")
            return jsonify({'success': False, 'error': 'Ad not found'}), 404
        
        # Dedupe short window
        dedupe_key_parts = ['impr', str(ad_id), _client_ip(), event_id or '']
        dedupe_key = 'dedupe:' + hashlib.md5('|'.join(dedupe_key_parts).encode()).hexdigest()
        if _dedupe_event(dedupe_key, ttl_seconds=300):
            return jsonify({'success': True, 'deduped': True})
        
        ad.record_impression()

        # Update aggregated stats
        today = datetime.utcnow().date()
        hour = datetime.utcnow().hour
        stats = AdStats.query.filter_by(ad_id=ad.id, date=today, hour=hour).first()
        if not stats:
            stats = AdStats(ad_id=ad.id, date=today, hour=hour, impressions=0, clicks=0)
            db.session.add(stats)
        stats.impressions += 1
        if is_viewable:
            stats.viewable_impressions += 1
        if request.user_agent:
            ua = (request.user_agent.platform or '').lower()
            if 'mobile' in ua:
                stats.mobile_impressions += 1
            elif 'tablet' in ua:
                stats.tablet_impressions += 1
            else:
                stats.desktop_impressions += 1

        db.session.commit()
        
        logger.info(f"Recorded impression for ad {ad_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording ad impression for ad {ad_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ads_bp.route('/api/track-click', methods=['POST'])
def record_ad_click():
    """Record an ad click."""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'JSON required'}), 400
        if rate_limited('ads_click', limit=30, window_seconds=60):
            return jsonify({'success': False, 'error': 'rate_limited'}), 429
        data = request.get_json() or {}
        ad_id = data.get('ad_id')
        event_id = data.get('event_id')
        
        if not ad_id:
            return jsonify({'success': False, 'error': 'ad_id required'}), 400
        
        # Find the ad
        ad = Ad.query.get(ad_id)
        if not ad:
            logger.warning(f"Ad with ID {ad_id} not found")
            return jsonify({'success': False, 'error': 'Ad not found'}), 404
        
        # Dedupe short window
        dedupe_key_parts = ['click', str(ad_id), _client_ip(), event_id or '']
        dedupe_key = 'dedupe:' + hashlib.md5('|'.join(dedupe_key_parts).encode()).hexdigest()
        if _dedupe_event(dedupe_key, ttl_seconds=300):
            return jsonify({'success': True, 'deduped': True})
        
        ad.record_click()

        # Update aggregated stats
        today = datetime.utcnow().date()
        hour = datetime.utcnow().hour
        stats = AdStats.query.filter_by(ad_id=ad.id, date=today, hour=hour).first()
        if not stats:
            stats = AdStats(ad_id=ad.id, date=today, hour=hour, impressions=0, clicks=0)
            db.session.add(stats)
        stats.clicks += 1

        db.session.commit()
        
        logger.info(f"Recorded click for ad {ad_id}")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error recording ad click for ad {ad_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ANALYTICS
# =============================================================================

@ads_bp.route('/analytics')
@login_required
def analytics_dashboard():
    """Ads analytics dashboard."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to view analytics.', 'error')
        return redirect(url_for('main.index'))
    
    # Get summary stats
    total_ads = Ad.query.count()
    active_ads = Ad.query.filter_by(is_active=True).count()
    total_campaigns = AdCampaign.query.count()
    active_campaigns = AdCampaign.query.filter_by(is_active=True).count()
    
    # Get recent stats
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    recent_stats = db.session.query(
        func.sum(AdStats.impressions).label('total_impressions'),
        func.sum(AdStats.clicks).label('total_clicks'),
        func.sum(AdStats.revenue).label('total_revenue')
    ).filter(
        AdStats.date >= week_ago
    ).first()
    
    # Get top performing ads
    top_ads = db.session.query(
        Ad.id,
        Ad.title,
        Ad.impressions,
        Ad.clicks,
        Ad.ctr
    ).filter(
        Ad.impressions > 0
    ).order_by(desc(Ad.impressions)).limit(10).all()
    
    return render_template('admin/ads/analytics_dashboard.html',
                         total_ads=total_ads,
                         active_ads=active_ads,
                         total_campaigns=total_campaigns,
                         active_campaigns=active_campaigns,
                         recent_stats=recent_stats,
                         top_ads=top_ads)


@ads_bp.route('/api/analytics/stats')
@login_required
def get_analytics_stats():
    """Get analytics statistics."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        # Get date range from request
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = db.session.query(AdStats)
        
        if start_date:
            query = query.filter(AdStats.date >= datetime.fromisoformat(start_date).date())
        if end_date:
            query = query.filter(AdStats.date <= datetime.fromisoformat(end_date).date())
        
        stats = query.all()
        
        # Aggregate data
        aggregated = {}
        for stat in stats:
            date_str = stat.date.isoformat()
            if date_str not in aggregated:
                aggregated[date_str] = {
                    'impressions': 0,
                    'clicks': 0,
                    'revenue': 0.0
                }
            
            aggregated[date_str]['impressions'] += stat.impressions
            aggregated[date_str]['clicks'] += stat.clicks
            aggregated[date_str]['revenue'] += float(stat.revenue or 0)
        
        return jsonify({
            'success': True,
            'stats': aggregated
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ADMIN DASHBOARD
# =============================================================================

@ads_bp.route('/dashboard')
@login_required
def admin_dashboard():
    """Main ads admin dashboard."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to access ads dashboard.', 'error')
        return redirect(url_for('main.index'))
    
    # Get summary stats
    total_ads = Ad.query.count()
    active_ads = Ad.query.filter_by(is_active=True).count()
    total_campaigns = AdCampaign.query.count()
    active_campaigns = AdCampaign.query.filter_by(is_active=True).count()
    total_placements = AdPlacement.query.count()
    active_placements = AdPlacement.query.filter_by(is_active=True).count()
    
    # Count ads with images
    total_images = Ad.query.filter(
        db.or_(
            Ad.image_upload_path.isnot(None),
            Ad.image_url.isnot(None)
        )
    ).count()
    
    # Get recent activity
    recent_ads = Ad.query.order_by(desc(Ad.created_at)).limit(5).all()
    recent_campaigns = AdCampaign.query.order_by(desc(AdCampaign.created_at)).limit(5).all()
    
    # Get performance stats
    total_impressions = db.session.query(func.sum(Ad.impressions)).scalar() or 0
    total_clicks = db.session.query(func.sum(Ad.clicks)).scalar() or 0
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    
    return render_template('admin/ads/dashboard.html',
                         total_ads=total_ads,
                         active_ads=active_ads,
                         total_campaigns=total_campaigns,
                         active_campaigns=active_campaigns,
                         total_placements=total_placements,
                         active_placements=active_placements,
                         recent_ads=recent_ads,
                         recent_campaigns=recent_campaigns,
                         total_impressions=total_impressions,
                         total_clicks=total_clicks,
                         overall_ctr=overall_ctr,
                         total_images=total_images)


# =============================================================================
# IMAGE MANAGEMENT ROUTES
# =============================================================================

@ads_bp.route('/images')
@login_required
def manage_images():
    """Image management interface for ads."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('You do not have permission to manage ad images.', 'error')
        return redirect(url_for('ads.dashboard'))
    
    try:
        # Get all ads with images
        ads_with_images = Ad.query.filter(
            db.or_(
                Ad.image_upload_path.isnot(None),
                Ad.image_url.isnot(None)
            )
        ).order_by(Ad.created_at.desc()).all()
        
        return render_template('admin/ads/images_management.html', 
                             ads_with_images=ads_with_images)
    
    except Exception as e:
        logger.error(f"Error loading image management: {e}")
        flash('Error loading image management interface.', 'error')
        return redirect(url_for('ads.dashboard'))


@ads_bp.route('/images/upload', methods=['POST'])
@login_required
def upload_images():
    """Upload multiple images for ads."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        uploaded_files = request.files.getlist('images')
        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        uploaded_count = 0
        errors = []
        
        for file in uploaded_files:
            if file and file.filename:
                try:
                    from routes.utils.ad_image_utils import save_ad_image
                    image_info, file_errors = save_ad_image(file)
                    
                    if image_info:
                        # Create a placeholder ad with the uploaded image
                        ad = Ad(
                            title=f"Uploaded Image - {image_info['filename']}",
                            description="Image uploaded via image management",
                            ad_type='internal',
                            content_type='image',
                            image_filename=image_info['filename'],
                            image_upload_path=image_info['upload_path'],
                            image_width=image_info['width'],
                            image_height=image_info['height'],
                            image_file_size=image_info['file_size'],
                            is_active=False,  # Inactive by default, needs to be configured
                            created_by=current_user.id
                        )
                        db.session.add(ad)
                        uploaded_count += 1
                    else:
                        errors.extend(file_errors)
                        
                except Exception as e:
                    errors.append(f"Error uploading {file.filename}: {str(e)}")
        
        if uploaded_count > 0:
            db.session.commit()
        
        if errors:
            return jsonify({
                'success': uploaded_count > 0,
                'message': f'Uploaded {uploaded_count} images',
                'errors': errors
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Successfully uploaded {uploaded_count} images'
            })
    
    except Exception as e:
        logger.error(f"Error uploading images: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Upload failed'}), 500


@ads_bp.route('/images/replace', methods=['POST'])
@login_required
def replace_image():
    """Replace an existing ad image."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        ad_id = request.form.get('ad_id')
        if not ad_id:
            return jsonify({'success': False, 'error': 'Ad ID required'}), 400
        
        ad = Ad.query.get_or_404(ad_id)
        
        # Check if new image file is provided
        if 'image_file' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        image_file = request.files['image_file']
        if not image_file or not image_file.filename:
            return jsonify({'success': False, 'error': 'No image file selected'}), 400
        
        # Delete old image file if it exists
        if ad.image_upload_path:
            from routes.utils.ad_image_utils import delete_ad_image
            delete_ad_image(ad.image_upload_path)
        
        # Save new image
        from routes.utils.ad_image_utils import save_ad_image
        image_info, errors = save_ad_image(image_file)
        
        if errors:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400
        
        # Update ad with new image info
        ad.image_filename = image_info['filename']
        ad.image_upload_path = image_info['upload_path']
        ad.image_width = image_info['width']
        ad.image_height = image_info['height']
        ad.image_file_size = image_info['file_size']
        ad.image_url = None  # Clear external URL
        ad.updated_by = current_user.id
        ad.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image replaced successfully'})
    
    except Exception as e:
        logger.error(f"Error replacing image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Replace failed'}), 500


@ads_bp.route('/images/delete', methods=['POST'])
@login_required
def delete_image():
    """Delete an ad image."""
    # Check permissions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    try:
        data = request.get_json()
        ad_id = data.get('ad_id')
        
        if not ad_id:
            return jsonify({'success': False, 'error': 'Ad ID required'}), 400
        
        ad = Ad.query.get_or_404(ad_id)
        
        # Delete image file if it exists
        if ad.image_upload_path:
            from routes.utils.ad_image_utils import delete_ad_image
            delete_ad_image(ad.image_upload_path)
        
        # Clear image fields
        ad.image_filename = None
        ad.image_upload_path = None
        ad.image_width = None
        ad.image_height = None
        ad.image_file_size = None
        ad.image_url = None
        ad.updated_by = current_user.id
        ad.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
    
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Delete failed'}), 500 