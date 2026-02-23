// Tailwind config
tailwind.config = {
    theme: {
        extend: {
            colors: {
                'charcoal-900': '#121212',
                'charcoal-800': '#1E1E1E',
                'charcoal-700': '#2A2A2A',
                'off-white': '#F5F5F0',
                'grunge-gray': '#A0A0A0',
                'accent-red': '#8B0000',
            },
            fontFamily: {
                'gothic': ['"UnifrakturMaguntia"', 'cursive'],
                'bebas': ['"Bebas Neue"', 'cursive'],
                'sans': ['"Helvetica Neue"', 'Arial', 'sans-serif'],
                'mono': ['"Courier New"', 'monospace'],
            },
            spacing: { '128': '32rem' }
        }
    }
};

// ─── Mobile Menu ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {

    const menuBtn     = document.getElementById('mobile-menu-btn');
    const sideMenu    = document.getElementById('side-menu');
    const overlay     = document.getElementById('side-menu-overlay');
    const bar1        = document.getElementById('bar1');
    const bar2        = document.getElementById('bar2');
    const bar3        = document.getElementById('bar3');

    if (!menuBtn || !sideMenu || !overlay) return;

    let isOpen = false;

    function openMenu() {
        isOpen = true;
        // animate bars → X
        bar1.style.transform = 'translateY(8px) rotate(45deg)';
        bar2.style.opacity = '0';
        bar3.style.transform = 'translateY(-8px) rotate(-45deg)';
        // show drawer
        sideMenu.classList.remove('-translate-x-full');
        // show overlay
        overlay.classList.remove('hidden');
        requestAnimationFrame(() => overlay.classList.remove('opacity-0'));
        document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
        isOpen = false;
        // revert bars
        bar1.style.transform = '';
        bar2.style.opacity = '';
        bar3.style.transform = '';
        // hide drawer
        sideMenu.classList.add('-translate-x-full');
        // hide overlay
        overlay.classList.add('opacity-0');
        setTimeout(() => overlay.classList.add('hidden'), 300);
        document.body.style.overflow = '';
    }

    menuBtn.addEventListener('click', () => isOpen ? closeMenu() : openMenu());
    overlay.addEventListener('click', closeMenu);

});
