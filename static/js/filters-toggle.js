document.addEventListener('DOMContentLoaded', function () {
  function initFiltersToggle(button) {
    if (!button) return;

    const targetSelector = button.getAttribute('data-filters-toggle');
    if (!targetSelector) return;
    const container = document.querySelector(targetSelector);
    if (!container) return;

    const storageKey = button.getAttribute('data-storage-key') || `filters_open_${targetSelector}`;
    const chevron = button.querySelector('[data-chevron]');

    function setExpanded(expanded) {
      button.setAttribute('aria-expanded', String(expanded));
      if (expanded) {
        container.classList.remove('hidden');
        if (chevron) chevron.style.transform = 'rotate(180deg)';
      } else {
        container.classList.add('hidden');
        if (chevron) chevron.style.transform = '';
      }
      try { localStorage.setItem(storageKey, expanded ? '1' : '0'); } catch (_) {}
    }

    // Initialize from storage (default collapsed)
    let initial = '0';
    try { initial = localStorage.getItem(storageKey) || '0'; } catch (_) {}
    setExpanded(initial === '1');

    button.addEventListener('click', function () {
      const isExpanded = button.getAttribute('aria-expanded') === 'true';
      setExpanded(!isExpanded);
    });
  }

  // Initialize all filter toggle buttons on the page
  const toggleButtons = document.querySelectorAll('[data-filters-toggle]');
  toggleButtons.forEach(initFiltersToggle);
});


