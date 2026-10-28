---
name: paper-figure-redraw
description: Redraw or create research-paper figures (motivation figures, method-overview diagrams, small bar/line chart panels, attention/heatmap glyphs, highlighted-token text examples) as crisp vector HTML/SVG in the "FlashTrace" academic style — indigo/sage/sky palette, IBM Plex Sans labels, STIX Two Text math and captions, DOM-measured arrow connectors that re-route when text changes. Use when the user shares a paper figure (screenshot/PNG/PDF page) to redraw, asks for a camera-ready / publication-quality / arXiv / NeurIPS-style figure, a method pipeline diagram, a teaser figure, or mentions FlashTrace figures.
---

# Paper Figure Redraw (FlashTrace style)

Origin: claude.ai/design project "FlashTrace Figures" — a vector redraw of Fig. 1 (motivation)
and Fig. 2 (method overview) from *Towards Long-Horizon Interpretability: Efficient and Faithful
Multi-Token Attribution for Reasoning LLMs*. `examples/flashtrace-figures.dc.html` is the full
original source (claude.ai/design `.dc.html` format: `<sc-for>`/`<sc-if>` templating + a
`DCLogic` class; read it for exact geometry, not to run it locally).

## Workflow

1. **Study the reference.** If the user gave an image, Read it. Inventory: panels, boxes,
   arrows (and their kind), text, math, chart data. Keep the original **structure and reading
   order**; change only the visual system.
2. **Separate data from placeholders.** Values you estimate from a raster (bar heights, line
   points, caption text cut off) are placeholders — list them for the user at the end and keep
   them in one JS data block so they are easy to replace with the paper's numbers.
3. **Build from `assets/template.html`** (CSS tokens + classes) and `assets/connectors.js`.
   Copy both next to the output. One `.sheet` per figure, laid out on the beige `.canvas`
   with a dark tag chip above each (`1a`, `1b`, …). Single-column figures ≈ 760px wide,
   full-width ≈ 1440px.
4. **HTML for layout, SVG for marks.** Boxes, equations and text examples are HTML flex/grid
   (so text reflows); charts, cubes, heatmaps, bars are inline SVG with computed geometry.
   Arrows between HTML boxes go in one absolutely-positioned overlay SVG, routed by
   `routeConnectors(root, CONN)` from elements tagged `data-a="id"` — never hand-place
   arrow coordinates over HTML.
5. **Render & check.** Screenshot with Playwright (Chromium preinstalled; launch with
   `executablePath: '/root/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome'` if needed), wait for `document.fonts.ready`
   + ~2s, view the PNG next to the reference, fix overlaps/clipping. Iterate until clean.
6. Deliver the HTML (and PNG/PDF export if asked: `page.pdf` or element screenshot at
   `deviceScaleFactor: 3`). For sharing, publish it as an Artifact.

## Design system

**Color roles** (semantic — keep roles consistent across all figures of a paper):

| Role | Fill | Stroke / ink |
|---|---|---|
| Method / high-score / "ours" | indigo `#555ad0` | `#33379a`, text on it white; deep ink `#2d3186` for value labels |
| Indigo ramp (weights, heatmaps) | `#e9ebfb #e4e7fa #c9cdf3 #b9bef2 #8d92e3 #7b80dd #555ad0` | heatmap lerp `rgb(241,242,251)→rgb(58,63,174)` |
| Attribution target / output span | sage `#dcefe6` | `#5e9e85`, text `#173f30` |
| Baseline / naive method | sky `#4a8cc4` (arcs `#5b9bcf` @ .55) | — |
| Neutral / "other" share | `#d7dae3` | — |
| Ink | `#1b2130` | secondary `#3a4152`, tertiary `#5b6275` |
| Rules / borders | `#e3e6ee` (gridlines, dividers) | `#c6cddc` (panel borders), dashed column divider `#b7bdcc` 1.5px |
| Panels | `#f6f7fa`, `#fafbfd`, `#eef1f8` | radius 8 (group) / 6 (sub-block) / 4–5 (leaf box) |
| Canvas | `#e7e5df` beige behind white sheets with soft shadow | |

Accents: section subtitle in `#3a3fae`; callout-card headers step through the indigo ramp
(`#e4e7fa` → `#b9bef2` → `#555ad0` with white text) to show progression across stages.

**Type**
- IBM Plex Sans for all labels. Stage titles 19px/700; panel titles 13px/600; box labels
  11.5px/500; legends 9.5–12px; chart ticks 9.5px `#5b6275`; axis titles 10px/500.
- STIX Two Text for math, the in-figure example text, and captions (15px single-column,
  19px full-width, line-height 1.4, `text-wrap:pretty`). Caption starts `<i>Figure N.</i>`;
  use `<b>Top:</b>/<b>Bottom:</b>` and (a)/(b)/(c) to reference panels.
- Method name in `font-variant:small-caps`.
- Math: italic variables, `<sub>`/`<sup>` at .7em; stacked super+sub via `.stk`
  (`<i>F</i><span class="stk"><i>h</i><span><i>i</i>→<i>S</i></span></span>`).
  Equations sit in white boxes with 1px ink border, radius 4.

**Mini charts** (panel size ≈ 226×168 SVG): plot area x 48→214, y 16→132; solid 1px ink
axes on left+bottom only; dashed `3 3` gridlines in `#e3e6ee`; 2–4 ticks; bars 40px wide,
no stroke; direct value labels above bars (600 11px `#2d3186`) instead of a y-readout;
inline legend (8px squares) in the panel title row; line charts 2px strokes with hollow
r=2.8 markers, series labelled at line ends in the series color — no boxed legends.
Panel titles "(a) Short noun phrase".

**Diagram glyphs**
- Token chips: `.tok.hi` (indigo) / `.tok.tgt` (sage) with a 1.5px offset bottom shadow
  in the stroke color — gives a pressed-key look. Plain input chips: `#f5f7fd` fill,
  `#8d9fd6` border.
- Vectors/matrices: 13–14px cells on the heatmap ramp, white 1px gaps for matrices, ink
  `#2d3186` 0.8px outline for vectors; matrices bracketed by left/right 1.5px borders with
  radius 6. Causal attention = lower-triangular, masked cells `#f4f5f9`.
- Isometric cube rows for token sequences (S=8.5, step DX 19 / DY 8.4, three face shades
  per group) with group labels rotated along the row; see `build()` in the example.
- "Paper sheet" cards for worked examples: `transform:rotate(3deg) skewX(-13deg)`,
  gradient `#fff→#edf0fa`, border `#b6c0da`, shadow `0 18px 26px -16px rgba(28,36,80,.35)`,
  `[Input]/[Reason]/[Output]` bold-italic row labels in a 68px grid column.
- Callout cards with a rotated-square pointer on the left edge and a tinted header bar.
- Underbrace-style group markers: 5px-tall box with no top border, radius `0 0 4px 4px`.
- Σ / ⊕ nodes: 20–28px white boxes/circles with 1.5px border, `z-index:4` above wires.

**Connector kinds** (`assets/connectors.js`, styles in `STYLES`):
- `pipe` — main data flow: 5.5px `#94a4d8` with a 1.6px `#eef1fb` core (tube look),
  rounded orthogonal corners r=10, head `#7e8fcc`.
- `thin` — derivation / "feeds formula": 1.2px ink, r=5.
- `hop` — step between stages: 2.6px `#3f4a72` over a white halo.
- `trace` — curved quadratic attribution arrows inside text: 1.6px ink over white halo,
  `bend` sets curvature.
Routes: `v vh hv vhv hvh curve`; pick sides with `fs/ts` (`t b l r`) and fractions `ff/tf`.
Paint order pipes → thins → hops → traces.

## Rules of thumb
- Every color encodes a role; never introduce a new hue for decoration. Max 3 hues + ramp.
- Prefer direct labels over legends; prefer one-line labels (`white-space:nowrap`).
- No drop shadows on marks; shadows only on sheets, paper cards and callouts.
- Keep stroke weights to the set {0.8, 1, 1.2, 1.5, 2, 2.6, 5.5}.
- Figures must stay correct if text changes — that is why connectors are measured.
- The live design may be updated by the user; if they say it changed, re-pull
  `FlashTrace Figures.dc.html` from project `98f7e9be-dcfd-4ab5-a3a7-1648c094ed08`.
