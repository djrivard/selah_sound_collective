# Selah Sound Collective — site

A small, data-driven static site for the Selah Sound Collective song catalog.
One template + one record per song. No frameworks, no build dependencies —
just Python 3.

## What's here

```
build.py              the generator — run it to (re)build the site
data/
  site.json           site-wide settings (name, donate links, contact form…)
  songs/*.json        one file per song
src/
  assets/             site.css, player.js, site.js  (shared by every page)
  covers/             cover images (one per song + _coming-soon.jpg)
  audio/              song mp3s
tools/
  convert_musixmatch.py   turn a Musixmatch transcript into lyric JSON
docs/                 ← THE GENERATED SITE (deploy this folder)
```

## Build it

```
python3 build.py
```

That regenerates everything into `docs/`.

## Deploy on Cloudflare Pages (recommended)

One-time setup:
1. Push this whole folder to a GitHub repo.
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages →
   Connect to Git**, pick the repo.
3. Build settings: **Framework preset: None · Build command: (leave empty) ·
   Build output directory: `docs`**. Save and Deploy.
4. Your site goes live at `https://<project>.pages.dev`. Add your custom
   domain (e.g. selahsoundcollective.com) under the project's
   **Custom domains** tab — Cloudflare handles the DNS and certificate.

After that, every `git push` redeploys automatically: edit data, run
`python3 build.py`, commit, push — live in about a minute.

(The generated `docs/_headers` file gives audio and covers long CDN
caching on Cloudflare automatically. If you ever outgrow the repo-size
comfort zone for audio, the mp3s can move to Cloudflare R2 and the
`"audio"` fields become full URLs — nothing else changes.)

### GitHub Pages still works too

Settings → Pages → Source: main branch, `/docs` folder. Same output.

## Add a new song (the whole loop)

1. Put the cover in `src/covers/` (e.g. `psalm-100.jpg`) and the audio in
   `src/audio/` (e.g. `psalm-100.mp3`).
2. Make `data/songs/psalm-100.json` modeled on an existing record.
   Set `"status": "published"`.
   - **Lyrics without timing yet?** Use `null` for every line's time:
     `[null, "The line of the lyric"]`. The page shows the full lyric
     sheet and the player works — it just doesn't highlight lines yet.
3. When the Musixmatch timing is ready:
   ```
   python3 tools/convert_musixmatch.py pasted.txt
   ```
   and swap the `null`s for the printed times (or paste its `sections`
   and re-split into Verse / Chorus labels).
4. `python3 build.py` — the library, song page, filter chips, and nav all
   update automatically.

A song with `"status": "coming-soon"` shows as a greyed "Coming soon" card
with no page — handy for teasing what's next.

## Settings to fill in (`data/site.json`)

- `baseUrl` — your live address (e.g. `https://selah-site.pages.dev` or
  your custom domain); used for share links and social previews
- `contactFormEndpoint` — your Formspree form URL (free at formspree.io)
- `contactEmail` — direct-email fallback on the contact page
- `donateUrl` — your Stripe Payment Link
- `donatePaypal` — your PayPal donate link (optional)
