from routes import main_blueprint
from .common_imports import *

@main_blueprint.route("/api/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    """
    GET: Fetch all categories.
    POST: Add a new category (only for settingss and superusers).
    """

    if request.method == "GET":
        # Fetch all categories
        categories = Category.query.all()
        return jsonify(
            [{"id": category.id, "name": category.name} for category in categories]
        )

    # Only allow admin-tier users to add categories
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        return jsonify({"error": "Forbidden"}), 403  # Return JSON, not HTML

    if request.method == "POST":
        # Add a new category
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400  # Return JSON, not HTML

        category_name = data.get("name")

        if not category_name:
            return jsonify(
                {"error": "Category name is required"}
            ), 400  # Return JSON, not HTML

        # Check if the category already exists
        existing_category = Category.query.filter_by(name=category_name).first()
        if existing_category:
            return jsonify(
                {"error": "Category already exists"}
            ), 400  # Return JSON, not HTML

        # Create and add the new category
        new_category = Category(name=category_name)
        db.session.add(new_category)
        db.session.commit()

        return jsonify(
            {"message": "Category added successfully", "id": new_category.id}
        ), 201


@main_blueprint.route("/api/categories/<int:category_id>", methods=["PUT", "DELETE"])
@login_required
def manage_category(category_id):
    """
    PUT: Update an existing category (only for settingss and superusers).
    DELETE: Delete a category (only for settingss and superusers).
    """
    # Only allow admin-tier users to modify categories
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    category = Category.query.get_or_404(category_id)

    if request.method == "PUT":
        # Update the category
        data = request.get_json()
        new_name = data.get("name")

        if not new_name:
            return jsonify({"error": "Category name is required"}), 400

        # Check if the new name already exists
        existing_category = Category.query.filter_by(name=new_name).first()
        if existing_category and existing_category.id != category.id:
            return jsonify({"error": "Category name already exists"}), 400

        # Update the category name
        category.name = new_name
        db.session.commit()

        return jsonify({"message": "Category updated successfully"})

    if request.method == "DELETE":
        # Check for dependencies before deleting
        from models import News, Album
        
        # Count dependencies
        news_count = News.query.filter_by(category_id=category_id).count()
        album_count = Album.query.filter_by(category_id=category_id).count()
        
        if news_count > 0 or album_count > 0:
            # Category is in use, return dependency info
            return jsonify({
                "error": "Category is in use",
                "has_dependencies": True,
                "dependencies": {
                    "news_count": news_count,
                    "album_count": album_count
                }
            }), 409  # Conflict status code
        
        # Safe to delete
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": "Category deleted successfully"})


@main_blueprint.route("/api/categories/<int:category_id>/safe-delete", methods=["POST"])
@login_required
def safe_delete_category(category_id):
    """
    Safe delete a category by reassigning its dependencies to another category.
    """
    # Only allow admin-tier users to modify categories
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    new_category_id = data.get("new_category_id")
    if not new_category_id:
        return jsonify({"error": "New category ID is required"}), 400
    
    # Verify the new category exists
    new_category = Category.query.get(new_category_id)
    if not new_category:
        return jsonify({"error": "New category not found"}), 404
    
    if new_category.id == category_id:
        return jsonify({"error": "Cannot reassign to the same category"}), 400
    
    try:
        from models import News, Album
        
        # Reassign all news items
        news_updated = News.query.filter_by(category_id=category_id).update({
            "category_id": new_category_id
        })
        
        # Reassign all albums
        album_updated = Album.query.filter_by(category_id=category_id).update({
            "category_id": new_category_id
        })
        
        # Delete the original category
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            "message": "Category deleted successfully",
            "reassigned": {
                "news_count": news_updated,
                "album_count": album_updated
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete category: {str(e)}"}), 500