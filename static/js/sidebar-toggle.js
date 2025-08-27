(() => {
    
    const sidebarToggleButton = document.getElementById('sidebar-toggle-button');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');


    if (sidebarToggleButton && sidebar && sidebarOverlay) {
        // Function to toggle the sidebar
        const toggleSidebar = () => {
    
            sidebar.classList.toggle('-translate-x-full');
            sidebarOverlay.classList.toggle('hidden');
        };

        // Toggle sidebar when the button is clicked
        sidebarToggleButton.addEventListener('click', (e) => {
    
            toggleSidebar();
        });

        // Toggle sidebar when hero section is clicked
        const heroToggle = document.getElementById('hero-toggle');
        if (heroToggle) heroToggle.addEventListener('click', (e) => {
    
            toggleSidebar();
        });

        // Hide sidebar when the overlay is clicked
        sidebarOverlay.addEventListener('click', toggleSidebar);

        // Hide sidebar when clicking outside of it on mobile
        document.addEventListener('click', (event) => {
            const isClickInsideSidebar = sidebar.contains(event.target);
            const isClickOnToggleButton = sidebarToggleButton.contains(event.target);
            const isClickOnHero = heroToggle && heroToggle.contains(event.target);
    

            if (!isClickInsideSidebar && !isClickOnToggleButton && !isClickOnHero) {
                sidebar.classList.add('-translate-x-full');
                sidebarOverlay.classList.add('hidden');
            }
        });
    }
})();