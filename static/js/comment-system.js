/**
 * Comment System JavaScript
 * Handles comment functionality for news articles and albums
 */

class CommentSystem {
    constructor(contentType, contentId, options = {}) {
        this.contentType = contentType; // 'news' or 'album'
        this.contentId = contentId;
        this.options = {
            autoLoad: true,
            perPage: 12, // Load 12 comments by default
            autoLoadMore: true, // Enable auto-loading
            loadMoreThreshold: 0.8, // Load more when user scrolls to 80% of container
            ...options
        };
        
        this.currentPage = 1;
        this.comments = [];
        this.allComments = []; // Store all loaded comments
        this.isLoading = false;
        this.isSubmitting = false; // Prevent duplicate submissions
        this.hasMoreComments = true;
        this.autoLoadObserver = null;
        this.eventListenerBound = false; // Track if event listener is already bound
        this.boundEventListeners = []; // Track all bound event listeners for cleanup
        
        this.init();
    }
    
    init() {
        // Prevent multiple CommentSystem instances
        if (window.commentSystem && window.commentSystem !== this) {
            console.warn('CommentSystem already initialized, destroying previous instance');
            window.commentSystem.destroy();
        }
        
        this.bindEvents();
        if (this.options.autoLoad) {
            this.loadComments();
        }
    }
    
    bindEvents() {
        // Only bind events once per instance
        if (this.eventListenerBound) {
            return;
        }
        
        // Prevent form submission events
        const commentForms = document.querySelectorAll('.comment-form');
        commentForms.forEach(form => {
            const submitHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
            };
            form.addEventListener('submit', submitHandler);
            this.boundEventListeners.push({ element: form, type: 'submit', handler: submitHandler });
        });
        
        // Bind events to document but with specific targeting
        const documentClickHandler = (e) => {
            // Only handle events for this specific content type and ID
            const targetContentType = this.contentType;
            const targetContentId = this.contentId;
            
            if (e.target.matches('.comment-submit-btn')) {
                e.preventDefault();
                e.stopPropagation();
                
                // Check if this button belongs to the correct content
                const form = e.target.closest('.comment-form');
                if (form) {
                    this.submitComment(form);
                }
            }
            
            if (e.target.matches('.comment-edit-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.editComment(e.target.dataset.commentId);
            }
            
            if (e.target.matches('.comment-delete-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.deleteComment(e.target.dataset.commentId);
            }
            
            if (e.target.matches('.comment-like-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.likeComment(e.target.dataset.commentId, true);
            }
            
            if (e.target.matches('.comment-dislike-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.likeComment(e.target.dataset.commentId, false);
            }
            
            if (e.target.matches('.comment-reply-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.showReplyForm(e.target.dataset.commentId);
            }
            
            if (e.target.matches('.comment-report-btn')) {
                e.preventDefault();
                e.stopPropagation();
                this.showReportForm(e.target.dataset.commentId);
            }
        };
        
        document.addEventListener('click', documentClickHandler);
        this.boundEventListeners.push({ element: document, type: 'click', handler: documentClickHandler });
        
        this.eventListenerBound = true;
        
        // Auto-load more comments on scroll
        if (this.options.autoLoadMore) {
            this.setupAutoLoad();
        }
    }
    
    destroy() {
        // Clean up event listeners and observers
        if (this.autoLoadObserver) {
            this.autoLoadObserver.disconnect();
            this.autoLoadObserver = null;
        }
        
        // Clean up all bound event listeners
        this.boundEventListeners.forEach(({ element, type, handler }) => {
            element.removeEventListener(type, handler);
        });
        this.boundEventListeners = [];
        
        this.eventListenerBound = false;
    }
    
    setupAutoLoad() {
        const container = document.querySelector('.comments-container');
        if (!container) return;
        
        // Create intersection observer for auto-loading
        this.autoLoadObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && this.hasMoreComments && !this.isLoading) {
                    this.loadMoreComments();
                }
            });
        }, {
            root: container,
            rootMargin: '0px',
            threshold: this.options.loadMoreThreshold
        });
        
        // Observe the last comment for auto-loading trigger
        this.observeLastComment();
    }
    
    observeLastComment() {
        const container = document.querySelector('.comments-container');
        if (!container) return;
        
        const comments = container.querySelectorAll('.comment-item');
        if (comments.length > 0) {
            const lastComment = comments[comments.length - 1];
            if (this.autoLoadObserver) {
                this.autoLoadObserver.observe(lastComment);
            }
        }
    }
    
    async loadComments(page = 1) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        try {
            const response = await fetch(`/api/comments/${this.contentType}/${this.contentId}?page=${page}&per_page=${this.options.perPage}`);
            const data = await response.json();
            
            if (response.ok) {
                if (page === 1) {
                    // First load - store all comments and show initial amount
                    this.allComments = data.comments;
                    this.comments = this.allComments.slice(0, this.options.perPage); // Show initial 12
                    this.hasMoreComments = this.allComments.length > this.options.perPage;
                } else {
                    // Load more - append to existing comments
                    this.allComments = [...this.allComments, ...data.comments];
                    this.comments = this.allComments.slice(0, this.options.perPage); // Show initial 12
                    this.hasMoreComments = data.comments.length === this.options.perPage;
                }
                
                this.currentPage = page;
                this.renderComments();
                
                // Setup auto-load observer for new comments
                if (this.options.autoLoadMore) {
                    this.observeLastComment();
                }
            } else {
                this.showError(data.error || 'Failed to load comments');
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            this.showError('Failed to load comments');
        } finally {
            this.hideLoading();
            this.isLoading = false;
        }
    }
    
    async submitComment(form) {
        const content = form.querySelector('.comment-content').value.trim();
        const parentId = form.dataset.parentId || null;
        
        if (!content) {
            this.showError('Comment content is required');
            return;
        }
        
        if (content.length > 5000) {
            this.showError('Comment content cannot exceed 5000 characters');
            return;
        }
        
        // Prevent duplicate submissions
        if (this.isSubmitting) {
            return;
        }
        
        this.isSubmitting = true;
        
        const submitBtn = form.querySelector('.comment-submit-btn');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Posting...';
        
        try {
            const response = await fetch('/api/comments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    content: content,
                    content_type: this.contentType,
                    content_id: this.contentId,
                    parent_id: parentId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                form.reset();
                
                // Reload comments to show the new comment
                this.loadComments(1);
                
                // If it's a reply, hide the reply form
                if (parentId) {
                    this.hideReplyForm(parentId);
                }
            } else {
                this.showError(data.error || 'Failed to post comment');
            }
        } catch (error) {
            console.error('Error posting comment:', error);
            this.showError('Failed to post comment');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            this.isSubmitting = false;
        }
    }
    
    async editComment(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const contentElement = commentElement.querySelector('.comment-content-display');
        const content = contentElement.textContent.trim();
        
        // Create edit form
        const editForm = document.createElement('div');
        editForm.className = 'comment-edit-form';
        editForm.innerHTML = `
            <textarea class="form-control comment-content-edit" rows="3">${content}</textarea>
            <div class="mt-2">
                <button class="btn btn-sm btn-primary comment-save-edit" data-comment-id="${commentId}">Save</button>
                <button class="btn btn-sm btn-secondary comment-cancel-edit" data-comment-id="${commentId}">Cancel</button>
            </div>
        `;
        
        // Replace content with edit form
        contentElement.style.display = 'none';
        contentElement.parentNode.insertBefore(editForm, contentElement.nextSibling);
        
        // Bind save and cancel events
        editForm.querySelector('.comment-save-edit').addEventListener('click', () => {
            this.saveEditComment(commentId, editForm.querySelector('.comment-content-edit').value);
        });
        
        editForm.querySelector('.comment-cancel-edit').addEventListener('click', () => {
            this.cancelEditComment(commentId);
        });
    }
    
    async saveEditComment(commentId, content) {
        if (!content.trim()) {
            this.showError('Comment content is required');
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    content: content
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                this.loadComments(this.currentPage);
            } else {
                this.showError(data.error || 'Failed to update comment');
            }
        } catch (error) {
            console.error('Error updating comment:', error);
            this.showError('Failed to update comment');
        }
    }
    
    cancelEditComment(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const contentElement = commentElement.querySelector('.comment-content-display');
        const editForm = commentElement.querySelector('.comment-edit-form');
        
        contentElement.style.display = 'block';
        editForm.remove();
    }
    
    async deleteComment(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/${commentId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                this.loadComments(this.currentPage);
            } else {
                this.showError(data.error || 'Failed to delete comment');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            this.showError('Failed to delete comment');
        }
    }
    
    async likeComment(commentId, isLike) {
        try {
            const response = await fetch(`/api/comments/${commentId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    is_like: isLike
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.updateCommentLikes(commentId, data);
            } else {
                this.showError(data.error || 'Failed to update like');
            }
        } catch (error) {
            console.error('Error liking comment:', error);
            this.showError('Failed to update like');
        }
    }
    
    updateCommentLikes(commentId, data) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        // Update like/dislike counts
        const likeCount = commentElement.querySelector('.comment-likes-count');
        const dislikeCount = commentElement.querySelector('.comment-dislikes-count');
        
        if (likeCount) likeCount.textContent = data.likes_count;
        if (dislikeCount) dislikeCount.textContent = data.dislikes_count;
        
        // Update button states
        const likeBtn = commentElement.querySelector('.comment-like-btn');
        const dislikeBtn = commentElement.querySelector('.comment-dislike-btn');
        
        if (likeBtn) {
            likeBtn.classList.toggle('active', data.user_liked);
        }
        if (dislikeBtn) {
            dislikeBtn.classList.toggle('active', data.user_disliked);
        }
    }
    
    showReplyForm(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const existingForm = commentElement.querySelector('.comment-reply-form');
        
        if (existingForm) {
            existingForm.remove();
            return;
        }
        
        const replyForm = document.createElement('div');
        replyForm.className = 'comment-reply-form mt-3';
        replyForm.innerHTML = `
            <form class="comment-form" data-parent-id="${commentId}">
                <div class="form-group">
                    <textarea class="form-control comment-content" rows="2" placeholder="Write a reply..."></textarea>
                </div>
                <div class="mt-2">
                    <button type="submit" class="btn btn-sm btn-primary comment-submit-btn">Reply</button>
                    <button type="button" class="btn btn-sm btn-secondary comment-cancel-reply">Cancel</button>
                </div>
            </form>
        `;
        
        commentElement.appendChild(replyForm);
        
        // Bind cancel event
        replyForm.querySelector('.comment-cancel-reply').addEventListener('click', () => {
            replyForm.remove();
        });
    }
    
    hideReplyForm(commentId) {
        const commentElement = document.querySelector(`[data-comment-id="${commentId}"]`);
        if (!commentElement) return;
        
        const replyForm = commentElement.querySelector('.comment-reply-form');
        if (replyForm) {
            replyForm.remove();
        }
    }
    
    showReportForm(commentId) {
        const reason = prompt('Report reason (spam, inappropriate, harassment, offensive, other):');
        if (!reason) return;
        
        const description = prompt('Additional details (optional):');
        
        this.submitReport(commentId, reason, description);
    }
    
    async submitReport(commentId, reason, description) {
        try {
            const response = await fetch(`/api/comments/${commentId}/report`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    reason: reason,
                    description: description || ''
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
            } else {
                this.showError(data.error || 'Failed to report comment');
            }
        } catch (error) {
            console.error('Error reporting comment:', error);
            this.showError('Failed to report comment');
        }
    }
    
    renderComments() {
        const container = document.querySelector('.comments-container');
        if (!container) return;
        
        if (this.comments.length === 0) {
            container.innerHTML = `
                <div class="no-comments">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                    </svg>
                    <p>Belum ada komentar. Jadilah yang pertama berkomentar!</p>
                </div>
            `;
            return;
        }
        
        const commentsHtml = this.comments.map(comment => this.renderComment(comment)).join('');
        
        // Add auto-loading indicator if there are more comments
        let loadingIndicator = '';
        if (this.hasMoreComments) {
            loadingIndicator = `
                <div class="auto-load-indicator" style="display: none;">
                    <div class="comments-loading-more">
                        <div class="spinner"></div>
                        <span>Memuat komentar...</span>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = commentsHtml + loadingIndicator;
        
        // Setup auto-load observer for new comments
        if (this.options.autoLoadMore) {
            this.observeLastComment();
        }
    }
    
    renderComment(comment) {
        const canEdit = comment.user_id === window.currentUserId;
        const canDelete = comment.user_id === window.currentUserId || window.currentUserRole === 'admin';
        
        return `
            <div class="comment-item mb-3" data-comment-id="${comment.id}">
                <div class="d-flex">
                    <div class="flex-shrink-0">
                        <div class="comment-avatar">
                            ${comment.user ? comment.user.first_name ? comment.user.first_name.charAt(0).toUpperCase() : 'U' : 'U'}
                        </div>
                    </div>
                    <div class="flex-grow-1 ms-3">
                        <div class="comment-header">
                            <strong class="comment-author">${comment.user ? (comment.user.first_name || comment.user.username) : 'Anonymous'}</strong>
                            <small class="text-muted comment-date">${this.formatDate(comment.created_at)}</small>
                        </div>
                        <div class="comment-content-display">${this.escapeHtml(comment.content)}</div>
                        <div class="comment-actions mt-2">
                            <button class="btn btn-sm btn-link comment-like-btn ${comment.user_liked ? 'active' : ''}" data-comment-id="${comment.id}">
                                👍 <span class="comment-likes-count">${comment.likes_count}</span>
                            </button>
                            <button class="btn btn-sm btn-link comment-dislike-btn ${comment.user_disliked ? 'active' : ''}" data-comment-id="${comment.id}">
                                👎 <span class="comment-dislikes-count">${comment.dislikes_count}</span>
                            </button>
                            <button class="btn btn-sm btn-link comment-reply-btn" data-comment-id="${comment.id}">Reply</button>
                            ${canEdit ? `<button class="btn btn-sm btn-link comment-edit-btn" data-comment-id="${comment.id}">Edit</button>` : ''}
                            ${canDelete ? `<button class="btn btn-sm btn-link text-danger comment-delete-btn" data-comment-id="${comment.id}">Delete</button>` : ''}
                            ${comment.user_id !== window.currentUserId ? `<button class="btn btn-sm btn-link comment-report-btn" data-comment-id="${comment.id}">Report</button>` : ''}
                        </div>
                        ${comment.replies && comment.replies.length > 0 ? this.renderReplies(comment.replies) : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    renderReplies(replies) {
        return `
            <div class="comment-replies mt-3">
                ${replies.map(reply => this.renderComment(reply)).join('')}
            </div>
        `;
    }
    
    updatePagination(pagination) {
        const paginationContainer = document.querySelector('.comments-pagination');
        if (!paginationContainer) return;
        
        if (pagination.pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }
        
        let paginationHtml = '<ul class="pagination pagination-sm">';
        
        if (pagination.has_prev) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.page - 1}">Previous</a></li>`;
        }
        
        for (let i = 1; i <= pagination.pages; i++) {
            const active = i === pagination.page ? 'active' : '';
            paginationHtml += `<li class="page-item ${active}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }
        
        if (pagination.has_next) {
            paginationHtml += `<li class="page-item"><a class="page-link" href="#" data-page="${pagination.page + 1}">Next</a></li>`;
        }
        
        paginationHtml += '</ul>';
        paginationContainer.innerHTML = paginationHtml;
        
        // Bind pagination events
        paginationContainer.addEventListener('click', (e) => {
            if (e.target.matches('.page-link')) {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                this.loadComments(page);
            }
        });
    }
    
    loadMoreComments() {
        if (this.isLoading || !this.hasMoreComments) return;
        
        this.isLoading = true;
        this.showLoadMoreLoading();
        
        // Load more comments from server
        this.loadComments(this.currentPage + 1);
    }
    
    showLoading() {
        const container = document.querySelector('.comments-container');
        if (container) {
            container.innerHTML = `
                <div class="comments-loading">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Memuat komentar...</p>
                </div>
            `;
        }
    }
    
    hideLoading() {
        // Loading is hidden when comments are rendered
    }
    
    showLoadMoreLoading() {
        const indicator = document.querySelector('.auto-load-indicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }
    
    hideLoadMoreLoading() {
        const indicator = document.querySelector('.auto-load-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        const container = document.querySelector('.comments-section') || document.body;
        container.insertBefore(notification, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize comment system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Respect UI-only feature flag
    if (window.__UI_FLAGS__ && window.__UI_FLAGS__.enableComments === false) {
        return; // Skip initializing the comment system
    }
    // Check if we're on a news or album page
    const contentType = document.querySelector('[data-content-type]')?.dataset.contentType;
    const contentId = document.querySelector('[data-content-id]')?.dataset.contentId;
    
    if (contentType && contentId) {
        window.commentSystem = new CommentSystem(contentType, parseInt(contentId));
    }
}); 