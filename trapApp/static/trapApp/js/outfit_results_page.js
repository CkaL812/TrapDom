/* ── Outfit results page: category filter ── */
document.addEventListener('DOMContentLoaded', function () {
    const catBtns    = document.querySelectorAll('.cat-btn');
    const cards      = document.querySelectorAll('.item-card');
    const shownCount = document.getElementById('shown-count');

    catBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const cat = this.dataset.cat;

            catBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll(`.cat-btn[data-cat="${cat}"]`).forEach(b => b.classList.add('active'));

            let count = 0;
            cards.forEach(card => {
                const show = cat === 'all' || card.dataset.cat === cat;
                if (show) {
                    card.style.display = '';
                    card.classList.remove('fade-up');
                    void card.offsetWidth;
                    card.classList.add('fade-up');
                    count++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (shownCount) shownCount.textContent = count;
        });
    });
});
