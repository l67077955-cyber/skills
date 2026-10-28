# Integrating a reference design into an existing codebase

Lessons from porting a dashboard artifact's Models page into a React/TS app (`features/pricing`).

## Before editing
- Read `CLAUDE.md`, `AGENTS.md` (also nested ones, e.g. `web/default/AGENTS.md`), README, `git status`
  and recent `git log`. Note any uncommitted work so you never touch or revert it.
- Find the existing feature the design maps to (route, feature folder, components, hooks, filter
  and sort logic, types). Grep for every consumer of things you plan to rename or remove.
- Note what data actually exists. Wire real data where the design shows it (the app already had a
  `/api/perf-metrics/summary` endpoint for latency/throughput columns). Show columns or filters only
  when the data has those fields; don't invent values.

## Mapping the design
- Map tokens onto the project's theme (e.g. shadcn CSS variables, Tailwind theme, `--chart-n`)
  instead of hard-coding the reference's hex values.
- Reuse existing UI primitives (`components/ui/*`: select, sheet, tabs, skeleton) and icon helpers.
- Keep behavior the project had (unit switches, billing modes, group filters) unless the user asks
  to drop it; place it where the design's toolbar would.
- Put new pure logic (sort keys, filters, formatters) in `lib/` so it's testable; components stay thin.
- Sorting: missing values stay at the bottom in both directions.
- Update anything keyed on old values: route search-param schemas (zod enums like
  `view: 'card' | 'table'` → `'list' | 'table'`), sibling routes that share the schema, constants,
  empty states and loading skeletons for the new layouts.
- Narrow screens: a side filter rail becomes a sheet opened by a Filter button.

## Project hygiene
- Keep required file headers (license/protected headers) on new files. Copy them from an existing file.
- i18n: add every new user-visible string to **all** locale files, preserving the files' existing
  JSON formatting (check `json.dumps(..., indent=2) + '\n' == raw` before rewriting).
- Find the project's own tools (they may live in a parent `node_modules/.bin`; Bun may not be on PATH).
  Run typecheck, then lint and format **only the files you changed**.
- **Watch repo-wide formatters.** A format script ignored its file list and reformatted the whole
  frontend. Afterwards, run `git status`, and for each unrelated file confirm the diff is
  formatting-only (format the HEAD version separately and compare) before `git checkout --` it.
  Pre-existing lint errors in untouched files aren't yours to fix; mention them.
- Add unit tests for new sort/filter logic, mirroring an existing test file's style.
- Don't commit unless asked.

## Verify in the running app
- Look for a running backend (`curl localhost:<port>/api/...`, `docker ps`) and point the dev
  server's proxy at it (env var such as `VITE_REACT_APP_SERVER_URL`).
- Start the dev server in the background on a free port, capture table/list/dark/mobile with
  `capture_style.py --wait 6000`, then script interactions (header sort order, filters, empty state,
  category tab counts) with Playwright and assert on rows.
- Stop the dev server when done.
- Report: files changed, what matches the design, what changed in behavior, checks run and their
  results, and anything not verified.
