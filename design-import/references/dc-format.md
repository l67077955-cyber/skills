# The `.dc.html` format (claude.ai/design "Design Component")

Distilled from the runtime (`support.js`, built from `dc-runtime/src/*.ts`). Read this when you
need to understand or edit a template; the snapshot script doesn't need any of it.

## File shape

```html
<script src="./support.js"></script>          <!-- the runtime; boots itself, loads React 18 UMD from unpkg -->
<x-dc>                                         <!-- the template (hidden; rendered into #dc-root) -->
  <helmet> <link …> <style>…</style> </helmet> <!-- moved into <head> -->
  …markup with {{ bindings }}…
</x-dc>
<script type="text/x-dc" data-dc-script data-props="{…json…}">
class Component extends DCLogic { … }         <!-- must be named Component -->
</script>
```

`data-props` (HTML-escaped JSON): `{ propName: { editor, default, tsType } }` — knobs shown in the
design tool; read in logic as `this.props.propName`. Keys starting with `$` (e.g. `$preview`) are
metadata.

`<meta name="design_doc_mode" content="canvas">` inside helmet = a pan/zoom canvas of boards
(the runtime sets a beige background); the content is usually a `width:max-content` flex row.

## Bindings `{{ expr }}`

Not JavaScript. Supported: paths (`a.b`, `a[0]`, `a[key]`), literals (`true false null undefined`,
numbers, quoted strings), `!x`, and one top-level `=== !== == !=`, parentheses. No calls, no
arithmetic, no ternaries — compute those in `renderVals()`.

- In text: renders the value (`null`/booleans render nothing).
- Attribute that is exactly `{{ x }}`: passes the raw value (functions for `onclick`, objects).
- Attribute mixing text and bindings: string interpolation.
- `style="…"` strings are parsed to React style objects.

## Control flow

- `<sc-for list="{{ items }}" as="it">…</sc-for>` — repeats children; `{{ $index }}` available;
  `hint-placeholder-count` only matters while streaming.
- `<sc-if value="{{ cond }}">…</sc-if>` — truthy test; `hint-placeholder-val` only for streaming.
- `<dc-import name="Other" prop="{{ v }}">` — renders sibling `Other.dc.html` as a child component.
- `<x-import from="./widget.js" component="Name">` / `component-from-global-scope="Name"` — external
  JS/JSX component (JSX is compiled with Babel standalone from unpkg).

## Attributes

- `onclick oninput onchange onsubmit onkeydown onmouseenter …` → React handlers (`onClick`, …).
- `class` → `className`; `for` → `htmlFor`.
- `style-hover="css"`, `style-focus`, `style-active`, `style-before`/`style-after` → generated
  class with a pseudo-class rule (inserted via CSSOM; `!important` added except for ::before/after).
- `ref="{{ someRef }}"` → a `React.createRef()` from the logic class (used for measuring).
- `hint-size` — placeholder sizing while streaming; ignore.

## Logic class

```js
class Component extends DCLogic {
  state = { … };                    // this.setState(update) re-renders
  componentDidMount() / componentDidUpdate() / componentWillUnmount()
  renderVals() { return { …values the template reads… }; }   // merged over props
}
```
`React` is in scope (e.g. `React.createRef()`). Common pattern for figures: geometry computed once
in a field (`geo = this.build()`), DOM-measured overlays (`getBoundingClientRect` in a rAF after
mount / ResizeObserver / `document.fonts.ready`) stored in state.

## Rendered DOM (what a snapshot sees)

`#dc-root > .sc-host[data-sc-name]` wraps the output; every element carries `data-dc-tpl="N"`;
interpolated text is wrapped in `<span class="sc-interp">`. Runtime failure markers:
`.sc-logic-error` (exception in logic), `.sc-placeholder` (missing import), `.sc-interp.sc-missing`
/ `.sc-unresolved` (binding never resolved). The raw `<x-dc>` template stays in the DOM hidden, which
is why the console shows harmless "attribute … Expected … {{ … }}" SVG parse errors.
