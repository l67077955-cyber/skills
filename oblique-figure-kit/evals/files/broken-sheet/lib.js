// Tiny SVG helpers shared by the style samples.
const NS = 'http://www.w3.org/2000/svg';
function el(parent, tag, attrs = {}, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text != null) e.textContent = text;
  parent.appendChild(e);
  return e;
}
// Rich text: <i>, <b>, <sub>, <sup>, <m> (mono) inside one <text>. anchor via attrs['text-anchor'].
function rich(parent, x, y, str, attrs = {}) {
  const t = el(parent, 'text', { x, y, ...attrs });
  const re = /<(\/?)(i|b|sub|sup|m)>/g;
  let last = 0, m, st = { i: 0, b: 0, sub: 0, sup: 0, m: 0 }, pendingShift = 0;
  const push = s => {
    if (!s) return;
    const a = {};
    if (st.i) a['font-style'] = 'italic';
    if (st.b) a['font-weight'] = 700;
    if (st.m) a['font-family'] = 'Liberation Mono, monospace';
    if (st.sub || st.sup) a['font-size'] = '0.72em';
    const shift = st.sub ? 4 : st.sup ? -6 : 0;
    if (shift !== pendingShift) { a.dy = shift - pendingShift; pendingShift = shift; }
    el(t, 'tspan', a, s);
  };
  while ((m = re.exec(str))) { push(str.slice(last, m.index)); st[m[2]] += m[1] ? -1 : 1; last = re.lastIndex; }
  push(str.slice(last));
  return t;
}
function width(svg, str, attrs) { const t = rich(svg, 0, 0, str, attrs); const w = t.getBBox().width; t.remove(); return w; }
function marker(svg, id, fill, L = 8, W = 3.2) {
  let defs = svg.querySelector('defs') || el(svg, 'defs');
  const m = el(defs, 'marker', { id, viewBox: `0 0 ${L} ${2 * W}`, refX: L - .5, refY: W, markerWidth: L, markerHeight: 2 * W, orient: 'auto-start-reverse', markerUnits: 'userSpaceOnUse' });
  el(m, 'path', { d: `M0,0 L${L},${W} L0,${2 * W} z`, fill });
}
// Orthogonal polyline with rounded corners.
function path(pts, r = 6) {
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [ax, ay] = pts[i - 1], [bx, by] = pts[i], [cx, cy] = pts[i + 1];
    const d1 = Math.hypot(bx - ax, by - ay), d2 = Math.hypot(cx - bx, cy - by), rr = Math.min(r, d1 / 2, d2 / 2);
    d += ` L${bx + (ax - bx) / d1 * rr},${by + (ay - by) / d1 * rr} Q${bx},${by} ${bx + (cx - bx) / d2 * rr},${by + (cy - by) / d2 * rr}`;
  }
  const l = pts[pts.length - 1];
  return d + ` L${l[0]},${l[1]}`;
}
