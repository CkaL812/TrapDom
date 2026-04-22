document.addEventListener('DOMContentLoaded', () => {
    const img = document.getElementById('main-img');

    document.querySelectorAll('.thumb').forEach(t => t.addEventListener('click', function() {
        document.querySelectorAll('.thumb').forEach(x => x.classList.remove('active'));
        this.classList.add('active');
        if (img) { img.style.opacity = 0; setTimeout(() => { img.src = this.dataset.src; img.style.opacity = 1; }, 200); }
    }));

    document.querySelectorAll('.size-btn:not(.no-stock)').forEach(b => b.addEventListener('click', function() {
        document.querySelectorAll('.size-btn').forEach(x => x.classList.remove('active'));
        this.classList.add('active');
        document.getElementById('sel-size').value = this.dataset.size;
    }));

    const qv = document.getElementById('qty-num');
    document.getElementById('qty-m')?.addEventListener('click', () => { let v = +qv.textContent; if (v > 1) qv.textContent = v - 1; });
    document.getElementById('qty-p')?.addEventListener('click', () => { qv.textContent = +qv.textContent + 1; });

    document.getElementById('btn-cart')?.addEventListener('click', function() {
        const id = +this.dataset.id, size = document.getElementById('sel-size')?.value || '', qty = +(qv?.textContent || 1);
        if (typeof trapAddToCart === 'function') trapAddToCart(id, size, qty, this);
    });

    document.getElementById('btn-buy')?.addEventListener('click', function() {
        const id = +this.dataset.id, size = document.getElementById('sel-size')?.value || '', qty = +(qv?.textContent || 1);
        fetch('/cart/add/' + id + '/', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({size, quantity:qty}) })
        .then(r => r.json()).then(d => { if (d.status === 'ok') location.href = '/cart/'; });
    });
});
