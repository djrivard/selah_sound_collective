#!/usr/bin/env python3
"""Edit song lyrics as plain text instead of raw JSON.

    python tools/lyrics.py list                 # every song and its slug
    python tools/lyrics.py export <slug>        # write lyrics/<slug>.txt
    python tools/lyrics.py apply  <slug>        # read it back into the song
    python tools/lyrics.py apply  <slug> --dry  # show the diff, change nothing

The text file looks exactly like a lyric sheet:

    [Verse 1]
    Before I shape a single word
    You know the thing I need

    [Chorus]
    Your kingdom come

Blank lines are ignored. A line in [brackets] starts a new section.

Karaoke timings: three songs have per-line timings for the highlight-as-it-plays
effect. Editing the words is fine -- timings are kept as long as a section still
has the same number of lines. Add or remove lines in a timed section and that
section's timings are dropped (the tool warns, and the words still display).
"""
import json
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
SONGS = SITE / "data" / "songs"
OUT = SITE / "lyrics"


def load(slug):
    p = SONGS / f"{slug}.json"
    if not p.exists():
        sys.exit(f"No song called '{slug}'. Run:  python tools/lyrics.py list")
    return p, json.loads(p.read_text(encoding="utf-8"))


def cmd_list():
    rows = []
    for p in sorted(SONGS.glob("*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        timed = any(t is not None for s in r.get("sections", []) for t, _ in s["lines"])
        rows.append((r["slug"], r["title"], r.get("scripture", ""), timed))
    for slug, title, scrip, timed in sorted(rows, key=lambda x: x[1].lower()):
        print(f"  {slug:34s} {title[:30]:32s} {scrip[:16]:18s}{'  [timed]' if timed else ''}")
    print(f"\n  {len(rows)} songs")


def cmd_export(slug):
    _, rec = load(slug)
    OUT.mkdir(exist_ok=True)
    out = OUT / f"{slug}.txt"
    body = []
    for sec in rec.get("sections", []):
        body.append(f"[{sec['label']}]")
        body += [line for _, line in sec["lines"]]
        body.append("")
    out.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")
    timed = any(t is not None for s in rec.get("sections", []) for t, _ in s["lines"])
    print(f"  wrote {out}")
    print(f"  {rec['title']} - {sum(len(s['lines']) for s in rec['sections'])} lines"
          + ("  [has karaoke timings]" if timed else ""))
    print("\n  Edit that file, then:  python tools/lyrics.py apply " + slug)


def parse(text):
    secs, cur = [], None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^\[(.+?)\]$", line)
        if m:
            cur = {"label": m.group(1).strip(), "lines": []}
            secs.append(cur)
            continue
        if cur is None:
            cur = {"label": "Verse 1", "lines": []}
            secs.append(cur)
        cur["lines"].append(line)
    return [s for s in secs if s["lines"]]


def cmd_apply(slug, dry=False):
    path, rec = load(slug)
    src = OUT / f"{slug}.txt"
    if not src.exists():
        sys.exit(f"No {src}. Run:  python tools/lyrics.py export {slug}")
    new = parse(src.read_text(encoding="utf-8"))
    if not new:
        sys.exit("That file has no lyrics in it - nothing was changed.")

    old = rec.get("sections", [])
    old_by_pos = {i: s for i, s in enumerate(old)}
    merged, lost = [], []
    for i, sec in enumerate(new):
        prev = old_by_pos.get(i)
        keep = (prev and prev["label"] == sec["label"]
                and len(prev["lines"]) == len(sec["lines"]))
        if keep:
            lines = [[prev["lines"][j][0], t] for j, t in enumerate(sec["lines"])]
        else:
            lines = [[None, t] for t in sec["lines"]]
            if prev and any(t is not None for t, _ in prev["lines"]):
                lost.append(sec["label"])
        merged.append({"label": sec["label"], "lines": lines})

    o_txt = [l for s in old for _, l in s["lines"]]
    n_txt = [l for s in merged for _, l in s["lines"]]
    # A real diff: comparing by position turns one inserted line into dozens of
    # bogus "rewordings", which buries the change you actually made.
    import difflib
    diff = list(difflib.SequenceMatcher(a=o_txt, b=n_txt, autojunk=False)
                .get_opcodes())
    edits = [op for op in diff if op[0] != "equal"]
    print(f"  sections {len(old)} -> {len(merged)} | lines {len(o_txt)} -> {len(n_txt)}"
          f" | changes {len(edits)}")
    for tag, i1, i2, j1, j2 in edits:
        for l in o_txt[i1:i2]:
            print(f"     - {l}")
        for l in n_txt[j1:j2]:
            print(f"     + {l}")
    for lab in lost:
        print(f"  !! karaoke timings dropped in [{lab}] (line count changed)")

    if dry:
        print("\n  --dry: nothing was written.")
        return
    rec["sections"] = merged
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  saved {path.name}")
    print("  Now run:  python build.py")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
    elif a[0] == "list":
        cmd_list()
    elif a[0] == "export" and len(a) > 1:
        cmd_export(a[1])
    elif a[0] == "apply" and len(a) > 1:
        cmd_apply(a[1], dry="--dry" in a)
    else:
        print(__doc__)
