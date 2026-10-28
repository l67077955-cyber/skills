// DOM-measured connector router (framework-free port of the FlashTrace Figure 2 router).
// Usage:
//   <div id="fig" style="position:relative"> ...boxes with data-a="id"... <svg class="conn"></svg></div>
//   routeConnectors(document.getElementById('fig'), CONN);
// Each connector: { f, fs, t, ts, r, k, ff?, tf?, mxo?, bend? }
//   f/t   : data-a ids of source / target element
//   fs/ts : side 't' | 'b' | 'l' | 'r'; ff/tf: fraction along that side (default .5)
//   r     : 'v' | 'vh' | 'hv' | 'vhv' | 'hvh' | 'curve' | undefined (straight)
//   mxo   : for 'hvh', offset of the vertical leg past the rightmost endpoint
//   bend  : for 'curve', perpendicular control-point offset (sign = side)
//   k     : style key in STYLES
(function () {
  const STYLES = {
    // [arrowLength, arrowHalfWidth, cornerRadius], then stacked strokes (bottom → top), then head fill
    pipe:  { head: [12, 7.5, 10], strokes: [['#94a4d8', 5.5], ['#eef1fb', 1.6]], fill: '#7e8fcc' },
    thin:  { head: [7, 3.5, 5],   strokes: [['#1b2130', 1.2]],                    fill: '#1b2130' },
    hop:   { head: [11, 5.5, 0],  strokes: [['#ffffff', 5.5, .85], ['#3f4a72', 2.6]], fill: '#3f4a72' },
    trace: { head: [8, 4, 0],     strokes: [['#ffffff', 4.5, .85], ['#1b2130', 1.6]], fill: '#1b2130' },
  };
  const f1 = n => n.toFixed(1);

  function head([p, q], L, W) {
    const dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const bx = q.x - ux * L, by = q.y - uy * L, nx = -uy, ny = ux;
    return { end: { x: bx + ux * 1.5, y: by + uy * 1.5 },
      poly: `${f1(q.x)},${f1(q.y)} ${f1(bx + nx * W)},${f1(by + ny * W)} ${f1(bx - nx * W)},${f1(by - ny * W)}` };
  }
  function rounded(pts, r) {
    let d = `M${f1(pts[0].x)},${f1(pts[0].y)}`;
    for (let i = 1; i < pts.length - 1; i++) {
      const a = pts[i - 1], b = pts[i], c = pts[i + 1];
      const d1 = Math.hypot(b.x - a.x, b.y - a.y), d2 = Math.hypot(c.x - b.x, c.y - b.y);
      const rr = Math.min(r, d1 / 2, d2 / 2);
      const p1 = { x: b.x + (a.x - b.x) / d1 * rr, y: b.y + (a.y - b.y) / d1 * rr };
      const p2 = { x: b.x + (c.x - b.x) / d2 * rr, y: b.y + (c.y - b.y) / d2 * rr };
      d += ` L${f1(p1.x)},${f1(p1.y)} Q${f1(b.x)},${f1(b.y)} ${f1(p2.x)},${f1(p2.y)}`;
    }
    const l = pts[pts.length - 1];
    return d + ` L${f1(l.x)},${f1(l.y)}`;
  }

  function draw(root, conns, svg) {
    const rb = root.getBoundingClientRect(), k = rb.width / root.offsetWidth || 1;
    const box = id => { const el = root.querySelector(`[data-a="${id}"]`); if (!el) return null;
      const b = el.getBoundingClientRect();
      return { x: (b.left - rb.left) / k, y: (b.top - rb.top) / k, w: b.width / k, h: b.height / k }; };
    const pt = (b, s, f) => s === 't' ? { x: b.x + b.w * f, y: b.y } : s === 'b' ? { x: b.x + b.w * f, y: b.y + b.h }
      : s === 'l' ? { x: b.x, y: b.y + b.h * f } : { x: b.x + b.w, y: b.y + b.h * f };
    const layers = {};
    for (const c of conns) {
      const A = box(c.f), B = box(c.t); if (!A || !B) continue;
      const st = STYLES[c.k], [L, W, R] = st.head;
      const p = pt(A, c.fs, c.ff ?? .5), q = pt(B, c.ts, c.tf ?? .5);
      let d, poly;
      if (c.r === 'curve') {
        const mx = (p.x + q.x) / 2, my = (p.y + q.y) / 2, dx = q.x - p.x, dy = q.y - p.y, dd = Math.hypot(dx, dy) || 1;
        const ctl = { x: mx - dy / dd * c.bend, y: my + dx / dd * c.bend };
        const h = head([ctl, q], L, W);
        d = `M${f1(p.x)},${f1(p.y)} Q${f1(ctl.x)},${f1(ctl.y)} ${f1(h.end.x)},${f1(h.end.y)}`; poly = h.poly;
      } else {
        let pts;
        if (c.r === 'v') pts = [p, { x: p.x, y: q.y }];
        else if (c.r === 'vh') pts = [p, { x: p.x, y: q.y }, q];
        else if (c.r === 'hv') pts = [p, { x: q.x, y: p.y }, q];
        else if (c.r === 'vhv') { const my = (p.y + q.y) / 2; pts = [p, { x: p.x, y: my }, { x: q.x, y: my }, q]; }
        else if (c.r === 'hvh') { const mx = c.mxo != null ? Math.max(p.x, q.x) + c.mxo : (p.x + q.x) / 2;
          pts = [p, { x: mx, y: p.y }, { x: mx, y: q.y }, q]; }
        else pts = [p, q];
        pts = pts.filter((a, i) => i === 0 || Math.hypot(a.x - pts[i - 1].x, a.y - pts[i - 1].y) > .5);
        if (pts.length < 2) continue;
        const h = head(pts.slice(-2), L, W); pts[pts.length - 1] = h.end;
        d = rounded(pts, R); poly = h.poly;
      }
      const g = st.strokes.map(([col, w, op]) =>
        `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" stroke-linejoin="round"${op ? ` opacity="${op}"` : ''}/>`).join('');
      (layers[c.k] ||= []).push(g + `<polygon points="${poly}" fill="${st.fill}" stroke="${st.fill}" stroke-linejoin="round"/>`);
    }
    // paint order: pipes under thins under hops under traces
    svg.innerHTML = ['pipe', 'thin', 'hop', 'trace'].map(k => (layers[k] || []).join('')).join('');
  }

  window.routeConnectors = function (root, conns) {
    let svg = root.querySelector('svg.conn');
    if (!svg) { svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.classList.add('conn'); root.appendChild(svg); }
    Object.assign(svg.style, { position: 'absolute', left: 0, top: 0, width: '100%', height: '100%',
      overflow: 'visible', pointerEvents: 'none', zIndex: 3 });
    let raf; const sched = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => draw(root, conns, svg)); };
    new ResizeObserver(sched).observe(root);
    addEventListener('resize', sched);
    document.fonts && document.fonts.ready.then(sched);
    [150, 700, 1800].forEach(t => setTimeout(sched, t)); // late font/layout settles
    sched();
    return sched;
  };
  window.routeConnectors.STYLES = STYLES;
})();
