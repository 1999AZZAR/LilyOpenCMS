// Initialize SimpleMDE editor (guarded, supports both #news-content and #story-content)
let addSimplemde = null;
window.addSimplemde = null;
window.simplemde = null; // compatibility

function initSimpleMDEWith(el) {
    try {
        addSimplemde = new SimpleMDE({
            element: el,
            spellChecker: true,
            autofocus: true,
            placeholder: "Tulis artikel Anda di sini:\n- Mulai dengan pengantar yang menarik.\n- Gunakan heading, daftar, atau teks tebal untuk struktur.\n- Klik toolbar untuk opsi format atau 'Panduan' untuk bantuan Markdown",
            autosave: {
                enabled: true,
                uniqueId: "news-content-autosave",
                delay: 1000,
            },
            toolbar: false, // Hide default toolbar; we provide a custom one
            status: false, // Hide default status bar
            forceSync: true, // Keep underlying textarea in sync
            autoDownloadFontAwesome: false,
            renderingConfig: {
                singleLineBreaks: false,
                codeSyntaxHighlighting: true,
            },
        });
        window.addSimplemde = addSimplemde;
        window.simplemde = addSimplemde;
        return true;
    } catch (e) {
        console.error('SimpleMDE init failed:', e);
        return false;
    }
}

function waitAndInitSimpleMDE(maxAttempts = 80, intervalMs = 100) {
    let attempts = 0;
    const timer = setInterval(() => {
        attempts++;
        // Critical: only initialize once the mapped textarea #news-content exists,
        // to avoid binding to #story-content which is replaced later.
        const el = document.getElementById('news-content');
        if (el && el.tagName && el.tagName.toLowerCase() === 'textarea') {
            clearInterval(timer);
            initSimpleMDEWith(el);
        } else if (attempts >= maxAttempts) {
            clearInterval(timer);
            // Final fallback: try again for #news-content; if still missing, do nothing to avoid broken init
            const fallback = document.getElementById('news-content');
            if (fallback && fallback.tagName && fallback.tagName.toLowerCase() === 'textarea') {
                initSimpleMDEWith(fallback);
            } else {
                console.warn('SimpleMDE not initialized: #news-content not found.');
            }
        }
    }, intervalMs);
}

document.addEventListener('DOMContentLoaded', () => {
    waitAndInitSimpleMDE();
});

// Get news_id from URL parameters to determine if we're in edit mode
const urlParams = new URLSearchParams(window.location.search);
const newsId = urlParams.get('news_id');
const albumId = urlParams.get('album_id');
const isEditMode = newsId !== null;
let isSubmitting = false; // guard to prevent double submission

// Modal Sisipkan Tautan Logika
function openLinkInsertModal(editor) {
    const modal = document.getElementById('link-insert-modal');
    const linkTextInput = document.getElementById('link-text');
    const linkUrlInput = document.getElementById('link-url');
    const insertBtn = document.getElementById('insert-link-btn');
    const cancelBtn = document.getElementById('cancel-link-btn');

    if (!modal || !linkTextInput || !linkUrlInput || !insertBtn || !cancelBtn) {
        console.error("Link insert modal elements not found!");
        return;
    }

    // Dapatkan teks yang dipilih
    const cm = editor.codemirror;
    const selectedText = cm.getSelection();
    linkTextInput.value = selectedText || '';
    linkUrlInput.value = 'https://'; // Default value

    // Tampilkan modal
    modal.classList.remove('hidden');

    // Tangani sisipkan
    const insertLink = () => {
        const text = linkTextInput.value.trim();
        const url = linkUrlInput.value.trim();
        if (url && url !== 'https://') { // Ensure URL is provided and not just the default
            const markdownLink = `[${text || url}](${url})`;
            cm.replaceSelection(markdownLink);
            closeModal();
        } else {
            console.warn("URL is required to insert a link.");
            linkUrlInput.focus();
        }
    };

    // Tangani batal
    const closeModal = () => {
        modal.classList.add('hidden');
        linkTextInput.value = '';
        linkUrlInput.value = '';
        // Remove event listeners to prevent duplicates if modal is reopened
        insertBtn.removeEventListener('click', insertLink);
        cancelBtn.removeEventListener('click', closeModal);
        linkUrlInput.removeEventListener('keypress', handleEnter);
    };

    // Tangani Enter key
    const handleEnter = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent potential form submission if inside a form
            insertLink();
        }
    };

    // Lampirkan event listener (ensure they are added only once)
    insertBtn.addEventListener('click', insertLink);
    cancelBtn.addEventListener('click', closeModal);
    linkUrlInput.addEventListener('keypress', handleEnter);

    // Fokus pada URL input
    linkUrlInput.focus();
}


// --- Pagination Helpers (Inline for Create Page) ---
function generatePageNumbers(currentPage, totalPages, edgeCount = 1, currentCount = 2) {
    if (totalPages <= 1) return [];
    const pages = new Set();
    for (let i = 1; i <= Math.min(edgeCount, totalPages); i++) pages.add(i);
    for (let i = Math.max(1, totalPages - edgeCount + 1); i <= totalPages; i++) pages.add(i);
    for (let i = Math.max(1, currentPage - currentCount); i <= Math.min(totalPages, currentPage + currentCount); i++) pages.add(i);
    const sortedPages = Array.from(pages).sort((a, b) => a - b);
    const result = [];
    let lastPage = 0;
    for (const page of sortedPages) {
        if (page > lastPage + 1) result.push(null); // Ellipsis
        result.push(page);
        lastPage = page;
    }
    return result;
}

function createPaginationElement(tag, classes, content, ariaLabel = null, title = null, disabled = false, onClick = null) {
    const el = document.createElement(tag);
    el.className = classes;
    el.innerHTML = content;
    if (ariaLabel) el.setAttribute('aria-label', ariaLabel);
    if (title) el.title = title;
    if (disabled) el.setAttribute('aria-disabled', 'true');
    if (onClick && !disabled) el.onclick = () => onClick();
    return el;
}

// --- Content Image Insert Modal Pagination (Create Page) ---
function updateContentImagePaginationControlsCreate(paginationData) {
    const controlsContainer = document.getElementById('content-image-pagination-controls-create');
    if (!controlsContainer) return;
    controlsContainer.innerHTML = '';
    if (!paginationData || paginationData.total_pages <= 1) return;

    const { page: currentPage, total_pages: totalPages } = paginationData;
    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Content Image Pagination');
    nav.className = 'flex flex-wrap items-center justify-center mt-4 gap-2 overflow-x-auto';

    const buttonClasses = 'button button-outline px-3 py-1 rounded-md hover:bg-primary/10 text-sm';
    const disabledClasses = 'button button-outline px-3 py-1 rounded-md opacity-50 cursor-not-allowed text-sm';
    const currentClasses = 'button button-primary px-3 py-1 rounded-md text-sm';
    const ellipsisClasses = 'h-8 px-1 inline-flex items-center text-muted-foreground text-sm font-medium';
    const firstIcon = `&laquo;`, prevIcon = `&lsaquo;`, nextIcon = `&rsaquo;`, lastIcon = `&raquo;`;

    nav.appendChild(createPaginationElement(currentPage > 1 ? 'button' : 'span', currentPage > 1 ? buttonClasses : disabledClasses, firstIcon, 'First Page', 'First Page', currentPage <= 1, () => fetchAndDisplayContentImagesCreate(1)));
    nav.appendChild(createPaginationElement(currentPage > 1 ? 'button' : 'span', currentPage > 1 ? buttonClasses : disabledClasses, prevIcon, 'Previous Page', 'Previous Page', currentPage <= 1, () => fetchAndDisplayContentImagesCreate(currentPage - 1)));
    generatePageNumbers(currentPage, totalPages, 1, 1).forEach(page_num => {
        if (page_num === null) nav.appendChild(createPaginationElement('span', ellipsisClasses, '...', null, null, true));
        else if (page_num === currentPage) {
            const el = createPaginationElement('span', currentClasses, page_num, null, `Page ${page_num}`, true);
            el.setAttribute('aria-current', 'page');
            nav.appendChild(el);
        } else nav.appendChild(createPaginationElement('button', buttonClasses, page_num, `Go to page ${page_num}`, `Go to page ${page_num}`, false, () => fetchAndDisplayContentImagesCreate(page_num)));
    });
    nav.appendChild(createPaginationElement(currentPage < totalPages ? 'button' : 'span', currentPage < totalPages ? buttonClasses : disabledClasses, nextIcon, 'Next Page', 'Next Page', currentPage >= totalPages, () => fetchAndDisplayContentImagesCreate(currentPage + 1)));
    nav.appendChild(createPaginationElement(currentPage < totalPages ? 'button' : 'span', currentPage < totalPages ? buttonClasses : disabledClasses, lastIcon, 'Last Page', 'Last Page', currentPage >= totalPages, () => fetchAndDisplayContentImagesCreate(totalPages)));
    controlsContainer.appendChild(nav);
}

// --- Header Image Library Pagination (Create Page) ---
function updateHeaderImagePaginationControlsCreate(paginationData) {
    const controlsContainer = document.getElementById('header-image-pagination-controls-create');
    if (!controlsContainer) return;
    controlsContainer.innerHTML = '';
    if (!paginationData || paginationData.total_pages <= 1) return;

    const { page: currentPage, total_pages: totalPages } = paginationData;
    const nav = document.createElement('nav');
    nav.setAttribute('aria-label', 'Header Image Pagination');
    nav.className = 'flex flex-wrap items-center justify-center mt-4 gap-2 overflow-x-auto';

    // Reusing the same classes and icons as content pagination
    const buttonClasses = 'button button-outline px-3 py-1 rounded-md hover:bg-primary/10 text-sm';
    const disabledClasses = 'button button-outline px-3 py-1 rounded-md opacity-50 cursor-not-allowed text-sm';
    const currentClasses = 'button button-primary px-3 py-1 rounded-md text-sm';
    const ellipsisClasses = 'h-8 px-1 inline-flex items-center text-muted-foreground text-sm font-medium';
    const firstIcon = `&laquo;`, prevIcon = `&lsaquo;`, nextIcon = `&rsaquo;`, lastIcon = `&raquo;`;

    // Generate pagination elements, calling loadHeaderLibraryCreate on click
    nav.appendChild(createPaginationElement(currentPage > 1 ? 'button' : 'span', currentPage > 1 ? buttonClasses : disabledClasses, firstIcon, 'First Page', 'First Page', currentPage <= 1, () => loadHeaderLibraryCreate(1)));
    nav.appendChild(createPaginationElement(currentPage > 1 ? 'button' : 'span', currentPage > 1 ? buttonClasses : disabledClasses, prevIcon, 'Previous Page', 'Previous Page', currentPage <= 1, () => loadHeaderLibraryCreate(currentPage - 1)));
    generatePageNumbers(currentPage, totalPages, 1, 1).forEach(page_num => {
        if (page_num === null) nav.appendChild(createPaginationElement('span', ellipsisClasses, '...', null, null, true));
        else if (page_num === currentPage) {
            const el = createPaginationElement('span', currentClasses, page_num, null, `Page ${page_num}`, true);
            el.setAttribute('aria-current', 'page');
            nav.appendChild(el);
        } else nav.appendChild(createPaginationElement('button', buttonClasses, page_num, `Go to page ${page_num}`, `Go to page ${page_num}`, false, () => loadHeaderLibraryCreate(page_num)));
    });
    nav.appendChild(createPaginationElement(currentPage < totalPages ? 'button' : 'span', currentPage < totalPages ? buttonClasses : disabledClasses, nextIcon, 'Next Page', 'Next Page', currentPage >= totalPages, () => loadHeaderLibraryCreate(currentPage + 1)));
    nav.appendChild(createPaginationElement(currentPage < totalPages ? 'button' : 'span', currentPage < totalPages ? buttonClasses : disabledClasses, lastIcon, 'Last Page', 'Last Page', currentPage >= totalPages, () => loadHeaderLibraryCreate(totalPages)));
    controlsContainer.appendChild(nav);
}

async function fetchAndDisplayContentImagesCreate(page = 1) {
    const librarySection = document.getElementById('image-library-section-create');
    const paginationContainer = document.getElementById('content-image-pagination-controls-create');
    if (!librarySection || !paginationContainer) return;
    librarySection.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Loading images...</p>';
    paginationContainer.innerHTML = '';
    try {
        const response = await fetch(`/api/images?page=${page}&per_page=12`); // Use pagination
        if (!response.ok) throw new Error('Failed to load content images');
        const data = await response.json();
        renderImageLibraryCreate(data.items);
        updateContentImagePaginationControlsCreate(data);
    } catch (err) {
        librarySection.innerHTML = '<p class="col-span-full text-center text-red-500 py-4">Error loading images.</p>';
        console.error("Content image load error (create):", err);
    }
}

// Ambil dan isi kategori
async function fetchCategories() {
    try {
        const response = await fetch('/api/categories?grouped=true');
        if (!response.ok) throw new Error('Gagal mengambil kategori');

        const groupedData = await response.json();
        const categoryDropdown = document.getElementById('news-category');
        if (!categoryDropdown) {
            console.error("Category dropdown (#news-category) not found.");
            return;
        }

        categoryDropdown.innerHTML = '<option value="" disabled selected>Pilih kategori...</option>';
        
        // Add optgroups for each category group
        groupedData.forEach(groupData => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = groupData.group.name;
            
            groupData.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                optgroup.appendChild(option);
            });
            
            categoryDropdown.appendChild(optgroup);
        });
    } catch (error) {
        console.error('Error mengambil kategori:', error);
        // Assuming showToast is globally available from toast.js
        if (typeof showToast === 'function') {
            showToast('error', 'Gagal memuat kategori.');
        }
    }
}

// Modal Sisip Gambar untuk Tambah Berita JS
function openImageInsertModalCreate() {
    
    const modal = document.getElementById('image-insert-modal-create');
    if (!modal) {
        console.error("Content image insert modal (#image-insert-modal-create) not found.");
        return;
    }
    modal.classList.remove('hidden');

    // Ensure correct sections are shown/hidden initially
    const librarySection = document.getElementById('image-library-section-create');
    const urlSection = document.getElementById('image-url-section-create');
    const libraryRadio = document.querySelector('input[name="image-source-create"][value="library"]');

    if (librarySection && urlSection && libraryRadio) {
        librarySection.classList.remove('hidden');
        urlSection.classList.add('hidden');
        libraryRadio.checked = true; // Default to library view
    }

    // Attach change listeners for radio buttons
    document.getElementsByName('image-source-create').forEach(radio => {
        // Use a flag to prevent adding listener multiple times if modal is reopened
        if (!radio.dataset.listenerAttached) {
            radio.addEventListener('change', e => {
                const val = e.target.value;
                if (librarySection) librarySection.classList.toggle('hidden', val === 'url');
                if (urlSection) urlSection.classList.toggle('hidden', val !== 'url');
            });
            radio.dataset.listenerAttached = 'true';
        }
    });

    fetchAndDisplayContentImagesCreate(1); // Fetch first page on open
}

function renderImageLibraryCreate(imgs) { // Separate function to render images
    const container = document.getElementById('image-library-section-create');
    if (!container) return;

    container.innerHTML = (imgs || []).map(image => { // Handle potential empty array
        // --- Thumbnail Logic (Content Insert Modal Grid) ---
        const placeholderImg = '/static/pic/placeholder.png';
        const fullImageUrl = image.file_url || image.url || '/static/pic/placeholder.png';
        let squareThumbUrl = placeholderImg; // For the grid display

        if (image.filepath) {
            const pathWithoutStatic = image.filepath.replace('static/', '', 1);
            const lastDotIndex = pathWithoutStatic.lastIndexOf('.');
            if (lastDotIndex !== -1) {
                const base_path = pathWithoutStatic.substring(0, lastDotIndex);
                const extension = pathWithoutStatic.substring(lastDotIndex);
                squareThumbUrl = `/static/${base_path}_thumb_square${extension}`; // Use square for grid
            } else {
                squareThumbUrl = fullImageUrl; // Fallback
            }
        } else {
            squareThumbUrl = fullImageUrl; // Fallback for external URLs
        }
        // --- End Thumbnail Logic ---
        return `
            <div class="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-lg transition p-3 flex flex-col gap-2 group cursor-pointer hover:border-blue-400">
            <img src="${squareThumbUrl}" onerror="this.onerror=null;this.src='${placeholderImg}'" alt="${image.filename||'Image'}" class="w-full aspect-square object-cover rounded-lg mb-2 shadow-sm group-hover:shadow-md">
            <button class="select-image-create bg-blue-600 text-white py-1 rounded-lg font-semibold" data-url="${fullImageUrl}" data-alt="${image.filename||''}">Select</button>
            </div>
        `;
    }).join('');

    // Re-attach listeners after rendering
    document.querySelectorAll('.select-image-create').forEach(btn => {
        // Remove old listener if exists to prevent duplicates
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        // Add new listener
        newBtn.addEventListener('click', () => {
            const url = newBtn.dataset.url;
            const alt = newBtn.dataset.alt;
            addSimplemde.codemirror.replaceSelection(`![${alt||null}](${url})`);
            closeImageInsertModalCreate();
        });
    });
}

function closeImageInsertModalCreate(){
    const modal = document.getElementById('image-insert-modal-create');
    if (modal) modal.classList.add('hidden');
}

// Modal Pilih Gambar Unggulan untuk Tambah Berita JS
async function loadHeaderLibraryCreate(page = 1) {
    const container = document.getElementById('header-image-library-create');
    const paginationContainer = document.getElementById('header-image-pagination-controls-create');
    if (!container || !paginationContainer) return;

    container.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Loading images...</p>'; // Loading state
    paginationContainer.innerHTML = ''; // Clear old pagination

    try {
        const response = await fetch(`/api/images?page=${page}&per_page=12`); // Fetch paginated images
        if (!response.ok) throw new Error('Failed to load header images');
        const data = await response.json();
        const imgs = data.items || [];

        container.innerHTML = imgs.map(image => {
             // --- Thumbnail Logic (Featured Image Modal Grid) ---
            const placeholderImg = '/static/pic/placeholder.png';
            const fullImageUrl = image.file_url || image.url || '/static/pic/placeholder.png';
            let squareThumbUrl = placeholderImg; // For the grid display
            let landscapeThumbUrl = placeholderImg; // For the preview after selection

            if (image.filepath) {
                const pathWithoutStatic = image.filepath.replace('static/', '', 1);
                const lastDotIndex = pathWithoutStatic.lastIndexOf('.');
                if (lastDotIndex !== -1) {
                    const base_path = pathWithoutStatic.substring(0, lastDotIndex);
                    const extension = pathWithoutStatic.substring(lastDotIndex);
                    squareThumbUrl = `/static/${base_path}_thumb_square${extension}`; // Use square for grid
                    landscapeThumbUrl = `/static/${base_path}_thumb_landscape${extension}`; // Use landscape for preview data
                } else {
                    squareThumbUrl = fullImageUrl; // Fallback
                    landscapeThumbUrl = fullImageUrl; // Fallback
                }
            } else {
                squareThumbUrl = fullImageUrl; // Fallback for external URLs
                landscapeThumbUrl = fullImageUrl; // Fallback for external URLs
            }
            // --- End Thumbnail Logic ---
            return `
            <div class="p-2 group cursor-pointer border border-transparent hover:border-yellow-400 rounded-lg transition duration-150">
                <img src="${squareThumbUrl}" onerror="this.onerror=null;this.src='${placeholderImg}'" alt="${image.filename || 'Image'}" class="w-full aspect-square object-cover rounded-lg mb-2 shadow-sm group-hover:shadow-md" loading="lazy">
                <button class="select-header-create mt-2 w-full bg-yellow-500 text-gray-900 py-1 rounded-lg font-semibold" data-thumb-url="${landscapeThumbUrl}" data-id="${image.id}">Select</button>
            </div>
            `;
        }).join('');

        // Re-attach listeners
        container.querySelectorAll('.select-header-create').forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', () => {
                const preview = document.getElementById('featured-preview-create');
                const imageIdInput = document.getElementById('news-image-id');
                if (preview && imageIdInput) {
                    preview.src = newBtn.dataset.thumbUrl; // Use the landscape thumb URL for preview
                    imageIdInput.value = newBtn.dataset.id; // Set the hidden input value
                    preview.classList.remove('hidden');
                }
                closeImageHeaderModalCreate();
            });
        });

        // Update pagination controls
        updateHeaderImagePaginationControlsCreate(data);
    } catch (err) {
        console.error('Error loading header images:', err);
        container.innerHTML = '<p class="col-span-full text-center text-red-500 py-4">Error loading images.</p>';
    }
}

function openImageHeaderModalCreate() {
    
    const modal = document.getElementById('image-header-modal-create');
    if (modal) {
        modal.classList.remove('hidden');
        loadHeaderLibraryCreate(1); // Load first page when opening
    } else {
        console.error("Featured image modal (#image-header-modal-create) not found.");
    }
}

function closeImageHeaderModalCreate() {
    const modal = document.getElementById('image-header-modal-create');
    if (modal) modal.classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
    fetchCategories();

    // Edit-mode quick prefill for date and age rating on public create_story.html
    if (isEditMode) {
        (async () => {
            try {
                const res = await fetch(`/api/news/${newsId}`);
                if (!res.ok) throw new Error('Failed to fetch article');
                const a = await res.json();
                const dateEl = document.getElementById('news-date');
                if (dateEl && a && a.date) {
                    try { dateEl.value = (a.date || '').split('T')[0]; } catch (_) {}
                }
                const ageEl = document.getElementById('news-age-rating');
                if (ageEl && a && a.age_rating) {
                    ageEl.value = a.age_rating;
                }
            } catch (_) {}
        })();
    }

    // Attach listener for the featured image modal button
    const openHeaderBtn = document.getElementById('open-header-modal-btn');
    if (openHeaderBtn) {
        openHeaderBtn.addEventListener('click', openImageHeaderModalCreate);
    } else {
        console.warn("Button #open-header-modal-btn not found.");
    }

    // Attach listener for closing header modal
    const closeHeaderBtn = document.getElementById('header-image-close-create');
    if (closeHeaderBtn) {
        closeHeaderBtn.addEventListener('click', closeImageHeaderModalCreate);
    }

    // Attach listener for uploading header image
    const uploadHeaderBtn = document.getElementById('header-upload-btn-create');
    if (uploadHeaderBtn) {
        uploadHeaderBtn.addEventListener('click', async () => {
            const fileInput = document.getElementById('header-upload-file-create');
            const urlInput = document.getElementById('header-upload-url-create');
            const nameInput = document.getElementById('header-upload-name-create');
            const urlValue = urlInput.value.trim();
            const nameValue = nameInput.value.trim();
            const fd = new FormData();

            if (fileInput.files.length) {
                fd.append('file', fileInput.files[0]);
            } else if (urlValue) {
                fd.append('url', urlValue);
            } else {
                if (typeof showToast === 'function') showToast('warning', 'Pilih berkas atau masukkan URL.');
                return; // No file or URL provided
            }
            if (nameValue) fd.append('name', nameValue);
            fd.append('is_visible', 'false'); // Make uploaded header images hidden by default

            try {
                const resp = await fetch('/api/images', { method: 'POST', body: fd });
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.error || 'Upload failed');

                // Clear inputs after successful upload
                nameInput.value = '';
                fileInput.value = ''; // Clear file input
                urlInput.value = '';

                await loadHeaderLibraryCreate(); // Refresh the library
                if (typeof showToast === 'function') showToast('success', 'Gambar berhasil diunggah!');
            } catch (err) {
                console.error('Header image upload error:', err);
                if (typeof showToast === 'function') showToast('error', 'Gagal mengunggah gambar: ' + err.message);
            }
        });
    }

    // Resolve form element once and use it for direct binding
    const addNewsForm = document.getElementById('add-news-form') || document.getElementById('create-story-form');
    if (addNewsForm) {
        // Ensure native validation does not block custom flow
        try { addNewsForm.setAttribute('novalidate', 'novalidate'); } catch(_) {}
        addNewsForm.addEventListener('submit', handleNewsFormSubmit);
    }

    // Note: Avoid adding a delegated submit handler to prevent double submission

    // Unified submit handler (can be used with direct binding or delegated capture)
    async function handleNewsFormSubmit(e) {
        e.preventDefault();
        if (isSubmitting) return; // prevent duplicate sends
        isSubmitting = true;

            // Basic validation
            const title = document.getElementById('news-title').value.trim();
            const content = addSimplemde.value().trim();
            const category = document.getElementById('news-category').value;
            const date = document.getElementById('news-date').value;
            const ageRating = document.getElementById('news-age-rating').value;

            const errors = [];
            if (!title) errors.push('Judul artikel harus diisi');
            if (!content) errors.push('Konten artikel harus diisi');
            if (!category) errors.push('Kategori harus dipilih');
            if (!date) errors.push('Tanggal harus diisi');
            if (!ageRating) errors.push('Rating usia konten harus dipilih');

            if (errors.length > 0) {
                if (typeof showToast === 'function') {
                    showToast('error', errors.join(', '));
                } else {
                    alert(errors.join(', '));
                }
                return;
            }

            const isPublishButton = e.submitter && e.submitter.name === 'publish';
            const formData = new FormData(); // Use FormData to handle potential file uploads if needed later
            formData.append('title', document.getElementById('news-title').value.trim());
            formData.append('content', addSimplemde.value().trim());
            formData.append('tagar', document.getElementById('news-tagar').value.trim());
            formData.append('date', document.getElementById('news-date').value);
            formData.append('category', document.getElementById('news-category').value);
            formData.append('age_rating', document.getElementById('news-age-rating').value);
            // Handle elements that may not exist in user story form
            const isPremiumElement = document.getElementById('news-is-premium');
            const prizeElement = document.getElementById('news-prize');
            const prizeCoinTypeElement = document.getElementById('news-prize-coin-type');
            
            formData.append('is_news', isPremiumElement ? isPremiumElement.checked : false);
            formData.append('is_main_news', false); // Fixed: news-main element doesn't exist, default to false
            formData.append('is_premium', isPremiumElement ? isPremiumElement.checked : false);
            formData.append('is_visible', isPublishButton);
            formData.append('writer', document.getElementById('news-writer').value.trim());
            formData.append('external_source', document.getElementById('news-external-source').value.trim());
            formData.append('image_id', document.getElementById('news-image-id').value); // Send the selected image ID
            formData.append('prize', prizeElement ? prizeElement.value || '0' : '0'); // Add prize field
            formData.append('prize_coin_type', prizeCoinTypeElement ? prizeCoinTypeElement.value || 'any' : 'any'); // Add coin type field

            try {
                let response;
                let data;
                
                if (isEditMode) {
                    // Edit mode: Use PUT method
                    const jsonData = {
                        title: document.getElementById('news-title').value.trim(),
                        content: addSimplemde.value().trim(),
                        tagar: document.getElementById('news-tagar').value.trim(),
                        date: document.getElementById('news-date').value,
                        category: document.getElementById('news-category').value,
                        age_rating: document.getElementById('news-age-rating').value,
                        is_news: isPremiumElement ? isPremiumElement.checked : false,
                        is_main_news: false, // Fixed: news-main element doesn't exist, default to false
                        is_premium: isPremiumElement ? isPremiumElement.checked : false,
                        writer: document.getElementById('news-writer').value.trim(),
                        external_source: document.getElementById('news-external-source').value.trim(),
                        image_id: document.getElementById('news-image-id').value,
                        prize: prizeElement ? prizeElement.value || '0' : '0',
                        prize_coin_type: prizeCoinTypeElement ? prizeCoinTypeElement.value || 'any' : 'any'
                    };
                    // Set visibility based on which button was clicked
                    jsonData.is_visible = !!isPublishButton;
                    
                    response = await fetch(`/api/news/${newsId}`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(jsonData),
                    });
                } else {
                    // Create mode: Use POST method
                    // Add album_id to form data if in album context
                    if (albumId) {
                        formData.append('album_id', albumId);
                    }
                    response = await fetch((window.NEWS_CREATE_ENDPOINT || '/api/news'), {
                        method: 'POST',
                        body: formData,
                    });
                }

                data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || (isEditMode ? 'Gagal memperbarui artikel berita' : 'Gagal menambahkan artikel berita'));
                }

                if (typeof showToast === 'function') {
                    const action = isEditMode ? 'diperbarui' : (isPublishButton ? 'diterbitkan' : 'disimpan sebagai draf');
                    showToast('success', `Berita berhasil ${action}!`);
                }

                // Handle redirect based on context (prefer server-provided redirect for user flow)
                setTimeout(() => {
                    if (data && data.redirect_url) {
                        window.location.href = data.redirect_url;
                        return;
                    }
                    if (data && data.redirect_url) {
                        window.location.href = data.redirect_url;
                        return;
                    }
                    if (albumId) {
                        window.location.href = `/admin/albums/${albumId}/chapters`;
                    } else if (window.CURRENT_USERNAME) {
                        // Prefer user stories page for both create and edit flows when username is available
                        window.location.href = `/user/${window.CURRENT_USERNAME}/stories`;
                    } else if (isEditMode) {
                        // Admin fallback
                        window.location.href = '/settings/manage_news';
                    } else {
                        window.location.href = '/settings/manage_news';
                    }
                }, 800);

                // Only reset form if not in edit mode
                if (!isEditMode) {
                    addNewsForm.reset(); // Reset the form fields
                    addSimplemde.value(''); // Clear the editor
                    document.getElementById('featured-preview-create').classList.add('hidden'); // Hide preview
                    document.getElementById('news-image-id').value = ''; // Clear hidden image ID
                    addSimplemde.clearAutosavedValue(); // Clear autosave
                }
            } catch (error) {
                console.error('Error mengirim berita:', error);
                const action = isEditMode ? 'memperbarui' : (isPublishButton ? 'menerbitkan' : 'menyimpan draf');
                if (typeof showToast === 'function') showToast('error', `Gagal ${action} berita: ${error.message}`);
                isSubmitting = false; // allow retry after failure
            }
        }


// Clear Featured Image Button Logic
const clearBtn = document.getElementById('clear-featured-image-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            const imageIdInput = document.getElementById('news-image-id');
            const preview = document.getElementById('featured-preview-create');
            if (imageIdInput) imageIdInput.value = ''; // Clear the hidden input
            if (preview) {
                preview.src = ''; // Clear the preview source
                preview.classList.add('hidden'); // Hide the preview
            }
        });
    }

    // Attach listeners for closing content image modal
    const closeContentInsertBtn = document.getElementById('close-image-insert-create');
    if (closeContentInsertBtn) {
        closeContentInsertBtn.addEventListener('click', closeImageInsertModalCreate);
    }

    // Attach listener for inserting image from URL (content modal)
    const insertContentUrlBtn = document.getElementById('insert-image-btn-create');
    if (insertContentUrlBtn) {
        insertContentUrlBtn.addEventListener('click', () => {
            const source = document.querySelector('input[name="image-source-create"]:checked').value;
            const cm = addSimplemde.codemirror;
            if (source === 'url') {
                const urlInput = document.getElementById('image-url-input-create');
                const altInput = document.getElementById('image-alt-input-create');
                const url = urlInput.value.trim();
                const alt = altInput.value.trim();
                if (url) {
                    cm.replaceSelection(`![${alt||null}](${url})`); // Correct Markdown format
                    closeImageInsertModalCreate();
                } else {
                    if (typeof showToast === 'function') showToast('warning', 'Masukkan URL gambar.');
                    urlInput.focus();
                }
            }
            // Library selection is handled by renderImageLibraryCreate attaching listeners
        });
    }

    // Pengikatan event toolbar kustom
    document.querySelectorAll('#custom-toolbar button[data-cmd]').forEach(btn => {
        btn.addEventListener('click', () => {
            const cmd = btn.getAttribute('data-cmd');
            const cm = addSimplemde.codemirror;
            switch (cmd) {
                case 'bold': SimpleMDE.toggleBold(addSimplemde); break;
                case 'italic': SimpleMDE.toggleItalic(addSimplemde); break;
                case 'heading': SimpleMDE.toggleHeadingSmaller(addSimplemde); break;
                case 'quote': SimpleMDE.toggleBlockquote(addSimplemde); break;
                case 'unordered-list': SimpleMDE.toggleUnorderedList(addSimplemde); break;
                case 'ordered-list': SimpleMDE.toggleOrderedList(addSimplemde); break;
                case 'link': openLinkInsertModal(addSimplemde); break;
                case 'image': openImageInsertModalCreate(); break;
                case 'preview': SimpleMDE.togglePreview(addSimplemde); break;
                case 'guide': window.open('https://www.markdownguide.org/cheat-sheet/', '_blank'); break;
            }
        });
    });

}); // End DOMContentLoaded
