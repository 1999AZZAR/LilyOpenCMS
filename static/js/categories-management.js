// Categories Management JavaScript

// Global variables for bulk operations
let selectedCategories = new Set();
let allCategories = [];

// Fetch and populate categories
async function fetchCategories() {
    try {
        const response = await fetch('/api/categories?grouped=true');
        if (!response.ok) throw new Error('Failed to fetch categories');
        const groupedData = await response.json();
        
        // Flatten categories for bulk operations
        allCategories = [];
        groupedData.forEach(groupData => {
            groupData.categories.forEach(cat => {
                allCategories.push({
                    ...cat,
                    group_name: groupData.group.name
                });
            });
        });
        
        renderManageCategories(groupedData);
    } catch (error) {
        console.error(error);
        showToast('error', 'Gagal memuat kategori');
    }
}

// Render list and actions
function renderManageCategories(groupedData) {
    const list = document.getElementById('category-list'); 
    list.innerHTML = '';
    
    groupedData.forEach(groupData => {
        // Create group header
        const groupHeader = document.createElement('div');
        groupHeader.className = 'bg-gray-100 border-b border-gray-200 p-3 mb-2';
        groupHeader.setAttribute('role', 'group');
        groupHeader.setAttribute('aria-label', `Category group: ${groupData.group.name}`);
        
        const groupTitle = document.createElement('h3');
        groupTitle.className = 'text-lg font-semibold text-gray-800 flex items-center';
        groupTitle.innerHTML = `
            <i class="fas fa-folder text-blue-600 mr-2"></i>
            ${groupData.group.name}
        `;
        groupHeader.appendChild(groupTitle);
        
        if (groupData.group.description) {
            const groupDesc = document.createElement('p');
            groupDesc.className = 'text-sm text-gray-600 mt-1';
            groupDesc.textContent = groupData.group.description;
            groupHeader.appendChild(groupDesc);
        }
        
        list.appendChild(groupHeader);
        
        // Create categories in this group
        groupData.categories.forEach(cat => {
            const row = document.createElement('div');
            row.className = 'flex items-center justify-between p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 ml-4';
            row.setAttribute('role', 'listitem');
            row.setAttribute('aria-label', `Kategori: ${cat.name}`);

            // Checkbox for bulk selection
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'mr-3 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded';
            checkbox.setAttribute('aria-label', `Pilih kategori ${cat.name}`);
            checkbox.checked = selectedCategories.has(cat.id);
            checkbox.onchange = () => toggleCategorySelection(cat.id, checkbox.checked);
            row.appendChild(checkbox);

            const name = document.createElement('span');
            name.textContent = cat.name;
            name.className = 'text-gray-800 font-medium flex-1';
            row.appendChild(name);

            const btns = document.createElement('div'); 
            btns.className = 'flex space-x-3';
            btns.setAttribute('role', 'group');
            btns.setAttribute('aria-label', `Actions for category ${cat.name}`);

            // Edit Button (Icon Style)
            const editBtn = document.createElement('button');
            editBtn.innerHTML = '<i class="fas fa-edit" aria-hidden="true"></i>';
            editBtn.className = 'p-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-600 rounded-full focus:outline-none focus:ring-2 focus:ring-yellow-300';
            editBtn.setAttribute('aria-label', `Edit category ${cat.name}`);
            editBtn.title = 'Edit';
            editBtn.onclick = () => showEditModal(cat.id, cat.name, cat.group_id);
            btns.appendChild(editBtn);

            // Delete Button (Icon Style)
            const delBtn = document.createElement('button');
            delBtn.innerHTML = '<i class="fas fa-trash" aria-hidden="true"></i>';
            delBtn.className = 'p-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-full focus:outline-none focus:ring-2 focus:ring-red-300';
            delBtn.setAttribute('aria-label', `Delete category ${cat.name}`);
            delBtn.title = 'Delete';
            delBtn.onclick = () => showDeleteModal(cat.id);
            btns.appendChild(delBtn);

            row.appendChild(btns); 
            list.appendChild(row);
        });
    });
    
    updateBulkActionsToolbar();
}

// Toggle category selection for bulk operations
function toggleCategorySelection(categoryId, isSelected) {
    if (isSelected) {
        selectedCategories.add(categoryId);
    } else {
        selectedCategories.delete(categoryId);
    }
    updateBulkActionsToolbar();
}

// Update bulk actions toolbar visibility and content
function updateBulkActionsToolbar() {
    const toolbar = document.getElementById('bulk-actions-toolbar');
    const selectedCount = document.getElementById('selected-count');
    const bulkEditBtn = document.getElementById('bulk-edit-btn');
    const bulkDeleteBtn = document.getElementById('bulk-delete-btn');
    
    if (selectedCategories.size > 0) {
        toolbar.classList.remove('hidden');
        selectedCount.textContent = `${selectedCategories.size} kategori dipilih`;
        bulkEditBtn.disabled = false;
        bulkDeleteBtn.disabled = false;
    } else {
        toolbar.classList.add('hidden');
    }
}

// Select all categories
function selectAllCategories() {
    allCategories.forEach(cat => {
        selectedCategories.add(cat.id);
    });
    renderManageCategories(allCategories);
}

// Deselect all categories
function deselectAllCategories() {
    selectedCategories.clear();
    renderManageCategories(allCategories);
}

// Update category
async function updateCategory(id, name, groupId = null) {
    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name,
                group_id: groupId
            }),
        });
        if (!response.ok) throw new Error('Gagal memperbarui kategori');
        fetchCategories();
        showToast('success', 'Kategori berhasil diperbarui!');
    } catch (error) {
        showToast('error', error.message);
    }
}

// Bulk update categories
async function bulkUpdateCategories(categoryIds, newName) {
    try {
        const promises = categoryIds.map(id => 
            fetch(`/api/categories/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName }),
            })
        );
        
        const responses = await Promise.all(promises);
        const failedUpdates = responses.filter(response => !response.ok);
        
        if (failedUpdates.length > 0) {
            throw new Error(`Gagal memperbarui ${failedUpdates.length} kategori`);
        }
        
        selectedCategories.clear();
        fetchCategories();
        showToast('success', `${categoryIds.length} kategori berhasil diperbarui!`);
    } catch (error) {
        showToast('error', error.message);
    }
}

// Delete category with safe delete check
async function deleteCategory(id) {
    try {
        const response = await fetch(`/api/categories/${id}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.status === 409) {
            // Category has dependencies, show safe delete modal
            const data = await response.json();
            showSafeDeleteModal(id, data.dependencies);
            return;
        }
        
        if (!response.ok) throw new Error('Gagal menghapus kategori');
        fetchCategories();
        showToast('success', 'Kategori berhasil dihapus!');
    } catch (error) {
        showToast('error', error.message);
    }
}

// Bulk delete categories
async function bulkDeleteCategories(categoryIds) {
    try {
        const promises = categoryIds.map(id => 
            fetch(`/api/categories/${id}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            })
        );
        
        const responses = await Promise.all(promises);
        const results = await Promise.all(responses.map(async (response, index) => {
            const categoryId = categoryIds[index];
            if (response.status === 409) {
                const data = await response.json();
                return { categoryId, hasDependencies: true, dependencies: data.dependencies };
            } else if (!response.ok) {
                return { categoryId, error: true };
            } else {
                return { categoryId, success: true };
            }
        }));
        
        const successful = results.filter(r => r.success);
        const withDependencies = results.filter(r => r.hasDependencies);
        const failed = results.filter(r => r.error);
        
        let message = '';
        if (successful.length > 0) {
            message += `${successful.length} kategori berhasil dihapus. `;
        }
        if (withDependencies.length > 0) {
            message += `${withDependencies.length} kategori memiliki konten dan memerlukan reassignment. `;
        }
        if (failed.length > 0) {
            message += `${failed.length} kategori gagal dihapus.`;
        }
        
        selectedCategories.clear();
        fetchCategories();
        showToast('info', message);
        
        // If there are categories with dependencies, show safe delete for the first one
        if (withDependencies.length > 0) {
            const firstWithDeps = withDependencies[0];
            showSafeDeleteModal(firstWithDeps.categoryId, firstWithDeps.dependencies);
        }
    } catch (error) {
        showToast('error', `Gagal menghapus kategori: ${error.message}`);
    }
}

// Safe delete category with reassignment
async function safeDeleteCategory(id, newCategoryId) {
    try {
        const response = await fetch(`/api/categories/${id}/safe-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_category_id: newCategoryId }),
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Gagal menghapus kategori');
        }
        
        const data = await response.json();
        fetchCategories();
        showToast('success', `Kategori berhasil dihapus! ${data.reassigned.news_count} berita dan ${data.reassigned.album_count} album telah dipindahkan.`);
    } catch (error) {
        showToast('error', error.message);
    }
}

// Show edit modal
async function showEditModal(id, name, groupId = null) {
    document.getElementById('edit-category-id').value = id;
    document.getElementById('edit-category-name').value = name;
    
    // Populate group select
    await populateGroupSelect();
    
    // Set selected group
    const groupSelect = document.getElementById('edit-category-group');
    groupSelect.value = groupId || '';
    
    document.getElementById('edit-category-modal').classList.remove('hidden');
}

// Populate group select
async function populateGroupSelect() {
    try {
        const response = await fetch('/api/category-groups');
        if (!response.ok) throw new Error('Failed to fetch category groups');
        const groups = await response.json();
        
        const select = document.getElementById('edit-category-group');
        select.innerHTML = '<option value="">Tanpa Grup</option>';
        
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to populate group select:', error);
        showToast('error', 'Gagal memuat daftar grup kategori');
    }
}

// Populate add category group select
async function populateAddCategoryGroupSelect() {
    try {
        const response = await fetch('/api/category-groups');
        if (!response.ok) throw new Error('Failed to fetch category groups');
        const groups = await response.json();
        
        const select = document.getElementById('category-group');
        select.innerHTML = '<option value="">Tanpa Grup</option>';
        
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to populate add category group select:', error);
        showToast('error', 'Gagal memuat daftar grup kategori');
    }
}

// Show delete modal
function showDeleteModal(id) {
    document.getElementById('delete-category-id').value = id;
    document.getElementById('delete-category-modal').classList.remove('hidden');
}

// Show bulk edit modal
function showBulkEditModal() {
    const selectedCount = selectedCategories.size;
    document.getElementById('bulk-edit-info').textContent = `Edit ${selectedCount} kategori yang dipilih`;
    document.getElementById('bulk-edit-name').value = '';
    document.getElementById('bulk-edit-modal').classList.remove('hidden');
}

// Show bulk delete modal
function showBulkDeleteModal() {
    const selectedCount = selectedCategories.size;
    document.getElementById('bulk-delete-info').textContent = `Anda akan menghapus ${selectedCount} kategori yang dipilih`;
    document.getElementById('bulk-delete-modal').classList.remove('hidden');
}

// Show safe delete modal
function showSafeDeleteModal(id, dependencies) {
    document.getElementById('safe-delete-category-id').value = id;
    
    // Update dependency text
    const dependencyText = document.getElementById('dependency-text');
    const parts = [];
    if (dependencies.news_count > 0) {
        parts.push(`${dependencies.news_count} berita`);
    }
    if (dependencies.album_count > 0) {
        parts.push(`${dependencies.album_count} album`);
    }
    dependencyText.textContent = parts.join(' dan ');
    
    // Populate category select
    populateCategorySelect(id);
    
    document.getElementById('safe-delete-category-modal').classList.remove('hidden');
}

// Populate category select for safe delete
async function populateCategorySelect(excludeId) {
    try {
        const response = await fetch('/api/categories');
        if (!response.ok) throw new Error('Failed to fetch categories');
        const categories = await response.json();
        
        const select = document.getElementById('new-category-select');
        select.innerHTML = '<option value="">Pilih kategori...</option>';
        
        categories.forEach(cat => {
            if (cat.id != excludeId) {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                select.appendChild(option);
            }
        });
    } catch (error) {
        console.error('Failed to populate category select:', error);
        showToast('error', 'Gagal memuat daftar kategori');
    }
}

// Close modals
function closeEditModal() {
    document.getElementById('edit-category-modal').classList.add('hidden');
}

function closeDeleteModal() {
    document.getElementById('delete-category-modal').classList.add('hidden');
}

function closeSafeDeleteModal() {
    document.getElementById('safe-delete-category-modal').classList.add('hidden');
}

function closeBulkEditModal() {
    document.getElementById('bulk-edit-modal').classList.add('hidden');
}

function closeBulkDeleteModal() {
    document.getElementById('bulk-delete-modal').classList.add('hidden');
}

// Initialize categories management
document.addEventListener('DOMContentLoaded', async () => {
    // Load categories and populate group selects on page load
    await Promise.all([
        fetchCategories(),
        populateGroupSelect(),
        populateAddCategoryGroupSelect()
    ]);
    
    // Add new category form handler
    document.getElementById('add-category').addEventListener('submit', async (e) => {
        e.preventDefault();
        const categoryName = document.getElementById('category-name').value.trim();
        const groupId = document.getElementById('category-group').value || null;
        
        if (!categoryName) { 
            showToast('warning', 'Nama kategori diperlukan'); 
            return; 
        }
        
        try {
            const response = await fetch('/api/categories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: categoryName,
                    group_id: groupId
                }),
            });
            if (!response.ok) { 
                const err = await response.json(); 
                throw new Error(err.error || 'Failed to add category'); 
            }
            showToast('success', 'Kategori berhasil ditambahkan!');
            fetchCategories(); 
            document.getElementById('category-name').value = '';
            document.getElementById('category-group').value = '';
        } catch (error) {
            showToast('error', `Gagal menambahkan kategori: ${error.message}`);
        }
    });

    // Edit category form handler
    document.getElementById('edit-category-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit-category-id').value;
        const name = document.getElementById('edit-category-name').value.trim();
        const groupId = document.getElementById('edit-category-group').value || null;
        
        if (!name) {
            showToast('warning', 'Nama kategori diperlukan');
            return;
        }
        await updateCategory(id, name, groupId);
        closeEditModal();
    });

    // Cancel edit button
    document.getElementById('cancel-edit-btn').addEventListener('click', () => {
        closeEditModal();
    });

    // Delete category confirmation
    document.getElementById('confirm-delete-category-btn').addEventListener('click', async () => {
        const id = document.getElementById('delete-category-id').value;
        await deleteCategory(id);
        closeDeleteModal();
    });

    // Cancel delete button
    document.getElementById('cancel-delete-btn').addEventListener('click', () => {
        closeDeleteModal();
    });

    // Safe delete category confirmation
    document.getElementById('confirm-safe-delete-btn').addEventListener('click', async () => {
        const id = document.getElementById('safe-delete-category-id').value;
        const newCategoryId = document.getElementById('new-category-select').value;
        
        if (!newCategoryId) {
            showToast('warning', 'Pilih kategori baru untuk reassignment');
            return;
        }
        
        await safeDeleteCategory(id, newCategoryId);
        closeSafeDeleteModal();
    });

    // Cancel safe delete button
    document.getElementById('cancel-safe-delete-btn').addEventListener('click', () => {
        closeSafeDeleteModal();
    });

    // Bulk operations
    document.getElementById('select-all-btn').addEventListener('click', () => {
        selectAllCategories();
    });

    document.getElementById('deselect-all-btn').addEventListener('click', () => {
        deselectAllCategories();
    });

    document.getElementById('bulk-edit-btn').addEventListener('click', () => {
        showBulkEditModal();
    });

    document.getElementById('bulk-delete-btn').addEventListener('click', () => {
        showBulkDeleteModal();
    });

    // Bulk edit confirmation
    document.getElementById('confirm-bulk-edit-btn').addEventListener('click', async () => {
        const newName = document.getElementById('bulk-edit-name').value.trim();
        if (!newName) {
            showToast('warning', 'Nama kategori diperlukan');
            return;
        }
        
        const categoryIds = Array.from(selectedCategories);
        await bulkUpdateCategories(categoryIds, newName);
        closeBulkEditModal();
    });

    // Cancel bulk edit button
    document.getElementById('cancel-bulk-edit-btn').addEventListener('click', () => {
        closeBulkEditModal();
    });

    // Bulk delete confirmation
    document.getElementById('confirm-bulk-delete-btn').addEventListener('click', async () => {
        const categoryIds = Array.from(selectedCategories);
        await bulkDeleteCategories(categoryIds);
        closeBulkDeleteModal();
    });

    // Cancel bulk delete button
    document.getElementById('cancel-bulk-delete-btn').addEventListener('click', () => {
        closeBulkDeleteModal();
    });

    // Close modals when clicking outside
    document.getElementById('edit-category-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeEditModal();
        }
    });

    document.getElementById('delete-category-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeDeleteModal();
        }
    });

    document.getElementById('safe-delete-category-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeSafeDeleteModal();
        }
    });

    document.getElementById('bulk-edit-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeBulkEditModal();
        }
    });

    document.getElementById('bulk-delete-modal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeBulkDeleteModal();
        }
    });
});