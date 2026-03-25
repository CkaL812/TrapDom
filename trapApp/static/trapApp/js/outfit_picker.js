/* ── Outfit Picker: Events Wheel + Form Submit ── */
document.addEventListener('DOMContentLoaded', function () {

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

    btnUp.addEventListener('click',   () => { if (offset > 0)               { offset--; renderWheel(); } });
    btnDown.addEventListener('click', () => { if (offset + VISIBLE < TOTAL) { offset++; renderWheel(); } });

    viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (e.deltaY > 0 && offset + VISIBLE < TOTAL) { offset++; renderWheel(); }
        if (e.deltaY < 0 && offset > 0)               { offset--; renderWheel(); }
    }, { passive: false });

    renderWheel();


    // ── Форма ────────────────────────────────────────────────
    const form         = document.getElementById('outfit-form');
    const submitBtn    = document.getElementById('submit-btn');
    const btnText      = document.getElementById('btn-text');
    const progress     = document.getElementById('submit-progress');
    const resultArea   = document.getElementById('result-area');
    const resultText   = document.getElementById('result-text');
    const genderSelect = document.getElementById('gender-select');
    const seasonSelect = document.getElementById('season-select');

    let progressTick = null;

    function checkReady() {
        const hasEvent  = eventInput.value.trim().length > 0;
        const hasGender = genderSelect.value !== '';
        const hasSeason = seasonSelect.value !== '';
        const ready     = hasEvent && hasGender && hasSeason;

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

    function showError(msg) {
        clearInterval(progressTick);
        progress.style.width = '0%';
        btnText.textContent  = 'Підібрати образ';
        submitBtn.disabled   = false;
        checkReady();
        resultText.textContent = msg;
        resultArea.classList.remove('hidden');
    }

    eventInput.addEventListener('input',    checkReady);
    genderSelect.addEventListener('change', checkReady);
    seasonSelect.addEventListener('change', checkReady);

    // ── Отримання CSRF токена ─────────────────────────────────
    function getCsrfToken() {
        const fromCookie = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        if (fromCookie) return fromCookie;
        const fromMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (fromMeta) return fromMeta;
        const fromInput = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        return fromInput || '';
    }

    // ── Сабміт ───────────────────────────────────────────────
    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (!eventInput.value.trim() || !genderSelect.value || !seasonSelect.value) {
            showError('⚠ Будь ласка, заповніть всі поля: подію, стать та сезон.');
            return;
        }

        submitBtn.disabled  = true;
        btnText.textContent = 'Підбираємо...';
        resultArea.classList.add('hidden');
        progress.style.width = '0%';

        let pct = 0;
        progressTick = setInterval(() => {
            pct += Math.random() * 10;
            if (pct >= 85) { pct = 85; clearInterval(progressTick); }
            progress.style.width = pct + '%';
        }, 200);

        const payload = {
            event:  eventInput.value.trim(),
            gender: genderSelect.value,
            season: seasonSelect.value,
        };

        try {
            const res = await fetch('/generate-outfit/', {
                method:  'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken':  getCsrfToken(),
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            if (res.status === 401 || res.status === 403) {
                showError('Сесія закінчилась. Перенаправляємо на сторінку входу...');
                setTimeout(() => { window.location.href = '/login/'; }, 1500);
                return;
            }

            if (res.redirected) {
                window.location.href = res.url;
                return;
            }

            let data;
            const contentType = res.headers.get('content-type') || '';

            if (contentType.includes('application/json')) {
                data = await res.json();
            } else {
                const text = await res.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                showError('Помилка сервера. Спробуйте ще раз або оновіть сторінку.');
                return;
            }

            clearInterval(progressTick);
            progress.style.width = '100%';

            setTimeout(() => {
                if (data.status === 'ok' && data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    const msg = data.message || 'Невідома помилка. Спробуйте ще раз.';
                    showError('⚠ ' + msg);
                }
            }, 400);

        } catch (err) {
            showError('Помилка з\'єднання. Перевірте інтернет та спробуйте знову.');
            console.error('Fetch error:', err);
        }
    });
});