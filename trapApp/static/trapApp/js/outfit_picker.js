document.addEventListener('DOMContentLoaded', function () {

    // ── Burger ───────────────────────────────────────────────
    const menuBtn = document.getElementById('mobile-menu-btn');
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
    if (overlay)  overlay.addEventListener('click', closeMenu);


    // ── Events Wheel ─────────────────────────────────────────
    const EVENTS = [
        'День народження',
        'Ювілей',
        'Заручини',
        'Розпис',
        'Весільний банкет (гість)',
        'Коктейльна вечірка',
        'Формальний вечір',
        'Корпоратив',
        'Конференція',
        'Нетворкінг',
        'Презентація',
        'Публічний виступ',
        'Фотосесія',
        'Випуск з університету',
        'Театр',
        'Опера / філармонія',
        'Гала-вечір',
        'Благодійний бал',
        'Свято в родині',
        'Бранч / зустріч з друзями',
    ];

    const VISIBLE = 2;
    const TOTAL   = EVENTS.length;
    let offset    = 0;
    let activeIdx = -1;

    const viewport   = document.getElementById('wheel-viewport');
    const btnUp      = document.getElementById('wheel-up');
    const btnDown    = document.getElementById('wheel-down');
    const counter    = document.getElementById('wheel-counter');
    const eventInput = document.getElementById('event-input');

    function renderWheel() {
        viewport.innerHTML = '';
        for (let i = offset; i < offset + VISIBLE; i++) {
            const li = document.createElement('div');
            li.className = 'event-wheel-item px-5 py-3.5 text-sm font-mono text-grunge-gray border-b border-charcoal-700';
            li.textContent = EVENTS[i];
            if (i === activeIdx) li.classList.add('active');
            li.addEventListener('click', () => {
                activeIdx = i;
                eventInput.value = EVENTS[i];
                eventInput.dispatchEvent(new Event('input'));
                renderWheel();
            });
            viewport.appendChild(li);
        }
        btnUp.disabled   = offset === 0;
        btnDown.disabled = offset + VISIBLE >= TOTAL;
        counter.textContent = `${offset + 1} – ${Math.min(offset + VISIBLE, TOTAL)} / ${TOTAL}`;
    }

    btnUp.addEventListener('click',   () => { if (offset > 0)                    { offset--; renderWheel(); } });
    btnDown.addEventListener('click', () => { if (offset + VISIBLE < TOTAL)      { offset++; renderWheel(); } });

    viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (e.deltaY > 0 && offset + VISIBLE < TOTAL) { offset++; renderWheel(); }
        if (e.deltaY < 0 && offset > 0)               { offset--; renderWheel(); }
    }, { passive: false });

    document.getElementById('wheel-viewport').parentElement
        .addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.deltaY > 0 && offset + VISIBLE < TOTAL) { offset++; renderWheel(); }
            if (e.deltaY < 0 && offset > 0)               { offset--; renderWheel(); }
        }, { passive: false });

    renderWheel();


    // ── Форма ────────────────────────────────────────────────
    const form        = document.getElementById('outfit-form');
    const submitBtn   = document.getElementById('submit-btn');
    const btnText     = document.getElementById('btn-text');
    const progress    = document.getElementById('submit-progress');
    const resultArea  = document.getElementById('result-area');
    const resultText  = document.getElementById('result-text');
    const genderSelect = document.getElementById('gender-select');
    const seasonSelect = document.getElementById('season-select');

    function checkReady() {
        const hasEvent  = eventInput.value.trim().length > 0;
        const allSelect = genderSelect.value && seasonSelect.value;
        const ready     = hasEvent || allSelect;

        if (ready) {
            submitBtn.disabled = false;
            submitBtn.className = `w-full relative overflow-hidden bg-off-white text-charcoal-900
                border border-off-white px-6 py-5 font-bold tracking-widest uppercase text-sm
                cursor-pointer transition-all duration-300 hover:bg-grunge-gray hover:text-white`;
        } else {
            submitBtn.disabled = true;
            submitBtn.className = `w-full relative overflow-hidden bg-charcoal-700 text-grunge-gray
                border border-charcoal-700 px-6 py-5 font-bold tracking-widest uppercase text-sm
                cursor-not-allowed transition-all duration-300`;
        }
    }

    eventInput.addEventListener('input',    checkReady);
    genderSelect.addEventListener('change', checkReady);
    seasonSelect.addEventListener('change', checkReady);


    // ── Сабміт ───────────────────────────────────────────────
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        submitBtn.disabled = true;
        btnText.textContent = 'Підбираємо...';
        resultArea.classList.add('hidden');
        progress.style.width = '0%';

        let pct = 0;
        const tick = setInterval(() => {
            pct += Math.random() * 12;
            if (pct >= 88) { pct = 88; clearInterval(tick); }
            progress.style.width = pct + '%';
        }, 180);

        const payload = {
            event:  eventInput.value.trim(),
            gender: genderSelect.value,
            season: seasonSelect.value,
        };

        try {
            const res  = await fetch('/generate-outfit/', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(payload),
            });
            const data = await res.json();

            clearInterval(tick);
            progress.style.width = '100%';

            setTimeout(() => {
                progress.style.width = '0%';
                btnText.textContent  = 'Підібрати образ';
                submitBtn.disabled   = false;
                checkReady();

                if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    btnText.textContent  = 'Помилка';
                    submitBtn.disabled   = false;
                    checkReady();
                }
            }, 400);

        } catch (err) {
            clearInterval(tick);
            progress.style.width = '0%';
            btnText.textContent  = 'Помилка. Спробуй знову';
            submitBtn.disabled   = false;
            console.error(err);
        }
    });
});