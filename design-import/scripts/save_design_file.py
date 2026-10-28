#!/usr/bin/env python3
"""Write DesignSync `get_file` results to disk, keeping the project's relative paths.

A get_file result is JSON like {"method":"get_file","path":"x/y.html","content":"...","isBase64":false,
"truncated":false}. Large results are saved by the harness to a tool-results .txt file; pass that path.
Small results arrive inline: save the JSON to a file first (or pipe it on stdin with `-`).

Usage: python3 save_design_file.py --out <dir> <result.json|result.txt|-> [...]
"""
import argparse
import base64
import json
import pathlib
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("results", nargs="+")
a = ap.parse_args()
root = pathlib.Path(a.out).resolve()
bad = 0
for r in a.results:
    raw = sys.stdin.read() if r == "-" else pathlib.Path(r).read_text(encoding="utf-8")
    d = json.loads(raw[raw.index("{"):])  # tolerate a leading label line
    rel = d["path"]
    dest = (root / rel).resolve()
    if root not in dest.parents:
        print(f"SKIP {rel}: escapes output dir"); bad += 1; continue
    if d.get("truncated"):
        print(f"WARN {rel}: truncated by get_file (256 KiB cap); this copy is incomplete"); bad += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    if d.get("isBase64"):
        dest.write_bytes(base64.b64decode(d["content"]))
    else:
        dest.write_text(d["content"], encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")
sys.exit(1 if bad else 0)
