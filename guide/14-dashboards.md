# Dashboards and Start Pages

Once you have fifteen services, you have fifteen URLs to remember, and your family has none of them memorised. A dashboard — a single page listing every service with an icon, a link, and ideally a live status or a useful widget — is the fix. It is also the first thing most self-hosters build, because it is satisfying and the payoff is immediate. This chapter compares Homepage, Homarr, Glance, Dashy, Heimdall, Flame, Organizr, and a few others, and offers guidance on making a dashboard that people actually use.

## What a dashboard is for

Two distinct audiences, and it is worth being honest about which you are building for:

**You, the operator.** You want density: every service, status indicators, container health, disk usage, download queue, the *arr calendar, Proxmox node load, Pi-hole block percentage, links to admin panels. Widgets that pull live data from APIs. A dark theme. Keyboard shortcuts.

**The household.** They want five big buttons — Photos, Films, Files, Recipes, Home — that work, and nothing that looks like a server room. No admin links, no status noise, ideally a friendly name and an icon per service.

The best setups run **two dashboards** (or two views of one): an operator page at `home.example.com` with everything, and a family page at `start.example.com` with the essentials. Several of the tools below support per-group visibility to do this from one instance.

## The candidates

### Homepage

The current community favourite (`gethomepage.dev`). Configured entirely by **YAML files** (`services.yaml`, `widgets.yaml`, `bookmarks.yaml`, `settings.yaml`), with a fast, clean, information-dense UI. Its defining feature is **service widgets**: 100+ integrations that show live data next to a service's link — Sonarr/Radarr queue and wanted counts, Jellyfin/Plex now-playing, Immich photo counts, Pi-hole/AdGuard stats, Proxmox node CPU/RAM, TrueNAS pool status, Uptime Kuma incidents, qBittorrent speeds, Home Assistant entity states, Gitea, Nextcloud, Paperless, Vaultwarden (via a proxy), Portainer, Traefik, Tailscale, weather, calendars, and more. **Docker integration**: point it at the socket (via a socket proxy, please) and it shows container status and can auto-discover services from container labels (`homepage.group`, `homepage.name`, `homepage.icon`, `homepage.href`), so a new stack appears on the dashboard without editing YAML. Icons via the **Dashboard Icons** project (thousands of service logos by name: `icon: jellyfin.png`) or Material Design Icons / Simple Icons.

**Strengths:** the widget ecosystem is unmatched; YAML in Git; auto-discovery via labels; light (~100 MB); actively developed with frequent releases; supports multiple "layouts" and per-group column control; a `HOMEPAGE_ALLOWED_HOSTS` setting for security.

**Weaknesses:** YAML editing is the *only* configuration method — no UI editor (this is a feature for some); widget API keys live in the config files (use `{{HOMEPAGE_VAR_*}}` environment substitution and `.env`); the many-widgets page hammers a dozen APIs every few seconds, which is fine at home; no built-in authentication or per-user views (put it behind forward-auth and run two instances for two audiences).

```yaml
# homepage/compose.yaml
services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: homepage
    restart: unless-stopped
    environment:
      HOMEPAGE_ALLOWED_HOSTS: home.example.com
      HOMEPAGE_VAR_SONARR_KEY: ${SONARR_KEY}
    volumes:
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock:ro   # or a socket proxy: DOCKER_HOST=tcp://socket-proxy:2375
    networks: [proxy]
```

```yaml
# homepage/config/services.yaml
- Media:
    - Jellyfin:
        icon: jellyfin.png
        href: https://jellyfin.example.com
        description: Films and TV
        widget:
          type: jellyfin
          url: http://jellyfin:8096
          key: {{HOMEPAGE_VAR_JELLYFIN_KEY}}
          enableBlocks: true
    - Sonarr:
        icon: sonarr.png
        href: https://sonarr.example.com
        widget:
          type: sonarr
          url: http://sonarr:8989
          key: {{HOMEPAGE_VAR_SONARR_KEY}}
- Infrastructure:
    - Proxmox:
        icon: proxmox.png
        href: https://pve.example.com:8006
        widget:
          type: proxmox
          url: https://10.0.20.2:8006
          username: api@pam!homepage
          password: {{HOMEPAGE_VAR_PVE_TOKEN}}
```

### Homarr

The **UI-configured** counterpart: drag-and-drop tile layout, an in-browser editor for everything, built-in **user accounts and groups with per-board permissions** (so the family sees one board and you see another, from one instance), integrations for the *arr stack, media servers, Pi-hole/AdGuard, Docker, Proxmox, Home Assistant, Dash. (system stats), Uptime Kuma, and more, plus widgets for calendars, weather, RSS, notebooks, iframes, and a Docker container manager. Since the 1.0 rewrite (2025) it is a polished, capable product with OIDC login support.

**Strengths:** no YAML required; multi-user with per-board access is exactly the operator/family split; looks great; drag-and-drop layouts; OIDC.

**Weaknesses:** heavier (~300–500 MB with its database); configuration lives in a database, not files — back it up and accept it is not in Git; fewer integrations than Homepage's widget list, though the important ones are present; the 0.x → 1.0 migration was disruptive.

**Pick Homarr if:** you want a UI and per-user boards. **Pick Homepage if:** you want YAML and the deepest widget catalogue.

### Glance

A 2024 arrival with a different philosophy: a **personal start page** rather than a service launcher. YAML-configured (like Homepage) but oriented around feeds and information — RSS, Reddit, Hacker News, YouTube channels, Twitch, weather, stocks/crypto, calendar, releases from GitHub repos, Docker container status, server stats (via a small agent), a "monitor" widget for service uptime, bookmarks, iframes, custom API widgets with templating, and multiple pages. Extremely light (a single Go binary, ~20 MB), fast, and beautiful in a restrained way.

**Pick it if:** you want your browser's new-tab page to be a self-hosted dashboard that mixes your services with the things you read. It is less a Homepage competitor than a complement — some people run both.

### Dashy

Configured by YAML *or* a built-in UI editor (which writes the YAML), with a huge feature list: status checks per item, widgets (many overlap with Homepage's), themes (dozens), icon packs, multi-page, search with keyboard shortcuts, authentication (basic, Keycloak, forward-auth headers) with per-user item visibility, and a cloud backup/restore feature. Vue-based.

**Strengths:** the most configurable *look*; UI editor for those who want it plus YAML for those who do not; built-in auth and per-user visibility.

**Weaknesses:** heavier front-end; development has slowed relative to Homepage/Homarr; widget freshness lags; occasional rough edges. A good tool that has been overtaken in mind-share.

### Heimdall

The classic (LinuxServer.io). A simple grid of tiles with "enhanced" apps that show a stat or two (Sonarr queue, Pi-hole blocks, Nextcloud users) via a built-in list of supported apps, a UI for adding items, user accounts, and a search bar. It does exactly one thing and has done it reliably since 2018.

**Pick it if:** you want a five-minute setup with a UI and do not care about deep widgets. It is the right "family dashboard" for many people precisely because it is simple.

### Flame

A minimalist start page with a UI editor: applications, bookmarks, a search bar, weather, themes, and Docker label auto-discovery. No widgets. Light and pleasant. Development has been sporadic. **Simple Icons**-style. If you want "links, tidy, nothing else," Flame or Heimdall.

### Organizr

An older, different beast: a **tabbed iframe container** that loads your services *inside* the dashboard page, with user roles, per-tab access, and an HTTP auth backend that lets Nginx/Traefik use Organizr as an auth gate (`auth_request`). Popular in the Plex/*arr community for years as an all-in-one portal. Iframes are increasingly blocked by apps' security headers (`X-Frame-Options`), which limits it; PHP-based. Still maintained; a niche choice.

### Others

**Fenrus**, **Mafl**, **Hiccup**, **LinkStack** (link-in-bio, not a dashboard), **Sui** / **Startpage**-style static pages, **Portall**, **Dashboard Icons** (not a dashboard — the icon repository everything uses), **Homer** (a single YAML file rendered as a static page — no backend at all, the lightest possible option, and it can be served from any web server), **Hajimari** (Kubernetes-focused), **Gethomepage**'s many forks, **Umbrel/CasaOS** home screens (bundled with those platforms; [Chapter 4](04-os-and-hypervisors.md)).

## Comparison

| | Homepage | Homarr | Glance | Dashy | Heimdall | Homer |
|---|---|---|---|---|---|---|
| Configuration | YAML | UI | YAML | YAML + UI | UI | YAML (static) |
| Service widgets | **100+** | ~40 | Docker, monitor, custom API | Many | Basic "enhanced" apps | None (static) |
| Docker auto-discovery | **Yes (labels)** | Yes | Container status | Partial | No | No |
| Multi-user / per-user views | No (run two) | **Yes** | No | Yes | Basic | No |
| Auth | External (forward-auth) | Built-in + OIDC | External | Built-in + headers | Built-in | External |
| Feeds/RSS | Limited | Yes | **Yes (core)** | Yes | No | No |
| RAM | ~100 MB | ~400 MB | ~20 MB | ~150 MB | ~100 MB | ~0 (static) |
| Best for | Operators wanting data density in Git | Households wanting UI + per-user boards | Personal start page with feeds | Themes + UI editor + auth | Simplest family page | Zero-backend static page |

## Making a dashboard people use

- **Two audiences, two views.** Operator page with everything; family page with 5–10 large tiles, friendly names ("Photos," not "Immich"), and no admin links. Homarr's boards, Dashy's per-user visibility, or two Homepage instances.
- **Icons matter.** The Dashboard Icons project has nearly everything; consistent iconography makes a page scannable.
- **Status, not noise.** A green/red dot per service is useful. Twelve live graphs are not, on the family page.
- **Set it as the browser home page** on family devices and as the new-tab page on yours. A dashboard nobody opens is decoration.
- **Search.** Homepage, Homarr, Dashy, and Glance all support a search bar with provider shortcuts (`!g` for Google, `!yt`) — configure it to hit your **SearXNG** ([Chapter 23](23-ai-llm.md)) and it becomes a genuinely useful start page.
- **Protect it.** The dashboard reveals your entire service inventory and often holds API keys. Behind the reverse proxy, forward-auth or at least LAN/VPN-only, never public.
- **Socket proxy for Docker integration.** Every dashboard that reads container status wants the Docker socket. Give it a read-only socket proxy ([Chapter 13](13-security.md)).
- **Keep it in Git** if it is YAML. The dashboard is documentation of what you run.

## Recommendation

**Homepage** for the operator view — the widget depth and YAML-in-Git are decisive. **Homarr** if you want one instance serving both audiences with per-board permissions and a UI, or if you simply prefer clicking. **Heimdall** or **Homer** for a family page that must never be fiddled with. **Glance** as a personal new-tab page if you read feeds. Any of them takes under an hour to set up and is among the most-used pages in your lab from then on.
