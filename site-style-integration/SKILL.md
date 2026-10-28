---
name: site-style-integration
description: Take the visual style of a website, screenshot, or published artifact the user likes and bring it into their code — as design tokens, a standalone demo page or artifact, or restyled components inside an existing project. Use this whenever the user says they like a site's look/design/style and wants it in their project ("I really like the style of X, can I use it", "make my page look like this site", "integrate this design into my app", "port this artifact's model page into our repo", "copy the CSS from this site"), shares screenshots of a UI they want to match, pastes a URL plus "this design", or asks how to get CSS from a site they can only open in their own Chrome — even if they never say "design tokens" or "style".
---

# Site style → code

The user has seen a design they like and wants it in their own code. The job has three parts and
the order matters: **capture** the style faithfully, **decide** with the user where it goes, then
**build and verify** it in their stack. Most failures come from skipping capture (guessing colors
from memory), copying a brand instead of a style, or declaring victory without looking at the result.

## 1. Identify the source and pick the capture route

| Source | Route |
|---|---|
| Public URL | Run `scripts/capture_style.py <url> --out <dir> --dark` (screenshots + computed-style report). Also read the screenshots yourself. |
| Screenshots only | Read them; estimate tokens and say clearly they're estimates. Ask for a URL if exact values matter. |
| Site only reachable in the user's Chrome (login, VPN, bot wall) | See `references/chrome-only.md`: Claude in Chrome if connected, otherwise have the user "Save page as → Webpage, Complete" and run the script on the saved `.html`. |
| claude.ai artifact link | `Artifact` action `read` — you get the full HTML; tokens are usually already `:root` variables. |
| claude.ai/design link or `.dc.html` | Hand off to the `design-import` skill. |
| Figma | Figma connector (needs authorization). |

`capture_style.py` reports the colors, fonts, type scale, radii, borders, shadows and gaps the page
actually renders, weighted by how much they're used, plus `:root` CSS variables, representative
elements (h1, button, card, table…), loaded web fonts, JS errors and horizontal overflow. Prefer it
over grepping minified CSS: computed styles show what's really applied, including Tailwind/utility
output. SPAs may need `--wait 6000`.

**Check which design skill fits before loading one.** `design-taste-frontend` is for landing pages,
portfolios and marketing sites; its rules (no 1px borders, no card rows, no gridlines) actively
destroy dashboards and app screens. For dashboards and data UIs, use `dataviz` for the charts and
follow the reference closely instead. If the user invokes a skill that doesn't fit, say so briefly
and explain what you're doing instead.

## 2. Write the style down as tokens

Turn the capture into a token block before writing any components — one place for the look, so the
rest of the code references names, not hex values:

```css
:root {
  /* surfaces */   --bg: …; --card: …; --card-border: …; --radius: 8px;
  /* text */       --ink: …; --ink-muted: …; --ink-faint: …;
  /* accent */     --accent: …; --down: …; --good: …;
  /* type */       --font: "Inter", system-ui, sans-serif; --text-sm: 13px; …
  /* data */       --series-1 … --series-n   (if charts)
}
```

Note beside each value whether it's exact (from computed styles) or estimated (from a screenshot).
Also capture the *patterns* that make the style recognisable, in a few bullets — e.g. "1px hairline
cards, no shadows; black pill filters; masonry 4-col grid; dashed chart gridlines; black date pill
in tooltips". Tokens alone don't reproduce a look; the patterns do.

Map tokens into whatever the target uses: CSS variables, Tailwind theme / `@theme`, shadcn's
`--background/--foreground` set, MUI theme, etc. If the project already has a token system, map
onto its names rather than adding a parallel set.

## 3. Ask where it goes (only if unclear)

If the user hasn't said, ask one question with these options:

- **Standalone demo** — a folder with `index.html / styles.css / app.js` and sample data, to see the
  style working and copy pieces from later.
- **Artifact** — the same as one self-contained page they can open and share.
- **Integrate into their project** — restyle an existing page/feature in their codebase.

Don't ask when the request already says ("integrate the model page into tokenhub" = integrate).

## 4. Build

### Borrow the style, not the brand
Rename the product, logos and brand-named series ("OpenRouter Spend" → "Platform spend"), make your
own wordmark, and label sample data as sample data. Layout, palette, type and component patterns are
fair to reproduce; names, logos, copy and imagery are not. This matters doubly for anything
published as an artifact.

### Standalone demo / artifact
- Tokens at the top of the stylesheet, then components. Realistic seeded sample data so it looks
  identical on every load.
- **No CDN runtime libraries in artifacts.** A blocked CDN (Chart.js) left every chart blank in the
  viewer while the static parts rendered. Draw charts as inline SVG with a small `drawChart` helper;
  it also makes dark-mode recoloring trivial.
- Add what the original may lack: dark mode via `prefers-color-scheme` (redraw charts on change),
  visible `:focus-visible` outlines, `prefers-reduced-motion`, and a phone layout.
- Controls that aren't wired up should look disabled (`aria-disabled`, "Not part of this demo"),
  not silently do nothing.
- When the user sends more screenshots of the same product, extend the same file (new tab/page,
  shared tokens and chart helper) rather than starting over. Back up the file before big patches.

### Integrating into an existing codebase
Read `references/codebase-integration.md` before editing. In short: read the project's
CLAUDE.md/AGENTS.md, find the existing feature and its data sources, map the design onto existing
components and real data (wire real metrics where the design shows them), keep file headers and
i18n complete in every locale, update route/search-param schemas, run typecheck/lint/tests on what
you changed, and don't let a repo-wide formatter sneak unrelated changes into the diff. Don't commit
unless asked.

## 5. Verify by looking

Render the result and read the screenshots — every time, not just at the end:

```bash
python3 scripts/capture_style.py <your page or dev-server URL> --out <dir> --widths 1440,1280,390 --dark --wait 6000
```

- Compare side by side with the reference shots; fix what visibly differs (spacing, label
  truncation, cards touching edges, tabs cut off, number formats like "13600B" vs "13.6T").
- Trust the report's **Horizontal overflow** line (scrollWidth vs clientWidth) over the picture:
  headless Chrome's CLI won't render narrower than ~485px and fakes a scrollbar at 390px.
- **JS errors** in the report usually explain blank areas. A blank page on a dev server often just
  needs a longer `--wait`.
- For interactions (sort, filter, tabs, hover tooltips, side panels), drive them with a short
  Playwright script and assert on the DOM.
- Snap Chromium can only write under `~/snap/chromium/common`; the script handles this, but remember
  it if you call chromium directly.

## 6. Report

Tell the user, briefly: where the result is (path or artifact link), which parts of the style it
reproduces, what intentionally differs (brand removed, dark mode added, features stubbed), and what
you did **not** verify (e.g. hover not tested, dark mode only screenshot-checked). Offer the next
step that fits: bring it into the project, add the next screen, or tighten something specific.
