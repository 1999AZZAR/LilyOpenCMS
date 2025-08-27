// About page functionality
export function initializeAbout() {
    // Load vision/mission content when page loads
    loadVisiMisiContent();
    
    // Modal toggling
    function toggleModal(type) {
        const modal = document.getElementById(type + 'Modal');
        if (!modal) {
            console.error(`Modal with type "${type}" not found.`);
            return;
        }
        const modalPanel = modal.querySelector('[data-state]');

        if (modal.classList.contains('hidden')) {
            modal.classList.remove('hidden');
            void modal.offsetWidth; // Trigger reflow
            modal.classList.add('opacity-100');
            modalPanel.dataset.state = 'open';
            modalPanel.classList.remove('scale-95', 'opacity-0');
            modalPanel.classList.add('scale-100', 'opacity-100');
            loadContent(type); // Load content when opening
            document.body.style.overflow = 'hidden';
        } else {
            modal.classList.remove('opacity-100');
            modalPanel.dataset.state = 'closed';
            modalPanel.classList.remove('scale-100', 'opacity-100');
            modalPanel.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                modal.classList.add('hidden');
                document.body.style.overflow = '';
            }, 300); // Match transition duration
        }
    }

    // Close modal logic
    document.querySelectorAll('[role="dialog"]').forEach(modal => {
        // Close on backdrop click
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                const type = modal.id.replace('Modal', '');
                toggleModal(type);
            }
        });
    });
    
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const openModal = document.querySelector('[role="dialog"]:not(.hidden)');
            if (openModal) {
                const type = openModal.id.replace('Modal', '');
                toggleModal(type);
            }
        }
    });

    // Load vision/mission content
    async function loadVisiMisiContent() {
        try {
            const response = await fetch('/api/visi-misi');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            if (!data || data.length === 0) {
                // Show default content if no data
                document.getElementById('visi-content').innerHTML = '<p class="text-muted-foreground">Visi belum tersedia.</p>';
                document.getElementById('misi-content').innerHTML = '<p class="text-muted-foreground">Misi belum tersedia.</p>';
                return;
            }

            // Separate visi and misi content
            const visiData = data.find(item => item.title.toLowerCase() === 'visi');
            const misiData = data.find(item => item.title.toLowerCase() === 'misi');

            // Update visi content
            const visiContainer = document.getElementById('visi-content');
            if (visiContainer) {
                if (visiData) {
                    visiContainer.innerHTML = `<div class="prose prose-sm max-w-none">${visiData.content}</div>`;
                } else {
                    visiContainer.innerHTML = '<p class="text-muted-foreground">Visi belum tersedia.</p>';
                }
            }

            // Update misi content
            const misiContainer = document.getElementById('misi-content');
            if (misiContainer) {
                if (misiData) {
                    // Format misi content as a list if it contains numbered items
                    let misiContent = misiData.content;
                    if (misiContent.includes('1.') || misiContent.includes('2.') || misiContent.includes('3.')) {
                        // Convert numbered text to HTML list
                        const lines = misiContent.split('\n').filter(line => line.trim());
                        const listItems = lines.map(line => {
                            const trimmed = line.trim();
                            if (trimmed.match(/^\d+\./)) {
                                return `<li>${trimmed.replace(/^\d+\.\s*/, '')}</li>`;
                            }
                            return `<li>${trimmed}</li>`;
                        });
                        misiContent = `<ol class="list-decimal list-inside space-y-2">${listItems.join('')}</ol>`;
                    } else {
                        misiContent = `<div class="prose prose-sm max-w-none">${misiContent}</div>`;
                    }
                    misiContainer.innerHTML = misiContent;
                } else {
                    misiContainer.innerHTML = '<p class="text-muted-foreground">Misi belum tersedia.</p>';
                }
            }

        } catch (error) {
            console.error('Error loading visi/misi content:', error);
            document.getElementById('visi-content').innerHTML = '<p class="text-destructive">Gagal memuat visi.</p>';
            document.getElementById('misi-content').innerHTML = '<p class="text-destructive">Gagal memuat misi.</p>';
        }
    }

    // Content loading for policies
    async function loadContent(type) {
        const contentDiv = document.getElementById(type + 'Content');
        if (!contentDiv) {
            console.error(`Content container for type "${type}" not found.`);
            return;
        }

        let endpoint = '';
        // Map type to the correct Flask endpoint
        switch(type) {
            case 'privacy':
                endpoint = '/api/privacy-policy';
                break;
            case 'media':
                endpoint = '/api/media-guidelines';
                break;
            case 'disclaimer':
                endpoint = '/api/penyangkalan';
                break;
            case 'rights':
                endpoint = '/api/pedomanhak';
                break;
            default:
                console.error(`Unknown content type: ${type}`);
                contentDiv.innerHTML = '<p class="text-center text-destructive">Tipe konten tidak dikenal.</p>';
                return;
        }

        // Show loading state immediately
        contentDiv.innerHTML = `
            <div class="text-center py-10">
                <div class="spinner mx-auto"></div>
                <p class="mt-4 text-muted-foreground">Memuat konten...</p>
            </div>`;

        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} for ${endpoint}`);
            }
            const data = await response.json();

            if (!data || data.length === 0) {
                contentDiv.innerHTML = '<p class="text-center text-muted-foreground">Tidak ada konten tersedia saat ini.</p>';
                return;
            }

            // Helper to normalize plain-text bullets/numbers into HTML lists (supports simple nesting by indentation)
            function normalizePolicyContent(rawText) {
                if (!rawText || /<\s*(ul|ol|li|p|div)[^>]*>/i.test(rawText)) {
                    // Already HTML-ish; return as-is
                    return rawText || '';
                }

                const lines = rawText
                    .split(/\r?\n/)
                    .map(l => l.replace(/\s+$/,'')).filter(l => l.trim().length > 0);

                if (lines.length === 0) return '';

                const bulletRe = /^\s*(?:[•\-*\u2022])\s+/; // bullets like • - *
                const numberRe = /^\s*\d+[\.)]\s+/;        // 1. or 1)

                const isMostlyList = lines.filter(l => bulletRe.test(l) || numberRe.test(l)).length >= Math.max(2, Math.floor(lines.length * 0.5));
                if (!isMostlyList) {
                    // Fallback: join as paragraphs
                    return lines.map(l => `<p>${l}</p>`).join('');
                }

                // Convert to nested lists by indentation depth (2 spaces = one level)
                const stack = [];
                let html = '';

                function openList(ordered) {
                    stack.push(ordered ? 'ol' : 'ul');
                    html += ordered ? '<ol>' : '<ul>';
                }
                function closeList() {
                    const tag = stack.pop();
                    html += tag === 'ol' ? '</ol>' : '</ul>';
                }

                lines.forEach(line => {
                    const indentMatch = line.match(/^\s*/)[0] || '';
                    const level = Math.min(5, Math.floor(indentMatch.replace(/\t/g,'  ').length / 2));
                    const isNumber = numberRe.test(line);
                    const isBullet = bulletRe.test(line);
                    let text = line
                        .replace(numberRe, '')
                        .replace(bulletRe, '')
                        .trim();

                    // Adjust current nesting depth
                    while (stack.length > level) closeList();
                    while (stack.length < level) openList(false); // open UL for deeper indents by default

                    // Ensure a list exists at this level with correct type
                    const desired = isNumber ? 'ol' : 'ul';
                    if (stack.length === 0 || stack[stack.length - 1] !== desired) {
                        // Close current and open desired list if type differs
                        if (stack.length > 0) closeList();
                        openList(isNumber);
                    }

                    html += `<li>${text}</li>`;
                });

                while (stack.length) closeList();
                return html;
            }

            // Display the content with consistent list styling
            const sectionsHTML = data.map(item => {
                const normalized = normalizePolicyContent(item.content);
                return `
                <section class="policy-section">
                    <h3 class="policy-title">${item.title}</h3>
                    <div class="policy-content prose prose-sm max-w-none">${normalized}</div>
                </section>`;
            }).join('');

            contentDiv.innerHTML = `<div class="policy-list">${sectionsHTML}</div>`;

        } catch (error) {
            console.error('Error loading content:', error);
            contentDiv.innerHTML = '<p class="text-center text-destructive">Gagal memuat konten.</p>';
        }
    }

    // Make toggleModal globally available
    window.toggleModal = toggleModal;
}

document.addEventListener('DOMContentLoaded', initializeAbout);