/* ── Cart page: quantity buttons & remove buttons ── */
document.addEventListener('DOMContentLoaded', function () {

    function updateTotals(total, currency) {
        const t1 = document.getElementById('page-total');
        const t2 = document.getElementById('page-total-big');
        if (t1) t1.textContent = `${total} ${currency}`;
        if (t2) t2.textContent = `${total} ${currency}`;
    }

    /* Qty buttons */
    document.querySelectorAll('.qty-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const key   = this.dataset.key;
            const delta = parseInt(this.dataset.delta);
            const row   = document.querySelector(`.cart-row[data-key="${key}"]`);
            if (!row) return;
            const currentQty = parseInt(row.querySelector('.qty-display').textContent);
            const newQty     = currentQty + delta;

            fetch('/cart/update/', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ key, quantity: newQty }),
            })
            .then(r => r.json())
            .then(data => {
                if (data.removed) {
                    row.style.opacity = '0';
                    row.style.transform = 'translateX(-20px)';
                    row.style.transition = 'all 0.25s ease';
                    setTimeout(() => {
                        row.remove();
                        updateTotals(data.cart_total, data.cart_currency);
                        if (data.cart_count === 0) location.reload();
                    }, 250);
                } else {
                    row.querySelector('.qty-display').textContent = newQty;
                    row.querySelector('.subtotal').textContent    = `${data.subtotal} ${data.cart_currency}`;
                    updateTotals(data.cart_total, data.cart_currency);
                    /* Оновлення data-qty */
                    row.querySelectorAll('.qty-btn').forEach(b => b.dataset.qty = newQty);
                }
            });
        });
    });

    /* Remove buttons */
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const key = this.dataset.key;
            const row = document.querySelector(`.cart-row[data-key="${key}"]`);
            fetch('/cart/remove/', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ key }),
            })
            .then(r => r.json())
            .then(data => {
                if (row) {
                    row.style.opacity   = '0';
                    row.style.transform = 'translateX(-20px)';
                    row.style.transition = 'all 0.25s ease';
                    setTimeout(() => {
                        row.remove();
                        updateTotals(data.cart_total, data.cart_currency);
                        if (data.cart_count === 0) location.reload();
                    }, 250);
                }
            });
        });
    });
});
