# Getting the style from a site only the user's Chrome can open

Use when fetching the page fails (login wall, VPN/intranet, bot protection, geo-block) or the user
says "it only opens in my Chrome".

## Option 1: Claude in Chrome (if connected)
If `mcp__claude-in-chrome__*` tools are available, load the `chrome-browser` skill and open the page
in a new tab. Read computed styles with a small script (body, h1–h3, button, card, table: font,
size, weight, color, background, radius, shadow) and take screenshots at desktop and phone width.
If the tools aren't available, tell the user it needs the extension plus a host that connects it
(e.g. the Claude desktop app), and offer Option 2 meanwhile.

## Option 2: The user exports it (no setup)
Give these steps, most useful first:

1. **Save the whole page.** Ctrl+S / Cmd+S → "Webpage, Complete". Produces `page.html` and a
   `page_files/` folder with CSS, fonts, images. Then run
   `scripts/capture_style.py /path/to/page.html --out <dir>`. Saved pages lose some JS-rendered
   content, but CSS and fonts survive, so tokens are reliable.
2. **CSS Overview.** F12 → ⋮ → More tools → CSS Overview → Capture overview. Lists every color,
   font, size, shadow and radius. A screenshot of this panel is a good token source.
3. **Raw CSS files.** DevTools → Network → filter CSS → reload → each file → Response → save.
4. **One element.** Right-click → Inspect → Computed panel, for a specific button or card.
5. **Screenshots** of the screens they like, at full width, plus one at phone width if possible.

Screenshots alone are fine for the overall feel; say values are estimated.
