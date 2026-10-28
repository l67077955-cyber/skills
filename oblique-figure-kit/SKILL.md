---
name: oblique-figure-kit
description: >-
  Draw and edit isometric/oblique technical figures — architecture diagrams, request-flow chains,
  deployment flows, rack/queue/pipeline illustrations — as HTML+SVG and export them to PNG. Use this
  whenever the user wants a diagram, figure, illustration, "technical drawing", "isometric picture",
  architecture picture, or wants an existing figure redrawn, fixed, extended, or re-styled, even if
  they never say "oblique", "SVG", or "isometric". Also use it when the user asks to export a diagram
  to PNG, or asks for a bilingual (zh/en) figure sheet. Includes a ready-made kit — solid 3D parts,
  shadows, label stacks, legends, measured arrows, and a Playwright exporter.
metadata:
  opencode/autoinvoke: true
---

# Oblique Figure Kit

This skill bundles a small, opinionated drawing kit for **oblique (isometric-style) technical
figures**: the kind of diagram that shows a system as a set of solid objects on a table, with
labelled parts and measured arrows, rather than as boxes-and-lines. It was extracted from a
production README, so every convention in it has been looked at at full size and shipped.

The kit is deliberately not a generic drawing library. The point of the oblique style is that the
whole sheet reads as one physical object: one light source, one ink colour, one set of semantic
colours, one type scale. Everything below exists to protect that.

## When to use this

- "Draw an architecture diagram of our request flow"
- "Add a new figure to the README" / "redraw figure 2"
- "Make an isometric illustration of the deployment steps"
- "This diagram needs a retry branch and a red error path"
- "Export the figure sheet to PNG"

If the user wants a *flowchart* of pure boxes, the `connectors.js` router in this kit still
applies (it is a standalone DOM-measured router); if they want a *chart*, use a chart tool
instead — the oblique style is for physical-looking systems.

## Files

```
assets/fig.css          type scale, palette, sheet layout
assets/lib.js           SVG helpers: el(), rich() (<i>/<b>/<sub>/<m>), marker(), path()
assets/oblique.js       Fig(): the drawing API (parts, shadows, arrows, labels, legend)
assets/parts.js         Parts(): ready-made parts (device, drum, shelves, plate, coins, …)
assets/connectors.js    DOM-measured arrow router for HTML-box diagrams
assets/template.html    a working starter sheet to copy
scripts/render.py       export a sheet HTML to PNG (Playwright)
scripts/optimize_png.py shrink exported PNGs to a light palette PNG
references/api.md       full API reference — read when you need a function signature
references/patterns.md  worked recipes, layout maths, and the pre-flight checklist
```

## Workflow

### 1. Copy the kit next to the figure you are making

```bash
cp <skill>/assets/{fig.css,lib.js,oblique.js,parts.js,connectors.js} <target-dir>/
cp <skill>/assets/template.html <target-dir>/figures.html   # then edit
```

Copying rather than referencing keeps the figure self-contained: the HTML renders correctly on a
machine that has never heard of this skill, which matters for docs that get committed.

### 2. Decide the story before the geometry

Write down the parts, their order, and the one thing the reader must understand. A figure with
eleven parts and no hierarchy is worse than a figure with five parts and a clear left-to-right
reading. Ask the user if the subject is unclear — a redrawn figure that answers the wrong
question is expensive to throw away.

### 3. Build the sheet

Start from `template.html`. The essential shape of a sheet:

```js
const F = Fig(document.getElementById('f1')), P = Parts(F);
const parts = [ {E: part, n:'01', t:'标题', s:['副标题']} ];
F.row(parts, { left: 50, right: 1360, G: 330 });   // G = ground line
```

Three rules carry most of the quality:

- **`G` is the ground line, not the top.** `row()` puts each part's *base* on `G`, so a 200-tall
  part reaches up to `G - 200`. If the sheet clips at the top, raise `G` — and remember the
  heading sits at `y ≈ 42`.
- **Measure every arrow.** `F.edgeAt(E, y, 'r')` gives the silhouette x of a part at height `y`.
  Hard-coded endpoints drift the moment a part changes size.
- **Label stacks hang under the ground line** (`F.label(part, G + 52)`), titles are short, and
  the legend goes at the bottom of the sheet.
- **The `Parts()` makers return an element, not a part object.** `F.label` and `F.row` want
  `{ E, n, t, s, chip }` when you want a numbered caption — see `references/api.md`.

Everything else — palette, roles, fan-out spines, callouts, bilingual strings — is in
`references/patterns.md`, and every function signature is in `references/api.md`. Read
`references/api.md` when you need a parameter you do not remember; do not guess signatures.

### 4. Bilingual sheets

If the docs are bilingual, every visible string goes through `t('中文', 'English')` and the sheet
is rendered twice with `?lang=zh` and `?lang=en`. Keep the English slightly shorter than the
Chinese — English labels are what overflow.

### 5. Export and look at the result

```bash
python3 <skill>/scripts/render.py figures.html                    # sheet's default language
python3 <skill>/scripts/render.py figures.html --langs zh,en      # one PNG per language
```

Needs `playwright` + `chromium` + `pillow` (`pip install playwright pillow && playwright install
chromium`). The exporter screenshots each `.sheet`, hides captions, waits for fonts and the
connector router to settle, and shrinks the PNG to a 256-colour palette image so docs stay light.
With `--langs zh,en` the language lands in the file name (`figure-1.zh.png`, `figure-1.en.png`);
with one language the name is the sheet's `data-out` value unchanged.

**Always look at the exported PNG before you call the figure done.** The PNG is what readers see;
the HTML in your browser is not. Walk the checklist in `references/patterns.md`: clipped tops,
colliding label stacks, arrows that land in the gap next to a part, English overflow, and file
size. That file also lists the traps that keep coming back — text stamped on a cylinder that
overflows its face, a dashed lane drawn over the solid bus, a label shortened into a wrong name.

## Editing an existing figure

The usual requests are "add a part", "fix the overlap", "make the error path red", "translate it
to English". All of them are edits to the same HTML:

1. Open the sheet HTML and find the part maker you want to change — parts are small local
   functions, so a single maker usually serves every instance in the figure.
2. Change the maker, not the call site, when the change should apply to every instance.
3. Re-export and look at the PNG. Geometry helpers (`row`, `edgeAt`, `label`) re-measure
   themselves, so most edits need no manual coordinate fixing — but the *sheet height* and the
   legend position do, because those are literal numbers.

If the figure uses `connectors.js` (HTML-box diagrams), the router re-routes itself on resize and
on font load, so moving boxes usually needs no connector edits either.

## Conventions worth protecting

- **One hue system.** The default *ice* palette is near-white bodies with indigo edges; role
  colour only tints the top cap. Do not introduce a second accent hue. `?pal=classic` is the
  older warm palette, `?mono=1` flattens everything to grey — use mono to check that a figure
  still reads without colour.
- **Semantic roles, not decorative colours.** `check` = validation, `limit` = throttling,
  `route` = routing, `bill` = money/quota, `up` = upstream, `neutral` = everything else.
  A reader should be able to guess a part's role from its colour alone.
- **The type scale is fixed** (`fig.css`): `.lb` label title, `.sb` sub-line, `.num` step number,
  `.chip` chip, `.scr` screen text, `.rej` rejection, `.hd`/`.hds` heading, `.key` legend.
- **Numbers carry the order.** Label parts `01`, `02`, `03` so the reading order survives a
  reader who only looks at the labels.
- **Light comes from the upper left.** Shadows fall down-right; keep new parts consistent with
  that or the sheet stops looking like one photograph.
