"""
Session Management Routes for Administrators

Provides endpoints for viewing and managing user sessions for security purposes.
"""

from flask import Blueprint
from .common_imports import *
from routes.utils.session_security import get_session_security_manager
from models import UserSession, UserActivity

# Create a separate blueprint for session management to avoid conflicts
session_mgmt_bp = Blueprint('session_mgmt', __name__)

@session_mgmt_bp.route("/session-management", methods=["GET"])
def session_management_dashboard():
    """Session management dashboard for superusers only."""
    if not current_user.is_owner():
        abort(403)

    return render_template("admin/session_management.html")

@session_mgmt_bp.route("/security-dashboard", methods=["GET"])
def security_dashboard():
    """Comprehensive security monitoring dashboard for superusers only."""
    if not current_user.is_owner():
        abort(403)

    return render_template("admin/security_dashboard.html")

@session_mgmt_bp.route("/session-analytics", methods=["GET"])
def session_analytics():
    """Advanced session analytics and reporting for superusers only."""
    if not current_user.is_owner():
        abort(403)

    return render_template("admin/session_analytics.html")

@session_mgmt_bp.route("/api/admin/sessions", methods=["GET"])
@login_required
def get_all_sessions():
    """Get all active sessions for admin monitoring."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_filter = request.args.get('user', '').strip()
        status_filter = request.args.get('status', 'active')

        # Base query
        query = UserSession.query

        # Apply filters
        if user_filter:
            query = query.join(User).filter(
                User.username.ilike(f'%{user_filter}%') |
                User.email.ilike(f'%{user_filter}%')
            )

        if status_filter == 'active':
            query = query.filter(UserSession.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(UserSession.is_active == False)

        # Get paginated results
        pagination = query.order_by(UserSession.last_activity.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        sessions_data = []
        for session in pagination.items:
            sessions_data.append({
                'id': session.id,
                'session_id': session.session_id,
                'user_id': session.user_id,
                'username': session.user.username if session.user else 'Unknown',
                'user_email': session.user.email if session.user else 'Unknown',
                'device_fingerprint': session.device_fingerprint,
                'user_agent': session.user_agent,
                'ip_address': session.ip_address,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                'is_active': session.is_active,
                'invalidated_at': session.invalidated_at.isoformat() if session.invalidated_at else None,
                'invalidation_reason': session.invalidation_reason
            })

        return jsonify({
            'sessions': sessions_data,
            'total': pagination.total,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching sessions: {e}")
        return jsonify({"error": "Failed to fetch sessions"}), 500

@session_mgmt_bp.route("/api/admin/sessions/<session_id>/invalidate", methods=["POST"])
@login_required
def invalidate_session(session_id):
    """Invalidate a specific session."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        session_manager = get_session_security_manager()
        session_manager.invalidate_session(session_id, "Admin manual invalidation")

        return jsonify({"message": f"Session {session_id} invalidated successfully"})

    except Exception as e:
        current_app.logger.error(f"Error invalidating session {session_id}: {e}")
        return jsonify({"error": "Failed to invalidate session"}), 500

@session_mgmt_bp.route("/api/admin/sessions/user/<int:user_id>/invalidate-all", methods=["POST"])
@login_required
def invalidate_all_user_sessions(user_id):
    """Invalidate all sessions for a specific user."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        data = request.get_json()
        reason = data.get('reason', 'Admin bulk invalidation')

        session_manager = get_session_security_manager()
        invalidated_count = session_manager.invalidate_user_sessions(user_id, reason)

        return jsonify({
            "message": f"Invalidated {invalidated_count} sessions for user {user_id}",
            "invalidated_count": invalidated_count
        })

    except Exception as e:
        current_app.logger.error(f"Error invalidating sessions for user {user_id}: {e}")
        return jsonify({"error": "Failed to invalidate user sessions"}), 500

@session_mgmt_bp.route("/api/admin/sessions/cleanup", methods=["POST"])
@login_required
def cleanup_expired_sessions():
    """Clean up expired sessions."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        session_manager = get_session_security_manager()
        cleaned_count = session_manager.cleanup_expired_sessions()

        return jsonify({
            "message": f"Cleaned up {cleaned_count} expired sessions",
            "cleaned_count": cleaned_count
        })

    except Exception as e:
        current_app.logger.error(f"Error cleaning up expired sessions: {e}")
        return jsonify({"error": "Failed to cleanup sessions"}), 500

@session_mgmt_bp.route("/api/admin/user-activity/<int:user_id>", methods=["GET"])
@login_required
def get_user_activity(user_id):
    """Get user activity log for security monitoring."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        activity_type = request.args.get('type', '').strip()

        query = UserActivity.query.filter_by(user_id=user_id)

        if activity_type:
            query = query.filter(UserActivity.activity_type == activity_type)

        pagination = query.order_by(UserActivity.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        activities_data = []
        for activity in pagination.items:
            activities_data.append({
                'id': activity.id,
                'activity_type': activity.activity_type,
                'description': activity.description,
                'ip_address': activity.ip_address,
                'user_agent': activity.user_agent,
                'created_at': activity.created_at.isoformat() if activity.created_at else None
            })

        return jsonify({
            'activities': activities_data,
            'total': pagination.total,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching user activity for {user_id}: {e}")
        return jsonify({"error": "Failed to fetch user activity"}), 500

@session_mgmt_bp.route("/api/admin/session-stats", methods=["GET"])
@login_required
def get_session_stats():
    """Get session statistics for admin dashboard."""
    if not (current_user.is_admin_tier() or current_user.is_owner()):
        abort(403)

    try:
        from sqlalchemy import func

        # Get session statistics
        total_sessions = UserSession.query.count()
        active_sessions = UserSession.query.filter_by(is_active=True).count()
        expired_sessions = UserSession.query.filter(
            UserSession.is_active == False,
            UserSession.invalidated_at.isnot(None)
        ).count()

        # Get activity statistics
        total_activities = UserActivity.query.count()
        recent_activities = UserActivity.query.filter(
            UserActivity.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()

        # Get failed login attempts in last 24 hours
        failed_logins_24h = UserActivity.query.filter_by(
            activity_type="login_failed"
        ).filter(
            UserActivity.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()

        # Get successful logins in last 24 hours
        successful_logins_24h = UserActivity.query.filter_by(
            activity_type="login"
        ).filter(
            UserActivity.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()

        return jsonify({
            'sessions': {
                'total': total_sessions,
                'active': active_sessions,
                'expired': expired_sessions,
                'inactive': total_sessions - active_sessions - expired_sessions
            },
            'activities': {
                'total': total_activities,
                'recent_24h': recent_activities
            },
            'security': {
                'failed_logins_24h': failed_logins_24h,
                'successful_logins_24h': successful_logins_24h
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching session stats: {e}")
        return jsonify({"error": "Failed to fetch session statistics"}), 500
