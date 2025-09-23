document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const searchInput = document.getElementById('search-input');
    const resultCount = document.getElementById('result-count');
    const noResults = document.getElementById('no-results');
    const contentGrid = document.getElementById('content-grid');
    const categoryFilter = document.getElementById('category-filter');
    const sortFilter = document.getElementById('sort-filter');
    const statusFilter = document.getElementById('status-filter');
    const searchLoading = document.getElementById('search-loading');
    const searchSuggestions = document.getElementById('search-suggestions');
    const paginationContainer = document.getElementById('pagination-container');

    // State
    let currentPage = 1;
    let isLoading = false;
    let searchTimeout;

    // Initialize
    loadContent();

    // Search input handler
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadContent();
        }, 300);
    });

    // Filter handlers
    [categoryFilter, sortFilter, statusFilter].forEach(filter => {
        if (filter) {
            filter.addEventListener('change', function() {
                currentPage = 1;
                loadContent();
            });
        }
    });

    // Load content function
    async function loadContent() {
        if (isLoading) return;
        
        isLoading = true;
        showLoading();

        try {
            const params = new URLSearchParams({
                page: currentPage,
                search: searchInput.value,
                category: categoryFilter?.value || '',
                sort: sortFilter?.value || 'newest',
                status: statusFilter?.value || '',
                tab: window.userInfo.activeTab || 'stories'
            });

            const response = await fetchWithCSRF(`/api/profile/${window.userInfo.username}/content?${params}`);
            const data = await response.json();

            if (data.success) {
                renderContent(data.content);
                renderPagination(data.pagination);
                updateResultCount(data.pagination.total);
                toggleNoResults(data.content.length === 0);
            } else {
                console.error('Failed to load content:', data.error);
                showError('Failed to load content');
            }
        } catch (error) {
            console.error('Error loading content:', error);
            showError('Error loading content');
        } finally {
            isLoading = false;
            hideLoading();
        }
    }

    // Render content
    function renderContent(content) {
        if (!content || content.length === 0) {
            contentGrid.innerHTML = '';
            return;
        }

        const contentHTML = content.map(item => {
            if (window.userInfo.activeTab === 'stories') {
                return renderStoryCard(item);
            } else {
                return renderAlbumCard(item);
            }
        }).join('');

        contentGrid.innerHTML = contentHTML;
    }

    // Render story card
    function renderStoryCard(story) {
        const thumbnail = story.image_url ? 
            `<img src="${story.image_url}" alt="${story.title}" class="content-thumbnail" loading="lazy">` :
            `<div class="content-thumbnail flex items-center justify-center" style="background: linear-gradient(135deg, hsl(var(--muted)) 0%, hsl(var(--muted) / 0.5) 100%); color: hsl(var(--muted-foreground));">
                <i class="fas fa-book text-4xl"></i>
            </div>`;

        const excerpt = story.content ? 
            `<div class="content-excerpt">${story.content.substring(0, 150)}${story.content.length > 150 ? '...' : ''}</div>` : '';

        const premiumBadge = story.is_premium ? 
            '<div class="stat-item"><i class="fas fa-crown text-yellow-500"></i> Premium</div>' :
            '<div class="stat-item"><i class="fas fa-unlock text-green-500"></i> Free</div>';

        return `
            <div class="content-card">
                ${thumbnail}
                <div class="content-info">
                    <h3 class="content-title">
                        <a href="${story.url}">${story.title}</a>
                    </h3>
                    <div class="content-meta">
                        <i class="fas fa-calendar"></i> ${story.created_at}
                        ${story.category ? `<span class="mx-2">•</span><i class="fas fa-tag"></i> ${story.category}` : ''}
                    </div>
                    ${excerpt}
                    <div class="content-stats">
                        <div class="stat-item">
                            <i class="fas fa-eye"></i> ${story.read_count || 0} reads
                        </div>
                        ${premiumBadge}
                    </div>
                </div>
            </div>
        `;
    }

    // Render album card
    function renderAlbumCard(album) {
        const thumbnail = album.cover_image_url ? 
            `<img src="${album.cover_image_url}" alt="${album.title}" class="content-thumbnail" loading="lazy">` :
            `<div class="content-thumbnail flex items-center justify-center" style="background: linear-gradient(135deg, hsl(var(--muted)) 0%, hsl(var(--muted) / 0.5) 100%); color: hsl(var(--muted-foreground));">
                <i class="fas fa-images text-4xl"></i>
            </div>`;

        const excerpt = album.description ? 
            `<div class="content-excerpt">${album.description.substring(0, 150)}${album.description.length > 150 ? '...' : ''}</div>` : '';

        const statusIcon = album.is_completed ? 
            '<i class="fas fa-check-circle text-green-500"></i> Completed' :
            album.is_hiatus ? 
            '<i class="fas fa-pause-circle text-yellow-500"></i> Hiatus' :
            '<i class="fas fa-play-circle text-blue-500"></i> Ongoing';

        return `
            <div class="content-card">
                ${thumbnail}
                <div class="content-info">
                    <h3 class="content-title">
                        <a href="${album.url}">${album.title}</a>
                    </h3>
                    <div class="content-meta">
                        <i class="fas fa-calendar"></i> ${album.created_at}
                        ${album.category ? `<span class="mx-2">•</span><i class="fas fa-tag"></i> ${album.category}` : ''}
                    </div>
                    ${excerpt}
                    <div class="content-stats">
                        <div class="stat-item">
                            <i class="fas fa-eye"></i> ${album.total_reads || 0} reads
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-book-open"></i> ${album.total_chapters || 0} chapters
                        </div>
                        <div class="stat-item">
                            ${statusIcon}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Render pagination
    function renderPagination(pagination) {
        if (!pagination || pagination.pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        const { page, pages, has_prev, has_next, prev_num, next_num } = pagination;
        
        let paginationHTML = `
            <div class="flex flex-col items-center justify-center mt-12 lg:mt-16">
                <div class="text-sm text-muted-foreground mb-6">
                    Page ${page} of ${pages} (${pagination.total} items)
                </div>
                <nav aria-label="Content pagination" class="flex items-center justify-center gap-2 sm:gap-3 lg:gap-4">
        `;

        // Previous button
        if (has_prev) {
            paginationHTML += `
                <button onclick="changePage(${prev_num})" 
                        class="inline-flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg border border-border bg-card text-foreground hover:bg-accent hover:border-primary/30 transition-all duration-200">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 sm:w-4 sm:h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                    </svg>
                </button>
            `;
        }

        // Page numbers
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(pages, page + 2);

        for (let i = startPage; i <= endPage; i++) {
            if (i === page) {
                paginationHTML += `
                    <span class="inline-flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-primary text-primary-foreground font-semibold shadow-sm text-sm">
                        ${i}
                    </span>
                `;
            } else {
                paginationHTML += `
                    <button onclick="changePage(${i})" 
                            class="inline-flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg border border-border bg-card text-foreground hover:bg-accent hover:border-primary/30 transition-all duration-200 text-sm">
                        ${i}
                    </button>
                `;
            }
        }

        // Next button
        if (has_next) {
            paginationHTML += `
                <button onclick="changePage(${next_num})" 
                        class="inline-flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg border border-border bg-card text-foreground hover:bg-accent hover:border-primary/30 transition-all duration-200">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3 h-3 sm:w-4 sm:h-4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                    </svg>
                </button>
            `;
        }

        paginationHTML += `
                </nav>
            </div>
        `;

        paginationContainer.innerHTML = paginationHTML;
    }

    // Change page function
    window.changePage = function(page) {
        currentPage = page;
        loadContent();
    };

    // Update result count
    function updateResultCount(total) {
        if (resultCount) {
            resultCount.textContent = `${total} ${total === 1 ? 'item' : 'items'} found`;
        }
    }

    // Toggle no results
    function toggleNoResults(show) {
        if (noResults) {
            noResults.classList.toggle('hidden', !show);
        }
    }

    // Show/hide loading
    function showLoading() {
        if (searchLoading) {
            searchLoading.classList.add('active');
        }
    }

    function hideLoading() {
        if (searchLoading) {
            searchLoading.classList.remove('active');
        }
    }

    // Show error
    function showError(message) {
        console.error(message);
        // You could add a toast notification here
    }

    // Clear all filters
    window.clearAllFilters = function() {
        searchInput.value = '';
        if (categoryFilter) categoryFilter.value = '';
        if (sortFilter) sortFilter.value = 'newest';
        if (statusFilter) statusFilter.value = '';
        currentPage = 1;
        loadContent();
    };
});
