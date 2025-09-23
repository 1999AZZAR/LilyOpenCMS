/**
 * Story Creation Image Management
 * Handles image library, uploads, and insertion functionality
 */

(function() {
    'use strict';
    
    const ImageManager = {
        config: {
            endpoints: {
                images: '/api/images'
            },
            pagination: {
                perPage: 12,
                maxPerPage: 50
            }
        },
        
        init: function() {
            console.log('Initializing image management...');
            
            this.setupCustomRenderers();
            this.setupImageLoading();
            this.setupImageSelection();
            this.setupImageUpload();
            
            console.log('Image management initialized');
        },
        
        setupCustomRenderers: function() {
            // Custom image library renderer for content images
            window.renderImageLibraryCreate = (images) => {
                console.log('🎯 Custom renderImageLibraryCreate function called with', images?.length || 0, 'images');
                
                try {
                    const container = document.getElementById('image-library-section-create');
                    if (!container) {
                        console.warn('Image library container not found');
                        return;
                    }
                    
                    if (!images || images.length === 0) {
                        container.innerHTML = this.getEmptyStateHTML('content');
                        return;
                    }
                    
                    console.log('Rendering', images.length, 'images with custom function');
                    
                    const imageHtml = images.map(img => this.renderImageItem(img, 'content')).join('');
                    container.innerHTML = imageHtml;
                    
                    // Debug logging
                    setTimeout(() => {
                        console.log('Container after custom rendering:', container.innerHTML.substring(0, 200));
                        const images = container.querySelectorAll('img');
                        console.log('Found', images.length, 'img elements in container with custom renderer');
                    }, 100);
                    
                } catch (error) {
                    console.error('Error in custom renderImageLibraryCreate:', error);
                    const container = document.getElementById('image-library-section-create');
                    if (container) {
                        container.innerHTML = '<p class="col-span-full text-center text-red-500 py-4">Error rendering images.</p>';
                    }
                }
            };
        },
        
        setupImageLoading: function() {
            // Content images loading
            window.fetchAndDisplayContentImagesCreate = async (page = 1) => {
                console.log('User-specific content images loading...');
                const librarySection = document.getElementById('image-library-section-create');
                const paginationContainer = document.getElementById('content-image-pagination-controls-create');
                
                if (!librarySection || !paginationContainer) return;
                
                librarySection.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Loading your images...</p>';
                paginationContainer.innerHTML = '';
                
                try {
                    const response = await fetchWithCSRF(`${this.config.endpoints.images}?page=${page}&per_page=${this.config.pagination.perPage}&all_users=true`);
                    if (!response.ok) throw new Error('Failed to load content images');
                    
                    const data = await response.json();
                    console.log('User content images loaded:', data.items.length, 'images');
                    
                    if (data.items.length === 0) {
                        librarySection.innerHTML = this.getEmptyStateHTML('content');
                    } else {
                        if (window.renderImageLibraryCreate) {
                            window.renderImageLibraryCreate(data.items);
                            if (window.updateContentImagePaginationControlsCreate) {
                                window.updateContentImagePaginationControlsCreate(data);
                            }
                        }
                    }
                } catch (err) {
                    librarySection.innerHTML = '<p class="col-span-full text-red-500 py-4">Error loading images.</p>';
                    console.error("Content image load error (user):", err);
                }
            };
            
            // Header images loading
            window.loadHeaderLibraryCreate = async (page = 1) => {
                console.log('User-specific header images loading...');
                
                try {
                    // Try multiple API endpoints to get all user images
                    const endpoints = [
                        `${this.config.endpoints.images}?page=${page}&per_page=${this.config.pagination.maxPerPage}&all_users=true`,
                        `${this.config.endpoints.images}?page=${page}&per_page=${this.config.pagination.maxPerPage}`,
                        `${this.config.endpoints.images}?page=${page}&per_page=${this.config.pagination.perPage}&all_users=true`
                    ];
                    
                    for (const endpoint of endpoints) {
                        try {
                            const response = await fetchWithCSRF(endpoint);
                            if (response.ok) {
                                const data = await response.json();
                                const imgs = data.items || [];
                                console.log('Successfully got user images:', imgs.length, 'images');
                                return data;
                            }
                        } catch (e) {
                            console.log('Endpoint failed:', endpoint, e);
                        }
                    }
                    
                    throw new Error('All image loading attempts failed');
                    
                } catch (err) {
                    console.error('Error loading header images:', err);
                    throw err;
                }
            };
            
            // Display header images
            window.loadAndDisplayHeaderImages = async (page = 1) => {
                console.log('Loading and displaying header images...');
                const container = document.getElementById('header-image-library-create');
                const paginationContainer = document.getElementById('header-image-pagination-controls-create');
                
                if (!container || !paginationContainer) return;

                container.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Loading your images...</p>';
                paginationContainer.innerHTML = '';

                try {
                    const data = await window.loadHeaderLibraryCreate(page);
                    const imgs = data.items || [];
                    console.log('Images loaded:', imgs.length, 'total images');
                    
                    if (imgs.length === 0) {
                        container.innerHTML = this.getEmptyStateHTML('header');
                    } else {
                        console.log('Rendering', imgs.length, 'images to container');
                        
                        const imageHtml = imgs.map(img => this.renderImageItem(img, 'header')).join('');
                        container.innerHTML = imageHtml;
                        
                        // Add pagination controls
                        if (data.total_pages > 1) {
                            console.log('Adding pagination controls for', data.total_pages, 'pages');
                            const paginationHtml = this.generatePaginationControls(data, page);
                            paginationContainer.innerHTML = paginationHtml;
                        }
                    }
                } catch (err) {
                    console.error('Error loading header images:', err);
                    container.innerHTML = '<p class="col-span-full text-center text-red-500 py-4">Error loading images.</p>';
                }
            };
        },
        
        setupImageSelection: function() {
            // Insert image from library into content
            window.insertImageFromLibrary = (imageUrl, altText) => {
                console.log('🎯 insertImageFromLibrary called with:', imageUrl, altText);
                
                const markdown = `![${altText || 'Image'}](${imageUrl})`;
                
                // Try multiple ways to get the SimpleMDE editor
                let cm = this.getCodeMirrorInstance();
                
                if (cm) {
                    try {
                        cm.replaceSelection(markdown);
                        console.log('✅ Image markdown inserted via CodeMirror');
                        this.closeImageModal();
                        return;
                    } catch (error) {
                        console.error('Error inserting via CodeMirror:', error);
                    }
                }
                
                // Fallback to textarea
                const textarea = document.getElementById('news-content') || document.getElementById('story-content');
                if (textarea) {
                    const cursorPos = textarea.selectionStart;
                    const textBefore = textarea.value.substring(0, cursorPos);
                    const textAfter = textarea.value.substring(cursorPos);
                    textarea.value = textBefore + markdown + textAfter;
                    textarea.selectionStart = textarea.selectionEnd = cursorPos + markdown.length;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    this.closeImageModal();
                    console.log('✅ Image markdown inserted directly into textarea');
                } else {
                    console.warn('❌ No editor or textarea found, cannot insert image');
                    alert('Tidak dapat menyisipkan gambar. Silakan salin URL gambar dan sisipkan secara manual.');
                }
            };
            
            // Select header image
            window.selectHeaderImage = (imageUrl, imageId) => {
                console.log('Selected header image:', imageUrl, 'ID:', imageId);
                
                const preview = document.getElementById('featured-preview-create');
                const noImagePlaceholder = document.getElementById('no-image-placeholder');
                const imageIdInput = document.getElementById('news-image-id');
                
                if (preview) {
                    preview.src = imageUrl;
                    preview.classList.remove('hidden');
                }
                if (noImagePlaceholder) {
                    noImagePlaceholder.classList.add('hidden');
                }
                if (imageIdInput) {
                    imageIdInput.value = imageId;
                }
                
                this.closeHeaderModal();
            };
        },
        
        setupImageUpload: function() {
            // This would handle image upload functionality
            // For now, we'll just set up the basic structure
            console.log('Image upload functionality ready for implementation');
        },
        
        getCodeMirrorInstance: function() {
            // Method 1: Check if addSimplemde is available
            if (window.addSimplemde) {
                if (window.addSimplemde.codemirror) {
                    return window.addSimplemde.codemirror;
                } else if (window.addSimplemde.simplemde && window.addSimplemde.simplemde.codemirror) {
                    return window.addSimplemde.simplemde.codemirror;
                }
            }
            
            // Method 2: Check global SimpleMDE instances
            if (window.SimpleMDE && window.SimpleMDE.instances && window.SimpleMDE.instances.length > 0) {
                return window.SimpleMDE.instances[0].codemirror;
            }
            
            return null;
        },
        
        renderImageItem: function(img, type) {
            // Debug the image object structure
            console.log('Processing image in renderer:', img);
            
            // Try different possible URL field names
            let imageUrl = img.url || img.image_url || img.file_url || img.path || img.filename;
            let description = img.description || img.alt || img.name || img.title || 'Image';
            
            console.log('Extracted URL:', imageUrl, 'Description:', description);
            
            // Ensure we have a proper URL
            if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/')) {
                imageUrl = '/' + imageUrl;
            }
            
            // If still no valid URL, skip this image
            if (!imageUrl || imageUrl === 'null' || imageUrl === 'undefined') {
                console.warn('Skipping image with invalid URL:', img);
                return '';
            }
            
            console.log('Processing image:', img.id, 'Final URL:', imageUrl, 'Description:', description);
            
            const onClick = type === 'header' 
                ? `selectHeaderImage('${imageUrl}', ${img.id})`
                : `window.insertImageFromLibrary('${imageUrl}', '${description}')`;
            
            const buttonText = type === 'header' ? 'Pilih' : 'Sisipkan';
            
            return `
                <div class="relative group cursor-pointer border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-shadow duration-200" 
                     onclick="${onClick}">
                    <img src="${imageUrl}" alt="${description}" 
                         class="w-full h-40 object-cover"
                         onload="console.log('Image loaded successfully:', '${imageUrl}')"
                         onerror="console.error('Image failed to load:', '${imageUrl}')">
                    <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-200 flex items-center justify-center">
                        <span class="text-white opacity-0 group-hover:opacity-100 font-medium">${buttonText}</span>
                    </div>
                </div>
            `;
        },
        
        getEmptyStateHTML: function(type) {
            return `
                <div class="col-span-full text-center py-8">
                    <i class="fas fa-images text-gray-400 text-4xl mb-4"></i>
                    <p class="text-gray-500 mb-2">Belum ada gambar</p>
                    <p class="text-sm text-gray-400">Upload gambar baru menggunakan form di atas</p>
                </div>
            `;
        },
        
        generatePaginationControls: function(data, currentPage) {
            const totalPages = data.total_pages;
            const totalItems = data.total_items;
            const perPage = data.per_page;
            
            let paginationHtml = `
                <div class="flex items-center justify-between text-sm text-gray-700 mb-4">
                    <div>
                        Showing ${((currentPage - 1) * perPage) + 1} to ${Math.min(currentPage * perPage, totalItems)} of ${totalItems} images
                    </div>
                    <div class="flex space-x-2">
            `;
            
            // Previous button
            if (currentPage > 1) {
                paginationHtml += `
                    <button onclick="window.loadAndDisplayHeaderImages(${currentPage - 1})" 
                            class="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors">
                        <i class="fas fa-chevron-left mr-1"></i>Previous
                    </button>
                `;
            }
            
            // Page numbers
            const startPage = Math.max(1, currentPage - 2);
            const endPage = Math.min(totalPages, currentPage + 2);
            
            for (let i = startPage; i <= endPage; i++) {
                if (i === currentPage) {
                    paginationHtml += `
                        <span class="px-3 py-2 bg-blue-600 text-white rounded-lg">${i}</span>
                    `;
                } else {
                    paginationHtml += `
                        <button onclick="window.loadAndDisplayHeaderImages(${i})" 
                                class="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors">
                            ${i}
                        </button>
                    `;
                }
            }
            
            // Next button
            if (currentPage < totalPages) {
                paginationHtml += `
                    <button onclick="window.loadAndDisplayHeaderImages(${currentPage + 1})" 
                            class="px-3 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors">
                        Next<i class="fas fa-chevron-right ml-1"></i>
                    </button>
                `;
            }
            
            paginationHtml += `
                    </div>
                </div>
            `;
            
            return paginationHtml;
        },
        
        closeImageModal: function() {
            const modal = document.getElementById('image-insert-modal-create');
            if (modal) modal.classList.add('hidden');
        },
        
        closeHeaderModal: function() {
            const modal = document.getElementById('image-header-modal-create');
            if (modal) modal.classList.add('hidden');
        }
    };
    
    // Initialize when DOM is ready
    function init() {
        if (document.readyState !== 'loading') {
            ImageManager.init();
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                ImageManager.init();
            });
        }
    }
    
    // Export for global access
    window.StoryImageManager = ImageManager;
    
    // Auto-initialize
    init();
    
})();
