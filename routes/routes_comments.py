from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import db, Comment, CommentLike, CommentReport, News, Album, User, UserRole
from datetime import datetime, timezone, timedelta
import re

comments_bp = Blueprint('comments', __name__)


@comments_bp.route('/api/comments/<content_type>/<int:content_id>', methods=['GET'])
def get_comments(content_type, content_id):
    """Get comments for a specific content (news or album)."""
    try:
        # Validate content type
        if content_type not in ['news', 'album']:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Check if content exists
        if content_type == 'news':
            content = News.query.get(content_id)
        else:
            content = Album.query.get(content_id)
        
        if not content:
            return jsonify({'error': 'Content not found'}), 404
        
        # Get comments with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get approved, non-deleted comments
        comments_query = Comment.query.filter_by(
            content_type=content_type,
            content_id=content_id,
            is_approved=True,
            is_deleted=False,
            parent_id=None  # Only top-level comments
        ).order_by(Comment.created_at.desc())
        
        comments_pagination = comments_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        comments_data = []
        for comment in comments_pagination.items:
            comment_dict = comment.to_dict()
            
            # Add user's like/dislike status if user is logged in
            if current_user.is_authenticated:
                comment_dict['user_liked'] = comment.is_liked_by_user(current_user.id)
                comment_dict['user_disliked'] = comment.is_disliked_by_user(current_user.id)
            
            # Get replies for this comment
            replies = Comment.query.filter_by(
                parent_id=comment.id,
                is_approved=True,
                is_deleted=False
            ).order_by(Comment.created_at.asc()).all()
            
            replies_data = []
            for reply in replies:
                reply_dict = reply.to_dict()
                if current_user.is_authenticated:
                    reply_dict['user_liked'] = reply.is_liked_by_user(current_user.id)
                    reply_dict['user_disliked'] = reply.is_disliked_by_user(current_user.id)
                replies_data.append(reply_dict)
            
            comment_dict['replies'] = replies_data
            comments_data.append(comment_dict)
        
        return jsonify({
            'comments': comments_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': comments_pagination.total,
                'pages': comments_pagination.pages,
                'has_next': comments_pagination.has_next,
                'has_prev': comments_pagination.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.exception("Error getting comments")
        return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


@comments_bp.route('/api/comments', methods=['POST'])
@login_required
def create_comment():
    """Create a new comment."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        content_type = data.get('content_type')
        content_id = data.get('content_id')
        parent_id = data.get('parent_id')
        
        # Validation
        if not content:
            return jsonify({'error': 'Comment content is required'}), 400
        
        if len(content) > 5000:
            return jsonify({'error': 'Comment content cannot exceed 5000 characters'}), 400
        
        if content_type not in ['news', 'album']:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Check if content exists
        if content_type == 'news':
            content_obj = News.query.get(content_id)
        else:
            content_obj = Album.query.get(content_id)
        
        if not content_obj:
            return jsonify({'error': 'Content not found'}), 404
        
        # Check if user is suspended
        if current_user.is_suspended:
            return jsonify({'error': 'Your account is suspended'}), 403
        
        # Check for spam (simple implementation)
        if is_spam_comment(content, current_user.id):
            return jsonify({'error': 'Comment detected as spam'}), 400
        
        # Create comment
        comment = Comment(
            content=content,
            content_type=content_type,
            content_id=content_id,
            user_id=current_user.id,
            parent_id=parent_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        # Validate comment
        comment.validate()
        
        # Auto-approve for trusted users, otherwise require moderation
        if current_user.role.value in ['admin', 'su'] or current_user.verified:
            comment.is_approved = True
        else:
            comment.is_approved = False  # Requires moderation
        
        db.session.add(comment)
        db.session.commit()
        
        # Record user activity (with safety check)
        try:
            if hasattr(current_user, 'record_activity'):
                current_user.record_activity(
                    'create_comment',
                    f'Created comment on {content_type} {content_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent')
                )
        except Exception as e:
            current_app.logger.warning(f"Could not record user activity: {str(e)}")
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment.to_dict(),
            'requires_moderation': not comment.is_approved
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/api/comments/<int:comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    """Update a comment."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        
        # Check if user can edit this comment
        if comment.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        
        # Validation
        if not content:
            return jsonify({'error': 'Comment content is required'}), 400
        
        if len(content) > 5000:
            return jsonify({'error': 'Comment content cannot exceed 5000 characters'}), 400
        
        # Update comment
        comment.content = content
        comment.updated_at = datetime.now(timezone.utc)
        
        # Re-validate for moderation if needed
        if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            comment.is_approved = False  # Requires re-approval
        
        db.session.commit()
        
        # Record user activity (with safety check)
        try:
            if hasattr(current_user, 'record_activity'):
                current_user.record_activity(
                    'update_comment',
                    f'Updated comment {comment_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent')
                )
        except Exception as e:
            current_app.logger.warning(f"Could not record user activity: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Comment updated successfully',
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    """Delete a comment (soft delete)."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        
        # Check if user can delete this comment
        if comment.user_id != current_user.id and current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            return jsonify({'error': 'Permission denied'}), 403
        
        # Soft delete
        comment.is_deleted = True
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        # Record user activity (with safety check)
        try:
            if hasattr(current_user, 'record_activity'):
                current_user.record_activity(
                    'delete_comment',
                    f'Deleted comment {comment_id}',
                    request.remote_addr,
                    request.headers.get('User-Agent')
                )
        except Exception as e:
            current_app.logger.warning(f"Could not record user activity: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Comment deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    """Like or unlike a comment."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        
        if comment.is_deleted:
            return jsonify({'error': 'Comment not found'}), 404
        
        data = request.get_json()
        is_like = data.get('is_like', True)  # True for like, False for dislike
        
        # Check if user already liked/disliked this comment
        existing_like = CommentLike.query.filter_by(
            comment_id=comment_id,
            user_id=current_user.id
        ).first()
        
        if existing_like:
            if existing_like.is_like == is_like:
                # Remove like/dislike
                existing_like.is_deleted = True
                action = 'removed'
            else:
                # Change like/dislike
                existing_like.is_like = is_like
                existing_like.is_deleted = False
                action = 'changed'
        else:
            # Create new like/dislike
            existing_like = CommentLike(
                comment_id=comment_id,
                user_id=current_user.id,
                is_like=is_like
            )
            db.session.add(existing_like)
            action = 'added'
        
        db.session.commit()
        
        return jsonify({
            'message': f'{action.title()} {"like" if is_like else "dislike"} successfully',
            'likes_count': comment.get_likes_count(),
            'dislikes_count': comment.get_dislikes_count(),
            'user_liked': comment.is_liked_by_user(current_user.id),
            'user_disliked': comment.is_disliked_by_user(current_user.id)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error liking comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/api/comments/<int:comment_id>/report', methods=['POST'])
@login_required
def report_comment(comment_id):
    """Report a comment."""
    try:
        comment = Comment.query.get_or_404(comment_id)
        
        if comment.is_deleted:
            return jsonify({'error': 'Comment not found'}), 404
        
        if comment.user_id == current_user.id:
            return jsonify({'error': 'Cannot report your own comment'}), 400
        
        data = request.get_json()
        reason = data.get('reason')
        description = data.get('description', '').strip()
        
        # Validation
        valid_reasons = ['spam', 'inappropriate', 'harassment', 'offensive', 'other']
        if reason not in valid_reasons:
            return jsonify({'error': f'Invalid reason. Must be one of: {", ".join(valid_reasons)}'}), 400
        
        # Check if user already reported this comment
        existing_report = CommentReport.query.filter_by(
            comment_id=comment_id,
            user_id=current_user.id,
            is_resolved=False
        ).first()
        
        if existing_report:
            return jsonify({'error': 'You have already reported this comment'}), 400
        
        # Create report
        report = CommentReport(
            comment_id=comment_id,
            user_id=current_user.id,
            reason=reason,
            description=description
        )
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({'message': 'Comment reported successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reporting comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Admin routes for comment moderation
@comments_bp.route('/admin/comments')
@login_required
def admin_comments():
    """Admin interface for comment moderation."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        flash('Permission denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get comments with filters
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')  # all, pending, approved, rejected, spam
    content_type = request.args.get('content_type', '')
    
    query = Comment.query
    
    # Apply filters
    if status == 'all':
        query = query.filter_by(is_deleted=False)
    elif status == 'pending':
        query = query.filter_by(is_approved=False, is_spam=False, is_deleted=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True, is_deleted=False)
    elif status == 'rejected':
        query = query.filter_by(is_approved=False, is_deleted=False)
    elif status == 'spam':
        query = query.filter_by(is_spam=True, is_deleted=False)
    
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    # Order by creation date
    query = query.order_by(Comment.created_at.desc())
    
    # Pagination
    comments = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        'admin/settings/comment_moderation.html',
        comments=comments,
        status=status,
        content_type=content_type
    )


@comments_bp.route('/admin/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def approve_comment(comment_id):
    """Approve a comment."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.is_approved = True
        comment.is_spam = False
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'message': 'Comment approved successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/admin/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
def reject_comment(comment_id):
    """Reject a comment."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.is_approved = False
        comment.is_spam = False
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'message': 'Comment rejected successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/admin/comments/<int:comment_id>/mark-spam', methods=['POST'])
@login_required
def mark_comment_spam(comment_id):
    """Mark a comment as spam."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.is_spam = True
        comment.is_approved = False
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'message': 'Comment marked as spam successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking comment as spam: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@comments_bp.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def admin_delete_comment(comment_id):
    """Admin delete a comment."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.is_deleted = True
        comment.updated_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({'message': 'Comment deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting comment: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Helper functions
def is_spam_comment(content, user_id):
    """Simple spam detection for comments."""
    # Check for excessive links
    link_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content))
    if link_count > 3:
        return True
    
    # Check for excessive caps
    if len(content) > 10:
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
        if caps_ratio > 0.7:
            return True
    
    # Check for repetitive characters
    if len(content) > 5:
        for char in content:
            if content.count(char) > len(content) * 0.5:
                return True
    
    # Check user's recent comment history
    recent_comments = Comment.query.filter_by(
        user_id=user_id
    ).filter(
        Comment.created_at >= datetime.now(timezone.utc) - timedelta(hours=1)
    ).count()
    
    if recent_comments > 10:
        return True
    
    return False 