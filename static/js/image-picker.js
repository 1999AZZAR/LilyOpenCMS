/*
 Reusable Image Picker Module
 - Expects the modal markup with ids:
   - image-header-modal-create
   - header-image-library-create
   - header-image-pagination-controls-create
   - header-upload-name-create, header-upload-file-create, header-upload-url-create, header-upload-btn-create
   - header-image-close-create
   - image-search (shared search input inside modal)
 - Provides: ImagePicker.open({ onSelect(image), perPage })
*/
(function (global) {
  'use strict';

  const state = {
    page: 1,
    totalPages: 1,
    perPage: 12,
    onSelect: null,
  };

  function $(id) { return document.getElementById(id); }

  function showModal() {
    const modal = $('image-header-modal-create');
    if (modal) modal.classList.remove('hidden');
  }

  function hideModal() {
    const modal = $('image-header-modal-create');
    if (modal) modal.classList.add('hidden');
  }

  async function fetchImages(page, query) {
    let url = `/api/images?page=${page}&per_page=${state.perPage}`;
    if (query) url += `&description=${encodeURIComponent(query)}`;
    const res = await fetchWithCSRF(url);
    if (!res.ok) throw new Error(`Failed to load images (${res.status})`);
    return res.json();
  }

  function computeLandscapeThumb(image) {
    const placeholderImg = '/static/pic/placeholder.png';
    if (!image) return placeholderImg;
    const fullImageUrl = image.file_url || image.url || placeholderImg;
    if (!image.filepath) return fullImageUrl;
    try {
      const pathWithoutStatic = image.filepath.replace('static/', '', 1);
      const lastDotIndex = pathWithoutStatic.lastIndexOf('.');
      if (lastDotIndex === -1) return fullImageUrl;
      const basePath = pathWithoutStatic.substring(0, lastDotIndex);
      const extension = pathWithoutStatic.substring(lastDotIndex);
      return `/static/${basePath}_thumb_landscape${extension}`;
    } catch (_) {
      return fullImageUrl;
    }
  }

  function renderImages(items) {
    const grid = $('header-image-library-create');
    if (!grid) return;
    grid.innerHTML = '';
    if (!items || items.length === 0) {
      grid.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Tidak ada gambar yang ditemukan.</p>';
      return;
    }
    const placeholderImg = '/static/pic/placeholder.png';
    items.forEach((image) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'p-2 group cursor-pointer border border-transparent hover:border-blue-400 rounded-lg transition duration-150';
      const landscapeThumbUrl = computeLandscapeThumb(image);
      wrapper.innerHTML = `
        <img src="${landscapeThumbUrl}" onerror="this.onerror=null;this.src='${placeholderImg}'" alt="${image.filename || 'Image'}" class="w-full aspect-square object-cover rounded-lg mb-2 shadow-sm group-hover:shadow-md" loading="lazy">
        <button class="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white py-1 rounded-lg font-semibold transition-colors">Pilih</button>
      `;
      wrapper.querySelector('button').addEventListener('click', (e) => {
        e.stopPropagation();
        if (typeof state.onSelect === 'function') state.onSelect(image, landscapeThumbUrl);
        hideModal();
      });
      grid.appendChild(wrapper);
    });
  }

  function renderPagination(page, totalPages) {
    const container = $('header-image-pagination-controls-create');
    if (!container) return;
    if (totalPages <= 1) { container.innerHTML = ''; return; }
    let html = '<div class="flex items-center space-x-2">';
    if (page > 1) {
      html += `<button class=\"px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50\" data-page=\"${page - 1}\">Previous</button>`;
    }
    for (let i = 1; i <= totalPages; i++) {
      if (i === page) {
        html += `<span class=\"px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-300 rounded-lg\">${i}</span>`;
      } else {
        html += `<button class=\"px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50\" data-page=\"${i}\">${i}</button>`;
      }
    }
    if (page < totalPages) {
      html += `<button class=\"px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-lg hover:bg-gray-50\" data-page=\"${page + 1}\">Next</button>`;
    }
    html += '</div>';
    container.innerHTML = html;
    container.querySelectorAll('button[data-page]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const p = parseInt(e.currentTarget.getAttribute('data-page'), 10) || 1;
        load(p);
      });
    });
  }

  async function load(page = 1) {
    state.page = page;
    const grid = $('header-image-library-create');
    if (grid) grid.innerHTML = '<p class="col-span-full text-center text-gray-500 py-4">Memuat gambar...</p>';
    const query = ($('image-search') && $('image-search').value) || '';
    try {
      const data = await fetchImages(page, query);
      renderImages(data.items || data.images || []);
      renderPagination(data.page || page, data.total_pages || 1);
    } catch (e) {
      console.error('ImagePicker load error:', e);
      if (grid) grid.innerHTML = '<p class="col-span-full text-center text-red-500 py-4">Error loading images.</p>';
    }
  }

  async function upload() {
    const nameInput = $('header-upload-name-create');
    const fileInput = $('header-upload-file-create');
    const urlInput = $('header-upload-url-create');
    const name = nameInput ? nameInput.value.trim() : '';
    const file = fileInput && fileInput.files ? fileInput.files[0] : null;
    const url = urlInput ? urlInput.value.trim() : '';
    if (!file && !url) { alert('Please select a file or enter a URL'); return; }
    const fd = new FormData();
    if (file) fd.append('file', file);
    if (url) fd.append('url', url);
    if (name) fd.append('name', name);
    fd.append('is_visible', 'false');
    try {
      const res = await fetchWithCSRF('/api/images', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Upload failed');
      if (nameInput) nameInput.value = '';
      if (fileInput) fileInput.value = '';
      if (urlInput) urlInput.value = '';
      await load(state.page);
      alert('Image uploaded successfully!');
    } catch (e) {
      console.error('ImagePicker upload error:', e);
      alert('Error uploading image: ' + (e.message || 'Unknown error'));
    }
  }

  function bindStaticHandlers() {
    const closeBtn = $('header-image-close-create');
    if (closeBtn && !closeBtn._ipBound) {
      closeBtn.addEventListener('click', hideModal);
      closeBtn._ipBound = true;
    }
    const uploadBtn = $('header-upload-btn-create');
    if (uploadBtn && !uploadBtn._ipBound) {
      uploadBtn.addEventListener('click', upload);
      uploadBtn._ipBound = true;
    }
    const searchInput = $('image-search');
    if (searchInput && !searchInput._ipBound) {
      let t;
      searchInput.addEventListener('input', function () {
        clearTimeout(t);
        t = setTimeout(() => load(1), 300);
      });
      searchInput._ipBound = true;
    }
  }

  function open(options) {
    state.onSelect = (options && options.onSelect) || null;
    if (options && options.perPage) state.perPage = options.perPage;
    bindStaticHandlers();
    showModal();
    load(1);
  }

  global.ImagePicker = { open };
})(window);


