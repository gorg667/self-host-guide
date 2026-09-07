# Planning Your Home Lab

The most expensive mistakes in self-hosting are made before any hardware is bought. This chapter is about the decisions that come first: what you actually want, how big to build, what it will cost in money and electricity and time, and where it will physically live. Read it even if you already own hardware — the questions still apply.

## Start with the services, not the hardware

The correct order is: decide what you want to *do*, derive the requirements, then choose hardware. The common order is the reverse, and it produces either a machine that cannot transcode 4K when the family wants to watch a film, or a 48-core dual-socket server that idles at 250 W running a Pi-hole.

Write down — actually write down — the services you intend to run in the first six months. Be honest and be specific. "Media server" is not specific; "Jellyfin, serving two simultaneous 1080p streams, occasionally one 4K HEVC stream to a TV that cannot direct-play it" is specific, and it tells you that you need a CPU with a hardware video encoder (see [Chapter 15](15-media.md)).

Then, for each service, note four things:

1. **Compute**: is it idle most of the time (almost everything), or does it need sustained CPU or a GPU (transcoding, AI inference, game servers, photo ML)?
2. **Memory**: most containers need 50–500 MB; a few (Nextcloud with its database, Immich with machine learning, GitLab, Home Assistant with many integrations, any LLM) need gigabytes.
3. **Storage**: capacity, growth rate, and whether it is *precious* (irreplaceable photos and documents) or *replaceable* (media you could re-acquire). This distinction drives your entire backup design.
4. **Availability**: what happens if it is down for a day? If the answer is "nothing," it can go on the same box as everything else. If the answer is "the house has no DNS and nobody can browse the web," it needs redundancy or at least a fallback.

A typical first list looks like this:

| Service | Compute | RAM | Storage | If down for a day |
|---|---|---|---|---|
| Pi-hole / AdGuard | negligible | 100 MB | negligible | Whole household loses DNS — needs a fallback |
| Jellyfin | bursty; transcoding needs iGPU | 500 MB–2 GB | Media library: 2–20 TB, replaceable | Annoying |
| Immich | ML bursts on upload | 2–4 GB | Photos: 200 GB–2 TB, **precious** | Phone keeps photos locally, fine |
| Vaultwarden | negligible | 50 MB | tiny, **precious** | Clients cache the vault, fine |
| Home Assistant | light | 1–2 GB | small, precious (config) | Lights still work via switches, automations stop |
| Nextcloud / Syncthing | light | 1 GB | Documents: 50–500 GB, **precious** | Annoying |
| Uptime Kuma | negligible | 100 MB | tiny | Nothing |

Sum the RAM (this one comes to ~8 GB with headroom), note the single "needs hardware transcode" requirement, note the split between precious and replaceable storage, and you have a hardware spec: a mini PC with an Intel iGPU, 16 GB RAM, a small SSD for the OS and containers, and a separate storage solution. That is a far more useful conclusion than "I should probably get a server."

## The three tiers

Throughout this guide, recommendations are grouped into three tiers. They are not rigid and most labs sit between two of them, but naming them makes it easier to talk about trade-offs. [Chapter 31](31-reference-architectures.md) gives a complete blueprint for each.

### Tier 1 — Starter

**One machine, ~10–25 W, USD 150–500 all in.** A mini PC (Intel N100/N150 or a used business desktop like a Lenovo ThinkCentre Tiny or Dell OptiPlex Micro), 16 GB RAM, an NVMe SSD for the system, and one or two USB or internal drives for data. Runs Debian or Ubuntu with Docker Compose, or a turnkey OS like CasaOS/Cosmos/Umbrel for people who want a GUI.

Good for: 5–20 containers, a household of 1–4, media streaming, photos, files, password manager, DNS, home automation.

Limitations: no storage redundancy (so backups are *not optional*), one point of failure, limited to what an iGPU can transcode.

This is where almost everyone should start, and where a large fraction of happy self-hosters stay forever.

### Tier 2 — Intermediate

**Two to three machines, ~40–100 W, USD 600–2,000.** Typically a compute node (a more capable mini PC or small-form-factor desktop running Proxmox) plus a dedicated NAS (TrueNAS, Unraid, or a commercial Synology/QNAP/UGREEN unit) with 4–8 drives in a redundant array, plus perhaps a Raspberry Pi or second mini PC for critical low-power services (DNS, VPN endpoint, monitoring) that should stay up when the main box is being rebuilt. A managed switch with VLANs and a proper router/firewall (OPNsense or similar).

Good for: 20–60 services, a household of several people plus extended family, network segmentation, proper backup targets, some VMs alongside containers.

Limitations: still a single site; more things to update; power bill becomes noticeable.

### Tier 3 — Advanced

**A rack or a shelf full of it, 100–400 W+, USD 2,000–10,000+.** Multiple hypervisor nodes (often clustered Proxmox with shared or replicated storage), 10 GbE or faster between nodes, a dedicated storage server with dozens of terabytes, a UPS that can carry the load through a real outage, a discrete GPU or two for AI workloads and transcoding, possibly a Kubernetes cluster because you want to learn it, and often a small VPS in the cloud as an ingress point and off-site backup target.

Good for: learning enterprise patterns, high availability, heavy AI/ML, serving dozens of users, running a small business.

Limitations: it is a part-time job. Electricity alone at 300 W is roughly USD 300–800 per year depending on where you live. Noise and heat become real problems. Complexity compounds.

!!! warning "Tier 3 is a destination, not a starting point"
    Almost nobody who starts at Tier 3 is still running it two years later. Almost everybody who starts at Tier 1 and grows to Tier 3 because their needs demanded it is still running it. Grow because you must, not because you can.

## Budget: the full picture

Hardware is the visible cost and usually not the largest one over a five-year horizon. Budget for all of it.

### Capital costs

- **Compute.** USD 100–300 for a used business mini PC with 16 GB RAM; USD 150–250 for a new N100/N150 box; USD 400–900 for a capable Ryzen or Core mini PC with 32–64 GB; USD 300–1,500 for a self-built SFF or tower.
- **Storage.** As of 2026, roughly USD 15–25 per TB for NAS-grade hard drives (cheaper per TB at larger capacities, 16–24 TB drives being the sweet spot), USD 50–80 per TB for consumer NVMe SSDs. Plan for the number of drives your redundancy scheme needs, not the number you would like to have (see [Chapter 6](06-storage.md)).
- **NAS enclosure or case.** USD 0 (use the mini PC's bays) to USD 300–800 (4–8 bay commercial NAS or a DIY case with hot-swap bays).
- **Networking.** USD 0 if you use the ISP router, USD 100–250 for a decent managed switch and a small firewall box. More for Wi-Fi access points, 10 GbE, or PoE.
- **UPS.** USD 100–250 for a 600–1,000 VA line-interactive unit adequate for a Tier 1–2 lab. Essential once you have a ZFS pool or anything else that dislikes unclean shutdowns. See [Chapter 29](29-power-cost-environment.md).
- **Miscellaneous.** Cables, a USB-to-serial adapter, a spare SSD, a label maker. Budget USD 50–100 and you will spend it.

### Recurring costs

- **Electricity.** The dominant recurring cost. Compute the annual cost as `watts × 8.76 × price_per_kWh`. A 15 W mini PC at USD 0.15/kWh is USD 20/year. A 150 W tower is USD 197/year. At European prices (USD 0.30–0.40/kWh) double those figures. [Chapter 29](29-power-cost-environment.md) covers measurement and reduction.
- **Off-site backup storage.** USD 5–7 per TB per month for Backblaze B2 or similar; a Hetzner Storage Box is cheaper at volume (roughly USD 4/month for 1 TB, USD 13/month for 5 TB as of 2026). A second machine at a friend's house costs electricity there and a favour.
- **Domain name.** USD 10–15/year. You want one; it makes TLS certificates trivial (see [Chapter 7](07-reverse-proxy-tls.md)).
- **VPS** (optional). USD 4–6/month for a small instance that acts as a public ingress point if you are behind CGNAT, or as a Headscale/Netbird coordinator, or as an Uptime Kuma instance watching your home from outside.
- **Drive replacements.** Assume a 2–5% annual failure rate per drive. With six drives, expect to replace one roughly every three to five years. Budget the cost of one drive per year and you will usually be under.
- **Your time.** Genuinely the largest cost. A Tier 1 lab needs perhaps two hours a month once stable. Tier 2 needs four to eight. Tier 3 can easily consume every weekend if you let it.

### A five-year cost example

Tier 1, a mini PC (USD 250) with two 8 TB drives (USD 320) and a small UPS (USD 120), drawing 20 W average at USD 0.20/kWh, with 1 TB of off-site backup and a domain:

| Item | Cost |
|---|---|
| Hardware (one-time) | USD 690 |
| Electricity (5 years) | USD 175 |
| Off-site backup (5 years, ~USD 6/mo) | USD 360 |
| Domain (5 years) | USD 65 |
| One drive replacement | USD 160 |
| **Total** | **USD 1,450** |

For comparison, 2 TB of mainstream cloud storage plus a streaming service plus a password manager subscription for the same household over five years is in the region of USD 1,500–2,500, and you would own nothing at the end of it. Self-hosting is not a way to save large amounts of money, but at Tier 1 it roughly breaks even while giving you vastly more capability and control. At Tier 3 it is a hobby with hobby-sized costs, and that is fine as long as you know it.

## Power, heat, noise, and space

These four are related and usually underestimated.

**Power** determines the electricity bill and the size of UPS you need. Modern mini PCs idle at 6–15 W. A used enterprise 1U or 2U server idles at 80–200 W *before* you add drives, and its fans are designed for a data centre. The single most impactful hardware decision for your running costs is choosing low-idle-power components. [Chapter 2](02-hardware.md) and [Chapter 29](29-power-cost-environment.md) go into detail.

**Heat** follows power: every watt becomes heat. 20 W is nothing. 300 W in a closet with no airflow will cook drives (which want to stay under about 40 °C for longevity) and eventually the room. If you are going beyond Tier 1, think about where the hot air goes.

**Noise** is the factor that gets hardware evicted from living spaces. A mini PC is silent or nearly so. A 4-bay NAS with hard drives produces a low hum and occasional clicking that most people tolerate in an office but not a bedroom. An enterprise server sounds like a hair dryer at idle and a jet engine under load; it needs a garage, basement, or a dedicated room. Check reviews for measured dB figures and be sceptical of anything described as "quiet" without a number.

**Space**: a mini PC fits behind a monitor. A NAS is the size of a toaster. A rack is a piece of furniture that needs floor space, clearance for airflow, and ideally a solid floor (a populated 24U rack can weigh 100–200 kg). Racks are wonderful for organisation and cable management and genuinely unnecessary for Tiers 1 and 2. If you want one anyway, a 12U wall-mount or a short open-frame rack is much more livable than a full-height enclosed cabinet.

!!! tip "Where to put it"
    The ideal location has: a wired Ethernet run back to your router (or is next to it), a power outlet that is not shared with a space heater or a vacuum cleaner, ambient temperature under about 27 °C year-round, no direct sunlight, low humidity, and is somewhere you will not trip over it. A closet with a door that can be left ajar, a utility room, or a basement shelf are common. Avoid attics (temperature swings) and the floor of anywhere that could flood.

## Internet connection realities

Your home lab's usefulness from outside the house depends on your internet connection in ways that are worth understanding before you plan remote access.

**Upload bandwidth** is the ceiling for anything you serve remotely: streaming a 4K film from home to a hotel needs 20–40 Mbps sustained upload. Many cable and DSL connections offer 10–40 Mbps up. Fibre often gives you symmetric 100 Mbps to 1 Gbps and changes what is practical. Check your actual measured upload, not the advertised figure.

**Public IPv4 address**: increasingly, ISPs put residential customers behind *carrier-grade NAT* (CGNAT), meaning you share a public IPv4 address with other customers and cannot forward ports at all. Cellular/5G home internet is almost always CGNAT. Some ISPs will give you a real public IP on request or for a small fee. If you are behind CGNAT, you can still do everything in this guide — but you will use a mesh VPN or a tunnel rather than port forwarding (see [Chapter 8](08-remote-access-vpn.md)). Find out which you have before designing your remote access. The test: compare the WAN IP your router reports with the IP a site like `ifconfig.me` shows. If they differ, you are behind CGNAT (or a double NAT of your own making).

**IPv6**: many ISPs now provide native IPv6, which gives every device a globally routable address and sidesteps CGNAT entirely for IPv6-capable clients. It is worth enabling and understanding ([Chapter 3](03-networking.md)), though you cannot rely on every remote network you connect from having IPv6.

**Dynamic IP**: most residential connections have a public IP that changes occasionally. This is a minor problem solved with dynamic DNS ([Chapter 9](09-dns-adblock.md)).

**ISP terms of service**: some ISPs prohibit "running servers" on residential connections. In practice this is almost never enforced against personal home labs with modest traffic, but it is worth reading your ToS ([Chapter 30](30-legal-ethical.md)). Business connections cost more and typically permit servers and include a static IP.

**Data caps**: if your ISP has one, off-site backups and remote streaming count against it. Initial backup seeding of several terabytes can blow through a monthly cap in a day.

## Decide your risk posture early

Two questions determine much of your design:

### What happens if this all disappears?

Divide your data into categories and decide the recovery requirement for each:

- **Irreplaceable** (family photos, personal documents, the password vault, years of notes): must survive a fire, theft, or ransomware. This *requires* an off-site copy, tested regularly. There is no shortcut.
- **Painful to lose** (service configuration, databases, Home Assistant history, Git repositories): should be backed up nightly, off-site if practical. Losing a week of it is annoying, not catastrophic.
- **Replaceable** (a media library that could be re-ripped or re-downloaded, Linux ISOs, Docker images): back up if convenient and cheap; otherwise accept the loss. Do not spend USD 500 protecting data you could recreate for USD 50 in time.

Then design storage and backups ([Chapter 6](06-storage.md) and [Chapter 11](11-backups.md)) around these categories rather than treating all data the same. Most people over-protect their media library and under-protect their photos.

### What happens if this is compromised?

Think about what an attacker who got onto your network — via an exposed service, a phishing email on a family laptop, or a cheap IoT device with a backdoor — could reach. If the answer is "everything, because it's all on one flat network with default passwords," then network segmentation and a proper authentication layer should be early priorities rather than afterthoughts. [Chapter 3](03-networking.md) covers VLANs; [Chapter 13](13-security.md) covers the rest.

A useful mental framing: **exposure is a cost you pay for convenience.** Every service exposed to the internet is a continuous liability. A mesh VPN gives you nearly the same convenience with a fraction of the exposure. Choose exposure deliberately, for services that genuinely need it (a public website, a service used by people who cannot install a VPN client), and put the rest behind the VPN.

## Choose your abstraction level

There is a spectrum from "turnkey appliance" to "bare Linux and a text editor," and where you sit on it determines both how much you learn and how much you can break.

| Approach | Examples | Learning | Control | Effort |
|---|---|---|---|---|
| Commercial NAS with app store | Synology DSM, QNAP QTS, UGREEN UGOS | Low | Low | Lowest |
| Turnkey self-hosting OS | Umbrel, CasaOS, Cosmos, YunoHost, TrueNAS Apps, Unraid Community Apps | Low–Medium | Medium | Low |
| Linux + Docker Compose (+ a GUI like Portainer/Dockge) | Debian, Ubuntu | Medium–High | High | Medium |
| Hypervisor + VMs/containers | Proxmox VE, XCP-ng | High | Very high | Medium–High |
| Declarative / IaC | NixOS, Ansible-managed hosts, k3s with GitOps | Very high | Very high | High up front, low later |

This guide's centre of gravity is **Linux + Docker Compose**, optionally on Proxmox, because it is the level at which the enormous majority of self-hosting documentation, community help, and project support is written. Turnkey systems are fine for getting started and for people who want an appliance; they are less fine when something breaks and the abstraction gets in the way. [Chapter 4](04-os-and-hypervisors.md) compares the options in depth.

!!! note "It is fine to not want to learn"
    Some people want a photo backup box that works, not a hobby. For them, a Synology or UGREEN NAS with Immich installed via Docker is a legitimate and good answer, and this guide's infrastructure chapters are largely optional. Be honest about which person you are.

## Time commitment and the sustainability check

Before buying anything, run the following thought experiment. Imagine it is eighteen months from now. You have moved house, or changed jobs, or had a child, or simply lost interest. Your lab is still running because the family depends on it. Something breaks.

- Can you fix it in an evening with the documentation you wrote?
- Can you restore from backup if you cannot fix it?
- Could you hand it to a technically competent friend with your notes and have them keep it running?
- If you were to shut it all down, could you get the data out in a standard format and move it elsewhere in a weekend?

If the honest answer to any of these is no, the design is too complex or the documentation is too thin for your circumstances. Simplify. The best home lab is the one that is still running — quietly, boringly, reliably — in five years.

## A planning checklist

Before proceeding to hardware:

- [ ] Listed the specific services for the first six months, with rough RAM/CPU/storage/availability notes.
- [ ] Classified data as irreplaceable / painful / replaceable and know the approximate volume of each.
- [ ] Chosen a tier and know roughly what it costs in hardware, electricity, and time.
- [ ] Know whether you have a public IPv4 address, CGNAT, and/or native IPv6.
- [ ] Measured your upload bandwidth.
- [ ] Picked a physical location with power, wired Ethernet, cooling, and tolerance for the noise level of your chosen hardware.
- [ ] Decided how much you want to expose to the internet (ideally: as little as possible) and how you will do remote access instead.
- [ ] Decided your abstraction level: appliance, turnkey OS, Docker on Linux, or hypervisor.
- [ ] Registered a domain name (or decided you will).
- [ ] Have a plan — even a rough one — for off-site backup of irreplaceable data from day one.

With this done, [Chapter 2](02-hardware.md) will feel like shopping with a list rather than browsing with a credit card.
