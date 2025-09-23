// SSR Optimization Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => {
                btn.classList.remove('active', 'bg-white', 'text-amber-800');
                btn.classList.add('bg-amber-200', 'text-amber-700');
            });
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active', 'bg-white', 'text-amber-800');
            button.classList.remove('bg-amber-200', 'text-amber-700');
            document.getElementById(targetTab + '-tab').classList.add('active');
        });
    });

    // Refresh functionality
    document.getElementById('refresh-ssr').addEventListener('click', function() {
        // Try to refetch SSR stats via API to avoid full reload
        fetch('/settings/ssr-optimization', { method: 'GET' })
            .then(() => location.reload())
            .catch(() => location.reload());
    });

    // Custom confirmation dialog
    function showConfirmDialog(message, onConfirm) {
        const dialog = document.createElement('div');
        dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        dialog.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
                <div class="flex items-center mb-4">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl"></i>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-lg font-medium text-gray-900">Konfirmasi</h3>
                    </div>
                </div>
                <div class="mb-6">
                    <p class="text-sm text-gray-600">${message}</p>
                </div>
                <div class="flex justify-end space-x-3">
                    <button type="button" class="cancel-btn px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-400">
                        Batal
                    </button>
                    <button type="button" class="confirm-btn px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-amber-400">
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

    document.getElementById('clear-ssr-cache').addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin membersihkan cache SSR?', () => {
            showToast('info', 'Clearing SSR cache...');
            
            fetchWithCSRF('/api/ssr-optimization/clear-cache', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('success', data.message);
                    setTimeout(() => location.reload(), 2000);
                } else {
                    showToast('error', data.message);
                }
            })
            .catch(error => {
                showToast('error', 'Error: ' + error.message);
            });
        });
    });

    // Save SSR settings
    const saveBtn = document.getElementById('save-ssr-settings');
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const selects = document.querySelectorAll('#settings-tab select');
            const inputs = document.querySelectorAll('#settings-tab input');

            const payload = {
                template_caching: (selects[0] && selects[0].value) || 'enabled',
                cache_duration: (inputs[0] && parseInt(inputs[0].value, 10)) || 300,
                max_cache_size: (inputs[1] && parseInt(inputs[1].value, 10)) || 100,
                auto_clear: (selects[1] && selects[1].value) || 'disabled'
            };

            showToast('info', 'Menyimpan pengaturan SSR...');
            fetchWithCSRF('/api/ssr-optimization/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('success', data.message || 'Pengaturan SSR disimpan');
                } else {
                    showToast('error', data.message || 'Gagal menyimpan pengaturan SSR');
                }
            })
            .catch(err => {
                showToast('error', 'Error: ' + err.message);
            });
        });
    }

    // Refresh Templates tab
    const refreshTemplatesBtn = document.getElementById('refresh-templates');
    if (refreshTemplatesBtn) {
        refreshTemplatesBtn.addEventListener('click', function() {
            showToast && showToast('info', 'Menyegarkan metrik SSR...');
            fetchWithCSRF('/api/ssr-optimization/stats')
                .then(r => r.json())
                .then(d => {
                    if (!d.success) throw new Error(d.message || 'Gagal memuat');
                    const s = d.stats || {};
                    const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
                    setText('ssr-total-renders', s.total_renders || 0);
                    setText('ssr-cached-renders', s.cached_renders || 0);
                    setText('ssr-hit-rate-text', (s.cache_hit_rate || 0) + '%');
                    setText('ssr-avg-time', ((s.avg_render_time || 0).toFixed ? s.avg_render_time.toFixed(2) : s.avg_render_time) + 's');
                    setText('ssr-avg-time-detail', ((s.avg_render_time || 0).toFixed ? s.avg_render_time.toFixed(3) : s.avg_render_time) + 's');
                    setText('ssr-max-time', ((s.max_render_time || 0).toFixed ? s.max_render_time.toFixed(3) : s.max_render_time) + 's');
                    setText('ssr-min-time', ((s.min_render_time || 0).toFixed ? s.min_render_time.toFixed(3) : s.min_render_time) + 's');
                    setText('ssr-cache-size', s.template_cache_size || 0);
                    setText('ssr-hit-rate-detail', (s.cache_hit_rate || 0) + '%');
                    setText('ssr-total-renders-detail', s.total_renders || 0);
                    const bar = document.getElementById('ssr-hit-rate-bar');
                    if (bar) bar.style.width = (s.cache_hit_rate || 0) + '%';
                    const barLg = document.getElementById('ssr-hit-rate-bar-lg');
                    const barLgText = document.getElementById('ssr-hit-rate-bar-lg-text');
                    if (barLg) barLg.style.width = (s.cache_hit_rate || 0) + '%';
                    if (barLgText) barLgText.textContent = (s.cache_hit_rate || 0) + '%';
                    const footer = document.getElementById('ssr-hit-rate-footer');
                    if (footer) footer.textContent = 'Cache Hit Rate: ' + (s.cache_hit_rate || 0) + '%';
                    showToast && showToast('success', 'Metrik SSR diperbarui');
                })
                .catch(e => {
                    showToast && showToast('error', 'Gagal memperbarui: ' + e.message);
                });
        });
    }

    // Refresh Cache tab
    const refreshCacheBtn = document.getElementById('refresh-cache');
    if (refreshCacheBtn) {
        refreshCacheBtn.addEventListener('click', function() {
            showToast && showToast('info', 'Menyegarkan statistik cache...');
            fetchWithCSRF('/api/ssr-optimization/cache-stats')
                .then(r => r.json())
                .then(d => {
                    if (!d.success) throw new Error(d.message || 'Gagal memuat');
                    const c = d.cache || {};
                    const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
                    setText('ssr-cache-size', c.cache_size || 0);
                    const hit = c.hit_rate || 0;
                    setText('ssr-hit-rate-text', hit + '%');
                    setText('ssr-hit-rate-detail', hit + '%');
                    const bar = document.getElementById('ssr-hit-rate-bar');
                    if (bar) bar.style.width = hit + '%';
                    const barLg = document.getElementById('ssr-hit-rate-bar-lg');
                    const barLgText = document.getElementById('ssr-hit-rate-bar-lg-text');
                    if (barLg) barLg.style.width = hit + '%';
                    if (barLgText) barLgText.textContent = hit + '%';
                    const footer = document.getElementById('ssr-hit-rate-footer');
                    if (footer) footer.textContent = 'Cache Hit Rate: ' + hit + '%';
                    showToast && showToast('success', 'Statistik cache diperbarui');
                })
                .catch(e => {
                    showToast && showToast('error', 'Gagal memperbarui: ' + e.message);
                });
        });
    }
});