# Communication: Chat, Video Calls, and Email

Communication is the category where self-hosting is hardest to justify — and, for the people who do it, the most satisfying. Chat and video have strong self-hosted options that work well within a household or community. Email is the notorious exception: possible, well-tooled, and burdened with deliverability problems that no amount of local competence fully solves. This chapter covers team and household chat (Matrix and its servers Synapse, Conduit/Conduwuit/Tuwunel, and Dendrite; Rocket.Chat; Mattermost; Zulip; XMPP), voice and video (Jitsi Meet, Mumble, Nextcloud Talk, Element Call, LiveKit), and self-hosted email in full honesty (Mailcow, Mailu, Stalwart, docker-mailserver, Maddy, and the outbound-relay compromise).

## Chat

### Matrix

**Matrix** is an open, **federated**, end-to-end-encrypted messaging protocol — the closest thing to "email for chat." You run a **homeserver** for your domain; your users have IDs like `@alice:example.com`; they can talk to users on any other Matrix server (matrix.org, a friend's server, communities) in rooms that are replicated across participating servers; **bridges** connect to other networks (Telegram, Discord, WhatsApp, Signal, Slack, IRC — via the mautrix family), so one client can aggregate everything. Clients: **Element** (web, desktop, mobile — the reference), **Element X** (the new mobile client, fast), **FluffyChat**, **Cinny**, **Nheko**, **SchildiChat**, and many more. Voice/video calls via **Element Call**/LiveKit (below). E2EE by default in private rooms; verified devices; cross-signing.

**Homeserver choices:**

- **Synapse** — the reference implementation (Python, Postgres). Complete, well-documented, the most features and the most admin tooling (Synapse Admin UI). Heavy-ish (1–2 GB RAM for a small server; more when federating with large rooms — joining a 50,000-member public room can spike CPU and RAM for minutes). Maintained by Element (it moved to AGPL in 2023 with a commercial licence option; the community fork of the last Apache version is not recommended).
- **Conduit** and its forks — a **Rust** homeserver using RocksDB, no Postgres, ~50–200 MB RAM, single binary, fast. Conduit itself slowed; **Conduwuit** became the community's Rust favourite in 2024, then was discontinued in 2025 by its maintainer; **Tuwunel** (continued by a maintainer with Matrix.org Foundation support) and **continuwuity** carry the lineage forward. Feature-complete for household and small-community use (federation, E2EE, media, most of the spec); some admin/moderation tooling and niche spec features lag Synapse. **The recommendation for a small self-hosted Matrix server** in 2026 — verify which fork is currently active before deploying.
- **Dendrite** — Element's Go second-generation server; capable, lighter than Synapse, development has been intermittent. Fine but not the momentum choice.

**Realities of running Matrix:**

- **Federation** is optional. A private homeserver for your household with federation disabled is simple and light. Federation to the wider network means your server participates in room replication and can be surprised by resource use; a small server *can* federate happily if users avoid the enormous public rooms.
- **Well-known delegation**: serve `https://example.com/.well-known/matrix/server` and `/client` from your main domain so `@alice:example.com` works while the homeserver lives at `matrix.example.com`. Port 8448 for federation can be avoided this way (federate over 443 via the proxy).
- **Media** grows: set retention and size limits; consider S3-backed media (Synapse supports it; the Rust servers are adding it).
- **Bridges** (mautrix-telegram/whatsapp/signal/discord, etc.) each run as a separate container and need care — WhatsApp and Signal bridges puppet your phone account and occasionally break with upstream changes. Powerful; not zero-maintenance.
- **Push notifications** on mobile go via Element's push gateway (or **ntfy**/UnifiedPush for Android with compatible clients) — the server sends only a "wake up" ping; content stays E2EE.
- **Matrix Authentication Service** (MAS) is the new OIDC-native auth layer for Synapse; Element X requires it in some configurations — the migration is a 2025–2026 concern for Synapse operators. Tuwunel supports OIDC/SSO via its own means.

**Pick Matrix if:** you want a household/friends chat with E2EE that *could* talk to the wider world, bridges to your other messengers, and no company in the middle. It is the recommendation for self-hosted chat, with the caveat that it is the most involved.

### Rocket.Chat

A **Slack-like** team chat (Node/Meteor + MongoDB): channels, DMs, threads, file sharing, video (via Jitsi/Pexip/its own), apps/integrations, omnichannel support desk features, LDAP/OIDC, mobile apps, and a polished UI. E2EE is optional and less mature than Matrix's; federation via Matrix bridge exists. The Community Edition has been repeatedly re-scoped — features moved to paid tiers, user/message caps introduced on some free options, and the licence and "Starter" plans have shifted several times since 2022. It works well; the trajectory is toward enterprise.

### Mattermost

The **Slack alternative for teams** (Go + Postgres): channels, threads, search, integrations (webhooks, slash commands, bots, a plugin marketplace), playbooks, Focalboard-derived boards, calls (built-in plugin, WebRTC), LDAP/SAML/OIDC (some auth methods Enterprise-only), mobile apps. The **free Team Edition** is capable and stable, though Mattermost has also moved features (some SSO, compliance, HA) to paid tiers and, in 2024–2025, introduced a user cap on free Enterprise-feature trials. Lighter and simpler to operate than Rocket.Chat. **Pick it if** you want Slack for a small team or a family and do not need E2EE or federation.

### Zulip

The **threaded** chat — every message belongs to a topic within a channel ("stream"), which makes asynchronous conversation dramatically more organised than Slack's firehose. Open source (Apache 2.0, Python/Django + Postgres + Redis + RabbitMQ), all features free when self-hosted, excellent documentation, LDAP/SAML/OIDC, mobile apps, integrations. Heavier to run (several services) and the topic model is loved or hated. **Pick it if** your group has many parallel discussions and values organisation over immediacy — open-source projects and study groups adore it.

### XMPP

The 25-year-old federated chat protocol (Jabber): **Prosody** (Lua, light, modular) or **ejabberd** (Erlang, industrial) as the server; **Conversations** (Android), **Monal** and **Siskin** (iOS), **Gajim**/**Dino** (desktop) as clients; **OMEMO** for E2EE; audio/video via Jingle. Extremely light (Prosody idles at ~30 MB), rock-solid, federates with a large existing network. Weaknesses: the client experience is uneven across platforms (iOS especially), group E2EE is fiddlier than Matrix's, and momentum has shifted to Matrix. **Snikket** packages Prosody with a curated client set for a turnkey family chat server — a genuinely lovely, low-maintenance option. **Pick XMPP/Snikket if** you want the lightest possible federated E2EE chat and your users are on Android/desktop.

### Others

**Revolt** (Discord-like, open source, self-hostable, young), **Spacebar** (a Discord-compatible server reimplementation), **Rocket.Chat**'s many forks, **Tinode**, **Nextcloud Talk** (chat + calls inside Nextcloud — fine for a Nextcloud household), **Signal** (not self-hostable in any practical sense), **Simplex** (self-hostable relays for a metadata-minimising messenger), **IRC** (**Ergo** is a modern server with history and auth; **The Lounge** is a web client — for the nostalgic and the pragmatic), **Discord** (no).

### Chat comparison

| | Matrix (Tuwunel/Synapse) | Mattermost | Rocket.Chat | Zulip | XMPP (Snikket/Prosody) |
|---|---|---|---|---|---|
| Model | Federated, E2EE by default | Team chat (Slack) | Team chat (Slack) | Threaded team chat | Federated, OMEMO E2EE |
| RAM | 100 MB (Rust) / 1–2 GB (Synapse) | ~500 MB | ~1–2 GB | ~2 GB | ~50 MB |
| Bridges to other networks | **Yes (mautrix, many)** | Some | Some | Some | Some (Slidge) |
| Voice/video | Element Call / LiveKit | Built-in calls | Jitsi/own | Jitsi/BigBlueButton | Jingle |
| Mobile clients | Element X, FluffyChat, many | Official | Official | Official | Conversations / Monal |
| Licence | AGPL / Apache (varies by server) | MIT (Team) + paid | MIT + paid tiers | Apache 2.0 | MIT |
| Best for | Households, communities, privacy | Small teams | Slack replacement with support desk | Organised async groups | Lightest federated E2EE |

## Voice and video

- **Jitsi Meet** — the self-hosted Zoom: browser-based (no accounts needed by default), screen sharing, recording (with Jibri), lobby and passwords, breakout rooms, mobile apps, and JWT/OIDC authentication for who may create rooms. A Compose stack of several containers (web, prosody, jicofo, jvb). Video quality is good for a handful of participants; the **JVB** (videobridge) needs UDP 10000 open to the internet (or a TURN server) for participants outside your network — this is the one place where a forwarded port is nearly unavoidable, or where a VPS should host it. Works best with a small number of participants; large meetings need real bandwidth and CPU on the bridge.
- **Element Call / LiveKit** — Matrix's native group calls, powered by **LiveKit** (an open-source SFU) with the **Matrix RTC** backend. Element X and Element Web use it; you run a LiveKit server (and its JWT service) alongside your homeserver. E2EE calls. The modern path for Matrix users; setup is more involved than Jitsi's but the integration is seamless once done.
- **Nextcloud Talk** — chat and calls inside Nextcloud; for more than 2–3 participants it needs the **High Performance Backend** (a separate signalling server, now open source and included in AIO). Fine for a Nextcloud household.
- **Mumble** — low-latency **voice** chat (the gamers' standard for two decades): tiny server (**Murmur**, ~20 MB), positional audio, channels, ACLs, clients everywhere including **Mumla** (Android) and **Mumble** (iOS). No video. Unbeatable for a gaming group or a family voice channel on a Raspberry Pi. **TeamSpeak** (proprietary) is the alternative nobody needs.
- **BigBlueButton** (education-oriented conferencing with whiteboards and breakout rooms — heavy, needs a dedicated server), **Galène** (a minimal, efficient SFU in Go — great for small groups), **MiroTalk** (WebRTC P2P/SFU meeting rooms, light), **Peer Calls**, **Rocket.Chat/Mattermost built-in calls**. **Signal/WhatsApp calls** are not self-hostable.

**Recommendation:** Jitsi Meet for ad-hoc video with anyone (send a link); Mumble for persistent voice; Element Call if you are on Matrix and want calls in the same client.

## Email: the honest chapter

Self-hosting email is possible, and the tooling in 2026 is better than it has ever been. Before choosing to do it, understand what you are signing up for.

### Why it is hard

- **Deliverability.** The large providers (Gmail, Outlook/Microsoft 365, Yahoo, iCloud) treat mail from unknown IPs with suspicion. Residential IP ranges are **blanket-blocked** for outbound SMTP by nearly every recipient and by most ISPs (port 25 outbound is blocked at the ISP level for the majority of home connections). So your mail server *cannot* live at home and send mail directly. It lives on a **VPS** — and VPS IP ranges are also treated with suspicion, especially cheap ones with a history of spam. A new IP starts with **no reputation**; building it takes weeks of low-volume legitimate mail, and a single misstep (an open relay, a compromised account, a mailing-list blast) lands you on a blocklist that can take days to escape. Microsoft in particular is opaque and slow about delisting.
- **The standards are non-negotiable now.** **SPF**, **DKIM**, and **DMARC** (with `p=quarantine` or `reject`) are required by Gmail and Yahoo for bulk senders since 2024 and effectively required for everyone. **Reverse DNS (PTR)** must match your HELO name. **TLS** with a valid certificate. **MTA-STS** and **DANE** are nice-to-haves. Any mail server package below sets these up; you still have to publish the DNS records correctly and understand what they do.
- **Inbound spam** must be filtered (rspamd is excellent) and *you* tune the false positives.
- **Availability.** If your server is down, senders retry for a few days, then bounce. A home internet outage or a botched update can lose mail. Email is the one service where downtime has irreversible consequences.
- **Time.** Initial setup is a weekend. Ongoing: monitoring blocklists, reading rspamd reports, updating, occasionally begging Microsoft. Perhaps an hour a month once stable — and the "once stable" takes a few months.

### Why people do it anyway

Complete control over the most important account you have (every password reset goes through it); no provider reading or mining it; unlimited addresses and domains; catch-all and plus-addressing; no risk of a provider locking you out; learning the protocols that underpin the internet. For some, it is the point of self-hosting.

### The realistic architectures

1. **Don't.** Use a privacy-respecting paid provider (**Fastmail**, **Proton**, **mailbox.org**, **Migadu**, **Posteo**, **Tuta**) with your own domain. USD 1–5/month per user. You keep domain portability (the actual lock-in protection), gain deliverability, and lose only the purity. **This is the right answer for most households**, and choosing it is not a failure.
2. **Receive at home, send via a relay.** Run your mail server at home (or on a VPS) for storage, IMAP, webmail, and filtering, but route **outbound** mail through a reputable **SMTP relay** — **Amazon SES** (USD 0.10 per 1,000 emails), **Mailgun**, **Postmark**, **SMTP2GO**, **Brevo**, **Resend**, or your ISP's relay. Deliverability becomes the relay's problem; you keep your mailbox and data. Inbound to a home IP requires port 25 open inbound (many ISPs allow it even when blocking outbound) and a static IP or a **backup MX**/**inbound relay** on a VPS that forwards to home over a VPN. **The recommendation for anyone who insists on self-hosting the mailbox.**
3. **Full stack on a VPS.** Mail server on a VPS with a clean IP (check its history against blocklists *before* committing; Hetzner, OVH, and Vultr ranges vary — some providers block port 25 on new accounts until you ask). Do everything right (rDNS, SPF, DKIM, DMARC, TLS, rate limits, no open relay, MTA-STS), warm the IP slowly, monitor with **mail-tester.com** and blocklist checks, and accept the occasional Microsoft fight. Feasible; hundreds of people do it successfully; not effortless.

### The server packages

- **Mailcow: dockerized** — the full suite: Postfix (SMTP), Dovecot (IMAP), rspamd (spam, DKIM), SOGo (webmail, calendar, contacts, ActiveSync), ClamAV, Netfilter (fail2ban-like), a comprehensive admin UI with domains/mailboxes/aliases/quotas/sync jobs, automatic Let's Encrypt, DKIM management, and a backup/restore script. ~2–4 GB RAM (ClamAV and SOGo are heavy; both can be disabled). The most complete and the most popular; excellent documentation; a paid support option. **The recommendation if you want a UI and everything included.**
- **Mailu** — a lighter, Compose-native suite (Postfix, Dovecot, rspamd, Roundcube or SnappyMail webmail, an admin UI, fetchmail, optional ClamAV/full-text search) at ~1 GB RAM. Clean, well-designed setup wizard on the project website that generates your Compose file. Less feature-rich admin than Mailcow; simpler to understand. **The recommendation for a lighter footprint.**
- **Stalwart Mail Server** — a **single Rust binary** implementing SMTP, IMAP, JMAP (the modern mail protocol), CalDAV/CardDAV/WebDAV (since 2025), with built-in spam filtering, DKIM/SPF/DMARC/ARC, DANE, MTA-STS, S3 or filesystem or database storage, OIDC/LDAP, a web admin, and remarkable performance at ~50–200 MB RAM. Launched 2023, maturing very fast, and the most technically modern option by a wide margin. Fewer years in production than Postfix/Dovecot; a smaller community; webmail is not bundled (pair with SnappyMail/Roundcube). **The recommendation for people who want modern, light, and are comfortable being slightly early.**
- **docker-mailserver** — Postfix + Dovecot + rspamd (or SpamAssassin) + ClamAV + fail2ban in **one container**, configured via environment variables and a `setup` script, no web admin, no bundled webmail. Lean, well-documented, mature, and exactly right for a person who wants a classic mail stack without a UI. ~500 MB–1 GB.
- **Maddy** — a single-binary Go mail server (SMTP + IMAP + DKIM/SPF/DMARC, SQLite-backed) with minimal configuration; lighter than everything but Stalwart; no webmail or admin UI; a good choice for a personal single-domain server on a tiny VPS.
- **Mail-in-a-Box** (an opinionated all-in-one that takes over an Ubuntu VPS — DNS, mail, webmail, Nextcloud), **iRedMail** (the older full-suite installer; free edition + paid admin panel), **Modoboa**, **Poste.io** (free tier limited), **YunoHost** (bundles a mail stack with its apps — surprisingly good for a family server), **Postal** (transactional mail platform — for sending app mail, not personal mailboxes), **Haraka**, **Zimbra** (enterprise groupware, heavy), **Cyrus**.

### Webmail and clients

**Roundcube** (the classic, complete, slightly dated), **SnappyMail** (the fast, modern fork of RainLoop — the current favourite), **SOGo** (bundled in Mailcow — groupware with calendar/contacts/ActiveSync), **Nextcloud Mail** (adequate). Desktop/mobile: **Thunderbird**, **K-9 Mail/Thunderbird for Android**, **FairEmail** (Android, superb), Apple Mail, **Outlook** (works with IMAP; ActiveSync via SOGo). JMAP clients (**Twake Mail**, **Mailtemi**) work with Stalwart.
