// Album Management JavaScript for Admin List Page
// Handles album deletion requests and other album management functions

// Request album deletion (for all users)
async function requestAlbumDeletion(albumId) {
    console.log('requestAlbumDeletion called with album ID:', albumId);
    
    showConfirmModal(
        'Permintaan Penghapusan Album',
        'Apakah Anda yakin ingin mengirim permintaan penghapusan album ini? Permintaan akan ditinjau oleh administrator.',
        () => {
            submitAlbumDeletionRequest(albumId);
        }
    );
}

// Submit album deletion request
async function submitAlbumDeletionRequest(albumId) {
    try {
        console.log('Making API call to request deletion for album:', albumId);
        const response = await fetch(`/admin/albums/${albumId}/request-deletion`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            // Check if response is JSON or HTML
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to request deletion');
            } else {
                // Handle HTML response (likely redirect to login)
                throw new Error('Session expired. Please refresh the page and try again.');
            }
        }

        const data = await response.json();
        
        // Use toast if available, otherwise use alert
        if (typeof showToast === 'function') {
            showToast('success', data.message || 'Permintaan penghapusan berhasil dikirim. Administrator akan meninjau permintaan Anda.');
        } else {
            alert('Success: ' + (data.message || 'Permintaan penghapusan berhasil dikirim.'));
        }
        
        closeConfirmModal();
        // Refresh the page to show updated status
        location.reload();
        
    } catch (error) {
        console.error('Error requesting album deletion:', error);
        // Use toast if available, otherwise use alert
        if (typeof showToast === 'function') {
            showToast('error', 'Gagal mengirim permintaan penghapusan: ' + error.message);
        } else {
            alert('Error: ' + error.message);
        }
    }
}

// Toggle album visibility
async function toggleAlbumVisibility(albumId) {
    try {
        const response = await fetch(`/admin/albums/${albumId}/toggle-visibility`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    }
}

// Toggle album type (premium/regular)
async function toggleAlbumType(albumId) {
    try {
        const response = await fetch(`/admin/albums/${albumId}/toggle-type`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    }
}

// Bulk actions
function bulkToggleVisibility() {
    const selectedIds = getSelectedAlbumIds();
    if (selectedIds.length === 0) return;
    
    fetch('/admin/albums/bulk/toggle-visibility', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ album_ids: selectedIds })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    });
}

function bulkToggleType() {
    const selectedIds = getSelectedAlbumIds();
    if (selectedIds.length === 0) return;
    
    fetch('/admin/albums/bulk/toggle-type', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ album_ids: selectedIds })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    });
}

function bulkArchive() {
    const selectedIds = getSelectedAlbumIds();
    if (selectedIds.length === 0) return;
    
    if (!confirm(`Apakah Anda yakin ingin mengarsipkan ${selectedIds.length} album(s)?`)) {
        return;
    }
    
    fetch('/admin/albums/bulk/archive', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ album_ids: selectedIds })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error: ' + error.message);
    });
}

function getSelectedAlbumIds() {
    const selectedCheckboxes = document.querySelectorAll('.album-checkbox:checked');
    return Array.from(selectedCheckboxes).map(checkbox => checkbox.value);
}

// Bulk selection functionality
function updateBulkActions() {
    const selectedCheckboxes = document.querySelectorAll('.album-checkbox:checked');
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    
    if (selectedCheckboxes.length > 0) {
        bulkActions.classList.remove('hidden');
        selectedCount.textContent = selectedCheckboxes.length;
    } else {
        bulkActions.classList.add('hidden');
    }
}

function clearSelection() {
    document.getElementById('select-all').checked = false;
    document.querySelectorAll('.album-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    updateBulkActions();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Setup bulk selection
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.album-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }

    // Setup individual checkboxes
    document.querySelectorAll('.album-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActions);
    });
});
