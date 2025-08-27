// Asset Optimization Dashboard JavaScript

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
    const refreshButtons = document.querySelectorAll('#refresh-assets, #refresh-management');
    refreshButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', function() {
        location.reload();
            });
        }
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

    // Toast notification function
    function showToast(type, message) {
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        const icon = type === 'success' ? 'fa-check' : type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        toast.className = `fixed top-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-x-full`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icon} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }

    // Precompile assets functionality
    const precompileButtons = document.querySelectorAll('#precompile-assets, #precompile-assets-opt');
    precompileButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin melakukan compress assets?', () => {
            showToast('info', 'Compressing assets...');
            
            fetch('/api/asset-optimization/compress', {
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
        }
    });

    // Run optimization functionality
    const runOptimizationButton = document.getElementById('run-optimization');
    if (runOptimizationButton) {
        runOptimizationButton.addEventListener('click', function() {
        showConfirmDialog('Apakah Anda yakin ingin menjalankan optimasi assets?', () => {
            showToast('info', 'Running asset optimization...');
            
            fetch('/api/asset-optimization/regenerate-hashes', {
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
    }

    // Clear asset cache functionality
    const clearCacheButton = document.getElementById('clear-asset-cache');
    if (clearCacheButton) {
        clearCacheButton.addEventListener('click', function() {
                showConfirmDialog('Apakah Anda yakin ingin membersihkan cache assets?', () => {
                    showToast('info', 'Clearing asset cache...');
                    
                    fetch('/api/asset-optimization/clear-cache', {
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
        }

    // Regenerate hashes functionality
    const regenerateHashesButton = document.getElementById('regenerate-hashes');
    if (regenerateHashesButton) {
        regenerateHashesButton.addEventListener('click', function() {
            showConfirmDialog('Apakah Anda yakin ingin regenerate asset hashes?', () => {
                showToast('info', 'Regenerating asset hashes...');
                
                fetch('/api/asset-optimization/regenerate-hashes', {
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
    }

    // File type optimization buttons
    const optimizeFileTypeButtons = document.querySelectorAll('.optimize-file-type');
    optimizeFileTypeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileType = this.getAttribute('data-type');
            showConfirmDialog(`Apakah Anda yakin ingin mengoptimasi file ${fileType.toUpperCase()}?`, () => {
                showToast('info', `Optimizing ${fileType.toUpperCase()} files...`);
                
                fetch('/api/asset-optimization/minify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        file_type: fileType
                    })
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
    });

    // View file type buttons
    const viewFileTypeButtons = document.querySelectorAll('.view-file-type');
    viewFileTypeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileType = this.getAttribute('data-type');
            showToast('info', `Viewing ${fileType.toUpperCase()} files in static folder`);
            // This could open a modal or redirect to file browser
        });
    });

    // Save settings functionality
    const saveSettingsButton = document.getElementById('save-settings');
    if (saveSettingsButton) {
        saveSettingsButton.addEventListener('click', function() {
            const cssCompression = document.getElementById('css-compression').value;
            const jsCompression = document.getElementById('js-compression').value;
            const imageOptimization = document.getElementById('image-optimization').value;
            const cacheDuration = document.getElementById('cache-duration').value;

            showToast('info', 'Saving settings...');
            
            // Here you would typically send the settings to the server
            // For now, we'll just show a success message
            setTimeout(() => {
                showToast('success', 'Settings saved successfully!');
            }, 1000);
        });
    }

    // Initialize settings values (if they exist in localStorage)
    const cssCompressionSelect = document.getElementById('css-compression');
    const jsCompressionSelect = document.getElementById('js-compression');
    const imageOptimizationSelect = document.getElementById('image-optimization');
    const cacheDurationInput = document.getElementById('cache-duration');

    if (cssCompressionSelect) {
        const savedCssCompression = localStorage.getItem('css-compression') || 'enabled';
        cssCompressionSelect.value = savedCssCompression;
        cssCompressionSelect.addEventListener('change', function() {
            localStorage.setItem('css-compression', this.value);
        });
    }

    if (jsCompressionSelect) {
        const savedJsCompression = localStorage.getItem('js-compression') || 'enabled';
        jsCompressionSelect.value = savedJsCompression;
        jsCompressionSelect.addEventListener('change', function() {
            localStorage.setItem('js-compression', this.value);
        });
    }

    if (imageOptimizationSelect) {
        const savedImageOptimization = localStorage.getItem('image-optimization') || 'enabled';
        imageOptimizationSelect.value = savedImageOptimization;
        imageOptimizationSelect.addEventListener('change', function() {
            localStorage.setItem('image-optimization', this.value);
        });
    }

    if (cacheDurationInput) {
        const savedCacheDuration = localStorage.getItem('cache-duration') || '31536000';
        cacheDurationInput.value = savedCacheDuration;
        cacheDurationInput.addEventListener('change', function() {
            localStorage.setItem('cache-duration', this.value);
        });
    }

});