// Login page functionality
export function initializeLogin() {
    const loginTabButton = document.getElementById('loginTabButton');
    const registerTabButton = document.getElementById('registerTabButton');
    const loginFormContainer = document.getElementById('loginFormContainer');
    const registerFormContainer = document.getElementById('registerFormContainer');
    
    // Determine initial tab based on URL hash or default to login
    const initialTab = window.location.hash === '#register' ? 'register' : 'login';

    function showTab(tabName) {
        if (tabName === 'login') {
            // Show login form and hide register form
            loginFormContainer.classList.remove('hidden');
            loginFormContainer.removeAttribute('hidden');
            registerFormContainer.classList.add('hidden');
            registerFormContainer.setAttribute('hidden', 'true');
            
            // Update tab states
            loginTabButton.classList.add('text-primary', 'border-primary');
            loginTabButton.classList.remove('text-muted-foreground', 'border-transparent');
            loginTabButton.setAttribute('aria-selected', 'true');
            loginTabButton.setAttribute('tabindex', '0');
            
            registerTabButton.classList.add('text-muted-foreground', 'border-transparent');
            registerTabButton.classList.remove('text-primary', 'border-primary');
            registerTabButton.setAttribute('aria-selected', 'false');
            registerTabButton.setAttribute('tabindex', '-1');
            
        } else if (tabName === 'register') {
            // Show register form and hide login form
            registerFormContainer.classList.remove('hidden');
            registerFormContainer.removeAttribute('hidden');
            loginFormContainer.classList.add('hidden');
            loginFormContainer.setAttribute('hidden', 'true');
            
            // Update tab states
            registerTabButton.classList.add('text-primary', 'border-primary');
            registerTabButton.classList.remove('text-muted-foreground', 'border-transparent');
            registerTabButton.setAttribute('aria-selected', 'true');
            registerTabButton.setAttribute('tabindex', '0');
            
            loginTabButton.classList.add('text-muted-foreground', 'border-transparent');
            loginTabButton.classList.remove('text-primary', 'border-primary');
            loginTabButton.setAttribute('aria-selected', 'false');
            loginTabButton.setAttribute('tabindex', '-1');
        }
    }

    // Modal toggling
    function toggleModal(type) {
        const modal = document.getElementById(type + 'Modal');
        if (!modal) { 
            console.error(`Modal "${type}" not found.`); 
            return; 
        }
        const modalPanel = modal.querySelector('[data-state]');
        if (modal.classList.contains('hidden')) {
            modal.classList.remove('hidden');
            void modal.offsetWidth;
            modal.classList.add('opacity-100');
            modalPanel.dataset.state = 'open';
            modalPanel.classList.remove('scale-95', 'opacity-0');
            modalPanel.classList.add('scale-100', 'opacity-100');
            loadContent(type);
            document.body.style.overflow = 'hidden';
        } else {
            modal.classList.remove('opacity-100');
            modalPanel.dataset.state = 'closed';
            modalPanel.classList.remove('scale-100', 'opacity-100');
            modalPanel.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                modal.classList.add('hidden');
                document.body.style.overflow = '';
            }, 300);
        }
    }

    // Close modal logic
    document.querySelectorAll('[role="dialog"]').forEach(modal => {
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

    // Content loading for policies
    async function loadContent(type) {
        const contentDiv = document.getElementById(type + 'Content');
        if (!contentDiv) { 
            console.error(`Content container "${type}" not found.`); 
            return; 
        }
        
        let endpoint = '';
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
                return;
        }

        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (!data || data.length === 0) {
                contentDiv.innerHTML = '<p class="text-center text-muted-foreground">Tidak ada konten tersedia saat ini.</p>';
                return;
            }

            // Display the content
            contentDiv.innerHTML = data.map(item => `
                <div class="mb-6">
                    <h3 class="text-lg font-semibold mb-2">${item.title}</h3>
                    <div class="prose prose-sm max-w-none">${item.content}</div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Error loading content:', error);
            contentDiv.innerHTML = '<p class="text-center text-destructive">Gagal memuat konten.</p>';
        }
    }

    // Initialize tabs
    showTab(initialTab);
    
    // Add event listeners for tab buttons
    if (loginTabButton) {
        loginTabButton.addEventListener('click', () => showTab('login'));
    }
    if (registerTabButton) {
        registerTabButton.addEventListener('click', () => showTab('register'));
    }

    // Make toggleModal globally available
    window.toggleModal = toggleModal;
}

document.addEventListener('DOMContentLoaded', initializeLogin);