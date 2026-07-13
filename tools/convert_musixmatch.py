#!/usr/bin/env python3
"""
Convert a Musixmatch time-synced transcript into the lyric JSON this site uses.

Musixmatch (Pro > Time-sync) shows each line as:
    MM:SS.ss
    <the line>
    <the line>      (it often repeats the text 2-3 times)

Usage:
    python3 tools/convert_musixmatch.py paste.txt
    # ...or pipe it:
    pbpaste | python3 tools/convert_musixmatch.py

It prints a ready-to-paste "sections" block. Everything lands in one
"Song" section -- split it into Intro / Verse / Chorus etc. by hand;
the site balances the two columns automatically.

To sync an existing song that was published with unsynced lyrics
(all "t" values null), replace each null with the matching time.
"""
import sys, re, json

TIME = re.compile(r"^\s*(\d+):(\d+(?:\.\d+)?)\s*$")


def parse(text):
    lines = [l.rstrip() for l in text.splitlines()]
    out = []
    i = 0
    while i < len(lines):
        m = TIME.match(lines[i])
        if not m:
            i += 1
            continue
        secs = int(m.group(1)) * 60 + float(m.group(2))
        j = i + 1
        lyric = ""
        while j < len(lines):
            if not lines[j].strip():
                j += 1
                continue
            if TIME.match(lines[j]):
                break
            lyric = lines[j].strip()
            break
        if lyric and lyric.lower() != "end of lyrics":
            out.append([round(secs, 2), lyric])
        i = j if j > i else i + 1
    return out


def main():
    text = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else sys.stdin.read()
    lines = parse(text)
    block = {"sections": [{"label": "Song", "lines": lines}]}
    print(json.dumps(block, indent=2, ensure_ascii=False))
    print(f"\n# {len(lines)} lines parsed "
          f"({lines[0][0] if lines else 0}s -> {lines[-1][0] if lines else 0}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
