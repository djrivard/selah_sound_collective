#!/usr/bin/env python3
"""
publish_song.py  -  flip a Selah song to "published" and wire its cover/audio by slug.

Put this in  tools/  next to convert_musixmatch.py, then run it from your repo root.

USAGE
  python3 tools/publish_song.py <slug> [options]

OPTIONS
  --cover NAME      cover file in src/covers/  (default: auto-detect <slug>.jpg/.png/...)
  --audio NAME      audio file in src/audio/   (default: auto-detect <slug>.mp3/.m4a/...)
  --status STATUS   published | coming-soon    (default: published)
  --repo PATH       repo root                  (default: auto-detected)
  --quiet           suppress the missing-asset warning

EXAMPLES
  python3 tools/publish_song.py where-im-planted
  python3 tools/publish_song.py guardian --cover guardian-v2.jpg    # cache-busted art
  python3 tools/publish_song.py forty --status coming-soon          # send back to placeholder
"""
import argparse, difflib, json, sys
from pathlib import Path

COVER_EXTS = ('.jpg', '.jpeg', '.png', '.webp')
AUDIO_EXTS = ('.mp3', '.m4a', '.ogg', '.wav')


def find_repo(*starts):
    for start in starts:
        for d in [start, *start.parents]:
            if (d / 'data' / 'songs').is_dir():
                return d
    return None


def autodetect(folder, slug, exts, override):
    if override:
        return override
    for e in exts:
        if (folder / f'{slug}{e}').is_file():
            return f'{slug}{e}'
    return f'{slug}{exts[0]}'          # sensible default even if not staged yet


def main():
    ap = argparse.ArgumentParser(add_help=True, description="Publish a Selah song by slug.")
    ap.add_argument('slug')
    ap.add_argument('--cover')
    ap.add_argument('--audio')
    ap.add_argument('--status', choices=['published', 'coming-soon'], default='published')
    ap.add_argument('--repo')
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo).resolve() if args.repo else find_repo(Path.cwd(), Path(__file__).resolve().parent)
    if not repo or not (repo / 'data' / 'songs').is_dir():
        sys.exit("error: couldn't find data/songs — run from your repo root or pass --repo PATH")

    songs = repo / 'data' / 'songs'
    covers, audio_dir = repo / 'src' / 'covers', repo / 'src' / 'audio'

    jf = songs / f'{args.slug}.json'
    if not jf.is_file():
        have = sorted(p.stem for p in songs.glob('*.json'))
        near = difflib.get_close_matches(args.slug, have, n=5, cutoff=0.5)
        msg = f"error: data/songs/{args.slug}.json not found"
        if near:
            msg += "\n  did you mean: " + ", ".join(near)
        sys.exit(msg)

    rec = json.loads(jf.read_text(encoding='utf-8'))     # dict preserves key order

    if args.status == 'coming-soon':
        rec['status'] = 'coming-soon'
        rec['cover'] = '_coming-soon.jpg'
        rec['audio'] = ''
        jf.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f"set {jf.relative_to(repo)} -> coming-soon (cover/audio reset to placeholder)")
        return

    cover = autodetect(covers, args.slug, COVER_EXTS, args.cover)
    audio = autodetect(audio_dir, args.slug, AUDIO_EXTS, args.audio)

    rec['status'] = 'published'
    rec['cover'] = cover
    rec['audio'] = audio
    jf.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    print(f"published {jf.relative_to(repo)}")
    print(f"  cover  = {cover}")
    print(f"  audio  = {audio}")

    if not args.quiet:
        missing = [f'src/covers/{cover}'] if not (covers / cover).is_file() else []
        if not (audio_dir / audio).is_file():
            missing.append(f'src/audio/{audio}')
        if missing:
            print("  ! stage these before you build:")
            for m in missing:
                print("     -", m)
        if not rec.get('sections'):
            print("  ! 'sections' is empty — page publishes without lyrics until you add them")

    print("next: python3 build.py")


if __name__ == '__main__':
    main()
