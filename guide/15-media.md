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

## Download clients and the VPN sidecar

### Torrent clients

- **qBittorrent** — the community default: full-featured web UI, categories (which the *arrs use to route downloads), RSS, sequential download, IP filtering, an API that everything integrates with. The **VueTorrent** alternative web UI is worth enabling. LinuxServer and hotio images are both well maintained.
- **Deluge** — older, plugin-based, lighter; a fine alternative.
- **Transmission** — minimal, extremely light, the choice for Raspberry Pis and NAS appliances; fewer features.
- **rTorrent/ruTorrent** — the power-user classic, common on seedboxes; more setup.
- **Flood** — a modern web UI that fronts rTorrent, qBittorrent, Deluge, or Transmission.

### Usenet clients

- **SABnzbd** — the standard: fast, reliable, categories, post-processing, good API. Pair with one or two Usenet providers (paid, ~USD 3–10/month) and indexers (some free, most ~USD 10–20/year). Usenet is direct-download over SSL from a provider, so no VPN is needed for privacy and speeds are line-rate.
- **NZBGet** — lighter (C++), the choice for low-power hardware; development resumed under new maintainers in 2023.

### Gluetun: the VPN sidecar pattern

Torrent traffic should go through a VPN if you value your ISP not knowing what you download and not receiving notices. The clean way is **Gluetun** — a container that connects to a commercial VPN provider (Mullvad, ProtonVPN, AirVPN, Private Internet Access, Surfshark, Windscribe, and dozens more, plus any WireGuard or OpenVPN config) with a **kill switch** built in: if the VPN drops, *nothing* can reach the internet. Other containers join its network namespace and inherit the tunnel:

```yaml
services:
  gluetun:
    image: qmcgaw/gluetun:latest
    container_name: gluetun
    restart: unless-stopped
    cap_add: [NET_ADMIN]
    devices: ["/dev/net/tun:/dev/net/tun"]
    environment:
      VPN_SERVICE_PROVIDER: mullvad
      VPN_TYPE: wireguard
      WIREGUARD_PRIVATE_KEY: ${MULLVAD_KEY}
      WIREGUARD_ADDRESSES: ${MULLVAD_ADDR}
      SERVER_CITIES: Amsterdam
      FIREWALL_OUTBOUND_SUBNETS: 10.0.0.0/8      # let the *arrs on the LAN reach qBittorrent's API
      VPN_PORT_FORWARDING: "on"                  # providers that support it (ProtonVPN, AirVPN, PIA)
    ports:
      - "127.0.0.1:8080:8080"                    # qBittorrent web UI is published HERE, on gluetun
    volumes: ["./gluetun:/gluetun"]
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    restart: unless-stopped
    network_mode: "service:gluetun"              # all traffic via the VPN or not at all
    depends_on: [gluetun]
    environment: { PUID: "1000", PGID: "1000", TZ: Europe/London, WEBUI_PORT: "8080" }
    volumes:
      - ./config/qbittorrent:/config
      - /mnt/data/torrents:/data/torrents
```

The *arrs reach qBittorrent at `http://gluetun:8080` (the Gluetun container's name, since qBittorrent has no network of its own). For **port forwarding** (which dramatically improves torrent connectivity), pick a provider that supports it — Mullvad dropped it in 2023; **ProtonVPN**, **AirVPN**, and **PIA** support it, and Gluetun can update qBittorrent's listening port automatically for some providers (or a small script does it). Verify the tunnel is working: `docker exec gluetun wget -qO- ifconfig.me` should show the VPN's IP; a torrent IP-check tool (ipleak.net's torrent test) confirms qBittorrent's announced IP.

**Seedboxes** — a rented server at a hosting company that downloads and seeds on your behalf, synced home via rsync/Syncthing/FTP — are the alternative for people who want the traffic off their home connection entirely; ~USD 5–20/month.

## Music

**Navidrome** is the standard self-hosted music server: light (Go, ~50 MB RAM), fast scanning of large libraries, a clean web player, multi-user with per-user play counts and favourites, Last.fm/ListenBrainz scrobbling, smart playlists, and — critically — the **Subsonic API**, which means dozens of excellent mobile and desktop clients: **Symfonium** (Android, the best), **DSub**, **Ultrasonic**, **Tempo**, **play:Sub** and **Amperfy** and **Substreamer** (iOS), **Feishin** and **Sonixd** (desktop), **Supersonic**. Navidrome has no transcoding UI drama, no metadata editing (it reads tags — fix them with **MusicBrainz Picard** or **beets** first), and just works.

Alternatives: **Jellyfin** itself with the **Finamp** client (good, and one fewer service); **Plexamp** if you are in Plex; **Airsonic-Advanced** and **Gonic** (other Subsonic servers); **Funkwhale** (federated, social, heavier); **Koel**, **Ampache**, **mStream**, **Black Candy**; **LMS** (Lightweight Music Server); **Mopidy/Snapcast** for multi-room playback; **Lidarr** upstream for acquisition; **beets** for library management and tagging. **Music Assistant** (a Home Assistant companion) bridges local libraries and streaming services to speakers around the house ([Chapter 19](19-home-automation.md)).

## Audiobooks and podcasts

**Audiobookshelf** has become the definitive self-hosted audiobook and podcast server: a beautiful web UI, per-user progress sync, chapters, playback speed, sleep timer, bookmarks, metadata from Audible/Google Books/OpenLibrary, podcast subscriptions with automatic downloading and episode management, ebook reading (EPUB/PDF/comics) in the browser, multi-library, and first-rate mobile apps (official Android/iOS, plus **Plappa** and **ShelfPlayer** on iOS). Easy to run, actively developed, and universally recommended. Pair with **Readarr** or **LazyLibrarian** for acquisition if you want automation.

For podcasts specifically, **AntennaPod** (Android app, with **gPodder.net** or **Nextcloud gPodder** sync) is a client-side alternative; **Podgrab** and **Podfetch** are minimal podcast downloaders; Audiobookshelf covers the same ground better.

## Books and comics

- **Kavita** — a fast, modern reader-server for manga, comics, and ebooks (EPUB, PDF, CBZ/CBR) with per-user progress, series metadata, collections, reading lists, and a good web reader plus OPDS for external apps. The best all-rounder if you read both books and comics.
- **Komga** — the comics/manga specialist (CBZ/CBR/PDF/EPUB), with strong metadata handling (ComicInfo.xml), OPDS, and the **Komf** metadata fetcher. Rock solid; **Mihon/Tachiyomi** (Android) and **Panels** (iOS) connect to it.
- **Calibre-Web** — a web UI for a Calibre library: browse, read EPUBs in the browser, send to Kindle by email, OPDS, per-user shelves. **Calibre-Web Automated** (CWA) adds an ingest folder that auto-converts and imports new books and a built-in book downloader — the current favourite for people who want the Calibre database with automation.
- **Calibre** itself (the desktop app, optionally served via **calibre-server** or a **Calibre in Docker** with a web VNC) remains the best tool for *managing and converting* ebooks; the web front-ends are for *reading and serving*.
- **BookLore** (2025, a modern all-in-one with metadata, reading, and OPDS), **Kapowarr** and **Mylar3** (comics acquisition), **Suwayomi/Tachidesk** (manga source aggregator), **Stump**, **Codex**, **Ubooquity** (older).
- Readers: **KOReader** on e-ink devices talks OPDS to any of the above and syncs progress; **Moon+ Reader** and **Librera** on Android; **Yomu** and **Panels** on iOS.

## Library optimisation: Tdarr and friends

**Tdarr** is a distributed transcoding system for *normalising a library*: define a flow ("if not HEVC → transcode to HEVC with QSV at CRF 22; strip non-English audio; remove image subtitles; remux to MKV") and it processes every file, using one or many worker nodes with hardware acceleration. Reduces library size by 30–60% and eliminates most on-the-fly transcoding by making everything direct-playable. Runs as a server + nodes; the flow editor takes learning; **Unmanic** is a simpler alternative; **FileFlows** is a more general file-processing pipeline. All three want a GPU and a long weekend for a large library. Be aware that re-encoding is lossy — many people choose to keep original remuxes for films they care about and transcode only TV.

## Library management and stats

**Jellystat** (Jellyfin statistics — who watched what, popular content, playback methods), **Tautulli** (the Plex equivalent, long-established, with notifications like "new episode added" and per-user history), **Streamystats**, **Jellyfin-Vue**/**Jellyfin Enhanced** (alternative front-ends), **Intro Skipper** (Jellyfin plugin for skip-intro, now maintained separately), **Kometa** (formerly Plex Meta Manager — collection and overlay automation for Plex, with Jellyfin support arriving), **Posterizarr** and **Posterr** (artwork), **Checkrr** (finds corrupt files), **Duplicacy**-style **dedupe** tools, **Radarr/Sonarr Trakt lists** for automation from Trakt watchlists, **Ryot** and **Yamtrack** (self-hosted Trakt/Letterboxd/Goodreads-style tracking across media types).

## Recommendations

- **Server:** Jellyfin. Add Plex alongside only if a specific non-technical viewer needs it.
- **Hardware:** Intel iGPU (8th gen+) or Arc A310. Pass `/dev/dri`.
- **Automation:** Prowlarr + Sonarr + Radarr + Bazarr + Recyclarr, all seeing `/mnt/data:/data`, hardlinks working (check with `stat` — link count > 1 after import). Read TRaSH Guides first.
- **Download:** qBittorrent behind Gluetun with a port-forwarding VPN provider; SABnzbd for Usenet (no VPN needed).
- **Requests:** Jellyseerr (or Seerr), with Wizarr for onboarding.
- **Music:** Navidrome + Symfonium/Amperfy; **Audiobooks/podcasts:** Audiobookshelf; **Books/comics:** Kavita (or Komga + Calibre-Web Automated).
- **Optimisation:** Tdarr once the library is large and the transcoding load is real — not before.

## Checklist

- [ ] Media on a filesystem with redundancy; classified as replaceable (or not) and backed up accordingly ([Chapter 11](11-backups.md)).
- [ ] One data mount into every media container; hardlinks verified.
- [ ] Hardware transcoding enabled and tested with a 4K HDR file on a phone; tone mapping on.
- [ ] Jellyfin/Plex reachable via the reverse proxy with a valid certificate; remote users via VPN or an exposed, rate-limited, CrowdSec-guarded proxy — never a raw forwarded 8096/32400.
- [ ] Torrent client cannot reach the internet except via the VPN (kill switch verified by stopping Gluetun and checking).
- [ ] *arr web UIs behind forward-auth or VPN-only; their API paths bypassed for the mobile companions.
- [ ] Quality profiles from TRaSH via Recyclarr; naming schemes consistent.
- [ ] Household onboarded via Wizarr; requests via Jellyseerr; nobody but you logs into Radarr.
