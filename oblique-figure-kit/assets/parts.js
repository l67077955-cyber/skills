// Ready-made parts for oblique figures. Load after lib.js + oblique.js.
//   const F = Fig(document.getElementById('f1')), P = Parts(F);
//   const dev = P.device(200, 128, 70, ['$ npm start'], { role: 'route' });
// Every maker returns an "element" (E) that carries its own geometry; pass E to F.row(),
// F.label(), F.edgeAt(), F.shadow() etc. Text is written with the raw strings you give,
// so bilingual sheets should wrap them in t('中文', 'English') before calling the makers.
(function () {
  window.Parts = function (F) {
    const { pr, box, cyl, hair, screw, element, INK, T } = F, Y0 = 30;

    // a device with a recessed screen on its front face; the screen lines are drawn as text
    const device = (w, h, d, lines, o = {}) => {
      const E = element();
      box(E, 0, Y0, w, d, 0, h, o.r ?? 7, o.role || 'neutral', { steps: 8, lit: o.lit });
      const s = F.windowOn(E, 11, w - 11, Y0, o.bottom ?? 12, h - 11);
      if (o.url) {
        el(E.g, 'line', { x1: s.x + 3, y1: s.y + 22, x2: s.x + s.w - 3, y2: s.y + 22, stroke: INK.faint, 'stroke-width': .6 });
        [0, 1, 2].forEach(i => el(E.g, 'circle', { cx: s.x + 10 + i * 8, cy: s.y + 11, r: 2.2, fill: 'none', stroke: INK.lo, 'stroke-width': .7 }));
        T(s.x + 36, s.y + 15, o.url, 'scr', 'start', E.g);
      }
      (lines || []).forEach((q, i) => T(s.x + 10, s.y + (o.url ? 42 : 20) + i * (o.lh || 18), q, o.cls || 'scr', 'start', E.g));
      if (o.screws !== false) { screw(E, 10, Y0 + 8, h); screw(E, w - 10, Y0 + 8, h); }
      return E;
    };

    // a file/document card standing upright
    const card = (w, h, lines, o = {}) => {
      const E = element();
      box(E, 0, Y0, w, 6, 0, h, 3, o.role || 'neutral', { steps: 3, lit: o.lit, bevel: false });
      const c = pr(w - 14, Y0, h);
      el(E.g, 'path', { d: `M${c[0]},${c[1]} l14,14`, stroke: INK.lo, 'stroke-width': .7, fill: 'none' });
      lines.forEach((q, i) => { const p = pr(10, Y0, h - 22 - i * 15); T(p[0], p[1], q, i ? 'scr' : 'face', 'start', E.g); });
      return E;
    };

    // a database drum
    const drum = (r, h, role = 'neutral', bands = 2) => {
      const E = element();
      cyl(E, r, Y0 + r, r, 0, h, role, { n: 72 });
      for (let b = 1; b <= bands; b++) {
        const zz = h * b / (bands + 1), arc = [];
        for (let i = 0; i <= 48; i++) { const a = Math.PI * i / 48; arc.push(pr(r - r * Math.cos(a), Y0 + r - r * Math.sin(a), zz)); }
        el(E.g, 'path', { d: path(arc, 0), fill: 'none', stroke: INK.faint, 'stroke-width': .6 });
      }
      return E;
    };

    // a rack of shelves, one drawer each; items = [[mono name, description]]
    const shelves = (items, RW, o = {}) => {
      const E = element(), SH = o.sh || 38, BH = o.bh || 24, D = 84, H = 8 + items.length * SH;
      const z = i => 8 + (items.length - 1 - i) * SH;
      box(E, 0, Y0 + D - 8, 7, 7, 0, H + 4, 2, 'neutral', { steps: 2, bevel: false, foot: false });
      box(E, RW - 7, Y0 + D - 8, 7, 7, 0, H + 4, 2, 'neutral', { steps: 2, bevel: false, foot: false });
      for (let i = items.length - 1; i >= 0; i--) {
        box(E, 0, Y0, RW, D, z(i) - 4, 4, 2, 'neutral', { steps: 2, bevel: false, footZ: 8 });
        box(E, 0, Y0, RW, 50, z(i), BH, 5, o.role || 'neutral', { foot: false, lit: o.lit === i });
        const p = pr(12, Y0, z(i) + BH / 2 - 3.5);
        T(p[0], p[1], items[i][0], 'face', 'start', E.g);
        if (items[i][1]) T(p[0] + (o.col || 120), p[1], items[i][1], 'sb', 'start', E.g);
      }
      box(E, -3, Y0 - 3, RW + 6, D + 6, H + 4, 5, 4, 'neutral', { foot: false });
      E.feet = E.feet.slice(-1);
      E.laneY = i => pr(0, Y0, z(i) + BH / 2)[1];   // y of shelf i, for fan-out connectors
      return E;
    };

    // a shipping parcel / package
    const parcel = (w, h, d, lines) => {
      const E = element();
      box(E, 0, Y0, w, d, 0, h, 4, 'bill', { steps: 4 });
      const a = pr(w / 2 - 9, Y0, h), b = pr(w / 2 + 9, Y0, h), a2 = pr(w / 2 - 9, Y0 + d, h), b2 = pr(w / 2 + 9, Y0 + d, h);
      el(E.g, 'polygon', { points: F.P([a, b, b2, a2]), fill: F.mat.bill.shade[2], stroke: INK.faint, 'stroke-width': .6 });
      lines.forEach((q, i) => { const p = pr(10, Y0, h - 22 - i * 15); T(p[0], p[1], q, i ? 'scr' : 'face', 'start', E.g); });
      return E;
    };

    // a thin upright panel: a middleware / gate stage, with an optional status lamp
    const plate = (role, o = {}) => {
      const E = element(), w = o.w || 34, h = o.h || 168, d = o.d || 56;
      box(E, 0, Y0, w, d, 0, h, 5, role, { steps: 5 });
      cyl(E, w / 2, Y0 + d / 2, 6, h, 3, role, { n: 32 });
      screw(E, 7, Y0 + 9, h); screw(E, w - 7, Y0 + d - 9, h);
      const f = z => pr(w / 2, Y0, z);
      if (o.lamp) {
        const c = f(o.lampZ || 118);
        el(E.g, 'circle', { cx: c[0], cy: c[1], r: 9, fill: 'none', stroke: INK.mid, 'stroke-width': .7 });
        el(E.g, 'circle', { cx: c[0], cy: c[1], r: 5, fill: 'none', stroke: INK.lo, 'stroke-width': .6 });
        el(E.g, 'circle', { cx: c[0], cy: c[1], r: 1.6, fill: INK.mid });
        E.lamp = [w / 2, Y0, o.lampZ || 118];   // 3D point; project with pr() and F.at() to place a callout
      }
      if (o.vent) for (let k = 0; k < 9; k++) hair(E, pr(6, Y0, 90 + k * 6.5), pr(k % 4 ? 15 : 22, Y0, 90 + k * 6.5), INK.mid);
      if (o.text) T(f(14)[0], f(14)[1], o.text, 'face', 'middle', E.g);
      return E;
    };

    // a stack of coins: a metered amount (quota, budget, tokens)
    const coins = (k, o = {}) => {
      const E = element();
      for (let i = 0; i < k; i++) cyl(E, 30, Y0 + 30, 30, i * 7.4, 5.8, o.role || 'bill', { n: 64, foot: i === 0 });
      return E;
    };

    // a thin vertical slice with fins: an adapter / converter stage
    const adapter = (o = {}) => {
      const E = element(), w = o.w || 30, h = o.h || 120, d = o.d || 84;
      box(E, 0, Y0, w, d, 0, h, 4, o.role || 'route');
      for (let k = 0; k < 7; k++) hair(E, pr(5, Y0, 54 + k * 9), pr(25, Y0, 54 + k * 9), INK.mid);
      screw(E, 15, Y0 + 11, h); screw(E, 15, Y0 + d - 11, h);
      return E;
    };

    // a console/terminal window, used for the client side of a request flow
    const terminal = (lines, o = {}) => {
      const E = element(), w = o.w || 214, h = o.h || 120, d = o.d || 56;
      box(E, 0, Y0, w, d, 0, h, 8, 'neutral', { steps: 8 });
      const s = F.windowOn(E, 12, w - 12, Y0, 14, h - 12);
      lines.forEach((q, i) => T(s.x + 10, s.y + 19 + i * 17.5, q, 'scr', 'start', E.g));
      screw(E, 10, Y0 + 8, h); screw(E, w - 10, Y0 + 8, h);
      return E;
    };

    // a merge manifold: a spine that gathers several lanes into one
    const manifold = (o = {}) => {
      const E = element();
      box(E, 0, Y0 + 6, 20, 44, 0, o.h || 180, 4, 'route', { steps: 4 });
      for (let i = 0; i < (o.lanes || 3); i++) {
        const c = pr(10, Y0 + 6, 40 + i * ((o.h || 180) - 60) / Math.max((o.lanes || 3) - 1, 1));
        el(E.g, 'circle', { cx: c[0], cy: c[1], r: 2.4, fill: 'none', stroke: INK.mid, 'stroke-width': .7 });
      }
      return E;
    };

    // a fan-out hub: one inlet, many radial outlets
    const hub = (o = {}) => {
      const E = element();
      box(E, 0, Y0, 60, 84, 0, 70, 7, o.role || 'route');
      cyl(E, 30, Y0 + 42, 13, 70, 7, o.role || 'route', { n: 48 });
      cyl(E, 30, Y0 + 42, 4.5, 77, 3.5, o.role || 'route', { n: 24 });
      const k = pr(30, Y0 + 42, 80.5);
      hair(E, k, [k[0] + 8, k[1] - 3.5], INK.edge, .9);
      for (let i = 0; i < 12; i++) {
        const a = Math.PI * 2 * i / 12, q = r => pr(30 + r * Math.cos(a), Y0 + 42 + r * Math.sin(a), 77);
        hair(E, q(15.5), q(i % 3 ? 17.5 : 19.5), INK.mid, .6);
      }
      if (o.text) T(pr(30, Y0, 12)[0], pr(30, Y0, 12)[1], o.text, 'face', 'middle', E.g);
      return E;
    };

    return { Y0, device, card, drum, shelves, parcel, plate, coins, adapter, terminal, manifold, hub };
  };
})();
