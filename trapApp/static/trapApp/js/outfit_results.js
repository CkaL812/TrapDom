/* ── Outfit Results: filter buttons URL update ── */
document.addEventListener('DOMContentLoaded', function () {
    const urlParams = new URLSearchParams(window.location.search);
    const ids       = urlParams.getAll('ids');
    const eventName = urlParams.get('event') || '';
    const gender    = urlParams.get('gender') || '';
    const season    = urlParams.get('season') || '';
    const style     = urlParams.get('style') || '';

    document.querySelectorAll('.filter-btn').forEach(btn => {
        const catKey = btn.dataset.cat;
        if (!catKey) return;
        const params = new URLSearchParams();
        ids.forEach(id => params.append('ids', id));
        params.set('cat', catKey);
        if (eventName) params.set('event', eventName);
        if (gender) params.set('gender', gender);
        if (season) params.set('season', season);
        if (style) params.set('style', style);
        btn.href = '?' + params.toString();
    });
});