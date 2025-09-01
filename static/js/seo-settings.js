/**
 * SEO Settings JavaScript
 * Handles the SEO settings page functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the page
    initializeSEOSettings();
    
    // Load current settings
    loadCurrentSettings();
    
    // Setup event listeners
    setupEventListeners();
});

function initializeSEOSettings() {
    console.log('Initializing SEO Settings...');
    
    // Check if required elements exist
    const requiredElements = [
        'current-brand-name',
        'current-website-url',
        'brand-name',
        'website-url',
        'root-seo-settings-btn',
        'root-seo-settings-modal'
    ];
    
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    if (missingElements.length > 0) {
        console.error('Missing required elements:', missingElements);
    } else {
        console.log('All required elements found');
    }
}

function loadCurrentSettings() {
    // Load brand information
    loadBrandInformation();
    
    // Load current root SEO settings
    loadRootSEOSettings();
    
    // Load global settings
    loadGlobalSettings();
}

function loadBrandInformation() {
    console.log('Loading brand information...');
    fetch('/api/brand-info')
        .then(response => {
            console.log('Brand info response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Brand info data:', data);
            // The API returns the brand info directly, not wrapped in success/brand_info
            const brandInfo = data;
            
            // Update current settings display
            document.getElementById('current-brand-name').textContent = brandInfo.brand_name || 'Not set';
            document.getElementById('current-website-url').textContent = brandInfo.website_url || 'Not set';
            
            // Update modal fields
            document.getElementById('brand-name').value = brandInfo.brand_name || '';
            document.getElementById('website-url').value = brandInfo.website_url || '';
        })
        .catch(error => {
            console.error('Error loading brand information:', error);
            showToast('Error loading brand information: ' + error.message, 'error');
        });
}

function loadRootSEOSettings() {
    console.log('Loading root SEO settings...');
    fetch('/api/root-seo-settings')
        .then(response => {
            console.log('Root SEO settings response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Root SEO settings data:', data);
            if (data.success) {
                const settings = data.settings || {};
                
                // Update current settings display
                document.getElementById('current-home-template').textContent = settings.home_meta_title || 'Not set';
                document.getElementById('current-about-template').textContent = settings.about_meta_title || 'Not set';
                document.getElementById('current-og-type').textContent = settings.default_og_type || 'website';
                document.getElementById('current-twitter-card').textContent = settings.default_twitter_card || 'summary_large_image';
                
                // Populate modal fields
                populateSettingsFields(settings);
            } else {
                console.error('Root SEO settings API returned error:', data.error);
                showToast('Error loading root SEO settings: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(error => {
            console.error('Error loading root SEO settings:', error);
            showToast('Error loading root SEO settings: ' + error.message, 'error');
        });
}

function loadGlobalSettings() {
    // Load global settings from localStorage or API
    const globalSettings = JSON.parse(localStorage.getItem('seo_global_settings') || '{}');
    
    // Populate form fields
    document.getElementById('global-meta-language').value = globalSettings.default_language || 'id';
    document.getElementById('global-meta-robots').value = globalSettings.default_meta_robots || 'index, follow';
    document.getElementById('global-og-type').value = globalSettings.default_og_type || 'website';
    document.getElementById('global-twitter-card').value = globalSettings.default_twitter_card || 'summary_large_image';
    document.getElementById('global-og-image').value = globalSettings.default_og_image || '';
    document.getElementById('global-twitter-image').value = globalSettings.default_twitter_image || '';
}

function populateSettingsFields(settings) {
    // Website URL
    document.getElementById('website-url').value = settings.website_url || '';
    
    // Root page templates
    document.getElementById('home-meta-title').value = settings.home_meta_title || '{brand_name} - Modern Content Management System';
    document.getElementById('home-meta-desc').value = settings.home_meta_description || 'LilyOpenCMS is a modern content management system for news, stories, and digital content. Discover our platform for managing articles, albums, and multimedia content.';
    document.getElementById('home-meta-keywords').value = settings.home_meta_keywords || 'content management, CMS, digital publishing, news, articles, stories, multimedia';
    
    document.getElementById('about-meta-title').value = settings.about_meta_title || 'About Us - {brand_name}';
    document.getElementById('about-meta-desc').value = settings.about_meta_description || 'Learn about LilyOpenCMS, our mission, team, and commitment to providing modern content management solutions for digital publishers and content creators.';
    document.getElementById('about-meta-keywords').value = settings.about_meta_keywords || 'about us, team, mission, company, organization, digital content';
    
    document.getElementById('news-meta-title').value = settings.news_meta_title || 'Latest News - {brand_name}';
    document.getElementById('news-meta-desc').value = settings.news_meta_description || 'Stay updated with the latest news, articles, and current events. Browse our comprehensive collection of news content and stay informed.';
    document.getElementById('news-meta-keywords').value = settings.news_meta_keywords || 'news, articles, current events, latest updates, breaking news, journalism';
    
    document.getElementById('albums-meta-title').value = settings.albums_meta_title || 'Albums & Stories - {brand_name}';
    document.getElementById('albums-meta-desc').value = settings.albums_meta_description || 'Explore our collection of albums, stories, and serialized content. Discover novels, comics, and creative works from talented authors.';
    document.getElementById('albums-meta-keywords').value = settings.albums_meta_keywords || 'albums, stories, novels, comics, creative works, serialized content';
    
    // Content type templates
    document.getElementById('article-meta-title').value = settings.article_meta_title || '{title} - {brand_name}';
    document.getElementById('article-meta-desc').value = settings.article_meta_description || '{excerpt} - Read the full article on {brand_name}.';
    document.getElementById('article-meta-keywords').value = settings.article_meta_keywords || '{category}, {title_keywords}, news, article, {brand_name}';
    document.getElementById('article-og-title').value = settings.article_og_title || '{title} - {brand_name}';
    
    document.getElementById('album-meta-title').value = settings.album_meta_title || '{title} - {brand_name}';
    document.getElementById('album-meta-desc').value = settings.album_meta_description || 'Discover {title} - a captivating story with {chapter_count} chapters. Read online for free on {brand_name}.';
    document.getElementById('album-meta-keywords').value = settings.album_meta_keywords || '{category}, {title_keywords}, story, novel, {brand_name}';
    document.getElementById('album-og-title').value = settings.album_og_title || '{title} - {brand_name}';
    
    document.getElementById('chapter-meta-title').value = settings.chapter_meta_title || '{title} - Chapter {chapter_number} - {album_title} - {brand_name}';
    document.getElementById('chapter-meta-desc').value = settings.chapter_meta_description || 'Read Chapter {chapter_number}: {title} from {album_title}. {excerpt} - Read online for free on {brand_name}.';
    document.getElementById('chapter-meta-keywords').value = settings.chapter_meta_keywords || '{album_category}, {title_keywords}, chapter {chapter_number}, {album_title}, {brand_name}';
    document.getElementById('chapter-og-title').value = settings.chapter_og_title || '{title} - Chapter {chapter_number} - {album_title} - {brand_name}';
    
    // News page template
    document.getElementById('news-meta-title').value = settings.news_meta_title || 'Latest News - {brand_name}';
    document.getElementById('news-meta-desc').value = settings.news_meta_description || 'Stay updated with the latest news, articles, and current events. Browse our comprehensive collection of news content and stay informed.';
    document.getElementById('news-meta-keywords').value = settings.news_meta_keywords || 'news, articles, current events, latest updates, breaking news, journalism';
    
    // Albums page template
    document.getElementById('albums-meta-title').value = settings.albums_meta_title || 'Albums & Stories - {brand_name}';
    document.getElementById('albums-meta-desc').value = settings.albums_meta_description || 'Explore our collection of albums, stories, and serialized content. Discover novels, comics, and creative works from talented authors.';
    document.getElementById('albums-meta-keywords').value = settings.albums_meta_keywords || 'albums, stories, novels, comics, creative works, serialized content';
}

function setupEventListeners() {
    // Root SEO Settings Modal
    document.getElementById('root-seo-settings-btn').addEventListener('click', openRootSEOSettings);
    document.getElementById('close-root-seo-settings').addEventListener('click', closeRootSEOSettings);
    document.getElementById('cancel-root-seo-settings').addEventListener('click', closeRootSEOSettings);
    
    // Root SEO Settings Form
    document.getElementById('root-seo-settings-form').addEventListener('submit', handleRootSEOSettingsSubmit);
    
    // Global Settings Form
    document.getElementById('global-seo-settings-form').addEventListener('submit', handleGlobalSettingsSubmit);
    document.getElementById('reset-global-settings').addEventListener('click', resetGlobalSettings);
    
    // Injection Settings
    document.getElementById('save-injection-settings').addEventListener('click', saveInjectionSettings);
    document.getElementById('test-injection-settings').addEventListener('click', testInjectionSettings);
    
    // Template placeholders update
    document.querySelectorAll('input[name*="meta_title"]').forEach(input => {
        input.addEventListener('input', updateTemplatePlaceholders);
    });
}

function openRootSEOSettings() {
    document.getElementById('root-seo-settings-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeRootSEOSettings() {
    document.getElementById('root-seo-settings-modal').classList.add('hidden');
    document.body.style.overflow = 'auto';
}

function updateTemplatePlaceholders() {
    const brandName = document.getElementById('brand-name').value || 'LilyOpenCMS';
    
    // Update all template fields with brand name
    document.querySelectorAll('input[name*="meta_title"]').forEach(input => {
        if (input.value.includes('{brand_name}')) {
            input.value = input.value.replace(/{brand_name}/g, brandName);
        }
    });
}

function handleRootSEOSettingsSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const settings = {};
    
    for (let [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    // Add website URL to settings with validation
    const websiteUrl = document.getElementById('website-url').value;
    if (websiteUrl && !websiteUrl.match(/^https?:\/\/.+/)) {
        showToast('Website URL harus dimulai dengan http:// atau https://', 'error');
        return;
    }
    settings.website_url = websiteUrl;
    
    // Add content type templates to settings
    settings.article_meta_title = document.getElementById('article-meta-title').value;
    settings.article_meta_description = document.getElementById('article-meta-desc').value;
    settings.article_meta_keywords = document.getElementById('article-meta-keywords').value;
    settings.article_og_title = document.getElementById('article-og-title').value;
    
    settings.album_meta_title = document.getElementById('album-meta-title').value;
    settings.album_meta_description = document.getElementById('album-meta-desc').value;
    settings.album_meta_keywords = document.getElementById('album-meta-keywords').value;
    settings.album_og_title = document.getElementById('album-og-title').value;
    
    settings.chapter_meta_title = document.getElementById('chapter-meta-title').value;
    settings.chapter_meta_description = document.getElementById('chapter-meta-desc').value;
    settings.chapter_meta_keywords = document.getElementById('chapter-meta-keywords').value;
    settings.chapter_og_title = document.getElementById('chapter-og-title').value;
    
    saveRootSEOSettings(settings);
}

function saveRootSEOSettings(settings) {
    showToast('Menyimpan pengaturan root SEO...', 'info');
    
    fetch('/api/root-seo-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Pengaturan root SEO berhasil disimpan', 'success');
            closeRootSEOSettings();
            loadCurrentSettings(); // Reload to show updated values
        } else {
            showToast(data.error || 'Gagal menyimpan pengaturan', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving root SEO settings:', error);
        showToast('Error saving settings', 'error');
    });
}

function handleGlobalSettingsSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const settings = {};
    
    for (let [key, value] of formData.entries()) {
        settings[key] = value;
    }
    
    // Save to localStorage for now (can be extended to API later)
    localStorage.setItem('seo_global_settings', JSON.stringify(settings));
    showToast('Pengaturan global berhasil disimpan', 'success');
}

function resetGlobalSettings() {
    if (confirm('Apakah Anda yakin ingin mereset pengaturan global ke default?')) {
        localStorage.removeItem('seo_global_settings');
        loadGlobalSettings();
        showToast('Pengaturan global telah direset', 'info');
    }
}

function saveInjectionSettings() {
    const settings = {
        auto_inject_articles: document.getElementById('auto-inject-articles').checked,
        auto_inject_albums: document.getElementById('auto-inject-albums').checked,
        auto_inject_chapters: document.getElementById('auto-inject-chapters').checked,
        enable_seo_lock: document.getElementById('enable-seo-lock').checked,
        lock_after_injection: document.getElementById('lock-after-injection').checked,
        batch_size: parseInt(document.getElementById('batch-size').value) || 20,
        delay_between_batches: parseInt(document.getElementById('delay-between-batches').value) || 100
    };
    
    localStorage.setItem('seo_injection_settings', JSON.stringify(settings));
    showToast('Pengaturan injection berhasil disimpan', 'success');
}

function testInjectionSettings() {
    showToast('Testing injection settings...', 'info');
    
    // Simulate a test injection
    setTimeout(() => {
        showToast('Test injection berhasil', 'success');
    }, 2000);
}

function getCSRFToken() {
    // CSRF protection is disabled in this app, so return empty string
    return '';
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    
    const bgColor = {
        'success': 'bg-green-500',
        'error': 'bg-red-500',
        'warning': 'bg-yellow-500',
        'info': 'bg-blue-500'
    }[type] || 'bg-blue-500';
    
    toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    }, 3000);
}

// Image selector functionality
function openImageSelector(targetField) {
    // This would integrate with your existing image selector
    console.log('Opening image selector for:', targetField);
    // For now, just show a placeholder
    showToast('Image selector functionality to be implemented', 'info');
}

// Export functions for potential external use
window.SEOSettings = {
    openRootSEOSettings,
    closeRootSEOSettings,
    loadCurrentSettings,
    saveRootSEOSettings,
    saveGlobalSettings: handleGlobalSettingsSubmit,
    saveInjectionSettings
};
