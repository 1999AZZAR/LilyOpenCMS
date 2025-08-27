// Performance Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => {
                btn.classList.remove('active', 'bg-white', 'text-blue-800');
                btn.classList.add('bg-blue-100', 'text-blue-700');
            });
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active', 'bg-white', 'text-amber-800');
            button.classList.remove('bg-amber-200', 'text-amber-700');
            document.getElementById(targetTab + '-tab').classList.add('active');
            
            // Load tab-specific data
            loadTabData(targetTab);
        });
    });

    // Load data for specific tabs
    function loadTabData(tabName) {
        switch(tabName) {
            case 'routes':
                loadRoutesData();
                break;
            case 'database':
                loadDatabaseData();
                break;
            case 'cache':
                loadCacheData();
                break;
            case 'overview':
                loadOverviewData();
                break;
        }
    }

    // Load overview data
    function loadOverviewData() {
        // Overview data is loaded server-side, just refresh if needed
    }

    // Load routes performance data
    function loadRoutesData() {
        const routesContainer = document.querySelector('#routes-tab table tbody');
        if (!routesContainer) return;

        routesContainer.innerHTML = '<tr><td colspan="6" class="text-center py-4"><i class="fas fa-spinner fa-spin mr-2"></i>Loading routes data...</td></tr>';

        fetch('/api/performance/summary')
            .then(response => response.json())
            .then(data => {
                if (data.routes && Object.keys(data.routes).length > 0) {
                    routesContainer.innerHTML = Object.entries(data.routes).map(([route, metrics]) => `
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${route}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${metrics.count || 0}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(metrics.avg_time * 1000).toFixed(2)}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(metrics.min_time * 1000).toFixed(2)}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${(metrics.max_time * 1000).toFixed(2)}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${metrics.last_request || 'N/A'}</td>
                        </tr>
                    `).join('');
                } else {
                    routesContainer.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-500">No routes data available</td></tr>';
                }
            })
            .catch(error => {
                console.error('Error loading routes data:', error);
                routesContainer.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-red-500">Error loading routes data</td></tr>';
            });
    }

    // Load database performance data
    function loadDatabaseData() {
        const databaseContainer = document.querySelector('#database-tab');
        if (!databaseContainer) return;

        fetch('/api/database/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateDatabaseMetrics(data.database_status);
                } else {
                    showToast('error', data.message || 'Failed to load database status');
                }
            })
            .catch(error => {
                console.error('Error loading database data:', error);
                showToast('error', 'Error loading database data');
            });
    }

    // Update database metrics display
    function updateDatabaseMetrics(stats) {
        // Update the main database metrics cards - use specific IDs
        const queryCountElement = document.getElementById('total-query');
        const avgTimeElement = document.getElementById('avg-query-time');
        const slowQueriesElement = document.getElementById('slow-queries');

        if (queryCountElement) queryCountElement.textContent = stats.performance?.query_count || stats.total_records || 0;
        if (avgTimeElement) avgTimeElement.textContent = `${(stats.performance?.avg_query_time || 0.50).toFixed(2)}ms`;
        if (slowQueriesElement) slowQueriesElement.textContent = stats.performance?.slow_queries || 0;

        // Update table counts - include all tables
        if (stats.tables) {
            const usersCountElement = document.getElementById('users-count');
            const newsCountElement = document.getElementById('news-count');
            const albumsCountElement = document.getElementById('albums-count');
            const chaptersCountElement = document.getElementById('chapters-count');
            const imagesCountElement = document.getElementById('images-count');
            const categoriesCountElement = document.getElementById('categories-count');
            const commentsCountElement = document.getElementById('comments-count');
            const ratingsCountElement = document.getElementById('ratings-count');
            const activitiesCountElement = document.getElementById('activities-count');

            if (usersCountElement) usersCountElement.textContent = stats.tables.users || 0;
            if (newsCountElement) newsCountElement.textContent = stats.tables.news || 0;
            if (albumsCountElement) albumsCountElement.textContent = stats.tables.albums || 0;
            if (chaptersCountElement) chaptersCountElement.textContent = stats.tables.chapters || 0;
            if (imagesCountElement) imagesCountElement.textContent = stats.tables.images || 0;
            if (categoriesCountElement) categoriesCountElement.textContent = stats.tables.categories || 0;
            if (commentsCountElement) commentsCountElement.textContent = stats.tables.comments || 0;
            if (ratingsCountElement) ratingsCountElement.textContent = stats.tables.ratings || 0;
            if (activitiesCountElement) activitiesCountElement.textContent = stats.tables.user_activities || 0;
        }

        // Update detailed stats if available
        if (stats.detailed_stats) {
            updateDetailedDatabaseStats(stats.detailed_stats);
        }

        // Update database info
        const dbSizeElement = document.getElementById('database-size');
        const dbTypeElement = document.getElementById('database-type');
        const dbIntegrityElement = document.getElementById('database-integrity');

        if (dbSizeElement) dbSizeElement.textContent = stats.database_size || 'Unknown';
        if (dbTypeElement) dbTypeElement.textContent = stats.database_type || 'Unknown';
        if (dbIntegrityElement) dbIntegrityElement.textContent = stats.integrity || 'Unknown';
    }

    function updateDetailedDatabaseStats(detailedStats) {
        // Update users detailed stats
        if (detailedStats.users) {
            const activeUsersElement = document.getElementById('active-users');
            const suspendedUsersElement = document.getElementById('suspended-users');
            const adminUsersElement = document.getElementById('admin-users');
            
            if (activeUsersElement) activeUsersElement.textContent = detailedStats.users.active_users || 0;
            if (suspendedUsersElement) suspendedUsersElement.textContent = detailedStats.users.suspended_users || 0;
            if (adminUsersElement) adminUsersElement.textContent = detailedStats.users.admin_users || 0;
        }

        // Update news detailed stats
        if (detailedStats.news) {
            const publishedNewsElement = document.getElementById('published-news');
            const draftNewsElement = document.getElementById('draft-news');
            const featuredNewsElement = document.getElementById('featured-news');

            if (publishedNewsElement) publishedNewsElement.textContent = detailedStats.news.published || 0;
            if (draftNewsElement) draftNewsElement.textContent = detailedStats.news.drafts || 0;
            if (featuredNewsElement) featuredNewsElement.textContent = detailedStats.news.featured || 0;
        }

        // Update albums detailed stats
        if (detailedStats.albums) {
            const publishedAlbumsElement = document.getElementById('published-albums');
            const hiddenAlbumsElement = document.getElementById('hidden-albums');
            const premiumAlbumsElement = document.getElementById('premium-albums');
            const completedAlbumsElement = document.getElementById('completed-albums');

            if (publishedAlbumsElement) publishedAlbumsElement.textContent = detailedStats.albums.published || 0;
            if (hiddenAlbumsElement) hiddenAlbumsElement.textContent = detailedStats.albums.hidden || 0;
            if (premiumAlbumsElement) premiumAlbumsElement.textContent = detailedStats.albums.premium || 0;
            if (completedAlbumsElement) completedAlbumsElement.textContent = detailedStats.albums.completed || 0;
        }

        // Update chapters detailed stats
        if (detailedStats.chapters) {
            const publishedChaptersElement = document.getElementById('published-chapters');
            const hiddenChaptersElement = document.getElementById('hidden-chapters');

            if (publishedChaptersElement) publishedChaptersElement.textContent = detailedStats.chapters.published || 0;
            if (hiddenChaptersElement) hiddenChaptersElement.textContent = detailedStats.chapters.hidden || 0;
        }

        // Update categories detailed stats
        if (detailedStats.categories) {
            const activeCategoriesElement = document.getElementById('active-categories');
            if (activeCategoriesElement) activeCategoriesElement.textContent = detailedStats.categories.active || 0;
        }

        // Update comments detailed stats
        if (detailedStats.comments) {
            const approvedCommentsElement = document.getElementById('approved-comments');
            const pendingCommentsElement = document.getElementById('pending-comments');

            if (approvedCommentsElement) approvedCommentsElement.textContent = detailedStats.comments.approved || 0;
            if (pendingCommentsElement) pendingCommentsElement.textContent = detailedStats.comments.pending || 0;
        }

        // Update ratings detailed stats
        if (detailedStats.ratings) {
            const avgRatingElement = document.getElementById('average-rating');
            if (avgRatingElement) avgRatingElement.textContent = detailedStats.ratings.average_rating || 0;
        }
    }

    // Load cache performance data
    function loadCacheData() {
        const cacheContainer = document.querySelector('#cache-tab');
        if (!cacheContainer) return;

        fetch('/api/cache/status')
            .then(async response => {
                if (!response.ok) {
                    let msg = 'Cache server unavailable';
                    try {
                        const data = await response.json();
                        msg = data.message || msg;
                    } catch {}
                    showToast('error', msg);
                    throw new Error(msg);
                }
                const data = await response.json();
                if (data.success) {
                    updateCacheMetrics(data.cache_status);
                } else {
                    showToast('error', data.message || 'Failed to load cache status');
                }
            })
            .catch(error => {
                showToast('error', error.message || 'Error loading cache data');
            });
    }

    // Update cache metrics display
    function updateCacheMetrics(stats) {
        const hitRateElement = document.querySelector('#cache-tab .bg-white:nth-child(1) .text-2xl');
        const missRateElement = document.querySelector('#cache-tab .bg-white:nth-child(2) .text-2xl');
        const totalRequestsElement = document.querySelector('#cache-tab .bg-white:nth-child(3) .text-2xl');

        if (hitRateElement) hitRateElement.textContent = `${stats.hit_rate}%`;
        if (missRateElement) missRateElement.textContent = `${stats.miss_rate}%`;
        if (totalRequestsElement) totalRequestsElement.textContent = stats.total_requests || 0;
    }

    // Refresh functionality
    document.getElementById('refresh-performance')?.addEventListener('click', function() {
        loadOverviewData();
        showToast('info', 'Performance data refreshed');
    });

    document.getElementById('refresh-routes')?.addEventListener('click', function() {
        loadRoutesData();
        showToast('info', 'Routes data refreshed');
    });

    // Database Management Functions
    document.getElementById('optimize-database')?.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin mengoptimalkan database?', () => {
            showToast('info', 'Optimizing database...');
            fetch('/api/database/optimize', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
            })
            .then(async response => {
                if (!response.ok) {
                    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.message || errorMsg;
                    } catch {
                        // If JSON parsing fails, use the default error message
                    }
                    showToast('error', `Optimize failed: ${errorMsg}`);
                    throw new Error(errorMsg);
                }
                
                const data = await response.json();
                if (data.success) {
                    showToast('success', data.message);
                    
                    // Update database status if available
                    if (typeof loadDatabaseStatus === 'function') {
                        loadDatabaseStatus();
                    }
                } else {
                    showToast('error', data.message || 'Optimize failed');
                }
            })
            .catch(error => {
                console.error('Optimize error:', error);
                showToast('error', 'Error: ' + error.message);
            });
        });
    });

    document.getElementById('cleanup-database')?.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin membersihkan database? Data lama akan dihapus.', () => {
            showToast('info', 'Cleaning up database...');
            fetch('/api/database/cleanup', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
            })
            .then(async response => {
                if (!response.ok) {
                    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.message || errorMsg;
                    } catch {
                        // If JSON parsing fails, use the default error message
                    }
                    showToast('error', `Cleanup failed: ${errorMsg}`);
                    throw new Error(errorMsg);
                }
                
                const data = await response.json();
                if (data.success) {
                    showToast('success', data.message);
                    if (data.cleanup_stats) {
                        showToast('info', `Removed ${data.cleanup_stats.old_activities || 0} old activities, ${data.cleanup_stats.orphaned_images || 0} orphaned images`);
                    }
                    setTimeout(() => loadDatabaseData(), 1000);
                } else {
                    showToast('error', data.message || 'Cleanup failed');
                }
            })
            .catch(error => {
                console.error('Cleanup error:', error);
                showToast('error', 'Error: ' + error.message);
            });
        });
    });

    document.getElementById('backup-database')?.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin membuat backup database?', () => {
            showToast('info', 'Creating database backup...');
            fetch('/api/database/backup', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
            })
            .then(async response => {
                if (!response.ok) {
                    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
                    try {
                        const errorData = await response.json();
                        errorMsg = errorData.message || errorMsg;
                    } catch {
                        // If JSON parsing fails, use the default error message
                    }
                    showToast('error', `Backup failed: ${errorMsg}`);
                    throw new Error(errorMsg);
                }
                
                const data = await response.json();
                if (data.success) {
                    showToast('success', data.message);
                    
                    // Update database status if available
                    if (typeof loadDatabaseStatus === 'function') {
                        loadDatabaseStatus();
                    }
                } else {
                    showToast('error', data.message || 'Backup failed');
                }
            })
            .catch(error => {
                console.error('Backup error:', error);
                showToast('error', 'Error: ' + error.message);
            });
        });
    });

    document.getElementById('list-backups')?.addEventListener('click', function() {
        showToast('info', 'Loading backups...');
        fetch('/api/database/backups')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showBackupsList(data.backups);
                } else {
                    showToast('error', data.message);
                }
            })
            .catch(error => {
                showToast('error', 'Error: ' + error.message);
            });
    });

    document.getElementById('refresh-database')?.addEventListener('click', function() {
        loadDatabaseData();
        showToast('info', 'Database data refreshed');
    });

    // Cache Management Functions
    // Cache invalidation buttons
    document.getElementById('invalidate-news-cache')?.addEventListener('click', () => {
        invalidateCachePattern('lilycms_news_*');
    });

    document.getElementById('invalidate-albums-cache')?.addEventListener('click', () => {
        invalidateCachePattern('lilycms_albums_*');
    });

    document.getElementById('invalidate-chapters-cache')?.addEventListener('click', () => {
        invalidateCachePattern('lilycms_chapters_*');
    });

    document.getElementById('invalidate-users-cache')?.addEventListener('click', () => {
        invalidateCachePattern('lilycms_users_*');
    });

    document.getElementById('clear-all-cache')?.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin membersihkan semua cache?', () => {
            clearAllCache();
        });
    });

    document.getElementById('refresh-cache')?.addEventListener('click', function() {
        loadCacheData();
    });

    // Clear cache from overview tab
    document.getElementById('clear-cache')?.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin membersihkan semua cache?', () => {
            showToast('info', 'Clearing cache...');
            
            fetch('/api/cache/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(async response => {
                if (!response.ok) {
                    let msg = 'Cache server unavailable';
                    try {
                        const data = await response.json();
                        msg = data.message || msg;
                    } catch {}
                    showToast('error', msg);
                    throw new Error(msg);
                }
                const data = await response.json();
                if (data.success) {
                    showToast('success', data.message);
                    setTimeout(() => {
                        loadCacheData();
                        loadOverviewData();
                    }, 1000);
                } else {
                    showToast('error', data.message);
                }
            })
            .catch(error => {
                console.error('Overview clear cache error:', error);
                showToast('error', 'Error: ' + error.message);
            });
        });
    });

    function showBackupsList(backups) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        
        const backupsList = backups.map(backup => `
            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                <div>
                    <div class="font-medium">${backup.filename}</div>
                    <div class="text-sm text-gray-500">Created: ${backup.created_at}</div>
                </div>
                <div class="text-sm text-gray-600">${backup.size}</div>
            </div>
        `).join('');

        dialog.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-medium text-gray-900">Database Backups</h3>
                    <button class="close-btn text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-2">
                    ${backups.length > 0 ? backupsList : '<p class="text-gray-500 text-center py-4">No backups found</p>'}
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Close dialog functionality
        dialog.querySelector('.close-btn').onclick = () => document.body.removeChild(dialog);
        dialog.onclick = (e) => {
            if (e.target === dialog) document.body.removeChild(dialog);
        };
    }

    function invalidateCachePattern(pattern) {
        showToast('info', `Invalidating ${pattern} cache...`);
        fetch(`/api/cache/invalidate/${pattern}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(async response => {
            if (!response.ok) {
                let msg = 'Cache server unavailable';
                try {
                    const data = await response.json();
                    msg = data.message || msg;
                } catch {}
                showToast('error', msg);
                throw new Error(msg);
            }
            const data = await response.json();
            if (data.success) {
                showToast('success', data.message);
                setTimeout(() => loadCacheData(), 1000);
            } else {
                showToast('error', data.message);
            }
        })
        .catch(error => {
            console.error('Cache invalidate error:', error);
            showToast('error', error.message || 'Error invalidating cache');
        });
    }

    function clearAllCache() {
        showToast('info', 'Clearing all cache...');
        fetch('/api/cache/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(async response => {
            if (!response.ok) {
                let msg = 'Cache server unavailable';
                try {
                    const data = await response.json();
                    msg = data.message || msg;
                } catch {}
                showToast('error', msg);
                throw new Error(msg);
            }
            const data = await response.json();
            if (data.success) {
                showToast('success', data.message);
                setTimeout(() => loadCacheData(), 1000);
            } else {
                showToast('error', data.message);
            }
        })
        .catch(error => {
            console.error('Cache clear error:', error);
            showToast('error', error.message || 'Error clearing cache');
        });
    }

    // Custom confirmation dialog
    function showConfirmDialog(message, onConfirm) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        dialog.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
                <div class="flex items-center mb-4">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-triangle text-blue-500 text-2xl"></i>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-lg font-medium text-gray-900">Konfirmasi</h3>
                    </div>
                </div>
                <div class="mb-6">
                    <p class="text-sm text-gray-600">${message}</p>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" class="cancel-btn px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        Batal
                    </button>
                    <button type="button" class="confirm-btn px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-amber-400">
                        Ya, Lanjutkan
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        
        const confirmBtn = dialog.querySelector('.confirm-btn');
        const cancelBtn = dialog.querySelector('.cancel-btn');
        
        const closeDialog = () => {
            document.body.removeChild(dialog);
        };
        
        confirmBtn.addEventListener('click', () => {
            closeDialog();
            onConfirm();
        });
        
        cancelBtn.addEventListener('click', closeDialog);
        
        // Close on backdrop click
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) {
                closeDialog();
            }
        });
    }

    // Toast notification function
    function showToast(type, message) {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : 
                       type === 'error' ? 'bg-red-500' : 
                       type === 'warning' ? 'bg-blue-500' : 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-4 py-2 rounded-lg shadow-lg flex items-center justify-between`;
        toast.innerHTML = `
            <span>${message}</span>
            <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }

    // Initialize tab-specific functionality
    function initializeTabFunctionality() {
        // Load initial data for active tab
        const activeTab = document.querySelector('.tab-button.active');
        if (activeTab) {
            const tabName = activeTab.getAttribute('data-tab');
            loadTabData(tabName);
        }
    }

    // Initialize when DOM is ready
    initializeTabFunctionality();
});