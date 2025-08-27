from routes import main_blueprint
from .common_imports import *
from models import UserLibrary, ReadingHistory


@main_blueprint.route("/api/library", methods=["GET"])
@login_required
def get_library():
    content_type = request.args.get("type")  # optional: 'news' | 'album'
    query = UserLibrary.query.filter_by(user_id=current_user.id)
    if content_type in ("news", "album"):
        query = query.filter_by(content_type=content_type)
    items = query.order_by(UserLibrary.added_at.desc()).all()
    return jsonify([i.to_dict() for i in items])


@main_blueprint.route("/api/library", methods=["POST"])
@login_required
def add_to_library():
    data = request.get_json() or {}
    content_type = data.get("content_type")
    content_id = data.get("content_id")
    if content_type not in ("news", "album") or not isinstance(content_id, int):
        return jsonify({"error": "Invalid content_type or content_id"}), 400
    existing = UserLibrary.query.filter_by(
        user_id=current_user.id, content_type=content_type, content_id=content_id
    ).first()
    if existing:
        return jsonify(existing.to_dict()), 200
    item = UserLibrary(user_id=current_user.id, content_type=content_type, content_id=content_id)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@main_blueprint.route("/api/library", methods=["DELETE"])
@login_required
def remove_from_library():
    data = request.get_json() or {}
    content_type = data.get("content_type")
    content_id = data.get("content_id")
    if content_type not in ("news", "album") or not isinstance(content_id, int):
        return jsonify({"error": "Invalid content_type or content_id"}), 400
    item = UserLibrary.query.filter_by(
        user_id=current_user.id, content_type=content_type, content_id=content_id
    ).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Removed"}), 200


@main_blueprint.route("/api/reading-history", methods=["GET"])
@login_required
def get_reading_history():
    content_type = request.args.get("type")  # optional filter
    query = ReadingHistory.query.filter_by(user_id=current_user.id)
    if content_type in ("news", "album"):
        query = query.filter_by(content_type=content_type)
    items = query.order_by(ReadingHistory.last_read_at.desc()).limit(100).all()
    return jsonify([i.to_dict() for i in items])


