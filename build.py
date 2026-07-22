#!/usr/bin/env python3
"""
Selah Sound Collective — static site generator.

Reads:
  data/site.json            site-wide settings
  data/songs/*.json         one record per song
  src/assets/*              shared css / js
  src/covers/*  src/audio/* media

Writes a complete static site to:
  docs/                     (deploy this folder — Cloudflare Pages or GitHub Pages)

Add a song = drop a new <slug>.json in data/songs/ (+ its cover and audio),
then run:  python3 build.py
"""
import datetime
import json, shutil, pathlib, html, hashlib, re

_VER = {}


def vurl(root, rel):
    """Asset URL with a content-hash version — changes automatically when the file changes,
    so browser/CDN caches can never serve a stale stylesheet, script, cover, or image."""
    if rel not in _VER:
        f = SRC / rel
        if not f.exists():
            f = OUT / rel          # audio may exist only in the built site
        _VER[rel] = hashlib.sha1(f.read_bytes()).hexdigest()[:8] if f.exists() else "0"
    return f"{root}{rel}?v={_VER[rel]}"

ROOT = pathlib.Path(__file__).parent
DATA = ROOT / "data"
SRC = ROOT / "src"
OUT = ROOT / "docs"

SPOTIFY = ("M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24"
           "-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6"
           " 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38"
           "-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2z"
           "m.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26"
           " 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z")
SHARE_NATIVE = ("M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81"
                " 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66"
                " 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92"
                " 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z")
SHARE_X = "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
SHARE_FB = "M24 12.07C24 5.41 18.63 0 12 0S0 5.41 0 12.07c0 6.02 4.39 11.01 10.13 11.93v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8v8.44C19.61 23.08 24 18.09 24 12.07z"
SHARE_MAIL = "M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4-8 5-8-5V6l8 5 8-5z"

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" '
         'href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?'
         'family=Gloock&family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Outfit:wght@300;400;500;600;700'
         '&display=swap" rel="stylesheet">')


def esc(s):
    return html.escape(str(s), quote=True)


def head(site, title, desc, root, og_image=None, canonical=None, extra="", og_type="website", jsonld=None):
    og = og_image or site.get("ogImage", "")
    if og and not og.startswith("http"):
        base = site.get("baseUrl", "").rstrip("/")
        og = f"{base}/{vurl('', og.lstrip('/'))}" if base else og
    bits = [
        '<!DOCTYPE html><html lang="en"><head>',
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
    ]
    if og:
        bits.append(f'<meta property="og:image" content="{esc(og)}">')
    if canonical:
        bits.append(f'<meta property="og:url" content="{esc(canonical)}">')
        bits.append(f'<link rel="canonical" href="{esc(canonical)}">')
    # Google Analytics (gtag.js)
    bits.append('<script async src="https://www.googletagmanager.com/gtag/js?id=G-HXR5J1NDZB"></script>'
                '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
                "gtag('js',new Date());gtag('config','G-HXR5J1NDZB');</script>")
    bits.append(f'<meta property="og:site_name" content="{esc(site["siteName"])}">')
    bits.append('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">')
    bits.append('<meta name="twitter:card" content="summary_large_image">')
    bits.append(f'<meta name="twitter:title" content="{esc(title)}">')
    bits.append(f'<meta name="twitter:description" content="{esc(desc)}">')
    if og:
        bits.append(f'<meta name="twitter:image" content="{esc(og)}">')
    bits.append(FONTS)
    bits.append(f'<link rel="icon" href="{vurl(root, "assets/favicon.ico")}" sizes="any">')
    bits.append(f'<link rel="icon" type="image/png" sizes="32x32" href="{vurl(root, "assets/favicon-32.png")}">')
    bits.append(f'<link rel="apple-touch-icon" href="{vurl(root, "assets/apple-touch-icon.png")}">')
    bits.append(f'<link rel="stylesheet" href="{vurl(root, "assets/site.css")}">')
    if jsonld:
        bits.append('<script type="application/ld+json">'
                    + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
                    + '</script>')
    bits.append(extra)
    bits.append("</head>")
    return "".join(bits)


def nav(site, root, active=""):
    items = [("Music", "index.html", "songs"), ("About", "about.html", "about"),
             ("Listen", "listen.html", "listen"),
             ("Support", "support.html", "support"), ("Contact", "contact.html", "contact")]
    links = "".join(
        f'<a href="{root}{href}"{" class=\"active\"" if active==key else ""}>{label}</a>'
        for label, href, key in items)
    return (f'<header class="nav"><div class="nav-wrap">'
            f'<a class="brand" href="{root}index.html" aria-label="{esc(site["siteName"])} home">'
            f'<img class="brand-logo" src="{vurl(root, "assets/logo-full.png")}" alt="{esc(site["siteName"])}"></a>'
            f'<button class="nav-toggle" id="navToggle" aria-label="Menu">&#9776;</button>'
            f'<nav class="nav-links" id="navLinks">{links}</nav></div></header>')


def footer(site, root):
    items = [("Songs", "index.html"), ("Listen", "listen.html"), ("About", "about.html"),
             ("Contact", "contact.html"), ("Support", "support.html")]
    links = "".join(f'<a href="{root}{href}">{label}</a>' for label, href in items)
    return (f'<footer class="site-footer">'
            f'<a class="brand" href="{root}index.html" aria-label="{esc(site["siteName"])} home">'
            f'<img class="foot-logo" src="{vurl(root, "assets/logo-full.png")}" alt="{esc(site["siteName"])}"></a>'
            f'<div class="foot-links">{links}</div>'
            f'<div class="foot-note">{esc(site.get("tagline",""))}</div></footer>')


def split_columns(sections):
    counts = [len(s["lines"]) for s in sections]
    total = sum(counts) or 1
    half = total / 2.0
    best_k, best_diff, cum = len(sections), 1e9, 0
    for k in range(1, len(sections)):
        cum += counts[k - 1]
        if abs(cum - half) < best_diff:
            best_diff, best_k = abs(cum - half), k
    return sections[:best_k], sections[best_k:]


def column_html(sections):
    out = ['      <div class="col">']
    for s in sections:
        out.append(f'        <div class="section"><span class="label">{esc(s["label"])}</span>')
        for t, text in s["lines"]:
            attr = f' data-t="{t}"' if t is not None else ""
            out.append(f'          <span class="ln"{attr}>{text}</span>')
        out.append("        </div>")
    out.append("      </div>")
    return "\n".join(out)



def song_seo(site, song, canonical):
    """A distinct title, description and MusicRecording record for each song.

    Every page previously shared one description, which search engines treat as
    duplicate content and which wastes the strongest ranking signal a song page
    has: the passage it is drawn from. People search "psalm 23 song".
    """
    base = site.get("baseUrl", "").rstrip("/")
    # A few songs carry no scripture field but do have a matched verse; use it,
    # so "Five Smooth Stones" still surfaces for a 1 Samuel 17 search.
    scrip = (song.get("scripture") or "").strip() or (song.get("epigraphRef") or "").strip()
    title = f'{song["title"]} \u2014 {scrip} | {site["siteName"]}' if scrip \
        else f'{song["title"]} | {site["siteName"]}'

    bits = [f'{song["title"]} is a modern Christian song']
    if scrip:
        bits.append(f'drawn from {scrip}')
    bits.append(f'by {site["siteName"]}')
    desc = " ".join(bits) + "."
    epi = (song.get("epigraph") or "").strip()
    if epi:
        desc += f' \u201c{epi}.\u201d'
    desc += " Listen free with the full lyrics."
    if len(desc) > 300:
        desc = desc[:297].rsplit(" ", 1)[0] + "\u2026"

    ld = {
        "@context": "https://schema.org",
        "@type": "MusicRecording",
        "name": song["title"],
        "byArtist": {"@type": "MusicGroup", "name": site["siteName"],
                     "url": base + "/" if base else None},
        "genre": ["Christian", "Contemporary Christian Music", "Worship"],
        "inLanguage": "en",
    }
    if canonical:
        ld["url"] = canonical
        ld["mainEntityOfPage"] = canonical
    if song.get("cover"):
        ld["image"] = f'{base}/covers/{song["cover"]}' if base else song["cover"]
    audio_base = (site.get("audioBaseUrl") or "").rstrip("/")
    if song.get("audio") and audio_base:
        ld["audio"] = {"@type": "AudioObject",
                       "contentUrl": f'{audio_base}/{song["audio"]}',
                       "encodingFormat": "audio/mpeg"}
    if scrip:
        ld["about"] = {"@type": "CreativeWork", "name": scrip}
        ld["keywords"] = f'{scrip}, {song["title"]}, modern Christian music, scripture song'
    if song.get("spotify"):
        ld["sameAs"] = [song["spotify"]]
    ld = {k: v for k, v in ld.items() if v is not None}
    return title, desc, ld


def render_song(site, song, root="../"):
    cover = song["cover"]
    title = song["title"]
    full_title = f'{title} \u2014 {site["siteName"]}'
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/songs/{song['slug']}.html" if base else None
    og_image = f"{base}/covers/{cover}" if base else None
    cover_rel = "covers/" + cover
    cover_style = f"<style>:root{{--cover:url('{vurl(root, cover_rel)}')}}</style>"
    seo_title, seo_desc, seo_ld = song_seo(site, song, canonical)
    h = head(site, seo_title, seo_desc, root, og_type="music.song", jsonld=seo_ld,
             og_image=og_image, canonical=canonical, extra=cover_style)

    left, right = split_columns(song["sections"])
    cols = column_html(left) + "\n\n" + column_html(right)

    synced = any(t is not None for s in song["sections"] for t, _ in s["lines"])
    hint = "&#9834; Lyrics follow the music" if synced else "&#9834; Synced lyrics coming soon"

    epi = ""
    if song.get("epigraph"):
        ref = f'<cite>{esc(song["epigraphRef"])}</cite>' if song.get("epigraphRef") else ""
        epi = f'<p class="epi">&ldquo;{esc(song["epigraph"])}&rdquo; {ref}</p>'

    whisper = f'<div class="whisper">{esc(song["whisper"])}</div>' if song.get("whisper") else ""
    listen_line = song.get("listenLine", "Press play and sit with the song.")
    spotify = song.get("spotify", "")
    share_text = song.get("shareText",
                          f'{title} \u2014 from {song.get("scripture","Scripture")}, by {site["siteName"]}.')

    sources = ""
    if song.get("audio"):
        # audioBaseUrl (e.g. an R2 bucket) keeps the big mp3s out of the repo.
        # Leave it blank in site.json to serve them from docs/audio instead.
        base = (site.get("audioBaseUrl") or "").rstrip("/")
        if base:
            sources += f'<source src="{esc(base)}/{esc(song["audio"])}" type="audio/mpeg">'
        else:
            sources += f'<source src="{vurl(root, "audio/" + song["audio"])}" type="audio/mpeg">'
    if song.get("audioFallback"):
        sources += f'<source src="{esc(song["audioFallback"])}" type="audio/mpeg">'

    spotify_cta = (f'<a class="btn btn-spotify" id="spotifyLink" href="{esc(spotify)}" target="_blank" rel="noopener">'
                   f'<svg viewBox="0 0 24 24"><path d="{SPOTIFY}"/></svg> Listen on Spotify</a>') if spotify else ""
    spotify_nb = (f'<a class="nb-spotify" href="{esc(spotify)}" target="_blank" rel="noopener" '
                  f'title="Listen on Spotify" aria-label="Listen on Spotify"><svg viewBox="0 0 24 24">'
                  f'<path d="{SPOTIFY}"/></svg></a>') if spotify else ""

    # "Find this on all other platforms" — artist-profile links (Spotify omitted; it has its own button)
    icons = json.loads((DATA / "icons.json").read_text())
    plat_names = {"applemusic": "Apple Music", "youtube": "YouTube", "deezer": "Deezer", "amazonmusic": "Amazon Music"}
    other = ""
    for pid, label in plat_names.items():
        url = site.get("artistLinks", {}).get(pid)
        if url:
            other += (f'<a class="oplat" href="{esc(url)}" target="_blank" rel="noopener" title="{esc(label)}" '
                      f'aria-label="{esc(label)}"><svg viewBox="0 0 24 24"><path d="{icons.get(pid,"")}"/></svg></a>')
    other_row = (f'<div class="other-plat"><span class="other-lab">Find this on all platforms</span>'
                 f'<div class="oplat-row">{other}</div></div>') if other else ""

    body = f"""<body>
{nav(site, root, "songs")}
<header class="hero">
  <div class="hero__bg"></div><div class="hero__veil"></div>
  <canvas id="viz"></canvas><div class="grain"></div>
  <h1 class="sr-only">{esc(title)} &mdash; {esc(site["siteName"])} ({esc(song.get("scripture",""))})</h1>
  <div class="hero__inner">
    <div class="release">
      <div class="cover-frame"><div class="scrim"></div><div class="cover-band" id="coverBand">{esc(site["siteName"])}</div></div>
      <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
    </div>
    <div class="scrip"><span class="dia"></span> {esc(song.get("scripture",""))} <span class="dia"></span></div>
    {epi}
    {f'<div class="style-note">{esc(song["styleNote"])}</div>' if song.get("styleNote") else ""}
    <button class="play-hero" id="heroPlay" aria-label="Play song"><svg viewBox="0 0 24 24" id="heroIcon"><path d="M8 5v14l11-7z"/></svg></button>
    <div class="play-label" id="heroLabel">Play the Song</div>
  </div>
  <div class="scrollcue"><span>Lyrics</span><span class="bar"></span></div>
</header>

<main class="lyrics-wrap"><div class="panel">
  <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
  <div class="lyric-head">
    <div class="eyebrow">{esc(song.get("lyricEyebrow","Lyrics"))}</div>
    <h2>{esc(song.get("lyricHeading", title))}</h2>
    <div class="rule"></div>
    <div class="sync-hint" id="syncHint">{hint}</div>
  </div>
  <div class="cols" id="cols">
{cols}
  </div>
  {whisper}
</div></main>

<section class="listen">
  <div class="eyebrow">Listen &amp; Share</div>
  <p>{esc(listen_line)}</p>
  <div class="cta-row">
    <button class="btn btn-play" id="ctaPlay"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg><span id="ctaText">Play the Song</span></button>
    {spotify_cta}
  </div>
  {other_row}
  <div class="share">
    <span class="lab">Share this song</span>
    <div class="share-icons">
      <button class="ic" id="shareNative" title="Share" aria-label="Share"><svg viewBox="0 0 24 24"><path d="{SHARE_NATIVE}"/></svg></button>
      <a class="ic" id="shareX" target="_blank" rel="noopener" title="Share on X" aria-label="Share on X"><svg viewBox="0 0 24 24"><path d="{SHARE_X}"/></svg></a>
      <a class="ic" id="shareFb" target="_blank" rel="noopener" title="Share on Facebook" aria-label="Share on Facebook"><svg viewBox="0 0 24 24"><path d="{SHARE_FB}"/></svg></a>
      <a class="ic" id="shareMail" title="Share by email" aria-label="Share by email"><svg viewBox="0 0 24 24"><path d="{SHARE_MAIL}"/></svg></a>
    </div>
  </div>
</section>

{footer(site, root)}

<div class="nowbar" id="nowbar">
  <div class="nb-cover"></div>
  <div class="nb-meta"><div class="nb-title">{esc(title)}</div><div class="nb-band">{esc(site["siteName"])}</div></div>
  <button class="nb-play" id="nbPlay" aria-label="Play / pause"><svg viewBox="0 0 24 24" id="nbIcon"><path d="M8 5v14l11-7z"/></svg></button>
  <div class="nb-prog">
    <span class="time cur" id="tCur">0:00</span>
    <div class="track" id="track"><div class="fill" id="fill"></div><div class="knob" id="knob"></div></div>
    <span class="time dur" id="tDur">0:00</span>
  </div>
  {spotify_nb}
</div>
<div class="toast" id="toast">Link copied</div>

<audio id="audio" preload="metadata">{sources}</audio>
<script>window.SELAH_SONG={{title:{json.dumps(title)},shareText:{json.dumps(share_text)}}};</script>
<script src="{vurl(root, "assets/site.js")}"></script>
<script src="{vurl(root, "assets/player.js")}"></script>
</body></html>"""
    return h + body


OT_BOOKS = ["Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
            "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
            "Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes",
            "Song of Solomon","Song of Songs",
            "Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos",
            "Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi"]
NT_BOOKS = ["Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians",
            "Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians",
            "1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter",
            "1 John","2 John","3 John","Jude","Revelation"]

# Canonical position of every book, Genesis -> Revelation.
BOOK_ORDER = {b: i for i, b in enumerate(OT_BOOKS + NT_BOOKS)}

# Songs whose scripture is a narrative title ("Cain & Abel") or a bare book name
# carry no chapter to sort on, so their place in the book is set here.
CANON_HINTS = {
    "brothers-keeper":        (4, 0),    # Cain & Abel        -> Genesis 4
    "a-little-less":          (29, 0),   # Leah & Rachel      -> Genesis 29
    "beyond-the-waters":      (14, 0),   # the crossing       -> Exodus 14
    "sea-of-triumph":         (15, 0),   # Song of Moses      -> Exodus 15
    "where-the-pillars-fall": (16, 0),   # Samson & Delilah   -> Judges 16
    "five-smooth-stones":     (17, 0),   # David & Goliath    -> 1 Samuel 17
    "when-morning-stars-sang": (38, 7),  # Job 38:7
    "wisdom-of-the-wind":     (1, 0),    # Solomon's Vanity   -> Ecclesiastes 1
    "yet-i-will-rejoice":     (3, 17),   # Habakkuk 3:17-18
    "one-body-one-spirit":    (4, 4),    # Ephesians 4:4
}

_BOOKISH = re.compile(r"^\s*(?:[123]\s*)?[A-Za-z][A-Za-z\s.'&]*")
_CHAPVERSE = re.compile(r"(\d+)(?:\s*:\s*(\d+))?")


def scripture_pos(song):
    """(chapter, verse) for ordering. Handles 'Genesis 6-9', 'Prov.1:2-5', '1Thes.5:3-6'."""
    hint = CANON_HINTS.get(song.get("slug"))
    if hint:
        return hint
    s = (song.get("scripture") or "").strip()
    m = _BOOKISH.match(s)                 # drop the book-name prefix first, so
    rest = s[m.end():] if m else s        # the '1' of '1 Samuel 17' is never the chapter
    m2 = _CHAPVERSE.search(rest)
    if not m2:
        return (999, 0)                   # no chapter known -> end of its book
    return (int(m2.group(1)), int(m2.group(2) or 0))


def canon_key(song):
    """Sort songs as the Bible runs: Genesis -> Revelation, then by chapter and verse."""
    book = song.get("book", "") or ""
    if book in BOOK_ORDER:
        rank = (0, BOOK_ORDER[book])
    else:
        rank = (1, 0)                     # standalone songs sit after the books
    ch, vs = scripture_pos(song)
    return rank + (ch, vs, song.get("title", ""))


def render_library(site, songs, root=""):
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/index.html" if base else None
    base = site.get("baseUrl", "").rstrip("/")
    live_songs = [s for s in songs if s.get("status") == "published"]
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "MusicGroup",
         "@id": f"{base}/#artist" if base else "#artist",
         "name": site["siteName"],
         "description": site.get("description", ""),
         "genre": ["Christian", "Contemporary Christian Music", "Worship", "Scripture Song"],
         "url": f"{base}/" if base else None,
         "sameAs": [u for u in list((site.get("artistLinks") or {}).values())
                    + ([site["spotifyArtist"]] if site.get("spotifyArtist") else []) if u]},
        {"@type": "WebSite",
         "@id": f"{base}/#website" if base else "#website",
         "url": f"{base}/" if base else None,
         "name": site["siteName"],
         "description": site.get("description", ""),
         "inLanguage": "en",
         "publisher": {"@id": f"{base}/#artist" if base else "#artist"}},
        {"@type": "CollectionPage",
         "name": f'{site["siteName"]} \u2014 Songs',
         "url": canonical,
         "isPartOf": {"@id": f"{base}/#website" if base else "#website"},
         "about": {"@id": f"{base}/#artist" if base else "#artist"},
         "numberOfItems": len(live_songs)},
    ]}
    for node in ld["@graph"]:
        for k in [k for k, v in node.items() if v is None]:
            del node[k]
    h = head(site, f'Modern Christian Music from Scripture \u2014 {site["siteName"]}',
             site.get("description", ""), root, canonical=canonical, jsonld=ld)
    books = {s.get("book", "") for s in songs if s.get("book")}

    def group_of(book):
        if book in OT_BOOKS: return "ot"
        if book in NT_BOOKS: return "nt"
        return "other"

    groups = [("ot", "Old Testament", [b for b in OT_BOOKS if b in books]),
              ("nt", "New Testament", [b for b in NT_BOOKS if b in books]),
              ("other", "Other Songs", sorted(books - set(OT_BOOKS) - set(NT_BOOKS)))]
    group_chips = '<button class="chip on" data-group="all">All Songs</button>'
    book_rows = ""
    for gid, label, bs in groups:
        if not bs:
            continue
        group_chips += f'<button class="chip" data-group="{gid}">{esc(label)}</button>'
        row = "".join(f'<button class="chip chip-book" data-book="{esc(b)}">{esc(b)}</button>' for b in bs)
        book_rows += f'<div class="book-row" data-row="{gid}">{row}</div>'

    cards = []
    for s in songs:
        soon = s.get("status") != "published"
        cover = s.get("cover", "_coming-soon.jpg")
        cover_url = s.get("coverUrl", "")
        img_src = esc(cover_url) if cover_url else vurl(root, "covers/" + cover)
        has_art = bool(cover_url) or not soon
        dot = ('<span class="play-dot"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>'
               if not soon else
               (f'<span class="play-dot sp"><svg viewBox="0 0 24 24"><path d="{SPOTIFY}"/></svg></span>'
                if s.get("spotify") else ""))
        badge = '<span class="badge">Coming soon</span>' if soon else ""
        sp_hint = ('<div class="card-sp"><svg viewBox="0 0 24 24"><path d="' + SPOTIFY + '"/></svg> Listen on Spotify</div>'
                   if soon and s.get("spotify") else "")
        inner = (f'<div class="card-cover{"" if has_art else " noart"}">'
                 f'<img class="card-img" src="{img_src}" alt="{esc(s["title"])} cover" loading="lazy">'
                 f'<div class="scrim"></div>{badge}{dot}</div>'
                 f'<div class="card-meta"><div class="card-title">{esc(s["title"])}</div>'
                 f'<div class="card-scrip">{esc(s.get("scripture",""))}</div>{sp_hint}</div>')
        attrs = (f'data-title="{esc(s["title"])}" data-book="{esc(s.get("book",""))}" '
                 f'data-group="{group_of(s.get("book",""))}"')
        if soon and s.get("spotify"):
            cards.append(f'<a class="song-card soon" href="{esc(s["spotify"])}" target="_blank" rel="noopener" {attrs}>{inner}</a>')
        elif soon:
            cards.append(f'<div class="song-card soon" {attrs}>{inner}</div>')
        else:
            cards.append(f'<a class="song-card" href="{root}songs/{esc(s["slug"])}.html" {attrs}>{inner}</a>')

    # "Over N songs" — derived from the catalogue and floored to a ten, so the
    # claim stays true as songs are added and never needs hand-editing.
    live = sum(1 for s in songs if s.get("status") == "published")
    over = max(10, ((live - 1) // 10) * 10)

    body = f"""<body>
<div class="page-bg"></div>
{nav(site, root, "songs")}
<section class="home-hero2">
  <div class="hh-eyebrow">/\u02c8si\u02d0.l\u0259/ \u2014 pause here, let it sink in</div>
  <h1 class="hh-selah">Selah</h1>
  <div class="hh-sub">Sound Collective</div>
  <p class="hh-tag">Ancient Scripture, Set to Today&rsquo;s Modern Music</p>
  <div class="hh-rule"><span></span></div>
  <div class="hh-proof">{over}+ songs &middot; all 150 psalms &middot; free with full lyrics</div>
  <div class="hh-ctas">
    <a class="btn btn-play" id="heroBrowse" href="#libSearch"><svg viewBox="0 0 24 24" width="13" height="13"><path d="M8 5v14l11-7z"/></svg>Start Listening</a>
    <a class="btn hh-ghost" href="listen.html">Streaming Services</a>
  </div>
  <div class="hh-rule hh-rule-end"><span></span></div>
</section>
<section class="home-intro">
  <p>In the psalms, one small word appears again and again: <em>Selah</em>. Pause here. Let what you just heard sink in.</p>
  <p>That&rsquo;s the invitation behind every song in this catalog &mdash; follow the Word as the music carries it, no two songs sounding alike. <span class="start">No account, no app. Start anywhere.</span></p>
  <p class="lead selah-line">Listen. Pause. Be inspired. <em>Selah.</em></p>
  <div class="rule"></div>
</section>
<main class="page page--after-hero">
  <div class="page-head">
    <div class="eyebrow">The Catalog</div>
    <h2 class="as-h1">Songs</h2>
    <div class="rule"></div>
  </div>
  <div class="filterbar">
    <input class="lib-search" id="libSearch" type="search" placeholder="Search songs&hellip;" aria-label="Search songs">
    <div class="chips">{group_chips}</div>
    <button class="chip toggle" id="hideSoon" aria-pressed="false">Hide coming soon</button>
  </div>
  <div class="book-rows" id="bookRows">{book_rows}</div>
  <div class="lib-grid" id="libGrid">
    {"".join(cards)}
  </div>
  <div class="lib-empty" id="libEmpty">No songs match that search yet.</div>
</main>
{footer(site, root)}
<script src="{vurl(root, "assets/site.js")}"></script>
</body></html>"""
    return h + body


def render_listen(site, root=""):
    icons = json.loads((DATA / "icons.json").read_text())
    songs = [json.loads(f.read_text()) for f in sorted((DATA / "songs").glob("*.json"))]
    by_slug = {s["slug"]: s for s in songs}

    def icon(iid):
        path = icons.get(iid, "")
        return f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{path}"/></svg>' if path else ""

    # Start here: three on-site songs
    sh = ""
    for slug in ["let-there-be-you", "where-you-go-ill-follow", "awake-awake"]:
        s = by_slug.get(slug)
        if not s or s.get("status") != "published":
            continue
        scrip = (s.get("scripture") or s.get("epigraphRef") or "").strip()
        sh += (f'<a class="sh-song" href="songs/{slug}.html">'
               f'<img src="{vurl(root, "covers/" + s["cover"])}" alt="{esc(s["title"])} cover" loading="lazy">'
               f'<span class="sh-meta"><span class="sh-title">{esc(s["title"])}</span>'
               f'<span class="sh-scrip">{esc(scrip)}</span>'
               f'<span class="sh-play"><svg viewBox="0 0 24 24" width="10" height="10"><path d="M8 5v14l11-7z"/></svg>Play</span></span></a>')

    links = site.get("artistLinks") or {}
    plats = [pl for pl in site.get("platforms", []) if pl.get("id") != "spotify"]
    plat_tiles = "".join(
        f'<a class="plat" href="{esc(pl["url"])}" target="_blank" rel="noopener">{icon(pl["id"])}'
        f'<span>{esc(pl["name"])}</span></a>' for pl in plats)

    socials = {s0["id"]: s0 for s0 in site.get("socials", [])}
    social_tiles = "".join(
        f'<a class="plat" href="{esc(socials[k]["url"])}" target="_blank" rel="noopener">{icon(k)}'
        f'<span>{esc(socials[k]["name"])}</span></a>'
        for k in ("instagram", "facebook") if k in socials)

    inner = f"""<div class="listen-page">
    <div class="start-here">
      <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
      <div class="sh-label">Start here \u2014 three to begin with</div>
      <div class="sh-grid">{sh}</div>
      <div class="sh-note">Plays right here \u2014 no account, no app</div>
    </div>
    <div class="plat-sec">
      <h2 class="plat-h">Stream the Songs</h2>
      <p class="plat-lede">Follow on the platform you already use \u2014 new releases will find you.</p>
      <div class="plat-grid plat-grid--lead">
        <a class="plat plat-lead" href="{esc(links.get("spotify", "#"))}" target="_blank" rel="noopener">
          <span class="pl-eyebrow">Most listeners are here</span>
          <span class="pl-name">Spotify</span>
          <span class="pl-lede">Follow the artist \u2014 every release, the day it lands.</span>
          <span class="pl-btn">Follow on Spotify</span>
        </a>
        {plat_tiles}
      </div>
    </div>
    <div class="plat-sec">
      <h2 class="plat-h">Follow Along</h2>
      <p class="plat-lede">Behind the songs \u2014 new releases, the stories in the Scriptures, and what&rsquo;s coming next.</p>
      <div class="plat-grid plat-grid--lead">
        <a class="plat plat-lead plat-lead--gold" href="https://selahsoundcollective.substack.com/p/i-cant-go-back" target="_blank" rel="noopener">
          <span class="pl-eyebrow pl-eyebrow--gold">On the Substack</span>
          <span class="pl-post">&ldquo;I Can&rsquo;t Go Back&rdquo; <em>\u2014 latest post</em></span>
          <span class="pl-lede">On vows, the weight of a word, and what a town decides to remember.</span>
        </a>
        {social_tiles}
      </div>
    </div>
    </div>"""
    return content_page(site, root, "listen", "Everywhere the Music Lives", "Listen & Follow",
                        "Stream, follow, and share \u2014 wherever you listen.", inner, "listen.html")


# A distinct description per page; sharing one is duplicate content.
PAGE_DESC = {
    "about.html": ("Selah Sound Collective sets Scripture to modern Christian music \u2014 over 230 songs "
                   "from Genesis to Revelation. Produced by Dominic Rivard; gifts send children to camp."),
    "listen.html": ("Stream Selah Sound Collective on Spotify, Apple Music, YouTube, Deezer and Amazon "
                    "Music \u2014 modern Christian songs drawn from Scripture and the psalms."),
    "support.html": ("Support Selah Sound Collective. Gifts go to God\u2019s Work and to sending children "
                     "to camp who could not otherwise go."),
    "contact.html": ("Contact Selah Sound Collective \u2014 questions, song requests, or a hello. "
                     "Modern Christian music drawn from Scripture."),
}


def content_page(site, root, active, eyebrow, title, lede, inner_html, canonical_name):
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/{canonical_name}" if base else None
    desc = PAGE_DESC.get(canonical_name, site.get("description", ""))
    ld = {"@context": "https://schema.org", "@type": "WebPage",
          "name": title, "description": desc, "inLanguage": "en"}
    if canonical:
        ld["url"] = canonical
        ld["isPartOf"] = {"@type": "WebSite", "@id": f"{base}/#website"}
    h = head(site, f'{title} \u2014 {site["siteName"]}', desc, root, canonical=canonical, jsonld=ld)
    body = f"""<body>
<div class="page-bg"></div>
{nav(site, root, active)}
<main class="page">
  <div class="page-head">
    <div class="eyebrow">{esc(eyebrow)}</div>
    <h1>{esc(title)}</h1>
    {f'<p class="lede">{esc(lede)}</p>' if lede else ''}
    <div class="rule"></div>
  </div>
  {inner_html}
</main>
{footer(site, root)}
<script src="{vurl(root, "assets/site.js")}"></script>
</body></html>"""
    return h + body


def render_about(site, root=""):
    songs = [json.loads(f.read_text()) for f in sorted((DATA / "songs").glob("*.json"))]
    pub = [s for s in songs if s.get("status") == "published"]
    over = max(10, ((len(pub) - 1) // 10) * 10)
    books = len({s.get("book") for s in pub if s.get("book") not in (None, "", "Standalone")})
    inner = f"""<div class="stat-row">
    <div class="stat"><div class="stat-n">{over}+</div><div class="stat-l">Original songs</div></div>
    <div class="stat-div"></div>
    <div class="stat"><div class="stat-n">150</div><div class="stat-l">Every psalm, set</div></div>
    <div class="stat-div"></div>
    <div class="stat"><div class="stat-n">{books}</div><div class="stat-l">Books of the Bible</div></div>
    <div class="stat-div"></div>
    <div class="stat"><div class="stat-n">Free</div><div class="stat-l">With full lyrics</div></div>
    </div>
    <div class="about-cols">
    <div class="prose" style="margin:0">
    <p>The name comes from the psalms. Seventy-one times, right in the middle of the singing, one small word appears: <em>Selah</em>. Most scholars read it as a musical instruction. Stop here. Let the last line land before the next one begins.</p>
    <p>Selah Sound Collective was built on that instruction: over 230 songs that each take a passage of Scripture &mdash; a vow, a psalm, a moment of deliverance &mdash; and give it a melody you can sit inside. These are modern settings, and no two sound alike.</p>
    </div>
    <div class="about-photo">
    <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
    <img src="{vurl(root, "assets/about-writing.jpg")}" alt="Writing song lyrics beside an open Bible">
    </div>
    </div>
    <div class="prose">
    <p class="scripture">&ldquo;Speak to one another with psalms, hymns, and songs from the Spirit.&rdquo;<br><cite style="font-style:normal;font-size:.82em;letter-spacing:.08em">Ephesians 5:19</cite></p>
    <p>A song travels further than a page. You can read Ruth&rsquo;s vow and admire it; humming it for a week is harder to walk away from. That&rsquo;s the hope here: that somewhere between the second verse and the drive home, one of these follows you out of the car and into Monday.</p>
    <p>Selah Sound Collective is produced by <strong>Dominic Rivard</strong>, who wrote the words to most of what you&rsquo;re hearing. The songs are only half of it: what this project raises goes to God&rsquo;s Work, and to sending kids to camp &mdash; the ones who have earned a week away, and the ones whose families cannot get them there. Usually the same kids.</p>
    <p>Thank you for listening. And when a line catches you, do what the psalms say. Pause. <em>Selah.</em></p>
    </div>
    <div class="about-cta">
    <div class="ac-label">Not sure where to begin?</div>
    <div class="cta-row" style="justify-content:center">
      <a class="btn btn-play" href="{root}index.html?book=Psalms"><svg viewBox="0 0 24 24" width="12" height="12"><path d="M8 5v14l11-7z"/></svg><span>Start with the Psalms</span></a>
      <a class="btn btn-goldline" href="{root}index.html"><span>Browse all songs</span></a>
    </div>
    </div>"""
    return content_page(site, root, "about", "The Project", "About the Selah Project", site.get("tagline", ""), inner, "about.html")


def render_contact(site, root=""):
    endpoint = site.get("contactFormEndpoint", "#")
    email = site.get("contactEmail", "")
    mail_alt = (f'<p class="form-alt">Or email us directly at <a href="mailto:{esc(email)}">{esc(email)}</a>.</p>'
                if email else "")
    inner = f"""<form class="form" action="{esc(endpoint)}" method="POST">
    <div class="field"><label for="name">Your name</label><input id="name" name="name" type="text" required></div>
    <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" required></div>
    <div class="field">
      <label>What&rsquo;s this about?</label>
      <div class="topic-chips">
        <label class="topic"><input type="radio" name="topic" value="Just a hello" checked><span>Just a hello</span></label>
        <label class="topic"><input type="radio" name="topic" value="Song request"><span>Song request</span></label>
        <label class="topic"><input type="radio" name="topic" value="Playing a song publicly"><span>Playing a song publicly</span></label>
        <label class="topic"><input type="radio" name="topic" value="Something else"><span>Something else</span></label>
      </div>
    </div>
    <div class="field"><label for="message">Message</label><textarea id="message" name="message" required></textarea></div>
    <button class="btn btn-play" type="submit"><span>Send Message</span></button>
    </form>
    {mail_alt}
    <div class="faq-card">
    <div class="faq-label">Before you write &mdash;</div>
    <p><strong>Can we play or sing these publicly?</strong> Yes &mdash; playing and singing the songs publicly is welcome and free. The full lyrics are on every song page; a note telling us where they&rsquo;re being heard always makes our week.</p>
    </div>"""
    return content_page(site, root, "contact", "Get in Touch", "Contact",
                        "Questions, song requests, or just a hello \u2014 we would love to hear from you.",
                        inner, "contact.html")


def _live(url):
    """A configured link, or empty if it is still a placeholder."""
    url = (url or "").strip()
    return "" if (not url or "REPLACE_WITH" in url) else url


def render_support(site, root=""):
    paypal = _live(site.get("donatePaypal"))
    stripe = _live(site.get("donateUrl"))
    links = site.get("artistLinks") or {}
    sp, ap = links.get("spotify"), links.get("applemusic")

    # streaming-first block
    stream = ""
    if sp or ap:
        btns = ""
        if sp:
            btns += (f'<a class="btn btn-spotify" href="{esc(sp)}" target="_blank" rel="noopener">'
                     f'<span>Follow on Spotify</span></a>')
        if ap:
            btns += (f'<a class="btn btn-goldline" href="{esc(ap)}" target="_blank" rel="noopener">'
                     f'<span>Apple Music</span></a>')
        stream = f"""<div class="stream-first">
    <div class="sf-label">The free way &mdash; just listen</div>
    <p>Stream the songs, add them to your playlists, share one with a friend. The royalties go to the same work as every gift below &mdash; and it costs you nothing.</p>
    <div class="cta-row" style="justify-content:center">{btns}</div>
    </div>"""

    give = paypal or stripe
    amounts = ""
    if give:
        cards = [("$5", "toward the music"),
                 ("$15", "toward a camper&rsquo;s week"),
                 ("$50", "toward getting a kid to camp")]
        amounts = '<div class="amount-cards">' + "".join(
            f'<a class="amt{" amt--hl" if n == "$15" else ""}" href="{esc(give)}" target="_blank" rel="noopener">'
            f'<span class="amt-n">{n}</span><span class="amt-l">{l}</span></a>' for n, l in cards) + "</div>"

    btns = []
    if stripe:
        btns.append(f'<a class="btn btn-play" href="{esc(stripe)}" target="_blank" rel="noopener"><span>Give by Card</span></a>')
    if paypal:
        cls = "btn btn-goldline" if stripe else "btn btn-play"
        btns.append(f'<a class="{cls}" href="{esc(paypal)}" target="_blank" rel="noopener"><span>Give with PayPal</span></a>')
    cta = ('<div class="cta-row" style="justify-content:center">' + "".join(btns) + '</div>') if btns else ""

    inner = f"""{stream}
    <div class="support-card">
    <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
    <p class="prose" style="margin-bottom:0">Selah Sound Collective is a labour of love. What you give goes to God&rsquo;s Work, and to sending kids to camp &mdash; the ones who have earned a week away, and the ones whose families cannot get them there.</p>
    {amounts}
    {cta}
    <p class="support-note">Every gift, of any size, is received with deep gratitude.</p>
    </div>"""
    return content_page(site, root, "support", "Give", "Support the Work",
                        "Help keep the songs coming.", inner, "support.html")


def write_seo_files(site, songs):
    """sitemap.xml, robots.txt and llms.txt.

    llms.txt is for answer engines: a plain, factual summary they can quote.
    Structured data and a clean sitemap do the same job for classic search.
    """
    base = site.get("baseUrl", "").rstrip("/")
    if not base:
        return
    today = datetime.date.today().isoformat()
    live = [s for s in songs if s.get("status") == "published"]

    urls = [(f"{base}/", "1.0", "weekly"), (f"{base}/listen.html", "0.7", "monthly"),
            (f"{base}/about.html", "0.6", "monthly"), (f"{base}/support.html", "0.5", "monthly"),
            (f"{base}/contact.html", "0.4", "yearly")]
    urls += [(f"{base}/songs/{s['slug']}.html", "0.8", "monthly") for s in live]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri, freq in urls:
        sm.append(f"<url><loc>{esc(loc)}</loc><lastmod>{today}</lastmod>"
                  f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm))

    # Answer engines are how people will find this next; let them read it.
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\n"
        "# Answer engines are welcome to read and cite these pages.\n"
        "User-agent: GPTBot\nAllow: /\n\n"
        "User-agent: ClaudeBot\nAllow: /\n\n"
        "User-agent: PerplexityBot\nAllow: /\n\n"
        "User-agent: Google-Extended\nAllow: /\n\n"
        "User-agent: CCBot\nAllow: /\n\n"
        f"Sitemap: {base}/sitemap.xml\n")

    books = {}
    for s in live:
        b = s.get("book") or "Other"
        books[b] = books.get(b, 0) + 1
    psalms = books.get("Psalms", 0)
    lines = [f"# {site['siteName']}", "",
             f"> {site.get('description','')}", "",
             f"{site['siteName']} is a modern Christian music project that sets passages of the Bible to "
             f"original songs. The catalogue holds {len(live)} songs spanning "
             f"{len([b for b in books if b not in ('Standalone','Other')])} books of Scripture, "
             f"from Genesis to Revelation, including all 150 psalms set to music one by one.",
             "",
             "Every song streams free on the site with its full lyrics and the passage it is drawn from. "
             "The songs are also on Spotify, Apple Music, YouTube, Deezer and Amazon Music.",
             "",
             "Funds raised support God's Work and send children to camp.",
             "",
             "## Pages", "",
             f"- [Songs]({base}/): the full catalogue, filterable by testament and book",
             f"- [Listen]({base}/listen.html): streaming links",
             f"- [About]({base}/about.html): the project and the people behind it",
             f"- [Support]({base}/support.html): donations",
             f"- [Contact]({base}/contact.html): get in touch", "",
             "## Catalogue", ""]
    for s in sorted(live, key=lambda x: x["title"]):
        ref = (s.get("scripture") or s.get("epigraphRef") or "").strip()
        lines.append(f"- [{s['title']}]({base}/songs/{s['slug']}.html)"
                     + (f" \u2014 {ref}" if ref else ""))
    (OUT / "llms.txt").write_text("\n".join(lines) + "\n")
    print(f"  seo: sitemap.xml ({len(urls)} urls), robots.txt, llms.txt ({len(live)} songs, {psalms} psalms)")


def main():
    site = json.loads((DATA / "site.json").read_text())
    songs = [json.loads(p.read_text()) for p in sorted((DATA / "songs").glob("*.json"))]
    songs.sort(key=canon_key)

    # Rebuild docs/ — but never destroy audio we cannot regenerate. The mp3s are
    # large, so a clone of this repo may carry them only in docs/audio (src/audio
    # is optional). Wiping docs/ blindly would delete the only copy.
    remote_audio = bool((site.get("audioBaseUrl") or "").strip())
    src_audio = SRC / "audio"
    have_src_audio = src_audio.is_dir() and any(src_audio.glob("*.mp3"))
    if OUT.exists():
        for child in OUT.iterdir():
            if child.name == "audio" and not have_src_audio and not remote_audio:
                continue                       # keep the only copy of the music
            shutil.rmtree(child) if child.is_dir() else child.unlink()
    (OUT / "songs").mkdir(parents=True, exist_ok=True)
    shutil.copytree(SRC / "assets", OUT / "assets")
    shutil.copytree(SRC / "covers", OUT / "covers")
    if have_src_audio and not remote_audio:
        shutil.copytree(src_audio, OUT / "audio", dirs_exist_ok=True)

    # Cloudflare Pages: long-cache immutable media, short-cache pages
    # Cloudflare Pages: long-cache fingerprinted assets, always revalidate pages
    headers = ("/*\n  X-Content-Type-Options: nosniff\n  Cache-Control: public, max-age=0, must-revalidate\n"
               "/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n"
               "/covers/*\n  Cache-Control: public, max-age=31536000, immutable\n")
    if not remote_audio:
        headers += "/audio/*\n  Cache-Control: public, max-age=31536000, immutable\n"
    (OUT / "_headers").write_text(headers)

    (OUT / "index.html").write_text(render_library(site, songs, root=""))
    (OUT / "listen.html").write_text(render_listen(site, root=""))
    (OUT / "about.html").write_text(render_about(site, root=""))
    (OUT / "contact.html").write_text(render_contact(site, root=""))
    (OUT / "support.html").write_text(render_support(site, root=""))

    built = 0
    for s in songs:
        if s.get("status") == "published":
            (OUT / "songs" / f"{s['slug']}.html").write_text(render_song(site, s, root="../"))
            built += 1

    print(f"Built site -> {OUT}")
    print(f"  songs: {len(songs)} total, {built} published pages")
    write_seo_files(site, songs)
    print(f"  pages: index, about, contact, support + {built} song page(s)")


if __name__ == "__main__":
    main()
