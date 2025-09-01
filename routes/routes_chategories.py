from routes import main_blueprint
from .common_imports import *

@main_blueprint.route("/api/categories", methods=["GET", "POST"])
@login_required
def manage_categories():
    """
    GET: Fetch all categories with groups.
    POST: Add a new category (only for admin-tier users and superusers).
    """

    if request.method == "GET":
        # Check if we want grouped categories or flat list
        grouped = request.args.get('grouped', 'true').lower() == 'true'
        
        if grouped:
            # Fetch categories grouped by their groups
            groups = CategoryGroup.query.filter_by(is_active=True).order_by(CategoryGroup.display_order).all()
            result = []
            
            for group in groups:
                group_categories = Category.query.filter_by(
                    group_id=group.id, 
                    is_active=True
                ).order_by(Category.display_order).all()
                
                if group_categories:  # Only include groups with categories
                    result.append({
                        "group": group.to_dict(),
                        "categories": [cat.to_dict() for cat in group_categories]
                    })
            
            return jsonify(result)
        else:
            # Fetch all categories as flat list (for backward compatibility)
            categories = Category.query.filter_by(is_active=True).order_by(Category.display_order).all()
            return jsonify([cat.to_dict() for cat in categories])

    # Only allow admin-tier users to add categories
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        return jsonify({"error": "Forbidden"}), 403  # Return JSON, not HTML

    if request.method == "POST":
        # Add a new category
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        category_name = data.get("name")
        description = data.get("description", "")
        group_id = data.get("group_id")
        display_order = data.get("display_order", 0)

        if not category_name:
            return jsonify({"error": "Category name is required"}), 400

        # Check if the category already exists
        existing_category = Category.query.filter_by(name=category_name).first()
        if existing_category:
            return jsonify({"error": "Category already exists"}), 400

        # Validate group_id if provided
        if group_id:
            group = CategoryGroup.query.get(group_id)
            if not group:
                return jsonify({"error": "Invalid category group ID"}), 400

        # Create and add the new category
        new_category = Category(
            name=category_name,
            description=description,
            group_id=group_id,
            display_order=display_order
        )
        db.session.add(new_category)
        db.session.commit()

        return jsonify(
            {"message": "Category added successfully", "id": new_category.id}
        ), 201


@main_blueprint.route("/api/category-groups", methods=["GET", "POST"])
@login_required
def manage_category_groups():
    """
    GET: Fetch all category groups.
    POST: Add a new category group (only for admin-tier users and superusers).
    """

    if request.method == "GET":
        # Fetch all category groups
        groups = CategoryGroup.query.filter_by(is_active=True).order_by(CategoryGroup.display_order).all()
        return jsonify([group.to_dict() for group in groups])

    # Only allow admin-tier users to add category groups
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        return jsonify({"error": "Forbidden"}), 403

    if request.method == "POST":
        # Add a new category group
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        group_name = data.get("name")
        description = data.get("description", "")
        display_order = data.get("display_order", 0)

        if not group_name:
            return jsonify({"error": "Group name is required"}), 400

        # Check if the group already exists
        existing_group = CategoryGroup.query.filter_by(name=group_name).first()
        if existing_group:
            return jsonify({"error": "Category group already exists"}), 400

        # Create and add the new group
        new_group = CategoryGroup(
            name=group_name,
            description=description,
            display_order=display_order
        )
        db.session.add(new_group)
        db.session.commit()

        return jsonify(
            {"message": "Category group added successfully", "id": new_group.id}
        ), 201


@main_blueprint.route("/api/category-groups/<int:group_id>", methods=["PUT", "DELETE"])
@login_required
def manage_category_group(group_id):
    """
    PUT: Update an existing category group (only for admin-tier users and superusers).
    DELETE: Delete a category group (only for admin-tier users and superusers).
    """
    # Only allow admin-tier users to modify category groups
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    group = CategoryGroup.query.get_or_404(group_id)

    if request.method == "PUT":
        # Update the category group
        data = request.get_json()
        new_name = data.get("name")
        description = data.get("description", group.description)
        display_order = data.get("display_order", group.display_order)

        if not new_name:
            return jsonify({"error": "Group name is required"}), 400

        # Check if the new name already exists
        existing_group = CategoryGroup.query.filter_by(name=new_name).first()
        if existing_group and existing_group.id != group.id:
            return jsonify({"error": "Group name already exists"}), 400

        # Update the group
        group.name = new_name
        group.description = description
        group.display_order = display_order
        db.session.commit()

        return jsonify({"message": "Category group updated successfully"})

    if request.method == "DELETE":
        # Check for dependencies before deleting
        category_count = Category.query.filter_by(group_id=group_id).count()
        
        if category_count > 0:
            # Group has categories, return dependency info
            return jsonify({
                "error": "Category group has categories",
                "has_dependencies": True,
                "dependencies": {
                    "category_count": category_count
                }
            }), 409  # Conflict status code
        
        # Safe to delete
        db.session.delete(group)
        db.session.commit()
        return jsonify({"message": "Category group deleted successfully"})


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
        description = data.get("description", category.description)
        group_id = data.get("group_id", category.group_id)
        display_order = data.get("display_order", category.display_order)

        if not new_name:
            return jsonify({"error": "Category name is required"}), 400

        # Check if the new name already exists
        existing_category = Category.query.filter_by(name=new_name).first()
        if existing_category and existing_category.id != category.id:
            return jsonify({"error": "Category name already exists"}), 400

        # Validate group_id if provided
        if group_id:
            group = CategoryGroup.query.get(group_id)
            if not group:
                return jsonify({"error": "Invalid category group ID"}), 400

        # Update the category
        category.name = new_name
        category.description = description
        category.group_id = group_id
        category.display_order = display_order
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