/* ── Outfit results page: category + subcategory filter ── */
document.addEventListener('DOMContentLoaded', function () {
    const catBtns     = document.querySelectorAll('.cat-btn');
    const cards       = document.querySelectorAll('.item-card');
    const shownCount  = document.getElementById('shown-count');
    const subcatPanel = document.getElementById('subcat-panel');

    let activeCat    = 'all';
    let activeSubcat = null;

    function applyFilters() {
        let count = 0;
        cards.forEach(card => {
            const catMatch    = activeCat === 'all' || card.dataset.cat === activeCat;
            const subcatMatch = !activeSubcat || card.dataset.subcat === activeSubcat;
            const show        = catMatch && subcatMatch;
            card.style.display = show ? '' : 'none';
            if (show) count++;
        });
        if (shownCount) shownCount.textContent = count;
    }

    function buildSubcatPanel(cat) {
        if (!subcatPanel) return;

        if (cat === 'all') {
            subcatPanel.classList.add('hidden');
            return;
        }

        // Collect unique subcats from visible cards of this category
        const subcatMap = {};
        cards.forEach(card => {
            if (card.dataset.cat !== cat) return;
            const sub   = card.dataset.subcat;
            const label = card.querySelector('.absolute span, .absolute')?.textContent?.trim() || sub;
            if (!subcatMap[sub]) subcatMap[sub] = { label, count: 0 };
            subcatMap[sub].count++;
        });

        const keys = Object.keys(subcatMap);
        if (keys.length <= 1) {
            subcatPanel.classList.add('hidden');
            return;
        }

        // Rebuild panel
        const header = subcatPanel.querySelector('p');
        subcatPanel.innerHTML = '';
        if (header) subcatPanel.appendChild(header.cloneNode(true));

        // "Всі" button
        const allBtn = document.createElement('button');
        allBtn.className = 'subcat-filter-btn w-full text-left px-4 py-2.5 font-mono text-[9px] uppercase tracking-widest text-off-white border-b border-charcoal-700 active';
        allBtn.dataset.subcat = '';
        allBtn.innerHTML = `Всі <span class="text-grunge-gray ml-1">(${cards.length})</span>`;
        subcatPanel.appendChild(allBtn);

        keys.forEach(sub => {
            const btn = document.createElement('button');
            btn.className = 'subcat-filter-btn w-full text-left px-4 py-2.5 font-mono text-[9px] uppercase tracking-widest text-grunge-gray border-b border-charcoal-700 last:border-0 hover:text-off-white transition-colors';
            btn.dataset.subcat = sub;
            btn.textContent = subcatMap[sub].label || sub;
            const cnt = document.createElement('span');
            cnt.className = 'text-charcoal-700 ml-1';
            cnt.textContent = `(${subcatMap[sub].count})`;
            btn.appendChild(cnt);
            subcatPanel.appendChild(btn);
        });

        subcatPanel.classList.remove('hidden');
        bindSubcatBtns();
    }

    function bindSubcatBtns() {
        document.querySelectorAll('.subcat-filter-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                document.querySelectorAll('.subcat-filter-btn').forEach(b => b.classList.remove('active', 'text-off-white'));
                document.querySelectorAll('.subcat-filter-btn').forEach(b => b.classList.add('text-grunge-gray'));
                this.classList.add('active', 'text-off-white');
                this.classList.remove('text-grunge-gray');
                activeSubcat = this.dataset.subcat || null;
                applyFilters();
            });
        });
    }

    catBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            activeCat    = this.dataset.cat;
            activeSubcat = null;

            catBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll(`.cat-btn[data-cat="${activeCat}"]`).forEach(b => b.classList.add('active'));

            applyFilters();
            buildSubcatPanel(activeCat);
        });
    });

    applyFilters();
});
