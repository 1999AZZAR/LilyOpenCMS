/**
 * Session Management JavaScript
 * Handles session monitoring, filtering, and security analytics
 */

class SessionManager {
    constructor() {
        this.currentPage = 1;
        this.perPage = 20;
        this.userFilter = '';
        this.statusFilter = 'active';
        this.sessions = [];
        this.analytics = null;
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSessions();
        this.startAutoRefresh();
    }

    bindEvents() {
        // Filter controls
        document.getElementById('user-filter')?.addEventListener('input', (e) => {
            this.userFilter = e.target.value;
        });

        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.statusFilter = e.target.value;
        });

        document.getElementById('per-page')?.addEventListener('change', (e) => {
            this.perPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadSessions();
        });
    }

    async loadSessions() {
        this.showLoading(true);

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                user: this.userFilter,
                status: this.statusFilter
            });

            const response = await fetch(`/admin/sessions?${params}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.sessions = data.sessions || [];
            this.updateSessionsTable();
            this.updateStats();
            this.updatePagination(data.pagination);

        } catch (error) {
            console.error('Error loading sessions:', error);
            this.showError('Failed to load sessions. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    updateSessionsTable() {
        const tbody = document.getElementById('sessions-table-body');
        if (!tbody) return;

        if (this.sessions.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                        <div class="flex flex-col items-center">
                            <svg class="w-12 h-12 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            No sessions found
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.sessions.map(session => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <div class="flex-shrink-0 h-10 w-10">
                            <div class="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                </svg>
                            </div>
                        </div>
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">${this.escapeHtml(session.username || 'Unknown')}</div>
                            <div class="text-sm text-gray-500">ID: ${session.user_id}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">
                        ${this.getDeviceInfo(session.user_agent).device}
                    </div>
                    <div class="text-sm text-gray-500">
                        ${this.getDeviceInfo(session.user_agent).browser}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.escapeHtml(session.ip_address || 'Unknown')}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.formatDate(session.created_at)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.formatDate(session.last_activity)}</div>
                    <div class="text-sm text-gray-500">${this.getTimeAgo(session.last_activity)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        session.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }">
                        ${session.is_active ? 'Active' : 'Inactive'}
                    </span>
                    ${session.invalidated_at ? `
                        <div class="text-xs text-gray-500 mt-1">
                            Invalidated: ${this.formatDate(session.invalidated_at)}
                        </div>
                    ` : ''}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex items-center space-x-2">
                        <button onclick="sessionManager.showSessionDetails('${session.session_id}')"
                                class="text-blue-600 hover:text-blue-900">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                        </button>
                        ${session.is_active ? `
                            <button onclick="sessionManager.invalidateSession('${session.session_id}', 'Manual invalidation')"
                                    class="text-red-600 hover:text-red-900">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    }

    updateStats() {
        const activeCount = this.sessions.filter(s => s.is_active).length;
        const uniqueUsers = new Set(this.sessions.map(s => s.user_id)).size;
        const avgSessionTime = this.calculateAverageSessionTime();

        document.getElementById('active-sessions-count').textContent = activeCount;
        document.getElementById('unique-devices-count').textContent = uniqueUsers;
        document.getElementById('avg-session-time').textContent = avgSessionTime;
    }

    updatePagination(pagination) {
        if (!pagination) return;

        const controls = document.getElementById('pagination-controls');
        if (!controls) return;

        const { page, pages, total, has_prev, has_next, prev_num, next_num } = pagination;

        controls.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="text-sm text-gray-700">
                    Showing page ${page} of ${pages} (${total} total sessions)
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="sessionManager.goToPage(${prev_num || 1})"
                            ${!has_prev ? 'disabled' : ''} class="px-3 py-1 border border-gray-300 rounded text-sm ${has_prev ? 'text-gray-700 hover:bg-gray-50' : 'text-gray-400 cursor-not-allowed'}">
                        Previous
                    </button>
                    <span class="px-3 py-1 text-sm text-gray-700">
                        Page ${page} of ${pages}
                    </span>
                    <button onclick="sessionManager.goToPage(${next_num || pages})"
                            ${!has_next ? 'disabled' : ''} class="px-3 py-1 border border-gray-300 rounded text-sm ${has_next ? 'text-gray-700 hover:bg-gray-50' : 'text-gray-400 cursor-not-allowed'}">
                        Next
                    </button>
                </div>
            </div>
        `;
    }

    async showSessionDetails(sessionId) {
        try {
            const response = await fetch(`/admin/sessions/${sessionId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const session = await response.json();
            const modal = document.getElementById('session-details-modal');
            const content = document.getElementById('session-details-content');

            content.innerHTML = `
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Session ID</label>
                            <div class="mt-1 p-2 bg-gray-50 rounded text-sm font-mono">${session.session_id}</div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">User ID</label>
                            <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${session.user_id}</div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">Username</label>
                        <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.escapeHtml(session.username || 'Unknown')}</div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">Device Fingerprint</label>
                        <div class="mt-1 p-2 bg-gray-50 rounded text-sm font-mono text-xs break-all">${session.device_fingerprint}</div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">IP Address</label>
                            <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.escapeHtml(session.ip_address || 'Unknown')}</div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Status</label>
                            <div class="mt-1">
                                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                    session.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                }">
                                    ${session.is_active ? 'Active' : 'Inactive'}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">User Agent</label>
                        <div class="mt-1 p-2 bg-gray-50 rounded text-sm break-all">${this.escapeHtml(session.user_agent || 'Unknown')}</div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Created</label>
                            <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.formatDate(session.created_at)}</div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Last Activity</label>
                            <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.formatDate(session.last_activity)}</div>
                        </div>
                    </div>

                    ${session.invalidated_at ? `
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Invalidated</label>
                                <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.formatDate(session.invalidated_at)}</div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Invalidation Reason</label>
                                <div class="mt-1 p-2 bg-gray-50 rounded text-sm">${this.escapeHtml(session.invalidation_reason || 'Unknown')}</div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;

            modal.classList.remove('hidden');

        } catch (error) {
            console.error('Error loading session details:', error);
            this.showError('Failed to load session details.');
        }
    }

    async invalidateSession(sessionId, reason) {
        if (!confirm(`Are you sure you want to invalidate this session? User will be logged out immediately.\n\nReason: ${reason}`)) {
            return;
        }

        try {
            const response = await fetch(`/admin/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.showSuccess('Session invalidated successfully');
            this.loadSessions(); // Refresh the list

        } catch (error) {
            console.error('Error invalidating session:', error);
            this.showError('Failed to invalidate session.');
        }
    }

    async showSecurityAnalytics() {
        try {
            const response = await fetch('/admin/session-analytics', {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRF-Token': this.csrfToken
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.analytics = await response.json();
            this.updateAnalyticsModal();
            document.getElementById('security-analytics-modal').classList.remove('hidden');

        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Failed to load security analytics.');
        }
    }

    updateAnalyticsModal() {
        if (!this.analytics) return;

        const content = document.getElementById('security-analytics-content');
        content.innerHTML = `
            <div class="space-y-6">
                <!-- Overview Stats -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h4 class="text-sm font-medium text-blue-800">Total Sessions</h4>
                        <p class="text-2xl font-bold text-blue-900">${this.analytics.total_sessions || 0}</p>
                    </div>
                    <div class="bg-green-50 p-4 rounded-lg">
                        <h4 class="text-sm font-medium text-green-800">Active Sessions</h4>
                        <p class="text-2xl font-bold text-green-900">${this.analytics.active_sessions || 0}</p>
                    </div>
                    <div class="bg-red-50 p-4 rounded-lg">
                        <h4 class="text-sm font-medium text-red-800">Security Events</h4>
                        <p class="text-2xl font-bold text-red-900">${this.analytics.security_events || 0}</p>
                    </div>
                </div>

                <!-- Device Breakdown -->
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Device Breakdown</h4>
                    <div class="bg-gray-50 p-4 rounded-lg">
                        ${Object.entries(this.analytics.device_breakdown || {}).map(([device, count]) => `
                            <div class="flex justify-between items-center py-2">
                                <span class="text-sm text-gray-700">${device}</span>
                                <span class="text-sm font-medium text-gray-900">${count}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Timeline -->
                <div>
                    <h4 class="text-lg font-medium text-gray-900 mb-3">Session Timeline</h4>
                    <div class="space-y-2">
                        ${this.analytics.timeline_data?.map(item => `
                            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                                <div>
                                    <span class="text-sm font-medium text-gray-900">${item.event_type}</span>
                                    <span class="text-sm text-gray-500 ml-2">${item.count} events</span>
                                </div>
                                <span class="text-sm text-gray-500">${this.formatDate(item.timestamp)}</span>
                            </div>
                        `).join('') || 'No timeline data available'}
                    </div>
                </div>
            </div>
        `;
    }

    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        return new Date(dateString).toLocaleString();
    }

    getTimeAgo(dateString) {
        if (!dateString) return '';
        const now = new Date();
        const date = new Date(dateString);
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }

    getDeviceInfo(userAgent) {
        if (!userAgent) return { device: 'Unknown', browser: 'Unknown' };

        const ua = userAgent.toLowerCase();

        // Device detection
        let device = 'Desktop';
        if (ua.includes('mobile') || ua.includes('android') || ua.includes('iphone')) {
            device = ua.includes('android') ? 'Android' : 'iOS';
        }

        // Browser detection
        let browser = 'Unknown';
        if (ua.includes('chrome')) browser = 'Chrome';
        else if (ua.includes('firefox')) browser = 'Firefox';
        else if (ua.includes('safari') && !ua.includes('chrome')) browser = 'Safari';
        else if (ua.includes('edge')) browser = 'Edge';

        return { device, browser };
    }

    calculateAverageSessionTime() {
        if (this.sessions.length === 0) return '0m';

        const activeSessions = this.sessions.filter(s => s.is_active);
        if (activeSessions.length === 0) return '0m';

        const totalTime = activeSessions.reduce((sum, session) => {
            const created = new Date(session.created_at);
            const now = new Date();
            return sum + (now - created);
        }, 0);

        const avgTime = totalTime / activeSessions.length;
        const minutes = Math.floor(avgTime / 60000);

        if (minutes < 60) return `${minutes}m`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ${minutes % 60}m`;
    }

    applyFilters() {
        this.currentPage = 1;
        this.loadSessions();
    }

    clearFilters() {
        this.userFilter = '';
        this.statusFilter = 'active';
        this.currentPage = 1;

        document.getElementById('user-filter').value = '';
        document.getElementById('status-filter').value = 'active';

        this.loadSessions();
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadSessions();
    }

    refreshData() {
        this.loadSessions();
    }

    startAutoRefresh() {
        // Refresh every 30 seconds
        setInterval(() => {
            this.loadSessions();
        }, 30000);
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

    closeSessionDetails() {
        document.getElementById('session-details-modal').classList.add('hidden');
    }

    closeSecurityAnalytics() {
        document.getElementById('security-analytics-modal').classList.add('hidden');
    }
}

// Global functions for template usage
function applyFilters() {
    window.sessionManager?.applyFilters();
}

function clearFilters() {
    window.sessionManager?.clearFilters();
}

function refreshData() {
    window.sessionManager?.refreshData();
}

function showSecurityAnalytics() {
    window.sessionManager?.showSecurityAnalytics();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sessionManager = new SessionManager();
});
