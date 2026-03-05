document.addEventListener('DOMContentLoaded', function () {
    // ── Burger ───────────────────────────────────────────────
    const menuBtn = document.getElementById('mobile-menu-btn');
    const sideMenu = document.getElementById('side-menu');
    const overlay = document.getElementById('side-menu-overlay');
    const bar1 = document.getElementById('bar1');
    const bar2 = document.getElementById('bar2');
    const bar3 = document.getElementById('bar3');
    let isOpen = false;

    function openMenu() {
        isOpen = true;
        bar1.style.transform = 'translateY(8px) rotate(45deg)';
        bar2.style.opacity = '0';
        bar3.style.transform = 'translateY(-8px) rotate(-45deg)';
        sideMenu.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
        requestAnimationFrame(() => overlay.classList.remove('opacity-0'));
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        isOpen = false;
        bar1.style.transform = '';
        bar2.style.opacity = '';
        bar3.style.transform = '';
        sideMenu.classList.add('-translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        document.body.style.overflow = '';
    }

    if (menuBtn) menuBtn.addEventListener('click', () => isOpen ? closeMenu() : openMenu());
    if (overlay) overlay.addEventListener('click', closeMenu);

    // ── Фільтри категорій ─────────────────────────────────────
    // Зчитуємо поточні params з URL
    const urlParams = new URLSearchParams(window.location.search);
    const ids = urlParams.getAll('ids');
    const eventName = urlParams.get('event') || '';
    const gender = urlParams.get('gender') || '';
    const season = urlParams.get('season') || '';
    const style = urlParams.get('style') || '';

    // Оновлюємо href усіх filter-btn щоб вони передавали ids
    document.querySelectorAll('.filter-btn').forEach(btn => {
        const catKey = btn.dataset.cat;
        if (!catKey) return;
        const params = new URLSearchParams();
        ids.forEach(id => params.append('ids', id));
        params.set('cat', catKey);
        if (eventName) params.set('event', eventName);
        if (gender) params.set('gender', gender);
        if (season) params.set('season', season);
        if (style) params.set('style', style);
        btn.href = '?' + params.toString();
    });
});