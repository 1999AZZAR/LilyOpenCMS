// Index page functionality
export function initializeIndex() {
    // Initialize Featured News Swiper
    const swiperContainer = document.querySelector('.featured-swiper');
    if (swiperContainer && swiperContainer.querySelector('.swiper-slide')) {
        try {
            const swiper = new Swiper('.featured-swiper', {
                loop: swiperContainer.querySelectorAll('.swiper-slide').length > 1,
                effect: 'fade',
                fadeEffect: { crossFade: true },
                autoplay: {
                    delay: 5000,
                    disableOnInteraction: false,
                    pauseOnMouseEnter: true
                },
                pagination: {
                    el: '.swiper-pagination',
                    clickable: true
                },
                navigation: {
                    nextEl: '.swiper-button-next',
                    prevEl: '.swiper-button-prev'
                },
                keyboard: { enabled: true },
                a11y: {
                    prevSlideMessage: 'Slide sebelumnya',
                    nextSlideMessage: 'Slide berikutnya',
                    paginationBulletMessage: 'Ke slide {{index}}',
                },
            });
        } catch(e) {
            console.error("Featured Swiper initialization failed:", e);
        }
    } else if (swiperContainer) {
        const controls = ['.swiper-button-next', '.swiper-button-prev', '.swiper-pagination'];
        controls.forEach(sel => {
            const el = swiperContainer.querySelector(sel);
            if (el) el.style.display = 'none';
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeIndex();
});