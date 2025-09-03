// DOCX Upload JavaScript

// Add global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
});

// Try to set up form handling immediately
function setupFormHandling() {
    const form = document.getElementById('docxUploadForm');
    const fileInput = document.getElementById('docxFile');
    const fileName = document.getElementById('fileName');
    const fileInfo = document.getElementById('fileInfo');
    const removeFile = document.getElementById('removeFile');
    const submitBtn = document.getElementById('submitBtn');
    
    if (!form) {
        return false;
    }
    
    // Set up form submission
    form.addEventListener('submit', handleFormSubmit);
    
    // Set up file handling
    if (fileInput && fileName && fileInfo) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            
            if (file) {
                updateFileDisplay(file);
            }
        });
    }
    
    // Set up remove file
    if (removeFile) {
        removeFile.addEventListener('click', function() {
            clearFileSelection();
        });
    }
    
    return true;
}

// Try immediately
if (!setupFormHandling()) {
    // If not ready, wait for DOM
    document.addEventListener('DOMContentLoaded', function() {
        setupFormHandling();
    });
}


    
    // Set today's date as default
    const dateInput = document.getElementById('date');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
    
    // Functions
    function updateFileDisplay(file) {
        const fileName = document.getElementById('fileName');
        const fileInfo = document.getElementById('fileInfo');
        const removeFile = document.getElementById('removeFile');
        
        // Update filename
        if (fileName) {
            fileName.textContent = file.name;
            fileName.className = 'text-base font-bold text-green-900';
        }
        
        // Update file info box
        if (fileInfo) {
            fileInfo.className = 'mt-3 p-4 bg-green-50 border-2 border-green-300 rounded-lg';
            const icon = fileInfo.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-file-word text-green-600 mr-3 text-lg';
            }
            const label = fileInfo.querySelector('p:first-of-type');
            if (label) {
                label.className = 'text-sm font-semibold text-green-800';
            }
        }
        
        // Show remove button
        if (removeFile) {
            removeFile.classList.remove('hidden');
            removeFile.className = 'text-green-600 hover:text-green-800 p-2 rounded-full hover:bg-green-100';
        }
        
        // Don't auto-fill title - let the backend extract it from document content
        

    }
    
    function clearFileSelection() {
        const fileInput = document.getElementById('docxFile');
        const fileName = document.getElementById('fileName');
        const fileInfo = document.getElementById('fileInfo');
        const removeFile = document.getElementById('removeFile');
        
        if (fileInput) {
            fileInput.value = '';
        }
        if (fileName) {
            fileName.textContent = 'Belum ada file dipilih';
            fileName.className = 'text-base font-bold text-gray-700';
        }
        if (fileInfo) {
            fileInfo.className = 'mt-3 p-4 bg-gray-50 border-2 border-gray-200 rounded-lg';
            const icon = fileInfo.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-file-word text-gray-400 mr-3 text-lg';
            }
            const label = fileInfo.querySelector('p:first-of-type');
            if (label) {
                label.className = 'text-sm font-semibold text-gray-600';
            }
        }
        if (removeFile) {
            removeFile.classList.add('hidden');
        }
        

    }
    
    function showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(toast => toast.remove());
        
        const toast = document.createElement('div');
        toast.className = `toast-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
        
        let bgColor, textColor, icon;
        switch(type) {
            case 'success':
                bgColor = 'bg-green-500';
                textColor = 'text-white';
                icon = 'fas fa-check-circle';
                break;
            case 'error':
                bgColor = 'bg-red-500';
                textColor = 'text-white';
                icon = 'fas fa-exclamation-circle';
                break;
            case 'warning':
                bgColor = 'bg-yellow-500';
                textColor = 'text-white';
                icon = 'fas fa-exclamation-triangle';
                break;
            default:
                bgColor = 'bg-blue-500';
                textColor = 'text-white';
                icon = 'fas fa-info-circle';
        }
        
        toast.innerHTML = `
            <div class="flex items-center ${bgColor} ${textColor} p-3 rounded-lg">
                <i class="${icon} mr-3"></i>
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('translate-x-full');
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }
    
    function clearForm() {
        const form = document.getElementById('docxUploadForm');
        const dateInput = document.getElementById('date');
        
        if (form) {
            form.reset();
        }
        clearFileSelection();
        
        // Reset date to today
        if (dateInput) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
        

    }
    
    async function handleFormSubmit(e) {
        e.preventDefault();
        
        const fileInput = document.getElementById('docxFile');
        const submitBtn = document.getElementById('submitBtn');
        const form = document.getElementById('docxUploadForm');
        
        if (!fileInput.files[0]) {
            showToast('Silakan pilih file DOCX terlebih dahulu.', 'error');
            return;
        }
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Memproses...';
        }
        
        try {
            const formData = new FormData(form);
            
            // Ensure visibility is set to hidden (draft)
            formData.set('is_visible', 'false');
            const response = await fetch('/api/news/upload-docx', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showToast('Draft artikel berhasil dibuat! Artikel tersimpan sebagai draft dan tidak terlihat publik.', 'success');
                clearForm();
            } else {
                showToast(data.error || 'Terjadi kesalahan saat upload.', 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showToast('Terjadi kesalahan saat upload.', 'error');
        } finally {
            // Reset button state
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-upload mr-2"></i>Upload & Buat Draft';
            }
        }
    }
    

