/**
 * CSRF Utilities for AJAX Requests
 * Provides CSRF token handling for all AJAX requests
 */

// Get CSRF token from meta tag
function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : null;
}

// Add CSRF token to form data
function addCSRFTokenToFormData(formData) {
    const token = getCSRFToken();
    if (token) {
        formData.append('csrf_token', token);
    }
    return formData;
}

// Add CSRF token to object data
function addCSRFTokenToData(data) {
    const token = getCSRFToken();
    if (token) {
        data.csrf_token = token;
    }
    return data;
}

// Enhanced fetch with CSRF token
function fetchWithCSRF(url, options = {}) {
    const token = getCSRFToken();

    // Set default headers (but don't set Content-Type for FormData)
    const headers = {
        'X-Requested-With': 'XMLHttpRequest',
        ...options.headers
    };

    // Only set Content-Type if not sending FormData
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    // Add CSRF token to headers
    if (token) {
        headers['X-CSRFToken'] = token;
    }

    // Add CSRF token to body if it's JSON
    if (options.body && typeof options.body === 'string') {
        try {
            const data = JSON.parse(options.body);
            data.csrf_token = token;
            options.body = JSON.stringify(data);
        } catch (e) {
            // If not JSON, add as form data
            if (options.body instanceof FormData) {
                options.body.append('csrf_token', token);
            }
        }
    }

    return fetch(url, {
        ...options,
        headers
    });
}

// Enhanced jQuery AJAX with CSRF token
if (typeof $ !== 'undefined') {
    // Set up CSRF token for all AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            const token = getCSRFToken();
            if (token && !settings.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', token);
            }
        }
    });
    
    // Add CSRF token to form data
    $.fn.serializeWithCSRF = function() {
        const formData = $(this).serializeArray();
        const token = getCSRFToken();
        if (token) {
            formData.push({name: 'csrf_token', value: token});
        }
        return $.param(formData);
    };
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCSRFToken,
        addCSRFTokenToFormData,
        addCSRFTokenToData,
        fetchWithCSRF
    };
}
