// Oblique "anatomy" figure kit: rounded prisms in four-tone material, floating with soft shadows,
// DOM-measured silhouettes for connectors, and a label stack under every part.
// Depends on lib.js (el, rich, marker, path). Camera: depth y runs up-right (x + .62y, -z - .42y).
function Fig(svg, opts = {}) {
  const KX = .62, KY = -.42, FLOAT = opts.float ?? 22;
  const pr = (x, y, z) => [x + y * KX, -z + y * KY];
  const P = pts => pts.map(p => p[0].toFixed(2) + ',' + p[1].toFixed(2)).join(' ');
  const mix = (hex, t) => { const n = parseInt(hex.slice(1), 16), c = [n >> 16, n >> 8 & 255, n & 255].map(v => Math.round(v + (255 - v) * t)); return `rgb(${c})`; };
  // role = the semantic colour of a part. Keep to this set so a figure reads as one system;
  // extra roles can be passed in via opts.roles and will still get a distinct cap tint.
  const ROLE = { neutral: '#d6d6d3', check: '#c3d0e6', limit: '#bfd6da', route: '#c6dcc8', bill: '#dbd6ce', up: '#d3cce8', avail: '#dfe4cf', frozen: '#c9d9e6', used: '#d3d3d6', warn: '#e0d0b0', ...(opts.roles || {}) };
  if (new URLSearchParams(location.search).has('mono')) for (const k in ROLE) ROLE[k] = '#d6d6d3';  // ?mono: all parts neutral
  const ICE = new URLSearchParams(location.search).get('pal') !== 'classic';
  // ice: one hue (indigo). Bodies near-white with hue-tinted sides, roles only tint the top cap, edges/shadows in the hue
  const ICE_TOP = { neutral: '#f4f6fd', check: '#e1e9ff', limit: '#def7f9', route: '#e6f7ed', bill: '#f1f0ef', up: '#ebe4ff', avail: '#f1f6e2', frozen: '#e9f1f9', used: '#f0f0f3', warn: '#fdf0dd' };
  const mat = Object.fromEntries(Object.entries(ROLE).map(([k, c]) => [k, ICE
    ? { shade: ['#c3cde8', '#d6deef', '#e8edf8', ICE_TOP[k] || mix(c, .88)], top: '#ffffff', key: ICE_TOP[k] || mix(c, .55) }
    : { shade: [mix(c, .16), mix(c, .4), mix(c, .62), mix(c, .8)], top: mix(c, .93), key: c }]));
  const INK = ICE ? { edge: '#4a5784', crease: 'rgba(62,99,221,.14)', faint: 'rgba(62,99,221,.22)', mid: '#8da4ef', lo: '#abbdf9', lit: '#3e63dd', red: '#e5484d' }
    : { edge: '#2b2b30', crease: 'rgba(40,40,50,.16)', faint: 'rgba(40,40,50,.22)', mid: '#8a8a8f', lo: '#b4b4b8', lit: '#000', red: '#cf4449' };
  const defs = el(svg, 'defs');
  const BG = opts.bg || (ICE ? '#ffffff' : '#faf7ef');
  if (ICE) document.documentElement.classList.add('ice');
  for (const [id, sd] of [['haloNear', 5], ['haloFar', 15]]) { const f = el(defs, 'filter', { id, x: '-40%', y: '-120%', width: '180%', height: '340%' }); el(f, 'feGaussianBlur', { stdDeviation: sd }); }
  // depth falloff: a side face fades from its tone at the front edge toward the paper at the back edge
  const grads = {};
  const fade = c => { if (grads[c]) return grads[c]; const id = 'df' + Object.keys(grads).length;
    const g = el(defs, 'linearGradient', { id, x1: 0, y1: 0, x2: 1, y2: 0 });
    el(g, 'stop', { offset: 0, 'stop-color': c }); el(g, 'stop', { offset: 1, 'stop-color': c, 'stop-opacity': .55 });
    return (grads[c] = `url(#${id})`); };
  marker(svg, 'arr', INK.edge, 7, 2.8); marker(svg, 'arrLit', INK.lit, 8, 3.2); marker(svg, 'arrMid', INK.mid, 7, 2.8); marker(svg, 'arrRej', INK.red, 7, 2.8);
  const L = { floor: el(svg, 'g'), solid: el(svg, 'g'), line: el(svg, 'g'), text: el(svg, 'g') };

  function rr(x, y, w, d, r, steps = 6) {
    const pts = [];
    for (const [cx, cy, a0] of [[x + w - r, y + r, -90], [x + w - r, y + d - r, 0], [x + r, y + d - r, 90], [x + r, y + r, 180]])
      for (let i = 0; i <= steps; i++) { const a = (a0 + 90 * i / steps) * Math.PI / 180; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
    return pts;
  }
  const circ = (cx, cy, r, n = 48) => Array.from({ length: n }, (_, i) => { const a = -Math.PI / 2 + 2 * Math.PI * i / n; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; });
  function hull(pts) {
    const p = [...pts].sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lo = [], up = [];
    for (const q of p) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
    for (const q of p.reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], q) <= 0) up.pop(); up.push(q); }
    return lo.slice(0, -1).concat(up.slice(0, -1));
  }
  function spanAt(H, y) {
    const xs = [];
    for (let i = 0; i < H.length; i++) { const a = H[i], b = H[(i + 1) % H.length];
      if ((a[1] - y) * (b[1] - y) <= 0 && a[1] !== b[1]) xs.push(a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])); }
    return xs.length ? [Math.min(...xs), Math.max(...xs)] : null;
  }
  const element = (parent = L.solid) => ({ g: el(parent, 'g'), hulls: [], feet: [], dx: 0, dy: 0 });
  function prism(E, ring, z, h, role = 'neutral', o = {}) {
    const m = mat[role], g = el(E.g, 'g');
    const bot = ring.map(([x, y]) => pr(x, y, z)), top = ring.map(([x, y]) => pr(x, y, z + h)), H = hull(bot.concat(top));
    el(g, 'polygon', { points: P(H), fill: '#fff' });
    const n = ring.length, crease = [];
    for (let i = 0; i < n; i++) {
      const a = ring[i], b = ring[(i + 1) % n], dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, nx = dy / len, ny = -dx / len;
      if (KX * nx - ny <= .015) continue;
      const lit = -.36 * nx - .93 * ny, s = lit > .8 ? 3 : lit > .45 ? 2 : lit > .05 ? 1 : 0, c = m.shade[s];
      const side = Math.abs(nx) > .7 && len > 8;   // long faces that run back into depth get the falloff; round parts stay solid
      el(g, 'polygon', { points: P([bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]]), fill: side ? fade(c) : c, stroke: side ? 'none' : c, 'stroke-width': .5, 'stroke-linejoin': 'round' });
      crease.push(`M${top[i][0].toFixed(2)},${top[i][1].toFixed(2)}L${top[(i + 1) % n][0].toFixed(2)},${top[(i + 1) % n][1].toFixed(2)}`);
    }
    el(g, 'polygon', { points: P(top), fill: m.top, stroke: m.top, 'stroke-width': .4 });
    if (crease.length) el(g, 'path', { d: crease.join(''), stroke: INK.crease, 'stroke-width': .7, fill: 'none' });
    if (o.bevel) el(g, 'polygon', { points: P(o.bevel.map(([x, y]) => pr(x, y, z + h))), fill: 'none', stroke: INK.faint, 'stroke-width': .6 });
    el(g, 'polygon', { points: P(H), fill: 'none', stroke: o.lit ? INK.lit : INK.edge, 'stroke-width': o.lit ? 1.25 : .8, 'stroke-linejoin': 'round', 'stroke-dasharray': o.ghost ? '4 3' : null });
    if (o.ghost) g.setAttribute('opacity', .75);
    E.hulls.push(H);
    if (o.foot !== false && z <= (o.footZ ?? 0.01)) E.feet.push(ring.map(([x, y]) => [x, y, z]));
    return g;
  }
  const box = (E, x, y, w, d, z, h, r, role, o = {}) => prism(E, rr(x, y, w, d, r, o.steps || 6), z, h, role,
    { ...o, bevel: o.bevel === false ? null : rr(x + 1.8, y + 1.8, w - 3.6, d - 3.6, Math.max(r - 1.8, .4), o.steps || 6) });
  const cyl = (E, cx, cy, r, z, h, role, o = {}) => prism(E, circ(cx, cy, r, o.n || 56), z, h, role, o);
  const hair = (E, a, b, stroke = INK.faint, w = .6) => el(E.g, 'line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke, 'stroke-width': w, 'stroke-linecap': 'round' });
  const screw = (E, x, y, z) => { const p = pr(x, y, z); el(E.g, 'ellipse', { cx: p[0], cy: p[1], rx: 2.3, ry: 1.3, fill: 'none', stroke: INK.lo, 'stroke-width': .6 }); el(E.g, 'circle', { cx: p[0], cy: p[1], r: .75, fill: INK.mid }); };
  // a recessed window on a front face (y = const), from (x0,z0) to (x1,z1)
  const windowOn = (E, x0, x1, y, z0, z1, fill = ICE ? '#f7f9ff' : '#f6f4ee') => {
    const a = pr(x0, y, z1), b = pr(x1, y, z0);
    el(E.g, 'rect', { x: a[0], y: a[1], width: b[0] - a[0], height: b[1] - a[1], rx: 4.5, fill, stroke: INK.mid, 'stroke-width': .7 });
    el(E.g, 'rect', { x: a[0] + 2.5, y: a[1] + 2.5, width: b[0] - a[0] - 5, height: b[1] - a[1] - 5, rx: 3, fill: 'none', stroke: INK.faint, 'stroke-width': .6 });
    return { x: a[0], y: a[1], w: b[0] - a[0], h: b[1] - a[1] };
  };
  const bbox = E => { const xs = E.hulls.flat().map(p => p[0]), ys = E.hulls.flat().map(p => p[1]); return [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]; };
  const move = (E, dx, dy = 0) => { E.dx += dx; E.dy += dy; E.g.setAttribute('transform', `translate(${E.dx.toFixed(2)},${E.dy.toFixed(2)})`); E.hulls = E.hulls.map(H => H.map(([x, y]) => [x + dx, y + dy])); };
  const at = (E, p) => [p[0] + E.dx, p[1] + E.dy];
  const edgeAt = (E, y, side) => { let best = null; for (const H of E.hulls) { const s = spanAt(H, y); if (s) best = best ? [Math.min(best[0], s[0]), Math.max(best[1], s[1])] : s; }
    if (!best) { const [l, r] = bbox(E); best = [l, r]; } return side === 'l' ? best[0] : best[1]; };
  // soft shadow on an invisible floor FLOAT below the part's base
  // soft shadow on an invisible floor FLOAT below the part: a tight penumbra plus a wide ambient layer,
  // both pushed a little down-right (light from the upper left)
  function shadow(E, k = 1) {
    for (const ring of E.feet) {
      const pts = hull(ring.map(([x, y, z]) => pr(x, y, z - FLOAT))).map(([x, y]) => [x + E.dx, y + E.dy]);
      const cx = pts.reduce((a, p) => a + p[0], 0) / pts.length, cy = pts.reduce((a, p) => a + p[1], 0) / pts.length;
      const grow = (f, dx, dy) => P(pts.map(([x, y]) => [cx + (x - cx) * f + dx, cy + (y - cy) * f + dy]));
      el(L.floor, 'polygon', { points: grow(1.06, 14, 10), fill: ICE ? '#3e63dd' : '#6f6a5e', opacity: (ICE ? .09 : .13) * k, filter: 'url(#haloFar)' });
      el(L.floor, 'polygon', { points: grow(.94, 5, 3), fill: ICE ? '#1f2d5c' : '#5f5a50', opacity: (ICE ? .12 : .16) * k, filter: 'url(#haloNear)' });
    }
  }
  const line = (pts, o = {}) => el(o.parent || L.line, 'path', { d: path(pts, o.r ?? 8), fill: 'none', stroke: o.stroke || INK.edge, 'stroke-width': o.w || 1, 'stroke-dasharray': o.dash || null,
    'marker-end': o.m === null ? null : `url(#${o.m || 'arr'})`, 'marker-start': o.ms ? `url(#${o.ms})` : null });
  const T = (x, y, s, cls, anchor = 'middle', parent = L.text) => rich(parent, x, y, s, { class: cls, 'text-anchor': anchor });
  const lineStyle = { solid: {}, lit: { stroke: INK.lit, w: 1.35, m: 'arrLit' }, alt: { stroke: INK.mid, w: .9, m: 'arrMid', dash: '4 3' }, back: { stroke: INK.mid, w: 1, m: 'arrMid', dash: '5 4' }, rej: { stroke: INK.red, m: 'arrRej' } };

  // lay parts out on one row between left and right with equal gaps (visual order), then float them
  function row(parts, { left, right, G, gap }) {
    const ws = parts.map(p => bbox(p.E));
    const g = gap ?? (right - left - ws.reduce((a, [l, r]) => a + r - l, 0)) / Math.max(parts.length - 1, 1);
    let cur = gap != null && right != null ? left + (right - left - ws.reduce((a, [l, r]) => a + r - l, 0) - g * (parts.length - 1)) / 2 : left;
    parts.forEach((p, i) => { move(p.E, cur - ws[i][0], G); cur += ws[i][1] - ws[i][0] + g; shadow(p.E); });
  }
  // label stack under a part: number, title, sub lines, chip
  function label(p, LY, o = {}) {
    const [l, r] = bbox(p.E), W = +svg.getAttribute('width'), pad = 24;
    let cx = o.cx ?? (l + r) / 2;
    // keep the widest line of the stack inside the canvas
    const probe = [p.t, ...(p.s || []), p.chip || ''].map((s, i) => { const t = T(0, -999, s, i === 0 ? 'lb' : (p.chip && i === (p.s || []).length + 1) ? 'chip' : 'sb'); const w = t.getBBox().width; t.remove(); return w; });
    const half = Math.max(...probe) / 2 + 8;
    cx = Math.min(Math.max(cx, pad + half), W - pad - half);
    let y = LY;
    if (p.n) T(cx, y, p.n, 'num');
    T(cx, y + 20, p.t, 'lb');
    (p.s || []).forEach((s, i) => T(cx, y + 39 + i * 17, s, 'sb'));
    if (p.chip) {
      const t = T(cx, y + 39 + (p.s || []).length * 17 + 12, p.chip, 'chip'), bb = t.getBBox();
      el(L.text, 'rect', { x: bb.x - 7, y: bb.y - 3, width: bb.width + 14, height: bb.height + 6, rx: 4, fill: 'none', stroke: INK.lo, 'stroke-width': .8 });
    }
  }
  const head = (x, y, a, b) => { const t = T(x, y, a, 'hd', 'start'); if (b) T(x + t.getBBox().width + 14, y, b, 'hds', 'start'); };
  function legend(x, y, items, extra) {
    let lx = x;
    for (const [role, s] of items) {
      const E = element(L.text); box(E, 0, 0, 15, 10, 0, 15, 2.5, role, { steps: 2, bevel: false, foot: false }); move(E, lx, y + 2);
      const t = T(lx + 34, y, s, 'key', 'start'); lx += 34 + t.getBBox().width + 30;
    }
    for (const [cls, a, b] of extra || []) { const t = T(lx, y, a, cls, 'start'); const t2 = T(lx + t.getBBox().width + 6, y, b, 'key', 'start'); lx += t.getBBox().width + 6 + t2.getBBox().width + 28; }
  }
  return { KX, KY, pr, P, mat, INK, L, rr, circ, hull, element, prism, box, cyl, hair, screw, windowOn, bbox, move, at, edgeAt, shadow, line, T, lineStyle, row, label, head, legend };
}
