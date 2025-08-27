// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    // const mobileMenuOverlay = document.getElementById('mobile-menu-overlay'); // Removed overlay reference
    const mobileMenuCloseButton = document.getElementById('mobile-menu-close-button'); // Added close button reference
    const body = document.body;

    // Function to open the mobile menu
    function openMobileMenu() {
        // if (!mobileMenu || !mobileMenuOverlay || !body) return; // Updated Guard clause
        if (!mobileMenu || !body) return;
        // mobileMenu.classList.remove('-translate-x-full'); // Removed transform classes
        // mobileMenu.classList.add('translate-x-0');
        mobileMenu.classList.remove('opacity-0', 'pointer-events-none', '-translate-y-4'); // Make menu visible, interactive, and slide down
        mobileMenu.classList.add('opacity-100', 'pointer-events-auto', 'translate-y-0');
        // mobileMenuOverlay.classList.remove('opacity-0', 'pointer-events-none'); // Removed overlay logic
        // mobileMenuOverlay.classList.add('opacity-50', 'pointer-events-auto');
        body.classList.add('no-scroll'); // Prevent body scrolling
    }

    // Function to close the mobile menu
    function closeMobileMenu() {
        // if (!mobileMenu || !mobileMenuOverlay || !body) return; // Updated Guard clause
        if (!mobileMenu || !body) return;
        // mobileMenu.classList.remove('translate-x-0'); // Removed transform classes
        // mobileMenu.classList.add('-translate-x-full');
        mobileMenu.classList.remove('opacity-100', 'pointer-events-auto', 'translate-y-0'); // Make menu invisible, non-interactive, and slide up
        mobileMenu.classList.add('opacity-0', 'pointer-events-none', '-translate-y-4');
        // mobileMenuOverlay.classList.remove('opacity-50', 'pointer-events-auto'); // Removed overlay logic
        // mobileMenuOverlay.classList.add('opacity-0', 'pointer-events-none');
        body.classList.remove('no-scroll'); // Allow body scrolling
    }

    // Toggle menu on button click
    // if (mobileMenuButton && mobileMenu && mobileMenuOverlay) { // Updated check
    if (mobileMenuButton && mobileMenu && mobileMenuCloseButton) {
        mobileMenuButton.addEventListener('click', (event) => {
            event.stopPropagation(); // Prevent click from bubbling up
            // Check if the menu is currently hidden (based on transform class)
            // const isHidden = mobileMenu.classList.contains('-translate-x-full'); // Check opacity instead
            const isHidden = mobileMenu.classList.contains('opacity-0');
            if (isHidden) openMobileMenu();
            // No need for else, close is handled by close button/escape/overlay click
        });

        // Close menu when clicking the internal close button
        mobileMenuCloseButton.addEventListener('click', closeMobileMenu);

        // Close menu on escape key press
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && mobileMenu.classList.contains('translate-x-0')) {
                closeMobileMenu();
            }
        });
    } else {
        console.error("Mobile menu elements (button, menu, or close button) not found!");
    }
});