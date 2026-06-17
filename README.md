# Twitch for Kodi — community fork

> ⚠️ **BETA — experimental, needs testing.**
> This is a personal fork that has been **tested only on LibreELEC 12.x / Kodi 21
> (Omega) / Raspberry Pi 4**. It is **untested on any other platform, OS or Kodi
> version** — use at your own risk. Provided as-is and not actively maintained.

A fork of **anxdpanic**'s Twitch addon for Kodi:

- [`plugin.video.twitch`](https://github.com/anxdpanic/plugin.video.twitch) — the addon (UI / routing / playback)
- [`script.module.python.twitch`](https://github.com/anxdpanic/script.module.python.twitch) — the Twitch API library

All credit for the original work goes to **anxdpanic** and the Twitch-on-Kodi
community. The library is in turn based on *python-twitch* by *ingwinlu*.
Licensed under **GPL-3.0-only** (see `LICENSE`); the original copyright headers
are kept intact.

## What this fork changes

- **HEVC / up to 2K** playback path (Raspberry Pi 4)
- **≥720p quality filter** (drops 160/360/480p)
- **OAuth Device Code login + automatic token refresh** (public client, no secret)
- **GraphQL search backend** (with Helix fallback)
- Optional **ad-free playback** via a private (Turbo) device login

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
4. In Kodi: *Twitch → Settings → Login* and paste it into **OAuth Client ID**
   (`oauth_clientid`).
5. Use **Login (Device Code)** and follow the on-screen code at
   <https://www.twitch.tv/activate>.

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
