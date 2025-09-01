// Users Management JavaScript
class UsersManagement {
    constructor() {
        this.currentUser = null;
        this.users = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.currentUserId = null;
        this.init();
    }

    init() {
    // Set current user data from template
    if (typeof window.currentUserData !== 'undefined') {
            this.currentUser = window.currentUserData;
        }
        
        this.bindEvents();
        this.initTabs();
        this.loadUsers();
        this.loadRoleStats(); // Load role statistics
    }

    bindEvents() {
        // Search and filter handlers
        const searchInput = document.getElementById('search');
        const roleFilter = document.getElementById('role-filter');
        const statusFilter = document.getElementById('status-filter');
        const verificationFilter = document.getElementById('verification-filter');
        
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => this.loadUsers(1), 500));
        }
        
        if (roleFilter) {
            roleFilter.addEventListener('change', () => this.loadUsers(1));
        }
        
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.loadUsers(1));
        }
        
        if (verificationFilter) {
            verificationFilter.addEventListener('change', () => this.loadUsers(1));
        }
        
        // Performance period handler
        const performancePeriod = document.getElementById('performance-period');
        if (performancePeriod) {
            performancePeriod.addEventListener('change', () => this.loadPerformanceData());
        }
        
        // Export buttons
        const exportUsersBtn = document.getElementById('export-users-btn');
        if (exportUsersBtn) {
            exportUsersBtn.addEventListener('click', () => this.exportUsers());
        }
        
        const exportPerformanceBtn = document.getElementById('export-performance-btn');
        if (exportPerformanceBtn) {
            exportPerformanceBtn.addEventListener('click', () => this.exportPerformance());
        }
        
        const exportRolesBtn = document.getElementById('export-roles-btn');
        if (exportRolesBtn) {
            exportRolesBtn.addEventListener('click', () => this.exportRoles());
        }
        
        // Active/Suspended checkbox interactions
        const activeCheckbox = document.getElementById('edit-is-active');
        const suspendedCheckbox = document.getElementById('edit-is-suspended');
        
        if (activeCheckbox && suspendedCheckbox) {
            activeCheckbox.addEventListener('change', () => {
                if (activeCheckbox.checked) {
                    suspendedCheckbox.checked = false;
                    this.toggleSuspensionDetails(false);
                }
            });
            
            suspendedCheckbox.addEventListener('change', () => {
                if (suspendedCheckbox.checked) {
                    activeCheckbox.checked = false;
                    this.toggleSuspensionDetails(true);
                } else {
                    this.toggleSuspensionDetails(false);
                }
            });
        }

        // Bulk actions
        const bulkActionsBtn = document.getElementById('bulk-actions-btn');
        if (bulkActionsBtn) {
            bulkActionsBtn.addEventListener('click', () => this.toggleBulkActions());
        }

        // Form handlers
        this.initFormHandlers();
        
        // Deletion requests handlers
        const deletionSearch = document.getElementById('deletion-search');
        const deletionDateFilter = document.getElementById('deletion-date-filter');
        const bulkApproveDeletionBtn = document.getElementById('bulk-approve-deletion-btn');
        const bulkRejectDeletionBtn = document.getElementById('bulk-reject-deletion-btn');
        
        if (deletionSearch) {
            deletionSearch.addEventListener('input', this.debounce(() => this.loadDeletionRequests(), 500));
        }
        
        if (deletionDateFilter) {
            deletionDateFilter.addEventListener('change', () => this.loadDeletionRequests());
        }
        
        if (bulkApproveDeletionBtn) {
            bulkApproveDeletionBtn.addEventListener('click', () => this.bulkApproveDeletions());
        }
        
        if (bulkRejectDeletionBtn) {
            bulkRejectDeletionBtn.addEventListener('click', () => this.bulkRejectDeletions());
        }
    }

    initTabs() {
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
                
                // Load specific data for the tab if needed
                this.loadTabData(targetTab);
            });
        });
    }

    loadTabData(tabName) {
        switch(tabName) {
            case 'users':
                this.loadUsers();
                this.loadUserStats();
                break;
            case 'roles':
                this.loadRoles();
                this.loadRoleStats();
                break;
            case 'pending':
                this.loadPendingUsers();
                this.loadPendingStats();
                break;
            case 'deletion-requests':
                this.loadDeletionRequests();
                break;
            case 'performance':
                this.loadPerformanceData();
                break;
        }
    }

    async loadUsers(page = 1) {
        try {
            const search = document.getElementById('search')?.value || '';
        const role = document.getElementById('role-filter')?.value || '';
        const status = document.getElementById('status-filter')?.value || '';
            const verification = document.getElementById('verification-filter')?.value || '';
        
        const params = new URLSearchParams({
            page: page,
            search: search,
            role: role,
                status: status,
                verification: verification
        });
        
            const response = await fetch(`/api/users?${params}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', response.status, errorText);
                throw new Error(`Failed to fetch users: ${response.status} ${errorText}`);
            }
        
        const data = await response.json();
            
            // Handle new API response format with pagination
            if (data.users && Array.isArray(data.users)) {
                this.users = data.users;
                this.pagination = data.pagination || {};
                this.currentPage = page;
            } else {
                // Fallback for old format
                this.users = Array.isArray(data) ? data : [];
                this.pagination = {};
                this.currentPage = page;
            }
            
            this.renderUsers();
            this.renderPagination();
            this.loadUserStats(); // Load statistics after users
    } catch (error) {
            console.error('Error loading users:', error);
            this.showToast('error', 'Gagal memuat daftar pengguna');
            this.showErrorInContainers(error.message);
        }
    }

    async loadUserStats() {
        try {
            const response = await fetch('/api/users/stats');
            if (!response.ok) {
                throw new Error('Failed to fetch user statistics');
            }
            
            const stats = await response.json();
            
            // Update statistics display
            const totalUsersElement = document.getElementById('total-users-count');
            const activeUsersElement = document.getElementById('active-users-count');
            const premiumUsersElement = document.getElementById('premium-users-count');
            const pendingUsersElement = document.getElementById('pending-users-count');
            
            if (totalUsersElement) totalUsersElement.textContent = stats.total_users || 0;
            if (activeUsersElement) activeUsersElement.textContent = stats.active_users || 0;
            if (premiumUsersElement) premiumUsersElement.textContent = stats.premium_users || 0;
            if (pendingUsersElement) pendingUsersElement.textContent = stats.pending_users || 0;
            
        } catch (error) {
            console.error('Error loading user statistics:', error);
        }
    }

    async loadRoleStats() {
        try {
            const response = await fetch('/api/roles');
            if (!response.ok) {
                throw new Error('Failed to fetch roles');
            }
            
            const roles = await response.json();
            
            // Update role statistics
            const totalRolesElement = document.getElementById('total-roles-count');
            const activeRolesElement = document.getElementById('active-roles-count');
            const totalPermissionsElement = document.getElementById('total-permissions-count');
            
            if (totalRolesElement) totalRolesElement.textContent = roles.length || 0;
            if (activeRolesElement) {
                const activeRoles = roles.filter(role => role.is_active).length;
                activeRolesElement.textContent = activeRoles;
            }
            
            // Load permissions count
            const permissionsResponse = await fetch('/api/permissions');
            if (permissionsResponse.ok) {
                const permissions = await permissionsResponse.json();
                if (totalPermissionsElement) totalPermissionsElement.textContent = permissions.length || 0;
            }
            
        } catch (error) {
            console.error('Error loading role statistics:', error);
        }
    }

    async loadPendingStats() {
        try {
            const response = await fetch('/api/pending/stats');
            if (!response.ok) {
                throw new Error('Failed to fetch pending statistics');
            }
            
            const stats = await response.json();
            
            // Update pending statistics
            const totalPendingElement = document.getElementById('total-pending-count');
            const approvedTodayElement = document.getElementById('approved-today-count');
            const rejectedTodayElement = document.getElementById('rejected-today-count');
            const avgApprovalTimeElement = document.getElementById('avg-approval-time');
            
            if (totalPendingElement) totalPendingElement.textContent = stats.total_pending || 0;
            if (approvedTodayElement) approvedTodayElement.textContent = stats.approved_today || 0;
            if (rejectedTodayElement) rejectedTodayElement.textContent = stats.rejected_today || 0;
            if (avgApprovalTimeElement) avgApprovalTimeElement.textContent = `${stats.avg_approval_time || 0} jam`;
            
        } catch (error) {
            console.error('Error loading pending statistics:', error);
        }
    }

    renderUsers() {
        const adminContainer = document.getElementById('admin-users');
        const generalContainer = document.getElementById('general-users');
        
        if (!adminContainer || !generalContainer) {
            console.error('User containers not found');
            return;
        }
        
        // Clear containers
        adminContainer.innerHTML = '';
        generalContainer.innerHTML = '';
        
        // Separate users by role
        const adminUsers = this.users.filter(user => user.role === 'su' || user.role === 'admin');
        const generalUsers = this.users.filter(user => user.role === 'general');
        
        // Render admin users
        if (adminUsers.length === 0) {
            adminContainer.innerHTML = '<div class="col-span-full text-amber-600">Tidak ada pengguna admin</div>';
        } else {
            adminUsers.forEach(user => {
                const userCard = this.createUserCard(user);
                adminContainer.appendChild(userCard);
            });
        }
        
        // Render general users
        if (generalUsers.length === 0) {
            generalContainer.innerHTML = '<div class="col-span-full text-amber-600">Tidak ada pengguna umum</div>';
        } else {
            generalUsers.forEach(user => {
                const userCard = this.createUserCard(user);
                generalContainer.appendChild(userCard);
            });
        }
    }

    createUserCard(user) {
    const card = document.createElement('div');
        card.className = 'bg-white border border-amber-200 rounded-lg p-4 hover:shadow-md transition-shadow';
    card.setAttribute('role', 'listitem');
    card.setAttribute('aria-label', `User: ${user.username}`);
    
        // Status and role badges
    const statusClass = user.is_suspended ? 'text-red-600 bg-red-100' : 'text-green-600 bg-green-100';
    const statusText = user.is_suspended ? 'Tersuspend' : 'Aktif';
        
        // Enhanced role display
        let roleBadge = '';
        if (user.role === 'su') {
            roleBadge = '<span class="px-2 py-1 text-xs rounded-full bg-red-100 text-red-600">Superuser</span>';
        } else if (user.role === 'admin') {
            roleBadge = '<span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-600">Admin</span>';
        } else {
            roleBadge = '<span class="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">Umum</span>';
        }
        
        // Custom role badge if exists
        let customRoleBadge = '';
        if (user.custom_role && user.custom_role.name) {
            customRoleBadge = `<span class="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-600">${user.custom_role.name}</span>`;
        }
        
        // Additional info
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
        const displayName = fullName || user.username;
    
    card.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-gradient-to-r from-amber-400 to-yellow-400 rounded-full flex items-center justify-center">
                    <span class="text-white font-semibold text-sm">${user.username.charAt(0).toUpperCase()}</span>
                </div>
                    <div class="flex-1">
                        <h3 class="font-semibold text-amber-800">${displayName}</h3>
                        <p class="text-sm text-amber-600">${user.email || 'Tidak ada email'}</p>
                        ${user.bio ? `<p class="text-xs text-gray-500 mt-1">${user.bio.substring(0, 50)}${user.bio.length > 50 ? '...' : ''}</p>` : ''}
                        <div class="flex items-center space-x-2 mt-2 flex-wrap gap-1">
                        <span class="px-2 py-1 text-xs rounded-full ${statusClass}">${statusText}</span>
                            ${roleBadge}
                            ${customRoleBadge}
                            ${user.verified ? '<span class="px-2 py-1 text-xs rounded-full bg-green-100 text-green-600">✓ Terverifikasi</span>' : ''}
                            ${user.is_premium ? '<span class="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-600">⭐ Premium</span>' : ''}
                        </div>
                </div>
            </div>
            <div class="flex space-x-2">
                    <button onclick="usersManagement.openEditUserModal(${user.id})" class="p-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-600 rounded-full focus:outline-none focus:ring-2 focus:ring-yellow-300 transition-colors" title="Edit User">
                    <i class="fas fa-edit"></i>
                </button>
                    <button onclick="usersManagement.showDeleteUserModal(${user.id})" class="p-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-full focus:outline-none focus:ring-2 focus:ring-red-300 transition-colors" title="Delete User">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
    
    return card;
}

renderPagination() {
    const paginationContainer = document.getElementById('users-pagination');
    if (!paginationContainer || !this.pagination) {
        return;
    }
    
    const { page, pages, has_next, has_prev } = this.pagination;
    
    if (pages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let paginationHTML = '<nav class="flex items-center space-x-2" aria-label="Navigasi halaman pengguna">';
    
    // Previous button
    if (has_prev) {
        paginationHTML += `
            <button onclick="usersManagement.loadUsers(${page - 1})" 
                    class="px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;
    } else {
        paginationHTML += `
            <span class="px-3 py-2 bg-gray-100 text-gray-400 rounded-lg cursor-not-allowed">
                <i class="fas fa-chevron-left"></i>
            </span>
        `;
    }
    
    // Page numbers
    const startPage = Math.max(1, page - 2);
    const endPage = Math.min(pages, page + 2);
    
    if (startPage > 1) {
        paginationHTML += `
            <button onclick="usersManagement.loadUsers(1)" 
                    class="px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors">
                1
            </button>
        `;
        if (startPage > 2) {
            paginationHTML += '<span class="px-2 text-amber-600">...</span>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        if (i === page) {
            paginationHTML += `
                <span class="px-3 py-2 bg-amber-500 text-white rounded-lg font-semibold">
                    ${i}
                </span>
            `;
        } else {
            paginationHTML += `
                <button onclick="usersManagement.loadUsers(${i})" 
                        class="px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors">
                    ${i}
                </button>
            `;
        }
    }
    
    if (endPage < pages) {
        if (endPage < pages - 1) {
            paginationHTML += '<span class="px-2 text-amber-600">...</span>';
        }
        paginationHTML += `
            <button onclick="usersManagement.loadUsers(${pages})" 
                    class="px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors">
                ${pages}
            </button>
        `;
    }
    
    // Next button
    if (has_next) {
        paginationHTML += `
            <button onclick="usersManagement.loadUsers(${page + 1})" 
                    class="px-3 py-2 bg-amber-100 hover:bg-amber-200 text-amber-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
    } else {
        paginationHTML += `
            <span class="px-3 py-2 bg-gray-100 text-gray-400 rounded-lg cursor-not-allowed">
                <i class="fas fa-chevron-right"></i>
            </span>
        `;
    }
    
    paginationHTML += '</nav>';
    paginationContainer.innerHTML = paginationHTML;
}

    showErrorInContainers(errorMessage) {
        const adminContainer = document.getElementById('admin-users');
        const generalContainer = document.getElementById('general-users');
        
        if (adminContainer) {
            adminContainer.innerHTML = `<div class="col-span-full text-red-600">Error: ${errorMessage}</div>`;
        }
        if (generalContainer) {
            generalContainer.innerHTML = `<div class="col-span-full text-red-600">Error: ${errorMessage}</div>`;
        }
    }

    initFormHandlers() {
    // Edit user form
    const editForm = document.getElementById('edit-user-form');
    if (editForm) {
            editForm.addEventListener('submit', (e) => this.handleEditUser(e));
    }
    
    // Create user form
    const createUserForm = document.getElementById('create-user-form');
    if (createUserForm) {
        createUserForm.addEventListener('submit', (e) => this.handleCreateUser(e));
    }
    
    // Password reset form
    const passwordResetForm = document.getElementById('password-reset-form');
    if (passwordResetForm) {
        passwordResetForm.addEventListener('submit', (e) => this.handlePasswordReset(e));
    }
    
    // Create role form
    const createRoleForm = document.getElementById('create-role-form');
    if (createRoleForm) {
            createRoleForm.addEventListener('submit', (e) => this.handleCreateRole(e));
        }
        
        // Edit role form
        const editRoleForm = document.getElementById('edit-role-form');
        if (editRoleForm) {
            editRoleForm.addEventListener('submit', (e) => this.handleEditRole(e));
        }
    }

    async handleEditUser(e) {
    e.preventDefault();
        
        const isActive = document.getElementById('edit-is-active').checked;
        const isSuspended = document.getElementById('edit-is-suspended').checked;
        
        // If active is checked, force suspended to be false
        const finalSuspendedStatus = isActive ? false : isSuspended;
    
    const formData = {
        username: document.getElementById('edit-username').value.trim(),
        email: document.getElementById('edit-email').value.trim(),
            first_name: document.getElementById('edit-first-name').value.trim(),
            last_name: document.getElementById('edit-last-name').value.trim(),
            bio: document.getElementById('edit-bio').value.trim(),
        role: document.getElementById('edit-role').value,
        is_verified: document.getElementById('edit-verified').checked,
            is_suspended: finalSuspendedStatus,
        is_premium: document.getElementById('edit-is-premium').checked,
        suspension_reason: document.getElementById('edit-suspension-reason').value.trim(),
            suspension_until: document.getElementById('edit-suspension-until').value,
            custom_role_id: document.getElementById('edit-custom-role').value || null
    };
    
    try {
            const response = await fetch(`/api/users/${this.currentUserId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update user');
        }
        
            this.showToast('success', 'Pengguna berhasil diperbarui!');
            this.closeEditUserModal();
            this.loadUsers(this.currentPage);
    } catch (error) {
            this.showToast('error', `Gagal memperbarui pengguna: ${error.message}`);
    }
}

async handleCreateUser(e) {
    e.preventDefault();
    
    const formData = {
        username: document.getElementById('create-username').value.trim(),
        email: document.getElementById('create-email').value.trim(),
        password: document.getElementById('create-password').value,
        first_name: document.getElementById('create-first-name').value.trim(),
        last_name: document.getElementById('create-last-name').value.trim(),
        bio: document.getElementById('create-bio').value.trim(),
        role: document.getElementById('create-role').value,
        custom_role: document.getElementById('create-custom-role').value || null,
        is_active: document.getElementById('create-is-active').checked,
        verified: document.getElementById('create-verified').checked,
        is_premium: document.getElementById('create-is-premium').checked,
        premium_duration: document.getElementById('create-premium-duration').value,
        send_welcome_email: document.getElementById('create-send-email').checked
    };
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create user');
        }
        
        const result = await response.json();
        this.showToast('success', 'Pengguna berhasil dibuat!');
        this.closeCreateUserModal();
        this.loadUsers(1); // Reload users to show the new user
        this.loadUserStats(); // Reload statistics
    } catch (error) {
        this.showToast('error', `Gagal membuat pengguna: ${error.message}`);
    }
}

async handlePasswordReset(e) {
    e.preventDefault();
    
    const formData = {
        new_password: document.getElementById('reset-password').value,
        send_email: document.getElementById('reset-send-email').checked
    };
    
    try {
        const response = await fetch(`/api/users/${this.currentUserId}/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to reset password');
        }
        
        this.showToast('success', 'Password berhasil direset!');
        this.closePasswordResetModal();
    } catch (error) {
        this.showToast('error', `Gagal reset password: ${error.message}`);
    }
}

    async handleCreateRole(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('role-name').value.trim(),
        description: document.getElementById('role-description').value.trim(),
            is_active: true,
            permission_ids: this.getSelectedPermissions()
    };
    
    try {
        const response = await fetch('/api/roles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create role');
        }
        
            this.showToast('success', 'Peran berhasil dibuat!');
            this.closeCreateRoleModal();
            this.loadRoles();
    } catch (error) {
            this.showToast('error', `Gagal membuat peran: ${error.message}`);
    }
}

    getSelectedPermissions() {
    const checkboxes = document.querySelectorAll('#permissions-list input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

    openEditUserModal(userId) {
        this.currentUserId = userId;
        const user = this.users.find(u => u.id === userId);
        if (!user) {
            this.showToast('error', 'User tidak ditemukan');
            return;
        }

        // Populate form fields with enhanced data handling
        document.getElementById('edit-username').value = user.username || '';
        document.getElementById('edit-email').value = user.email || '';
        document.getElementById('edit-first-name').value = user.first_name || '';
        document.getElementById('edit-last-name').value = user.last_name || '';
        document.getElementById('edit-bio').value = user.bio || '';
        document.getElementById('edit-role').value = user.role || 'user';
        document.getElementById('edit-verified').checked = user.verified || false;
        document.getElementById('edit-is-active').checked = !user.is_suspended; // Active is opposite of suspended
        document.getElementById('edit-is-suspended').checked = user.is_suspended || false;
        document.getElementById('edit-is-premium').checked = user.is_premium || false;
    document.getElementById('edit-suspension-reason').value = user.suspension_reason || '';
        
        // Format datetime for datetime-local input (YYYY-MM-DDTHH:MM)
        let suspensionUntil = '';
        if (user.suspension_until) {
            const date = new Date(user.suspension_until);
            if (!isNaN(date.getTime())) {
                // Format as YYYY-MM-DDTHH:MM for datetime-local input
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                suspensionUntil = `${year}-${month}-${day}T${hours}:${minutes}`;
            }
        }
        document.getElementById('edit-suspension-until').value = suspensionUntil;

        // Populate custom role dropdown with proper handling
        const customRoleId = user.custom_role_id || user.custom_role?.id || null;
        this.populateCustomRoleDropdown(customRoleId);
    
    // Show/hide suspension details
        this.toggleSuspensionDetails(user.is_suspended);
    
        // Show modal
    document.getElementById('edit-user-modal').classList.remove('hidden');
        

    }

    async populateCustomRoleDropdown(selectedRoleId = null) {
        try {
            const response = await fetch('/api/roles');
            if (response.ok) {
                const roles = await response.json();
                const dropdown = document.getElementById('edit-custom-role');
                
                // Clear existing options
                dropdown.innerHTML = '<option value="">Tidak ada peran kustom</option>';
                
                // Add role options
                roles.forEach(role => {
                    const option = document.createElement('option');
                    option.value = role.id;
                    option.textContent = role.name;
                    if (selectedRoleId && role.id === parseInt(selectedRoleId)) {
                        option.selected = true;
                    }
                    dropdown.appendChild(option);
                });
                

            } else {
                console.error('Failed to load custom roles:', response.status);
            }
        } catch (error) {
            console.error('Error loading custom roles for dropdown:', error);
        }
    }

    closeEditUserModal() {
    document.getElementById('edit-user-modal').classList.add('hidden');
        this.currentUserId = null;
}

    showDeleteUserModal(userId) {
        this.currentUserId = userId;
    document.getElementById('delete-user-modal').classList.remove('hidden');
}

    closeDeleteUserModal() {
    document.getElementById('delete-user-modal').classList.add('hidden');
        this.currentUserId = null;
    }

    async confirmDeleteUser() {
        try {
            const response = await fetch(`/api/users/${this.currentUserId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete user');
            }
            
            this.showToast('success', 'Pengguna berhasil dihapus!');
            this.closeDeleteUserModal();
            this.loadUsers(this.currentPage);
        } catch (error) {
            this.showToast('error', `Gagal menghapus pengguna: ${error.message}`);
        }
    }

    closeCreateRoleModal() {
    document.getElementById('create-role-modal').classList.add('hidden');
}

    openCreateRoleModal() {
        // Clear form fields
        document.getElementById('role-name').value = '';
        document.getElementById('role-description').value = '';
        
        // Clear all permission checkboxes
        const checkboxes = document.querySelectorAll('#permissions-list input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        // Show modal
        document.getElementById('create-role-modal').classList.remove('hidden');
    }

    toggleSuspensionDetails(isSuspended) {
    const details = document.getElementById('suspension-details');
        if (isSuspended) {
            details.classList.remove('hidden');
        } else {
            details.classList.add('hidden');
        }
    }

    async loadRoles() {
        try {
            
            // Load custom roles
            const customRolesResponse = await fetch('/api/roles');
            if (customRolesResponse.ok) {
                const customRoles = await customRolesResponse.json();
                this.renderCustomRoles(customRoles);
            }
            
            // Load permissions
            const permissionsResponse = await fetch('/api/permissions');
            if (permissionsResponse.ok) {
                const permissions = await permissionsResponse.json();
                this.renderPermissions(permissions);
                this.populatePermissionsList(permissions);
            }
        } catch (error) {
            console.error('Error loading roles:', error);
            this.showToast('error', 'Gagal memuat peran dan izin');
        }
    }

    populatePermissionsList(permissions) {
        // Populate create permissions list
        const container = document.getElementById('permissions-list');
        if (container) {
            container.innerHTML = permissions.map(permission => `
                <div class="flex items-center space-x-2">
                    <input type="checkbox" id="perm-${permission.id}" value="${permission.id}" class="rounded border-amber-300 text-amber-500 focus:ring-amber-300">
                    <label for="perm-${permission.id}" class="text-sm text-amber-700">
                        ${permission.name} (${permission.resource}:${permission.action})
                    </label>
                </div>
            `).join('');
        }
        
        // Populate edit permissions list
        const editContainer = document.getElementById('edit-permissions-list');
        if (editContainer) {
            editContainer.innerHTML = permissions.map(permission => `
                <div class="flex items-center space-x-2">
                    <input type="checkbox" id="edit-perm-${permission.id}" value="${permission.id}" class="rounded border-amber-300 text-amber-500 focus:ring-amber-300">
                    <label for="edit-perm-${permission.id}" class="text-sm text-amber-700">
                        ${permission.name} (${permission.resource}:${permission.action})
                    </label>
                </div>
            `).join('');
        }
    }

    renderCustomRoles(roles) {
        const container = document.getElementById('custom-roles');
        if (!container) return;
        
        if (roles.length === 0) {
            container.innerHTML = '<div class="text-amber-600">Tidak ada peran kustom</div>';
            return;
        }
        
        container.innerHTML = roles.map(role => `
            <div class="bg-white border border-amber-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-semibold text-amber-800">${role.name}</h4>
                        <p class="text-sm text-amber-600">${role.description || 'Tidak ada deskripsi'}</p>
                        <div class="flex items-center space-x-2 mt-2">
                            <span class="px-2 py-1 text-xs rounded-full ${role.is_active ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}">
                                ${role.is_active ? 'Aktif' : 'Tidak Aktif'}
                            </span>
                            <span class="text-xs text-amber-600">${role.permissions?.length || 0} izin</span>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="usersManagement.editRole(${role.id})" class="p-2 bg-yellow-100 hover:bg-yellow-200 text-yellow-600 rounded-full">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="usersManagement.deleteRole(${role.id})" class="p-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-full">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderPermissions(permissions) {
        const container = document.getElementById('permissions');
        if (!container) return;
        
        if (permissions.length === 0) {
            container.innerHTML = '<div class="text-amber-600">Tidak ada izin</div>';
            return;
        }
        
        container.innerHTML = permissions.map(permission => `
            <div class="bg-white border border-amber-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-semibold text-amber-800">${permission.name}</h4>
                        <p class="text-sm text-amber-600">${permission.description || 'Tidak ada deskripsi'}</p>
                        <div class="flex items-center space-x-2 mt-2">
                            <span class="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-600">${permission.resource}</span>
                            <span class="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-600">${permission.action}</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadPendingUsers() {
        try {
            
            const response = await fetch('/api/registrations/pending');
            if (!response.ok) {
                throw new Error('Failed to fetch pending users');
            }
            
            const pendingUsers = await response.json();
            this.renderPendingUsers(pendingUsers);
        } catch (error) {
            console.error('Error loading pending users:', error);
            this.showToast('error', 'Gagal memuat pengguna yang menunggu persetujuan');
        }
    }

    async loadDeletionRequests() {
        try {
            const response = await fetch('/api/users/deletion-requests');
            if (!response.ok) {
                throw new Error('Failed to fetch deletion requests');
            }
            
            const data = await response.json();
            this.renderDeletionRequests(data.deletion_requests || []);
            this.updateDeletionStats(data);
        } catch (error) {
            console.error('Error loading deletion requests:', error);
            this.showToast('error', 'Gagal memuat permintaan penghapusan');
        }
    }

    renderDeletionRequests(requests) {
        const container = document.getElementById('deletion-requests-list');
        if (!container) return;
        
        if (requests.length === 0) {
            container.innerHTML = '<div class="text-gray-600">Tidak ada permintaan penghapusan akun yang menunggu</div>';
            return;
        }
        
        container.innerHTML = requests.map(request => `
            <div class="bg-white border border-red-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-r from-red-400 to-pink-400 rounded-full flex items-center justify-center">
                            <span class="text-white font-semibold text-sm">${request.username.charAt(0).toUpperCase()}</span>
                        </div>
                        <div>
                            <h4 class="font-semibold text-red-800">${request.username}</h4>
                            <p class="text-sm text-red-600">${request.email || 'Tidak ada email'}</p>
                            <p class="text-xs text-red-500">Daftar: ${new Date(request.created_at).toLocaleDateString('id-ID')}</p>
                            <p class="text-xs text-red-500">Permintaan: ${new Date(request.deletion_requested_at).toLocaleDateString('id-ID')}</p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="usersManagement.approveDeletion(${request.id})" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">
                            <i class="fas fa-check mr-1"></i>Setujui
                        </button>
                        <button onclick="usersManagement.rejectDeletion(${request.id})" class="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm">
                            <i class="fas fa-times mr-1"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateDeletionStats(data) {
        const totalRequests = document.getElementById('total-deletion-requests');
        const approvedToday = document.getElementById('approved-deletions-today');
        const rejectedToday = document.getElementById('rejected-deletions-today');
        const avgTime = document.getElementById('avg-deletion-time');
        
        if (totalRequests) totalRequests.textContent = data.total || 0;
        if (approvedToday) approvedToday.textContent = '0'; // TODO: Add API for today's stats
        if (rejectedToday) rejectedToday.textContent = '0'; // TODO: Add API for today's stats
        if (avgTime) avgTime.textContent = '-'; // TODO: Add API for average time
    }

    async approveDeletion(userId) {
        try {
            const response = await fetch(`/api/users/${userId}/approve-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to approve deletion');
            }
            
            const result = await response.json();
            this.showToast('success', result.message || 'Permintaan penghapusan disetujui');
            this.loadDeletionRequests();
        } catch (error) {
            console.error('Error approving deletion:', error);
            this.showToast('error', error.message || 'Gagal menyetujui permintaan penghapusan');
        }
    }

    async rejectDeletion(userId) {
        try {
            const response = await fetch(`/api/users/${userId}/reject-deletion`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to reject deletion');
            }
            
            const result = await response.json();
            this.showToast('success', result.message || 'Permintaan penghapusan ditolak');
            this.loadDeletionRequests();
        } catch (error) {
            console.error('Error rejecting deletion:', error);
            this.showToast('error', error.message || 'Gagal menolak permintaan penghapusan');
        }
    }

    async bulkApproveDeletions() {
        if (!confirm('Apakah Anda yakin ingin menyetujui semua permintaan penghapusan? Tindakan ini tidak dapat dibatalkan.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/users/deletion-requests');
            if (!response.ok) {
                throw new Error('Failed to fetch deletion requests');
            }
            
            const data = await response.json();
            const requests = data.deletion_requests || [];
            
            if (requests.length === 0) {
                this.showToast('info', 'Tidak ada permintaan penghapusan untuk disetujui');
                return;
            }
            
            let approvedCount = 0;
            for (const request of requests) {
                try {
                    await this.approveDeletion(request.id);
                    approvedCount++;
                } catch (error) {
                    console.error(`Error approving deletion for user ${request.id}:`, error);
                }
            }
            
            this.showToast('success', `${approvedCount} permintaan penghapusan berhasil disetujui`);
            this.loadDeletionRequests();
        } catch (error) {
            console.error('Error bulk approving deletions:', error);
            this.showToast('error', 'Gagal menyetujui permintaan penghapusan secara massal');
        }
    }

    async bulkRejectDeletions() {
        if (!confirm('Apakah Anda yakin ingin menolak semua permintaan penghapusan?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/users/deletion-requests');
            if (!response.ok) {
                throw new Error('Failed to fetch deletion requests');
            }
            
            const data = await response.json();
            const requests = data.deletion_requests || [];
            
            if (requests.length === 0) {
                this.showToast('info', 'Tidak ada permintaan penghapusan untuk ditolak');
                return;
            }
            
            let rejectedCount = 0;
            for (const request of requests) {
                try {
                    await this.rejectDeletion(request.id);
                    rejectedCount++;
                } catch (error) {
                    console.error(`Error rejecting deletion for user ${request.id}:`, error);
                }
            }
            
            this.showToast('success', `${rejectedCount} permintaan penghapusan berhasil ditolak`);
            this.loadDeletionRequests();
        } catch (error) {
            console.error('Error bulk rejecting deletions:', error);
            this.showToast('error', 'Gagal menolak permintaan penghapusan secara massal');
        }
    }

    renderPendingUsers(users) {
        const container = document.getElementById('pending-users');
        if (!container) return;
        
        if (users.length === 0) {
            container.innerHTML = '<div class="text-amber-600">Tidak ada pengguna yang menunggu persetujuan</div>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="bg-white border border-amber-200 rounded-lg p-4">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-10 h-10 bg-gradient-to-r from-amber-400 to-yellow-400 rounded-full flex items-center justify-center">
                            <span class="text-white font-semibold text-sm">${user.username.charAt(0).toUpperCase()}</span>
                        </div>
                        <div>
                            <h4 class="font-semibold text-amber-800">${user.username}</h4>
                            <p class="text-sm text-amber-600">${user.email || 'Tidak ada email'}</p>
                            <p class="text-xs text-amber-500">Daftar: ${new Date(user.created_at).toLocaleDateString('id-ID')}</p>
                        </div>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="usersManagement.approveUser(${user.id})" class="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded text-sm">
                            <i class="fas fa-check mr-1"></i>Setujui
                        </button>
                        <button onclick="usersManagement.rejectUser(${user.id})" class="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm">
                            <i class="fas fa-times mr-1"></i>Tolak
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async loadPerformanceData() {
        try {
            
            const period = document.getElementById('performance-period')?.value || '30';
            
            // Load performance summary
            const summaryResponse = await fetch(`/api/users/performance/report?days=${period}`);
            if (summaryResponse.ok) {
                const summary = await summaryResponse.json();
                this.renderPerformanceSummary(summary);
            }
            
            // Load leaderboard
            const leaderboardResponse = await fetch(`/api/users/performance/leaderboard`);
            if (leaderboardResponse.ok) {
                const leaderboard = await leaderboardResponse.json();
                this.renderPerformanceLeaderboard(leaderboard);
            }
        } catch (error) {
            console.error('Error loading performance data:', error);
            this.showToast('error', 'Gagal memuat data performa');
        }
    }

    renderPerformanceSummary(summary) {
        // Update summary cards
        const activeUsersCount = document.getElementById('active-users-count');
        const totalActivities = document.getElementById('total-activities');
        const totalContent = document.getElementById('total-content');
        const avgEngagement = document.getElementById('avg-engagement');
        
        // The API returns data in a nested structure
        const summaryData = summary.summary || summary;
        
        if (activeUsersCount) activeUsersCount.textContent = summaryData.active_users || '-';
        if (totalActivities) totalActivities.textContent = summaryData.total_activities || '-';
        if (totalContent) totalContent.textContent = (summaryData.total_news + summaryData.total_images + summaryData.total_videos) || '-';
        
        // Calculate average engagement score from users data
        if (avgEngagement && summary.users && summary.users.length > 0) {
            const totalScore = summary.users.reduce((sum, user) => sum + user.engagement_score, 0);
            const avgScore = Math.round(totalScore / summary.users.length);
            avgEngagement.textContent = avgScore;
        } else if (avgEngagement) {
            avgEngagement.textContent = '-';
        }
    }

    renderPerformanceLeaderboard(leaderboard) {
        const container = document.getElementById('performance-leaderboard');
        if (!container) return;
        
        if (!leaderboard.leaderboard || leaderboard.leaderboard.length === 0) {
            container.innerHTML = '<div class="text-amber-600">Tidak ada data performa</div>';
            return;
        }
        
        container.innerHTML = leaderboard.leaderboard.map((entry, index) => {
            const user = entry.user;
            const metrics = entry.metrics;
            
            return `
                <div class="bg-white border border-amber-200 rounded-lg p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="w-8 h-8 bg-gradient-to-r from-amber-400 to-yellow-400 rounded-full flex items-center justify-center">
                                <span class="text-white font-semibold text-xs">${index + 1}</span>
                            </div>
                            <div>
                                <h4 class="font-semibold text-amber-800">${user.username}</h4>
                                <p class="text-sm text-amber-600">${user.role}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-amber-800">${metrics.engagement_score}</div>
                            <div class="text-xs text-amber-600">Skor</div>
                        </div>
                    </div>
                    <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                        <div class="text-center">
                            <div class="font-semibold text-blue-600">${metrics.news_count}</div>
                            <div class="text-gray-500">Berita</div>
                        </div>
                        <div class="text-center">
                            <div class="font-semibold text-green-600">${metrics.images_count}</div>
                            <div class="text-gray-500">Gambar</div>
                        </div>
                        <div class="text-center">
                            <div class="font-semibold text-purple-600">${metrics.videos_count}</div>
                            <div class="text-gray-500">Video</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Additional methods for role management
    async editRole(roleId) {
        try {
            // Get role details
            const roleResponse = await fetch(`/api/roles/${roleId}`);
            if (!roleResponse.ok) {
                throw new Error('Failed to fetch role details');
            }
            
            const role = await roleResponse.json();
            
            // Get role permissions
            const permissionsResponse = await fetch(`/api/roles/${roleId}/permissions`);
            const rolePermissions = permissionsResponse.ok ? await permissionsResponse.json() : [];
            
            // Populate edit form
            document.getElementById('edit-role-name').value = role.name;
            document.getElementById('edit-role-description').value = role.description || '';
            document.getElementById('edit-role-active').checked = role.is_active;
            
            // Clear and set permissions
            const permissionCheckboxes = document.querySelectorAll('#edit-permissions-list input[type="checkbox"]');
            permissionCheckboxes.forEach(cb => {
                cb.checked = rolePermissions.some(p => p.id === parseInt(cb.value));
            });
            
            // Store role ID for update
            this.currentRoleId = roleId;
            
            // Show edit modal
            document.getElementById('edit-role-modal').classList.remove('hidden');
        } catch (error) {
            console.error('Error loading role for edit:', error);
            this.showToast('error', 'Gagal memuat detail peran');
        }
    }

    async deleteRole(roleId) {
        // Store role ID for confirmation
        this.currentRoleId = roleId;
        
        // Show confirmation modal
        document.getElementById('delete-role-modal').classList.remove('hidden');
    }

    async confirmDeleteRole() {
        try {
            const response = await fetch(`/api/roles/${this.currentRoleId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete role');
            }
            
            this.showToast('success', 'Peran berhasil dihapus!');
            this.closeDeleteRoleModal();
            this.loadRoles();
        } catch (error) {
            this.showToast('error', `Gagal menghapus peran: ${error.message}`);
        }
    }

    closeDeleteRoleModal() {
        document.getElementById('delete-role-modal').classList.add('hidden');
        this.currentRoleId = null;
    }

    async handleEditRole(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('edit-role-name').value.trim(),
            description: document.getElementById('edit-role-description').value.trim(),
            is_active: document.getElementById('edit-role-active').checked,
            permission_ids: this.getSelectedEditPermissions()
        };
        
        try {
            const response = await fetch(`/api/roles/${this.currentRoleId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to update role');
            }
            
            this.showToast('success', 'Peran berhasil diperbarui!');
            this.closeEditRoleModal();
            this.loadRoles();
        } catch (error) {
            this.showToast('error', `Gagal memperbarui peran: ${error.message}`);
        }
    }

    getSelectedEditPermissions() {
        const checkboxes = document.querySelectorAll('#edit-permissions-list input[type="checkbox"]:checked');
        return Array.from(checkboxes).map(cb => parseInt(cb.value));
    }

    closeEditRoleModal() {
        document.getElementById('edit-role-modal').classList.add('hidden');
        this.currentRoleId = null;
    }

    // Additional methods for user approval
    async approveUser(userId) {
        try {
            const response = await fetch(`/api/registrations/${userId}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to approve user');
            }
            
            this.showToast('success', 'Pengguna berhasil disetujui!');
            this.loadPendingUsers();
        } catch (error) {
            this.showToast('error', `Gagal menyetujui pengguna: ${error.message}`);
        }
    }

    async rejectUser(userId) {
        try {
            const response = await fetch(`/api/registrations/${userId}/reject`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason: 'Ditolak oleh administrator' })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to reject user');
            }
            
            this.showToast('success', 'Pengguna berhasil ditolak!');
            this.loadPendingUsers();
        } catch (error) {
            this.showToast('error', `Gagal menolak pengguna: ${error.message}`);
        }
    }

    toggleBulkActions() {
        const panel = document.getElementById('bulk-actions-panel');
        if (panel) {
            panel.classList.toggle('hidden');
        }
    }

    async exportUsers() {
        try {
            const response = await fetch('/api/users/bulk/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: 'csv' })
            });
            
            if (!response.ok) {
                throw new Error('Failed to export users');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'users-export.csv';
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showToast('success', 'Ekspor berhasil!');
        } catch (error) {
            this.showToast('error', 'Gagal mengekspor pengguna');
        }
    }

    async exportPerformance() {
        try {
            const period = document.getElementById('performance-period')?.value || '30';
            const response = await fetch(`/api/users/performance/report/export?days=${period}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: 'csv' })
            });

            if (!response.ok) {
                throw new Error('Failed to export performance report');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'performance-report.csv';
            a.click();
            window.URL.revokeObjectURL(url);

            this.showToast('success', 'Ekspor laporan performa berhasil!');
        } catch (error) {
            this.showToast('error', 'Gagal mengekspor laporan performa');
        }
    }

    async exportRoles() {
        try {
            const response = await fetch('/api/roles/bulk/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format: 'csv' })
            });

            if (!response.ok) {
                throw new Error('Failed to export roles');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'roles-export.csv';
            a.click();
            window.URL.revokeObjectURL(url);

            this.showToast('success', 'Ekspor peran berhasil!');
        } catch (error) {
            this.showToast('error', 'Gagal mengekspor peran');
        }
    }

    debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
    }

    showToast(message, type = 'info') {
        if (typeof showToast === 'function') {
            showToast(type, message);
        }
    }

    // Modal functions for new features
    openCreateUserModal() {
        const modal = document.getElementById('create-user-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    closeCreateUserModal() {
        const modal = document.getElementById('create-user-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            // Reset form
            const form = document.getElementById('create-user-form');
            if (form) form.reset();
        }
    }

    openUserDetailsModal(userId) {
        this.currentUserId = userId;
        const user = this.users.find(u => u.id === userId);
        if (!user) {
            this.showToast('error', 'User tidak ditemukan');
            return;
        }

        // Generate user details HTML
        const detailsHTML = this.generateUserDetailsHTML(user);
        const detailsContainer = document.getElementById('user-details-content');
        if (detailsContainer) {
            detailsContainer.innerHTML = detailsHTML;
        }

        const modal = document.getElementById('user-details-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
        }
    }

    closeUserDetailsModal() {
        const modal = document.getElementById('user-details-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    openPasswordResetModal(userId) {
        this.currentUserId = userId;
        const modal = document.getElementById('password-reset-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            // Reset form
            const form = document.getElementById('password-reset-form');
            if (form) form.reset();
        }
    }

    closePasswordResetModal() {
        const modal = document.getElementById('password-reset-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
    }

    generateUserDetailsHTML(user) {
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
        const displayName = fullName || user.username;
        
        return `
            <div class="space-y-4">
                <div class="flex items-center space-x-4">
                    <div class="w-16 h-16 bg-gradient-to-r from-amber-400 to-yellow-400 rounded-full flex items-center justify-center">
                        <span class="text-white font-semibold text-xl">${user.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <div>
                        <h3 class="text-xl font-semibold text-amber-800">${displayName}</h3>
                        <p class="text-amber-600">@${user.username}</p>
                    </div>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <h4 class="font-semibold text-amber-700 mb-2">Informasi Dasar</h4>
                        <div class="space-y-2 text-sm">
                            <p><span class="font-medium">Email:</span> ${user.email || 'Tidak ada email'}</p>
                            <p><span class="font-medium">Bio:</span> ${user.bio || 'Tidak ada bio'}</p>
                            <p><span class="font-medium">Role:</span> ${user.role || 'Tidak ada role'}</p>
                            <p><span class="font-medium">Custom Role:</span> ${user.custom_role?.name || 'Tidak ada'}</p>
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="font-semibold text-amber-700 mb-2">Status</h4>
                        <div class="space-y-2 text-sm">
                            <p><span class="font-medium">Aktif:</span> ${user.is_active ? 'Ya' : 'Tidak'}</p>
                            <p><span class="font-medium">Terverifikasi:</span> ${user.verified ? 'Ya' : 'Tidak'}</p>
                            <p><span class="font-medium">Premium:</span> ${user.is_premium ? 'Ya' : 'Tidak'}</p>
                            <p><span class="font-medium">Tersuspend:</span> ${user.is_suspended ? 'Ya' : 'Tidak'}</p>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h4 class="font-semibold text-amber-700 mb-2">Aktivitas</h4>
                    <div class="space-y-2 text-sm">
                        <p><span class="font-medium">Login Terakhir:</span> ${user.last_login ? new Date(user.last_login).toLocaleString() : 'Tidak ada'}</p>
                        <p><span class="font-medium">Jumlah Login:</span> ${user.login_count || 0}</p>
                        <p><span class="font-medium">Dibuat:</span> ${user.created_at ? new Date(user.created_at).toLocaleString() : 'Tidak ada'}</p>
                        <p><span class="font-medium">Diperbarui:</span> ${user.updated_at ? new Date(user.updated_at).toLocaleString() : 'Tidak ada'}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.usersManagement = new UsersManagement();
});

// Global functions for onclick handlers
function openEditUserModal(userId) {
    if (window.usersManagement) {
        window.usersManagement.openEditUserModal(userId);
    }
}

function closeEditUserModal() {
    if (window.usersManagement) {
        window.usersManagement.closeEditUserModal();
    }
}

function showDeleteUserModal(userId) {
    if (window.usersManagement) {
        window.usersManagement.showDeleteUserModal(userId);
    }
}

function closeDeleteUserModal() {
    if (window.usersManagement) {
        window.usersManagement.closeDeleteUserModal();
    }
}

function confirmDeleteUser() {
    if (window.usersManagement) {
        window.usersManagement.confirmDeleteUser();
    }
}

function closeCreateRoleModal() {
    if (window.usersManagement) {
        window.usersManagement.closeCreateRoleModal();
    }
}

function openCreateRoleModal() {
    if (window.usersManagement) {
        window.usersManagement.openCreateRoleModal();
    }
}

// Additional global functions for new features
function editRole(roleId) {
    if (window.usersManagement) {
        window.usersManagement.editRole(roleId);
    }
}

function deleteRole(roleId) {
    if (window.usersManagement) {
        window.usersManagement.deleteRole(roleId);
    }
}

function closeEditRoleModal() {
    if (window.usersManagement) {
        window.usersManagement.closeEditRoleModal();
    }
}

function confirmDeleteRole() {
    if (window.usersManagement) {
        window.usersManagement.confirmDeleteRole();
    }
}

function closeDeleteRoleModal() {
    if (window.usersManagement) {
        window.usersManagement.closeDeleteRoleModal();
    }
}

function approveUser(userId) {
    if (window.usersManagement) {
        window.usersManagement.approveUser(userId);
    }
}

// New modal functions
function openCreateUserModal() {
    if (window.usersManagement) {
        window.usersManagement.openCreateUserModal();
    }
}

function closeCreateUserModal() {
    if (window.usersManagement) {
        window.usersManagement.closeCreateUserModal();
    }
}

function openUserDetailsModal(userId) {
    if (window.usersManagement) {
        window.usersManagement.openUserDetailsModal(userId);
    }
}

function closeUserDetailsModal() {
    if (window.usersManagement) {
        window.usersManagement.closeUserDetailsModal();
    }
}

function openPasswordResetModal(userId) {
    if (window.usersManagement) {
        window.usersManagement.openPasswordResetModal(userId);
    }
}

function closePasswordResetModal() {
    if (window.usersManagement) {
        window.usersManagement.closePasswordResetModal();
    }
}

function rejectUser(userId) {
    if (window.usersManagement) {
        window.usersManagement.rejectUser(userId);
    }
}

// Deletion request functions
function approveDeletion(userId) {
    if (window.usersManagement) {
        window.usersManagement.approveDeletion(userId);
    }
}

function rejectDeletion(userId) {
    if (window.usersManagement) {
        window.usersManagement.rejectDeletion(userId);
    }
}