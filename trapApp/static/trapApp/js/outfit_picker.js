/* ── Outfit Picker: Collapsibles + Age Display + Equalizer + Form ── */
document.addEventListener('DOMContentLoaded', function () {

    function createCollapsible({ menuEl, triggerEl, bodyEl, chevronEl, hintEl, onOpen, onClose }) {
        let isOpen = false;
        function open() {
            isOpen = true;
            bodyEl.style.maxHeight = bodyEl.scrollHeight + 'px';
            chevronEl.style.transform = 'rotate(180deg)';
            menuEl.classList.add('is-open');
            if (hintEl) hintEl.style.opacity = '0.4';
            onOpen && onOpen();
        }
        function close() {
            isOpen = false;
            bodyEl.style.maxHeight = '0px';
            chevronEl.style.transform = 'rotate(0deg)';
            menuEl.classList.remove('is-open');
            if (hintEl) hintEl.style.opacity = '1';
            onClose && onClose();
        }
        function toggle() { isOpen ? close() : open(); }
        function recalc() { if (isOpen) bodyEl.style.maxHeight = bodyEl.scrollHeight + 'px'; }
        triggerEl.addEventListener('click', toggle);
        document.addEventListener('click', (e) => {
            if (isOpen && !menuEl.contains(e.target)) close();
        });
        return { open, close, toggle, recalc, get isOpen() { return isOpen; } };
    }


    // ── EVENTS ──
    const EVENTS = [
        'День народження', 'Ювілей', 'Заручини', 'Розпис',
        'Весільний банкет (гість)', 'Коктейльна вечірка', 'Формальний вечір',
        'Корпоратив', 'Конференція', 'Нетворкінг', 'Презентація',
        'Публічний виступ', 'Фотосесія', 'Випуск з університету',
        'Театр', 'Опера / філармонія', 'Гала-вечір', 'Благодійний бал',
        'Свято в родині', 'Бранч / зустріч з друзями',
    ];

    const VISIBLE = 4;
    const TOTAL   = EVENTS.length;
    let offset    = 0;
    let activeIdx = -1;

    const eventsMenu    = document.getElementById('events-menu');
    const eventsTrigger = document.getElementById('events-trigger');
    const eventsBody    = document.getElementById('events-body');
    const eventsChevron = document.getElementById('events-chevron');
    const eventsBadge   = document.getElementById('events-selected-badge');
    const eventsHint    = document.getElementById('events-hint');
    const eventsTotal   = document.getElementById('events-total');

    const viewport   = document.getElementById('wheel-viewport');
    const btnUp      = document.getElementById('wheel-up');
    const btnDown    = document.getElementById('wheel-down');
    const counter    = document.getElementById('wheel-counter');
    const eventInput = document.getElementById('event-input');

    eventsTotal.textContent = TOTAL;
    const eventsCollapsible = createCollapsible({
        menuEl: eventsMenu, triggerEl: eventsTrigger,
        bodyEl: eventsBody, chevronEl: eventsChevron, hintEl: eventsHint,
    });

    function renderWheel() {
        viewport.innerHTML = '';
        for (let i = offset; i < offset + VISIBLE && i < TOTAL; i++) {
            const li = document.createElement('div');
            li.className = 'event-wheel-item px-5 py-3 text-sm font-mono text-grunge-gray border-b border-charcoal-700';
            li.textContent = EVENTS[i];
            if (i === activeIdx) li.classList.add('active');
            li.addEventListener('click', (e) => {
                e.stopPropagation();
                activeIdx = i;
                eventInput.value = EVENTS[i];
                eventInput.dispatchEvent(new Event('input'));
                updateEventsBadge();
                renderWheel();
                setTimeout(() => eventsCollapsible.close(), 200);
            });
            viewport.appendChild(li);
        }
        btnUp.disabled   = offset === 0;
        btnDown.disabled = offset + VISIBLE >= TOTAL;
        counter.textContent = `${offset + 1} – ${Math.min(offset + VISIBLE, TOTAL)} / ${TOTAL}`;
        eventsCollapsible.recalc();
    }

    function updateEventsBadge() {
        if (eventInput.value.trim()) {
            eventsBadge.textContent = eventInput.value.trim();
            eventsBadge.classList.remove('hidden');
        } else {
            eventsBadge.classList.add('hidden');
        }
    }

    btnUp.addEventListener('click', (e) => { e.stopPropagation(); if (offset > 0) { offset--; renderWheel(); } });
    btnDown.addEventListener('click', (e) => { e.stopPropagation(); if (offset + VISIBLE < TOTAL) { offset++; renderWheel(); } });
    viewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (e.deltaY > 0 && offset + VISIBLE < TOTAL) { offset++; renderWheel(); }
        if (e.deltaY < 0 && offset > 0)               { offset--; renderWheel(); }
    }, { passive: false });
    renderWheel();


    // ── STYLES ──
    const STYLES = [
        { value: 'classic', label: 'Класичний' },
        { value: 'minimal', label: 'Мінімалізм' },
        { value: 'street',  label: 'Street' },
        { value: 'elegant', label: 'Елегантний' },
        { value: 'sporty',  label: 'Спортивний' },
        { value: 'vintage', label: 'Вінтаж' },
        { value: 'boho',    label: 'Boho' },
        { value: 'avantgarde', label: 'Авангард' },
    ];

    const stylesMenu    = document.getElementById('styles-menu');
    const stylesTrigger = document.getElementById('styles-trigger');
    const stylesBody    = document.getElementById('styles-body');
    const stylesChevron = document.getElementById('styles-chevron');
    const stylesBadge   = document.getElementById('styles-selected-badge');
    const stylesHint    = document.getElementById('styles-hint');
    const stylesFooter  = document.getElementById('styles-footer');
    const stylesCounter = document.getElementById('styles-counter');
    const chipsContainer = document.getElementById('style-chips');
    const chipsClearBtn  = document.getElementById('style-clear');
    const selectedStyles = new Set();

    const stylesCollapsible = createCollapsible({
        menuEl: stylesMenu, triggerEl: stylesTrigger,
        bodyEl: stylesBody, chevronEl: stylesChevron, hintEl: stylesHint,
    });

    function updateStylesBadge() {
        const count = selectedStyles.size;
        if (count > 0) {
            if (count === 1) {
                const first = STYLES.find(s => selectedStyles.has(s.value));
                stylesBadge.textContent = first ? first.label : `${count} обрано`;
            } else {
                stylesBadge.textContent = `${count} обрано`;
            }
            stylesBadge.classList.remove('hidden');
            stylesFooter.classList.remove('hidden');
            stylesFooter.classList.add('flex');
            stylesCounter.textContent = `Обрано: ${count} / ${STYLES.length}`;
        } else {
            stylesBadge.classList.add('hidden');
            stylesFooter.classList.add('hidden');
            stylesFooter.classList.remove('flex');
        }
        stylesCollapsible.recalc();
    }

    function renderChips() {
        chipsContainer.innerHTML = '';
        STYLES.forEach(s => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.dataset.value = s.value;
            chip.className = 'style-chip px-4 py-2 text-[11px] font-mono uppercase tracking-wider border transition-colors';
            chip.textContent = s.label;
            if (selectedStyles.has(s.value)) chip.classList.add('selected');
            chip.addEventListener('click', (e) => {
                e.stopPropagation();
                if (selectedStyles.has(s.value)) selectedStyles.delete(s.value);
                else selectedStyles.add(s.value);
                renderChips();
                updateStylesBadge();
            });
            chipsContainer.appendChild(chip);
        });
    }

    chipsClearBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedStyles.clear();
        renderChips();
        updateStylesBadge();
    });

    renderChips();
    updateStylesBadge();


    // ── AGE ──
    const AGE_MIN = 13, AGE_MAX = 70, AGE_DEFAULT = 25;
    const ageSlider  = document.getElementById('age-slider');
    const ageNumber  = document.getElementById('age-number');
    const agePlus    = document.getElementById('age-plus');
    const ageReset   = document.getElementById('age-reset');
    const ageMinus   = document.getElementById('age-minus');
    const agePlusBtn = document.getElementById('age-plus-btn');
    const ageTicks   = document.getElementById('age-ticks');
    const ageModule  = document.querySelector('.age-module');
    let ageTouched   = false;

    function buildAgeTicks() {
        ageTicks.innerHTML = '';
        for (let i = 0; i <= (AGE_MAX - AGE_MIN); i++) {
            const tick = document.createElement('div');
            tick.className = 'age-tick';
            if (i % 5 === 0) tick.classList.add('age-tick-major');
            ageTicks.appendChild(tick);
        }
    }

    function updateAgeDisplay() {
        const v = +ageSlider.value;
        if (v >= AGE_MAX) {
            ageNumber.textContent = AGE_MAX;
            agePlus.classList.remove('hidden');
        } else {
            ageNumber.textContent = v;
            agePlus.classList.add('hidden');
        }

        const children = ageTicks.children;
        const currentIdx = v - AGE_MIN;
        for (let i = 0; i < children.length; i++) {
            children[i].classList.toggle('active', i <= currentIdx);
            children[i].classList.toggle('is-current', i === currentIdx);
        }

        ageModule.classList.toggle('is-active', ageTouched);
        ageReset.classList.toggle('hidden', !ageTouched);
    }

    function bumpAge(delta) {
        const next = Math.max(AGE_MIN, Math.min(AGE_MAX, +ageSlider.value + delta));
        ageSlider.value = next;
        ageTouched = true;
        updateAgeDisplay();
    }

    ageSlider.addEventListener('input', () => { ageTouched = true; updateAgeDisplay(); });
    ageMinus.addEventListener('click', () => bumpAge(-1));
    agePlusBtn.addEventListener('click', () => bumpAge(1));
    ageReset.addEventListener('click', () => {
        ageTouched = false;
        ageSlider.value = AGE_DEFAULT;
        updateAgeDisplay();
    });

    buildAgeTicks();
    updateAgeDisplay();


    // ── BUDGET EQUALIZER ──
    const BAR_COUNT = 32;
    const BUDGET_MIN_ABS = 500;
    const BUDGET_MAX_ABS = 50000;
    const BUDGET_DEFAULT_MIN = 1000;
    const BUDGET_DEFAULT_MAX = 10000;

    const eqCanvas    = document.getElementById('eq-canvas');
    const eqMinLabel  = document.getElementById('eq-min-label');
    const eqMaxLabel  = document.getElementById('eq-max-label');
    const budgetReset = document.getElementById('budget-reset');
    const budgetModule = document.querySelector('.budget-module');

    let budgetTouched = false;

    function valueToIdx(v) {
        // інверсія від idxToValue (приблизна, через Math.pow)
        const t = (v - BUDGET_MIN_ABS) / (BUDGET_MAX_ABS - BUDGET_MIN_ABS);
        return Math.round(Math.pow(t, 1 / 1.6) * (BAR_COUNT - 1));
    }
    function idxToValue(idx) {
        const t = idx / (BAR_COUNT - 1);
        const val = BUDGET_MIN_ABS + Math.pow(t, 1.6) * (BUDGET_MAX_ABS - BUDGET_MIN_ABS);
        return Math.round(val / 500) * 500;
    }
    function formatUAH(n) {
        if (n >= BUDGET_MAX_ABS) return '50k+ ₴';
        return n.toLocaleString('uk-UA').replace(/\u00A0/g, ' ') + ' ₴';
    }

    let budgetMinIdx = valueToIdx(BUDGET_DEFAULT_MIN);
    let budgetMaxIdx = valueToIdx(BUDGET_DEFAULT_MAX);

    function buildEqualizer() {
        eqCanvas.innerHTML = '';
        for (let i = 0; i < BAR_COUNT; i++) {
            const bar = document.createElement('div');
            bar.className = 'eq-bar';
            bar.dataset.idx = i;
            const heightPct = 35 + (i / (BAR_COUNT - 1)) * 65;
            bar.style.height = heightPct + '%';
            const inner = document.createElement('div');
            inner.className = 'eq-bar-fill';
            bar.appendChild(inner);
            eqCanvas.appendChild(bar);
        }
    }

    function renderEqualizer() {
        const bars = eqCanvas.children;
        for (let i = 0; i < bars.length; i++) {
            const bar = bars[i];
            bar.classList.remove('active', 'edge-min', 'edge-max');
            if (i >= budgetMinIdx && i <= budgetMaxIdx) bar.classList.add('active');
            if (i === budgetMinIdx) bar.classList.add('edge-min');
            if (i === budgetMaxIdx) bar.classList.add('edge-max');
        }

        eqMinLabel.textContent = formatUAH(idxToValue(budgetMinIdx));
        eqMaxLabel.textContent = formatUAH(idxToValue(budgetMaxIdx));

        eqMinLabel.classList.toggle('text-off-white', budgetTouched);
        eqMinLabel.classList.toggle('text-grunge-gray', !budgetTouched);
        eqMaxLabel.classList.toggle('text-off-white', budgetTouched);
        eqMaxLabel.classList.toggle('text-grunge-gray', !budgetTouched);

        budgetModule.classList.toggle('is-active', budgetTouched);
        budgetReset.classList.toggle('hidden', !budgetTouched);
    }

    let dragging = null;

    function idxFromPointer(clientX) {
        const rect = eqCanvas.getBoundingClientRect();
        const x = clientX - rect.left;
        const pct = Math.max(0, Math.min(1, x / rect.width));
        return Math.round(pct * (BAR_COUNT - 1));
    }

    function handlePointer(clientX) {
        const idx = idxFromPointer(clientX);
        if (dragging === null) {
            const dMin = Math.abs(idx - budgetMinIdx);
            const dMax = Math.abs(idx - budgetMaxIdx);
            dragging = dMin <= dMax ? 'min' : 'max';
        }
        if (dragging === 'min') {
            budgetMinIdx = Math.max(0, Math.min(idx, budgetMaxIdx - 1));
        } else {
            budgetMaxIdx = Math.min(BAR_COUNT - 1, Math.max(idx, budgetMinIdx + 1));
        }
        budgetTouched = true;
        renderEqualizer();
    }

    eqCanvas.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        try { eqCanvas.setPointerCapture(e.pointerId); } catch(_) {}
        dragging = null;
        handlePointer(e.clientX);
    });
    eqCanvas.addEventListener('pointermove', (e) => {
        if (dragging !== null && e.buttons > 0) handlePointer(e.clientX);
    });
    eqCanvas.addEventListener('pointerup', (e) => {
        dragging = null;
        try { eqCanvas.releasePointerCapture(e.pointerId); } catch(_) {}
    });
    eqCanvas.addEventListener('pointercancel', () => { dragging = null; });

    budgetReset.addEventListener('click', () => {
        budgetTouched = false;
        budgetMinIdx  = valueToIdx(BUDGET_DEFAULT_MIN);
        budgetMaxIdx  = valueToIdx(BUDGET_DEFAULT_MAX);
        renderEqualizer();
    });

    buildEqualizer();
    renderEqualizer();


    // ── FORM ──
    const form            = document.getElementById('outfit-form');
    const submitBtn       = document.getElementById('submit-btn');
    const btnText         = document.getElementById('btn-text');
    const progress        = document.getElementById('submit-progress');
    const resultArea      = document.getElementById('result-area');
    const resultText      = document.getElementById('result-text');
    const genderSelect    = document.getElementById('gender-select');
    const seasonSelect    = document.getElementById('season-select');
    const dresscodeSelect = document.getElementById('dresscode-select');
    const timeSelect      = document.getElementById('time-select');

    let progressTick = null;

    function checkReady() {
        const ready = eventInput.value.trim().length > 0 && genderSelect.value && seasonSelect.value;
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

    eventInput.addEventListener('input', () => { checkReady(); updateEventsBadge(); });
    genderSelect.addEventListener('change', checkReady);
    seasonSelect.addEventListener('change', checkReady);

    function getCsrfToken() {
        const fromCookie = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
        if (fromCookie) return fromCookie;
        const fromMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (fromMeta) return fromMeta;
        const fromInput = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        return fromInput || '';
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!eventInput.value.trim() || !genderSelect.value || !seasonSelect.value) {
            showError('⚠ Будь ласка, заповніть обов\'язкові поля: подію, стать та сезон.');
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
            event:      eventInput.value.trim(),
            gender:     genderSelect.value,
            season:     seasonSelect.value,
            dresscode:  dresscodeSelect.value || null,
            time:       timeSelect.value || null,
            age:        ageTouched ? +ageSlider.value : null,
            budget_min: budgetTouched ? idxToValue(budgetMinIdx) : null,
            budget_max: budgetTouched ? idxToValue(budgetMaxIdx) : null,
            styles:     Array.from(selectedStyles),
        };

        try {
            const res = await fetch('/generate-outfit/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            if (res.status === 401 || res.status === 403) {
                showError('Сесія закінчилась. Перенаправляємо на сторінку входу...');
                setTimeout(() => { window.location.href = '/login/'; }, 1500);
                return;
            }
            if (res.redirected) { window.location.href = res.url; return; }

            let data;
            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                data = await res.json();
            } else {
                console.error('Non-JSON response');
                showError('Помилка сервера. Спробуйте ще раз або оновіть сторінку.');
                return;
            }

            clearInterval(progressTick);
            progress.style.width = '100%';

            setTimeout(() => {
                if (data.status === 'ok' && data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    showError('⚠ ' + (data.message || 'Невідома помилка. Спробуйте ще раз.'));
                }
            }, 400);

        } catch (err) {
            showError('Помилка з\'єднання. Перевірте інтернет та спробуйте знову.');
            console.error('Fetch error:', err);
        }
    });
});