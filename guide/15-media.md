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
