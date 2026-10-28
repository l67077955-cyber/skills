#!/usr/bin/env python3
"""Compile a claude.ai/design `.dc.html` into a static, standalone HTML page.

Renders the design with its real runtime (support.js + React from unpkg) in headless Chromium,
waits until the DOM stops changing, then serializes the rendered page with the runtime stripped.
It then re-opens the output from disk and pixel-diffs it against the live render.

Usage:
  python3 snapshot_dc.py "<dir>/Name.dc.html" --out <dir>/index.html [--png shot.png]
         [--viewport 1440x900] [--props '{"showCaptions": false}'] [--settle-ms 1500] [--timeout-ms 20000]

The .dc.html must sit next to support.js (and any .dc.html / assets it imports). Prints a JSON
report on stdout; exit code 0 = written and verified, 2 = written but needs attention, 1 = failed.
"""
import argparse
import functools
import http.server
import json
import pathlib
import re
import sys
import threading
import urllib.parse

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("entry")
ap.add_argument("--out", required=True)
ap.add_argument("--png", help="also save a full-page PNG of the static output")
ap.add_argument("--viewport", default="1600x1000")
ap.add_argument("--props", help="JSON object of prop overrides (applied as the design's defaults)")
ap.add_argument("--settle-ms", type=int, default=1500, help="DOM must be unchanged this long")
ap.add_argument("--timeout-ms", type=int, default=20000)
args = ap.parse_args()

entry = pathlib.Path(args.entry).resolve()
out = pathlib.Path(args.out).resolve()
vw, vh = (int(x) for x in args.viewport.lower().split("x"))
src = entry.read_text(encoding="utf-8")
report = {"entry": str(entry), "out": str(out), "warnings": [], "notes": []}


def warn(msg):
    report["warnings"].append(msg)


# ---- static analysis of the source: what a snapshot cannot preserve ----
tpl = src[src.find("<x-dc"): src.rfind("</x-dc>")] if "<x-dc" in src else ""
logic = re.search(r"<script[^>]*data-dc-script[^>]*>([\s\S]*?)</script>", src)
logic = logic.group(1) if logic else ""
handlers = sorted(set(re.findall(r"\s(on[a-z]+)=\"\{\{", tpl)))
controls = sorted(set(re.findall(r"<(input|select|textarea)\b", tpl)))
report["interactive"] = bool(handlers or controls)
report["handlers"] = handlers + [f"<{c}>" for c in controls]
report["animated"] = bool(re.search(r"setInterval|requestAnimationFrame\(\s*(?:this\.)?(?:tick|loop|step|animate)", logic))
report["measured_layout"] = bool(re.search(r"getBoundingClientRect|ResizeObserver|offsetWidth", logic))
report["imports"] = sorted(set(re.findall(r"<(?:dc-import|x-import)\b[^>]*?(?:name|component|from|src)=\"([^\"]+)\"", tpl)))
if not tpl:
    print(json.dumps({**report, "error": "no <x-dc> block: not a design component"}, indent=2))
    sys.exit(1)
if report["interactive"]:
    warn("design is interactive (" + ", ".join(report["handlers"]) + "): the snapshot freezes its initial state "
         "and event handlers do nothing. Decide with the user: port the behaviour to vanilla JS, or ship it live.")
if report["animated"]:
    warn("logic runs a timer/animation loop: the snapshot captures one frame")
if report["measured_layout"]:
    report["notes"].append("logic measures the DOM (e.g. connectors): positions are baked at snapshot time; "
                           "re-run this script after any text/font change instead of hand-editing coordinates")
if args.props:
    # bake overrides into data-props defaults in a temp copy next to the original
    props = json.loads(args.props)
    m = re.search(r'data-props="([^"]*)"', src)
    meta = json.loads(m.group(1).replace("&quot;", '"')) if m else {}
    for k, v in props.items():
        meta.setdefault(k, {})["default"] = v
    enc = json.dumps(meta).replace('"', "&quot;")
    patched = src.replace(m.group(0), f'data-props="{enc}"') if m else src.replace(
        "data-dc-script", f'data-dc-script data-props="{enc}"', 1)
    tmp = entry.with_name(".snapshot-props-" + entry.name)
    tmp.write_text(patched, encoding="utf-8")
    page_file = tmp
else:
    page_file = entry

# ---- serve the folder (runtime fetches sibling files; file:// can't) ----
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


handler = functools.partial(Quiet, directory=str(entry.parent))
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/" + urllib.parse.quote(page_file.name)

SERIALIZE = r"""() => {
  // CSSOM-only rules (style-hover pseudo-classes use insertRule) -> text, so they survive outerHTML
  for (const s of document.querySelectorAll('style')) {
    try { const rules = [...s.sheet.cssRules].map(r => r.cssText).join('\n');
      if (rules && !s.textContent.trim()) s.textContent = rules; } catch (e) {}
  }
  const doc = document.documentElement.cloneNode(true);
  const kill = sel => doc.querySelectorAll(sel).forEach(e => e.remove());
  kill('script');                       // runtime, React UMD, logic class, and any template scripts
  kill('x-dc'); kill('template#__bundler_thumbnail'); kill('link[rel=modulepreload]');
  doc.querySelectorAll('style').forEach(s => {
    const t = s.textContent;
    if (t.includes('x-dc{display:none') || t.includes('.sc-placeholder{')) s.remove();
  });
  doc.querySelectorAll('[data-dc-tpl],[data-sc-name],[data-dc-canvas],[data-omelette-chrome]').forEach(e => {
    e.removeAttribute('data-dc-tpl'); e.removeAttribute('data-sc-name'); e.removeAttribute('data-dc-canvas');
  });
  doc.querySelectorAll('span.sc-interp').forEach(s => s.replaceWith(...s.childNodes));
  doc.querySelectorAll('meta[name=design_doc_mode]').forEach(e => e.remove());
  doc.classList.remove(...[...doc.classList].filter(c => c.startsWith('sc-')));
  if (!doc.className) doc.removeAttribute('class');
  return '<!DOCTYPE html>\n' + doc.outerHTML;
}"""

STABLE = """async ([settle, timeout]) => {
  const t0 = performance.now(); let last = '', since = performance.now();
  if (document.fonts) await document.fonts.ready;
  while (performance.now() - t0 < timeout) {
    const root = document.getElementById('dc-root');
    const cur = root ? root.innerHTML : '';
    if (cur && cur === last) { if (performance.now() - since >= settle) return true; }
    else { last = cur; since = performance.now(); }
    await new Promise(r => setTimeout(r, 150));
  }
  return false;
}"""

PAGE_ERR_IGNORE = re.compile(r"attribute .*: Expected .*\{\{|Expected moveto path command.*\{\{")
code = 0
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": vw, "height": vh})
        pg = ctx.new_page()
        console, failed = [], []
        pg.on("console", lambda m: console.append((m.type, m.text)))
        pg.on("pageerror", lambda e: console.append(("pageerror", str(e))))
        pg.on("requestfailed", lambda r: failed.append(r.url))
        pg.goto(url, wait_until="networkidle", timeout=args.timeout_ms)
        stable = pg.evaluate(STABLE, [args.settle_ms, args.timeout_ms])
        if not stable:
            warn("DOM never settled within timeout (animation? streaming?); snapshot taken anyway")
        state = pg.evaluate("""() => ({
          rendered: !!document.querySelector('#dc-root > .sc-host'),
          logicErrors: [...document.querySelectorAll('.sc-logic-error')].map(e => e.textContent.trim()),
          placeholders: document.querySelectorAll('.sc-placeholder').length,
          missing: [...document.querySelectorAll('.sc-interp.sc-missing,.sc-interp.sc-unresolved')].map(e => e.textContent),
          size: [document.documentElement.scrollWidth, document.documentElement.scrollHeight] })""")
        if not state["rendered"]:
            raise RuntimeError("runtime did not render (no #dc-root > .sc-host). Is support.js next to the file? "
                               "Console: " + json.dumps(console[-8:]))
        for e in state["logicErrors"]:
            warn("logic error shown by runtime: " + e)
        if state["placeholders"]:
            warn(f"{state['placeholders']} unresolved component placeholder(s): a dc-import/x-import file is missing")
        for m in state["missing"]:
            warn("unresolved binding: " + m)
        for t, txt in console:
            if t in ("error", "pageerror") and not PAGE_ERR_IGNORE.search(txt):
                warn(f"{t}: {txt[:300]}")
            elif t == "warning" and "[dc-runtime]" in txt:
                warn(txt[:300])
        for f in failed:
            warn("request failed: " + f)
        full = {"width": max(vw, state["size"][0]), "height": state["size"][1]}
        live_png = pg.screenshot(full_page=True)
        html = pg.evaluate(SERIALIZE)
        html = html.replace("<head>", "<head>\n<!-- Static snapshot of " + entry.name +
                            " (claude.ai/design), generated by design-import/snapshot_dc.py. Edit the .dc.html and re-run; "
                            "do not hand-edit generated coordinates. -->", 1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

        # ---- verify: the static file, opened from disk, looks like the live render ----
        pg2 = ctx.new_page()
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        pg2.goto(out.as_uri(), wait_until="networkidle", timeout=args.timeout_ms)
        pg2.evaluate("document.fonts && document.fonts.ready")
        pg2.wait_for_timeout(500)
        static_png = pg2.screenshot(full_page=True)
        if args.png:
            pathlib.Path(args.png).write_bytes(static_png)
        from io import BytesIO
        from PIL import Image, ImageChops
        a, c = Image.open(BytesIO(live_png)).convert("RGB"), Image.open(BytesIO(static_png)).convert("RGB")
        if a.size != c.size:
            warn(f"static page size {c.size} differs from live render {a.size}")
            c = c.resize(a.size)
        diff = ImageChops.difference(a, c).convert("L").point(lambda v: 255 if v > 24 else 0)
        changed = diff.histogram()[255] / (a.size[0] * a.size[1])
        report["pixel_diff_pct"] = round(changed * 100, 3)
        if changed > 0.005:
            warn(f"static output differs from live render on {changed:.2%} of pixels; inspect --png")
        for e in errs2:
            warn("static page error: " + e)
        report["bytes"] = len(html.encode())
        report["page_size"] = state["size"]
        b.close()
except Exception as e:  # noqa: BLE001
    report["error"] = str(e)
    code = 1
finally:
    srv.shutdown()
    if page_file != entry:
        page_file.unlink(missing_ok=True)

if code == 0 and report["warnings"]:
    code = 2
report["ok"] = code == 0
print(json.dumps(report, indent=2))
sys.exit(code)
