# Resources and Community

No guide stays current for long in this space. Projects fork, licences change, a new reverse proxy becomes fashionable every eighteen months. What *does* stay useful is knowing where the reliable information lives, who explains things well, and how to evaluate a project before you trust it with your data. This chapter is that map: directories, communities, documentation you should actually read, creators worth your time, newsletters, and a short checklist for judging a project's health. Nothing here is sponsored; everything here has been useful to real self-hosters for years.

!!! note "Link rot is inevitable"
    Names are given alongside URLs so you can search when a link dies. Where a project has a canonical home (GitHub org, docs site), that is preferred over third-party mirrors.

## Software directories

Start here when you know *what* you want to do but not *which* project does it.

| Directory | URL | What it's good for |
|---|---|---|
| **awesome-selfhosted** | github.com/awesome-selfhosted/awesome-selfhosted · awesome-selfhosted.net | The canonical list. Categorised, licence-tagged, actively curated with strict inclusion rules (must be actively maintained, must be self-hostable). The website version is filterable |
| **selfh.st apps** | selfh.st/apps | Curated, searchable, with icons, GitHub stars, last-release dates. Companion to the selfh.st newsletter |
| **Awesome-Sysadmin** | github.com/awesome-foss/awesome-sysadmin | Infra-side tooling: monitoring, backup, config management |
| **awesome-docker-compose** / **Haxxnet Compose-Examples** | github.com/Haxxnet/Compose-Examples | Hundreds of working compose files with Traefik labels; great for "how do others run X" |
| **LinuxServer.io** | linuxserver.io · docs.linuxserver.io | Consistent, well-documented images for ~200 apps with PUID/PGID conventions; the fleet page lists everything |
| **Proxmox VE Helper-Scripts** | community-scripts.github.io/ProxmoxVE | One-line LXC/VM creators for ~300 apps. Read the script before running it, as with anything `curl | bash` |
| **AlternativeTo** / **European Alternatives** | alternativeto.net · european-alternatives.eu | "What replaces Google Photos?" style discovery, including non-self-hosted options |
| **Privacy Guides** | privacyguides.org | Vetted recommendations with reasoning; overlaps with self-hosting on VPN, DNS, passwords, email |
| **OpenAlternative** | openalternative.co | Open-source alternatives to SaaS, with health metrics |
| **Selfhosted Show wiki** / **r/selfhosted wiki** | reddit.com/r/selfhosted/wiki | Community FAQ, beginner links |
| **Docker Hub / GHCR / Quay** | hub.docker.com · ghcr.io | Check pull counts, tag history and whether the image is *official*, *verified* or random |

## Communities

Where to ask, lurk and learn. Each has a personality.

| Community | Where | Personality & etiquette |
|---|---|---|
| **r/selfhosted** | reddit.com/r/selfhosted | Largest general community (~500k). Weekly "what are you running" threads, project announcements, lots of beginners. Search before posting; read the wiki. Tolerant of newbies, allergic to ads |
| **r/homelab** / **r/HomeServer** / **r/minilab** | reddit | Hardware-heavy. r/homelab loves racks and eBay enterprise gear; r/HomeServer is more practical; r/minilab is small-form-factor |
| **r/Proxmox**, **r/truenas**, **r/unRAID**, **r/DataHoarder**, **r/zfs**, **r/docker**, **r/Traefik**, **r/homeassistant**, **r/jellyfin**, **r/immich** | reddit | Per-project subs; devs often read them. r/DataHoarder for disk deals and storage philosophy |
| **Lemmy: selfhosted@lemmy.world**, **selfhost@lemmy.ml**, **homelab@lemmy.ml** | lemmy.world / lemmy.ml | The federated Reddit alternative; smaller, technical, very friendly; good if you left Reddit in 2023 |
| **Self-Hosted Podcast Discord** / **selfh.st Discord** | invite via selfhosted.show / selfh.st | Active chat, project maintainers present |
| **LinuxServer.io Discord/Discourse** | discord.gg/YWrKVTn · discourse.linuxserver.io | Support for their images; very responsive |
| **Level1Techs forum** | forum.level1techs.com | Hardware, ZFS, virtualisation; Wendell's community, high signal |
| **ServeTheHome forum** | forums.servethehome.com | Enterprise-ish hardware, "TinyMiniMicro" thread, NIC/HBA deep dives, great for used-gear questions |
| **Proxmox forum** | forum.proxmox.com | Official; staff answer. Search first — most questions are duplicates |
| **TrueNAS forum** | forums.truenas.com | Official; strong opinions on ZFS best practice |
| **Unraid forum** | forums.unraid.net | Official; Community Apps discussions |
| **Home Assistant Community** | community.home-assistant.io | Enormous, well-moderated, integration-specific threads |
| **Matrix rooms** | #selfhosted:matrix.org and per-project rooms (Immich, Nextcloud, Jellyfin, Authelia…) | Real-time, decentralised, often where developers actually hang out |
| **Hacker News** | news.ycombinator.com | "Show HN" launches of new self-hosted tools; skeptical, useful comment threads |
| **Stack Exchange: Server Fault, Unix & Linux, Super User** | *.stackexchange.com | For precise technical questions with reproducible detail |
| **Project GitHub Discussions / Issues** | per project | The most authoritative place; search closed issues for your exact error |

How to ask well: state goal, environment (host OS, Docker version, how you deployed), exact error text, the relevant compose/config with secrets removed, what you already tried and what changed recently. Format code as code. Say thanks and post the fix when you find it — the next person searching will bless you.

## Documentation worth reading end to end

Most people skim docs. These are worth an evening each and will save you weeks.

| Document | Why |
|---|---|
| **Docker docs: Compose specification, networking, storage** — docs.docker.com | Understand `networks`, bind vs volume, `user:`, healthchecks and you'll debug 80 % of container issues without asking |
| **Traefik docs (Routing & Load Balancing, Middlewares, Let's Encrypt)** — doc.traefik.io | Dense but precise; the "Docker provider" page explains labels properly |
| **Caddy docs (Caddyfile concepts, reverse_proxy, Automatic HTTPS)** — caddyserver.com/docs | Short and excellent; the Caddyfile tutorial takes 30 minutes |
| **OpenZFS docs & Aaron Toponce's ZFS series** — openzfs.github.io/openzfs-docs · pthree.org/2012/04/17/install-zfs-on-debian-gnulinux | The Toponce series is old but the mental model is timeless (vdevs, ARC, snapshots) |
| **Proxmox VE Administration Guide** — pve.proxmox.com/pve-docs | The PDF is 500 pages; read Storage, Backup, Cluster, PCI passthrough chapters |
| **Proxmox Backup Server docs** — pbs.proxmox.com/docs | Especially Datastore, Prune & GC, Verification, Sync jobs |
| **Tailscale docs & KB** — tailscale.com/kb | Model documentation; subnet routers, exit nodes, MagicDNS, ACLs are all explained with diagrams |
| **WireGuard whitepaper & Quick Start** — wireguard.com | The whitepaper is readable and explains why it's simple |
| **Let's Encrypt: Challenge Types, Rate Limits, Chain of Trust** — letsencrypt.org/docs | Understand DNS-01 vs HTTP-01 and the rate limits before you hit them |
| **Restic docs / Borg docs / Kopia docs** — restic.readthedocs.io · borgbackup.readthedocs.io · kopia.io/docs | Read the "Removing snapshots" and "Repository format/encryption" sections; know how to restore before you need to |
| **Authelia / Authentik / Pocket ID docs** | OIDC concepts, forward-auth headers, and per-app integration guides (Authentik's integrations list is huge) |
| **Immich docs (Install, Backup & Restore, Hardware Transcoding, ML)** — immich.app/docs | Read *before* every update; the release notes are mandatory |
| **Nextcloud Admin Manual (Server tuning, Background jobs, Reverse proxy)** — docs.nextcloud.com | Most "Nextcloud is slow" complaints are a skipped chapter |
| **Home Assistant docs (Installation methods, Networking, Reverse proxy)** — home-assistant.io/docs | Understand HAOS vs Container vs Core before choosing |
| **Arch Wiki** — wiki.archlinux.org | Distro-agnostic gold for systemd, networking, PipeWire, disks, power management |
| **Debian Administrator's Handbook** — debian-handbook.info | Free; the fundamentals of the OS most of this runs on |
| **Mozilla SSL Configuration Generator / SSL Labs** — ssl-config.mozilla.org · ssllabs.com/ssltest | Sensible TLS defaults and a way to test public endpoints |
| **OWASP Docker Security Cheat Sheet** — cheatsheetseries.owasp.org | The security baseline for containers in one page |
| **NIST SP 800-63B (Digital Identity)** | Why passkeys/2FA matter and how to think about authenticator strength |
| **Backblaze Drive Stats** — backblaze.com/cloud-storage/resources/hard-drive-test-data | Real failure rates by model; published quarterly |

## Blogs and creators

Quality over quantity. All of these show their work.

### Written

| Author / site | Focus |
|---|---|
| **selfh.st (Ethan Sholly)** | Weekly roundup of releases, new apps, community content; the best single feed for staying current |
| **noted.lol** | Reviews and how-tos of self-hosted apps, honest about rough edges |
| **mariushosting** | Synology-centric Docker guides; hundreds of step-by-step tutorials |
| **ServeTheHome (Patrick Kennedy)** | Hardware reviews, the "Project TinyMiniMicro" series on 1L PCs, NICs, switches, power measurements |
| **Wolfgang's Channel blog / notthebee** | Low-power builds and ZFS; measured idle-power tables |
| **Jeff Geerling** | Raspberry Pi, Ansible (he wrote *Ansible for DevOps*), homelab experiments; rigorous |
| **Wolfgang, Louwrentius (Blog Louwrentius)** | Storage and ZFS deep dives; 71 TiB build write-ups |
| **Jim Salter (Ars Technica, jrs-s.net)** | ZFS explained properly; Sanoid/Syncoid author |
| **Chris Titus Tech, Christian Lempa (blog)** | Practical Linux/Docker/Proxmox tutorials |
| **smallstep blog, Scott Helme (scotthelme.co.uk)** | TLS, PKI, HTTP security headers |
| **Julia Evans (jvns.ca)** | Networking, DNS, Linux fundamentals as comics/zines; *How DNS Works* is the best DNS primer anywhere |
| **Michael Stapelberg** | Router7, gokrazy, Go-based homelab infrastructure; meticulous |
| **Ben Cox (blog.benjojo.co.uk), Cloudflare blog, Tailscale blog** | Networking internals; the Tailscale NAT traversal post is essential reading |
| **Awesome Selfhosted blog / AlternativeTo blog** | Project comparisons |
| **DB-Tech, Techno Tim (docs.technotim.live)** | Written companions to their videos; Techno Tim's docs repo has all his configs |

### Video

| Channel | Focus |
|---|---|
| **Techno Tim** | Homelab, Kubernetes, Proxmox, Traefik; clear and structured; all configs on GitHub |
| **Christian Lempa** | Docker, Proxmox, security, Traefik, Authentik; teaches concepts, not just clicks |
| **Wolfgang's Channel** | Low-power NAS builds, Jellyfin, Immich; measured, no hype |
| **Hardware Haven** | Budget/used hardware for homelab, honest reviews |
| **Jeff Geerling** | Pi, Ansible, NAS builds, weird hardware experiments |
| **NetworkChuck** | Entertaining intros; good for enthusiasm, verify details elsewhere |
| **Lawrence Systems (Tom Lawrence)** | pfSense/OPNsense, TrueNAS, UniFi, business-grade networking explained for home users; very thorough |
| **Craft Computing** | Proxmox, GPU passthrough, enterprise hardware, cloud gaming |
| **DB Tech** | Fast Docker app walkthroughs; high volume, so pick the ones you need |
| **Raid Owl, Jim's Garage, Novaspirit Tech, The Digital Life** | Practical homelab builds and app setups |
| **Level1Techs (Wendell)** | Deep hardware, ZFS, Linux; long-form |
| **apalrd's adventures** | Proxmox, networking, VLANs, Ceph — very technical |
| **Home Network Guy** | OPNsense, VLANs, Omada/UniFi; step-by-step |
| **Everything Smart Home, Smart Home Solver, The Hook Up** | Home Assistant and devices, with actual testing |
| **Awesome Open Source** | Ten-minute overviews of a project a week |

### Podcasts

| Podcast | Notes |
|---|---|
| **Self-Hosted (Jupiter Broadcasting)** | Alex Kretzschmar & Chris Fisher; the community's flagship show; app picks, Home Assistant, hardware |
| **2.5 Admins** | Allan Jude, Jim Salter, Joe Ressington; ZFS, sysadmin war stories, news |
| **Linux Unplugged**, **Late Night Linux**, **Ask Noah** | Broader Linux; frequent self-hosting segments |
| **Selfhosted Show / Homelab Show** | Interviews with maintainers |
| **The Homelab Show** | Tom Lawrence & Jay LaCroix; networking and infra |
| **Darknet Diaries** | Security storytelling; motivational for locking things down |

## Newsletters and feeds

- **selfh.st Weekly** — the one to subscribe to.
- **This Week in Self-Hosted** (r/selfhosted stickied / selfh.st) — release notes roundup.
- **Console.dev** — weekly two-tool newsletter for developers; many self-hostable finds.
- **TLDR / TLDR DevOps** — broader, but flags new infra tools.
- **Changelog Nightly** — trending GitHub repos.
- **Awesome-Selfhosted commits feed** — watch the repo to see additions.
- **GitHub Releases RSS** for the projects you run: `https://github.com/<org>/<repo>/releases.atom` into Miniflux/FreshRSS — the most reliable way to learn about breaking changes before Renovate opens the PR.
- **Security**: **CISA KEV**, **oss-security list**, per-project security advisories (GitHub "Security" tab, watch → custom → security alerts).

## Evaluating a project before you adopt it

A self-hosted app is a long relationship. Ten minutes of due diligence:

| Signal | Check | Green | Yellow | Red |
|---|---|---|---|---|
| **Activity** | Commits, releases in last 3–6 months | Regular releases, changelog | Sporadic, "looking for maintainers" | Last commit > 1 year, issues piling up |
| **Bus factor** | Contributors graph | Several active | One person, responsive | One person, silent |
| **Issues** | Open/closed ratio, response time, tone | Triaged, labelled, answered | Backlog, but polite | Hostile or ignored |
| **Licence** | LICENSE file; recent changes | OSI-approved (MIT/Apache/GPL/AGPL) | Source-available (BSL/SSPL), stable | Recent relicensing, "open core" with critical features paywalled |
| **Docs** | Install, upgrade, **backup/restore**, reverse-proxy pages | All present, current | Install only | Wiki last edited years ago |
| **Data portability** | Export formats, open file storage | Standard formats, plain files on disk | Export via API only | Proprietary blobs, no export |
| **Upgrade story** | Migration notes; does `:latest` break? | Semver, migration guides | "Read the release notes" | Frequent breaking changes without notes |
| **Security** | SECURITY.md, past CVE handling, default auth | Responsible disclosure, quick fixes, auth on by default | Slow but fixed | Unauthenticated by default, dismissive of reports |
| **Image provenance** | Who builds the Docker image? | Project or LinuxServer.io, multi-arch, signed/attested | Trusted third party | Random user's image with no Dockerfile |
| **Dependencies** | DB/queue requirements | SQLite or Postgres, Redis optional | Needs 4 services | Requires a specific ancient DB version |
| **Community** | Discord/Matrix/forum size and tone | Active, helpful | Small but present | None |
| **Funding** | Sponsors, company backing, roadmap | Transparent | Unknown | VC-backed with no revenue model (see the relicensing pattern in [Legal](30-legal-ethical.md)) |

Two extra tests: **install it in a throwaway VM/LXC first**, and **perform a backup and restore on day one**. If restoring is undocumented or painful, that's your answer.

## Giving back

Self-hosting runs on volunteer labour. Ways to sustain it that don't require writing code:

- **Sponsor** the two or three projects you rely on most (GitHub Sponsors, Open Collective, Liberapay). €5/month to Immich, Jellyfin, Vaultwarden, Paperless or Home Assistant is less than one streaming subscription.
- **Report bugs well** and confirm fixes. Reproducible reports are gifts.
- **Improve documentation**: fix the typo, add the reverse-proxy example that took you an hour to figure out.
- **Translate**, **triage issues**, **answer questions** in the community you learned from.
- **Publish your compose files and notes** (redacted) — someone's Sunday will be shorter for it.
- **Buy a licence** for the commercial-but-fair projects you use (Unraid, Plex Pass if you use Plex, JetBrains, Proxmox subscription for enterprise repo access).
- Support the **infrastructure** the ecosystem leans on: Let's Encrypt (ISRG), the OpenZFS/FreeBSD/Debian foundations, Wikipedia, Internet Archive.

## Books

| Book | Why |
|---|---|
| *The Debian Administrator's Handbook* (Hertzog & Mas, free online) | Fundamentals of the base OS |
| *UNIX and Linux System Administration Handbook*, 5th ed. (Nemeth et al.) | The comprehensive reference; skim chapters as needed |
| *Ansible for DevOps* (Jeff Geerling) | The friendly Ansible book, homelab-relevant examples |
| *Docker Deep Dive* (Nigel Poulton) | Concise, current, covers Compose and security |
| *FreeBSD Mastery: ZFS* and *Advanced ZFS* (Lucas & Jude) | Best ZFS books; concepts apply to OpenZFS on Linux |
| *Practical Monitoring* (Mike Julian) | Philosophy of alerts that matter |
| *Site Reliability Engineering* (Google, free online) | Overkill for home, but the chapters on toil, SLOs and postmortems reframe how you run things |
| *Network Warrior* (Gary Donahue) / *Computer Networking: A Top-Down Approach* (Kurose & Ross) | Networking fundamentals; VLANs and routing will stop being mysterious |
| *Security Engineering* (Ross Anderson, free online) | Threat modelling, why systems fail |
| *The Practice of System and Network Administration* (Limoncelli et al.) | Process, documentation, change management — the parts hobbyists skip |

## Keeping this guide current

This guide is a snapshot. When something here contradicts a project's current documentation, the project is right. Suggested cadence: revisit the [maintenance chapter](28-maintenance-operations.md) quarterly, re-read a project's release notes before every major version, and check awesome-selfhosted or selfh.st once a year for whether a better tool has appeared in a category you care about. Contributions and corrections to this guide's repository are welcome — see the README.
