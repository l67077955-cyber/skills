#!/usr/bin/env python3
"""Capture a page's visual style: screenshots plus a token report built from computed styles.

Works on a live URL, a local .html file (e.g. a "Save page as, complete" export), or a dev server.
Run it on the reference site to extract the style, and again on your own page to verify it.

    python3 capture_style.py https://example.com --out ./ref
    python3 capture_style.py ./saved/page.html --out ./ref --widths 1440,390 --dark
    python3 capture_style.py http://localhost:5173/pricing --out ./mine --wait 6000

Outputs in --out:
    shot-<width>[-dark].png   full-page screenshots (height capped by --max-height)
    style-report.json         raw counts and samples
    style-report.md           readable summary: palette, type scale, radii, shadows, CSS vars, fonts,
                              JS errors and horizontal-overflow offenders per width

Needs Python Playwright (`pip install playwright && playwright install chromium`). Without it, falls
back to the chromium CLI for screenshots and a regex scan of the linked CSS (less accurate).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from collections import Counter
from pathlib import Path

COLLECT_JS = r"""
() => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none';
  };
  const els = [...document.querySelectorAll('body *')].filter(vis).slice(0, 4000);
  const count = {color: {}, background: {}, border: {}, font: {}, size: {}, weight: {}, radius: {}, shadow: {}, gap: {}, lh: {}};
  const bump = (k, v, w = 1) => { if (v) count[k][v] = (count[k][v] || 0) + w; };
  const hasText = (el) => [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
  for (const el of els) {
    const cs = getComputedStyle(el);
    const area = Math.min(el.getBoundingClientRect().width * el.getBoundingClientRect().height, 2e5);
    if (hasText(el)) {
      bump('color', cs.color);
      bump('font', cs.fontFamily.split(',')[0].replace(/["']/g, '').trim());
      bump('size', cs.fontSize);
      bump('weight', cs.fontWeight);
      bump('lh', cs.lineHeight);
    }
    if (cs.backgroundColor !== 'rgba(0, 0, 0, 0)') bump('background', cs.backgroundColor, Math.ceil(area / 1000));
    if (parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none') bump('border', `${cs.borderTopWidth} ${cs.borderTopStyle} ${cs.borderTopColor}`);
    if (cs.borderRadius !== '0px') bump('radius', cs.borderRadius);
    if (cs.boxShadow !== 'none') bump('shadow', cs.boxShadow);
    if (cs.gap && cs.gap !== 'normal') bump('gap', cs.gap);
  }
  // CSS custom properties declared on :root / html / body
  const vars = {};
  const rootCs = getComputedStyle(document.documentElement);
  const scan = (rules) => {
    for (const r of rules) {
      try {
        if (r.cssRules) scan(r.cssRules);
        if (r.style && /^(:root|html|body|\.dark|\[data-theme)/.test(r.selectorText || '')) {
          for (const p of r.style) if (p.startsWith('--')) vars[p] = rootCs.getPropertyValue(p).trim() || r.style.getPropertyValue(p).trim();
        }
      } catch (e) {}
    }
  };
  for (const s of document.styleSheets) { try { scan(s.cssRules); } catch (e) {} }
  // Representative elements
  const pick = (sel) => { const e = [...document.querySelectorAll(sel)].find(vis); return e || null; };
  const desc = (e) => {
    if (!e) return null;
    const cs = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    return {tag: e.tagName.toLowerCase(), cls: (e.className && e.className.baseVal === undefined ? e.className : '').toString().slice(0, 120),
      text: (e.innerText || '').trim().slice(0, 60), w: Math.round(r.width), h: Math.round(r.height),
      font: cs.fontFamily, size: cs.fontSize, weight: cs.fontWeight, lh: cs.lineHeight, ls: cs.letterSpacing,
      color: cs.color, bg: cs.backgroundColor, border: cs.border, radius: cs.borderRadius, shadow: cs.boxShadow,
      padding: cs.padding, transform: cs.textTransform};
  };
  const samples = {};
  for (const [k, sel] of Object.entries({
    body: 'body', h1: 'h1', h2: 'h2', h3: 'h3', p: 'p', a: 'a', button: 'button, [role=button]', input: 'input, select, textarea',
    nav: 'nav, header', card: '[class*=card], article, li[class]', table: 'table, [role=table]', footer: 'footer'})) samples[k] = desc(pick(sel));
  const W = document.documentElement.clientWidth;
  const overflow = [...document.querySelectorAll('body *')].filter((e) => e.getBoundingClientRect().right > W + 1)
    .slice(0, 8).map((e) => `${e.tagName.toLowerCase()}.${(e.className || '').toString().split(' ')[0]} right=${Math.round(e.getBoundingClientRect().right)}`);
  const fonts = [...document.fonts].filter((f) => f.status === 'loaded').map((f) => `${f.family} ${f.weight} ${f.style}`);
  const sheets = [...document.styleSheets].map((s) => s.href).filter(Boolean);
  return {count, vars, samples, fonts: [...new Set(fonts)], sheets, title: document.title,
    layout: {clientWidth: W, scrollWidth: document.documentElement.scrollWidth, overflow}};
}
"""


def top(d, n=12):
    return Counter(d).most_common(n)


def to_target(t):
    if re.match(r'^https?://', t):
        return t
    p = Path(t).resolve()
    if not p.exists():
        sys.exit(f'not found: {t}')
    return p.as_uri()


def with_playwright(target, out, widths, dark, wait, max_h):
    from playwright.sync_api import sync_playwright
    runs = {}
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--no-sandbox'])
        for w in widths:
            for scheme in (['light', 'dark'] if dark else ['light']):
                ctx = b.new_context(viewport={'width': w, 'height': 900}, color_scheme=scheme, device_scale_factor=1)
                pg = ctx.new_page()
                errors = []
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: m.type == 'error' and errors.append('console: ' + m.text[:200]))
                try:
                    pg.goto(target, wait_until='load', timeout=60000)
                except Exception as e:  # keep going: a slow analytics script shouldn't sink the capture
                    errors.append(f'goto: {e}')
                pg.wait_for_timeout(wait)
                # Trigger lazy-loaded content, then return to top
                pg.evaluate('async () => { for (let y = 0; y < document.body.scrollHeight && y < 20000; y += 800) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); }')
                pg.wait_for_timeout(500)
                name = f'shot-{w}' + ('-dark' if scheme == 'dark' else '')
                h = min(pg.evaluate('document.documentElement.scrollHeight'), max_h)
                pg.set_viewport_size({'width': w, 'height': max(h, 400)})
                pg.wait_for_timeout(300)
                pg.screenshot(path=str(out / f'{name}.png'))
                pg.set_viewport_size({'width': w, 'height': 900})
                data = pg.evaluate(COLLECT_JS)
                data['errors'] = errors
                runs[name] = data
                ctx.close()
        b.close()
    return runs


def find_chromium():
    for c in ('chromium-browser', 'chromium', 'google-chrome', 'google-chrome-stable'):
        if shutil.which(c):
            return shutil.which(c)
    return None


def with_cli(target, out, widths, wait, max_h):
    """Fallback: chromium CLI screenshots + regex scan of linked CSS."""
    exe = find_chromium()
    runs = {}
    # Snap chromium can only write under ~/snap/chromium/common (AppArmor), so stage files there
    stage = Path.home() / 'snap/chromium/common' if '/snap/' in os.path.realpath(exe or '') else Path(tempfile.mkdtemp())
    stage.mkdir(parents=True, exist_ok=True)
    for w in widths:
        if exe:
            shot = stage / f'shot-{w}.png'
            subprocess.run([exe, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                            f'--window-size={w},{min(max_h, 2400)}', f'--virtual-time-budget={wait * 2}',
                            f'--screenshot={shot}', target], capture_output=True, timeout=120)
            if shot.exists():
                shutil.move(str(shot), out / shot.name)
    css = ''
    html = ''
    try:
        if target.startswith('file://'):
            html = Path(target[7:]).read_text(errors='ignore')
        else:
            html = urllib.request.urlopen(urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
    except Exception as e:
        print('fetch failed:', e)
    css += ''.join(re.findall(r'<style[^>]*>(.*?)</style>', html, re.S))
    for href in re.findall(r'<link[^>]+rel=["\']?stylesheet[^>]*href=["\']([^"\']+)', html) + re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)', html):
        try:
            url = urllib.parse.urljoin(target, href)
            css += urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf8', 'ignore')
        except Exception:
            pass
    (out / 'collected.css').write_text(css)
    f = lambda rx: dict(Counter(m.strip() for m in re.findall(rx, css)))
    runs['css-scan'] = {
        'count': {'font': f(r'font-family:\s*([^;}]+)'), 'size': f(r'font-size:\s*([^;}]+)'), 'radius': f(r'border-radius:\s*([^;}]+)'),
                  'shadow': f(r'box-shadow:\s*([^;}]+)'), 'color': f(r'(#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|oklch\([^)]+\))'),
                  'background': {}, 'border': {}, 'weight': f(r'font-weight:\s*([^;}]+)'), 'gap': f(r'gap:\s*([^;}]+)'), 'lh': {}},
        'vars': dict(re.findall(r'(--[\w-]+)\s*:\s*([^;}]+)', css)[:300]),
        'samples': {}, 'fonts': re.findall(r'@font-face\s*{[^}]*font-family:\s*([^;]+)', css), 'sheets': [], 'errors': [],
        'layout': {}, 'title': ''}
    return runs


def write_md(runs, out, target):
    lines = [f'# Style report: {target}', '']
    first = next(iter(runs.values()))
    lines += [f"Title: {first.get('title', '')}", '', '## Fonts loaded', ', '.join(first['fonts'][:20]) or '(none reported)', '']
    labels = {'background': 'Backgrounds (weighted by area)', 'color': 'Text colors', 'font': 'Font families (text elements)',
              'size': 'Font sizes', 'weight': 'Font weights', 'lh': 'Line heights', 'radius': 'Border radii',
              'border': 'Borders', 'shadow': 'Box shadows', 'gap': 'Gaps'}
    for name, data in runs.items():
        lines += [f'## {name}', '']
        for k, label in labels.items():
            items = top(data['count'].get(k, {}), 8 if k in ('shadow', 'border') else 12)
            if items:
                lines.append(f'**{label}:** ' + ' · '.join(f'`{v}` ×{c}' for v, c in items))
        lay = data.get('layout') or {}
        if lay:
            ok = lay['scrollWidth'] <= lay['clientWidth']
            lines.append(f"**Horizontal overflow:** {'none' if ok else 'YES'} (client {lay['clientWidth']}, scroll {lay['scrollWidth']})"
                         + ('' if ok or not lay['overflow'] else ' — ' + '; '.join(lay['overflow'])))
        if data.get('errors'):
            lines.append('**JS errors:** ' + ' | '.join(e[:160] for e in data['errors'][:6]))
        lines.append('')
    if first.get('vars'):
        lines += ['## CSS custom properties (:root/html/body/theme selectors)', '']
        lines += [f'- `{k}: {v}`' for k, v in list(first['vars'].items())[:120]]
        lines.append('')
    if first.get('samples'):
        lines += ['## Representative elements (first visible match)', '']
        for k, s in first['samples'].items():
            if s:
                lines.append(f"- **{k}** <{s['tag']}> \"{s['text']}\" — {s['font'].split(',')[0]} {s['size']}/{s['lh']} w{s['weight']} ls {s['ls']}; "
                             f"color {s['color']}; bg {s['bg']}; radius {s['radius']}; padding {s['padding']}; border {s['border']}"
                             + (f"; shadow {s['shadow']}" if s['shadow'] != 'none' else '') + (f"; {s['transform']}" if s['transform'] != 'none' else ''))
    if first.get('sheets'):
        lines += ['', '## Stylesheets', ''] + [f'- {h}' for h in first['sheets'][:20]]
    (out / 'style-report.md').write_text('\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='URL or local .html file')
    ap.add_argument('--out', default='style-capture')
    ap.add_argument('--widths', default='1440,390')
    ap.add_argument('--dark', action='store_true', help='also capture with prefers-color-scheme: dark')
    ap.add_argument('--wait', type=int, default=3000, help='ms to wait after load (SPAs often need 5000+)')
    ap.add_argument('--max-height', type=int, default=6000)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = to_target(a.target)
    widths = [int(w) for w in a.widths.split(',')]
    try:
        import playwright  # noqa: F401
        runs = with_playwright(target, out, widths, a.dark, a.wait, a.max_height)
    except ImportError:
        print('playwright not installed; using chromium CLI + CSS regex fallback', file=sys.stderr)
        runs = with_cli(target, out, widths, a.wait, a.max_height)
    (out / 'style-report.json').write_text(json.dumps(runs, indent=1))
    write_md(runs, out, target)
    print(f'wrote {out}/style-report.md and {len(list(out.glob("shot-*.png")))} screenshots')


if __name__ == '__main__':
    main()
