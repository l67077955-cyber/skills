---
name: html
description: Write rich, self-contained single-file HTML instead of Markdown whenever the output is something a person has to read, compare, judge, tune, or share. Use it for specs, implementation plans, option explorations, code review or PR explainers, design prototypes with sliders/knobs, research or status/incident reports, "explain how X works" pages, slide decks, SVG diagrams, throwaway editing UIs (drag-to-triage, config editors, prompt tuners) that end in a copy/export button, and discovery pages such as blindspot passes, design-direction mocks, tweakable plans, buy-in docs, or a quiz before merging. Trigger on "make an HTML file", "HTML artifact", "html report", "don't use markdown", "做成 HTML", "用 HTML 呈現", "不要 markdown", "unreasonable effectiveness of HTML", "explain this PR visually", "compare these approaches side by side", or any plan/report/explainer likely to exceed ~100 lines or benefit from diagrams, color, tables, diffs, tabs or interaction. Skip it when the user wants Markdown/plain text or another file format, the answer is short and conversational, or the file must be hand-edited or line-reviewed in git.
---

# HTML as the output format

Markdown is where agents default, but it caps out fast: few people read past ~100 lines, diagrams degrade to ASCII, color gets faked with Unicode blocks, and a `.md` file is awkward to share. HTML carries far more per screen (tables, SVG, CSS-accurate color, annotated code, tabs, controls) and opens in any browser or as a link. Since the user increasingly steers by prompting you rather than hand-editing the file, Markdown's main advantage (easy to edit) matters less than its reading and sharing limits. A page people actually read keeps them in the loop on what you did and decided.

You do not need a ceremony for this. "Make an HTML file" is the whole technique. What matters is knowing what the page is *for*.

## 1. Decide the page's job

Before writing, name the verb the reader will perform: **compare**, **approve**, **understand**, **tune**, **triage**, or **learn**. Layout follows from it.

| Job | Shape |
|---|---|
| Compare approaches | Grid of 3-6 cards, each labeled with the tradeoff it makes; vary layout/approach/density meaningfully, not cosmetically |
| Approve a plan | Answer first, contents list, data-flow diagram, mockups, key code snippets, risks |
| Understand / review code | Real diff with inline margin notes, severity color, flow diagram of the changed path, "focus here" callouts |
| Tune a value | Sliders/toggles with live preview plus a copy button for the winning parameters |
| Triage / reorder / edit data | Purpose-built throwaway editor (drag cards, form, side-by-side) ending in an export |
| Learn / report | Narrative top to bottom, SVG diagrams, annotated snippets, a gotchas section |

More prompt patterns per use case (including decks, diagrams, reports): `references/use-cases.md`.

Pages that help the user discover what they don't know before, during, or after a build (blindspot pass, interview, mock before wiring, tweakable plan, implementation notes, buy-in doc, quiz before merge): `references/lifecycle-patterns.md`. Reach for these when the user is in unfamiliar territory, can't articulate what they want, or is about to merge something they didn't write. Their shared trick is that the page's clicks (chips, checkboxes, toggles) compose the user's reply or next prompt for them.

## 2. Ground it in real context

Claude Code's advantage over a chat UI is what it can ingest. Read the actual files, git history, diffs, logs, and any connected tools (Slack, Linear, browser) before drawing anything. Real file paths, real numbers, real code. Never invent data to fill a diagram.

## 3. Pick the HTML feature that carries each kind of information

- tables → `<table>` (sticky header, sortable if long)
- flows, architecture, timelines, workflows → inline SVG with real names from the source
- code → `<pre><code>` annotated, never screenshots
- design values → actual CSS (swatches, type specimens, live components)
- spatial data → absolutely positioned elements or `<canvas>`
- options → cards in a grid
- long documents → sticky contents list, tabs, or `<details>` for low-importance detail
- parameters → range/select/checkbox with live preview

If a sentence starts "A calls B, which then...", it wants a diagram.

## 4. Build

Start from `assets/template.html`: palette, type, and components (cards, badges, chips, buttons, diff rows, margin-note bubbles, tables, folds) are already there, responsive, with a dark mode. Inline all CSS and JS in one file so it works offline and is trivial to share. If a library is truly needed, pin an exact version from a CDN; prefer none.

Default look (change it if the user or their project has its own): ivory page `#FAF9F5`, white cards, slate text, one clay accent `#D97757`, olive for added/safe, rust for removed/danger, serif headings at weight 500, system sans body, monospace for paths/labels/code, 1.5px warm-gray borders, almost no shadows. Color should mean something (severity, diff, status); neutrals carry the rest.

If the user wants a company or project style instead, look for an existing design-system HTML or the codebase's tokens, or build one `design-system.html` (swatches, type scale, components in each state) and reuse it as the reference for later pages.

## 5. Content principles

- **Lead with the answer.** First screen states the recommendation or summary; detail follows.
- **One idea per section**, visible hierarchy, narrow measure for prose, wider room for tables and diagrams.
- **Give a map** for anything with many parts (file list, risk chips, contents), and fold low-risk detail.
- **Label tradeoffs** on every alternative.
- **Annotate real artifacts** instead of paraphrasing them.
- Mobile-friendly: single column that reflows, wide content scrolls inside its own container.

## 6. Close the loop on interactive pages

Whenever the user changes something in the page (reorders, toggles, tunes, approves), end with a **Copy as prompt / JSON / Markdown / diff** button that turns their changes back into text they can paste to you. Without it the page is a dead end; with it the page is a two-way tool. Pre-fill sensible defaults (e.g. your best-guess ordering) so the user adjusts rather than starts from zero.

## 7. Deliver

Save the file where the user will find it (or publish via the Artifact tool when it's available and the page is meant to be shared) and open it for them if they want. Reply in a sentence or two on what's in it and any assumptions; do not restate the page in chat.

For bigger problems, build a small web of linked pages (explore options → deepen the chosen one with mockups/snippets → implementation plan) in one folder. When handing off to an implementing or verifying session, pass all of them in so it has the full context, not just the final plan.

## Honest tradeoffs (mention only when relevant)

- HTML takes roughly 2-4x longer to generate and uses more tokens than Markdown; worth it when the output will be read, shared, or judged, not for a quick answer.
- HTML diffs are noisy in version control; a spec that must be reviewed line by line in git is better as Markdown.
- A page shared by link is visible to anyone with the link, so keep secrets out.

## Before delivering

- [ ] One self-contained file that works offline
- [ ] First screen states the point
- [ ] Everything real, nothing invented
- [ ] Readable at phone width and in dark mode
- [ ] Interactive? There is an export button
- [ ] Chat reply is short
