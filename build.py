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
import json, shutil, pathlib, html

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


def head(site, title, desc, root, og_image=None, canonical=None, extra=""):
    og = og_image or site.get("ogImage", "")
    bits = [
        '<!DOCTYPE html><html lang="en"><head>',
        '<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
    ]
    if og:
        bits.append(f'<meta property="og:image" content="{esc(og)}">')
    if canonical:
        bits.append(f'<meta property="og:url" content="{esc(canonical)}">')
        bits.append(f'<link rel="canonical" href="{esc(canonical)}">')
    bits.append('<meta name="twitter:card" content="summary_large_image">')
    bits.append(f'<meta name="twitter:title" content="{esc(title)}">')
    if og:
        bits.append(f'<meta name="twitter:image" content="{esc(og)}">')
    bits.append(FONTS)
    bits.append(f'<link rel="stylesheet" href="{root}assets/site.css">')
    bits.append(extra)
    bits.append("</head>")
    return "".join(bits)


def nav(site, root, active=""):
    items = [("Songs", "index.html", "songs"), ("About", "about.html", "about"),
             ("Contact", "contact.html", "contact"), ("Support", "support.html", "support")]
    links = "".join(
        f'<a href="{root}{href}"{" class=\"active\"" if active==key else ""}>{label}</a>'
        for label, href, key in items)
    return (f'<header class="nav"><div class="nav-wrap">'
            f'<a class="brand" href="{root}index.html">{esc(site["siteName"])}</a>'
            f'<button class="nav-toggle" id="navToggle" aria-label="Menu">&#9776;</button>'
            f'<nav class="nav-links" id="navLinks">{links}</nav></div></header>')


def footer(site, root):
    items = [("Songs", "index.html"), ("About", "about.html"),
             ("Contact", "contact.html"), ("Support", "support.html")]
    links = "".join(f'<a href="{root}{href}">{label}</a>' for label, href in items)
    return (f'<footer class="site-footer"><a class="brand" href="{root}index.html">{esc(site["siteName"])}</a>'
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


def render_song(site, song, root="../"):
    cover = song["cover"]
    title = song["title"]
    full_title = f'{title} \u2014 {site["siteName"]}'
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/songs/{song['slug']}.html" if base else None
    og_image = f"{base}/covers/{cover}" if base else None
    cover_style = f"<style>:root{{--cover:url('{root}covers/{esc(cover)}')}}</style>"
    h = head(site, full_title, site.get("description", ""), root,
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
        sources += f'<source src="{root}audio/{esc(song["audio"])}" type="audio/mpeg">'
    if song.get("audioFallback"):
        sources += f'<source src="{esc(song["audioFallback"])}" type="audio/mpeg">'

    spotify_cta = (f'<a class="btn btn-spotify" id="spotifyLink" href="{esc(spotify)}" target="_blank" rel="noopener">'
                   f'<svg viewBox="0 0 24 24"><path d="{SPOTIFY}"/></svg> Listen on Spotify</a>') if spotify else ""
    spotify_nb = (f'<a class="nb-spotify" href="{esc(spotify)}" target="_blank" rel="noopener" '
                  f'title="Listen on Spotify" aria-label="Listen on Spotify"><svg viewBox="0 0 24 24">'
                  f'<path d="{SPOTIFY}"/></svg></a>') if spotify else ""

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
    <div class="style-note">{esc(song.get("styleNote",""))}</div>
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
<script src="{root}assets/site.js"></script>
<script src="{root}assets/player.js"></script>
</body></html>"""
    return h + body


def render_library(site, songs, root=""):
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/index.html" if base else None
    h = head(site, f'{site["siteName"]} \u2014 Songs', site.get("description", ""), root,
             canonical=canonical)
    books = sorted({s.get("book", "") for s in songs if s.get("book")})
    chips = '<button class="chip on" data-book="all">All</button>' + "".join(
        f'<button class="chip" data-book="{esc(b)}">{esc(b)}</button>' for b in books)

    cards = []
    for s in songs:
        soon = s.get("status") != "published"
        cover = s.get("cover", "_coming-soon.jpg")
        inner = (f'<div class="card-cover">'
                 f'<img class="card-img" src="{root}covers/{esc(cover)}" alt="{esc(s["title"])} cover" loading="lazy">'
                 f'<div class="scrim"></div>'
                 + ('<span class="badge">Coming soon</span>' if soon else
                    '<span class="play-dot"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>')
                 + '</div>'
                 f'<div class="card-meta"><div class="card-title">{esc(s["title"])}</div>'
                 f'<div class="card-scrip">{esc(s.get("scripture",""))}</div></div>')
        attrs = f'data-title="{esc(s["title"])}" data-book="{esc(s.get("book",""))}"'
        if soon:
            cards.append(f'<div class="song-card soon" {attrs}>{inner}</div>')
        else:
            cards.append(f'<a class="song-card" href="{root}songs/{esc(s["slug"])}.html" {attrs}>{inner}</a>')

    body = f"""<body>
<div class="page-bg"></div>
{nav(site, root, "songs")}
<main class="page">
  <div class="page-head">
    <div class="eyebrow">The Catalog</div>
    <h1>Songs</h1>
    <p class="lede">{esc(site.get("tagline",""))}</p>
    <div class="rule"></div>
  </div>
  <div class="filterbar">
    <input class="lib-search" id="libSearch" type="search" placeholder="Search songs&hellip;" aria-label="Search songs">
    <div class="chips">{chips}</div>
  </div>
  <div class="lib-grid" id="libGrid">
    {"".join(cards)}
  </div>
  <div class="lib-empty" id="libEmpty">No songs match that search yet.</div>
</main>
{footer(site, root)}
<script src="{root}assets/site.js"></script>
</body></html>"""
    return h + body


def content_page(site, root, active, eyebrow, title, lede, inner_html, canonical_name):
    base = site.get("baseUrl", "").rstrip("/")
    canonical = f"{base}/{canonical_name}" if base else None
    h = head(site, f'{title} \u2014 {site["siteName"]}', site.get("description", ""), root, canonical=canonical)
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
<script src="{root}assets/site.js"></script>
</body></html>"""
    return h + body


def render_about(site, root=""):
    inner = """<div class="prose">
    <p>Selah Sound Collective began with a simple conviction: that the oldest stories still have the power to move us, and that music is one of the truest ways to carry them. Each song here takes a passage of Scripture &mdash; a vow, a psalm, a moment of deliverance &mdash; and gives it a melody you can sit inside.</p>
    <p class="scripture">&ldquo;Speak to one another with psalms, hymns, and songs from the Spirit.&rdquo;</p>
    <p>These are cinematic settings: soft pianos that swell into something grand, voices that carry the weight of the words. They&rsquo;re made to be listened to slowly &mdash; with the lyrics in front of you, and the story unfolding line by line.</p>
    <p>Thank you for listening, and for sharing them with the people you love.</p>
    </div>"""
    return content_page(site, root, "about", "The Project", "About", site.get("tagline", ""), inner, "about.html")


def render_contact(site, root=""):
    endpoint = site.get("contactFormEndpoint", "#")
    email = site.get("contactEmail", "")
    mail_alt = (f'<p class="form-alt">Or email us directly at <a href="mailto:{esc(email)}">{esc(email)}</a>.</p>'
                if email else "")
    inner = f"""<form class="form" action="{esc(endpoint)}" method="POST">
    <div class="field"><label for="name">Your name</label><input id="name" name="name" type="text" required></div>
    <div class="field"><label for="email">Email</label><input id="email" name="email" type="email" required></div>
    <div class="field"><label for="message">Message</label><textarea id="message" name="message" required></textarea></div>
    <button class="btn btn-play" type="submit"><span>Send Message</span></button>
    </form>
    {mail_alt}"""
    return content_page(site, root, "contact", "Get in Touch", "Contact",
                        "Questions, song requests, or just a hello \u2014 we\u2019d love to hear from you.",
                        inner, "contact.html")


def render_support(site, root=""):
    donate = site.get("donateUrl", "#")
    paypal = site.get("donatePaypal", "")
    amounts = site.get("donateAmounts", [])
    amt_html = "".join(f'<a class="amount" href="{esc(donate)}" target="_blank" rel="noopener">{esc(a)}</a>'
                       for a in amounts)
    paypal_html = (f'<a class="btn btn-spotify" href="{esc(paypal)}" target="_blank" rel="noopener" '
                   f'style="border-color:rgba(201,164,70,.5)">Give with PayPal</a>') if paypal else ""
    inner = f"""<div class="support-card">
    <span class="tick tl"></span><span class="tick tr"></span><span class="tick bl"></span><span class="tick br"></span>
    <p class="prose" style="margin-bottom:0">Selah Sound Collective is a labour of love. If these songs have meant something to you, your gift helps cover production, distribution, and the making of the next one.</p>
    <div class="amount-row">{amt_html}</div>
    <div class="cta-row" style="justify-content:center">
      <a class="btn btn-play" href="{esc(donate)}" target="_blank" rel="noopener"><span>Support the Work</span></a>
      {paypal_html}
    </div>
    <p class="support-note">Every gift, of any size, is received with deep gratitude. Thank you for helping the music continue.</p>
    </div>"""
    return content_page(site, root, "support", "Give", "Support the Work",
                        "Help keep the songs coming.", inner, "support.html")


def main():
    site = json.loads((DATA / "site.json").read_text())
    songs = [json.loads(p.read_text()) for p in sorted((DATA / "songs").glob("*.json"))]
    songs.sort(key=lambda s: (s.get("status") != "published", s.get("book", ""), s.get("title", "")))

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "songs").mkdir(parents=True)
    shutil.copytree(SRC / "assets", OUT / "assets")
    shutil.copytree(SRC / "covers", OUT / "covers")
    if (SRC / "audio").exists():
        shutil.copytree(SRC / "audio", OUT / "audio")

    # Cloudflare Pages: long-cache immutable media, short-cache pages
    (OUT / "_headers").write_text(
        "/audio/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/covers/*\n  Cache-Control: public, max-age=31536000, immutable\n"
        "/assets/*\n  Cache-Control: public, max-age=86400\n"
        "/*\n  X-Content-Type-Options: nosniff\n")

    (OUT / "index.html").write_text(render_library(site, songs, root=""))
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
    print(f"  pages: index, about, contact, support + {built} song page(s)")


if __name__ == "__main__":
    main()
