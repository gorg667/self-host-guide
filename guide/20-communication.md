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
