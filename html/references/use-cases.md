# Use cases and prompt patterns

Read the section that matches the job. Each lists what the page should contain and an example of the kind of request that triggers it. Adapt the specifics; the point is the shape of the page.

## Specs, planning, exploration

Expect a *web* of pages for real problems: brainstorm several options, deepen one with mockups and code, then write the implementation plan. Later sessions (implementer, verifier) read all of them.

- Options page: grid of 3-6 distinctly different approaches (vary layout, tone, density), each labeled with the tradeoff it makes.
- Plan page: answer first, contents list, data-flow diagram (SVG), mockups, important code snippets, risks, open questions.

Example requests:
- "I'm not sure what direction to take the onboarding screen. Generate 6 distinctly different approaches and lay them out in one HTML grid so I can compare them side by side. Label each with its tradeoff."
- "Write a thorough implementation plan as an HTML file with mockups, data flow, and the code snippets I'd want to review. Easy to read and digest."

## Code review and understanding

Replace the wall of diff with a page: real diff rendered with inline margin notes, findings color-coded by severity, a flowchart of the changed path, a risk map up top, low-risk files folded away. Good as the description attached to a PR you author, or for reviewing someone else's.

Example request:
- "Help me review this PR with an HTML artifact. I'm not familiar with the streaming/backpressure logic so focus there. Render the actual diff with inline margin annotations, color-code findings by severity, and add whatever else conveys the concept."

## Design and prototypes

HTML is expressive enough to sketch any UI or interaction, even when the real target is React or Swift. Include sliders/knobs for the values being tuned and a copy button for the parameters that worked.

Example request:
- "Prototype a checkout button that plays an animation on click then turns purple quickly. Give me sliders and options to try variations, plus a copy button for the parameters I like."

Also: design-system pages, component state galleries, animation playgrounds.

## Reports, research, learning

Synthesize across sources (code, git history, Slack, web) into a page built to be read once. Use SVG for diagrams, annotate 3-4 key snippets, end with a "gotchas" section. Can be a long page, an interactive explainer, or a slide deck.

Example requests:
- "I don't understand how our rate limiter works. Read the code and produce one HTML explainer: token-bucket flow diagram, the key snippets annotated, and a gotchas section."
- Weekly status report for a manager; incident report for leadership.

## Decks, diagrams, and other page types

- **Slide deck in one file**: sections as slides, left/right arrow-key navigation, no library needed. Good for a short talk or readout.
- **SVG figure sheet**: several inline SVG diagrams (for a blog post or docs) on one page, each with a copy-SVG control.
- **Annotated flowchart**: e.g. a deploy pipeline where clicking a step shows what runs, timings, and failure paths.
- **Module map**: a package drawn as boxes and arrows with the hot path highlighted and entry points listed.
- **Feature explainer**: TL;DR first, collapsible steps, tabbed config snippets, FAQ.
- **Concept explainer**: teach with a live, manipulable model (e.g. a consistent-hashing ring), a comparison table, and a hover-linked glossary.
- **Status report**: shipped vs slipped, a small chart, built to skim in 30 seconds.
- **Incident report**: minute-by-minute timeline, log excerpts, follow-up checklist.
- **PR writeup for reviewers**: motivation, before/after, file-by-file tour, and where to focus the review.
- **Component variants sheet**: every size, state, and intent of one component on a single page.
- **Living design system**: color, type scale, and spacing tokens as copyable swatches.
- **Clickable flow**: four or so linked screens to test interaction feel.

For the pre-/during-/post-implementation patterns (blindspot pass, interview, mock-before-wire, tweakable plan, implementation notes, buy-in doc, merge quiz), see `lifecycle-patterns.md`.

When unsure what a page type should look like, the reference gallery is `https://github.com/ThariqS/html-effectiveness` (Apache-2.0; files `01-` to `20-` plus `unknowns/`). Fetch one example as inspiration; don't copy its content or fictional "Acme" data into real work.

## Custom editing interfaces

When a request is awkward to express in text, build a throwaway editor for exactly this one piece of data. Not a product. It must end in an export (copy as JSON / markdown / prompt / diff).

Example requests:
- "Reprioritize these 30 tickets: draggable cards across Now / Next / Later / Cut, pre-sorted by your guess, with a 'copy as markdown' button including a one-line rationale per bucket."
- "Build a form editor for this feature-flag config: group by area, show dependencies, warn if a flag is enabled while its prerequisite is off, 'copy diff' for changed keys only."
- "Side-by-side prompt tuner: editable prompt with variable slots highlighted on the left; three sample inputs re-rendering the filled template live on the right; token counter and copy button."

Good fits: triaging/bucketing, structured config with constraints, live-preview tuning, approving/rejecting dataset rows, annotating a transcript or diff, picking values that are hard to type (colors, easing curves, crop regions, cron schedules, regexes).
