/**
 * Premium Content Management
 * Handles premium content display, masking, and user interactions
 */

class PremiumContentManager {
    constructor() {
        this.isPremiumUser = window.currentUserId && window.currentUserRole;
        this.init();
    }

    init() {
        this.setupPremiumContentHandlers();
        this.setupContentMaskInteractions();
        this.setupPremiumStats();
    }

    setupPremiumContentHandlers() {
        // Handle premium content containers
        const premiumContainers = document.querySelectorAll('.premium-content-container');
        premiumContainers.forEach(container => {
            if (container.classList.contains('truncated')) {
                this.setupTruncatedContent(container);
            }
        });
    }

    setupTruncatedContent(container) {
        // Add fade effect to truncated content
        const content = container.querySelector('#article-body');
        if (content) {
            content.style.position = 'relative';
            content.style.overflow = 'hidden';
        }
    }

    setupContentMaskInteractions() {
        // Handle content mask interactions
        const contentMasks = document.querySelectorAll('.content-mask-overlay');
        contentMasks.forEach(mask => {
            this.setupMaskInteractions(mask);
        });
    }

    setupMaskInteractions(mask) {
        // Add click handlers for mask buttons
        const buttons = mask.querySelectorAll('.button');
        buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.handlePremiumButtonClick(button);
            });
        });

        // Add hover effects
        mask.addEventListener('mouseenter', () => {
            mask.style.transform = 'scale(1.02)';
        });

        mask.addEventListener('mouseleave', () => {
            mask.style.transform = 'scale(1)';
        });
    }

    handlePremiumButtonClick(button) {
        const action = button.textContent.trim();
        
        if (action.includes('Berlangganan')) {
            // Redirect to premium page
            window.location.href = '/premium';
        } else if (action.includes('Login')) {
            // Redirect to login page
            window.location.href = '/login';
        }
    }

    setupPremiumStats() {
        // Animate premium stats
        const stats = document.querySelectorAll('.premium-content-stats .stat');
        stats.forEach((stat, index) => {
            setTimeout(() => {
                stat.style.opacity = '0';
                stat.style.transform = 'translateY(10px)';
                stat.style.transition = 'all 0.3s ease';
                
                setTimeout(() => {
                    stat.style.opacity = '1';
                    stat.style.transform = 'translateY(0)';
                }, 100);
            }, index * 100);
        });
    }

    // Method to reveal premium content (for testing or admin use)
    revealPremiumContent(contentId) {
        const container = document.querySelector(`#content-mask-${contentId}`);
        if (container) {
            container.style.display = 'none';
            
            // Remove truncated class from parent
            const contentContainer = container.closest('.premium-content-container');
            if (contentContainer) {
                contentContainer.classList.remove('truncated');
            }
        }
    }

    // Method to check if content is premium
    isContentPremium(contentId) {
        const container = document.querySelector(`#content-mask-${contentId}`);
        return container !== null;
    }

    // Method to get premium content statistics
    getPremiumContentStats() {
        const stats = {
            totalPremiumContent: document.querySelectorAll('.content-mask-overlay').length,
            totalTruncatedContent: document.querySelectorAll('.premium-content-container.truncated').length,
            userHasPremium: this.isPremiumUser
        };
        return stats;
    }
}

// Initialize premium content manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize premium content manager
    window.premiumContentManager = new PremiumContentManager();
    
    // Add global methods for external access
    window.revealPremiumContent = (contentId) => {
        if (window.premiumContentManager) {
            window.premiumContentManager.revealPremiumContent(contentId);
        }
    };
    
    window.isContentPremium = (contentId) => {
        if (window.premiumContentManager) {
            return window.premiumContentManager.isContentPremium(contentId);
        }
        return false;
    };
    
    window.getPremiumContentStats = () => {
        if (window.premiumContentManager) {
            return window.premiumContentManager.getPremiumContentStats();
        }
        return {};
    };
});

// Utility functions for premium content
const PremiumContentUtils = {
    // Check if user has premium access
    hasPremiumAccess: function() {
        return window.currentUserId && window.currentUserRole;
    },

    // Format premium content stats
    formatStats: function(stats) {
        return {
            totalWords: stats.total_words || 0,
            totalChars: stats.total_chars || 0,
            isPremium: stats.is_premium || false,
            userHasAccess: stats.user_has_access || false
        };
    },

    // Create premium notice element
    createPremiumNotice: function(contentType = 'artikel') {
        const notice = document.createElement('div');
        notice.className = 'premium-content-notice';
        notice.innerHTML = `
            <div class="flex items-center gap-3 mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-6 h-6 text-primary">
                    <path fill-rule="evenodd" d="M5.166 2.621v.858c-1.035.148-2.059.33-3.071.543a.75.75 0 00-.584.859 6.937 6.937 0 006.222 6.222.75.75 0 00.859-.584 48.332 48.332 0 001.243-5.034 48.332 48.332 0 005.034-1.243.75.75 0 00.584-.859 6.937 6.937 0 00-6.222-6.222.75.75 0 00-.859.584 48.332 48.332 0 00-1.243 5.034zM13.5 2.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM13.5 6.75a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V7.5a.75.75 0 01.75-.75zM13.5 11.25a.75.75 0 01.75.75v.75a.75.75 0 01-1.5 0V12a.75.75 0 01.75-.75z" clip-rule="evenodd" />
                </svg>
                <h3 class="text-lg font-semibold text-foreground">Konten Premium</h3>
            </div>
            <p class="text-muted-foreground mb-4">Untuk membaca ${contentType} ini secara lengkap, Anda memerlukan langganan premium.</p>
            <div class="flex flex-wrap gap-3">
                <a href="/premium" class="button button-primary">
                    Berlangganan Premium
                </a>
                <a href="/login" class="button button-outline">
                    Login
                </a>
            </div>
        `;
        return notice;
    },

    // Show premium content notice
    showPremiumNotice: function(container, contentType = 'artikel') {
        const notice = this.createPremiumNotice(contentType);
        container.appendChild(notice);
    },

    // Hide premium content notice
    hidePremiumNotice: function(container) {
        const notice = container.querySelector('.premium-content-notice');
        if (notice) {
            notice.remove();
        }
    }
};

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PremiumContentManager, PremiumContentUtils };
} 