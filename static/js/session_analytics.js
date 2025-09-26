/**
 * Session Analytics JavaScript
 * Handles advanced session analytics and reporting with Chart.js integration
 */

class SessionAnalytics {
    constructor() {
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        this.currentTimeRange = '24h';
        this.charts = {};

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadAnalytics();
        this.initializeCharts();
    }

    bindEvents() {
        document.getElementById('time-range')?.addEventListener('change', (e) => {
            this.currentTimeRange = e.target.value;
            this.loadAnalytics();
        });
    }

    async loadAnalytics() {
        this.showLoading(true);

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

            const analytics = await response.json();
            this.updateAnalytics(analytics);
            this.updateCharts(analytics);

        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Failed to load analytics data');
        } finally {
            this.showLoading(false);
        }
    }

    updateAnalytics(analytics) {
        // Update overview metrics
        document.getElementById('total-users').textContent = analytics.total_sessions || 0;
        document.getElementById('active-sessions').textContent = analytics.active_sessions || 0;
        document.getElementById('avg-session-time').textContent = this.formatDuration(analytics.avg_session_time || 0);
        document.getElementById('peak-concurrent').textContent = analytics.peak_concurrent || 0;

        // Update quality metrics
        document.getElementById('success-rate').textContent = this.calculateSuccessRate(analytics) + '%';
        document.getElementById('avg-duration').textContent = this.formatDuration(analytics.avg_session_time || 0);
        document.getElementById('bounce-rate').textContent = this.calculateBounceRate(analytics) + '%';

        // Update tables
        this.updateTopUsersTable(analytics.top_users || []);
        this.updateSecurityEventsTable(analytics.security_events || []);
    }

    updateTopUsersTable(users) {
        const tbody = document.getElementById('top-users-table');
        if (!tbody) return;

        if (users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-gray-500">
                        No user data available
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = users.map(user => `
            <tr>
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
                            <div class="text-sm font-medium text-gray-900">${this.escapeHtml(user.username || 'Unknown')}</div>
                            <div class="text-sm text-gray-500">ID: ${user.user_id}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${user.session_count || 0}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.formatDuration(user.total_time || 0)}</div>
                </td>
            </tr>
        `).join('');
    }

    updateSecurityEventsTable(events) {
        const tbody = document.getElementById('security-events-table');
        if (!tbody) return;

        if (events.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-4 text-center text-gray-500">
                        No security events
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = events.map(event => `
            <tr>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${this.formatEventType(event.event_type)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${event.count || 0}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.formatDate(event.last_occurrence)}</div>
                </td>
            </tr>
        `).join('');
    }

    initializeCharts() {
        // Initialize Chart.js charts with error handling
        try {
            this.initializeSessionTimelineChart();
            this.initializeDeviceDistributionChart();
            this.initializeGeoAnalysisChart();
        } catch (error) {
            console.error('Error initializing charts:', error);
            // Provide fallback for missing charts
            this.showError('Failed to initialize analytics charts. Please refresh the page.');
        }
    }

    initializeSessionTimelineChart() {
        const canvasElement = document.getElementById('session-timeline-chart');
        if (!canvasElement) {
            console.error('Session timeline chart canvas element not found');
            return;
        }

        const ctx = canvasElement.getContext('2d');
        if (!ctx) {
            console.error('Failed to get 2D context for session timeline chart');
            return;
        }

        this.charts.sessionTimeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Active Sessions',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }

    initializeDeviceDistributionChart() {
        const canvasElement = document.getElementById('device-distribution-chart');
        if (!canvasElement) {
            console.error('Device distribution chart canvas element not found');
            return;
        }

        const ctx = canvasElement.getContext('2d');
        if (!ctx) {
            console.error('Failed to get 2D context for device distribution chart');
            return;
        }

        this.charts.deviceDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Desktop', 'Mobile', 'Tablet', 'Unknown'],
                datasets: [{
                    data: [45, 30, 15, 10],
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(107, 114, 128)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initializeGeoAnalysisChart() {
        const canvasElement = document.getElementById('geo-analysis-chart');
        if (!canvasElement) {
            console.error('Geo analysis chart canvas element not found');
            return;
        }

        const ctx = canvasElement.getContext('2d');
        if (!ctx) {
            console.error('Failed to get 2D context for geo analysis chart');
            return;
        }

        this.charts.geoAnalysis = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Indonesia', 'United States', 'Singapore', 'Others'],
                datasets: [{
                    label: 'Sessions by Country',
                    data: [70, 15, 10, 5],
                    backgroundColor: 'rgba(59, 130, 246, 0.8)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 10
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    updateCharts(analytics) {
        // Update session timeline chart with real data
        if (this.charts.sessionTimeline && analytics.timeline_data) {
            this.charts.sessionTimeline.data.labels = analytics.timeline_data.map(item => this.formatTime(item.timestamp));
            this.charts.sessionTimeline.data.datasets[0].data = analytics.timeline_data.map(item => item.count);
            this.charts.sessionTimeline.update();
        }

        // Update device distribution with real data
        if (this.charts.deviceDistribution && analytics.device_breakdown) {
            this.charts.deviceDistribution.data.labels = Object.keys(analytics.device_breakdown);
            this.charts.deviceDistribution.data.datasets[0].data = Object.values(analytics.device_breakdown);
            this.charts.deviceDistribution.update();
        }

        // Update geographic analysis with real data
        if (this.charts.geoAnalysis && analytics.geographic_data) {
            this.charts.geoAnalysis.data.labels = Object.keys(analytics.geographic_data);
            this.charts.geoAnalysis.data.datasets[0].data = Object.values(analytics.geographic_data);
            this.charts.geoAnalysis.update();
        }
    }

    calculateSuccessRate(analytics) {
        const total = analytics.total_sessions || 0;
        const failed = analytics.failed_logins || 0;
        if (total === 0) return 100;
        return Math.round(((total - failed) / total) * 100);
    }

    calculateBounceRate(analytics) {
        const sessions = analytics.total_sessions || 0;
        const timeouts = analytics.session_timeouts || 0;
        if (sessions === 0) return 0;
        return Math.round((timeouts / sessions) * 100);
    }

    formatDuration(seconds) {
        if (!seconds) return '0s';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    formatTime(dateString) {
        if (!dateString) return '';
        return new Date(dateString).toLocaleTimeString();
    }

    formatEventType(eventType) {
        return eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    formatDate(dateString) {
        if (!dateString) return 'Never';
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

    exportAnalytics() {
        // Create and download analytics report
        const data = {
            timestamp: new Date().toISOString(),
            timeRange: this.currentTimeRange,
            metrics: {
                totalUsers: document.getElementById('total-users').textContent,
                activeSessions: document.getElementById('active-sessions').textContent,
                avgSessionTime: document.getElementById('avg-session-time').textContent,
                peakConcurrent: document.getElementById('peak-concurrent').textContent
            }
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `session-analytics-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showSuccess('Analytics exported successfully');
    }

    // Cleanup method
    destroy() {
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
    }
}

// Global function for template usage
function exportAnalytics() {
    window.sessionAnalytics?.exportAnalytics();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.sessionAnalytics = new SessionAnalytics();
});
