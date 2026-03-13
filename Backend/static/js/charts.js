/* Small dependency-free SVG charts for the progress pages.
   Specs: bars <= 24px with a 4px rounded data-end, hairline grid, sparse direct labels,
   tooltip on hover/focus with a hit target larger than the mark. Colors come from .viz-root CSS tokens. */
(function (root) {
    const NS = 'http://www.w3.org/2000/svg';
    const el = (tag, attrs = {}, parent) => {
        const node = document.createElementNS(NS, tag);
        for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
        if (parent) parent.appendChild(node);
        return node;
    };
    const text = (parent, x, y, value, attrs = {}) => { const t = el('text', { x, y, ...attrs }, parent); t.textContent = value; return t; };

    // Clean ticks: a 1/2/5 x 10^n step with the max rounded up to a whole number of steps
    function niceScale(max, target = 4) {
        if (max <= 0) return { max: 4, step: 1 };
        const raw = max / target, pow = 10 ** Math.floor(Math.log10(raw));
        const step = [1, 2, 5, 10].map((m) => m * pow).find((s) => s >= raw);
        return { max: Math.ceil(max / step) * step, step };
    }
    const compact = (v) => (v >= 1000 ? `${+(v / 1000).toFixed(1)}K` : `${Math.round(v * 10) / 10}`);

    // Column path with a rounded top and a square baseline
    function columnPath(x, y, w, h, r = 4) {
        r = Math.min(r, h, w / 2);
        return `M${x},${y + h} V${y + r} Q${x},${y} ${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h} Z`;
    }

    function tooltip(container) {
        let tip = container.querySelector('.viz-tooltip');
        if (!tip) {
            tip = document.createElement('div');
            tip.className = 'viz-tooltip';
            tip.hidden = true;
            container.appendChild(tip);
        }
        return {
            show(x, y, value, label) {
                tip.replaceChildren();
                const strong = document.createElement('strong');
                strong.textContent = value;
                tip.append(strong, document.createTextNode(label));
                tip.hidden = false;
                const box = container.getBoundingClientRect();
                tip.style.left = `${Math.min(Math.max(x - tip.offsetWidth / 2, 0), box.width - tip.offsetWidth)}px`;
                tip.style.top = `${Math.max(y - tip.offsetHeight - 10, 0)}px`;
            },
            hide() { tip.hidden = true; },
        };
    }

    // Plot frame shared by the charts: y grid + ticks, x labels thinned to avoid collisions
    function frame(container, labels, scale, height) {
        const yMax = scale.max;
        const width = container.clientWidth;
        const m = { top: 18, right: 8, bottom: 26, left: 34 };
        const svg = el('svg', { width, height, viewBox: `0 0 ${width} ${height}`, role: 'img' });
        const plotW = width - m.left - m.right, plotH = height - m.top - m.bottom;
        const y = (v) => m.top + plotH - (v / yMax) * plotH;
        for (let v = 0; v <= yMax + 1e-9; v += scale.step) {
            const i = v;
            el('line', { x1: m.left, x2: width - m.right, y1: y(v), y2: y(v), stroke: i ? 'var(--viz-grid)' : 'var(--viz-axis)', 'stroke-width': 1 }, svg);
            text(svg, m.left - 6, y(v) + 4, compact(v), { 'text-anchor': 'end', 'font-size': 11, fill: 'var(--viz-muted)', style: 'font-variant-numeric: tabular-nums' });
        }
        const band = plotW / labels.length;
        const every = Math.ceil(labels.length / Math.max(1, Math.floor(plotW / 56)));
        const last = labels.length - 1;
        labels.forEach((label, i) => {
            // every k-th label, plus the last one only if it won't collide with the previous shown label
            if (i % every && !(i === last && last % every >= every * 0.75)) return;
            text(svg, m.left + band * (i + 0.5), height - 8, label, { 'text-anchor': 'middle', 'font-size': 11, fill: 'var(--viz-muted)' });
        });
        return { svg, width, m, plotH, band, y };
    }

    // Single-series column chart. data: [{label, value}]
    function columnChart(container, data, { unit = '', height = 220 } = {}) {
        container.replaceChildren();
        container.style.position = 'relative';
        const max = Math.max(0, ...data.map((d) => d.value));
        const { svg, m, band, y } = frame(container, data.map((d) => d.label), niceScale(max), height);
        const tip = tooltip(container);
        const barW = Math.min(24, band * 0.6);
        const peak = data.findIndex((d) => d.value === max && max > 0);
        data.forEach((d, i) => {
            const cx = m.left + band * (i + 0.5), top = y(d.value), h = y(0) - top;
            const hit = el('rect', { x: cx - band / 2, y: m.top, width: band, height: y(0) - m.top, fill: 'transparent', class: 'viz-hit', tabindex: 0,
                                     'aria-label': `${d.label}: ${d.value} ${unit}` }, svg);
            if (h > 0) el('path', { d: columnPath(cx - barW / 2, top, barW, h), fill: 'var(--viz-series-1)', class: 'viz-mark' }, svg);
            const show = () => tip.show(cx, top, `${d.value} ${unit}`.trim(), d.label);
            hit.addEventListener('pointermove', show);
            hit.addEventListener('focus', show);
            hit.addEventListener('pointerleave', tip.hide);
            hit.addEventListener('blur', tip.hide);
            if (i === peak) text(svg, cx, top - 6, compact(d.value), { 'text-anchor': 'middle', 'font-size': 11, 'font-weight': 600, fill: 'var(--viz-ink-2)' });
        });
        container.prepend(svg);
    }

    // Single-series line over a fixed set of x slots; days without a value are skipped. data: [{label, value|null}]
    function lineChart(container, data, { unit = '', height = 220 } = {}) {
        container.replaceChildren();
        container.style.position = 'relative';
        const values = data.map((d) => d.value).filter((v) => v !== null);
        const { svg, m, band, y, width } = frame(container, data.map((d) => d.label), niceScale(Math.max(0, ...values)), height);
        const tip = tooltip(container);
        const x = (i) => m.left + band * (i + 0.5);
        // One line through the days that have a value (rest days are skipped, not drawn as zero)
        let path = '';
        data.forEach((d, i) => { if (d.value !== null) path += `${path ? 'L' : 'M'}${x(i)},${y(d.value)} `; });
        el('path', { d: path, fill: 'none', stroke: 'var(--viz-series-1)', 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
        const lastIdx = data.map((d) => d.value !== null).lastIndexOf(true);
        data.forEach((d, i) => {
            if (d.value === null) return;
            el('circle', { cx: x(i), cy: y(d.value), r: 4, fill: 'var(--viz-series-1)', stroke: 'var(--viz-surface)', 'stroke-width': 2 }, svg);
        });
        if (lastIdx >= 0) text(svg, Math.min(x(lastIdx), width - 20), y(data[lastIdx].value) - 10, `${compact(data[lastIdx].value)}${unit}`,
                               { 'text-anchor': 'middle', 'font-size': 11, 'font-weight': 600, fill: 'var(--viz-ink-2)' });
        // Crosshair: snaps to the nearest x slot that has a value
        const cross = el('line', { y1: m.top, y2: y(0), stroke: 'var(--viz-axis)', 'stroke-width': 1, visibility: 'hidden' }, svg);
        const overlay = el('rect', { x: m.left, y: m.top, width: band * data.length, height: y(0) - m.top, fill: 'transparent', tabindex: 0,
                                     'aria-label': 'Range of motion by day; use arrow keys to step through values' }, svg);
        const points = data.map((d, i) => [i, d]).filter(([, d]) => d.value !== null);
        let focus = points.length - 1;
        const showAt = (k) => {
            if (!points.length) return;
            const [i, d] = points[k];
            cross.setAttribute('x1', x(i)); cross.setAttribute('x2', x(i)); cross.setAttribute('visibility', 'visible');
            tip.show(x(i), y(d.value), `${d.value}${unit}`, d.label);
        };
        overlay.addEventListener('pointermove', (e) => {
            const px = e.clientX - svg.getBoundingClientRect().left;
            focus = points.reduce((best, [i], k) => (Math.abs(x(i) - px) < Math.abs(x(points[best][0]) - px) ? k : best), 0);
            showAt(focus);
        });
        overlay.addEventListener('focus', () => showAt(focus));
        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') focus = Math.max(0, focus - 1);
            else if (e.key === 'ArrowRight') focus = Math.min(points.length - 1, focus + 1);
            else return;
            e.preventDefault();
            showAt(focus);
        });
        const hide = () => { tip.hide(); cross.setAttribute('visibility', 'hidden'); };
        overlay.addEventListener('pointerleave', hide);
        overlay.addEventListener('blur', hide);
        container.prepend(svg);
    }

    // Stacked columns. data: [{label, parts: [..]}], series: [{name, color}] listed bottom -> top
    function stackedColumnChart(container, data, series, { unit = '', height = 220 } = {}) {
        container.replaceChildren();
        container.style.position = 'relative';
        const totals = data.map((d) => d.parts.reduce((a, b) => a + b, 0));
        const { svg, m, band, y } = frame(container, data.map((d) => d.label), niceScale(Math.max(0, ...totals)), height);
        const tip = tooltip(container);
        const barW = Math.min(24, band * 0.6), GAP = 2;
        data.forEach((d, i) => {
            const cx = m.left + band * (i + 0.5);
            const hit = el('rect', { x: cx - band / 2, y: m.top, width: band, height: y(0) - m.top, fill: 'transparent', class: 'viz-hit', tabindex: 0,
                                     'aria-label': `${d.label}: ` + series.map((s, k) => `${d.parts[k]} ${s.name}`).join(', ') }, svg);
            const group = el('g', { class: 'viz-mark' }, svg);
            let base = y(0);
            const top = d.parts.reduce((last, v, k) => (v > 0 ? k : last), -1);
            d.parts.forEach((v, k) => {
                if (!v) return;
                const h = y(0) - y(v);
                const segTop = base - h, drawH = Math.max(h - (k === top ? 0 : GAP), 1);
                // only the top segment gets the rounded data-end; a 2px surface gap separates segments
                el('path', { d: k === top ? columnPath(cx - barW / 2, segTop, barW, drawH) : `M${cx - barW / 2},${segTop + GAP} h${barW} v${drawH} h${-barW} Z`,
                             fill: series[k].color }, group);
                base = segTop;
            });
            const show = () => {
                tip.show(cx, y(totals[i]), `${totals[i]} ${unit}`.trim(), `${d.label} · ` + series.map((s, k) => `${d.parts[k]} ${s.name.toLowerCase()}`).join(', '));
            };
            hit.addEventListener('pointermove', show);
            hit.addEventListener('focus', show);
            hit.addEventListener('pointerleave', tip.hide);
            hit.addEventListener('blur', tip.hide);
        });
        container.prepend(svg);
    }

    // Re-render charts when their container resizes
    function responsive(container, render) {
        render();
        let w = container.clientWidth;
        new ResizeObserver(() => { if (container.clientWidth !== w) { w = container.clientWidth; render(); } }).observe(container);
    }

    root.Charts = { columnChart, lineChart, stackedColumnChart, responsive, niceScale, frame, tooltip, columnPath, el, text, compact };
})(this);
