// Content Edit Requests Manager (Admin)
(function() {
  const el = (id) => document.getElementById(id);

  function safeToast(type, message) {
    try { if (typeof showToast === 'function') { showToast(type, message); return; } } catch (_) {}
    try { console[type === 'error' ? 'error' : 'log']('[Toast]', type, message); } catch(_) {}
  }

  function fmtDate(iso) {
    if (!iso) return '-';
    try { const d = new Date(iso); return d.toLocaleString(); } catch(_) { return iso; }
  }

  function renderNewsRequests(list) {
    const container = el('news-requests-list');
    const empty = el('news-no-requests');
    if (!container) return;
    container.innerHTML = '';
    if (!Array.isArray(list) || list.length === 0) {
      if (empty) empty.classList.remove('hidden');
      return;
    }
    if (empty) empty.classList.add('hidden');

    list.forEach((req) => {
      const card = document.createElement('div');
      card.className = 'border border-gray-200 rounded-lg p-4 bg-white shadow-sm';
      card.innerHTML = `
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-base font-semibold text-gray-800">${req.title || 'Tanpa Judul'}</h3>
            <p class="text-sm text-gray-600 mt-1">Diminta oleh <span class="font-medium">${req.requester_username || 'unknown'}</span> • ${fmtDate(req.created_at)}</p>
            <p class="text-sm text-gray-700 mt-3"><span class="font-medium">Alasan:</span> ${req.reason ? req.reason : '-'}</p>
            <p class="text-xs mt-2"><span class="inline-block px-2 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700">${(req.status || 'pending').toUpperCase()}</span></p>
          </div>
          <div class="flex gap-2 ml-4">
            <button data-action="approve" data-id="${req.news_id}" class="px-3 py-2 rounded bg-green-600 hover:bg-green-700 text-white text-sm">Setujui</button>
            <button data-action="reject" data-id="${req.news_id}" class="px-3 py-2 rounded bg-red-600 hover:bg-red-700 text-white text-sm">Tolak</button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    container.addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-action]');
      if (!btn) return;
      const id = Number(btn.getAttribute('data-id'));
      const action = btn.getAttribute('data-action');
      if (!id || !action) return;
      try {
        const url = action === 'approve' ? `/api/news/${id}/approve-edit` : `/api/news/${id}/reject-edit`;
        const rsp = await fetchWithCSRF(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
        if (!rsp.ok) throw new Error(`HTTP ${rsp.status}`);
        safeToast('success', action === 'approve' ? 'Permintaan edit disetujui' : 'Permintaan edit ditolak');
        await loadNewsRequests();
      } catch (err) {
        safeToast('error', `Gagal memproses: ${err.message}`);
      }
    }, { once: true });
  }

  async function loadNewsRequests() {
    try {
      const rsp = await fetchWithCSRF('/api/news/edit-requests');
      if (!rsp.ok) throw new Error(`HTTP ${rsp.status}`);
      const data = await rsp.json();
      renderNewsRequests(data.requests || []);
    } catch (e) {
      safeToast('error', `Gagal memuat permintaan edit: ${e.message}`);
    }
  }

  function initTabs() {
    const buttons = document.querySelectorAll('.tab-button');
    const newsTab = el('news-requests-tab');
    const albumTab = el('album-requests-tab');
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        buttons.forEach(b => {
          b.classList.remove('bg-blue-500','text-white');
          b.classList.add('bg-gray-200','text-gray-700');
        });
        btn.classList.remove('bg-gray-200','text-gray-700');
        btn.classList.add('bg-blue-500','text-white');
        if (tab === 'news-requests') {
          if (newsTab) newsTab.classList.remove('hidden');
          if (albumTab) albumTab.classList.add('hidden');
        } else {
          if (albumTab) albumTab.classList.remove('hidden');
          if (newsTab) newsTab.classList.add('hidden');
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', async () => {
    initTabs();
    await loadNewsRequests();
  });
})();


