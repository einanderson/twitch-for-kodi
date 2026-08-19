# Twitch for Kodi — community fork

> ℹ️ **Everything up to v3.0.3 is upstream — this repo continues as a 4.x line.**
> The 3.x feature set of this fork (OAuth device-code login, Turbo/ad-free login,
> GQL search, HEVC codec setting, search & tofu fixes, ISA improvements) was merged
> into the original addon and released as
> **[anxdpanic v3.0.3](https://github.com/anxdpanic/plugin.video.twitch/releases/tag/v3.0.3)**.
> **If you want the maintained, general-purpose addon, use upstream.** The 4.x
> releases here are a personal, opinionated line that trades features for a
> deterministic playback path — see *Limitations* below before installing.

> ⚠️ **Experimental — tested only on LibreELEC 12.x / Kodi 21 (Omega) /
> Raspberry Pi 4** with InputStream Adaptive 21.5. **Untested on any other
> platform, OS or Kodi version.** Provided as-is, not actively maintained.

A fork of **anxdpanic**'s Twitch addon for Kodi:

- [`plugin.video.twitch`](https://github.com/anxdpanic/plugin.video.twitch) — the addon (UI / routing / playback)
- [`script.module.python.twitch`](https://github.com/anxdpanic/script.module.python.twitch) — the Twitch API library

All credit for the original work goes to **anxdpanic** and the Twitch-on-Kodi
community. The library is in turn based on *python-twitch* by *ingwinlu*.
Licensed under **GPL-3.0-only** (see `LICENSE`); the original copyright headers
are kept intact.

## What this fork changes

- **Deterministic 2K/HEVC start, with audio.** Twitch mixes one HEVC source variant
  into the H.264 transcode ladder and shuffles the variant order per request, so Kodi
  started sometimes in 1080p, sometimes in 2K, and a manual codec switch ended in a
  black screen. The addon now rewrites the master playlist before handing it to
  InputStream Adaptive: if a HEVC variant of 720p or better exists, only HEVC video is
  kept.
- **No more random silent starts.** The audio tracks ISA synthesizes from the muxed
  variants never deliver packets (no child-audio playlist is ever fetched, no
  "Creating audio stream" appears in the log) — audible sound always comes from the
  separate `audio_only` variant. `mp4a` is therefore stripped from the CODECS of every
  video variant, leaving `audio_only` as the single real audio track. This applies to
  **all** streams, not just HEVC ones.
- **Adaptive-only playback.** Live streams and VODs always play through InputStream
  Adaptive; clips remain a direct MP4 at source quality.
- **OAuth Device Code login + automatic token refresh** (public client, no secret)
- **GraphQL search backend** (with Helix fallback)
- Optional **ad-free playback** via a private (Turbo) device login

## Limitations — please read before installing

- **There is no quality selection any more.** Preferred/default quality, the quality
  dialog, per-channel defaults, bandwidth and frame-rate limits and the "use ISA"
  toggle were all removed in 4.0.0. Quality is left to InputStream Adaptive (capped at
  1440p). If you want to pick qualities by hand, use the upstream addon.
- **The addon runs a small local HTTP service** on `127.0.0.1:48664` while Kodi is
  running. It serves nothing but the rewritten playlist to ISA on the loopback
  interface — ISA insists on a real HTTP status line, so a local file or a direct
  media playlist does not work. If anything in the rewrite fails, playback silently
  falls back to the unmodified Twitch URL.
- **Install the bundled library, not just the plugin.** This fork builds on upstream
  3.0.3, and HEVC is offered to Twitch inside `script.module.python.twitch` — the
  plugin itself never requests a codec. With a stock library the rewrite finds no HEVC
  variant and you simply get H.264; the audio fix still applies either way.
- Tested on one hardware/OS combination only (see the warning at the top).

## Installation (sideload)

Both folders are Kodi addons. Copy them into your Kodi `addons/` directory and
enable them in Kodi (install the **library first**, then the plugin):

1. `script.module.python.twitch/`  → `…/.kodi/addons/script.module.python.twitch/`
2. `plugin.video.twitch/`          → `…/.kodi/addons/plugin.video.twitch/`
3. In Kodi: *Add-ons → My add-ons → Video add-ons → Twitch → Enable*.

On LibreELEC the addons directory is `/storage/.kodi/addons/`.

### Alternative: install from zip

Pre-built zips are attached to the [latest release](../../releases/latest). In
Kodi use *Add-ons → Install from zip file* and install the **library first**:

1. `script.module.python.twitch-*.zip` (the API library dependency)
2. `plugin.video.twitch-*.zip` (the addon)

(Building yourself: `python3 build.py` writes the same zips into `dist/`.)

## Login (required)

Anonymous playback does **not** work — Twitch requires a logged-in token to hand
out a usable playback access token. This fork therefore needs **your own free
Twitch application** (the bundled upstream client cannot refresh tokens):

1. Go to <https://dev.twitch.tv/console> → *Applications* → **Register Your Application**.
2. Name: anything. OAuth Redirect URL: `http://localhost`. Category: *Application Integration*.
   Client Type: **Public** (so no client secret is needed; this enables the OAuth
   Device Code flow).
3. Copy the **Client ID**.
4. In Kodi: *Twitch → Settings → Developer* and paste it into **OAuth Client ID**
   (`oauth_clientid`).
5. *Twitch → Settings → Login* → **Login (Device Code)**, then follow the on-screen
   code at <https://www.twitch.tv/activate>.

Since 4.0.2 the order of steps 4 and 5 no longer matters: changing the Client ID
discards any token issued for the previous one, so you are simply asked to log in
again. Earlier versions could get stuck in a loop here (upstream issue #712).

**The login is required for the addon to work at all — not just for playback.**
Twitch's Helix API needs an OAuth token on *every* request; with only a Client-ID
it returns `401 Unauthorized`. This fork ships no app token (it has no client
secret), so until you log in there is no usable token and even browsing (top
games, channels, search) fails. After login, browsing and playback both work.

### Optional: ad-free playback

A separate **private (kimne78/Turbo) device login** is available in the settings
for ad-free playback if you have Twitch Turbo or relevant subscriptions. This is
optional and independent of the normal login above.

## License

GPL-3.0-only. See [`LICENSE`](LICENSE).
