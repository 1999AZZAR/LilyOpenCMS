// Content Deletion Requests Management
class ContentDeletionRequestsManager {
    constructor() {
        this.currentTab = 'news-requests';
        this.newsRequests = [];
        this.albumRequests = [];
        this.init();
    }

    // Project-styled confirmation modal returning a Promise<boolean>
    async showConfirmDialog({ title = 'Konfirmasi', message = 'Apakah Anda yakin?', confirmText = 'Ya', cancelText = 'Batal' } = {}) {
        return new Promise((resolve) => {
            // Remove existing modal if any
            const existing = document.getElementById('confirm-modal-overlay');
            if (existing) existing.remove();

            const overlay = document.createElement('div');
            overlay.id = 'confirm-modal-overlay';
            overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';

            const modal = document.createElement('div');
            modal.className = 'bg-white rounded-lg shadow-xl border border-gray-200 w-full max-w-md mx-4';
            modal.innerHTML = `
                <div class="px-6 py-4 border-b border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-800">${title}</h3>
                </div>
                <div class="px-6 py-5 text-gray-700">${message}</div>
                <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-end gap-3">
                    <button id="confirm-cancel-btn" class="px-4 py-2 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200">${cancelText}</button>
                    <button id="confirm-accept-btn" class="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700">${confirmText}</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            const cleanup = () => overlay.remove();
            modal.querySelector('#confirm-cancel-btn').addEventListener('click', () => { cleanup(); resolve(false); });
            modal.querySelector('#confirm-accept-btn').addEventListener('click', () => { cleanup(); resolve(true); });
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) { cleanup(); resolve(false); }
            });
        });
    }

    init() {
        this.bindEvents();
        // Show default "no data" message
        this.showNoDataMessage('news-requests');
        this.loadTabData('news-requests');
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });

        // News search and filter
        document.getElementById('news-search')?.addEventListener('input', (e) => {
            this.filterNewsRequests(e.target.value);
        });

        document.getElementById('news-date-filter')?.addEventListener('change', (e) => {
            this.filterNewsRequestsByDate(e.target.value);
        });

        // Album search and filter
        document.getElementById('album-search')?.addEventListener('input', (e) => {
            this.filterAlbumRequests(e.target.value);
        });

        document.getElementById('album-date-filter')?.addEventListener('change', (e) => {
            this.filterAlbumRequestsByDate(e.target.value);
        });

        // Bulk actions
        document.getElementById('bulk-approve-news-btn')?.addEventListener('click', () => {
            this.bulkApproveNewsRequests();
        });

        document.getElementById('bulk-reject-news-btn')?.addEventListener('click', () => {
            this.bulkRejectNewsRequests();
        });

        document.getElementById('bulk-approve-album-btn')?.addEventListener('click', () => {
            this.bulkApproveAlbumRequests();
        });

        document.getElementById('bulk-reject-album-btn')?.addEventListener('click', () => {
            this.bulkRejectAlbumRequests();
        });
    }

    switchTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            if (button.dataset.tab === tabName) {
                button.className = 'tab-button bg-blue-500 text-white px-4 py-2 rounded-md font-medium';
            } else {
                button.className = 'tab-button bg-gray-200 text-gray-700 px-4 py-2 rounded-md font-medium';
            }
        });

        // Simple show/hide tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        const targetTab = document.getElementById(`${tabName}-tab`);
        targetTab.classList.remove('hidden');
        
        console.log('Tab switched to:', tabName);

        this.currentTab = tabName;
        // Show no data message first, then load data
        this.showNoDataMessage(tabName);
        this.loadTabData(tabName);
    }

    showNoDataMessage(tabName) {
        if (tabName === 'news-requests') {
            const container = document.getElementById('news-requests-list');
            const noRequestsMsg = document.getElementById('news-no-requests');
            if (container) {
                container.innerHTML = '';
            }
            if (noRequestsMsg) {
                noRequestsMsg.classList.remove('hidden');
            }
        } else if (tabName === 'album-requests') {
            const container = document.getElementById('album-requests-list');
            const noRequestsMsg = document.getElementById('album-no-requests');
            if (container) {
                container.innerHTML = '';
            }
            if (noRequestsMsg) {
                noRequestsMsg.classList.remove('hidden');
            }
        }
    }

    async loadTabData(tabName) {
        try {
            if (tabName === 'news-requests') {
                await this.loadNewsRequests();
            } else if (tabName === 'album-requests') {
                await this.loadAlbumRequests();
            }
        } catch (error) {
            console.error('Error loading tab data:', error);
            showToast('error', 'Gagal memuat data permintaan penghapusan');
        }
    }

    async loadNewsRequests() {
        try {
            console.log('Loading news deletion requests...');
            const response = await fetch('/api/news/deletion-requests');
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            
            if (!response.ok) {
                // Check if response is a redirect (authentication issue)
                if (response.status === 302 || response.status === 401) {
                    throw new Error('Session expired. Please refresh the page and try again.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('News requests data:', data);
            this.newsRequests = data.requests || [];
            console.log('News requests count:', this.newsRequests.length);
            console.log('First news request:', this.newsRequests[0]);
            this.renderNewsRequests();
            this.updateNewsStats();
        } catch (error) {
            console.error('Error loading news requests:', error);
            showToast('error', `Gagal memuat permintaan penghapusan artikel: ${error.message}`);
        }
    }

    async loadAlbumRequests() {
        try {
            const response = await fetch('/admin/albums/deletion-requests');
            if (!response.ok) {
                // Check if response is a redirect (authentication issue)
                if (response.status === 302 || response.status === 401) {
                    throw new Error('Session expired. Please refresh the page and try again.');
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.albumRequests = data.requests || [];
            this.renderAlbumRequests();
            this.updateAlbumStats();
        } catch (error) {
            console.error('Error loading album requests:', error);
            showToast('error', `Gagal memuat permintaan penghapusan album: ${error.message}`);
        }
    }

    renderNewsRequests() {
        console.log('Rendering news requests...');
        const container = document.getElementById('news-requests-list');
        if (!container) {
            console.error('News requests container not found');
            return;
        }

        console.log('News requests to render:', this.newsRequests.length);
        
        // Hide no-requests message if there are requests
        const noRequestsMsg = document.getElementById('news-no-requests');
        if (noRequestsMsg) {
            noRequestsMsg.classList.add('hidden');
        }
        
        if (this.newsRequests.length === 0) {
            container.innerHTML = '';
            if (noRequestsMsg) {
                noRequestsMsg.classList.remove('hidden');
            }
            return;
        }

        const html = this.newsRequests.map(request => `
            <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; align-items: flex-start; justify-content: space-between;">
                    <div style="flex: 1;">
                        <h3 style="font-size: 18px; font-weight: 600; color: #1f2937; margin-bottom: 8px;">${request.title}</h3>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 14px; color: #6b7280;">
                            <div>
                                <p><strong>Penulis:</strong> ${request.author}</p>
                                <p><strong>Kategori:</strong> ${request.category}</p>
                                <p><strong>Dibuat:</strong> ${new Date(request.created_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Dibaca:</strong> ${request.read_count} kali</p>
                            </div>
                            <div>
                                <p><strong>Pemohon:</strong> ${request.requester}</p>
                                <p><strong>Tanggal Permintaan:</strong> ${new Date(request.deletion_requested_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Status:</strong> <span style="background: #fed7aa; color: #9a3412; padding: 2px 8px; border-radius: 12px; font-size: 12px;">Menunggu</span></p>
                                <p><strong>Terlihat:</strong> ${request.is_visible ? 'Ya' : 'Tidak'}</p>
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; margin-left: 16px;">
                        <button onclick="contentDeletionManager.approveNewsDeletion(${request.id})" 
                                style="background: #059669; color: white; padding: 4px 12px; border-radius: 4px; font-size: 14px; border: none; cursor: pointer;">
                            <i class="fas fa-check" style="margin-right: 4px;"></i>Setujui
                        </button>
                        <button onclick="contentDeletionManager.rejectNewsDeletion(${request.id})" 
                                style="background: #dc2626; color: white; padding: 4px 12px; border-radius: 4px; font-size: 14px; border: none; cursor: pointer;">
                            <i class="fas fa-times" style="margin-right: 4px;"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        console.log('Generated HTML length:', html.length);
        console.log('Generated HTML preview:', html.substring(0, 200) + '...');
        container.innerHTML = html;
        console.log('Content rendered successfully');
        console.log('Container children count:', container.children.length);
    }

    renderAlbumRequests() {
        const container = document.getElementById('album-requests-list');
        if (!container) return;

        // Hide no-requests message if there are requests
        const noRequestsMsg = document.getElementById('album-no-requests');
        if (noRequestsMsg) {
            noRequestsMsg.classList.add('hidden');
        }
        
        if (this.albumRequests.length === 0) {
            container.innerHTML = '';
            if (noRequestsMsg) {
                noRequestsMsg.classList.remove('hidden');
            }
            return;
        }

        container.innerHTML = this.albumRequests.map(request => `
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">${request.title}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                                <p><strong>Penulis:</strong> ${request.author}</p>
                                <p><strong>Kategori:</strong> ${request.category}</p>
                                <p><strong>Dibuat:</strong> ${new Date(request.created_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Bab:</strong> ${request.total_chapters} bab</p>
                            </div>
                            <div>
                                <p><strong>Pemohon:</strong> ${request.requester}</p>
                                <p><strong>Tanggal Permintaan:</strong> ${new Date(request.deletion_requested_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Status:</strong> <span class="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">Menunggu</span></p>
                                <p><strong>Selesai:</strong> ${request.is_completed ? 'Ya' : 'Tidak'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex space-x-2 ml-4">
                        <button onclick="contentDeletionManager.approveAlbumDeletion(${request.id})" 
                                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-check mr-1"></i>Setujui
                        </button>
                        <button onclick="contentDeletionManager.rejectAlbumDeletion(${request.id})" 
                                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-times mr-1"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateNewsStats() {
        const pendingCount = this.newsRequests.length;
        const today = new Date().toISOString().split('T')[0];
        const approvedToday = this.newsRequests.filter(r => 
            r.deletion_requested_at && r.deletion_requested_at.startsWith(today)
        ).length; // This would need to be calculated from actual approved data

        document.getElementById('news-pending-count').textContent = pendingCount;
        document.getElementById('news-approved-today').textContent = approvedToday;
        document.getElementById('news-rejected-today').textContent = '0'; // Would need actual data
        document.getElementById('news-avg-time').textContent = '2 jam'; // Would need actual calculation
    }

    updateAlbumStats() {
        const pendingCount = this.albumRequests.length;
        const today = new Date().toISOString().split('T')[0];
        const approvedToday = this.albumRequests.filter(r => 
            r.deletion_requested_at && r.deletion_requested_at.startsWith(today)
        ).length; // This would need to be calculated from actual approved data

        document.getElementById('album-pending-count').textContent = pendingCount;
        document.getElementById('album-approved-today').textContent = approvedToday;
        document.getElementById('album-rejected-today').textContent = '0'; // Would need actual data
        document.getElementById('album-avg-time').textContent = '3 jam'; // Would need actual calculation
    }

    filterNewsRequests(searchTerm) {
        const filtered = this.newsRequests.filter(request => 
            request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            request.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
            request.requester.toLowerCase().includes(searchTerm.toLowerCase())
        );
        this.renderFilteredNewsRequests(filtered);
    }

    filterNewsRequestsByDate(date) {
        if (!date) {
            this.renderNewsRequests();
            return;
        }
        const filtered = this.newsRequests.filter(request => 
            request.deletion_requested_at && request.deletion_requested_at.startsWith(date)
        );
        this.renderFilteredNewsRequests(filtered);
    }

    filterAlbumRequests(searchTerm) {
        const filtered = this.albumRequests.filter(request => 
            request.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
            request.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
            request.requester.toLowerCase().includes(searchTerm.toLowerCase())
        );
        this.renderFilteredAlbumRequests(filtered);
    }

    filterAlbumRequestsByDate(date) {
        if (!date) {
            this.renderAlbumRequests();
            return;
        }
        const filtered = this.albumRequests.filter(request => 
            request.deletion_requested_at && request.deletion_requested_at.startsWith(date)
        );
        this.renderFilteredAlbumRequests(filtered);
    }

    renderFilteredNewsRequests(requests) {
        const container = document.getElementById('news-requests-list');
        const noRequestsMsg = document.getElementById('news-no-requests');
        if (!container) return;

        // Hide no-requests message when showing filtered results
        if (noRequestsMsg) {
            noRequestsMsg.classList.add('hidden');
        }

        if (requests.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">Tidak ada permintaan yang sesuai dengan filter.</p>';
            return;
        }

        // Use the same rendering logic as renderNewsRequests but with filtered data
        container.innerHTML = requests.map(request => `
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">${request.title}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                                <p><strong>Penulis:</strong> ${request.author}</p>
                                <p><strong>Kategori:</strong> ${request.category}</p>
                                <p><strong>Dibuat:</strong> ${new Date(request.created_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Dibaca:</strong> ${request.read_count} kali</p>
                            </div>
                            <div>
                                <p><strong>Pemohon:</strong> ${request.requester}</p>
                                <p><strong>Tanggal Permintaan:</strong> ${new Date(request.deletion_requested_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Status:</strong> <span class="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">Menunggu</span></p>
                                <p><strong>Terlihat:</strong> ${request.is_visible ? 'Ya' : 'Tidak'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex space-x-2 ml-4">
                        <button onclick="contentDeletionManager.approveNewsDeletion(${request.id})" 
                                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-check mr-1"></i>Setujui
                        </button>
                        <button onclick="contentDeletionManager.rejectNewsDeletion(${request.id})" 
                                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-times mr-1"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderFilteredAlbumRequests(requests) {
        const container = document.getElementById('album-requests-list');
        const noRequestsMsg = document.getElementById('album-no-requests');
        if (!container) return;

        // Hide no-requests message when showing filtered results
        if (noRequestsMsg) {
            noRequestsMsg.classList.add('hidden');
        }

        if (requests.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">Tidak ada permintaan yang sesuai dengan filter.</p>';
            return;
        }

        // Use the same rendering logic as renderAlbumRequests but with filtered data
        container.innerHTML = requests.map(request => `
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-800 mb-2">${request.title}</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                            <div>
                                <p><strong>Penulis:</strong> ${request.author}</p>
                                <p><strong>Kategori:</strong> ${request.category}</p>
                                <p><strong>Dibuat:</strong> ${new Date(request.created_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Bab:</strong> ${request.total_chapters} bab</p>
                            </div>
                            <div>
                                <p><strong>Pemohon:</strong> ${request.requester}</p>
                                <p><strong>Tanggal Permintaan:</strong> ${new Date(request.deletion_requested_at).toLocaleDateString('id-ID')}</p>
                                <p><strong>Status:</strong> <span class="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">Menunggu</span></p>
                                <p><strong>Selesai:</strong> ${request.is_completed ? 'Ya' : 'Tidak'}</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex space-x-2 ml-4">
                        <button onclick="contentDeletionManager.approveAlbumDeletion(${request.id})" 
                                class="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-check mr-1"></i>Setujui
                        </button>
                        <button onclick="contentDeletionManager.rejectAlbumDeletion(${request.id})" 
                                class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition-colors">
                            <i class="fas fa-times mr-1"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async approveNewsDeletion(newsId, { skipConfirm = false } = {}) {
        if (!skipConfirm) {
            const confirmed = await this.showConfirmDialog({
                title: 'Setujui Penghapusan',
                message: 'Apakah Anda yakin ingin menyetujui penghapusan artikel ini?',
                confirmText: 'Setujui',
                cancelText: 'Batal'
            });
            if (!confirmed) return;
        }

        try {
            const response = await fetch(`/api/news/${newsId}/approve-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to approve deletion');
            }

            showToast('success', 'Artikel berhasil dihapus');
            await this.loadNewsRequests();
        } catch (error) {
            console.error('Error approving news deletion:', error);
            showToast('error', `Gagal menyetujui penghapusan: ${error.message}`);
        }
    }

    async rejectNewsDeletion(newsId, { skipConfirm = false } = {}) {
        if (!skipConfirm) {
            const confirmed = await this.showConfirmDialog({
                title: 'Tolak Permintaan',
                message: 'Apakah Anda yakin ingin menolak permintaan penghapusan artikel ini?',
                confirmText: 'Tolak',
                cancelText: 'Batal'
            });
            if (!confirmed) return;
        }

        try {
            const response = await fetch(`/api/news/${newsId}/reject-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to reject deletion');
            }

            showToast('success', 'Permintaan penghapusan ditolak');
            await this.loadNewsRequests();
        } catch (error) {
            console.error('Error rejecting news deletion:', error);
            showToast('error', `Gagal menolak permintaan: ${error.message}`);
        }
    }

    async approveAlbumDeletion(albumId, { skipConfirm = false } = {}) {
        if (!skipConfirm) {
            const confirmed = await this.showConfirmDialog({
                title: 'Setujui Penghapusan',
                message: 'Apakah Anda yakin ingin menyetujui penghapusan album ini?',
                confirmText: 'Setujui',
                cancelText: 'Batal'
            });
            if (!confirmed) return;
        }

        try {
            const response = await fetch(`/admin/albums/${albumId}/approve-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to approve deletion');
            }

            showToast('success', 'Album berhasil dihapus');
            await this.loadAlbumRequests();
        } catch (error) {
            console.error('Error approving album deletion:', error);
            showToast('error', `Gagal menyetujui penghapusan: ${error.message}`);
        }
    }

    async rejectAlbumDeletion(albumId, { skipConfirm = false } = {}) {
        if (!skipConfirm) {
            const confirmed = await this.showConfirmDialog({
                title: 'Tolak Permintaan',
                message: 'Apakah Anda yakin ingin menolak permintaan penghapusan album ini?',
                confirmText: 'Tolak',
                cancelText: 'Batal'
            });
            if (!confirmed) return;
        }

        try {
            const response = await fetch(`/admin/albums/${albumId}/reject-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to reject deletion');
            }

            showToast('success', 'Permintaan penghapusan ditolak');
            await this.loadAlbumRequests();
        } catch (error) {
            console.error('Error rejecting album deletion:', error);
            showToast('error', `Gagal menolak permintaan: ${error.message}`);
        }
    }

    async bulkApproveNewsRequests() {
        // Single confirmation for bulk action
        const count = this.newsRequests.length;
        if (count === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan artikel yang menunggu');
            return;
        }
        const confirmed = await this.showConfirmDialog({
            title: 'Setujui Semua',
            message: `Apakah Anda yakin ingin menyetujui penghapusan ${count} artikel?`,
            confirmText: 'Setujui Semua',
            cancelText: 'Batal'
        });
        if (!confirmed) return;


        if (this.newsRequests.length === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan artikel yang menunggu');
            return;
        }


        try {
            let successCount = 0;
            let errorCount = 0;
            
            for (const request of this.newsRequests) {
                try {
                    await this.approveNewsDeletion(request.id, { skipConfirm: true });
                    successCount++;
                } catch (error) {
                    errorCount++;
                    console.error(`Error approving news deletion ${request.id}:`, error);
                }
            }
            
            if (successCount > 0) {
                showToast('success', `${successCount} artikel berhasil dihapus`);
            }
            if (errorCount > 0) {
                showToast('error', `${errorCount} artikel gagal dihapus`);
            }
            
            // Reload the data
            await this.loadNewsRequests();
        } catch (error) {
            console.error('Error bulk approving news requests:', error);
            showToast('error', 'Gagal menyetujui penghapusan massal');
        }
    }

    async bulkRejectNewsRequests() {
        const count = this.newsRequests.length;
        if (count === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan artikel yang menunggu');
            return;
        }
        const confirmed = await this.showConfirmDialog({
            title: 'Tolak Semua',
            message: `Apakah Anda yakin ingin menolak ${count} permintaan penghapusan?`,
            confirmText: 'Tolak Semua',
            cancelText: 'Batal'
        });
        if (!confirmed) return;


        if (this.newsRequests.length === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan artikel yang menunggu');
            return;
        }


        try {
            let successCount = 0;
            let errorCount = 0;
            
            for (const request of this.newsRequests) {
                try {
                    await this.rejectNewsDeletion(request.id, { skipConfirm: true });
                    successCount++;
                } catch (error) {
                    errorCount++;
                    console.error(`Error rejecting news deletion ${request.id}:`, error);
                }
            }
            
            if (successCount > 0) {
                showToast('success', `${successCount} permintaan ditolak`);
            }
            if (errorCount > 0) {
                showToast('error', `${errorCount} permintaan gagal ditolak`);
            }
            
            // Reload the data
            await this.loadNewsRequests();
        } catch (error) {
            console.error('Error bulk rejecting news requests:', error);
            showToast('error', 'Gagal menolak permintaan massal');
        }
    }

    async bulkApproveAlbumRequests() {
        const count = this.albumRequests.length;
        if (count === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan album yang menunggu');
            return;
        }
        const confirmed = await this.showConfirmDialog({
            title: 'Setujui Semua',
            message: `Apakah Anda yakin ingin menyetujui penghapusan ${count} album?`,
            confirmText: 'Setujui Semua',
            cancelText: 'Batal'
        });
        if (!confirmed) return;


        if (this.albumRequests.length === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan album yang menunggu');
            return;
        }


        try {
            let successCount = 0;
            let errorCount = 0;
            
            for (const request of this.albumRequests) {
                try {
                    await this.approveAlbumDeletion(request.id, { skipConfirm: true });
                    successCount++;
                } catch (error) {
                    errorCount++;
                    console.error(`Error approving album deletion ${request.id}:`, error);
                }
            }
            
            if (successCount > 0) {
                showToast('success', `${successCount} album berhasil dihapus`);
            }
            if (errorCount > 0) {
                showToast('error', `${errorCount} album gagal dihapus`);
            }
            
            // Reload the data
            await this.loadAlbumRequests();
        } catch (error) {
            console.error('Error bulk approving album requests:', error);
            showToast('error', 'Gagal menyetujui penghapusan massal');
        }
    }

    async bulkRejectAlbumRequests() {
        const count = this.albumRequests.length;
        if (count === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan album yang menunggu');
            return;
        }
        const confirmed = await this.showConfirmDialog({
            title: 'Tolak Semua',
            message: `Apakah Anda yakin ingin menolak ${count} permintaan penghapusan?`,
            confirmText: 'Tolak Semua',
            cancelText: 'Batal'
        });
        if (!confirmed) return;


        if (this.albumRequests.length === 0) {
            showToast('warning', 'Tidak ada permintaan penghapusan album yang menunggu');
            return;
        }


        try {
            let successCount = 0;
            let errorCount = 0;
            
            for (const request of this.albumRequests) {
                try {
                    await this.rejectAlbumDeletion(request.id, { skipConfirm: true });
                    successCount++;
                } catch (error) {
                    errorCount++;
                    console.error(`Error rejecting album deletion ${request.id}:`, error);
                }
            }
            
            if (successCount > 0) {
                showToast('success', `${successCount} permintaan ditolak`);
            }
            if (errorCount > 0) {
                showToast('error', `${errorCount} permintaan gagal ditolak`);
            }
            
            // Reload the data
            await this.loadAlbumRequests();
        } catch (error) {
            console.error('Error bulk rejecting album requests:', error);
            showToast('error', 'Gagal menolak permintaan massal');
        }
    }
}

// Initialize the manager when the page loads
let contentDeletionManager;
document.addEventListener('DOMContentLoaded', () => {
    contentDeletionManager = new ContentDeletionRequestsManager();
});

// Global helper functions
function approveNewsDeletion(newsId) {
    contentDeletionManager?.approveNewsDeletion(newsId);
}

function rejectNewsDeletion(newsId) {
    contentDeletionManager?.rejectNewsDeletion(newsId);
}

function approveAlbumDeletion(albumId) {
    contentDeletionManager?.approveAlbumDeletion(albumId);
}

function rejectAlbumDeletion(albumId) {
    contentDeletionManager?.rejectAlbumDeletion(albumId);
}
