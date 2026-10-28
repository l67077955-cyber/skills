#!/usr/bin/env python3
"""Export oblique-figure sheets (HTML) to PNG.

    python3 render.py figures.html                    # one PNG per .sheet
    python3 render.py figures.html --langs zh,en     # one PNG per sheet per language
    python3 render.py figures.html --langs zh,en --query pal=classic

Conventions this script follows (see SKILL.md):
  * every figure lives in a <div class="sheet"> wrapper; the wrapper is what gets screenshotted
  * a sheet may carry data-out="name.png" to pin the output file name
  * language is selected with a ?lang= query parameter; ?pal=classic / ?mono switch palettes
  * captions and language bars are hidden for export (the surrounding document carries them)

Needs: pip install playwright pillow && playwright install chromium
"""

import argparse
import asyncio
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from optimize_png import optimize  # noqa: E402


EXPORT_CSS = """
body { background:#fff; padding:0; }
.sheet { box-shadow:none; margin:0; }
.caption, .langbar { display:none !important; }
"""


async def export(html: pathlib.Path, outdir: pathlib.Path, langs, scale: float, query: str, prefix: str):
    from playwright.async_api import async_playwright

    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for lang in langs:
            page = await browser.new_page(viewport={"width": 1800, "height": 1200}, device_scale_factor=scale)
            url = html.resolve().as_uri()
            params = []
            if lang:
                params.append(f"lang={lang}")
            if query:
                params.append(query)
            if params:
                url += "?" + "&".join(params)
            await page.goto(url)
            await page.add_style_tag(content=EXPORT_CSS)
            await page.evaluate("document.fonts.ready")
            await page.wait_for_timeout(2500)  # connectors re-route after late font/layout settles
            sheets = await page.query_selector_all(".sheet")
            for i, sheet in enumerate(sheets, 1):
                pinned = await sheet.get_attribute("data-out")
                base = pathlib.Path(pinned).name if pinned else f"sheet-{i}.png"
                stem, suffix = base[:-4], base[-4:] if base.endswith(".png") else ".png"
                name = f"{prefix}{stem}" + (f".{lang}" if langs and len(langs) > 1 else "") + suffix
                out = outdir / name
                await sheet.screenshot(path=str(out))
                written.append(out)
            await page.close()
        await browser.close()
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=pathlib.Path, help="sheet HTML file")
    ap.add_argument("--outdir", type=pathlib.Path, default=None, help="where to write PNGs (default: next to the HTML)")
    ap.add_argument("--langs", default="", help="comma separated languages to render (?lang=), e.g. zh,en")
    ap.add_argument("--query", default="", help="extra query string, e.g. 'pal=classic' or 'mono=1'")
    ap.add_argument("--scale", type=float, default=2.0, help="device scale factor for the screenshot (default 2)")
    ap.add_argument("--prefix", default="", help="prefix for output file names")
    ap.add_argument("--no-optimize", action="store_true", help="skip the palette-PNG shrink step")
    args = ap.parse_args()

    html = args.html.resolve()
    if not html.exists():
        sys.exit(f"no such file: {html}")
    outdir = (args.outdir or html.parent).resolve()
    langs = [s.strip() for s in args.langs.split(",") if s.strip()] or [""]  # "" = render the sheet's default language

    written = asyncio.run(export(html, outdir, langs, args.scale, args.query, args.prefix))
    for f in written:
        if not args.no_optimize:
            try:
                optimize(str(f))
            except Exception as exc:  # pillow missing is not fatal for the export itself
                print(f"optimize skipped for {f.name}: {exc}")
        print(f.name)


if __name__ == "__main__":
    main()
