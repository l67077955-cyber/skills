#!/usr/bin/env python3
"""Inventory the skills that feed Claude Code's skill listing, and edit skillOverrides safely.

  skill_audit.py inventory [--json]
  skill_audit.py apply NAME=STATE ... [--personal STATE] [--remove NAME ...] [--reset] [--write]

STATE is one of: on, name-only, user-invocable-only, off.
`apply` only prints the resulting skillOverrides unless --write is given; with --write it
backs up settings.json to ~/.claude/backups/ first and keeps every other key untouched.
--home points at another home directory (for testing).
"""
import argparse, datetime, glob, json, os, re, shutil, sys

STATES = ("on", "name-only", "user-invocable-only", "off")
DESC_CAP = 1536  # default skillListingMaxDescChars


def frontmatter(path):
    """Return (fields, error). error is set when the block is not strict YAML; fields then come
    from a line-by-line fallback."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        return {}, str(e)
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}, "no frontmatter block"
    try:
        import yaml
    except ImportError:
        yaml = None
    if yaml:
        try:
            data = yaml.safe_load(m.group(1)) or {}
            return (data, None) if isinstance(data, dict) else ({}, "frontmatter is not a mapping")
        except Exception as e:
            err = str(e).splitlines()[0]
    else:
        err = None
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if v and not line.startswith(" "):
            out[k.strip()] = v.strip().strip('"')
    return out, err


def entry(name, source, path, lever):
    fm, err = frontmatter(path)
    desc = " ".join(str(fm.get(k) or "") for k in ("description", "when_to_use")).strip()
    desc = re.sub(r"\s+", " ", desc)
    shown = min(len(desc), DESC_CAP)
    return {
        "name": name, "source": source, "lever": lever, "path": os.path.dirname(path),
        "desc_chars": len(desc), "line_chars": len(f"- {name}: ") + shown,
        "frontmatter_hidden": bool(fm.get("disable-model-invocation")),
        "yaml_error": err,
    }


def inventory(home, cwd):
    claude = os.path.join(home, ".claude")
    rows = []
    for p in sorted(glob.glob(os.path.join(claude, "skills", "*", "SKILL.md"))):
        n = os.path.basename(os.path.dirname(p))
        rows.append(entry(n, "personal", p, "skillOverrides / frontmatter"))
    for p in sorted(glob.glob(os.path.join(claude, "skills", "synced", "*", "*", "SKILL.md"))):
        n = os.path.basename(os.path.dirname(p))
        rows.append(entry("anthropic-skills:" + n, "claude.ai sync", p, "claude.ai settings (skillOverrides unverified)"))
    if os.path.realpath(cwd) != os.path.realpath(home):
        for p in sorted(glob.glob(os.path.join(cwd, ".claude", "skills", "*", "SKILL.md"))):
            n = os.path.basename(os.path.dirname(p))
            rows.append(entry(n, "project", p, "skillOverrides / frontmatter"))
    for pj in glob.glob(os.path.join(claude, "plugins", "**", ".claude-plugin", "plugin.json"), recursive=True):
        if "/.trash/" in pj:
            continue
        root = os.path.dirname(os.path.dirname(pj))
        try:
            pname = json.load(open(pj)).get("name") or os.path.basename(root)
        except Exception:
            pname = os.path.basename(root)
        skills = glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))
        if os.path.isfile(os.path.join(root, "SKILL.md")):
            skills.append(os.path.join(root, "SKILL.md"))
        for p in sorted(skills):
            sname = frontmatter(p)[0].get("name") or os.path.basename(os.path.dirname(p))
            rows.append(entry(f"{pname}:{sname}", "plugin", p, "/plugin (whole plugin only)"))
    return rows


def settings_path(home):
    return os.path.join(home, ".claude", "settings.json")


def load_overrides(home, cwd):
    merged = {}
    files = [settings_path(home), os.path.join(home, ".claude", "settings.local.json"),
             os.path.join(cwd, ".claude", "settings.json"), os.path.join(cwd, ".claude", "settings.local.json")]
    for f in dict.fromkeys(files):
        try:
            merged.update(json.load(open(f)).get("skillOverrides") or {})
        except (OSError, ValueError):
            pass
    return merged


def cmd_inventory(a):
    rows = inventory(a.home, a.cwd)
    ov = load_overrides(a.home, a.cwd)
    for r in rows:
        short = r["name"].split(":", 1)[1] if r["source"] == "claude.ai sync" else r["name"]
        r["override"] = ov.get(r["name"]) or ov.get(short) or "on"
    if a.json:
        print(json.dumps({"skills": rows, "overrides": ov}, ensure_ascii=False, indent=2))
        return
    total = 0
    for src in ("personal", "project", "claude.ai sync", "plugin"):
        group = [r for r in rows if r["source"] == src]
        if not group:
            continue
        sub = sum(r["line_chars"] for r in group)
        total += sub
        print(f"\n## {src}  ({len(group)} skills, {sub:,} chars full listing)  lever: {group[0]['lever']}")
        for r in sorted(group, key=lambda r: -r["line_chars"]):
            flag = " [frontmatter: disable-model-invocation]" if r["frontmatter_hidden"] else ""
            print(f"  {r['line_chars']:>6,}  {r['override']:<20} {r['name']}{flag}")
    print(f"\nOn-disk skills total: {total:,} chars. Bundled skills are not on disk; count them from the listing in context.")
    broken = [r for r in rows if r["yaml_error"]]
    if broken:
        print("\nWARNING: frontmatter is not strict YAML (char counts above came from a line-by-line fallback):")
        for r in broken:
            print(f"  {r['name']}: {r['yaml_error']}  ({r['path']}/SKILL.md)")
        print("  Claude Code's own parser may still read it; check whether the skill's description shows in your listing.")
        print("  Strict tools (claude plugin validate, other agents) can reject it. Usual fix: quote the description. Edit only with the user's OK.")
    extra = sorted(set(ov) - {r["name"] for r in rows} - {r["name"].split(":", 1)[-1] for r in rows})
    if extra:
        print("Overrides with no matching on-disk skill (bundled, or stale): " + ", ".join(f"{k}={ov[k]}" for k in extra))


def cmd_apply(a):
    path = settings_path(a.home)
    try:
        data = json.load(open(path))
    except FileNotFoundError:
        data = {}
    ov = {} if a.reset else dict(data.get("skillOverrides") or {})
    if a.personal:
        for r in inventory(a.home, a.cwd):
            if r["source"] == "personal":
                ov[r["name"]] = a.personal
    for pair in a.set:
        name, _, state = pair.partition("=")
        if state not in STATES:
            sys.exit(f"bad state {state!r} for {name}; use one of {', '.join(STATES)}")
        if state == "on":
            ov.pop(name, None)
        else:
            ov[name] = state
    for name in a.remove:
        ov.pop(name, None)
    before = data.get("skillOverrides") or {}
    if ov:
        data["skillOverrides"] = ov
    else:
        data.pop("skillOverrides", None)
    print(json.dumps({"skillOverrides": ov}, ensure_ascii=False, indent=2))
    changed = sorted(k for k in set(before) | set(ov) if before.get(k) != ov.get(k))
    print("changed: " + (", ".join(f"{k}: {before.get(k, 'on')} -> {ov.get(k, 'on')}" for k in changed) or "nothing"))
    if not a.write:
        print("(dry run; add --write to save)")
        return
    if not changed:
        return
    backups = os.path.join(a.home, ".claude", "backups")
    os.makedirs(backups, exist_ok=True)
    if os.path.exists(path):
        dst = os.path.join(backups, "settings.json.bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(path, dst)
        print("backup: " + dst)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    json.load(open(path))
    print("wrote: " + path + " (takes effect in a new session)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--home", default=os.path.expanduser("~"))
    ap.add_argument("--cwd", default=os.getcwd())
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("inventory"); i.add_argument("--json", action="store_true"); i.set_defaults(fn=cmd_inventory)
    p = sub.add_parser("apply")
    p.add_argument("set", nargs="*", metavar="NAME=STATE")
    p.add_argument("--personal", choices=STATES, help="set every personal skill to this state")
    p.add_argument("--remove", nargs="*", default=[])
    p.add_argument("--reset", action="store_true", help="start from an empty skillOverrides")
    p.add_argument("--write", action="store_true")
    p.set_defaults(fn=cmd_apply)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
