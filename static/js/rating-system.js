/**
 * Rating System JavaScript
 * Handles rating functionality for news articles and albums
 */

class RatingSystem {
    constructor(contentType, contentId, options = {}) {
        this.contentType = contentType; // 'news' or 'album'
        this.contentId = contentId;
        this.options = {
            autoLoad: true,
            showDistribution: true,
            ...options
        };
        
        this.currentRating = null;
        this.ratingStats = null;
        this.isSubmitting = false; // Prevent duplicate submissions
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        if (this.options.autoLoad) {
            this.loadRatingStats();
        }
    }
    
    bindEvents() {
        // Create a unique identifier for this rating system instance
        const instanceId = `${this.contentType}-${this.contentId}`;
        
        // Star rating clicks - use more specific selectors
        document.addEventListener('click', (e) => {
            if (e.target.matches(`[data-rating-instance="${instanceId}"] .star-rating`)) {
                e.preventDefault();
                e.stopPropagation(); // Prevent event bubbling
                const rating = parseInt(e.target.dataset.rating);
                this.submitRating(rating);
            }
            
            if (e.target.matches(`[data-rating-instance="${instanceId}"] .star-rating-hover`)) {
                e.preventDefault();
                e.stopPropagation();
                const rating = parseInt(e.target.dataset.rating);
                this.highlightStars(rating);
            }
        });
        
        // Star rating hover effects - use more specific selectors
        document.addEventListener('mouseover', (e) => {
            if (e.target.matches(`[data-rating-instance="${instanceId}"] .star-rating`)) {
                const rating = parseInt(e.target.dataset.rating);
                this.highlightStars(rating);
            }
        });
        
        document.addEventListener('mouseout', (e) => {
            if (e.target.matches(`[data-rating-instance="${instanceId}"] .star-rating`)) {
                this.resetStarHighlight();
            }
        });
        
        // Remove rating - use more specific selectors
        document.addEventListener('click', (e) => {
            if (e.target.matches(`[data-rating-instance="${instanceId}"] .remove-rating-btn`)) {
                e.preventDefault();
                e.stopPropagation();
                this.removeRating();
            }
        });
    }
    
    async loadRatingStats() {
        try {
            let url = `/api/ratings/${this.contentType}/${this.contentId}`;
            
            // Use weighted endpoint for albums
            if (this.contentType === 'album') {
                url = `/api/ratings/album/${this.contentId}/weighted`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (response.ok) {
                this.ratingStats = data;
                this.currentRating = data.user_rating;
                this.renderRatingDisplay();
                this.updateStarRating();
                
                // Chapter breakdown is now handled in renderRatingDisplay()
                // No need to call renderChapterBreakdown here
            } else {
                console.error('Error loading rating stats:', data.error);
                this.showRatingError('Gagal memuat rating');
            }
        } catch (error) {
            console.error('Error loading rating stats:', error);
            this.showRatingError('Gagal memuat rating');
        }
    }
    
    showRatingError(message) {
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .rating-display`);
        if (!container) return;
        
        // Remove loading state
        const loadingElement = container.querySelector('.rating-loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        container.innerHTML = `
            <div class="rating-error text-center py-8">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 text-muted-foreground mx-auto mb-4">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <p class="text-muted-foreground">${message}</p>
                <button class="mt-4 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors" onclick="this.parentElement.parentElement.parentElement.querySelector('.rating-loading').style.display='flex'; this.parentElement.remove(); window.ratingSystem?.loadRatingStats();">
                    Coba Lagi
                </button>
            </div>
        `;
    }
    
    async submitRating(rating) {
        if (!window.currentUserId) {
            this.showError('Please log in to rate this content');
            return;
        }
        
        // Prevent duplicate submissions
        if (this.isSubmitting) {
            return;
        }
        
        this.isSubmitting = true;
        
        try {
            const response = await fetch('/api/ratings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    rating_value: rating,
                    content_type: this.contentType,
                    content_id: this.contentId
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                this.currentRating = rating;
                this.ratingStats = {
                    average_rating: data.average_rating,
                    rating_count: data.rating_count,
                    rating_distribution: data.rating_distribution,
                    user_rating: rating
                };
                this.renderRatingDisplay();
                this.updateStarRating();
            } else {
                this.showError(data.error || 'Failed to submit rating');
            }
        } catch (error) {
            console.error('Error submitting rating:', error);
            this.showError('Failed to submit rating');
        } finally {
            this.isSubmitting = false;
        }
    }
    
    async removeRating() {
        const proceed = await this.confirmModal('Hapus rating?', 'Tindakan ini akan menghapus rating Anda untuk konten ini.');
        if (!proceed) return;
        
        // Prevent duplicate submissions
        if (this.isSubmitting) {
            return;
        }
        
        this.isSubmitting = true;
        
        try {
            const response = await fetch(`/api/ratings/${this.contentType}/${this.contentId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess(data.message);
                this.currentRating = null;
                this.ratingStats = {
                    average_rating: data.average_rating,
                    rating_count: data.rating_count,
                    rating_distribution: data.rating_distribution,
                    user_rating: null
                };
                this.renderRatingDisplay();
                this.updateStarRating();
            } else {
                this.showError(data.error || 'Failed to remove rating');
            }
        } catch (error) {
            console.error('Error removing rating:', error);
            this.showError('Failed to remove rating');
        } finally {
            this.isSubmitting = false;
        }
    }

    confirmModal(title, message) {
        return new Promise((resolve) => {
            const modal = document.getElementById('confirmation-modal');
            const msgEl = document.getElementById('confirmation-message');
            const confirmBtn = document.getElementById('confirm-action');
            const cancelBtn = document.getElementById('cancel-confirmation');
            if (modal && msgEl && confirmBtn && cancelBtn) {
                msgEl.textContent = `${title} ${message ? '\n' + message : ''}`;
                modal.classList.remove('hidden');
                const cleanup = () => {
                    modal.classList.add('hidden');
                    confirmBtn.removeEventListener('click', onConfirm);
                    cancelBtn.removeEventListener('click', onCancel);
                };
                const onConfirm = () => { cleanup(); resolve(true); };
                const onCancel = () => { cleanup(); resolve(false); };
                confirmBtn.addEventListener('click', onConfirm, { once: true });
                cancelBtn.addEventListener('click', onCancel, { once: true });
            } else {
                // Fallback
                resolve(window.confirm(title));
            }
        });
    }
    
    renderRatingDisplay() {
        if (!this.ratingStats) return;
        
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .rating-display`);
        if (!container) return;
        
        // Remove loading state
        const loadingElement = container.querySelector('.rating-loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        const { average_rating, rating_count, rating_distribution } = this.ratingStats;
        

        
        let html = '';
        
        // Check if there are any ratings (count > 0)
        if (rating_count > 0) {
            // Show rating summary with actual data
            // Even if average_rating is 0.0, we still show it because there are ratings
            html = `
                <div class="rating-summary">
                    <div class="average-rating">
                        <span class="rating-value">${average_rating.toFixed(1)}</span>
                        <div class="star-display">
                            ${this.generateStars(average_rating)}
                        </div>
                    </div>
                    <div class="rating-count">
                        ${rating_count} rating${rating_count !== 1 ? 's' : ''}
                    </div>
                </div>
            `;
            
            // Show rating distribution if available
            if (rating_distribution && Object.values(rating_distribution).some(count => count > 0)) {
                html += this.renderRatingDistribution(rating_distribution, rating_count);
            }
            
            // Show chapter breakdown for albums if available
            if (this.contentType === 'album' && this.ratingStats.chapter_breakdown) {
                // Don't append the result since renderChapterBreakdown handles its own insertion
                this.renderChapterBreakdown(this.ratingStats.chapter_breakdown);
            }
        } else {
            // No ratings yet
            html = `
                <div class="no-ratings">
                    <div class="no-ratings-icon">⭐</div>
                    <div class="no-ratings-text">Belum ada rating</div>
                    <div class="no-ratings-subtext">Jadilah yang pertama memberikan rating!</div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    renderRatingDistribution(distribution, totalCount) {
        if (!distribution || totalCount === 0) return '';
        
        let html = '<div class="rating-distribution">';
        for (let i = 5; i >= 1; i--) {
            const count = distribution[i] || 0;
            const percentage = totalCount > 0 ? (count / totalCount) * 100 : 0;
            html += `
                <div class="rating-bar-row">
                    <span class="rating-label">${i}</span>
                    <div class="rating-bar">
                        <div class="rating-bar-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span class="rating-count">${count}</span>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }
    
    renderChapterBreakdown(chapterBreakdown) {
        if (!chapterBreakdown || chapterBreakdown.length === 0) return;
        
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .rating-display`);
        if (!container) return;
        
        let html = '<div class="chapter-breakdown mt-4">';
        html += '<h4 class="text-lg font-semibold mb-3">Chapter Ratings</h4>';
        html += '<div class="chapter-list">';
        
        chapterBreakdown.forEach(chapter => {
            // Ensure all values are defined and have fallbacks
            const chapterNumber = chapter.chapter_number || 'Unknown';
            const chapterTitle = chapter.chapter_title || 'Untitled';
            const rating = chapter.rating || 0;
            const ratingCount = chapter.rating_count || 0;
            const weight = chapter.weight || 1;
            
            const weightPercentage = ((weight - 1) * 100).toFixed(0);
            html += `
                <div class="chapter-item border rounded p-3 mb-2">
                    <div class="flex justify-between items-center">
                        <div>
                            <h5 class="font-medium">Chapter ${chapterNumber}: ${chapterTitle}</h5>
                            <div class="text-sm text-gray-600">
                                ${rating.toFixed(1)} ★ (${ratingCount} ratings)
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm text-gray-500">Weight: ${weight.toFixed(2)}x</div>
                            <div class="text-xs text-gray-400">+${weightPercentage}% popularity</div>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
        
        // Append to existing content
        container.insertAdjacentHTML('beforeend', html);
    }
    
    updateStarRating() {
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .star-rating-container`);
        if (!container) return;
        
        // Remove loading state
        const loadingElement = container.querySelector('.star-rating-loading');
        if (loadingElement) {
            loadingElement.remove();
        }
        
        const instanceId = `${this.contentType}-${this.contentId}`;
        
        let html = '<div class="star-rating-wrapper">';
        for (let i = 1; i <= 5; i++) {
            const isActive = this.currentRating && i <= this.currentRating;
            const starClass = isActive ? 'star-rating active' : 'star-rating';
            html += `
                <span class="${starClass}" 
                      data-rating="${i}" 
                      data-rating-instance="${instanceId}"
                      title="${i} star${i !== 1 ? 's' : ''}">
                    ★
                </span>
            `;
        }
        html += '</div>';
        
        if (this.currentRating) {
            html += `
                <button class="btn btn-sm btn-outline remove-rating-btn" 
                        data-rating-instance="${instanceId}"
                        style="margin-top: 0.5rem;">
                    Hapus Rating
                </button>
            `;
        } else {
            html += `
                <div class="text-center mt-4">
                    <p class="text-sm text-muted-foreground">Klik bintang untuk memberikan rating</p>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    highlightStars(rating) {
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .star-rating-wrapper`);
        if (!container) return;
        
        const stars = container.querySelectorAll('.star-rating');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('hover');
            } else {
                star.classList.remove('hover');
            }
        });
    }
    
    resetStarHighlight() {
        const container = document.querySelector(`[data-rating-instance="${this.contentType}-${this.contentId}"] .star-rating-wrapper`);
        if (!container) return;
        
        const stars = container.querySelectorAll('.star-rating');
        stars.forEach(star => {
            star.classList.remove('hover');
        });
    }
    
    generateStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        let html = '';
        
        for (let i = 1; i <= 5; i++) {
            if (i <= fullStars) {
                html += '<span class="star">★</span>';
            } else if (i === fullStars + 1 && hasHalfStar) {
                html += '<span class="star half">★</span>';
            } else {
                html += '<span class="star empty">☆</span>';
            }
        }
        
        return html;
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            // Fallback to alert if toast system is not available
            // Minimal fallback UI
            const containerId = 'toast-container';
            let container = document.getElementById(containerId);
            if (!container) {
                container = document.createElement('div');
                container.id = containerId;
                container.className = 'fixed top-5 right-5 space-y-2 z-50';
                document.body.appendChild(container);
            }
            const toast = document.createElement('div');
            toast.className = `${type === 'error' ? 'bg-red-600' : 'bg-green-600'} text-white px-4 py-2 rounded-lg shadow`;
            toast.textContent = (type === 'error' ? 'Error: ' : '') + message;
            container.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }
}

// Initialize rating system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Respect UI-only feature flag
    if (window.__UI_FLAGS__ && window.__UI_FLAGS__.enableRatings === false) {
        return; // Skip initializing any rating instances
    }
    // Find all rating instances on the page
    const ratingInstances = document.querySelectorAll('[data-rating-instance]');
    
    ratingInstances.forEach(instance => {
        const instanceId = instance.dataset.ratingInstance;
        const contentType = instance.dataset.contentType;
        const contentId = instance.dataset.contentId;
        
        if (contentType && contentId) {
            // Create unique variable name for each instance
            const varName = instanceId.replace(/[^a-zA-Z0-9]/g, '_');
            window[varName] = new RatingSystem(contentType, parseInt(contentId), {
                autoLoad: true,
                showDistribution: true
            });
            

        }
    });
    
    // Fallback for backward compatibility
    if (ratingInstances.length === 0) {
        const contentType = document.querySelector('[data-content-type]')?.dataset.contentType;
        const contentId = document.querySelector('[data-content-id]')?.dataset.contentId;
        
        if (contentType && contentId && !window.ratingSystem) {
            window.ratingSystem = new RatingSystem(contentType, parseInt(contentId));
        }
    }
});

// Global rating functions for use in templates
window.RatingSystem = {
    // Initialize rating system for a specific content
    init: function(contentType, contentId, options = {}) {
        return new RatingSystem(contentType, contentId, options);
    },
    
    // Submit rating from external call
    submitRating: function(contentType, contentId, rating) {
        const system = new RatingSystem(contentType, contentId, { autoLoad: false });
        return system.submitRating(rating);
    },
    
    // Load rating stats from external call
    loadStats: function(contentType, contentId) {
        const system = new RatingSystem(contentType, contentId, { autoLoad: false });
        return system.loadRatingStats();
    }
}; 