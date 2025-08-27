// Share logic (share count, clipboard, tracking)
// showToast is now available globally

// Make functions globally available
function initializeSharing(contentData, logger) {
    // Make functions globally available
    window.initializeSharing = initializeSharing;
    window.trackShare = trackShare;
    window.fetchShareData = fetchShareData;
    
    if (!contentData || contentData.id === null) {
        if (logger) logger.error("Cannot initialize sharing: Invalid or missing content ID.");
        const shareSection = document.querySelector('.share-section');
        if (shareSection) {
            shareSection.style.display = 'none';
            if (logger) logger.log("Hiding share section due to missing content ID.");
        }
        return;
    }
    
    // Detect content type based on the data structure or URL
    const isAlbum = contentData.type === 'album' || window.location.pathname.includes('/album/');
    const contentType = isAlbum ? 'album' : 'news';
    
    if (logger) logger.log(`Initializing sharing for ${contentType} with ID: ${contentData.id}`);
    
    const shareButtons = document.querySelectorAll('.share-button');
    if (shareButtons.length === 0) {
        if (logger) logger.warn("No share buttons found with class '.share-button'.");
        return;
    }
    
    // Add content type to the data
    contentData.type = contentType;
    
    // Fetch initial share data
    fetchShareData(contentData, logger);
    
    shareButtons.forEach((button, index) => {
        button.addEventListener('click', (event) => {
            const platform = button.dataset.platform;
            if (logger) logger.log(`Share button clicked for platform: ${platform}`);
            if (platform) {
                handleShareClick(platform, contentData, logger);
            } else {
                if (logger) logger.warn("Share button clicked without a 'data-platform' attribute.");
            }
        });
    });
    
    if (logger) logger.log(`Share initialization complete for ${contentType} ID: ${contentData.id}`);
}

function fetchShareData(contentData, logger) {
    if (!contentData || contentData.id === null) {
        if (logger) logger.warn("Cannot fetch share data: Invalid contentData or missing ID");
        return;
    }
    
    const contentType = contentData.type || 'news';
    const apiUrl = contentType === 'album' 
        ? `/api/albums/${contentData.id}/share-data`
        : `/api/news/${contentData.id}/share-data`;
    
    if (logger) logger.log(`Fetching share data from: ${apiUrl}`);
    
    fetch(apiUrl)
    .then(response => {
        if (!response.ok) {
            if (logger) logger.error(`Share data fetch failed: ${response.status} ${response.statusText}`);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (logger) logger.log("Share data received:", data);
        let totalShares = 0;
        const countSpans = document.querySelectorAll('.share-count');
        
        countSpans.forEach((span, index) => {
            const platform = span.dataset.platform;
            const count = Number(data[`${platform}_count`]) || 0;
            if (logger) logger.log(`Setting ${platform} count to ${count} (span ${index + 1})`);
            span.textContent = count;
            totalShares += count;
        });
        
        const totalSpan = document.querySelector('#total-share-count span');
        if (totalSpan) {
            if (logger) logger.log(`Setting total share count to ${totalShares}`);
            totalSpan.textContent = totalShares;
        } else {
            if (logger) logger.warn("Could not find #total-share-count span");
        }
    })
    .catch(error => {
        if (logger) logger.error("Error fetching share data:", error);
        // Set default values on error
        const countSpans = document.querySelectorAll('.share-count');
        countSpans.forEach(span => {
            span.textContent = '0';
        });
        const totalSpan = document.querySelector('#total-share-count span');
        if (totalSpan) totalSpan.textContent = '0';
    });
}

function trackShare(platform, contentData, logger) {
    if (!contentData || contentData.id === null) {
        const error = "Invalid contentData for tracking";
        if (logger) logger.error(error);
        return Promise.reject(error);
    }
    
    const contentType = contentData.type || 'news';
    const trackUrl = contentType === 'album'
        ? `/api/albums/${contentData.id}/track-share`
        : `/api/news/${contentData.id}/track-share`;
    
    if (logger) logger.log(`Tracking share for ${platform} at: ${trackUrl}`);
    
    return fetch(trackUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ platform })
    })
    .then(response => {
        if (!response.ok) {
            if (logger) logger.error(`Share tracking failed: ${response.status} ${response.statusText}`);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (logger) logger.log("Share track successful:", data.message || 'Success (No message)');
        // Refresh share data after successful tracking
        if (logger) logger.log("Refreshing share data after successful tracking...");
        fetchShareData(contentData, logger);
    })
    .catch(error => {
        if (logger) logger.error("Error tracking share:", error);
        throw error; // Re-throw to allow calling code to handle
    });
}

function handleShareClick(platform, contentData, logger) {
    if (!contentData || !contentData.url) {
        if (logger) logger.error("Cannot handle share click: Missing contentData or URL.");
        return;
    }
    
    // Track the share first
    trackShare(platform, contentData, logger).catch(error => {
        if (logger) logger.error("Failed to track share:", error);
        // Continue with sharing even if tracking fails
    });
    
    const title = contentData.title;
    const url = contentData.url;
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(title);
    let shareUrl = '';
    
    switch (platform) {
        case 'whatsapp':
            shareUrl = `https://wa.me/?text=${encodeURIComponent(title + ' ' + url)}`;
            break;
        case 'facebook':
            shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`;
            break;
        case 'twitter':
            shareUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`${title} ${url}`)}`;
            break;
        case 'instagram':
            showToast('info', 'Untuk berbagi ke Instagram:\n1. Salin tautan berita ini.\n2. Buka Instagram dan buat Story.\n3. Tempel tautan menggunakan fitur Stiker Tautan di Story, atau di bio profil Anda.');
            copyToClipboard(contentData, logger);
            return;
        case 'bluesky':
            shareUrl = `https://bsky.app/intent/compose?text=${encodeURIComponent(title + '\n\n' + url)}`;
            break;
        case 'clipboard':
            copyToClipboard(contentData, logger);
            return;
        default:
            if (logger) logger.warn(`Unknown share platform clicked: ${platform}`);
            return;
    }
    
    if (shareUrl) {
        const windowFeatures = 'noopener,noreferrer,width=600,height=450,resizable=yes,scrollbars=yes';
        window.open(shareUrl, '_blank', windowFeatures);
        if (logger) logger.log(`Opened share window for ${platform}: ${shareUrl}`);
    }
}

function copyToClipboard(contentData, logger) {
    if (!contentData || !contentData.url) {
        if (logger) logger.error("Cannot copy: No URL available in contentData.");
        showToast('error', 'Gagal menyalin: Tautan tidak tersedia.');
        return;
    }
    const urlToCopy = contentData.url;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(urlToCopy).then(() => {
            showToast('success', 'Tautan berhasil disalin ke clipboard!');
            if (logger) logger.log('Link copied using modern Clipboard API.');
        }).catch(() => {
            showToast('error', 'Gagal menyalin tautan secara otomatis. Coba salin manual.');
        });
    } else {
        const textArea = document.createElement("textarea");
        textArea.value = urlToCopy;
        textArea.style.position = "fixed";
        textArea.style.top = "-9999px";
        textArea.style.left = "-9999px";
        textArea.style.opacity = "0";
        textArea.setAttribute("readonly", "");
        document.body.appendChild(textArea);
        try {
            textArea.select();
            textArea.setSelectionRange(0, textArea.value.length);
            document.execCommand('copy');
            showToast('success', 'Tautan berhasil disalin ke clipboard!');
            if (logger) logger.log('Link copied using fallback execCommand.');
        } catch (err) {
            showToast('error', 'Gagal menyalin tautan secara otomatis. Coba salin manual.');
        } finally {
            if (document.body.contains(textArea)) {
                document.body.removeChild(textArea);
            }
        }
    }
}
