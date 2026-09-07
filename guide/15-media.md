# Media: Streaming, Libraries, and Automation

Media serving is the gateway drug of self-hosting. A media server that streams your film collection to every TV and phone in the house, with cover art and resume-where-you-left-off and no monthly fee, is what convinces most people the whole hobby is worthwhile. It is also the category with the deepest tooling: the media servers themselves (Jellyfin, Plex, Emby), the automation stack that manages libraries (the *arr suite), request systems for the household (Jellyseerr), download clients and how to run them safely, hardware transcoding, and the adjacent categories of music (Navidrome), audiobooks and podcasts (Audiobookshelf), books and comics (Kavita, Komga, Calibre-Web), and library optimisation (Tdarr).

A note on legality up front: everything in this chapter is about serving media *you have the right to*. Ripped discs you own, purchased downloads, home videos, and legally free content are unambiguous. The automation tools are agnostic and are widely used for both legitimate and infringing purposes; [Chapter 30](30-legal-ethical.md) discusses the legal landscape. This guide describes the tools; what you feed them is your responsibility.

## Media servers

A media server scans directories of video/audio files, matches them against metadata databases (TMDB, TVDB, MusicBrainz) to fetch artwork and descriptions, and streams them to client apps — **direct playing** when the client can handle the file's codec and container, **transcoding** on the fly when it cannot (or when bandwidth is limited), with per-user libraries, watch history, and parental controls.

### Jellyfin

The fully free and open-source (GPL) media server, forked from Emby in 2018 when Emby went proprietary. No accounts, no subscriptions, no phone-home, no feature paywalls: hardware transcoding, multiple users, SyncPlay (watch together), live TV and DVR (with a tuner), plugins, a full API, and clients for web, Android, Android TV, iOS/tvOS (Swiftfin), Roku, Fire TV, LG webOS, Samsung Tizen, Kodi (via the Jellyfin for Kodi addon), and third-party clients (Infuse, Streamyfin, Findroid, Jellyfin Media Player for desktop). Development is community-driven and active; releases every few months.

**Strengths:** free forever, respects privacy, hardware transcoding on Intel QSV, NVIDIA NVENC, AMD VAAPI/AMF, and Apple VideoToolbox without any licence; excellent OIDC/LDAP via plugins; SyncPlay; an increasingly polished web client; trickplay (scrubbing thumbnails) built in; the *arr and request ecosystem treats it as a first-class target.

**Weaknesses:** client polish lags Plex on some platforms — the official iOS/tvOS client (Swiftfin) has matured but Infuse (paid, third-party) remains the best Apple experience; some smart-TV apps are community-maintained with variable quality; no hosted relay for remote access (you handle it — reverse proxy or VPN); metadata matching is good but occasionally needs manual fixing; no built-in "sharing with friends" beyond creating them a user account.

**Pick it if:** you want the free, open, no-strings option — which is most people reading this guide.

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    restart: unless-stopped
    user: 1000:1000
    group_add: ["render"]            # or the numeric GID of /dev/dri/renderD128 (getent group render)
    devices:
      - /dev/dri:/dev/dri            # Intel/AMD iGPU for hardware transcoding
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /mnt/data/media:/media:ro
    tmpfs:
      - /config/transcodes:size=8g   # keep transcode scratch off the SSD (optional)
    environment:
      JELLYFIN_PublishedServerUrl: https://jellyfin.example.com
    networks: [proxy]
    # For NVIDIA: install nvidia-container-toolkit and add
    # deploy: { resources: { reservations: { devices: [ { driver: nvidia, count: 1, capabilities: [gpu] } ] } } }
```

### Plex

The commercial incumbent, closed-source, with a free tier and **Plex Pass** (USD 5/month, USD 40/year, or USD 250 lifetime as of the 2025 price increase — lifetime is the only sensible purchase). Plex's strengths are exactly where Jellyfin is weakest: **client apps on every platform are polished and first-party**, including excellent smart-TV apps; **remote access "just works"** through Plex's relay/UPnP without you configuring a reverse proxy; **sharing** libraries with friends is a built-in feature with their own Plex accounts; metadata matching is very good; Plexamp is arguably the best music app of any kind; skip-intro, credits detection, and downloads for offline viewing are mature.

**The costs, plainly:** hardware transcoding, skip intro, downloads, and several other features require Plex Pass. As of 2025, **remote streaming requires Plex Pass** (or a per-user Remote Watch Pass) — a change that pushed many toward Jellyfin. Plex requires a plex.tv account and phones home constantly; when Plex's auth servers have outages, local playback has been affected (they added a local-auth fallback, but the dependency is real). Plex has been steadily adding ad-supported streaming content, "Discover" social features, and other things that a self-hoster did not ask for, and the free tier has been eroded over time. The company sells your viewing data in aggregate. It is a good product from a company whose incentives are not fully aligned with yours.

**Pick it if:** client polish and effortless sharing with non-technical friends matter more to you than openness, and you are willing to pay for and depend on a company.

### Emby

The proprietary middle option: the codebase Jellyfin forked from, still developed, with a free tier and **Emby Premiere** (USD 5/month, USD 54/year, USD 119 lifetime) required for hardware transcoding, mobile apps beyond a trial, and DVR. Client coverage is good (including smart TVs), the UI is clean, and it phones home less than Plex. It has neither Plex's ecosystem breadth nor Jellyfin's openness, and its community is far smaller. A reasonable product that most new users skip in favour of one of the other two.

### Comparison

| | Jellyfin | Plex | Emby |
|---|---|---|---|
| Licence | GPL (fully open) | Proprietary | Proprietary (source-available core, closed apps) |
| Cost | Free | Free tier; Plex Pass USD 250 lifetime | Free tier; Premiere USD 119 lifetime |
| Hardware transcoding | **Free** | Plex Pass | Premiere |
| Remote access | You configure (proxy/VPN) | Built-in relay; **now requires Plex Pass** | You configure |
| Account required | No | **Yes (plex.tv)** | Optional (Emby Connect) |
| Client quality (TVs/mobile) | Good, improving; Apple via Swiftfin/Infuse | **Excellent, first-party everywhere** | Good |
| Sharing with friends | Create user accounts | **Built-in, their own accounts** | Emby Connect |
| Music | Good (Finamp client; or use Navidrome) | **Plexamp (excellent)** | Good |
| Live TV / DVR | Free | Plex Pass | Premiere |
| SSO (OIDC/LDAP) | Plugins | No | No |
| Privacy | No telemetry | Telemetry, viewing data | Minimal |
| Best for | Most self-hosters | Non-technical households sharing widely | Neither camp |

Many people run **both** Jellyfin and Plex against the same library — Jellyfin for themselves, Plex for a parent who needs the Roku app to work with zero explanation. Read-only library mounts make this harmless.

## Hardware transcoding

Transcoding — decoding a video and re-encoding it in real time to a format or bitrate the client can handle — is the CPU-hungriest thing a home server does. A software transcode of a 4K HEVC stream can saturate eight cores; a hardware transcode on an Intel iGPU uses almost nothing. This is why [Chapter 2](02-hardware.md) insists on Intel Quick Sync.

**When transcoding happens:** the client cannot decode the codec (HEVC/H.265 on an older TV; AV1 on almost anything older than 2023); the container is unsupported (MKV in a browser → remux, which is cheap, or transcode); subtitles are image-based (PGS) and need burning in — this forces a *video* transcode and is the most common surprise; the audio codec is unsupported (TrueHD/DTS-HD on a phone → audio-only transcode, cheap); or the bandwidth setting on the client is below the file's bitrate (remote streaming).

**When it does not:** direct play. Most modern TVs and phones direct-play H.264 and HEVC in MP4/MKV with AAC/AC3 audio. A library encoded that way needs almost no transcoding. Tdarr (below) can normalise a library to that profile.

**Hardware options:**

| | Intel Quick Sync (iGPU / Arc) | NVIDIA NVENC | AMD VAAPI/AMF | Apple VideoToolbox |
|---|---|---|---|---|
| Simultaneous streams | 5–10+ on a modern iGPU; more on Arc | Consumer cards had a 3–5 session driver limit; **lifted to 8 in 2023**; patchable further | Several | Several |
| Codecs | H.264, HEVC, VP9, **AV1 (11th gen+, Arc)** encode/decode | H.264, HEVC, AV1 (40-series+) | H.264, HEVC, AV1 (RDNA 3+) | H.264, HEVC |
| Quality per bitrate | Very good (Arc: excellent) | Very good | Good, improving | Good |
| HDR → SDR tone mapping | Yes (OpenCL/VPP) | Yes | Yes | Yes |
| Idle power | ~0 (it's in the CPU) | 10–30 W for a discrete card | ~0 (iGPU) | n/a |
| Linux/Docker friction | **Lowest** (`/dev/dri`) | Medium (container toolkit) | Low–medium | Mac only |
| Cost | Included, or Arc A310 ~USD 100 | USD 150+ | Included | Mac |

**Recommendation:** an Intel CPU from 8th gen onward (10th+ for HEVC 10-bit, 11th+ for AV1 decode, Arc for AV1 encode) or an Arc A310/A380 in any machine. Pass `/dev/dri` into the container, add the `render` group, enable QSV in the server's transcoding settings, tick every codec the hardware supports, enable tone mapping, and test with a 4K HDR file on a phone. `intel_gpu_top` on the host shows the engine in use.

## The *arr automation stack

The "*arr" applications are a family of .NET tools that automate acquiring and organising media: you tell them what you want, they monitor indexers for it, send it to a download client, and when it arrives they rename it, move it into your library with a consistent naming scheme, and notify your media server to scan. They share a common UI lineage and configuration model.

- **Sonarr** — TV series. Monitors series, grabs episodes as they air (or the back catalogue), handles seasons, specials, upgrades to better quality.
- **Radarr** — films. Same model.
- **Lidarr** — music (albums/artists via MusicBrainz).
- **Readarr** — books and audiobooks (development stalled in 2024–2025; **Bookshelf** and others are forks; many users moved to Calibre-Web-Automated's book downloader or LazyLibrarian).
- **Prowlarr** — the **indexer manager**: configure your indexers (Usenet indexers, torrent trackers, public indexers) *once* here and it syncs them to every other *arr. Replaced Jackett for most people (Jackett is still maintained and Prowlarr can use it as a fallback).
- **Bazarr** — subtitles: watches Sonarr/Radarr libraries and fetches subtitles from OpenSubtitles, Subscene alternatives, and others in your languages.
- **Whisparr** (adult content), **Mylar3** (comics), **Kapowarr** (comics), **Lidarr** alternatives (**Headphones**, **Bliss** for tagging).
- **Recyclarr** — syncs **TRaSH Guides** quality profiles and custom formats into Sonarr/Radarr, so your quality preferences (prefer x265 web-dl, avoid low-quality groups, score HDR correctly) are expert-maintained rather than hand-built.
- **Unpackerr** — extracts archived downloads so the *arrs can import them.
- **Autobrr** — IRC announce-based grabbing for private trackers; niche, powerful.
- **Huntarr**, **Cleanuparr**, **Decluttarr** — newer helpers that hunt missing items or clean stalled downloads.
- **Maintainerr** — rules-based library cleanup ("delete films nobody has watched in 6 months and that were requested via Jellyseerr").

**The single most important setup concept is the TRaSH Guides folder structure.** All *arrs and the download client must see the *same* filesystem path for downloads and media so that imports are **hardlinks** (instant, no extra space, seeding continues) rather than copies. That means one bind mount — `/mnt/data:/data` — into every container, with `/data/torrents/{movies,tv}`, `/data/usenet/{movies,tv}`, and `/data/media/{movies,tv,music}` underneath, all on the *same filesystem*. Two separate mounts (`/downloads` and `/movies`) force copies and double your disk usage. TRaSH Guides (trash-guides.info) is the canonical reference for *arr configuration and should be read before setting anything up.

```yaml
# media/compose.yaml (excerpt — the pattern, not every option)
x-arr: &arr
  restart: unless-stopped
  environment:
    PUID: "1000"
    PGID: "1000"
    TZ: Europe/London
  networks: [proxy, default]

services:
  prowlarr:
    <<: *arr
    image: lscr.io/linuxserver/prowlarr:latest
    volumes: ["./config/prowlarr:/config"]
  sonarr:
    <<: *arr
    image: lscr.io/linuxserver/sonarr:latest
    volumes: ["./config/sonarr:/config", "/mnt/data:/data"]
  radarr:
    <<: *arr
    image: lscr.io/linuxserver/radarr:latest
    volumes: ["./config/radarr:/config", "/mnt/data:/data"]
  bazarr:
    <<: *arr
    image: lscr.io/linuxserver/bazarr:latest
    volumes: ["./config/bazarr:/config", "/mnt/data/media:/data/media"]
  recyclarr:
    image: ghcr.io/recyclarr/recyclarr:latest
    restart: unless-stopped
    user: 1000:1000
    volumes: ["./config/recyclarr:/config"]
    environment: { TZ: Europe/London }
```

## Requests: Jellyseerr, Overseerr, Ombi

Your household should not need to log into Radarr. A **request system** gives them a Netflix-like browse-and-request UI: search for a film, click request, it goes to Radarr, and they get a notification when it is available.

- **Jellyseerr** — the fork of Overseerr with Jellyfin and Emby support (and Plex). Users log in with their Jellyfin account; per-user quotas and approval rules; notifications via email, Discord, Telegram, ntfy, Gotify, webhooks; a discover page with trending/popular; watchlist sync. **The standard choice** for Jellyfin users and works fine with Plex too.
- **Overseerr** — the original, Plex-only. Still excellent; Jellyseerr has superseded it for most.
- **Ombi** — the older, more configurable request system with Plex/Emby/Jellyfin support, music requests via Lidarr, and a more dated UI. Still maintained.
- **Seerr** — the 2025 reunification: Overseerr and Jellyseerr merging into one project. Watch for it.
- **Doplarr**, **Requestrr** — Discord bots for requests.
- **Wizarr** — invitation and onboarding for new users: sends them a link, creates their Jellyfin/Plex account, walks them through installing the apps and Jellyseerr. Lovely for sharing with family.
