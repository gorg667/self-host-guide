# Gaming: Game Servers, Retro Libraries, and Streaming

Gaming is a category where a home lab pays off in a way everyone in the house understands: a Minecraft server for the kids and their friends that is always on and under your control; a Valheim or Palworld world for your group; a retro game library browsable from the couch; and a gaming PC in the closet streamed to any screen in the house. This chapter covers game server management panels (Pterodactyl and its fork Pelican, Crafty Controller, PufferPanel, AMP, and the container-per-game approach), the reality of exposing game servers to friends (and how to do it behind CGNAT with Playit.gg or a VPS), retro game libraries (RomM, Gaseous, EmulatorJS), game streaming from a home PC or VM (Sunshine and Moonlight, with GPU passthrough on Proxmox), and adjacent tools (LAN caches, Steam library management, save-game sync).

## Game servers

### The container-per-game approach

The simplest way to run one game server is one Docker container with a well-maintained image:

- **itzg/minecraft-server** — the gold standard: every server type (Vanilla, Paper, Purpur, Fabric, Forge, NeoForge, Spigot, Velocity proxy), automatic version handling, mod/plugin downloads from CurseForge/Modrinth via environment variables, RCON, world backups (companion `itzg/mc-backup`), auto-pause when empty (saves CPU), and exhaustive documentation. If you run one Minecraft server, use this.
- **itzg/minecraft-bedrock-server** for Bedrock (console/phone players); **GeyserMC** (plugin) lets Bedrock clients join a Java server.
- **lloesche/valheim-server**, **thijsvanloef/palworld-server-docker**, **ich777/steamcmd** images (Unraid favourites — hundreds of Steam games), **CM2Network** (Source games), **wolveix/satisfactory-server**, **LinuxGSM** (a script-based manager for 100+ games, also in Docker), **factoriotools/factorio**, **Terraria** (`ryshe/terraria`), **Project Zomboid**, **Rust**, **ARK/ASA**, **Enshrouded**, **V Rising**, **7 Days to Die**… nearly every popular dedicated server has a maintained image.

Pros: no panel to maintain, everything in your Compose file, trivially backed up (the world directory). Cons: no web UI for non-technical co-admins, no console access without `docker attach`/RCON, manual per-game.

### Pterodactyl and Pelican

**Pterodactyl** is the game-server management panel: a web UI (PHP/Laravel + MariaDB + Redis) where users create servers from "eggs" (templates for Minecraft, Rust, ARK, Valheim, Terraria, Discord bots, and hundreds more via the community egg repository), each server runs as an isolated Docker container managed by the **Wings** daemon on one or more nodes, with a web console, file manager, scheduled tasks, backups (local or S3), per-user permissions (give a friend admin over *their* server only), resource limits, and an API. It is what most game hosting companies run. **Pelican Panel** is the 2024 fork by former Pterodactyl maintainers after Pterodactyl's development stalled — same architecture, actively developed, modern UI (Filament), simpler installation, and rapid feature additions. **Pelican is the recommendation** for a new install in 2026; Pterodactyl still works but the momentum has moved.

Watch out for: the panel and the Wings daemon are separate (Wings on the game host, panel anywhere; both must have valid TLS); the panel is a full LAMP-style stack (~1 GB with database); each game server is a container *inside* Wings' Docker, so nesting on a Docker host works but understand the layering; eggs vary in quality.

### Crafty Controller

A **Minecraft-focused** panel (Python): create and manage many Java/Bedrock servers, web console, scheduled backups and restarts, player management, scheduled commands, plugin/mod support, user roles. Simpler than Pelican, does Minecraft superbly, does nothing else. **The recommendation for a Minecraft-only household** — especially if a teenager will be the admin.

### PufferPanel

A lightweight Go panel supporting Minecraft, Source games, Terraria, and others via templates, with a clean UI, user permissions, OAuth2, and a small footprint (~100 MB). Less feature-rich than Pelican; faster to set up. A good middle option.

### AMP (Application Management Panel)

**CubeCoders AMP** is the **paid** (USD 10–20 one-time per licence tier) commercial panel: polished, supports 100+ games with "generic" module support for others, one-click mod/plugin installs, scheduling, backups, and excellent Windows *and* Linux support. It is the closest thing to a consumer product in this space and worth the money for people who want it to just work. Runs in Docker or natively.

### Others

**LinuxGSM** (the CLI script manager — reliable, no UI), **Gameyfin** (library, not servers), **Multicraft** (commercial, dated), **MCSManager**, **Cuberite** (a lightweight C++ Minecraft-compatible server), **Velocity/Waterfall** (Minecraft proxies for networks of servers), **Lazymc** (puts a Minecraft server to sleep when empty and wakes it on connect — saves a lot of CPU/RAM; itzg's image has similar auto-pause).

### Comparison

| | Container-per-game | Pelican / Pterodactyl | Crafty Controller | PufferPanel | AMP |
|---|---|---|---|---|---|
| Games | Any with an image | Hundreds (eggs) | Minecraft only | Dozens (templates) | 100+ |
| Web UI / console | No | **Yes, full** | Yes | Yes | **Yes, polished** |
| Multi-user with permissions | No | **Yes** | Yes | Yes | Yes |
| Multi-node | Compose per host | **Yes (Wings)** | No | Yes | Yes |
| Footprint | Just the game | ~1 GB panel + Wings | ~200 MB | ~100 MB | ~300 MB |
| Cost | Free | Free | Free | Free | **Paid** |
| Best for | One or two servers, you as admin | Many games, many users | Minecraft households | Light general panel | Turnkey polish |

## Resources and hardware for game servers

Game servers are unusual in a home lab: they are **single-thread-heavy and RAM-hungry** rather than idle. Minecraft Java wants a fast core and 4–8 GB for a modded server; Valheim/Palworld/ARK want 8–16 GB; most tick along at 5–30% of a core when players are idle and spike when they are active. An N100 runs a vanilla Minecraft server for a few players; a modded server or several concurrent games wants a real desktop CPU (Ryzen 5/7, Core i5/i7) with high single-core clocks — the same used SFF workstation that makes a good Proxmox node. Give game servers **local SSD** for worlds (chunk loading is I/O-sensitive) and **auto-pause/sleep** when empty. Back up worlds nightly (`mc-backup`, Pelican's backups, or snapshots) — a corrupted world is a family crisis.

## Exposing servers to friends

Friends outside your house need to connect. Options in order of preference:

1. **Mesh VPN for your friend group.** Tailscale's free tier allows sharing individual devices/subnets with other tailnets, and friends can install Tailscale in two minutes. Nothing exposed; works behind CGNAT; the server is reachable at a stable tailnet IP or MagicDNS name. **The best option when friends are willing** — and gamers usually are.
2. **Playit.gg** — a free (with paid tiers) tunnelling service designed for game servers: a small agent at home makes an outbound connection; Playit gives you a public address (TCP/UDP) that forwards to your server. Works behind CGNAT, no port forwarding, supports Minecraft/Valheim/Terraria/etc. natively, no client install for friends. Traffic passes through Playit's relays (latency adds 10–40 ms). **The best option when friends will not install anything.**
3. **Pangolin or a VPS with WireGuard + DNAT** ([Chapter 8](08-remote-access-vpn.md)) for raw TCP/UDP forwarding through your own relay — full control, ~USD 4/month, works behind CGNAT.
4. **Port forwarding** the game's port (Minecraft 25565/TCP, Valheim 2456–2458/UDP, etc.) directly, with a DDNS name. Simple if you have a public IP; exposes the game server binary to the internet — keep it updated, use a whitelist (Minecraft `white-list=true`), enable online-mode, and consider a non-default port to reduce scanner noise. Game servers are generally hardened against random connections, but a Minecraft server with `online-mode=false` and no whitelist *will* be griefed within days.
5. **Cloudflare Tunnel** — HTTP-only on free plans (TCP via `cloudflared access` needs the client installed, and Spectrum for raw UDP is enterprise); not suitable for most games.

For **voice**, run **Mumble** ([Chapter 20](20-communication.md)) alongside — light, low-latency, exposed the same way.

## Retro game libraries

The other half of gaming in a home lab: your collection of ROMs and disc images (from cartridges and discs you own — [Chapter 30](30-legal-ethical.md)), organised with box art and metadata, playable in a browser or streamed to a handheld.

- **RomM** — the modern ROM manager: scans a folder tree organised by platform, fetches metadata and artwork from IGDB/ScreenScraper/MobyGames/Hasheous, shows a beautiful library UI, supports 400+ platforms, has **in-browser play via EmulatorJS** for supported systems (NES through PS1/N64/DS), **save states and saves synced across devices**, multi-user with per-user libraries, collections, and integration with **Playnite** and **muOS/OnionOS/KNULLI** handheld firmware via its API and the community sync apps. Python + Postgres, ~500 MB. **The recommendation** — it has become the Jellyfin of ROMs.
- **Gaseous Server** — the .NET alternative with similar goals: library, metadata from IGDB, EmulatorJS in-browser play, ROM hash verification against No-Intro/TOSEC DATs (excellent for verifying a collection), user management. Slightly more archivist-oriented; a solid alternative.
- **EmulatorJS** (the standalone project) — the browser emulation engine (RetroArch cores compiled to WebAssembly) that RomM and Gaseous embed; can be self-hosted alone as a simple "put ROMs in a folder, play in browser" site.
- **RetroArch** on the client (any device: Steam Deck, Android, Raspberry Pi with RetroPie/Batocera/RecalBox, an old laptop) reading from an SMB/NFS share of your library — the traditional approach; RomM adds the pretty library and the sync.
- **Playnite** (Windows launcher aggregating Steam/GOG/Epic/emulators — with a RomM plugin), **Pegasus**, **ES-DE (EmulationStation Desktop Edition)** on the couch PC/Steam Deck pointed at the share.
- **Gameyfin** — a library manager for *PC* game installers (GOG offline installers and the like), with download links for the household. Different niche.
- **Steam ROM Manager**, **Skyscraper** (metadata scrapers for handheld frontends).
- Handheld sync: **RomM's muOS/KNULLI apps**, **Syncthing** for save files, **Ludusavi** for PC save-game backups.

## Game streaming from a home PC or VM

Play a full gaming PC on a TV, laptop, tablet, phone, or Steam Deck anywhere in the house (or, over a good connection, anywhere) — the machine stays in the closet with the GPU, the client shows a low-latency stream.

- **Sunshine** (host) + **Moonlight** (client) — the open-source pair that replaced NVIDIA GameStream when NVIDIA discontinued it: Sunshine runs on the gaming machine (Windows or Linux; NVIDIA, AMD, or Intel encoders — NVENC/AMF/QSV/VAAPI), Moonlight runs on everything (Windows, macOS, Linux, iOS, Android, Android TV, Apple TV, Steam Deck, Raspberry Pi, Nintendo Switch homebrew, Xbox, web). 4K 120 Hz HDR with ~5–15 ms added latency on a wired LAN, gamepad/mouse/keyboard passthrough, multi-monitor, virtual displays (via **Virtual Display Driver** on Windows, so the host needs no monitor plugged in). **The standard.** Pair with **Apollo** (a Sunshine fork with per-client virtual displays and a few conveniences) if you like.
- **Steam Remote Play / Steam Link** — built into Steam; simpler; slightly higher latency and less control; fine for a TV in the same house.
- **Parsec** — proprietary, hosted brokering, excellent low-latency; free for personal use, requires an account; good over the internet.
- **Wolf** (Games on Whales) — a Linux-native streaming host that runs each session in a container with its own virtual display and GPU access — multiple simultaneous users on one GPU, Moonlight-compatible; the multi-tenant/Linux-first alternative for people who want a "cloud gaming" box at home.
- **Remote desktop tools** (RustDesk, Apache Guacamole, NoMachine) for non-gaming remote use; too laggy for games.

**GPU passthrough on Proxmox** is how many people build the host: a Windows (or Linux/Bazzite) VM with a discrete GPU passed through via VFIO (IOMMU enabled in BIOS; the GPU's IDs bound to `vfio-pci`; the VM set to `q35`/OVMF with the PCIe device added; a dummy HDMI plug or virtual display so the GPU has an output), Sunshine inside the VM, the VM started on demand (Wake-on-LAN-style via the Proxmox API or a Home Assistant button). This gives you a gaming PC that is also a Proxmox node and, when the VM is off, the GPU can be reassigned to an LLM container or a Linux VM. Caveats: consumer NVIDIA passthrough works without the old Code 43 workaround since 2021; AMD cards have a "reset bug" on some models that prevents re-use without a host reboot (the `vendor-reset` module helps); anti-cheat in some games blocks VMs (detectable virtualisation — mitigations exist but games like Valorant refuse). A bare-metal Windows box with Sunshine is simpler if gaming is the primary purpose.

## Adjacent tools

- **LAN cache**: **LanCache** (`lancachenet`) — a caching proxy for Steam, Epic, Blizzard, Origin, Windows Update, and more: the first download of a 100 GB game from the internet is cached; every other PC in the house pulls it at LAN speed. Needs a DNS override (point the CDN hostnames at the cache via Pi-hole/AdGuard) and lots of disk. Superb for households with several gaming PCs or a slow connection.
- **Save-game sync**: **Ludusavi** (backs up PC game saves to any folder — then Syncthing/Nextcloud carries them; also restores), **Syncthing** for emulator saves, **GameVault** (a self-hosted "Steam for your own game files" — library, downloads, metadata, save sync; for DRM-free collections), **Gameyfin**.
- **Discord bots** and **game-server status pages**: **Uptime Kuma** has game-server monitors (Steam query); **Gamedig**-based bots post player counts.
- **Voice**: Mumble ([Chapter 20](20-communication.md)).
- **Mod management**: Modrinth/CurseForge via itzg's image variables; **Pelican's** egg-level mod installers; **r2modman**/**Thunderstore** for client-side.
- **Windows game servers** (some games have no Linux server): a Windows VM on Proxmox, or **Wine/Proton in Docker** (many Steam dedicated servers run under Wine — images exist for ARK, Palworld, etc.).

## Recommendations

- **One Minecraft server for the family:** `itzg/minecraft-server` with auto-pause and `mc-backup`, exposed to friends via Tailscale or Playit.gg, whitelist on.
- **Several games, several admins:** Pelican Panel with Wings on a decent-CPU host; Crafty if it is only Minecraft and a teenager runs it.
- **Retro library:** RomM with EmulatorJS in the browser and RetroArch/ES-DE on the couch device reading the same share; verify hashes with Gaseous or the DATs if you care about archival quality.
- **Streaming:** Sunshine + Moonlight from a Windows VM with GPU passthrough on Proxmox (or a bare-metal box), with a Home Assistant button to power it on.
- **Households with several gaming PCs:** LanCache.

## Checklist

- [ ] Game servers on a host with fast single-core performance and local SSD; RAM allocated per game; auto-pause/sleep when empty.
- [ ] World/save directories in nightly backups (and snapshots); a restore tested once.
- [ ] Friends' access via Tailscale (preferred) or Playit.gg/relay; if port-forwarding, whitelist + online-mode + non-default port + updates.
- [ ] Panel (if used) behind the reverse proxy with TLS; Wings/agent daemons only reachable from the panel; admin accounts with MFA.
- [ ] ROM library organised per platform; RomM (or Gaseous) scanned with metadata; saves synced; hashes verified if desired.
- [ ] Streaming host reachable via Moonlight on the LAN with sub-20 ms latency; a wake/power-on mechanism for the gaming VM/PC.
- [ ] Mumble (or chosen voice) alongside for the group.
