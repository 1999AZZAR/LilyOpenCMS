// Settings Management Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('settings-search');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const managementCards = document.querySelectorAll('.tab-content a');
    const resultsTabBtn = document.getElementById('results-tab-btn');
    const searchResultsContainer = document.getElementById('search-results-container');
    
    // Store original card templates for search results
    const originalCards = Array.from(managementCards).map(card => {
        const title = card.querySelector('h3')?.textContent || '';
        const description = card.querySelector('p')?.textContent || '';
        const icon = card.querySelector('i')?.className || '';
        const href = card.getAttribute('href');
        
        return {
            element: card.cloneNode(true),
            text: card.textContent.toLowerCase(),
            url: href.toLowerCase(),
            title: title,
            description: description,
            icon: icon,
            href: href
        };
    });
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            
            if (searchTerm === '') {
                // Reset to normal state immediately
                resetToNormalState();
                return;
            }
            
            // Perform search and show results
            performSearch(searchTerm);
        });
        
        // Also handle the 'search' event for better compatibility
        searchInput.addEventListener('search', function() {
            if (this.value === '') {
                resetToNormalState();
            }
        });
        
        // Clear search when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !e.target.closest('.tab-btn')) {
                searchInput.value = '';
                resetToNormalState();
            }
        });
        
        // Keyboard shortcuts
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                resetToNormalState();
                this.blur();
            }
        });
    }
    
    function resetToNormalState() {
        // Hide results tab
        resultsTabBtn.classList.add('hidden');
        resultsTabBtn.classList.remove('active', 'border-blue-500');
        
        // Show all regular tabs and reset their states
        tabButtons.forEach(btn => {
            if (btn !== resultsTabBtn) {
                btn.style.display = 'block';
                btn.classList.remove('opacity-50');
            }
        });
        
        // Reset all tab contents - hide everything first
        tabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        // Reset all cards to their original state
        managementCards.forEach(card => {
            card.style.display = 'block';
            // Restore original card content
            const originalCard = originalCards.find(oc => oc.href === card.getAttribute('href'));
            if (originalCard) {
                card.innerHTML = originalCard.element.innerHTML;
            }
        });
        
        // Clear search results
        searchResultsContainer.innerHTML = '';
        
        // Force a reflow to ensure proper rendering
        document.body.offsetHeight;
    }
    
    function performSearch(searchTerm) {
        // Hide all regular tabs
        tabButtons.forEach(btn => {
            if (btn !== resultsTabBtn) {
                btn.style.display = 'none';
            }
        });
        
        // Hide all tab contents
        tabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        // Show results tab
        resultsTabBtn.classList.remove('hidden');
        resultsTabBtn.style.display = 'block';
        resultsTabBtn.classList.add('active', 'border-amber-500');
        
        // Show results content
        const resultsContent = document.getElementById('results-tab');
        resultsContent.classList.add('active');
        resultsContent.style.display = 'block';
        
        // Clear previous results
        searchResultsContainer.innerHTML = '';
        
        // Find matching cards
        const matchingCards = originalCards.filter(card => 
            card.text.includes(searchTerm) || 
            card.url.includes(searchTerm) ||
            card.title.toLowerCase().includes(searchTerm) ||
            card.description.toLowerCase().includes(searchTerm)
        );
        
        if (matchingCards.length === 0) {
            // Show no results message
            searchResultsContainer.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="w-16 h-16 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full flex items-center justify-center">
                        <i class="fas fa-search text-2xl text-white"></i>
                    </div>
                    <h3 class="text-xl font-bold mb-2 text-gray-800">Tidak ada hasil</h3>
                    <p class="text-gray-700">Tidak ada menu yang cocok dengan pencarian "${searchTerm}"</p>
                </div>
            `;
        } else {
            // Create result cards
            matchingCards.forEach(card => {
                const resultCard = createSearchResultCard(card, searchTerm);
                searchResultsContainer.appendChild(resultCard);
            });
        }
        
        // Force a reflow to ensure proper rendering
        document.body.offsetHeight;
    }
    
    function createSearchResultCard(cardData, searchTerm) {
        const card = document.createElement('a');
        card.href = cardData.href;
        card.className = 'bg-gradient-to-br from-blue-50 to-indigo-50 border border-gray-200 rounded-lg shadow-lg p-4 text-center hover:shadow-xl transition-all duration-300';
        card.setAttribute('role', 'article');
        
        // Highlight matching text in title and description
        const highlightedTitle = cardData.title.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<mark class="bg-blue-200 text-blue-900 px-1 rounded">${match}</mark>`
        );
        
        const highlightedDescription = cardData.description.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<mark class="bg-yellow-200 text-amber-900 px-1 rounded">${match}</mark>`
        );
        
        card.innerHTML = `
            <div class="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-amber-500 to-yellow-500 rounded-full flex items-center justify-center" aria-hidden="true">
                <i class="${cardData.icon} text-2xl text-white"></i>
            </div>
            <h3 class="text-xl font-bold mb-2 text-amber-800">${highlightedTitle}</h3>
            <p class="text-amber-700">${highlightedDescription}</p>
        `;
        
        return card;
    }
    
    // Initialize the page in the correct state
    function initializePage() {
        // Hide all tab contents initially
        tabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        // Remove active from all buttons
        tabButtons.forEach(btn => btn.classList.remove('active', 'border-amber-500'));
        
        // Set content as active by default
        const contentTabBtn = document.querySelector('[data-tab="content"]');
        const contentTab = document.getElementById('content-tab');
        
        if (contentTabBtn && contentTab) {
            contentTabBtn.classList.add('active', 'border-amber-500');
            contentTab.classList.add('active');
            contentTab.style.display = 'block';
        }
        
        // Hide results tab initially
        resultsTabBtn.classList.add('hidden');

        // Initialize UI-only feature toggles for comments and ratings
        initUiFeatureToggles();
    }
    
    // Tab switching functionality
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // If switching away from results tab, clear search first
            if (targetTab !== 'results') {
                searchInput.value = '';
                resetToNormalState();
                
                // Small delay to ensure state is properly reset
                setTimeout(() => {
                    switchToTab(targetTab);
                }, 10);
            } else {
                switchToTab(targetTab);
            }
        });
    });
    
    function switchToTab(targetTab) {
        // Hide all tab contents first
        tabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
        });
        
        // Remove active class from all buttons
        tabButtons.forEach(btn => btn.classList.remove('active', 'border-amber-500'));
        
        // Add active class to clicked button
        const targetButton = document.querySelector(`[data-tab="${targetTab}"]`);
        if (targetButton) {
            targetButton.classList.add('active', 'border-amber-500');
        }
        
        // Show target content
        const targetContent = document.getElementById(targetTab + '-tab');
        if (targetContent) {
            targetContent.classList.add('active');
            targetContent.style.display = 'block';
        }
    }
    
    // Initialize the page
    initializePage();

    // --- UI Feature Toggles (LocalStorage-based, no backend changes) ---
    function initUiFeatureToggles() {
        const commentsToggle = document.getElementById('toggle-comments-enable');
        const ratingsToggle = document.getElementById('toggle-ratings-enable');
        const adsToggle = document.getElementById('toggle-ads-enable');
        const campaignsToggle = document.getElementById('toggle-campaigns-enable');

        // Fetch persisted settings from server (BrandIdentity)
        fetch('/api/brand-identity')
            .then(r => r.ok ? r.json() : {})
            .then(cfg => {
                const persistedComments = typeof cfg.enable_comments === 'boolean' ? cfg.enable_comments : null;
                const persistedRatings = typeof cfg.enable_ratings === 'boolean' ? cfg.enable_ratings : null;
                const persistedAds = typeof cfg.enable_ads === 'boolean' ? cfg.enable_ads : null;
                const persistedCampaigns = typeof cfg.enable_campaigns === 'boolean' ? cfg.enable_campaigns : null;

                // Local overrides via localStorage still supported
                const lsComments = localStorage.getItem('ui_enable_comments');
                const lsRatings = localStorage.getItem('ui_enable_ratings');
                const lsAds = localStorage.getItem('ui_enable_ads');
                const lsCampaigns = localStorage.getItem('ui_enable_campaigns');

                const commentsEnabled = lsComments !== null ? (lsComments === 'true') : (persistedComments !== null ? persistedComments : true);
                const ratingsEnabled = lsRatings !== null ? (lsRatings === 'true') : (persistedRatings !== null ? persistedRatings : true);
                const adsEnabled = lsAds !== null ? (lsAds === 'true') : (persistedAds !== null ? persistedAds : true);
                const campaignsEnabled = lsCampaigns !== null ? (lsCampaigns === 'true') : (persistedCampaigns !== null ? persistedCampaigns : true);

                if (commentsToggle) commentsToggle.checked = commentsEnabled;
                if (ratingsToggle) ratingsToggle.checked = ratingsEnabled;
                if (adsToggle) adsToggle.checked = adsEnabled;
                if (campaignsToggle) campaignsToggle.checked = campaignsEnabled;
            })
            .catch(() => {
                // Fallback to localStorage only
                const enableComments = localStorage.getItem('ui_enable_comments');
                const enableRatings = localStorage.getItem('ui_enable_ratings');
                const enableAds = localStorage.getItem('ui_enable_ads');
                const enableCampaigns = localStorage.getItem('ui_enable_campaigns');
                if (commentsToggle) commentsToggle.checked = enableComments === null ? true : enableComments === 'true';
                if (ratingsToggle) ratingsToggle.checked = enableRatings === null ? true : enableRatings === 'true';
                if (adsToggle) adsToggle.checked = enableAds === null ? true : enableAds === 'true';
                if (campaignsToggle) campaignsToggle.checked = enableCampaigns === null ? true : enableCampaigns === 'true';
            });

        if (commentsToggle) {
            commentsToggle.addEventListener('change', () => {
                localStorage.setItem('ui_enable_comments', commentsToggle.checked ? 'true' : 'false');
                // Persist to server as well
                fetch('/api/brand-identity/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ field: 'enable_comments', value: commentsToggle.checked })
                }).catch(() => {});
                // Optional: notify
                if (typeof showToast === 'function') {
                    showToast(`Komentar ${commentsToggle.checked ? 'diaktifkan' : 'dinonaktifkan'}`, commentsToggle.checked ? 'success' : 'warning');
                }
            });
        }

        if (ratingsToggle) {
            ratingsToggle.addEventListener('change', () => {
                localStorage.setItem('ui_enable_ratings', ratingsToggle.checked ? 'true' : 'false');
                fetch('/api/brand-identity/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ field: 'enable_ratings', value: ratingsToggle.checked })
                }).catch(() => {});
                if (typeof showToast === 'function') {
                    showToast(`Rating ${ratingsToggle.checked ? 'diaktifkan' : 'dinonaktifkan'}`, ratingsToggle.checked ? 'success' : 'warning');
                }
            });
        }

        if (adsToggle) {
            adsToggle.addEventListener('change', () => {
                localStorage.setItem('ui_enable_ads', adsToggle.checked ? 'true' : 'false');
                fetch('/api/brand-identity/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ field: 'enable_ads', value: adsToggle.checked })
                }).catch(() => {});
                if (typeof showToast === 'function') {
                    showToast(`Iklan ${adsToggle.checked ? 'diaktifkan' : 'dinonaktifkan'}`, adsToggle.checked ? 'success' : 'warning');
                }
            });
        }

        if (campaignsToggle) {
            campaignsToggle.addEventListener('change', () => {
                localStorage.setItem('ui_enable_campaigns', campaignsToggle.checked ? 'true' : 'false');
                fetch('/api/brand-identity/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ field: 'enable_campaigns', value: campaignsToggle.checked })
                }).catch(() => {});
                if (typeof showToast === 'function') {
                    showToast(`Kampanye ${campaignsToggle.checked ? 'diaktifkan' : 'dinonaktifkan'}`, campaignsToggle.checked ? 'success' : 'warning');
                }
            });
        }
    }
});