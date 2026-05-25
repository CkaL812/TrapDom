// ═══════════════════════════════════════════════
//   VIRTUAL TRY-ON — TrapDom
// ═══════════════════════════════════════════════

// ── State ──
let personFile   = null;
let clothingFile = null;
let currentTab   = 'catalog';
let pollingTimer = null;

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    setupPersonUpload();
    setupClothUpload();
    setupGuideToggle();
    document.getElementById('tryon-btn').addEventListener('click', startTryOn);
    checkReady();
});

// ══════════════════════════════════════════════
//   PERSON PHOTO
// ══════════════════════════════════════════════

function setupPersonUpload() {
    const zone  = document.getElementById('person-drop-zone');
    const input = document.getElementById('person-file');

    input.addEventListener('change', () => {
        if (input.files[0]) applyPersonFile(input.files[0]);
    });

    zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', ()  => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const f = e.dataTransfer.files[0];
        if (f && f.type.startsWith('image/')) applyPersonFile(f);
    });
}

function applyPersonFile(file) {
    personFile = file;
    previewFile(file, 'person-preview', 'person-placeholder', 'person-preview-wrap');
    checkReady();
}

function removePerson() {
    personFile = null;
    document.getElementById('person-file').value = '';
    clearPreview('person-preview', 'person-placeholder', 'person-preview-wrap');
    checkReady();
}

// ══════════════════════════════════════════════
//   CLOTHING UPLOAD TAB
// ══════════════════════════════════════════════

function setupClothUpload() {
    const zone  = document.getElementById('cloth-drop-zone');
    const input = document.getElementById('cloth-file');

    input.addEventListener('change', () => {
        if (input.files[0]) applyClothFile(input.files[0]);
    });

    zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', ()  => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const f = e.dataTransfer.files[0];
        if (f && f.type.startsWith('image/')) applyClothFile(f);
    });
}

function applyClothFile(file) {
    clothingFile = file;
    previewFile(file, 'cloth-preview', 'cloth-placeholder', 'cloth-preview-wrap');
    checkReady();
}

function removeCloth() {
    clothingFile = null;
    document.getElementById('cloth-file').value = '';
    clearPreview('cloth-preview', 'cloth-placeholder', 'cloth-preview-wrap');
    checkReady();
}

function previewFile(file, imgId, placeholderId, wrapId) {
    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById(imgId).src = e.target.result;
        document.getElementById(placeholderId).classList.add('hidden');
        document.getElementById(wrapId).classList.add('visible');
    };
    reader.readAsDataURL(file);
}

function clearPreview(imgId, placeholderId, wrapId) {
    document.getElementById(imgId).src = '';
    document.getElementById(placeholderId).classList.remove('hidden');
    document.getElementById(wrapId).classList.remove('visible');
}

// ══════════════════════════════════════════════
//   TAB SWITCHING
// ══════════════════════════════════════════════

function switchClothTab(tab) {
    currentTab = tab;
    const isCatalog = tab === 'catalog';

    document.getElementById('cloth-catalog-panel').classList.toggle('hidden', !isCatalog);
    document.getElementById('cloth-upload-panel').classList.toggle('hidden', isCatalog);
    document.getElementById('tab-catalog').classList.toggle('tryon-tab-active', isCatalog);
    document.getElementById('tab-upload').classList.toggle('tryon-tab-active', !isCatalog);

    if (isCatalog) clothingFile = null;
    checkReady();
}

// ══════════════════════════════════════════════
//   GUIDE TOGGLE
// ══════════════════════════════════════════════

function setupGuideToggle() {
    const trigger = document.getElementById('guide-trigger');
    const body    = document.getElementById('guide-body');
    const chevron = document.getElementById('guide-chevron');

    trigger.addEventListener('click', () => {
        const open = !body.classList.contains('hidden');
        body.classList.toggle('hidden', open);
        chevron.style.transform = open ? '' : 'rotate(180deg)';
    });
}

// ══════════════════════════════════════════════
//   VALIDATION
// ══════════════════════════════════════════════

function checkReady() {
    const hasPerson = !!personFile;

    let hasCloth = false;
    if (currentTab === 'upload') {
        hasCloth = !!clothingFile;
    } else {
        hasCloth = !!(window.PRESELECTED_ITEM);
    }

    const ready = hasPerson && hasCloth;
    const btn   = document.getElementById('tryon-btn');
    btn.disabled = !ready;
    btn.classList.toggle('ready', ready);
}

// ══════════════════════════════════════════════
//   TRY-ON START
// ══════════════════════════════════════════════

async function startTryOn() {
    const btn = document.getElementById('tryon-btn');
    if (btn.disabled || btn.classList.contains('loading')) return;

    hideError();
    setLoading(true);

    const form = new FormData();
    form.append('person_photo', personFile);

    if (currentTab === 'upload' && clothingFile) {
        form.append('clothing_photo', clothingFile);
    } else if (currentTab === 'catalog' && window.PRESELECTED_ITEM) {
        form.append('item_ids[]', window.PRESELECTED_ITEM.id);
    }

    try {
        const res  = await fetch('/virtual-tryon/start/', {
            method:  'POST',
            headers: { 'X-CSRFToken': CSRF_TOKEN },
            body:    form,
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Помилка відправки');
        startPolling(data.job_id);
    } catch (err) {
        setLoading(false);
        showError(err.message || 'Помилка. Спробуйте ще раз.');
    }
}

// ══════════════════════════════════════════════
//   POLLING — тихий, лише спінер на кнопці
// ══════════════════════════════════════════════

function startPolling(jobId) {
    pollingTimer = setInterval(async () => {
        try {
            const res  = await fetch(`/virtual-tryon/status/${jobId}/`);
            const data = await res.json();

            if (data.status === 'done') {
                clearInterval(pollingTimer);
                window.location.href = `/virtual-tryon/result/${jobId}/`;
            } else if (data.status === 'error') {
                clearInterval(pollingTimer);
                setLoading(false);
                showError(data.error || 'Помилка обробки. Спробуйте ще раз.');
            }
        } catch { /* мережевий збій — продовжуємо */ }
    }, 3000);
}

// ══════════════════════════════════════════════
//   UI STATES
// ══════════════════════════════════════════════

function setLoading(on) {
    const btn     = document.getElementById('tryon-btn');
    const btnText = document.getElementById('tryon-btn-text');
    const spinner = document.getElementById('tryon-btn-spinner');

    if (on) {
        btn.disabled = true;
        btn.classList.remove('ready');
        btn.classList.add('loading');
        btnText.textContent = 'Обробляємо';
        spinner.classList.remove('hidden');
    } else {
        btn.classList.remove('loading');
        btn.classList.add('ready');
        btnText.textContent = 'Приміряти';
        spinner.classList.add('hidden');
        checkReady();
    }
}

function showError(msg) {
    const wrap = document.getElementById('tryon-error');
    document.getElementById('tryon-error-text').textContent = msg;
    wrap.classList.remove('hidden');
    wrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    document.getElementById('tryon-error').classList.add('hidden');
}
