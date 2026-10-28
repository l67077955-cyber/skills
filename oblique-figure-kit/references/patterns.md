# Worked patterns

Patterns that come up again and again when building these figures, and the mistakes that make a
figure look wrong.

## Sheet skeleton

```html
<div class="sheet" data-out="figure-1.png">
  <svg id="f1" width="1500" height="990"></svg>
</div>
```

- One `.sheet` per figure; the export script screenshots the wrapper, so nothing outside it lands
  in the PNG.
- The sheet width is 1500px — that is the width the exported PNG is scaled to. Design in that
  coordinate space.
- Height is yours to choose; keep it just tall enough for the labels and legend, because empty
  paper reads as an unfinished figure.

## Bilingual sheets

```js
const LANG = new URLSearchParams(location.search).get('lang') || 'zh';
const t = (zh, en) => LANG === 'en' ? en : zh;
```

Every visible string goes through `t()`. Text that is identical in both languages (`403`,
`POST /v1/chat/completions`, `PostgreSQL`) does not need `t()`. Keep the English string a little
shorter than the Chinese one — the label stacks are laid out from the Chinese version, and
English tends to run wider.

## A single row of parts

```js
const parts = [ {E: client, n:'01', t:'客户端', s:['…']}, … ];
F.row(parts, { left: 50, right: 1360, G: 330 });
```

- `G` is the ground line. `F.row` puts each part's **base** on it, so a 200-tall part reaches up
  to `G - 200`.
- `right` is the x the last part's right edge should reach; the gaps are computed for you.
- Two rows of parts (e.g. an inbound chain and an outbound chain) use two `row()` calls with
  different `G` values; the first row's parts are reversed in the source so the visual order
  matches the flow.

## Arrows between 3D parts

Never hard-code an arrow endpoint — the part geometry moves as you edit the figure.

```js
const FLOW = G + pr(0, Y0, 36)[1];          // ~48px above the ground line
const e = F.edgeAt;
F.line([[e(a.E, FLOW, 'r') + 5, FLOW], [e(b.E, FLOW, 'l') - 4, FLOW]], S.solid);
```

`edgeAt(E, y, side)` returns the silhouette x of the part at height `y`, so the arrow always
starts and ends on the visible edge.

## Fan-out to several lanes (upstream channels, replicas, targets)

```js
const lanes = [y1, y2, y3];                  // one y per target row
const bus = (leftEdge + rightEdge) / 2;      // the vertical spine
lanes.forEach((y, i) => {
  const o = i === 0 ? S.lit : S.alt;
  F.line([[axl, FLOW], [bus, FLOW], [bus, y], [e(target.E, y, 'r') + 4, y]], { ...o, r: 6 });
});
```

One lane is highlighted (`S.lit`), the rest are dashed (`S.alt`). The spine x sits between the
source and the target block.

## Callouts and error branches

```js
const c = F.at(part.E, pr(part.E.lamp[0], part.E.lamp[1], part.E.lamp[2]));
F.line([[c[0], c[1] - 3], [c[0], c[1] - 30]], S.rej);
T(c[0], c[1] - 38, '403', 'rej');
```

`F.at(E, p)` adds the part's layout offset to an already-projected point — use it whenever you
project a point that belongs to a part that `row()` has moved.

For a callout that points at something in the middle of a figure, draw the leader line first and
the text last, so the text sits on top of the line.

## Labels, headings, legend

```js
F.head(M, 42, '(a) 准入中间件', '任一步失败即拒绝');   // section heading
F.label(part, G + 52);                                // stack under a part
F.legend(M, 962, [['check','校验'], ['limit','限流']]); // colour key
```

Order matters for legibility: headings at the top of a section, label stacks under the parts,
legend at the very bottom of the sheet.

## Palette switches

- `?pal=classic` — the older warm paper palette.
- `?mono=1` — every role grey. Use it to check the figure still reads without colour; if the
  parts become indistinguishable, the figure was relying on colour alone and needs shape or
  numbering.

## Traps that keep coming back

These are the bugs that survive the first render and only show up when you look at the PNG.

- **Text stamped on a drum overflows the silhouette.** A label drawn at the cylinder's front
  tangent plane (depth `y = 30`) sits outside the visible face, so it hangs off the left edge.
  Either project the stamp further forward (depth ≈ `30 + .6r`) or leave the name in the label
  stack and keep the drum bare.
- **A dashed lane drawn over a shared bus makes the bus look dashed.** Draw the solid trunk
  first, then the dashed branches on top of it — otherwise the primary route reads as secondary.
- **Shortening a label to make it fit can corrupt a name.** "POSTGRESQL" shortened to "POSTGRES"
  is a wrong label, not a shorter one. Move the long word into a sub-line instead of mangling it.
- **A caption stack is clamped to the canvas, not to its neighbours.** Two parts close together
  with long titles overlap even though nothing leaves the sheet. Stagger the stacks (draw them at
  different `LY`) or shorten the titles.
- **The sheet must be tall enough for the lowest caption.** A stack at `G + 52` needs about
  `G + 52 + 20 + 17 * lines` of height; a staggered stack at `G + 104` needs that much more.
- **The 403 callout sits above the lamp, so the part must have headroom.** A tall part with a
  rejection branch needs `G` large enough that the branch does not run into the heading.
- **An arrow that crosses a part is not "behind" it.** The kit paints all solids before all
  lines, so a line always crosses over a part. Route around, or accept it and shorten the line.

## Checklist before you call a figure done

1. **Look at the exported PNG at full size.** The renderer is the only truth; the HTML in a
   browser may look different because of window size and font loading.
2. **Check both languages.** The English labels are usually the ones that overflow.
3. **Check the top of the sheet.** Parts are lifted by `G`; a part taller than `G` is clipped.
4. **Check label collisions.** `F.label` clamps text to the canvas, not to its neighbours — two
   parts close together with long titles will overlap. Shorten the title or widen the gap.
5. **Check that the arrows land on geometry**, not in the gap next to a part.
6. **Check the file size.** The exported PNG should land around 80–140 KB after the palette
   shrink; anything much larger usually means a photographic or gradient-heavy fill crept in.
