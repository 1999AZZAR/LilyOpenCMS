document.addEventListener('DOMContentLoaded', function() {
  // DOM elements
  const searchInput = document.getElementById('search-input');
  const searchLoading = document.getElementById('search-loading');
  const searchSuggestions = document.getElementById('search-suggestions');
  const resultCount = document.getElementById('result-count');
  const noResults = document.getElementById('no-results');
  const albumsGrid = document.getElementById('albums-grid');
  const categoryFilter = document.getElementById('category-filter');
  const statusFilter = document.getElementById('status-filter');
  const ratingFilter = document.getElementById('rating-filter');
  const ageFilter = document.getElementById('age-filter');
  const sortFilter = document.getElementById('sort-filter');
  
  let searchTimeout;
  let currentSearchTerm = '';
  let selectedSuggestionIndex = -1;
  let currentPage = 1;
  let isLoading = false;
  
  // Function to generate thumbnail URL using the project's thumbnailing mechanism
  function generateThumbnailUrl(imageData) {
    if (!imageData || !imageData.url) {
      return '/static/pic/placeholder.png';
    }
    
    try {
      // Extract the filepath from the URL
      // The URL format is like: /static/uploads/image.jpg
      // We need to extract: uploads/image.jpg
      let filepath = imageData.url.replace('/static/', '');
      
      // Find the last dot to separate base path and extension
      const lastDotIndex = filepath.lastIndexOf('.');
      if (lastDotIndex === -1) {
        return '/static/pic/placeholder.png';
      }
      
      // Split into base path and extension
      const basePath = filepath.substring(0, lastDotIndex);
      const extension = filepath.substring(lastDotIndex);
      
      // Create thumbnail path with '_thumb_portrait' suffix
      const thumbPath = basePath + '_thumb_portrait' + extension;
      
      return '/static/' + thumbPath;
    } catch (error) {
      console.error('Error generating thumbnail URL:', error);
      return '/static/pic/placeholder.png';
    }
  }
  
  // Load all albums on page load
  function loadInitialAlbums() {
    showLoading(true);
    
    // Check for URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const urlQuery = urlParams.get('q') || '';
    const urlCategory = urlParams.get('category') || '';
    const urlStatus = urlParams.get('status') || '';
    const urlRating = urlParams.get('rating') || '';
    const urlSort = urlParams.get('sort') || 'newest';
    
    // Set filter values from URL parameters
    if (urlQuery) {
      searchInput.value = urlQuery;
      currentSearchTerm = urlQuery;
    }
    if (urlCategory) {
      categoryFilter.value = urlCategory;
    }
    if (urlStatus) {
      statusFilter.value = urlStatus;
    }
    if (urlRating) {
      ratingFilter.value = urlRating;
    }
    if (urlSort) {
      sortFilter.value = urlSort;
    }
    
    performSearch(urlQuery, true); // Use URL query or empty search to get all albums
  }
  
  // Debounced search function
  function debouncedSearch(searchTerm) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      performSearch(searchTerm);
    }, 300);
  }
  
  // Perform server-side search
  function performSearch(searchTerm, isInitialLoad = false) {
    if (isLoading) return;
    
    isLoading = true;
    showLoading(true);
    
    // Build search parameters
    const params = new URLSearchParams();
    if (searchTerm.trim()) {
      params.append('q', searchTerm.trim());
    }
    
    const categoryValue = categoryFilter.value;
    if (categoryValue) {
      params.append('category', categoryValue);
    }
    
    const statusValue = statusFilter.value;
    if (statusValue) {
      params.append('status', statusValue);
    }

    const ratingValue = ratingFilter.value;
    if (ratingValue) {
      params.append('rating', ratingValue);
    }
    const ageValue = ageFilter.value;
    if (ageValue) {
      params.append('age', ageValue);
    }
    
    const sortValue = sortFilter.value;
    if (sortValue) {
      params.append('sort', sortValue);
    }
    
    params.append('page', currentPage);
    params.append('per_page', 12);
    
    // Make AJAX request
    fetch(`/api/search/albums?${params.toString()}`)
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          displaySearchResults(data, isInitialLoad);
        } else {
          console.error('Search error:', data.error);
          showErrorMessage('Terjadi kesalahan saat mencari album');
        }
      })
      .catch(error => {
        console.error('Search request failed:', error);
        showErrorMessage('Gagal melakukan pencarian');
      })
      .finally(() => {
        isLoading = false;
        showLoading(false);
      });
  }
  
  // Display search results
  function displaySearchResults(data, isInitialLoad = false) {
    const albums = data.albums;
    const pagination = data.pagination;
    const searchInfo = data.search_info;
    
    // Clear current grid
    albumsGrid.innerHTML = '';
    
    if (albums.length === 0) {
      noResults.classList.remove('hidden');
      albumsGrid.classList.add('hidden');
      updateResultCount(0, 0);
      return;
    }
    
    // Hide no results message
    noResults.classList.add('hidden');
    albumsGrid.classList.remove('hidden');
    
    // Generate album cards
    albums.forEach(album => {
      const albumCard = createAlbumCard(album);
      albumsGrid.appendChild(albumCard);
    });
    
    // Update result count with pagination info
    const startItem = (pagination.page - 1) * pagination.per_page + 1;
    const endItem = startItem + albums.length - 1;
    
    if (pagination.pages > 1) {
      resultCount.textContent = `Menampilkan ${startItem}-${endItem} dari ${searchInfo.total_count} album (Halaman ${pagination.page} dari ${pagination.pages})`;
    } else {
      resultCount.textContent = `Total ${searchInfo.total_count} album`;
    }
    
    // Update pagination if needed
    updatePagination(pagination);

    // Trigger ads refresh after albums are rendered
    if (window.adsSystem) {
      setTimeout(() => {
        try { window.adsSystem.refreshAds(); } catch (e) {}
      }, 600);
    }
  }
  
  // Create album card HTML
      function createAlbumCard(album) {
    
    const card = document.createElement('article');
    card.className = 'album-card bg-card rounded-lg border border-border overflow-hidden fade-in';
    
    const statusClass = album.status === 'completed' ? 'status-completed' : 
                       album.status === 'hiatus' ? 'status-hiatus' : 'status-ongoing';
    const statusText = album.status === 'completed' ? 'Selesai' : 
                      album.status === 'hiatus' ? 'Hiatus' : 'Ongoing';
    
    // Generate thumbnail URL using the project's thumbnailing mechanism
    const imageUrl = generateThumbnailUrl(album.cover_image);
    
    // Create rating stars HTML
    let ratingStars = '';
    if (album.rating && album.rating.has_ratings) {
      const avgRating = album.rating.average;
      const fullStars = Math.floor(avgRating);
      const hasHalfStar = avgRating % 1 >= 0.5;
      
      for (let i = 1; i <= 5; i++) {
        if (i <= fullStars) {
          ratingStars += '<i class="fas fa-star text-yellow-400"></i>';
        } else if (i === fullStars + 1 && hasHalfStar) {
          ratingStars += '<i class="fas fa-star-half-alt text-yellow-400"></i>';
        } else {
          ratingStars += '<i class="far fa-star text-gray-300"></i>';
        }
      }
    }
    
    const ageBadge = album.age_rating ? `<span class="overlay-badge">${album.age_rating}</span>` : '';

    card.innerHTML = `
      <a href="${album.url}" class="block group">
        <div class="relative">
          <img src="/static/pic/placeholder.png"
               data-src="${imageUrl}"
               alt="${album.title}"
               class="album-cover w-full"
               onload="this.classList.add('loaded')"
               onerror="this.onerror=null; this.src='/static/pic/placeholder.png';">
          
          <span class="chapter-count">${album.total_chapters} Bab</span>
          <span class="status-badge ${statusClass}">${statusText}</span>
          
          ${album.is_premium ? '<span class="premium-badge">Premium</span>' : ''}
          ${ageBadge}
        </div>
        
        <div class="p-4">
          ${album.category ? `<span class="inline-block mb-2 px-2 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary category-badge">${album.category.name}</span>` : ''}
          
          <h3 class="text-lg font-semibold text-card-foreground mb-2 line-clamp-2 group-hover:text-primary transition-colors album-title">
            ${highlightSearchTerms(album.title, currentSearchTerm)}
          </h3>
          
          ${album.description ? `<p class="text-sm text-muted-foreground line-clamp-3 mb-3 album-description">${highlightSearchTerms(album.description, currentSearchTerm)}</p>` : ''}
          
          ${album.rating && album.rating.has_ratings ? `
            <div class="flex items-center mb-2">
              <div class="flex items-center mr-2">
                ${ratingStars}
                <span class="ml-1 text-xs text-muted">(${album.rating.count})</span>
              </div>
              <span class="text-xs font-medium text-primary">${album.rating.average.toFixed(1)}</span>
            </div>
          ` : ''}
          
          <div class="flex items-center justify-between text-xs text-muted-foreground">
            <span>${formatDate(album.created_at)}</span>
            <span>${album.total_views} dilihat • ${album.total_reads} baca</span>
          </div>
        </div>
      </a>
    `;
    
    // Load the image after the card is added to DOM
    setTimeout(() => {
      const img = card.querySelector('img');
      if (img && img.dataset.src) {
        img.src = img.dataset.src;
      }
    }, 50);
    
    return card;
  }
  
  // Highlight search terms in text
  function highlightSearchTerms(text, searchTerm) {
    if (!searchTerm || !text) return text;
    
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<span class="search-highlight">$1</span>');
  }
  
  // Format date
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    });
  }
  
  // Update result count display
  function updateResultCount(visible, total) {
    if (currentSearchTerm.trim() || categoryFilter.value || statusFilter.value || ratingFilter.value) {
      resultCount.textContent = `Menampilkan ${visible} dari ${total} album`;
    } else {
      resultCount.textContent = `Total ${total} album`;
    }
  }
  
  // Show/hide loading indicator
  function showLoading(show) {
    if (show) {
      searchLoading.classList.add('active');
    } else {
      searchLoading.classList.remove('active');
    }
  }
  
  // Show error message
  function showErrorMessage(message) {
    resultCount.textContent = message;
    resultCount.style.color = '#ef4444';
    setTimeout(() => {
      resultCount.style.color = '';
    }, 3000);
  }
  
  // Generate search suggestions
  function generateSuggestions(searchTerm) {
    if (!searchTerm.trim()) {
      searchSuggestions.style.display = 'none';
      return;
    }
    
    // For now, we'll use a simple approach
    // In a real implementation, you might want to create a separate endpoint for suggestions
    const suggestions = [];
    const searchLower = searchTerm.toLowerCase();
    
    // Get categories from the page
    const categoryOptions = categoryFilter.querySelectorAll('option');
    categoryOptions.forEach(option => {
      if (option.value && option.text.toLowerCase().includes(searchLower)) {
        suggestions.push(option.text);
      }
    });
    
    // Add some common search terms
    const commonTerms = ['ongoing', 'completed', 'hiatus', 'premium'];
    commonTerms.forEach(term => {
      if (term.toLowerCase().includes(searchLower)) {
        suggestions.push(term);
      }
    });
    
    // Add sort options if they match
    const sortOptions = ['terbaru', 'terlama', 'terpopuler', 'kurang populer', 'rating tertinggi'];
    sortOptions.forEach(option => {
      if (option.toLowerCase().includes(searchLower)) {
        suggestions.push(option);
      }
    });
    
    displaySuggestions(suggestions.slice(0, 5));
  }
  
  // Display search suggestions
  function displaySuggestions(suggestions) {
    if (suggestions.length === 0) {
      searchSuggestions.style.display = 'none';
      return;
    }
    
    searchSuggestions.innerHTML = suggestions
      .map(suggestion => `<div class="search-suggestion">${suggestion}</div>`)
      .join('');
    
    searchSuggestions.style.display = 'block';
  }
  
  // Update pagination
  function updatePagination(pagination) {
    const paginationContainer = document.getElementById('pagination-container');
    
    if (pagination.pages <= 1) {
      paginationContainer.innerHTML = '';
      return;
    }
    
    let paginationHTML = '<nav class="flex items-center space-x-2">';
    
    // Previous button
    if (pagination.has_prev) {
      paginationHTML += `
        <button onclick="changePage(${pagination.prev_num})" 
                class="px-3 py-2 text-sm border border-border rounded-lg hover:bg-secondary transition-colors">
          Sebelumnya
        </button>
      `;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let pageNum = startPage; pageNum <= endPage; pageNum++) {
      if (pageNum === pagination.page) {
        paginationHTML += `
          <span class="px-3 py-2 text-sm bg-primary text-primary-foreground rounded-lg">
            ${pageNum}
          </span>
        `;
      } else {
        paginationHTML += `
          <button onclick="changePage(${pageNum})" 
                  class="px-3 py-2 text-sm border border-border rounded-lg hover:bg-secondary transition-colors">
            ${pageNum}
          </button>
        `;
      }
    }
    
    // Next button
    if (pagination.has_next) {
      paginationHTML += `
        <button onclick="changePage(${pagination.next_num})" 
                class="px-3 py-2 text-sm border border-border rounded-lg hover:bg-secondary transition-colors">
          Selanjutnya
        </button>
      `;
    }
    
    paginationHTML += '</nav>';
    paginationContainer.innerHTML = paginationHTML;
  }
  
  // Change page function (global for onclick handlers)
  window.changePage = function(pageNum) {
    currentPage = pageNum;
    
    // Show loading state
    showLoading(true);
    
    // Scroll to top of results
    albumsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    performSearch(currentSearchTerm);
  };
  
  // Clear all filters function (global for onclick handlers)
  window.clearAllFilters = function() {
    event.stopPropagation(); // Prevent card click
    searchInput.value = '';
    categoryFilter.value = '';
    statusFilter.value = '';
    ratingFilter.value = '';
    sortFilter.value = 'newest';
    currentSearchTerm = '';
    currentPage = 1;
    performSearch('');
    albumsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  
  // Event listeners
  searchInput.addEventListener('input', function() {
    currentSearchTerm = this.value;
    currentPage = 1; // Reset to first page on new search
    debouncedSearch(this.value);
    generateSuggestions(this.value);
    selectedSuggestionIndex = -1;
  });
  
  searchInput.addEventListener('keydown', function(e) {
    const suggestions = searchSuggestions.querySelectorAll('.search-suggestion');
    
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, suggestions.length - 1);
      updateSuggestionSelection(suggestions);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
      updateSuggestionSelection(suggestions);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedSuggestionIndex >= 0 && suggestions[selectedSuggestionIndex]) {
        this.value = suggestions[selectedSuggestionIndex].textContent;
        searchSuggestions.style.display = 'none';
        performSearch(this.value);
      }
    } else if (e.key === 'Escape') {
      searchSuggestions.style.display = 'none';
      selectedSuggestionIndex = -1;
    }
  });
  
  // Update suggestion selection
  function updateSuggestionSelection(suggestions) {
    suggestions.forEach((suggestion, index) => {
      suggestion.classList.toggle('selected', index === selectedSuggestionIndex);
    });
  }
  
  // Click on suggestion
  searchSuggestions.addEventListener('click', function(e) {
    if (e.target.classList.contains('search-suggestion')) {
      searchInput.value = e.target.textContent;
      searchSuggestions.style.display = 'none';
      performSearch(searchInput.value);
    }
  });
  
  // Hide suggestions when clicking outside
  document.addEventListener('click', function(e) {
    if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
      searchSuggestions.style.display = 'none';
    }
  });
  
  // Category filter
  categoryFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
  });
  
  // Status filter
  statusFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
  });

  // Rating filter
  ratingFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
  });

  // Age filter
  ageFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
  });

  // Sort filter
  sortFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
  });
  
  // Initialize by loading all albums
  loadInitialAlbums();
}); 