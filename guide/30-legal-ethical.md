# Legal and Ethical Considerations

Self-hosting sits at the intersection of several bodies of law and a few ethical questions that the community discusses less than it should. None of this is legal advice — laws differ by country and change — but a self-hoster ought to understand the landscape: what open-source licences actually permit and why the "source-available" trend matters; the copyright realities of media libraries, ripping, and the automation tooling; what your ISP's terms say about servers; what you take on when you hold other people's data (GDPR and its cousins, even for a family); the law around recording cameras and voice assistants; the ethics of privacy front-ends and scraping; and how to think about sustainability and e-waste. The aim is informed choices, not fear.

## Software licences: what you are actually allowed to do

Nearly everything in this guide is free to download and run at home. The licence differences matter when you *redistribute*, *modify*, *offer as a service*, or care about the project's long-term openness.

### The families

| Family | Examples | You may… | Obligations | Notes |
|---|---|---|---|---|
| **Permissive** (MIT, BSD, Apache 2.0) | Immich (MIT), Vaultwarden (AGPL — see below), Caddy (Apache), Traefik (MIT), Homepage (GPL) | Use, modify, redistribute, sell, keep changes private | Keep the copyright notice; Apache adds patent grant and NOTICE | Maximum freedom; a company can take it closed |
| **Weak copyleft** (LGPL, MPL 2.0) | OpenTofu, Kanidm (MPL) | Use freely; modify | Share changes *to the licensed files*; can link into proprietary code | Middle ground |
| **Strong copyleft** (GPLv2/v3) | Linux, Jellyfin, Home Assistant (Apache actually), Pi-hole (EUPL), Proxmox (AGPL) | Use, modify, redistribute | Distributed modifications must be GPL too, with source | Running it privately triggers nothing; distributing does |
| **Network copyleft** (AGPLv3) | Nextcloud, Vaultwarden, Grafana, Synapse, Paperless-ngx, MinIO, Plausible, Docmost | Use, modify | Also: if you *offer the modified software over a network*, you must provide source to users | Running an unmodified copy for your household: no obligations. Modifying and hosting for the public: share the changes |
| **Source-available / "fair" licences** (BSL/BUSL, SSPL, Elastic Licence, Sustainable Use Licence, Fair Source, FSL) | HashiCorp Terraform/Vault (BSL), MongoDB/Redis 7.4 (SSPL), n8n (SUL), ZeroTier (BSL), Outline (BSL), Sentry (FSL), Plausible's hosted features, Gitea Enterprise | Usually: use internally, self-host, modify | Usually: **may not offer as a competing hosted service**; sometimes non-commercial only; BSL converts to open source after N years | **Not open source** by the OSI definition; fine for home use; the concern is the project's direction |
| **Freeware / proprietary with free tier** | Plex, Emby, Unraid, Portainer BE, Bitwarden server (mixed), Synology DSM | Use per the EULA | Whatever the EULA says; features may be paywalled or removed | You are a customer, not a participant |

### Why the source-available trend matters

Since roughly 2018, a steady procession of formerly open-source projects — MongoDB, Elastic, Redis, HashiCorp's suite, Sentry, Akka, CockroachDB, and many smaller ones — moved to licences that prohibit cloud providers from selling them as a service. For a home user *nothing changes*: you may still run them. Three things do change:

1. **Community forks appear** (OpenTofu, OpenBao, Valkey, OpenSearch) and the ecosystem splits; you must choose which side to follow, and packagers (Debian, Fedora) generally follow the open fork.
2. **The project's incentives change**: development effort follows the paid tier; the community edition may lose features over time (Rocket.Chat, Mattermost, Portainer, MinIO's console, Plausible's features, GitLab's tiers are all examples of features migrating upward). "Open-core" is a spectrum, and where a project sits on it tends to drift in one direction.
3. **"Free for personal use" is a contract, not a right.** The permission can be narrowed (Docker Desktop's 2021 licence change, ZeroTier's tier reduction, Plex's 2025 remote-streaming paywall). Open-source licences are irrevocable for the version you have; EULAs are not.

Practical guidance: prefer OSI-approved licences for infrastructure you depend on long-term (proxy, DNS, backups, identity, storage); accept source-available for applications where the community edition is generous and an exit exists (your data in open formats); note the licence in your service inventory; and when a project relicenses, do not panic — evaluate the fork and the actual restrictions rather than reacting to the headline. This guide notes licences for that reason.

### Copyleft and your own modifications

If you patch Jellyfin and run it for your family, you owe nobody anything. If you patch Nextcloud (AGPL) and run it for a club of fifty people, those users are entitled to your modified source. If you build a product on an MIT component, you owe attribution. If you fork a GPL project and publish it, it must stay GPL. These are the rules; they are simple for home use and matter the moment "home" becomes "public."

## Copyright and media

The media chapter ([Chapter 15](15-media.md)) is neutral about content; this section is not neutral about the law.

- **Ripping discs you own** for personal use is legal in some jurisdictions (many EU countries have a private-copy exception, often funded by a levy on blank media), illegal-but-unenforced in others (the US DMCA prohibits circumventing DRM — CSS on DVDs, AACS on Blu-rays — even for personal backup; the UK briefly legalised then re-criminalised format-shifting in 2015). Almost nobody has been prosecuted for ripping their own discs; it remains technically unlawful in the US and UK.
- **Downloading copyrighted works you have not paid for** is infringement everywhere. **Uploading** (which BitTorrent does by design while you download) is the act rights-holders actually pursue — via ISP notices, "speculative invoicing" letters (Germany's *Abmahnung* industry is the most aggressive; the US and UK have waves of it), and occasionally lawsuits. A commercial VPN ([Chapter 15](15-media.md)) hides your IP from the swarm; it does not make the act legal. Usenet is one-directional (no uploading) and less pursued, but equally infringing for copyrighted content.
- **The *arr tools, Jellyfin, Plex, qBittorrent, SABnzbd** are legal software. They are also the standard pipeline for infringement, and the community's polite fiction that everyone is "downloading Linux ISOs" is exactly that. This guide describes the tools; you are responsible for what you feed them.
- **Legitimate sources** exist and are growing: your own rips (where legal), DRM-free purchases (GOG for games; Bandcamp, Qobuz, HDtracks, 7digital for music; Humble Bundle, Standard Ebooks, Project Gutenberg, Tor.com's free stories for books; Vimeo On Demand and some indie studios for video), public domain (Internet Archive, Prelinger, Wikimedia Commons), Creative Commons (Blender Foundation films, Jamendo, Free Music Archive), YouTube downloads of your *own* channel or CC-licensed content, recording OTA broadcasts (legal for personal time-shifting in most countries — an HDHomeRun tuner and Jellyfin's DVR), and podcasts. A legitimate library is entirely possible.
- **ROMs**: dumping cartridges/discs you own with a dumper (Retrode, Sanni cart reader, a disc drive) is the legal route in jurisdictions with a private-copy exception; downloading a ROM of a game you own is *not* legalised by owning the cartridge in most jurisdictions (the "24-hour rule" is an internet myth). Emulators themselves are legal (Sony v. Connectix, Sony v. Bleem); Nintendo's aggressive 2024–2025 actions against Yuzu, Ryujinx, and ROM sites changed the landscape for current-generation emulation. Homebrew and public-domain ROMs are unambiguously fine.
- **Sharing your library**: giving your family Jellyfin accounts is the personal-use grey zone most people are comfortable in; giving fifty strangers access is distribution and a different legal category (and a different Plex ToS category — Plex's terms prohibit it).

Be honest with yourself about what you are doing, understand your jurisdiction's actual exposure (an ISP notice is the realistic worst case for most personal downloaders in most countries; a EUR 1,000 *Abmahnung* is the realistic worst case in Germany), and make your choices as an adult.

## Your ISP's terms

Most residential ISP terms of service contain a clause prohibiting "servers" or "commercial use" and reserving the right to block ports. In practice:

- **Enforcement against personal home labs is almost unheard of.** ISPs care about bandwidth abuse, spam, and legal complaints. A Jellyfin server for your family or a Vaultwarden instance generates none of these.
- **Port 25 outbound is blocked** by most residential ISPs specifically to stop spam; inbound 25 often too. This is the one "server" they actively prevent ([Chapter 20](20-communication.md)).
- **CGNAT** ([Chapter 3](03-networking.md)) is increasingly common and makes the question moot for inbound.
- **Data caps** are a real constraint for off-site backups and remote streaming; read yours.
- **Business tiers** cost more, typically permit servers explicitly, and often include a static IP and better support. Worth it for anyone hosting for others or running anything commercial.
- Read the ToS once. Know what you agreed to. Then do what everyone does.

## Holding other people's data

The moment your Immich has your partner's photos, your Nextcloud has your parents' documents, or your Vaultwarden has a friend's vault, you are — in the eyes of privacy law — processing personal data.

- **GDPR (EU/UK) has a "household exemption"** (Article 2(2)(c)): processing "by a natural person in the course of a purely personal or household activity" is outside its scope. A family's photos on a family server is the archetype. The exemption narrows as you extend to friends, a club, or the public — a sports club's member database on your server is not a household activity, and GDPR's obligations (lawful basis, security, breach notification, data-subject rights) apply, with you as controller. The US has no general equivalent; state laws (CCPA etc.) apply to businesses above thresholds and rarely to individuals. Other jurisdictions vary (Brazil's LGPD, Canada's PIPEDA — mostly commercial).
- **Regardless of law**, the ethical position is simple: people who trust you with their data deserve the security in [Chapter 13](13-security.md), the backups in [Chapter 11](11-backups.md), honesty about the risks, an exit (their data exportable), and to be told if something goes wrong. Write it down for them if they are not family ([Chapter 28](28-maintenance-operations.md)).
- **Special categories** — health data (Baby Buddy, Wger, Fasten Health), financial data (Firefly, Actual), location (Dawarich, OwnTracks), children's data — carry heightened expectations everywhere. Keep them VPN-only, encrypted at rest, and backed up encrypted.
- **Data you scrape or archive** (ArchiveBox, Karakeep, Tube Archivist, Invidious) about *other* people — public posts, videos, comments — is theirs. Private archives for personal use are the norm; republishing is where problems start.

## Cameras, microphones, and recording

- **Cameras** ([Chapter 19](19-home-automation.md)): recording your own property is legal everywhere; recording *beyond* it — the street, a neighbour's garden, a shared hallway — is regulated in many countries (the UK ICO's guidance on domestic CCTV; Germany's strict rules against filming public space and neighbours; Austria, France, and others similar; US states vary on audio). Use Frigate's **masks** to exclude the neighbour's windows and the pavement; **audio recording** is more restricted than video in many jurisdictions (US "one-party consent" states vs "all-party"; illegal for many public spaces in Europe) — consider disabling camera microphones. Signage may be required for shared areas. Tenancy agreements and homeowner associations may have rules.
- **Voice assistants** (HA Assist, Whisper): local processing avoids the cloud-recording concerns entirely, which is the point. Guests should know there are microphones; a hardware mute is a courtesy.
- **Presence and location tracking** of household members (phone GPS, BLE, Wi-Fi tracking) is a consent conversation, not a technical one. Tracking a partner or teenager without their knowledge is a serious matter regardless of legality.
- **Doorbell cameras** face the street by design and are the most contested category; check local guidance and angle them at your doorstep.

## Privacy front-ends, scraping, and terms of service

Invidious, Piped, Redlib, SearXNG, RSS-Bridge, yt-dlp, and their kin access services in ways their terms of service prohibit (YouTube's ToS forbids access "through any automated means"; Reddit's API terms changed in 2023 specifically to kill third-party clients). This is a **contract** issue, not a criminal one, in almost all jurisdictions; the realistic consequence is your IP being blocked or an account banned, not legal action against an individual. Public instances of these tools shift the burden to the operator and are where the cease-and-desist letters (Invidious received one from YouTube in 2023) land. Run private instances for yourself; do not run public ones unless you understand the exposure. Ethically: these tools remove ads that fund creators — many users mitigate by supporting creators directly (Patreon, memberships, buying merch), which is a reasonable position.

## Running public services

If you expose anything to the public — a Mastodon instance, a Matrix server with open registration, a Lemmy community, a public SearXNG or Invidious, a forum — you become a **service operator** with obligations that scale with your user count: content moderation (illegal content — CSAM in particular — on federated platforms is a real and serious operator burden; the EU's DSA and the UK's Online Safety Act 2023 impose duties on services above thresholds and in some cases below), abuse handling, uptime expectations, data-protection duties, and potentially registration requirements. **Single-user or closed-registration** instances avoid nearly all of this. Open a service to the public only with intent, a moderation plan, and an understanding of the local law; the fediverse's operator communities (Mastodon's admin guides, the IFTAS resources) are the place to learn.

## Domains, accounts, and continuity

- **Your domain is the root of trust** for everything (TLS, email, identity). Register it for multiple years, enable auto-renew with a working payment method, lock it (registrar lock, transfer lock), enable 2FA on the registrar and DNS provider, use a recovery email that does not depend on the domain itself, and record the details in the "if I'm not here" document ([Chapter 28](28-maintenance-operations.md)). Expired domains are snapped up in hours; the consequences for a household's email and services are severe.
- **Trademark**: do not register a domain that infringes a brand (`plexforfriends.com`); it can be taken from you via UDRP.
- **Free-tier dependencies** (Tailscale, Cloudflare, ntfy.sh, Healthchecks.io, Let's Encrypt) are gifts with terms; have a plan if any change.

## Sustainability and e-waste

Self-hosting's environmental story is mixed. Reusing a decommissioned corporate mini PC for a decade is excellent (embodied carbon already spent; 10 W idle). Running a 2014 dual-Xeon at 200 W idle to host a Pi-hole is not — its electricity over a year exceeds the embodied carbon of a new N100 box several times over. Rules of thumb:

- **Idle watts dominate** over hardware lifetime; [Chapter 29](29-power-cost-environment.md)'s tuning is the environmental lever as well as the financial one.
- **Reuse over new** where power is comparable; **new efficient over old power-hungry** where it is not.
- **Buy drives for the data you have**, not the data you imagine; spin down what you can.
- **Dispose properly**: WEEE recycling in the EU/UK; e-waste programmes elsewhere; **wipe drives** first (`shred`, `blkdiscard`/secure erase for SSDs, or physical destruction for anything that held the vault or the photos) — a sold or recycled drive with recoverable data is a real breach.
- **Right-size the lab.** The greenest service is the one you did not run.

## Ethics in brief

A few positions this guide takes, stated plainly so you can disagree:

- **Privacy is a legitimate reason to self-host**, and so is learning, and so is fun. You do not owe anyone a justification.
- **Owning your data means owning the responsibility for it** — to yourself and to the people whose data you hold. Backups and security are ethical obligations, not just technical ones.
- **Support the projects you depend on.** Open-source maintainers are frequently unpaid; the tools in this guide represent thousands of person-years of volunteer work. Star repos, file good bug reports, write documentation, translate, and — where you can — donate (GitHub Sponsors, Open Collective, Liberapay, direct). A household that saves USD 300/year in subscriptions can afford USD 30 to the five projects that made it possible. Nabu Casa's subscription funds Home Assistant; FUTO funds Immich; Codeberg runs Forgejo on donations.
- **Be honest about legality.** Pretending the media pipeline is for Linux ISOs helps nobody. Make informed choices.
- **Be a good network citizen.** Rate-limit your scrapers, do not run open resolvers or relays, do not expose things that will be used to attack others, respond to abuse reports if you run public services.
- **Help the next person.** The community's generosity is why this guide could be written. Answer a question on r/selfhosted; document your setup; share what broke and how you fixed it.

## Checklist

- [ ] The licence of every service in the inventory noted; infrastructure dependencies preferably OSI-open; source-available and freeware understood as contracts that can change.
- [ ] Media library provenance understood; jurisdiction's actual exposure known; VPN/Usenet choices made deliberately; legitimate sources used where they exist.
- [ ] ISP ToS read once; port 25 and data cap constraints known.
- [ ] If hosting for anyone beyond the household: expectations set, data exportable, security and backups at the level their trust deserves; GDPR-style obligations considered for groups/clubs.
- [ ] Cameras masked to your own property; audio recording decision made; household members and guests aware of microphones; tracking consensual.
- [ ] Privacy front-ends and scrapers run privately, rate-limited, and with the understanding that they violate ToS.
- [ ] No public-registration services without a moderation plan and awareness of applicable law.
- [ ] Domain: multi-year, auto-renew, locked, 2FA, off-domain recovery email, recorded in the emergency document.
- [ ] Old drives wiped before disposal; hardware choices consider idle power as an environmental cost.
- [ ] A budget — however small — for donating to the projects you rely on.
