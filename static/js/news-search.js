document.addEventListener('DOMContentLoaded', function() {
  // DOM elements
  const searchInput = document.getElementById('search-input');
  const resultCount = document.getElementById('result-count');
  const noResults = document.getElementById('no-results');
  const newsGrid = document.getElementById('news-grid');
  const categoryFilter = document.getElementById('category-filter');
  const tagFilter = document.getElementById('tag-filter');
  const sortFilter = document.getElementById('sort-filter');
  const ageFilter = document.getElementById('age-filter');
  
  // Global function to refresh news cards with new design
  window.refreshNewsCards = function() {
    console.log('🔄 Refreshing news cards with new design:', window.brandInfo?.card_design);
    const currentCards = newsGrid.querySelectorAll('.news-card');
    currentCards.forEach(card => {
      const cardDesign = window.brandInfo?.card_design || 'classic';
      card.className = `news-card ${cardDesign} bg-card rounded-lg border border-border overflow-hidden fade-in`;
    });
  };
  
  // Listen for card design changes from admin panel
  window.addEventListener('cardDesignChanged', function(event) {
    console.log('🎨 Card design changed to:', event.detail.cardDesign);
    if (window.brandInfo) {
      window.brandInfo.card_design = event.detail.cardDesign;
    }
    window.refreshNewsCards();
  });
  
  // Function to refresh brand info from server
  async function refreshBrandInfo() {
    try {
      const response = await fetch('/api/brand-info');
      if (response.ok) {
        const brandData = await response.json();
        window.brandInfo = brandData;
        console.log('🔄 Brand info refreshed from server:', brandData.card_design);
        window.refreshNewsCards();
      }
    } catch (error) {
      console.error('Failed to refresh brand info:', error);
    }
  }

  // Initialize brand info on page load
  async function initializeBrandInfo() {
    console.log('🚀 Initializing brand info...');
    console.log('📋 Initial brandInfo from context processor:', window.brandInfo);
    console.log('🎨 Card design from context processor:', window.brandInfo?.card_design);
    
    // Always fetch fresh data from server to ensure we have the latest settings
    console.log('📡 Fetching fresh brand info from server...');
    await refreshBrandInfo();
  }
  
  // Refresh brand info every 30 seconds to catch changes from other tabs
  setInterval(refreshBrandInfo, 30000);
  
  // Manual refresh button
  const refreshDesignBtn = document.getElementById('refresh-design-btn');
  if (refreshDesignBtn) {
    refreshDesignBtn.addEventListener('click', function() {
      this.classList.add('animate-spin');
      refreshBrandInfo().finally(() => {
        setTimeout(() => this.classList.remove('animate-spin'), 1000);
      });
    });
  }
  
  let searchTimeout;
  let currentSearchTerm = '';
  let currentPage = 1;
  let currentType = 'general';
  let isLoading = false;
  
  // Function to generate thumbnail URL using the project's thumbnailing mechanism
  function generateThumbnailUrl(imageData) {
    if (!imageData || !imageData.filepath) {
      return '/static/pic/placeholder.png';
    }
    
    try {
      let filepath = imageData.filepath.replace('static/', '');
      const lastDotIndex = filepath.lastIndexOf('.');
      if (lastDotIndex === -1) {
        return '/static/pic/placeholder.png';
      }
      
      const basePath = filepath.substring(0, lastDotIndex);
      const extension = filepath.substring(lastDotIndex);
      const thumbPath = basePath + '_thumb_landscape' + extension;
      
      return '/static/' + thumbPath;
    } catch (error) {
      console.error('Error generating thumbnail URL:', error);
      return '/static/pic/placeholder.png';
    }
  }
  
  // Function to safely get category name
  function getCategoryName(category) {
    if (!category || category === null || category === undefined) {
      return 'Tanpa Kategori';
    }
    
    // Handle different category data structures
    if (typeof category === 'string') {
      return category.trim() || 'Tanpa Kategori';
    } else if (typeof category === 'object') {
      return category.name || category.title || 'Tanpa Kategori';
    }
    
    return 'Tanpa Kategori';
  }
  
  // Function to generate star rating HTML
  function generateStarRating(rating) {
    if (!rating || !rating.has_ratings) {
      return '<span class="text-xs text-muted-foreground">Belum ada rating</span>';
    }
    
    const average = rating.average || 0;
    const count = rating.count || 0;
    const fullStars = Math.floor(average);
    const hasHalfStar = average % 1 >= 0.5;
    
    let starsHTML = '<div class="flex items-center mr-2">';
    
    for (let i = 1; i <= 5; i++) {
      if (i <= fullStars) {
        starsHTML += '<i class="fas fa-star text-yellow-400"></i>';
      } else if (i === fullStars + 1 && hasHalfStar) {
        starsHTML += '<i class="fas fa-star-half-alt text-yellow-400"></i>';
      } else {
        starsHTML += '<i class="far fa-star text-gray-300"></i>';
      }
    }
    
    starsHTML += '</div>';
    starsHTML += `<span class="text-xs font-medium text-primary">${average.toFixed(1)}</span>`;
    starsHTML += `<span class="ml-1 text-xs text-muted">(${count})</span>`;
    
    return starsHTML;
  }
  
  // Function to generate tags HTML
  function generateTagsHTML(tags) {
    if (!tags || tags.length === 0) {
      return '';
    }
    
    let tagsHTML = '<div class="news-tags">';
    tags.forEach(tag => {
      tagsHTML += `<span class="news-tag" onclick="filterByTag('${tag}')" title="Filter by tag #${tag}">${tag}</span>`;
    });
    tagsHTML += '</div>';
    
    return tagsHTML;
  }
  
  // Function to detect current type from page
  function detectCurrentType() {
    // Check URL parameters first
    const urlParams = new URLSearchParams(window.location.search);
    const urlType = urlParams.get('type');
    if (urlType) {
      return urlType;
    }
    
    // Check if we're on a specific news type page by looking at the active tab
    const activeTab = document.querySelector('.content-type-tab.active');
    if (activeTab) {
      return activeTab.dataset.type;
    }
    
    // Check the current URL path to determine type
    const path = window.location.pathname;
    if (path.includes('/news')) {
      return 'news';
    } else if (path.includes('/articles')) {
      return 'articles';
    } else if (path.includes('/utama')) {
      return 'utama';
    }
    
    // Default to general
    return 'general';
  }
  
  // Load initial content
  function loadInitialContent() {
    const urlParams = new URLSearchParams(window.location.search);
    const urlQuery = urlParams.get('q') || '';
    const urlCategory = urlParams.get('category') || '';
    const urlTag = urlParams.get('tag') || '';
    const urlType = urlParams.get('type') || detectCurrentType();
    const urlSort = urlParams.get('sort') || 'newest';
    
    if (urlQuery) {
      searchInput.value = urlQuery;
      currentSearchTerm = urlQuery;
    }
    if (urlCategory) {
      categoryFilter.value = urlCategory;
    }
    if (urlTag) {
      tagFilter.value = urlTag;
    }
    if (urlType) {
      currentType = urlType;
      updateContentTypeTabs(urlType);
    }
    if (urlSort) {
      sortFilter.value = urlSort;
    }
    

    
    performSearch(urlQuery, true);
  }
  
  // Switch content type
  window.switchContentType = function(type) {
    currentType = type;
    currentPage = 1;
    updateContentTypeTabs(type);
    updateURL();
    performSearch(currentSearchTerm);
  };
  
  // Update content type tabs
  function updateContentTypeTabs(activeType) {
    const tabs = document.querySelectorAll('.content-type-tab');
    tabs.forEach(tab => {
      tab.classList.remove('active');
      if (tab.dataset.type === activeType) {
        tab.classList.add('active');
      }
    });
  }
  
  // Update URL without reloading
  function updateURL() {
    const url = new URL(window.location);
    if (currentType !== 'general') {
      url.searchParams.set('type', currentType);
    } else {
      url.searchParams.delete('type');
    }
    if (currentSearchTerm) {
      url.searchParams.set('q', currentSearchTerm);
    } else {
      url.searchParams.delete('q');
    }
    if (categoryFilter.value) {
      url.searchParams.set('category', categoryFilter.value);
    } else {
      url.searchParams.delete('category');
    }
    if (tagFilter.value) {
      url.searchParams.set('tag', tagFilter.value);
    } else {
      url.searchParams.delete('tag');
    }
    if (sortFilter.value !== 'newest') {
      url.searchParams.set('sort', sortFilter.value);
    } else {
      url.searchParams.delete('sort');
    }
    window.history.replaceState({}, '', url);
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
    
    const params = new URLSearchParams();
    if (searchTerm.trim()) {
      params.append('q', searchTerm.trim());
    }
    
    const categoryValue = categoryFilter.value;
    if (categoryValue) {
      params.append('category', categoryValue);
    }
    
    const tagValue = tagFilter.value;
    if (tagValue) {
      params.append('tag', tagValue);
    }
    
    const sortValue = sortFilter.value;
    if (sortValue) {
      params.append('sort', sortValue);
    }
    const ageValue = ageFilter.value;
    if (ageValue) {
      params.append('age', ageValue);
    }
    
    if (currentType !== 'general') {
      params.append('type', currentType);
    }
    
    params.append('page', currentPage);
    params.append('per_page', 12);
    
    fetch(`/api/search/news?${params.toString()}`)
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          displaySearchResults(data, isInitialLoad);
        } else {
          console.error('Search error:', data.error);
          showErrorMessage('Terjadi kesalahan saat mencari berita');
        }
      })
      .catch(error => {
        console.error('Search request failed:', error);
        showErrorMessage('Gagal melakukan pencarian');
      })
      .finally(() => {
        isLoading = false;
      });
  }
  
  // Display search results
  function displaySearchResults(data, isInitialLoad = false) {
    const news = data.news;
    const pagination = data.pagination;
    const searchInfo = data.search_info;
    
    newsGrid.innerHTML = '';
    
    if (news.length === 0) {
      noResults.classList.remove('hidden');
      newsGrid.classList.add('hidden');
      updateResultCount(0, 0);
      return;
    }
    
    noResults.classList.add('hidden');
    newsGrid.classList.remove('hidden');
    
    news.forEach(newsItem => {
      const newsCard = createNewsCard(newsItem);
      newsGrid.appendChild(newsCard);
    });
    
    // Update result count with pagination info
    const startItem = (pagination.page - 1) * pagination.per_page + 1;
    const endItem = startItem + news.length - 1;
    

    
    if (pagination.pages > 1) {
      resultCount.textContent = `Menampilkan ${startItem}-${endItem} dari ${searchInfo.total_count} berita (Halaman ${pagination.page} dari ${pagination.pages})`;
    } else {
      resultCount.textContent = `Total ${searchInfo.total_count} berita`;
    }
    
    updatePagination(pagination);

    // Trigger ads refresh after news are rendered
    if (window.adsSystem) {
      setTimeout(() => {
        try { window.adsSystem.refreshAds(); } catch (e) {}
      }, 600);
    }
  }
  
  // Create news card HTML
  function createNewsCard(newsItem) {
    const card = document.createElement('article');
    
    // Get card design from brand settings
    const cardDesign = window.brandInfo?.card_design || 'classic';
    console.log('🎨 Creating card with design:', cardDesign, 'from brandInfo:', window.brandInfo?.card_design);
    card.className = `news-card ${cardDesign} bg-card rounded-lg border border-border overflow-hidden fade-in`;
    
    const imageUrl = generateThumbnailUrl(newsItem.image);
    
    let badges = '';
    
    // News/Article badge (left position)
    if (newsItem.is_news) {
      badges += '<span class="status-badge badge-news">Berita</span>';
    } else {
      badges += '<span class="status-badge badge-article">Artikel</span>';
    }
    
    // Premium badge (bottom right position)
    if (newsItem.is_premium) {
      badges += '<span class="premium-badge">Premium</span>';
    }
    // Age rating badge (use same overlay style)
    if (newsItem.age_rating) {
      badges += `<span class="overlay-badge">${newsItem.age_rating}</span>`;
    }
    
    // Main news badge (if not premium, use second left position)
    if (newsItem.is_main_news && !newsItem.is_premium) {
      badges += '<span class="status-badge badge-main">Utama</span>';
    }
    
    // For minimal design, use the reader.html related news card structure
    if (cardDesign === 'minimal') {
      console.log('🎨 Creating MINIMAL card design');
      card.innerHTML = `
        <a href="${newsItem.url}" class="block group h-full flex flex-col">
          <div class="aspect-video bg-secondary overflow-hidden relative">
            <img src="/static/pic/placeholder.png"
                 data-src="${imageUrl}"
                 alt="${newsItem.title}"
                 class="lazy w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                 onload="this.classList.add('loaded')"
                 onerror="this.onerror=null; this.src='/static/pic/placeholder.png';">
            ${badges}
          </div>
          <div class="p-4 flex flex-col">
            ${getCategoryName(newsItem.category) ? `
              <span class="inline-block mb-2 px-3 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary uppercase tracking-wider">
                ${getCategoryName(newsItem.category)}
              </span>
            ` : ''}
            <h3 class="text-base font-semibold text-card-foreground leading-snug line-clamp-2 mb-2 group-hover:text-primary transition-colors">
              ${highlightSearchTerms(stripMarkdown(newsItem.title), currentSearchTerm)}
            </h3>
            <div class="mt-auto pt-2 text-xs text-muted-foreground border-t border-border/50">
              ${newsItem.date ? `<span>${formatDate(newsItem.date)}</span>` : ''}
            </div>
          </div>
        </a>
      `;
    } else {
      // Original card structure for other designs
      console.log('🎨 Creating', cardDesign.toUpperCase(), 'card design');
      card.innerHTML = `
        <a href="${newsItem.url}" class="block group h-full flex flex-col">
          <div class="relative">
            <img src="/static/pic/placeholder.png"
                 data-src="${imageUrl}"
                 alt="${newsItem.title}"
                 class="news-image w-full"
                 onload="this.classList.add('loaded')"
                 onerror="this.onerror=null; this.src='/static/pic/placeholder.png';">
            
            ${badges}
          </div>
          
          <div class="p-5 flex flex-col flex-grow h-full">
            <div class="flex-grow flex flex-col">
              <div class="flex justify-between items-start mb-2">
                <h3 class="text-lg font-semibold text-card-foreground group-hover:text-primary transition-colors leading-snug line-clamp-2 min-h-[3rem]">
                  ${highlightSearchTerms(stripMarkdown(newsItem.title), currentSearchTerm)}
                </h3>
              </div>
              
              <p class="text-xs font-semibold text-primary mb-2 uppercase tracking-wide">
                ${getCategoryName(newsItem.category)}
              </p>
              
              <p class="text-sm text-muted-foreground mb-4 line-clamp-3 min-h-[3.5rem]">
                ${highlightSearchTerms(stripMarkdown(newsItem.excerpt || newsItem.content), currentSearchTerm)}
              </p>
              
              ${generateTagsHTML(newsItem.tags)}
            </div>
            
            <div class="mt-auto pt-3 border-t border-border text-xs text-muted-foreground">
              <div class="flex items-center justify-between mb-1">
                <span class="truncate">${newsItem.writer || newsItem.author?.username || 'Unknown'}</span>
                <span class="text-right">${formatDate(newsItem.date)} • ${newsItem.read_count || 0} reads</span>
              </div>
              ${newsItem.rating && newsItem.rating.has_ratings ? `
                <div class="flex items-center mb-1">
                  ${generateStarRating(newsItem.rating)}
                </div>
              ` : ''}
            </div>
          </div>
        </a>
      `;
    }
    
    setTimeout(() => {
      const img = card.querySelector('img');
      if (img && img.dataset.src) {
        img.src = img.dataset.src;
      }
    }, 50);
    
    return card;
  }
  
  // Strip Markdown formatting from text
  function stripMarkdown(text) {
    if (!text) return text;
    
    return text
      // Remove headers (# ## ### etc.)
      .replace(/^#{1,6}\s+/gm, '')
      // Remove bold/italic markers
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      .replace(/_(.*?)_/g, '$1')
      // Remove code blocks
      .replace(/```[\s\S]*?```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      // Remove links but keep text
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      // Remove images
      .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
      // Remove horizontal rules
      .replace(/^[-*_]{3,}$/gm, '')
      // Remove blockquotes
      .replace(/^>\s+/gm, '')
      // Remove list markers
      .replace(/^[\s]*[-*+]\s+/gm, '')
      .replace(/^[\s]*\d+\.\s+/gm, '')
      // Clean up extra whitespace
      .replace(/\n\s*\n/g, '\n')
      .replace(/\s+/g, ' ')
      .trim();
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
    if (currentSearchTerm.trim() || categoryFilter.value || tagFilter.value || sortFilter.value !== 'newest' || currentType !== 'general') {
      resultCount.textContent = `Menampilkan ${visible} dari ${total} berita`;
    } else {
      resultCount.textContent = `Total ${total} berita`;
    }
  }
  
  // Show error message
  function showErrorMessage(message) {
    resultCount.textContent = message;
    resultCount.style.color = 'hsl(var(--destructive))';
    setTimeout(() => {
      resultCount.style.color = '';
    }, 3000);
  }
  
  // Update pagination
  function updatePagination(pagination) {
    const paginationContainer = document.getElementById('pagination-container');
    
    if (pagination.pages <= 1) {
      paginationContainer.innerHTML = '';
      return;
    }
    
    let paginationHTML = '<nav class="flex items-center space-x-2">';
    
    if (pagination.has_prev) {
      paginationHTML += `
        <button onclick="changePage(${pagination.prev_num})" 
                class="px-3 py-2 text-sm border border-border rounded-lg hover:bg-secondary transition-colors">
          Sebelumnya
        </button>
      `;
    }
    
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
    newsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
    performSearch(currentSearchTerm);
  };
  
  // Filter by tag function (global for onclick handlers)
  window.filterByTag = function(tag) {
    event.stopPropagation(); // Prevent card click
    tagFilter.value = tag;
    tagFilter.classList.add('filter-applied');
    setTimeout(() => tagFilter.classList.remove('filter-applied'), 300);
    currentPage = 1;
    performSearch(currentSearchTerm);
    updateURL();
    newsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  
  // Clear all filters function (global for onclick handlers)
  window.clearAllFilters = function() {
    event.stopPropagation(); // Prevent card click
    searchInput.value = '';
    categoryFilter.value = '';
    tagFilter.value = '';
    sortFilter.value = 'newest';
    currentSearchTerm = '';
    currentPage = 1;
    performSearch('');
    updateURL();
    newsGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  
  // Event listeners
  searchInput.addEventListener('input', function() {
    currentSearchTerm = this.value;
    currentPage = 1;
    debouncedSearch(this.value);
    updateURL();
  });
  
  categoryFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
    updateURL();
  });

  tagFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
    updateURL();
  });

  sortFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
    updateURL();
  });
  
  ageFilter.addEventListener('change', function() {
    currentPage = 1;
    performSearch(currentSearchTerm);
    updateURL();
  });
  
  // Initialize brand info first, then load content
  initializeBrandInfo().then(() => {
    loadInitialContent();
  });
}); 