/* ── Index page: Brand slider + Brand drawer + Add to cart ── */

/* ── Brand Slider ── */
(function () {
    const track   = document.getElementById('brands-track');
    const btnPrev = document.getElementById('brands-prev');
    const btnNext = document.getElementById('brands-next');
    const counter = document.getElementById('brands-counter');
    if (!track) return;

    const slides = track.querySelectorAll('.brand-slide');
    const total  = slides.length;
    let current  = 0;
    let perView  = getPerView();

    function getPerView() {
        if (window.innerWidth < 480) return 1;
        if (window.innerWidth < 768) return 2;
        return 3;
    }
    function maxIndex() { return Math.max(0, total - perView); }
    function updateSlider() {
        const slideWidth = slides[0]?.offsetWidth || 0;
        track.style.transform = `translateX(-${current * (slideWidth + 24)}px)`;
        btnPrev.disabled = current === 0;
        btnNext.disabled = current >= maxIndex();
        counter.textContent = total > 0
            ? `${current + 1} – ${Math.min(current + perView, total)} / ${total}` : '';
    }
    btnPrev.addEventListener('click', () => { if (current > 0) { current--; updateSlider(); } });
    btnNext.addEventListener('click', () => { if (current < maxIndex()) { current++; updateSlider(); } });
    window.addEventListener('resize', () => {
        perView = getPerView();
        current = Math.min(current, maxIndex());
        updateSlider();
    });
    updateSlider();
})();

/* ── Brand Drawer ── */
(function () {
    const trigger     = document.getElementById('drawer-trigger');
    const drawer      = document.getElementById('brand-drawer');
    const overlay     = document.getElementById('drawer-overlay');
    const closeBtn    = document.getElementById('drawer-close');
    const triggerName = document.getElementById('trigger-brand-name');
    const viewAllBtn  = document.getElementById('catalog-view-all');
    const countEl     = document.getElementById('catalog-item-count');
    const drawerItems = document.querySelectorAll('.drawer-brand-item');
    const panels      = document.querySelectorAll('.brand-panel');

    if (!trigger || !drawer) return;

    function openDrawer() {
        drawer.classList.add('open');
        overlay.classList.add('visible');
        trigger.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
    function closeDrawer() {
        drawer.classList.remove('open');
        overlay.classList.remove('visible');
        trigger.classList.remove('open');
        document.body.style.overflow = '';
    }

    trigger.addEventListener('click', () => {
        drawer.classList.contains('open') ? closeDrawer() : openDrawer();
    });
    overlay.addEventListener('click', closeDrawer);
    closeBtn.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

    function activate(slug) {
        drawerItems.forEach(item => item.classList.toggle('active', item.dataset.brand === slug));
        panels.forEach(panel => panel.classList.toggle('active', panel.id === `panel-${slug}`));
        const activeItem = document.querySelector(`.drawer-brand-item[data-brand="${slug}"]`);
        if (activeItem && triggerName) {
            triggerName.textContent = activeItem.querySelector('.drawer-brand-name').textContent;
        }
        if (viewAllBtn && window.BRAND_URLS && window.BRAND_URLS[slug]) viewAllBtn.href = window.BRAND_URLS[slug];
        if (countEl && window.BRAND_COUNTS && window.BRAND_COUNTS[slug] !== undefined) {
            countEl.textContent = `${window.BRAND_COUNTS[slug]} речей у каталозі`;
        }
        closeDrawer();
    }

    drawerItems.forEach(item => {
        item.addEventListener('click', () => activate(item.dataset.brand));
        item.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(item.dataset.brand); }
        });
    });

    if (drawerItems.length > 0) activate(drawerItems[0].dataset.brand);
})();


