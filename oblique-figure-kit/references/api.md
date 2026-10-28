# Kit API reference

Everything below is live in `assets/`. Load the scripts in this order:
`lib.js` → `oblique.js` → `parts.js` → `connectors.js`.

- `lib.js` — tiny SVG helpers: `el(parent, tag, attrs, text)`, `rich(parent, x, y, str, attrs)`,
  `width(svg, str, attrs)`, `marker(svg, id, fill, L, W)`, `path(pts, r)` (orthogonal polyline with
  rounded corners). `rich` understands `<i>`, `<b>`, `<sub>`, `<sup>`, `<m>` (mono) inside a string.
- `oblique.js` — the figure kit: `Fig(svg, opts)` returns the drawing API below.
- `parts.js` — ready-made parts: `Parts(F)` returns the part makers.
- `connectors.js` — DOM-measured connector router for HTML/CSS box diagrams (`routeConnectors`).

## Coordinate system

Oblique projection, camera constants `KX = .62`, `KY = -.42`:

```
pr(x, y, z)  →  [ x + y * KX ,  -z + y * KY ]
```

- `x` — right along the front face
- `y` — into the depth (up-right on screen)
- `z` — up (screen y is `-z`)

`pr` is the only projection you need for placing text, dots, and callouts. Everything else in the
kit is already projected.

## `Fig(svg, opts)`

`opts`: `{ float = 22, roles = {}, bg }`. `float` is the shadow gap below a part; `roles` adds
semantic colours on top of the built-in ones.

Returns:

| member | what it does |
|---|---|
| `pr(x,y,z)` | project a 3D point to screen coords |
| `P(points)` | format a point array as an SVG `points` attribute |
| `mat` | per-role material colours (`mat.bill.shade[2]` etc.) |
| `INK` | ink palette: `edge`, `crease`, `faint`, `mid`, `lo`, `lit`, `red` |
| `L` | layer groups: `floor` (shadows), `solid` (parts), `line` (arrows), `text` |
| `element(parent?)` | create a part container: `{ g, hulls, feet, dx, dy }` |
| `prism(E, ring, z, h, role, o)` | extrude a 2D ring into a solid |
| `box(E, x,y,w,d, z,h, r, role, o)` | rounded box; `o`: `steps`, `bevel`, `lit`, `ghost`, `foot`, `footZ` |
| `cyl(E, cx,cy,r, z,h, role, o)` | cylinder; `o.n` = side segments (default 56) |
| `hair(E, a, b, stroke, w)` | thin line between two projected points |
| `screw(E, x,y,z)` | small screw head detail |
| `windowOn(E, x0,x1, y, z0,z1, fill)` | recessed screen on a front face; returns `{x,y,w,h}` |
| `bbox(E)` | `[left, right, top, bottom]` of the part's hulls |
| `move(E, dx, dy)` | translate a part (also used by `row`) |
| `at(E, p)` | add the part's offset to an already-projected point |
| `edgeAt(E, y, side)` | x of the part's silhouette at height `y`; `side` is `'l'` or `'r'` |
| `shadow(E, k)` | soft shadow on the floor plane (called by `row`) |
| `line(pts, o)` | polyline arrow; `o`: `stroke`, `w`, `dash`, `m` (marker id), `ms`, `r` (corner radius), `parent` |
| `T(x, y, s, cls, anchor, parent)` | text; `cls` is a CSS class (see below), `anchor` is `'start'|'middle'|'end'` |
| `lineStyle` | `solid`, `lit` (highlighted), `alt` (dashed), `back` (dashed, quieter), `rej` (red) |
| `row(parts, {left, right, G, gap})` | lay parts out on one row and drop their shadows |
| `label(p, LY, o)` | label stack under a part: `p = {n, t, s:[], chip}` |
| `head(x, y, a, b)` | section heading (bold part + quiet part) |
| `legend(x, y, items, extra)` | colour legend: `items = [[role, text]]` |

### `row()` semantics that surprise people

`row(parts, {left, right, G})` places every part's **base** (its `z = 0` origin) on the ground
line `G`, not its top. A 168-tall plate on `G = 230` therefore reaches up to `y = 62`. Choose `G`
so that `G - tallestPartHeight` still clears the heading and the top of the sheet.

### Label stack

`F.label(p, LY)` draws, under the part: the step number (`p.n`), the title (`p.t`), one or more
sub-lines (`p.s`), and an optional boxed chip (`p.chip`). The stack is centred on the part and
clamped so the widest line stays inside the canvas — but only the *text* is clamped, so keep the
title short enough that neighbouring stacks do not collide. `LY` is the y of the number line;
the title sits 20px below, sub-lines every 17px after that.

## `Parts(F)`

**Every maker returns an element (E), not a part object.** `F.label`, `F.row` and `F.shadow` want
either the element or a part object — wrap it when you want a label stack:

```js
const drum = P.drum(36, 86, 'neutral', 2);
F.row([{ E: drum }], { left: 50, right: 1400, G: 230 });
F.label({ E: drum, n: '03', t: '共享存储', s: ['PostgreSQL 与 Redis'] }, 282);
```

| maker | shape |
|---|---|
| `device(w, h, d, lines, o)` | a box with a recessed screen; `o`: `role`, `url`, `cls`, `lh`, `lit`, `r`, `bottom` |
| `card(w, h, lines, o)` | an upright document/file card |
| `drum(r, h, role, bands)` | a database drum with band lines |
| `shelves(items, RW, o)` | a rack; `items = [[name, description]]`; exposes `E.laneY(i)` for fan-out |
| `parcel(w, h, d, lines)` | a package with a tape strip |
| `plate(role, o)` | a thin upright stage panel; `o.lamp` adds a status lamp and sets `E.lamp`; `o.vent` adds fins; `o.text` |
| `coins(k, o)` | a stack of coins (a metered amount) |
| `adapter(o)` | a finned vertical slice (a converter stage) |
| `terminal(lines, o)` | a console window (the client side of a flow) |
| `manifold(o)` | a spine that gathers several lanes into one; `o.lanes` |
| `hub(o)` | a fan-out hub: one inlet, twelve radial outlets |

## `connectors.js` — DOM-measured routing

For diagrams built from HTML boxes (rather than 3D parts) the router measures the boxes in the
browser and draws the arrows itself, so arrows keep pointing at the right edge after the layout
changes.

```html
<div id="fig" style="position:relative">
  <div data-a="a">…</div>
  <div data-a="b">…</div>
</div>
<script>
routeConnectors(document.getElementById('fig'), [
  { f: 'a', t: 'b', fs: 'r', ts: 'l', r: 'vh' }
]);
</script>
```

Each connector: `{ f, fs, t, ts, ff, tf, r, k, ff, tf, mxo, bend }`

- `f` / `t` — `data-a` ids of source and target
- `fs` / `ts` — side: `'t' | 'b' | 'l' | 'r'`
- `ff` / `tf` — fraction along that side (default `.5`)
- `r` — route: `'v' | 'vh' | 'hv' | 'vhv' | 'hvh' | 'curve'`, or omitted for a straight line
- `mxo` — for `'hvh'`: how far past the rightmost endpoint the vertical leg sits
- `bend` — for `'curve'`: perpendicular control-point offset (sign = side)
- `k` — style key: `pipe` (thick light-blue duct), `thin` (hairline), `hop` (arrow over a line),
  `trace` (thin arrow over a white line)

Painting order is fixed: pipes under thins under hops under traces.

## CSS classes (`assets/fig.css`)

| class | use |
|---|---|
| `.lb` | label title (600 weight) |
| `.sb` | sub-line of a label |
| `.num` | step number, monospace, letterspaced |
| `.chip` | mono chip text |
| `.face` / `.faceb` | text on a 3D face / bold face title |
| `.scr` | monospace text on a screen |
| `.rej` | rejection text (red) |
| `.note` / `.key` | quiet annotation / legend text |
| `.hd` / `.hds` | section heading / its quiet subtitle |
| `.tag` | small monospace tag |

Fonts: `Noto Sans CJK SC` for anything with Chinese, `Liberation Mono` for code and chips.

## Roles (semantic colours)

`neutral` (body), `check` (validation), `limit` (throttling), `route` (routing), `bill` (billing /
quota), `up` (upstream), `avail`, `frozen`, `used`, `warn`.

In the default *ice* palette every body is near-white with an indigo edge and only the top cap
carries the role tint — that is what makes a figure read as one system. `?pal=classic` switches
to the older warm palette, `?mono=1` flattens every role to grey (useful for checking that the
figure still reads without colour).
