from routes import main_blueprint
from .common_imports import *
from .routes_helper import *
import re

def safe_title(title):
    filtered_title = re.sub(r'\s+', '_', title)
    filtered_title = re.sub(r'[^\w]', '', filtered_title)
    max_length = 50
    if len(filtered_title) > max_length:
        filtered_title = filtered_title[:max_length]
    return filtered_title

# 🛠️ Admin Image Management Page
@main_blueprint.route("/settings/image")
@login_required
def settingsimage():
    if not current_user.is_owner() and current_user.role != UserRole.ADMIN:
        abort(403)

    page = request.args.get('page', 1, type=int)
    # Get per_page from config or default to 20 (adjust default as needed)
    per_page = current_app.config.get('IMAGES_PER_PAGE', 20)

    # Query images using pagination, ordered by upload date descending
    images_pagination = Image.query.order_by(Image.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False) # Use updated_at instead
    return render_template('admin/settings/images_management.html', images_pagination=images_pagination, pagination_route='main.settingsimage')


# 🛠️ Fetch All Images (API)
@main_blueprint.route("/api/images", methods=["GET"])
@login_required
def get_images():
    """Fetches images with pagination for the API."""
    page = request.args.get('page', 1, type=int)
    visibility_filter = request.args.get('visibility', 'all') # Default to 'all'
    description_filter = request.args.get('description', 'all') # Default to 'all'
    usage_filter = request.args.get("usage", "all")

    # Use the same config or default as the HTML route
    per_page = current_app.config.get('IMAGES_PER_PAGE', 20)

    # Base query
    query = Image.query

    # Scope by ownership based on role
    # Superuser/Admin: unrestricted. Subadmin (custom role): unrestricted.
    # Editor (custom role): own + assigned writers' images. Others: own only.
    custom_name = (current_user.custom_role.name.lower() if getattr(current_user, 'custom_role', None) and current_user.custom_role.name else "")
    is_admin_tier = current_user.role in [UserRole.SUPERUSER, UserRole.ADMIN] or custom_name == "subadmin"
    if is_admin_tier:
        pass
    else:
        # Join uploader to allow including admin-tier uploads for everyone
        query = query.join(User, Image.user_id == User.id)
        admin_uploader = or_(
            User.role.in_([UserRole.SUPERUSER, UserRole.ADMIN]),
            and_(User.custom_role_id.isnot(None), CustomRole.name.ilike('%subadmin%'))
        )
        if custom_name == "editor":
            try:
                writer_ids = [w.id for w in getattr(current_user, 'assigned_writers', [])]
            except Exception:
                writer_ids = []
            allowed_ids = set(writer_ids + [current_user.id])
            query = query.filter(or_(Image.user_id.in_(allowed_ids), admin_uploader))
        else:
            query = query.filter(or_(Image.user_id == current_user.id, admin_uploader))

    # Apply visibility filter
    if visibility_filter == 'visible':
        query = query.filter(Image.is_visible == True)
    elif visibility_filter == 'hidden':
        query = query.filter(Image.is_visible == False)

    # Apply description filter
    if description_filter == 'has':
        query = query.filter(or_(Image.description != None, Image.description != ''))
    elif description_filter == 'no':
        query = query.filter(or_(Image.description == None, Image.description == ''))

    # Apply usage filter
    if usage_filter == "used":
        query = query.filter(Image.news.any())
    elif usage_filter == "unused":
        query = query.filter(~Image.news.any())

    # Apply ordering and pagination
    images_pagination = query.order_by(Image.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [image.to_dict() for image in images_pagination.items],
        'page': images_pagination.page,
        'per_page': images_pagination.per_page,
        'total_pages': images_pagination.pages,
        'total_items': images_pagination.total
    })


# 🛠️ Fetch a Single Image (API)
@main_blueprint.route("/api/images/<int:image_id>", methods=["GET"])
def get_image(image_id):
    image = Image.query.get_or_404(image_id)
    return jsonify(image.to_dict())


# 🛠️ Upload an Image (API)
@main_blueprint.route("/api/images", methods=["POST"])
@login_required
def upload_image():
    data = request.form
    file = request.files.get("file")
    image_url = data.get("url")
    description = data.get("description", "")
    name = data.get("name", "")
    is_visible_param = data.get("is_visible")

    if not file and not image_url:
        return jsonify({"error": "Either a file or a URL must be provided"}), 400

    if file and image_url:
        return jsonify({"error": "Cannot provide both a file and a URL"}), 400

    # Process File Upload
    if file:
        filename, file_path = save_file(file, name)

    # Process URL Upload
    else:
        try:
            filename, file_path = download_image(image_url)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # Now AUTO convert to WebP and create thumbnails
    result = process_single_image(file_path)
    if result != "ok":
        return jsonify({"error": result}), 500

    # Update filename to webp version
    base_name, _ = os.path.splitext(filename)
    new_filename = f"{base_name}.webp"
    new_filepath = os.path.join(os.path.dirname(file_path), new_filename)

    # Save Image Record (only WebP version saved)
    # Determine default visibility:
    # - Admin-tier and Editor/Writer uploads default to hidden
    # - Others default to visible
    custom_name = (current_user.custom_role.name.lower() if getattr(current_user, 'custom_role', None) and current_user.custom_role.name else "")
    is_editor_or_writer = custom_name in ["editor", "writer"]
    is_admin_tier = current_user.role in [UserRole.SUPERUSER, UserRole.ADMIN] or custom_name == "subadmin"
    if is_visible_param is not None:
        default_visible = str(is_visible_param).lower() in ("true", "1", "on", "yes")
    else:
        default_visible = not (is_editor_or_writer or is_admin_tier)

    image = Image(
        filename=new_filename,
        filepath=new_filepath,
        description=description,
        is_visible=default_visible,
        user_id=current_user.id,
    )
    db.session.add(image)
    db.session.commit()

    return jsonify({"message": "Image uploaded successfully", "id": image.id}), 201


# 🛠️ Update an Image (API)
@main_blueprint.route("/api/images/<int:image_id>", methods=["PUT"])
@login_required
def update_image(image_id):
    if not current_user.is_owner() and current_user.role != UserRole.ADMIN:
        abort(403)

    image = Image.query.get_or_404(image_id)
    data = request.form
    file = request.files.get("file")
    image_url = data.get("url")
    name = data.get("name", "")
    description = data.get("description", "")

    if file and image_url:
        return jsonify({"error": "Cannot provide both a file and a URL"}), 400

    if not file and not image_url:
        return jsonify({"error": "Either a file or a URL must be provided"}), 400

    # 🔥 Delete old main file + thumbnail
    delete_existing_file(image.filepath)
    if image.thumbnail_path:
        delete_existing_file(image.thumbnail_path)

    # 🔄 Process File Upload
    if file:
        filename, file_path = save_file(file, name)
    else:
        try:
            filename, file_path = download_image(image_url)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    # 🔄 AUTO convert to WebP and generate thumbnail
    result = process_single_image(file_path)
    if result != "ok":
        return jsonify({"error": result}), 500

    # 🔄 Update database with new WebP paths
    base_name, _ = os.path.splitext(filename)
    new_filename = f"{base_name}.webp"
    new_filepath = os.path.join(os.path.dirname(file_path), new_filename)

    image.filename = new_filename
    image.filepath = new_filepath

    # 🔄 Update thumbnail path
    thumbnail_filename = f"{base_name}_thumb.webp"
    thumbnail_filepath = os.path.join(os.path.dirname(file_path), thumbnail_filename)
    image.thumbnail_path = thumbnail_filepath

    # ✏️ Update description if provided
    if description:
        image.description = description

    db.session.commit()
    return jsonify({"message": "Image updated successfully"}), 200


# 🛠️ Toggle Image Visibility (API)
@main_blueprint.route("/api/images/<int:image_id>/visibility", methods=["PATCH"])
@login_required
def toggle_image_visibility(image_id):
    image = Image.query.get_or_404(image_id)
    # Accept JSON, form-encoded, or query param; support keys: is_visible or visible
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = {k: request.form.get(k) for k in ("is_visible", "visible") if k in request.form}
    if not data and request.args:
        data = {k: request.args.get(k) for k in ("is_visible", "visible") if k in request.args}

    val = data.get("is_visible") if "is_visible" in data else data.get("visible")
    if val is None:
        # Fallback: toggle when no explicit value provided
        image.is_visible = not bool(image.is_visible)
        db.session.commit()
        return jsonify({"message": "Visibility toggled", "is_visible": image.is_visible}), 200
    if isinstance(val, str):
        val_norm = val.strip().lower()
        image.is_visible = val_norm in ("true", "1", "on", "yes")
    elif isinstance(val, bool):
        image.is_visible = val
    else:
        return jsonify({"error": "is_visible must be boolean or boolean-like string"}), 400
    db.session.commit()

    return jsonify({"message": "Visibility updated successfully"}), 200


# 🛠️ Delete an Image (API)
@main_blueprint.route("/api/images/<int:image_id>", methods=["DELETE"])
@login_required
def delete_image(image_id):
    if not current_user.is_owner() and current_user.role != UserRole.ADMIN:
        abort(403)

    image = Image.query.get_or_404(image_id)
    delete_existing_file(image.filepath)
    try:
        base_path, _ = os.path.splitext(image.filepath)
        thumb_square_path = f"{base_path}_thumb_square.webp"
        thumb_portrait_path = f"{base_path}_thumb_portrait.webp"
        thumb_landscape_path = f"{base_path}_thumb_landscape.webp"
        delete_existing_file(thumb_square_path)
        delete_existing_file(thumb_portrait_path)
        delete_existing_file(thumb_landscape_path)
    except Exception as e:
        # Log error but don't necessarily stop the deletion process
        current_app.logger.error(f"Error deleting thumbnails for image ID {image_id}: {e}")


    db.session.delete(image)
    db.session.commit()

    return jsonify({"message": "Image deleted successfully"}), 200

@main_blueprint.route("/api/images/bulk-delete", methods=["POST"])
@login_required
def bulk_delete_images():
    data = request.get_json()
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return jsonify({"error": "Invalid or missing 'ids'"}), 400
    images_to_delete = Image.query.filter(Image.id.in_(ids)).all()
    deleted_count = 0
    for image in images_to_delete:
        if image.user_id == current_user.id or current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
            db.session.delete(image)
            deleted_count += 1
    db.session.commit()
    return jsonify({"deleted": deleted_count}), 200

@main_blueprint.route("/api/images/bulk-visibility", methods=["POST"])
@login_required
def bulk_update_images_visibility():
    data = request.get_json()
    ids = data.get("ids", [])
    is_visible = data.get("is_visible")
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        return jsonify({"error": "Invalid or missing 'ids'"}), 400
    if not isinstance(is_visible, bool):
        return jsonify({"error": "'is_visible' must be a boolean"}), 400
    images_to_update = Image.query.filter(Image.id.in_(ids)).all()
    updated_count = 0
    for image in images_to_update:
        if image.user_id == current_user.id or current_user.role in [UserRole.ADMIN, UserRole.SUPERUSER]:
            image.is_visible = is_visible
            updated_count += 1
    db.session.commit()
    return jsonify({"updated": updated_count}), 200

@main_blueprint.route("/api/images/<int:image_id>/usage", methods=["GET"])
@login_required
def get_image_usage(image_id):
    image = Image.query.get_or_404(image_id)
    news_list = []
    for news in image.news:
        news_list.append({
            "id": news.id,
            "title": news.title,
            "url": url_for("main.news_detail", news_id=news.id, news_title=safe_title(news.title), _external=True)
        })
    return jsonify({"news": news_list})