"""
Brand Routes

This module handles brand identity and social media management routes.
"""

from routes import main_blueprint
from .common_imports import *
import os
from flask import jsonify


@main_blueprint.route("/settings/social-media")
@login_required
def settings_social_media():
    """Admin page for managing social media links."""
    # Ensure user has the necessary role (admin-tier)
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        current_app.logger.warning(
            f"Forbidden access attempt to /settings/social-media by user {current_user.username} (ID: {current_user.id})"
        )
        abort(
            403, "You do not have permission to access this page."
        )
    # Renders the HTML page where admins can interact with the API (e.g., using JavaScript)
    return render_template('admin/settings/social_media_management.html')


@main_blueprint.route("/settings/brand-identity")
@login_required
def settings_brand_identity():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    # Get brand identity info
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    if not brand_info:
        brand_info = BrandIdentity()
        db.session.add(brand_info)
        db.session.commit()
    
    return render_template('admin/brand/brand_management.html', brand_info=brand_info)


@main_blueprint.route("/settings/brand/info")
@login_required
def settings_brand_info():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    # Get brand identity info
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    if not brand_info:
        brand_info = BrandIdentity()
        db.session.add(brand_info)
        db.session.commit()
    
    return render_template('admin/brand/brand_info.html', brand_info=brand_info)


@main_blueprint.route("/settings/brand/design")
@login_required
def settings_brand_design():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    # Get brand identity info
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    if not brand_info:
        brand_info = BrandIdentity()
        db.session.add(brand_info)
        db.session.commit()
    
    return render_template('admin/brand/brand_design.html', brand_info=brand_info)


@main_blueprint.route("/settings/brand/assets")
@login_required
def settings_brand_assets():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    # Get brand identity info
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    if not brand_info:
        brand_info = BrandIdentity()
        db.session.add(brand_info)
        db.session.commit()
    
    return render_template('admin/brand/brand_assets.html', brand_info=brand_info)


@main_blueprint.route("/settings/brand/colors")
@login_required
def settings_brand_colors():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    # Get brand identity info
    from models import BrandIdentity
    brand_info = BrandIdentity.query.first()
    if not brand_info:
        brand_info = BrandIdentity()
        db.session.add(brand_info)
        db.session.commit()
    
    return render_template('admin/brand/brand_colors.html', brand_info=brand_info)


@main_blueprint.route("/api/brand-identity", methods=["GET"])
@login_required
def get_brand_identity():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    from models import BrandIdentity
    brand = BrandIdentity.query.first()
    if not brand:
        return jsonify({}), 200
    return jsonify(brand.to_dict()), 200


@main_blueprint.route("/api/brand-info", methods=["GET"])
def get_public_brand_info():
    """Public endpoint for getting brand info (no authentication required)"""
    from models import BrandIdentity
    # Force a fresh query to get the latest data
    db.session.expire_all()
    brand = BrandIdentity.query.first()
    if brand:
        # Ensure we have the latest data
        db.session.refresh(brand)
    if not brand:
        return jsonify({
            "brand_name": "LilyOpenCMS",
            "card_design": "classic",
            "homepage_design": "news",
            "categories_display_location": "body"
        }), 200
    return jsonify(brand.to_dict()), 200


@main_blueprint.route("/api/brand-identity", methods=["POST"])
@login_required
def update_brand_identity():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    from models import BrandIdentity
    from routes.routes_helper import save_brand_asset_file
    brand = BrandIdentity.query.first()
    if not brand:
        brand = BrandIdentity()
        db.session.add(brand)
    updated = False
    fixed_urls = {
        "logo_header": "/static/pic/logo.png",
        "logo_footer": "/static/pic/logo_footer.png",
        "favicon": "/static/pic/favicon.png",
        "placeholder_image": "/static/pic/placeholder.png",
    }
    for field in ["logo_header", "logo_footer", "favicon", "placeholder_image"]:
        file = request.files.get(field)
        if file:
            try:
                save_brand_asset_file(file, field)
            except Exception as e:
                return jsonify({"error": str(e)}), 400
            setattr(brand, field, fixed_urls[field])
            updated = True
    # Always set the fields to the fixed URLs (in case files were replaced outside DB)
    for field, url in fixed_urls.items():
        setattr(brand, field, url)
    # Optional: update feature toggles if provided in form
    enable_comments = request.form.get('enable_comments')
    enable_ratings = request.form.get('enable_ratings')
    if enable_comments is not None:
        brand.enable_comments = enable_comments.lower() in ['true', '1', 'on', 'yes']
        updated = True
    if enable_ratings is not None:
        brand.enable_ratings = enable_ratings.lower() in ['true', '1', 'on', 'yes']
        updated = True

    if updated:
        db.session.commit()
    return jsonify(brand.to_dict()), 200


@main_blueprint.route("/api/brand-identity/text", methods=["POST"])
@login_required
def update_brand_identity_text():
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)
    
    from models import BrandIdentity
    data = request.get_json()
    field = data.get("field")
    value = data.get("value")
    
    # Accept False for boolean toggles; only reject when value is truly missing
    if field is None or value is None:
        return jsonify({"error": "Missing field or value"}), 400
    
    if field not in ["brand_name", "tagline", "brand_description", "homepage_design", "categories_display_location", "card_design", "enable_comments", "enable_ratings", "enable_ads", "enable_campaigns"]:
        return jsonify({"error": "Invalid field"}), 400
    
    brand = BrandIdentity.query.first()
    if not brand:
        brand = BrandIdentity()
        db.session.add(brand)
    
    # Coerce boolean for toggles
    if field in ["enable_comments", "enable_ratings", "enable_ads", "enable_campaigns"]:
        setattr(brand, field, str(value).lower() in ['true','1','on','yes'])
    else:
        setattr(brand, field, value)
    db.session.commit()
    
    return jsonify(brand.to_dict()), 200


@main_blueprint.route("/api/brand-colors", methods=["POST"])
@login_required
def update_brand_colors():
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    data = request.get_json()
    variable = data.get("variable")
    value = data.get("value")
    if not variable or not value:
        return jsonify({"error": "Missing variable or value"}), 400
    css_path = os.path.join(current_app.root_path, "static/css/base_css.css")
    try:
        import fcntl
        with open(css_path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            lines = f.readlines()
            f.seek(0)
            in_root = False
            for i, line in enumerate(lines):
                if line.strip().startswith(":root"):
                    in_root = True
                if in_root and variable in line:
                    # Replace the value for this variable
                    parts = line.split(";")
                    new_parts = []
                    for part in parts:
                        if variable in part:
                            new_parts.append(f"    {variable}: {value}")
                        elif part.strip():
                            new_parts.append(part)
                    lines[i] = "; ".join(new_parts) + ";\n"
                    break
                if in_root and "}" in line:
                    break
            f.seek(0)
            f.truncate()
            f.writelines(lines)
            fcntl.flock(f, fcntl.LOCK_UN)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_blueprint.route("/api/brand-colors", methods=["GET"])
@login_required
def get_brand_colors():
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        abort(403)
    css_path = os.path.join(current_app.root_path, "static/css/base_css.css")
    try:
        with open(css_path, "r") as f:
            content = f.read()
        
        # Find the :root block
        import re
        root_match = re.search(r':root\s*\{([^}]+)\}', content, re.DOTALL)
        if not root_match:
            return jsonify([]), 200
        
        root_content = root_match.group(1)
        color_vars = []
        
        # Parse each line in the :root block
        lines = root_content.split(';')
        for line in lines:
            line = line.strip()
            if line.startswith('--') and ':' in line:
                # Split on first colon to handle values that might contain colons
                parts = line.split(':', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip()
                    # Only include color variables (exclude --radius)
                    if not var_name.endswith('radius'):
                        color_vars.append({"name": var_name, "value": var_value})
        
        return jsonify(color_vars), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500