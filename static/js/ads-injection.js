/**
 * LilyOpenCMS Ads Injection System (Production)
 * Robust, navigation-safe, content-aware ad injection with premium detector integration
 */

// Lightweight feature-flag reader shared across init paths
function getAdsFeatureFlags() {
    try {
        const flags = (typeof window !== 'undefined' && window.__UI_FLAGS__) || {};
        const lsAds = typeof localStorage !== 'undefined' ? localStorage.getItem('ui_enable_ads') : null;
        const lsCampaigns = typeof localStorage !== 'undefined' ? localStorage.getItem('ui_enable_campaigns') : null;
        const enableAds = lsAds === null ? (typeof flags.enableAds === 'boolean' ? flags.enableAds : true) : (lsAds === 'true');
        const enableCampaigns = lsCampaigns === null ? (typeof flags.enableCampaigns === 'boolean' ? flags.enableCampaigns : true) : (lsCampaigns === 'true');
        return { enableAds, enableCampaigns };
    } catch (_) {
        return { enableAds: true, enableCampaigns: true };
    }
}

// Gatekeeper: Only allow ads on whitelisted pages that set this flag
function isAdsAllowed() {
    try {
        return typeof window !== 'undefined' && window.__ADS_ALLOWED__ === true;
    } catch (_) {
        return false;
    }
}

class AdsInjectionSystem {
    constructor() {
        // Runtime configuration
        this.viewabilityThreshold = 0.5; // 50% of pixels in viewport
        this.viewabilityMinMs = 800; // must remain in view for at least 0.8s
        this.frequencyCapPerAdPerDay = 6; // max impressions per ad per day (client-side soft cap)
        this.lazyLoadRootMargin = '200px'; // start loading slightly before visible

        this.userPreferences = {
            hasPremiumAccess: false,
            shouldShowAds: true,
            premiumExpiresAt: null
        };
        this.pageContext = {};
        this.adPlacements = new Map();
        this.deviceType = this.detectDeviceType();
        // this.injectedAds removed to avoid suppressing valid placements across sections
        this.adContainers = new Map();
        this.refreshTimeout = null;
        this.isRefreshing = false;
        this.adApiCache = new Map(); // placementKey -> ad array
        this.lastPlacementContext = '';
        this.premiumDetectorInitialized = false;
        this.impressionsTracked = new Set(); // ad_id set to prevent double counting
        this.adEventIds = new Map(); // ad_id -> event_id
        this.viewObserver = null;
        this.placementObserver = null;
        this.designSignatureCache = new Map();
        this.init();
    }

    async init() {
        try {
            // Page-level allow list gate
            if (!isAdsAllowed()) {
                return;
            }
            // Global feature gate: do nothing when ads or campaigns are disabled
            const { enableAds, enableCampaigns } = getAdsFeatureFlags();
            if (!enableAds || !enableCampaigns) {
                return;
            }
            await this.initializePremiumDetector();
            this.analyzePageContext();
            this.setupViewabilityObserver();
            this.setupPlacementObserver();
            await this.loadAdsForAllPlacements();
            this.setupMutationObserver();
        } catch (error) {
            // Silent fail in production
        }
    }

    async initializePremiumDetector() {
        try {
            // Use the same premium detector mechanism as news reader and chapter reader
            const response = await fetch('/api/subscriptions/check-premium-access', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.userPreferences.hasPremiumAccess = data.has_premium_access || false;
                this.userPreferences.shouldShowAds = data.should_show_ads !== false; // Default to true if not specified
                this.userPreferences.premiumExpiresAt = data.premium_expires_at || null;
                
                // Log premium status for debugging (remove in production)
                console.log('Premium detector initialized:', {
                    hasPremiumAccess: this.userPreferences.hasPremiumAccess,
                    shouldShowAds: this.userPreferences.shouldShowAds,
                    premiumExpiresAt: this.userPreferences.premiumExpiresAt
                });
            } else {
                // Fallback to basic detection
                this.fallbackPremiumDetection();
            }
        } catch (error) {
            console.warn('Premium detector failed, using fallback:', error);
            this.fallbackPremiumDetection();
        }
        
        this.premiumDetectorInitialized = true;
    }

    fallbackPremiumDetection() {
        // Fallback detection for when the premium detector API is unavailable
        const hasUserSession = document.querySelector('[data-user-id]') || 
            document.querySelector('.user-menu') ||
            document.querySelector('.logout-link');
        
        // Check for premium indicators in the page
        const hasPremiumContent = document.querySelector('.premium-content') ||
            document.querySelector('[data-premium="true"]') ||
            document.querySelector('.content-mask-overlay');
        
        this.userPreferences.hasPremiumAccess = hasUserSession && hasPremiumContent;
        this.userPreferences.shouldShowAds = !this.userPreferences.hasPremiumAccess;
    }

    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            let shouldRefresh = false;
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // Ignore changes inside ad containers
                            if (node.closest && node.closest('.ad-placement-container')) return;
                            if (node.classList && (
                                node.classList.contains('album-card') ||
                                node.classList.contains('news-card') ||
                                node.querySelector('.album-card') ||
                                node.querySelector('.news-card')
                            )) {
                                shouldRefresh = true;
                            }
                        }
                    });
                }
            });
            if (shouldRefresh) {
                this.debouncedRefreshAds();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    debouncedRefreshAds() {
        if (this.refreshTimeout) clearTimeout(this.refreshTimeout);
        this.refreshTimeout = setTimeout(() => {
            if (!this.isRefreshing) this.refreshAds();
        }, 2000); // 2s debounce
    }

    detectDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/mobile|android|iphone|ipad|phone/.test(userAgent)) return 'mobile';
        if (/tablet|ipad/.test(userAgent)) return 'tablet';
        return 'desktop';
    }

    analyzePageContext() {
        this.pageContext = {
            pageType: this.detectPageType(),
            pageSpecific: this.detectPageSpecific(),
            cardStyle: this.extractCardStyle()
        };
    }

    detectPageType() {
        const path = window.location.pathname;
        if (path === '/' || path === '/index') {
            // Distinguish between default index and index_albums variants
            const hasIndexAlbumsGrid = document.querySelector('section .lg\:hidden ~ .hidden.lg\:grid, .flex.overflow-x-auto + .flex.overflow-x-auto');
            const manyAlbumCards = document.querySelectorAll('.album-card').length >= 6;
            if (hasIndexAlbumsGrid || manyAlbumCards) return 'home_albums';
            return 'home';
        }
        if (path.startsWith('/news')) return 'news';
        if (path.startsWith('/album/') && /\/album\/\d+\//.test(path)) return 'album_detail';
        if (path.startsWith('/albums')) return 'album';
        if (path.startsWith('/gallery')) return 'gallery';
        if (path.startsWith('/videos')) return 'videos';
        if (path.startsWith('/about')) return 'about';
        return 'general';
    }

    detectPageSpecific() {
        const path = window.location.pathname;
        const match = path.match(/\/(\d+)/);
        return match ? match[1] : null;
    }

    extractCardStyle() {
        const cards = document.querySelectorAll('.news-card, .album-card, .content-card, .gallery-item, .video-card');
        if (cards.length > 0) {
            return cards[0].className;
        }
        return '';
    }

    async loadAdsForAllPlacements() {
        // Respect global feature flags immediately
        const { enableAds, enableCampaigns } = getAdsFeatureFlags();
        if (!enableAds || !enableCampaigns) {
            this.removeAllAds();
            return;
        }
        // Respect page-level allow list
        if (!isAdsAllowed()) {
            this.removeAllAds();
            return;
        }
        // Enhanced premium check - don't load ads if user has premium access and doesn't want ads
        if (this.userPreferences.hasPremiumAccess && !this.userPreferences.shouldShowAds) {
            console.log('Premium user with ads disabled - skipping ad injection');
            return;
        }
        
        let placements = this.getPlacementsForPage();

        // Cleanup any containers/placements that are no longer valid for this page
        const validKeys = new Set(placements.map(p => this.buildPlacementKey(p)));
        this.cleanupStalePlacements(validKeys);

        // First, prepare all containers and skeletons
        for (const placement of placements) {
            const placementKey = this.buildPlacementKey(placement);
            this.adPlacements.set(placementKey, placement);
            let container = this.ensureAdContainer(placement);
            if (container && !container.querySelector('.ad-skeleton')) {
                const skeleton = document.createElement('div');
                let suffixClass = '';
                if (placement.position === 'after_n_items') {
                    const signature = this.deriveDesignSignature(placement, container);
                    if (signature && signature.cardClassName) suffixClass = ' ' + signature.cardClassName;
                }
                skeleton.className = 'ad-skeleton' + suffixClass;
                container.appendChild(skeleton);
            }
            // If container could not be created because targets aren't ready yet,
            // schedule a retry for this placement
            if (!container) {
                this.retryCreateContainerForPlacement(placement);
            }
        }

        // Ask backend for layout recommendation to adjust "after N" smartly
        try {
            const sectionsProbe = this.probeSectionsForCounts(placements);
            const resp = await fetch('/ads/api/layout/recommend', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ page_type: this.pageContext.pageType, sections: sectionsProbe })
            });
            if (resp.ok) {
                const rec = await resp.json();
                if (rec && rec.success && rec.recommendations) {
                    placements = this.applyRecommendations(placements, rec.recommendations);
                }
            }
        } catch (_) {}

        // If IO is available, observe containers; otherwise use batch serve
        if (this.placementObserver) {
            for (const placement of placements) {
                const container = this.adContainers.get(this.buildPlacementKey(placement));
                if (container) this.placementObserver.observe(container);
            }
            // Prefetch ads in background to reduce perceived latency
            try { if (placements && placements.length) this.loadAdsForPlacementsBatch(placements); } catch (_) {}
            } else {
            if (placements && placements.length) await this.loadAdsForPlacementsBatch(placements);
        }

        // Fallback: disable for home pages to avoid UX issues; only use on known grids
        const anyContainer = document.querySelector('.ad-placement-container');
        if (!anyContainer) {
            const page = this.pageContext.pageType;
            if (page === 'album' || page === 'news') {
                const discovered = this.discoverAndTagAutoGroups();
                const fallbackPlacements = [];
                for (const group of discovered) {
                    const sel = `[data-ad-group="${group.key}"] > *`;
                    const qualifier = group.key;
                    const ns = group.kind === 'album' ? [4] : [3];
                    ns.forEach(n => fallbackPlacements.push({ section: 'content', position: 'after_n_items', positionValue: n, maxAds: 1, targetSelector: sel, targetQualifier: qualifier }));
                }
                for (const p of fallbackPlacements) {
                    const container = this.ensureAdContainer(p);
                    if (!container) this.retryCreateContainerForPlacement(p);
                }
                try { await this.loadAdsForPlacementsBatch(fallbackPlacements); } catch (_) {}
            }
        }
    }

    probeSectionsForCounts(placements) {
        const buckets = new Map();
        for (const p of placements) {
            const key = this.placementQualifier(p);
            if (!buckets.has(key)) {
                const selector = p.targetSelector || '';
                const nodes = Array.from(document.querySelectorAll(selector)).filter(el => !el.classList?.contains('ad-placement-container'));
                buckets.set(key, { key, selector, item_count: nodes.length });
            }
        }
        return Array.from(buckets.values());
    }

    applyRecommendations(placements, recommendations) {
        const adjusted = [];
        for (const p of placements) {
            if (p.position !== 'after_n_items') { adjusted.push(p); continue; }
            const key = this.placementQualifier(p);
            const rec = recommendations[key];
            if (rec && Array.isArray(rec.after) && rec.after.length) {
                // explode into multiple placements as suggested
                for (const n of rec.after) {
                    adjusted.push({ ...p, positionValue: n });
                }
            } else {
                adjusted.push(p);
            }
        }
        return adjusted;
    }

    retryCreateContainerForPlacement(placement, attempts = 20, delayMs = 300) {
        let tries = 0;
        const interval = setInterval(() => {
            tries += 1;
            const container = this.ensureAdContainer(placement);
            if (container) {
                // add skeleton for visual stability
                if (!container.querySelector('.ad-skeleton')) {
                    const skeleton = document.createElement('div');
                    skeleton.className = 'ad-skeleton';
                    container.appendChild(skeleton);
                }
                if (this.placementObserver) this.placementObserver.observe(container);
                else this.loadAdsForPlacement(placement);
                clearInterval(interval);
            } else if (tries >= attempts) {
                clearInterval(interval);
            }
        }, delayMs);
    }

    buildPlacementKey(placement) {
        const suffix = placement.positionValue != null ? `_${placement.positionValue}` : '';
        const qualifier = this.placementQualifier(placement);
        return `${placement.section}_${qualifier}_${placement.position}${suffix}`;
    }

    placementQualifier(placement) {
        if (placement.targetQualifier) return placement.targetQualifier;
        const sel = placement.targetSelector || '';
        const idMatch = sel.match(/#([A-Za-z0-9_-]+)/);
        if (idMatch) return idMatch[1];
        const groupMatch = sel.match(/\[data-group=\"([^\"]+)\"\]/);
        if (groupMatch) return groupMatch[1];
        const adGroupMatch = sel.match(/\[data-ad-group=\"([^\"]+)\"\]/);
        if (adGroupMatch) return adGroupMatch[1];
        return 'default';
    }

    cleanupStalePlacements(validKeys) {
        // Remove containers not in the current valid set
        document.querySelectorAll('.ad-placement-container').forEach(container => {
            const key = container.getAttribute('data-placement');
            if (!validKeys.has(key)) {
                container.remove();
            }
        });
        // Sync internal maps
        Array.from(this.adContainers.keys()).forEach(key => {
            if (!validKeys.has(key)) this.adContainers.delete(key);
        });
        Array.from(this.adPlacements.keys()).forEach(key => {
            if (!validKeys.has(key)) this.adPlacements.delete(key);
        });
    }

    getPlacementsForPage() {
        const pageType = this.pageContext.pageType;
        const placements = [];
        
        // Enhanced placement logic with premium user consideration
        if (pageType === 'home') {
            // Home (news landing): in-stream only to avoid breaking the hero and layout
            placements.push(
                { section: 'content', position: 'after_n_items', positionValue: 3, maxAds: 1, targetSelector: '[data-group="latest-articles"] article', targetQualifier: 'latest-articles' },
                { section: 'content', position: 'after_n_items', positionValue: 6, maxAds: 1, targetSelector: '[data-group="latest-articles"] article', targetQualifier: 'latest-articles' },
                { section: 'content', position: 'after_n_items', positionValue: 2, maxAds: 1, targetSelector: '[data-group="popular-news"] article', targetQualifier: 'popular-news' }
            );
            // Auto-discover additional article groups (e.g., latest news carousels)
            this.discoverAndTagAutoGroups().forEach(group => {
                // Prefer modest spacing for carousels
                placements.push({ section: 'content', position: 'after_n_items', positionValue: 3, maxAds: 1, targetSelector: `[data-ad-group="${group.key}"] > *`, targetQualifier: group.key });
            });
        } else if (pageType === 'home_albums') {
            // Explicitly tag well-known sections by heading text
            const groupsFixed = [
                { title: 'Album Terbaru', key: 'home-latest-albums' },
                { title: 'Terpopuler', key: 'home-popular-albums' },
                { title: 'Best Albums', key: 'home-best-albums' },
                { title: 'Sedang Berlangsung', key: 'home-ongoing-albums' },
                { title: 'Best Completed', key: 'home-completed-albums' },
            ];
            const fixedTagged = [];
            groupsFixed.forEach(({ title, key }) => {
                const tagged = this.tagGroupByHeading(title, key);
                if (tagged) fixedTagged.push({ key: tagged, kind: 'album' });
            });
            // Also auto-discover any other album groups
            const discovered = this.discoverAndTagAutoGroups();
            const allGroups = [...fixedTagged, ...discovered.filter(g => g.kind === 'album')];
            allGroups.forEach(group => {
                [5, 10].forEach(n => placements.push({ section: 'content', position: 'after_n_items', positionValue: n, maxAds: 1, targetSelector: `[data-ad-group="${group.key}"] > *`, targetQualifier: group.key }));
            });
        } else if (pageType === 'news') {
            // In-stream placements inside the news grid
            placements.push(
                { section: 'content', position: 'after_n_items', positionValue: 3, maxAds: 1, targetSelector: '#news-grid > *', targetQualifier: 'news-grid' },
                { section: 'content', position: 'after_n_items', positionValue: 7, maxAds: 1, targetSelector: '#news-grid > *', targetQualifier: 'news-grid' }
            );
        } else if (pageType === 'album') {
            // In-stream placements inside the album grid
            placements.push(
                { section: 'content', position: 'after_n_items', positionValue: 4, maxAds: 1, targetSelector: '#albums-grid > *', targetQualifier: 'albums-grid' },
                { section: 'content', position: 'after_n_items', positionValue: 9, maxAds: 1, targetSelector: '#albums-grid > *', targetQualifier: 'albums-grid' }
            );
        } else if (pageType === 'album_detail') {
            // Explicitly tag the two album carousels
            const authorOther = document.querySelector('h2:contains("Album Lainnya")')?.closest('.bg-card')?.querySelector('.flex.overflow-x-auto');
            const related = document.querySelector('h2:contains("Album Terkait")')?.closest('.bg-card')?.querySelector('.flex.overflow-x-auto');
            if (authorOther && !authorOther.hasAttribute('data-ad-group')) authorOther.setAttribute('data-ad-group', 'album-detail-author');
            if (related && !related.hasAttribute('data-ad-group')) related.setAttribute('data-ad-group', 'album-detail-related');
            const groups = this.discoverAndTagAutoGroups();
            groups.forEach(group => {
                if (group.kind === 'album') {
                    const sel = `[data-ad-group="${group.key}"] > *`;
                    [2, 5].forEach(n => placements.push({ section: 'content', position: 'after_n_items', positionValue: n, maxAds: 1, targetSelector: sel, targetQualifier: group.key }));
                }
            });
        } else if (pageType === 'gallery') {
            placements.push(
                { section: 'content', position: 'top', maxAds: 1, targetSelector: 'main', insertMethod: 'prepend', targetQualifier: 'main' },
                { section: 'content', position: 'after_n_items', positionValue: 2, maxAds: 1, targetSelector: '#image-grid-container > *, #latest-image-grid-container > *', targetQualifier: 'image-grid' },
                { section: 'content', position: 'after_n_items', positionValue: 5, maxAds: 1, targetSelector: '#image-grid-container > *, #latest-image-grid-container > *', targetQualifier: 'image-grid' }
            );
        } else if (pageType === 'videos') {
            placements.push(
                { section: 'content', position: 'top', maxAds: 1, targetSelector: 'main', insertMethod: 'prepend', targetQualifier: 'main' },
                { section: 'content', position: 'after_n_items', positionValue: 2, maxAds: 1, targetSelector: '#videos-grid > *', targetQualifier: 'videos-grid' },
                { section: 'content', position: 'after_n_items', positionValue: 5, maxAds: 1, targetSelector: '#videos-grid > *', targetQualifier: 'videos-grid' }
            );
        } else if (pageType === 'about') {
            placements.push(
                { section: 'content', position: 'top', maxAds: 1, targetSelector: 'main', insertMethod: 'prepend' },
                { section: 'content', position: 'middle', maxAds: 1, targetSelector: 'main' }
            );
        } else {
            placements.push(
                { section: 'content', position: 'top', maxAds: 1, targetSelector: 'main', insertMethod: 'prepend' },
                { section: 'content', position: 'after_n_items', positionValue: 3, maxAds: 1, targetSelector: 'main' },
                { section: 'content', position: 'middle', maxAds: 1, deviceOnly: 'mobile', targetSelector: 'main' }
            );
        }
        return placements;
    }

    // Discover content groups (cards) and tag them with data-ad-group for stable selectors
    discoverAndTagAutoGroups() {
        const results = [];
        const candidates = new Set();
        const cardSelector = '.album-card, article';
        document.querySelectorAll(cardSelector).forEach(card => {
            const parent = card.parentElement;
            if (!parent) return;
            // Only consider immediate parents with multiple card children
            const children = Array.from(parent.children).filter(el => el.matches(cardSelector));
            if (children.length >= 3) candidates.add(parent);
        });
        // Filter out nested groups; keep highest-level groups
        const groups = Array.from(candidates).filter(el => !Array.from(candidates).some(other => other !== el && other.contains(el)));
        let idx = 0;
        for (const group of groups) {
            if (!group.hasAttribute('data-ad-group')) {
                group.setAttribute('data-ad-group', `auto-${idx}`);
            }
            const key = group.getAttribute('data-ad-group');
            const firstCard = group.querySelector('.album-card') ? 'album' : 'article';
            results.push({ key, kind: firstCard });
            idx += 1;
        }
        return results;
    }

    // Find the card group following a heading whose text contains the title; tag it with data-ad-group
    tagGroupByHeading(titleText, key) {
        try {
            const headings = Array.from(document.querySelectorAll('h2, h3, .section-title'));
            const h = headings.find(el => (el.textContent || '').trim().toLowerCase().includes(titleText.toLowerCase()));
            if (!h) return null;
            // Look for the nearest card group after the heading
            let cursor = h.parentElement;
            // ascend a bit to reach the section card wrapper
            for (let i = 0; i < 3 && cursor && !cursor.querySelector('.album-card'); i++) {
                cursor = cursor.nextElementSibling || cursor.parentElement;
            }
            let group = null;
            if (cursor) {
                group = cursor.querySelector('.flex.overflow-x-auto') || cursor.querySelector('.grid, .lg\\:grid');
            }
            if (!group) return null;
            if (!group.hasAttribute('data-ad-group')) group.setAttribute('data-ad-group', key);
            return group.getAttribute('data-ad-group');
        } catch (_) {
            return null;
        }
    }

    async loadAdsForPlacement(placement) {
        const placementKey = this.buildPlacementKey(placement);
        
        // Enhanced premium user filtering
        if (placement.deviceOnly && placement.deviceOnly !== this.deviceType) return;
        if (placement.userType === 'non_premium' && this.userPreferences.hasPremiumAccess) return;
        
        // Additional premium check - don't show ads to premium users who have disabled ads
        if (this.userPreferences.hasPremiumAccess && !this.userPreferences.shouldShowAds) {
            console.log(`Skipping ad placement ${placementKey} for premium user with ads disabled`);
            return;
        }
        
        // Check cache validity (invalidate if page context changes)
        const cacheKey = `${placementKey}_${this.pageContext.pageType}_${this.pageContext.pageSpecific}`;
        if (this.adApiCache.has(cacheKey)) {
            const ads = this.adApiCache.get(cacheKey);
            this.injectAdsForPlacement(ads, placement);
            return;
        }
        
        try {
            const response = await fetch('/ads/api/serve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    page_type: this.pageContext.pageType,
                    page_specific: this.pageContext.pageSpecific,
                    section: placement.section,
                    position: placement.position,
                    position_value: placement.positionValue,
                    user_id: this.getUserId(),
                    device_type: this.deviceType,
                    card_style: this.pageContext.cardStyle,
                    max_ads: placement.maxAds || 1,
                    // Add premium context for better ad targeting
                    user_has_premium: this.userPreferences.hasPremiumAccess,
                    user_should_show_ads: this.userPreferences.shouldShowAds
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.ads.length > 0) {
                    this.adApiCache.set(cacheKey, data.ads);
                    this.injectAdsForPlacement(data.ads, placement);
                } else {
                    // No ads, clear container if present
                    const adContainer = this.adContainers.get(placementKey);
                    if (adContainer) adContainer.innerHTML = '';
                }
            }
        } catch (error) {
            console.warn(`Failed to load ads for placement ${placementKey}:`, error);
        }
    }

    getUserId() { 
        // Enhanced user ID detection
        const userElement = document.querySelector('[data-user-id]');
        if (userElement) {
            return userElement.getAttribute('data-user-id');
        }
        
        // Fallback to window variable if available
        if (window.currentUserId) {
            return window.currentUserId;
        }
        
        return null; 
    }

    injectAdsForPlacement(ads, placement) {
        const placementKey = this.buildPlacementKey(placement);
        let adContainer = this.adContainers.get(placementKey);
        
        // Only skip reinjection if adContainer is present, visible, and contains the correct ad(s)
        if (adContainer && adContainer.childElementCount > 0 && adContainer.offsetParent !== null) {
            // Check if all ad_ids are present
            const existingAdIds = Array.from(adContainer.querySelectorAll('.ad-wrapper')).map(el => el.getAttribute('data-ad-id'));
            const allPresent = ads.every(ad => existingAdIds.includes(String(ad.ad_id)));
            if (allPresent) return;
        }
        
        if (!adContainer) {
            adContainer = this.ensureAdContainer(placement);
        }
        
        // Clear loading state but keep container
        adContainer.innerHTML = '';
        ads.forEach(ad => {
            const closeKey = `ad_closed_${ad.ad_id}_${placementKey}`;
            if (sessionStorage.getItem(closeKey)) return; // Don't show if closed
            if (!this.canShowAdByFrequency(ad.ad_id)) return; // Frequency capping
                this.injectAdIntoContainer(ad, adContainer, placement);
        });
    }

    createAdContainer(placement) {
        const container = document.createElement('div');
        container.className = `ad-placement-container ad-${placement.section}-${placement.position}`;
        container.setAttribute('data-placement', this.buildPlacementKey(placement));
        container.setAttribute('data-ad-section', placement.section);
        container.setAttribute('data-ad-position', placement.position);
        if (placement.positionValue != null) container.setAttribute('data-ad-position-value', String(placement.positionValue));
        
        const targetElement = this.findTargetElement(placement);
        if (!targetElement) {
            return null; // targets not ready yet; caller will retry later
        }
        // Make the container behave like the targeted card item (especially in flex carousels)
        try { this.applyContainerSizingFromTarget(container, targetElement); } catch (_) {}
            if (placement.insertMethod === 'prepend') {
                targetElement.insertBefore(container, targetElement.firstChild);
            } else if (placement.position === 'after_n_items') {
            const parent = targetElement.parentElement || targetElement.parentNode;
            if (parent) parent.insertBefore(container, targetElement.nextSibling);
            else return null;
            } else {
                targetElement.appendChild(container);
        }
        return container;
    }

    applyContainerSizingFromTarget(container, targetElement) {
        if (!targetElement) return;
        const parent = targetElement.parentElement;
        if (!parent) return;
        const parentStyle = window.getComputedStyle(parent);
        const isFlexRow = parentStyle.display.includes('flex');
        if (isFlexRow) {
            // Copy width/shrink-related classes so the container occupies same footprint
            const classes = Array.from(targetElement.classList || []);
            const widthClasses = classes.filter(c => /^(?:sm:|md:|lg:|xl:)?w-/.test(c));
            if (widthClasses.length) container.classList.add(...widthClasses);
            if (classes.includes('flex-shrink-0')) container.classList.add('flex-shrink-0');
            // Ensure min width matches to avoid collapsing in carousels
            const targetWidth = targetElement.getBoundingClientRect().width;
            if (targetWidth > 0) {
                container.style.minWidth = `${Math.round(targetWidth)}px`;
            }
        }
    }

    ensureAdContainer(placement) {
        const placementKey = this.buildPlacementKey(placement);
        let container = this.adContainers.get(placementKey);
        // Drop orphaned containers not in DOM
        if (container && !container.isConnected) {
            this.adContainers.delete(placementKey);
            container = null;
        }
        if (!container) {
            const created = this.createAdContainer(placement);
            if (created && created.isConnected) {
                this.adContainers.set(placementKey, created);
                return created;
            }
            return null;
        }
        return container;
    }

    findTargetElement(placement) {
        if (placement.position === 'after_n_items') {
            return this.findTargetAfterItems(placement.positionValue, placement.targetSelector);
        } else if (placement.position === 'top') {
            return this.findTargetTop(placement.section, placement);
        } else if (placement.position === 'bottom') {
            return this.findTargetBottom(placement.section, placement);
        } else if (placement.position === 'middle') {
            return this.findTargetMiddle(placement.section, placement);
        }
        return null;
    }

    findTargetAfterItems(n, targetSelector = null) {
        const selector = targetSelector || 'article, [data-group="latest-articles"] article, [data-group="popular-news"] article, #news-grid > *, #albums-grid > *, #videos-grid > *, #image-grid-container > *, #latest-image-grid-container > *';
        let elements = Array.from(document.querySelectorAll(selector)).filter(el => !el.classList?.contains('ad-placement-container'));
        // If this is an auto-tagged group selector, restrict to card elements to keep N stable
        const adGroupMatch = selector.match(/\[data-ad-group=\"([^\"]+)\"\]/);
        if (adGroupMatch) {
            const groupEl = document.querySelector(`[data-ad-group="${adGroupMatch[1]}"]`);
            if (groupEl) {
                elements = Array.from(groupEl.children).filter(el => el.classList?.contains('album-card') || el.tagName.toLowerCase() === 'article');
            }
        }
        // If nothing found yet, retry after dom settles (e.g., async list rendering)
        if (!elements.length) {
            // try common container ids
            const lateContainers = ['#news-grid', '#albums-grid', '#videos-grid', '[data-group="latest-articles"]', '[data-group="popular-news"]'];
            for (const sel of lateContainers) {
                const host = document.querySelector(sel);
                if (host && host.children && host.children.length) return host.children[Math.min(host.children.length - 1, Math.max(0, (n - 1)) )];
            }
        }
        if (elements.length >= n) {
            return elements[n - 1];
        }
        return elements[elements.length - 1] || null;
    }

    findTargetTop(section, placement) {
        const selector = placement.targetSelector || 'main';
        return document.querySelector(selector);
    }

    findTargetBottom(section, placement) {
        const selector = placement.targetSelector || 'main';
        const element = document.querySelector(selector);
        return element;
    }

    findTargetMiddle(section, placement) {
        const selector = placement.targetSelector || 'main';
        const element = document.querySelector(selector);
        if (element && element.children.length > 0) {
            const middleIndex = Math.floor(element.children.length / 2);
            return element.children[middleIndex];
        }
        return element;
    }

    injectAdIntoContainer(adData, container, placement) {
        const { ad_id, html } = adData;
        // Generate and cache a per-injection event_id
        const eventId = this.generateEventId();
        this.adEventIds.set(String(ad_id), eventId);
        const adWrapper = document.createElement('div');
        adWrapper.className = 'ad-wrapper ad-fade-in';
        adWrapper.setAttribute('data-ad-id', ad_id);
        adWrapper.setAttribute('data-event-id', eventId);
        adWrapper.setAttribute('data-injected-ad', '1');
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ad-close-btn';
        closeBtn.innerHTML = '&times;';
        closeBtn.title = 'Close ad';
        closeBtn.onclick = (e) => {
            e.stopPropagation();
            adWrapper.remove();
            const placementKey = placement ? `${placement.section}_${placement.position}` : '';
            sessionStorage.setItem(`ad_closed_${ad_id}_${placementKey}`, '1');
        };
        adWrapper.appendChild(closeBtn);
        
        // Card style logic (smarter imitation)
        this.applyCardImitationClasses(adWrapper, placement, container);

        // Inject raw ad HTML content inside a padded inner wrapper to match card spacing
        const inner = document.createElement('div');
        inner.className = 'ad-inner p-4 sm:p-5';
        inner.innerHTML = html;
        adWrapper.appendChild(inner);

        // Try to align media to nearby card style (aspect ratio and sizing)
        try {
            const mediaEl = adWrapper.querySelector('img, video, iframe');
            const pageType = this.pageContext.pageType;
            if (mediaEl) {
                mediaEl.classList.add('w-full');
                if (pageType === 'news') {
                    mediaEl.classList.add('news-image');
                } else if (pageType === 'album') {
                    mediaEl.classList.add('album-cover');
                }
            }
        } catch (_) {}

        this.applyPageStyling(adWrapper);
        this.initializeAdScripts(adWrapper, ad_id);
        this.attachClickTracking(adWrapper, ad_id);
        container.appendChild(adWrapper);
        this.observeAdForImpression(adWrapper, ad_id);
    }

    applyCardImitationClasses(adWrapper, placement, container) {
        const isStreamPlacement = placement && placement.section === 'content' && placement.position === 'after_n_items';
        const signature = this.deriveDesignSignature(placement, container);
        const sourceEl = this.findNearestDesignSource(placement, container);

        if (signature) {
            if (signature.cardClassName) {
                adWrapper.className += ' ' + signature.cardClassName;
            }
            if (signature.cssVars) {
                Object.entries(signature.cssVars).forEach(([key, value]) => {
                    if (value) adWrapper.style.setProperty(key, value);
                });
            }
            if (signature.aspectRatio) {
                adWrapper.style.setProperty('--ad-aspect-ratio', signature.aspectRatio);
            }
            if (signature.sourceHint) {
                adWrapper.setAttribute('data-design-source', signature.sourceHint);
            }
        }

        // If inside a horizontal carousel, copy width and shrink classes from the nearby card to match sizing
        try {
            if (sourceEl && getComputedStyle(sourceEl.parentElement).overflowX !== 'visible') {
                const parentStyle = getComputedStyle(sourceEl.parentElement);
                if (parentStyle.overflowX === 'auto' || parentStyle.overflowX === 'scroll') {
                    const widthClasses = Array.from(sourceEl.classList || []).filter(cls => /^(?:[sm|md|lg|xl]:)?w-/.test(cls) || cls === 'flex-shrink-0');
                    if (widthClasses.length) adWrapper.classList.add(...widthClasses);
                }
            }
        } catch (_) {}

        // Apply full card style set used by templates when possible
        adWrapper.classList.add(
            'bg-card', 'rounded-lg', 'border', 'border-border', 'overflow-hidden',
            'shadow-sm', 'transition-all', 'duration-300', 'hover:border-primary/30', 'hover:shadow-lg', 'group',
            'w-full', 'h-full', 'block'
        );

        if (isStreamPlacement) {
            // Container visuals are already neutralized by CSS
        }
    }

    deriveDesignSignature(placement, container) {
        const cacheKey = this.buildPlacementKey(placement);
        if (this.designSignatureCache.has(cacheKey)) {
            return this.designSignatureCache.get(cacheKey);
        }

        const source = this.findNearestDesignSource(placement, container);
        if (!source) {
            const fallback = { cardClassName: this.getCardClassForPlacement(placement) || '', extraUtilityClasses: [], cssVars: {}, sourceHint: '' };
            this.designSignatureCache.set(cacheKey, fallback);
            return fallback;
        }

        const cardClassName = this.extractPrimaryCardClass(source);
        const extraUtilityClasses = this.extractAllowedUtilities(source);
        const cssVars = this.computeStyleVarsFrom(source);
        const aspectRatio = this.estimateAspectRatio(source);
        const signature = {
            cardClassName,
            extraUtilityClasses,
            cssVars,
            sourceHint: source.className || source.tagName,
            aspectRatio
        };
        this.designSignatureCache.set(cacheKey, signature);
        return signature;
    }

    findNearestDesignSource(placement, container) {
        let el = null;
        if (container) {
            el = container.previousElementSibling && container.previousElementSibling.matches?.('.album-card, .content-card, .gallery-item, .video-card, article, .bg-card')
                ? container.previousElementSibling
                : null;
            if (!el) {
                el = container.nextElementSibling && container.nextElementSibling.matches?.('.album-card, .content-card, .gallery-item, .video-card, article, .bg-card')
                    ? container.nextElementSibling
                    : null;
            }
        }
        if (!el && placement && placement.targetSelector) {
            const target = document.querySelector(placement.targetSelector);
            if (target) {
                if (target.matches?.('.album-card, .content-card, .gallery-item, .video-card, article, .bg-card')) {
                    el = target;
                } else {
                    el = target.querySelector?.('.album-card, .content-card, .gallery-item, .video-card, article, .bg-card') || null;
                }
            }
        }
        if (!el) {
            el = document.querySelector('.album-card, .content-card, .gallery-item, .video-card, article, .bg-card');
        }
        return el || null;
    }

    extractPrimaryCardClass(sourceEl) {
        if (!sourceEl) return '';
        const classes = Array.from(sourceEl.classList || []);
        const cardClasses = ['album-card', 'content-card', 'gallery-item', 'video-card'];
        const found = classes.find(c => cardClasses.includes(c));
        if (found) return found;
        // If it looks like a card, return empty to fall back to generic imitation
        return '';
    }

    extractAllowedUtilities(sourceEl) {
        if (!sourceEl) return [];
        const classes = Array.from(sourceEl.classList || []);
        const allowPrefix = [
            'rounded', 'rounded-', 'shadow', 'shadow-', 'border', 'border-',
            // avoid spacing/grid utilities to prevent layout jumps
            'aspect-'
        ];
        const allowed = [];
        for (const cls of classes) {
            if (allowPrefix.some(prefix => cls.startsWith(prefix))) {
                allowed.push(cls);
            }
        }
        // De-duplicate and cap to a safe amount
        return Array.from(new Set(allowed)).slice(0, 8);
    }

    computeStyleVarsFrom(sourceEl) {
        try {
            const cs = getComputedStyle(sourceEl);
            const vars = {};
            const radius = cs.getPropertyValue('border-radius');
            const bg = cs.getPropertyValue('background-color');
            const shadow = cs.getPropertyValue('box-shadow');
            if (radius) vars['--ad-card-radius'] = radius.trim();
            if (bg) vars['--ad-card-bg'] = bg.trim();
            if (shadow && shadow !== 'none') vars['--ad-card-shadow'] = shadow.trim();
            return vars;
        } catch (_) {
            return {};
        }
    }

    estimateAspectRatio(sourceEl) {
        // Try to infer aspect ratio from media inside the card or CSS aspect-ratio
        try {
            const media = sourceEl.querySelector('img, video');
            if (media) {
                const w = media.naturalWidth || media.videoWidth;
                const h = media.naturalHeight || media.videoHeight;
                if (w && h && w > 0 && h > 0) {
                    return `${Math.max(1, Math.round((w / h) * 100))}/100`.replace('.','');
                }
            }
            const cs = getComputedStyle(sourceEl);
            const cssAR = cs.getPropertyValue('aspect-ratio');
            if (cssAR && cssAR.trim()) return cssAR.trim();
            // Check common utility classes
            if (sourceEl.classList.contains('album-card') || sourceEl.querySelector('.album-cover')) return '3/4';
            if (sourceEl.classList.contains('aspect-video') || sourceEl.querySelector('.aspect-video')) return '16/9';
        } catch (_) { /* ignore */ }
        // Fallback by page type
        const page = this.pageContext.pageType;
        if (page === 'album') return '3/4';
        if (page === 'gallery') return '1/1';
        return '16/9';
    }

    getCardClassForPlacement(placement) {
        // Determine an appropriate card class to blend ad with nearby content
        let cardClass = '';
        if (placement && placement.targetSelector) {
            const target = document.querySelector(placement.targetSelector);
            if (target) {
                // If target itself is a card
                if (target.classList && (target.classList.contains('news-card') || target.classList.contains('album-card') || target.classList.contains('content-card') || target.classList.contains('gallery-item') || target.classList.contains('video-card'))) {
                    cardClass = target.className;
                } else {
                    // Find closest card within target context
                    const card = target.querySelector('.news-card, .album-card, .content-card, .gallery-item, .video-card');
                    if (card) cardClass = card.className;
                }
            }
        }
        if (!cardClass) {
            const cards = document.querySelectorAll('.news-card, .album-card, .content-card, .gallery-item, .video-card');
            if (cards.length > 0) cardClass = cards[0].className;
        }
        return cardClass;
    }

    applyPageStyling(adContainer) {
        // Apply page-specific styling to match the site's design
        const pageStyle = getComputedStyle(document.body);
        adContainer.style.setProperty('--radius', pageStyle.getPropertyValue('--radius') || '0.5rem');
        adContainer.style.setProperty('--card', pageStyle.getPropertyValue('--card') || 'hsl(0 0% 100%)');
        adContainer.style.setProperty('--border', pageStyle.getPropertyValue('--border') || 'hsl(214.3 31.8% 91.4%)');
    }

    initializeAdScripts(adContainer, adId) {
        // Initialize any ad scripts within the container
        const scripts = adContainer.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.src) {
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.async = true;
                document.head.appendChild(newScript);
            } else if (script.textContent) {
                try {
                    // Prefer creating a new executable script node to avoid eval
                    const inline = document.createElement('script');
                    inline.text = script.textContent;
                    document.body.appendChild(inline);
                } catch (e) {
                    console.warn('Ad script evaluation failed:', e);
                }
            }
        });
    }

    async trackAdImpression(adId) {
        try {
            const eventId = this.adEventIds.get(String(adId)) || this.generateEventId();
            await fetch('/ads/api/track-impression', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ad_id: adId, event_id: eventId, viewable: true })
            });
        } catch (error) {
            // Silent fail in production
        }
    }

    async trackAdClick(adId) {
        try {
            const eventId = this.adEventIds.get(String(adId)) || this.generateEventId();
            await fetch('/ads/api/track-click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ad_id: adId, event_id: eventId })
            });
        } catch (error) {
            // Silent fail in production
        }
    }

    async updateAdPreferences(showAds) {
        try {
            const response = await fetch('/api/subscriptions/update-ad-preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ show_ads: showAds })
            });
            
            if (response.ok) {
                this.userPreferences.shouldShowAds = showAds;
                if (!showAds) {
                    this.removeAllAds();
                } else {
                    this.refreshAds();
                }
            }
        } catch (error) {
            console.warn('Failed to update ad preferences:', error);
        }
    }

    removeAllAds() {
        // Remove all injected ads
        document.querySelectorAll('.ad-placement-container').forEach(container => {
            container.remove();
        });
        this.adContainers.clear();
        // Ensure internal caches are reset safely
        this.adPlacements.clear();
        this.adApiCache.clear();
    }

    async refreshAds() {
        if (this.isRefreshing) return;
        this.isRefreshing = true;
        
        try {
            // Re-check feature flags; if disabled, purge and stop
            const { enableAds, enableCampaigns } = getAdsFeatureFlags();
            if (!enableAds || !enableCampaigns) {
                this.removeAllAds();
                return;
            }
            // Re-check premium status before refreshing
            await this.initializePremiumDetector();
            await this.loadAdsForAllPlacements();
        } finally {
            this.isRefreshing = false;
        }
    }

    showPremiumUpgradePrompt() {
        // Show premium upgrade prompt for non-premium users
        const prompt = document.createElement('div');
        prompt.className = 'premium-upgrade-prompt';
        prompt.innerHTML = `
            <div class="premium-upgrade-content">
                <h3>Upgrade to Premium</h3>
                <p>Get an ad-free experience with premium content access.</p>
                <a href="/premium" class="button button-primary">Upgrade Now</a>
            </div>
        `;
        document.body.appendChild(prompt);
    }

    getCurrentPlacement() { 
        return null; 
    }

    // ============ Enhancements ============
    setupViewabilityObserver() {
        if (!('IntersectionObserver' in window)) return;
        const entriesInView = new Map(); // adWrapper -> { visibleSince }
        this.viewObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                const adWrapper = entry.target;
                const adId = adWrapper.getAttribute('data-ad-id');
                if (!adId || this.impressionsTracked.has(adId)) return;

                if (entry.isIntersecting && entry.intersectionRatio >= this.viewabilityThreshold) {
                    // Start timer if not running
                    if (!entriesInView.has(adWrapper)) {
                        entriesInView.set(adWrapper, { visibleSince: performance.now() });
                    }
                    const started = entriesInView.get(adWrapper).visibleSince;
                    if (performance.now() - started >= this.viewabilityMinMs) {
                        this.trackAdImpression(adId);
                        this.impressionsTracked.add(adId);
                        this.bumpFrequencyCount(adId);
                        this.viewObserver.unobserve(adWrapper);
                        entriesInView.delete(adWrapper);
                    }
                } else {
                    // Reset timer when not sufficiently visible
                    entriesInView.delete(adWrapper);
                }
            });
        }, { threshold: [this.viewabilityThreshold] });
    }

    observeAdForImpression(adWrapper, adId) {
        if (this.viewObserver) {
            this.viewObserver.observe(adWrapper);
        } else {
            // Fallback: immediate tracking
            this.trackAdImpression(adId);
            this.bumpFrequencyCount(adId);
        }
    }

    setupPlacementObserver() {
        if (!('IntersectionObserver' in window)) return;
        this.placementObserver = new IntersectionObserver((entries) => {
            entries.forEach(async (entry) => {
                if (!entry.isIntersecting) return;
                const container = entry.target;
                const section = container.getAttribute('data-ad-section');
                const position = container.getAttribute('data-ad-position');
                const posVal = container.getAttribute('data-ad-position-value');
                const placementKey = `${section}_${position}${posVal ? '_' + posVal : ''}`;
                const placement = this.adPlacements.get(placementKey);
                if (!placement) return;
                // Stop observing to avoid duplicate loads
                this.placementObserver.unobserve(container);
                await this.loadAdsForPlacement(placement);
            });
        }, { rootMargin: this.lazyLoadRootMargin, threshold: 0.01 });
    }

    attachClickTracking(adWrapper, adId) {
        // Delegate clicks inside the ad wrapper
        adWrapper.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                this.trackAdClick(adId);
                try {
                    // Replace link href with signed redirect if it points external
                    const url = new URL(link.href, window.location.origin);
                    if (url.origin !== window.location.origin) {
                        const eventId = this.adEventIds.get(String(adId)) || this.generateEventId();
                        const signed = this.buildSignedClickUrl(adId, url.toString(), eventId);
                        if (signed) {
                            link.setAttribute('rel', 'nofollow noopener sponsored');
                            link.setAttribute('target', '_blank');
                            link.href = signed;
                        }
                    } else {
                        link.setAttribute('rel', 'nofollow noopener');
                        link.setAttribute('target', '_blank');
                    }
                } catch (_) {}
            }
        }, { capture: true });
    }

    canShowAdByFrequency(adId) {
        try {
            const todayKey = this.frequencyKeyForToday(adId);
            const count = Number(localStorage.getItem(todayKey) || '0');
            return count < this.frequencyCapPerAdPerDay;
        } catch (_) {
            return true;
        }
    }

    bumpFrequencyCount(adId) {
        try {
            const todayKey = this.frequencyKeyForToday(adId);
            const count = Number(localStorage.getItem(todayKey) || '0') + 1;
            localStorage.setItem(todayKey, String(count));
        } catch (_) {
            // ignore
        }
    }

    frequencyKeyForToday(adId) {
        const d = new Date();
        const day = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
        return `ad_impr_${adId}_${day}`;
    }
    
    async loadAdsForPlacementsBatch(placements) {
        try {
            if (!placements || !placements.length) return;
            const batch = placements.map(p => ({
                key: this.buildPlacementKey(p),
                page_type: this.pageContext.pageType,
                page_specific: this.pageContext.pageSpecific,
                section: p.section,
                position: p.position,
                position_value: p.positionValue,
                max_ads: p.maxAds || 1
            }));
            const response = await fetch('/ads/api/serve/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    placements: batch,
                    user_id: this.getUserId(),
                    user_has_premium: this.userPreferences.hasPremiumAccess,
                    user_should_show_ads: this.userPreferences.shouldShowAds,
                    device_type: this.deviceType,
                    card_style: this.pageContext.cardStyle
                })
            });
            if (!response.ok) throw new Error('batch serve failed');
            const data = await response.json();
            if (!data.success || !data.adsByPlacement) throw new Error('bad payload');
            Object.entries(data.adsByPlacement).forEach(([key, ads]) => {
                const placement = this.adPlacements.get(key);
                if (placement) this.injectAdsForPlacement(ads || [], placement);
            });
        } catch (err) {
            // Fallback to per-placement requests
            for (const p of placements) {
                await this.loadAdsForPlacement(p);
            }
        }
    }

    // Utilities
    generateEventId() {
        // RFC4122-ish v4 UUID
        if (crypto && crypto.randomUUID) {
            return crypto.randomUUID();
        }
        const bytes = new Uint8Array(16);
        if (crypto && crypto.getRandomValues) crypto.getRandomValues(bytes);
        bytes[6] = (bytes[6] & 0x0f) | 0x40;
        bytes[8] = (bytes[8] & 0x3f) | 0x80;
        const hex = [...bytes].map(b => b.toString(16).padStart(2, '0'));
        return `${hex.slice(0,4).join('')}-${hex.slice(4,6).join('')}-${hex.slice(6,8).join('')}-${hex.slice(8,10).join('')}-${hex.slice(10,16).join('')}`;
    }

    buildSignedClickUrl(adId, targetUrl, eventId) {
        try {
            // Ask server for signature
            const params = new URLSearchParams({ ad_id: String(adId), url: targetUrl, event_id: eventId });
            // Lightweight approach: server will re-sign in redirect validation; keep plain here to avoid sync call
            return `/ads/click?${params.toString()}`;
        } catch (_) { return null; }
    }
}

let adsSystem;
document.addEventListener('DOMContentLoaded', () => {
    // Check feature flags before creating the system
    const { enableAds, enableCampaigns } = getAdsFeatureFlags();
    if (enableAds && enableCampaigns && isAdsAllowed()) {
        adsSystem = new AdsInjectionSystem();
        window.adsSystem = adsSystem;
        // Enhanced initialization with premium detector
        setTimeout(() => {
            if (adsSystem && !adsSystem.isRefreshing && adsSystem.premiumDetectorInitialized) {
                adsSystem.debouncedRefreshAds();
            }
        }, 3000);
    } else {
        // Defensive: remove any stray ad containers if present
        try {
            document.querySelectorAll('.ad-placement-container').forEach(el => el.remove());
        } catch (_) {}
    }
});

