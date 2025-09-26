/**
 * Security Dashboard JavaScript
 * Handles comprehensive security monitoring and threat analysis
 */

class SecurityDashboard {
    constructor() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        this.refreshInterval = null;
        this.charts = {};

        this.init();
    }

    init() {
        this.loadSecurityData();
        this.startAutoRefresh();
        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('time-range')?.addEventListener('change', (e) => {
            this.loadSecurityData(e.target.value);
        });
    }

    async loadSecurityData(timeRange = '24h') {
        this.showLoading(true);

        try {
            // Load session analytics
            const analyticsResponse = await fetch('/admin/session-analytics', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (analyticsResponse.ok) {
                const analytics = await analyticsResponse.json();
                this.updateAnalytics(analytics);
            }

            // Load security events
            const eventsResponse = await fetch('/admin/security-events?per_page=50', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (eventsResponse.ok) {
                const events = await eventsResponse.json();
                this.updateSecurityEvents(events.events || []);
            }

            // Load device breakdown
            this.updateDeviceBreakdown();

        } catch (error) {
            console.error('Error loading security data:', error);
            this.showError('Failed to load security data');
        } finally {
            this.showLoading(false);
        }
    }

    updateAnalytics(analytics) {
        // Update overview stats
        document.getElementById('security-score').textContent = this.calculateSecurityScore(analytics) + '%';
        document.getElementById('active-users-count').textContent = analytics.active_sessions || 0;
        document.getElementById('total-sessions-today').textContent = analytics.total_sessions || 0;
        document.getElementById('failed-logins-today').textContent = analytics.failed_logins || 0;
        document.getElementById('suspicious-activities').textContent = analytics.suspicious_activities || 0;
        document.getElementById('session-timeouts').textContent = analytics.session_timeouts || 0;

        // Update threat level
        const threatLevel = this.calculateThreatLevel(analytics);
        document.getElementById('threat-level').textContent = threatLevel.level;
        document.getElementById('threat-level').className = threatLevel.color;
    }

    updateSecurityEvents(events) {
        const timeline = document.getElementById('security-events-timeline');
        if (!timeline) return;

        if (events.length === 0) {
            timeline.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <svg class="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    No recent events
                </div>
            `;
            return;
        }

        timeline.innerHTML = events.slice(0, 10).map(event => `
            <div class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50">
                <div class="flex-shrink-0 w-2 h-2 rounded-full mt-2 ${this.getEventIconColor(event.event_type)}"></div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900">${this.formatEventType(event.event_type)}</p>
                    <p class="text-sm text-gray-500">${this.escapeHtml(event.description || 'No description')}</p>
                    <p class="text-xs text-gray-400">${this.formatDate(event.created_at)}</p>
                </div>
            </div>
        `).join('');
    }

    updateDeviceBreakdown() {
        // Mock data for demonstration - in real implementation, this would come from API
        const mockData = {
            deviceBreakdown: {
                'Desktop': 45,
                'Mobile': 30,
                'Tablet': 15,
                'Unknown': 10
            },
            browserBreakdown: {
                'Chrome': 60,
                'Firefox': 20,
                'Safari': 15,
                'Edge': 5
            },
            geoBreakdown: {
                'Indonesia': 70,
                'United States': 15,
                'Singapore': 10,
                'Others': 5
            }
        };

        this.updateBreakdownSection('device-type-breakdown', mockData.deviceBreakdown);
        this.updateBreakdownSection('browser-breakdown', mockData.browserBreakdown);
        this.updateBreakdownSection('geo-breakdown', mockData.geoBreakdown);
    }

    updateBreakdownSection(elementId, data) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const total = Object.values(data).reduce((sum, count) => sum + count, 0);

        element.innerHTML = Object.entries(data).map(([key, count]) => {
            const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
            return `
                <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">${key}</span>
                    <div class="flex items-center space-x-2">
                        <div class="w-16 bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-600 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                        <span class="text-sm text-gray-900 font-medium">${count}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    calculateSecurityScore(analytics) {
        // Simple security score calculation based on available metrics
        let score = 100;

        if (analytics.failed_logins > 0) {
            score -= Math.min(analytics.failed_logins * 2, 20);
        }

        if (analytics.suspicious_activities > 0) {
            score -= Math.min(analytics.suspicious_activities * 5, 30);
        }

        if (analytics.session_timeouts > 0) {
            score -= Math.min(analytics.session_timeouts, 10);
        }

        return Math.max(score, 0);
    }

    calculateThreatLevel(analytics) {
        const score = this.calculateSecurityScore(analytics);

        if (score >= 90) {
            return { level: 'LOW', color: 'text-green-600' };
        } else if (score >= 70) {
            return { level: 'MEDIUM', color: 'text-yellow-600' };
        } else {
            return { level: 'HIGH', color: 'text-red-600' };
        }
    }

    getEventIconColor(eventType) {
        const colors = {
            'login_success': 'bg-green-500',
            'login_failure': 'bg-red-500',
            'session_created': 'bg-blue-500',
            'session_invalidated': 'bg-gray-500',
            'session_expired': 'bg-yellow-500',
            'suspicious_activity': 'bg-red-600',
            'password_change': 'bg-purple-500',
            'logout': 'bg-gray-400'
        };
        return colors[eventType] || 'bg-gray-300';
    }

    formatEventType(eventType) {
        return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.toggle('hidden', !show);
        }
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-600' : 'bg-green-600'
        }`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    startAutoRefresh() {
        // Refresh every 2 minutes
        this.refreshInterval = setInterval(() => {
            this.loadSecurityData();
        }, 120000);
    }

    refreshAllData() {
        this.loadSecurityData();
        this.showSuccess('Security data refreshed');
    }

    // Cleanup method
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Global function for template usage
function refreshAllData() {
    window.securityDashboard?.refreshAllData();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.securityDashboard = new SecurityDashboard();
});
