let currentTab = 'login';

function showTab(tab) {
    currentTab = tab;
    document.getElementById('loginForm').classList.toggle('hidden', tab !== 'login');
    document.getElementById('registerForm').classList.toggle('hidden', tab !== 'register');

    // Update tab styles
    document.getElementById('loginTab').classList.toggle('text-blue-500', tab === 'login');
    document.getElementById('loginTab').classList.toggle('border-blue-500', tab === 'login');
    document.getElementById('registerTab').classList.toggle('text-yellow-400', tab === 'register');
    document.getElementById('registerTab').classList.toggle('border-yellow-400', tab === 'register');
}

function showInlineToast(type, message) {
    if (typeof showToast === 'function') {
        showToast(type, message);
        return;
    }
    // Minimal fallback if global showToast not available
    const containerId = 'toast-container';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.className = 'fixed top-5 right-5 space-y-2 z-50';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `${type === 'error' ? 'bg-red-600' : type === 'success' ? 'bg-green-600' : 'bg-blue-600'} text-white px-4 py-2 rounded-lg shadow`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function validateLoginForm() {
    const password = document.getElementById('loginPassword').value;
    if (password.length < 6) {
    showInlineToast('error', 'Password must be at least 6 characters long');
    return false;
    }
    return true;
}

function validateRegisterForm() {
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const username = document.getElementById('registerUsername').value;

    if (username.length < 3) {
    showInlineToast('error', 'Username must be at least 3 characters long');
    return false;
    }

    if (password.length < 6) {
    showInlineToast('error', 'Password must be at least 6 characters long');
    return false;
    }

    if (password !== confirmPassword) {
    showInlineToast('error', 'Passwords do not match');
    return false;
    }

    return true;
}

function showPolicyModal(type) {
    document.getElementById('policyModal').classList.remove('hidden');
    document.getElementById('policyTitle').textContent = type === 'privacy' ? 'Kebijakan Privasi' : 'Pedoman Media Siber';

    // Show loading state
    document.getElementById('policyContent').innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';

    fetch(type === 'privacy' ? '/api/privacy-policy' : '/api/media-guidelines')
    .then(res => res.json())
    .then(data => {
        document.getElementById('policyContent').innerHTML = data.map(section => `
        <div>
            <h3 class="text-yellow-400 text-lg font-semibold">${section.title}</h3>
            <p class="text-gray-300">${section.content.replace(/\n/g, '<br>')}</p>
        </div>
        `).join('');
    })
    .catch(error => {
        document.getElementById('policyContent').innerHTML = '<div class="text-red-500">Failed to load content. Please try again later.</div>';
    });
}

function closePolicyModal() {
    document.getElementById('policyModal').classList.add('hidden');
}

// Close modal when clicking outside
document.getElementById('policyModal').addEventListener('click', function(e) {
    if (e.target === this) {
    closePolicyModal();
    }
});

// Handle error message fade-out
const errorMessage = document.querySelector('.animate-fade-in');
if (errorMessage) {
    setTimeout(() => {
    errorMessage.style.opacity = '0';
    errorMessage.style.transition = 'opacity 0.5s ease-out';
    }, 5000);
}