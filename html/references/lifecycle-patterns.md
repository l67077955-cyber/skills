# Finding your unknowns: HTML at each stage of a build

From the "Know your unknowns" companion section of the html-effectiveness gallery (github.com/ThariqS/html-effectiveness, `unknowns/`). The idea: an unknown is the gap between the plan and the territory, and a cheap page can expose it before, during, or after implementation. Every pattern below is a page whose interactive parts (copy chips, checkboxes, toggles) **assemble the user's reply or the next prompt for them**, so the page feeds straight back into the session.

## Before implementing (cheapest place to find unknowns)

| Pattern | Use when | What the page contains |
|---|---|---|
| **Blindspot pass** | User is about to work in unfamiliar code | Scan the real code and report their unknown unknowns as cards: what it is, why it bites, and a **copyable prompt fragment** that fixes it. End with all fragments assembled into one better implementation prompt. |
| **Teach me my unknowns** | User lacks the vocabulary for a domain (color grading, auth, etc.) | A concept explainer with a vocabulary ladder (beginner to pro terms), live demo with sliders/presets, and a way to turn what they picked into a precise prompt. |
| **Design directions** | "I have no taste / don't know what's possible" | One page, 4 *wildly* different directions of the same content (e.g. ops console, editorial, kanban, terminal). Per direction "steal / skip" chips that write the user's reply. |
| **Mock before you wire** | UI idea that's only judgeable by seeing it | Clickable throwaway mock with fake data, toggleable placements, A/B questions, and a self-filling reply template. No real code touched. |
| **Brainstorm the intervention** | Open problem (e.g. churn) | ~10 options grounded in the actual codebase, plotted from cheapest to most ambitious, with "resonates" checkboxes that build the reply. |
| **The interview** | Feature is still ambiguous | Ask one question at a time, ordered by *architectural blast radius* (answers that would change the design come first). End with a decisions table and a ready-to-paste implementation prompt. |
| **Point at a reference** | Port or reimplement existing code (other language/repo) | Before porting, show a **semantics map** proving you understood it: matched code excerpts, gotcha notes, edge-case tables. The user confirms, then you port. |
| **The tweakable plan** | Writing an implementation plan | Order by *likelihood the user will want to tweak it*, not by execution order: data model, new type interfaces, and anything user-facing first (with toggleable alternatives for flagged choices); mechanical refactoring collapsed at the bottom. |

## During implementing

**Implementation notes.** Keep a running log while you build. When an edge case forces a deviation from the plan, pick the conservative option, log it under "Deviations" (what the plan said, what the code forced, what you chose), and keep going. At the end, summarize which plan assumptions failed and what to fold into a second attempt. This is cheap and makes attempt #2 start smarter.

## After implementing (others inherit your unknowns)

- **The buy-in doc.** Package prototype, spec, and implementation notes into one shareable page. Lead with the demo (animated or interactive), then pre-answer each objection a reviewer is likely to raise with evidence, and name who must sign off on what.
- **Quiz before merge.** A merge-readiness report on the diff (context, intuition, what was done) that ends in a short quiz the user must pass. Wrong answers point back to the exact section they skimmed. Makes "I understand this change" something verified rather than assumed.

## Why they work

- The prompt that made each page is shown at the top in the gallery; short, plain-English requests were enough. Specify the *job* and the *export*, not the CSS.
- Ground every card in the real codebase (file names, PR numbers, flags); generic cards are noise.
- Prefer the user answering with a click (chip, checkbox, toggle) over typing, and prefer the page composing their reply.
