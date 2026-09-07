# AGENT NOTES — READ THIS FIRST AFTER ANY CONTEXT COMPACTION

This file is the single source of truth for the state of this project. It exists because
the agentic session can be interrupted (credits) or compacted (context) at any moment.
**Every future instance must read this file first, then `git log --oneline | head -30`, then continue.**

## The task (verbatim intent from user)

> Create the best possible, the most comprehensive and detailed and in-depth review/guide on
> services to self host on one's home lab and everything related to it. Final deliverable is
> an MD doc and a web adaptation of it.

Constraints from the user:
- Push straight to `main` on GitHub after every meaningful unit of work. **No branches, no PRs.**
- Document reasoning here so a compacted-context instance can continue with minimal degradation.
- Remote: `https://github.com/gorg667/self-host-guide.git` (credentials already configured via
  `setup_github_environment`; re-run that tool if `git push` fails with auth error).

## Session-start checklist (do this every time)

1. `cd /home/user/webapp && git status && git log --oneline | head`
2. `pip install -q markdown pymdown-extensions` — the sandbox may have been reset; build.py exits early without these.
3. If `git push` fails on auth, call the `setup_github_environment` tool.
4. Read the STATUS table below; continue with the first unchecked chapter.
5. A chapter that was being written when the session died is LOST unless it is on disk — always check `ls guide/`.

## Repository layout

```
/home/user/webapp
├── AGENT_NOTES.md          <- this file (status, plan, conventions)
├── README.md               <- public-facing readme
├── build.py                <- builds SELF-HOSTING-GUIDE.md + docs/ static site from guide/*.md
├── guide/                  <- SOURCE OF TRUTH. One Markdown file per chapter, numeric prefix = order
│   ├── 00-introduction.md
│   ├── 01-planning.md
│   └── ...
├── site/                   <- web adaptation assets (template.html, style.css, app.js) used by build.py
├── docs/                   <- GENERATED static site (GitHub Pages serves from /docs on main). Committed.
└── SELF-HOSTING-GUIDE.md   <- GENERATED single-file Markdown deliverable. Committed.
```

Workflow per chapter:
1. Write/extend `guide/NN-slug.md`.
2. `cd /home/user/webapp && python3 build.py` (regenerates SELF-HOSTING-GUIDE.md and docs/).
3. `git add -A && git commit -m "docs(guide): <chapter> ..." && git push origin main`.
4. Update the status table below and push again (can be folded into the same commit).

## Chapter conventions

- Each chapter file starts with a single `# Title` H1. build.py uses it for nav. No other H1s in file.
- Use `##` for major sections, `###` for subsections, `####` sparingly.
- Every *service* review follows this mini-template where it makes sense:
  - **What it is** (1–2 sentences), **Why you'd pick it**, **Watch out for**, **Resources** (RAM/CPU rough),
    **Minimal docker-compose** (fenced ```yaml), **Alternatives** (comparison table where useful).
- Admonitions: python-markdown `admonition` syntax: `!!! tip "Title"` / `!!! warning` / `!!! note` / `!!! danger`.
  Indent the body by 4 spaces. build.py renders these to styled callouts; in the raw .md they still read fine.
- Tables: standard GFM pipe tables.
- Diagrams: fenced ```mermaid blocks (rendered client-side in the web version; readable as text in MD).
- Cross-links between chapters: link to `NN-slug.md` relative (e.g. `[Backups](11-backups.md)`).
  build.py rewrites `NN-slug.md` -> `../NN-slug/` for the site and to in-document anchors for the single MD.
- Tone: expert, opinionated but fair, practical. State versions/dates as "as of 2026" where relevant.
  Prefer concrete numbers (watts, GB RAM, ports) over vagueness. No fluff, no emoji.
- Length target: 2,500–6,000 words per chapter. Depth beats breadth within a chapter; breadth is achieved by the
  number of chapters.

## Master outline and STATUS

Legend: `[ ]` not started · `[~]` draft/partial · `[x]` complete (first full pass) · `[R]` reviewed/polished

### Part I — Foundations
- [x] 00-introduction.md — What self-hosting is, why, who this is for, philosophy, how to use the guide, responsibilities
- [x] 01-planning.md — Goals, tiers (starter/intermediate/advanced), budget, power/noise/space, requirements, 3-2-1 mindset
- [x] 02-hardware.md — Mini PCs, used enterprise, SBCs, NAS, DIY builds, drives (CMR/SMR, NAS drives), RAM/ECC, NICs, switches, UPS, racks, GPUs
- [x] 03-networking.md — IP/subnets, VLANs, DHCP/DNS, NAT/port forwarding, CGNAT, IPv6, firewalls, router OS (OPNsense/pfSense/OpenWrt/UniFi/MikroTik), segmentation
- [x] 04-os-and-hypervisors.md — Proxmox VE, TrueNAS SCALE, Unraid, Debian/Ubuntu, NixOS, XCP-ng, Harvester; LXC vs VM; comparison matrix; Proxmox install walkthrough
- [x] 05-containers.md — Docker, Compose, Podman, k3s/Talos/microk8s; best practices; updates (Watchtower/Diun/Renovate); patterns
- [x] 06-storage.md — ZFS deep dive, Btrfs, mdadm/LVM, MergerFS+SnapRAID, Ceph, NFS/SMB/iSCSI, SMART, capacity planning

### Part II — Core infrastructure services
- [x] 07-reverse-proxy-tls.md — NPM, Traefik, Caddy, Nginx, HAProxy, Pangolin, SWAG; Let's Encrypt DNS-01, wildcard, internal CA, split DNS
- [x] 08-remote-access-vpn.md — WireGuard, Tailscale/Headscale, Netbird, ZeroTier, OpenVPN, Cloudflare Tunnel, Pangolin; CGNAT; VPS relay
- [x] 09-dns-adblock.md — Pi-hole, AdGuard Home, Blocky, Technitium, Unbound, DoH/DoT, local records, HA DNS
- [ ] 10-identity-sso.md — Authelia, Authentik, Keycloak, Zitadel, Pocket ID, LLDAP, Kanidm; forward-auth; OIDC; passkeys
- [ ] 11-backups.md — 3-2-1, Restic, Borg, Kopia, Duplicati, PBS, ZFS replication (sanoid/syncoid), rclone, B2/Storage Box, restore testing, DB dumps
- [ ] 12-monitoring.md — Prometheus/Grafana, Uptime Kuma, Gatus, Netdata, Beszel, Loki, Dozzle, Zabbix, Scrutiny, ntfy/Gotify/Apprise, Healthchecks
- [ ] 13-security.md — Threat model, SSH, fail2ban, CrowdSec, firewalls, Docker hardening, secrets, Wazuh, checklists

### Part III — Application services (reviews by category)
- [ ] 14-dashboards.md — Homepage, Homarr, Dashy, Glance, Heimdall, Organizr, Flame
- [ ] 15-media.md — Jellyfin/Plex/Emby, *arr stack, Jellyseerr, download clients + Gluetun, transcoding (QSV/NVENC/VAAPI), Navidrome, Audiobookshelf, Kavita/Komga, Tdarr
- [ ] 16-photos.md — Immich, PhotoPrism, Nextcloud Memories, Lychee, Ente, LibrePhotos
- [ ] 17-files-sync-documents.md — Nextcloud, Seafile, Syncthing, OpenCloud/oCIS, FileBrowser, Copyparty, Paperless-ngx, Stirling PDF, OnlyOffice/Collabora, file sharing
- [ ] 18-notes-productivity.md — Obsidian LiveSync, Joplin, Trilium, Outline, BookStack, Wiki.js, Memos, SilverBullet, AFFiNE, Hedgedoc; Vikunja/Planka; Radicale/Baikal; Linkwarden/Linkding/Karakeep/Wallabag; FreshRSS/Miniflux
- [ ] 19-home-automation.md — Home Assistant, Zigbee2MQTT/ZHA, Z-Wave JS, Mosquitto, Node-RED, ESPHome, Frigate, Scrypted, Homebridge, Matter, Music Assistant
- [ ] 20-communication.md — Matrix (Synapse/Conduit/Tuwunel), Rocket.Chat, Mattermost, XMPP, Jitsi, Mumble; self-hosted email (Mailcow/Mailu/Stalwart/docker-mailserver) with caveats
- [ ] 21-passwords-secrets.md — Vaultwarden, Bitwarden, Passbolt, KeePassXC+Syncthing, Psono, Infisical, OpenBao, 2FAuth
- [ ] 22-dev-git-automation.md — Gitea/Forgejo/GitLab, Woodpecker/Gitea Actions, Harbor, code-server/Coder, Portainer/Dockge/Komodo, n8n/Windmill/Activepieces, it-tools
- [ ] 23-ai-llm.md — Ollama, Open WebUI, LocalAI, llama.cpp, vLLM, ComfyUI/SD, Whisper/Speaches, Piper/Kokoro, SearXNG/Perplexica, LibreChat, AnythingLLM; GPU/VRAM sizing, quantization
- [ ] 24-gaming.md — Pterodactyl/Pelican, Crafty, PufferPanel, AMP, itzg Minecraft, RomM, Gaseous, EmulatorJS, Sunshine/Moonlight
- [ ] 25-misc-apps.md — Recipes (Mealie/Tandoor), Grocy, finance (Firefly III/Actual/Ghostfolio/Wallos), inventory (Homebox), Speedtest Tracker, ChangeDetection, Invidious, analytics (Umami/Plausible/Matomo), blogging (Ghost/WordPress/Hugo), URL shorteners, Excalidraw, Cal.com, DocuSeal, etc.
- [ ] 26-databases-backing-services.md — PostgreSQL, MariaDB, Redis/Valkey, MongoDB, SQLite; pgAdmin/Adminer; object storage (Garage/SeaweedFS/MinIO); message queues

### Part IV — Operations
- [ ] 27-automation-iac.md — Ansible, Terraform/OpenTofu + Proxmox, cloud-init, NixOS, Renovate, GitOps (Komodo, Flux/ArgoCD)
- [ ] 28-maintenance-operations.md — Update cadence, pinning, runbooks, documentation, disaster drills, bus factor
- [ ] 29-power-cost-environment.md — Measuring watts, cost calc, idle tuning (powertop/C-states/ASPM), spin-down, heat/noise, UPS + NUT
- [ ] 30-legal-ethical.md — Licensing (OSS vs source-available), hosting for family, copyright, ISP ToS, GDPR-lite
- [ ] 31-reference-architectures.md — Starter / Intermediate / Advanced blueprints with Mermaid diagrams + full compose stacks
- [ ] 32-troubleshooting-faq.md — Common failures & fixes, FAQ
- [ ] 33-resources-community.md — Communities, creators, wikis, newsletters
- [ ] 34-appendix.md — Glossary, port reference, checklists, compose cheat-sheet

### Build system / web adaptation
- [x] build.py (concat + static site) — implemented and tested
- [x] site/template.html, site/style.css, site/app.js (sidebar nav, per-page TOC, search, dark mode, mermaid, copy buttons)
- [x] README.md
- [x] docs/ generated (regenerated on every build)

## Decisions & reasoning log

- **2026-09-07**: Chose plain python-markdown + custom template over MkDocs/Docusaurus so the build has zero
  network/npm dependency and remains trivially reproducible after interruption. `pip install markdown pymdown-extensions`
  is the only requirement (build.py falls back gracefully if pymdownx missing).
- **2026-09-07**: One file per chapter so that each push is a complete, useful increment. Single-file MD is generated,
  never hand-edited.
- **2026-09-07**: docs/ is committed (not built in CI) so the site is live on GitHub Pages immediately after push
  without any Actions config. If GitHub Pages is not enabled, user enables it: Settings → Pages → Deploy from branch →
  main → /docs.
- **2026-09-07**: Dates: the environment date is 2026-09-07. Write "as of 2026" for version-sensitive claims and avoid
  hyper-specific version numbers that will rot; prefer describing stable characteristics of projects.
- **2026-09-07**: Priority order for writing: skeleton/build first (so the deliverable exists early), then Part I and II
  (foundations + infra are most valuable), then Part III (service reviews — the "review" heart of the guide), then Part IV.
  If interrupted, whatever exists is already a coherent, published guide.

## Next steps (keep this current!)

1. Create build.py + site/ template, README.md, and a stub 00-introduction.md; run build; push. (Deliverable exists early.)
2. Write chapters in order 00 → 34. After each chapter: build, commit, push, tick the box above.
3. When all chapters are done: consistency pass on cross-links, then polish.
4. User action eventually: enable GitHub Pages (Settings → Pages → main → /docs).
