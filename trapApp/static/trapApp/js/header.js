/* ── Burger Menu (shared across all pages) ── */
document.addEventListener('DOMContentLoaded', function () {
    const menuBtn  = document.getElementById('mobile-menu-btn');
    const sideMenu = document.getElementById('side-menu');
    const overlay  = document.getElementById('side-menu-overlay');
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
        bar2.style.opacity  = '';
        bar3.style.transform = '';
        sideMenu.classList.add('-translate-x-full');
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        document.body.style.overflow = '';
    }

    if (menuBtn) menuBtn.addEventListener('click', () => isOpen ? closeMenu() : openMenu());
    if (overlay) overlay.addEventListener('click', closeMenu);
});
