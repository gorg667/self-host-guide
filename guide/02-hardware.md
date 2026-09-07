# Hardware: Choosing What to Run It On

Hardware is where planning meets a credit card. This chapter covers every category of machine people run home labs on — mini PCs, used business desktops, used enterprise servers, single-board computers, commercial NAS units, and DIY builds — with honest trade-offs, followed by the components that matter most: storage drives, memory, network interfaces, switches, UPS units, racks, and GPUs.

The headline recommendation, stated once here and justified below: **for most people in 2026, the right first machine is a low-power x86 mini PC with an Intel iGPU, 16–32 GB of RAM, and an NVMe SSD, paired with a separate storage solution sized to your data.** Everything else in this chapter is about when and why to deviate from that.

## Guiding principles

**Idle power is the number that matters.** Your lab will spend 95% of its life idle. A machine that idles at 8 W costs USD 10–25 a year to run; one that idles at 120 W costs USD 150–400. Over five years the difference pays for the machine several times over. Always look for measured idle power figures in reviews, and be suspicious of any spec sheet that lists only TDP (which is a thermal design figure, not a consumption figure).

**Used business hardware is the value sweet spot.** Corporations lease desktops for three years and dump them by the pallet. A three-year-old Lenovo ThinkCentre M-series Tiny, Dell OptiPlex Micro, or HP EliteDesk/ProDesk Mini with an 8th-gen or newer Intel Core i5, 16 GB of RAM, and a 256 GB NVMe sells for USD 100–200. These machines are quiet, sip power (8–15 W idle), have Intel Quick Sync for transcoding, and are extraordinarily reliable. The community calls them "TinyMiniMicro" after a well-known review series.

**Buy ECC when it is cheap, don't agonise when it isn't.** Covered in detail below; the short version is that ECC memory is a nice-to-have for a home ZFS NAS, not a requirement, and the internet has spent far too much energy arguing otherwise.

**Buy drives for the workload, not the brand.** CMR vs SMR matters far more than Seagate vs Western Digital. Details below.

**Do not buy enterprise rack servers as a first machine.** They are cheap on eBay for a reason: they are loud, hot, power-hungry, and their hardware RAID controllers and proprietary parts make them awkward. They are wonderful for learning enterprise patterns and for people with a basement and a tolerance for a USD 40/month electricity bump. They are a terrible choice for a first lab.

## Category 1: Mini PCs

The mini PC category has exploded since roughly 2022, driven by Intel's N-series (N100, N150, N305, N355) and AMD's Ryzen mobile chips finding their way into palm-sized boxes from dozens of mostly Chinese brands (Beelink, GMKtec, Minisforum, Aoostar, Trigkey, and many others) plus the established players (Intel NUC — now made by ASUS — Lenovo, Dell, HP).

### Intel N100 / N150 / N305 / N355 boxes

The Intel N100 (and its refresh, the N150) is a four-core, four-thread part with no hyperthreading, a 6 W TDP, and a surprisingly capable iGPU with Quick Sync that handles multiple simultaneous 4K HEVC/AV1 transcodes. Boxes built around it sell for USD 130–220 with 16 GB of RAM and a 500 GB SSD. They idle at 6–10 W.

The N305 and N355 are the eight-core siblings with roughly double the multi-threaded performance for USD 80–150 more. Worth it if you plan to run more than about 20 containers or anything CPU-bound.

**Good for:** Tier 1 labs, dedicated DNS/VPN/monitoring node, Home Assistant, media serving with hardware transcoding, small NAS duty (some models have 2–4 SATA bays or two NVMe slots).

**Watch out for:**

- Most N100 boards officially support only 16 GB of single-channel DDR4/DDR5 in one SODIMM slot. 32 GB SODIMMs generally *work* but are not guaranteed. The single-channel memory is a real bottleneck for memory-bandwidth-heavy work (AI inference, heavy databases).
- Cheap brands ship with cheap SSDs and cheap RAM. Budget to replace both, or buy barebones.
- Some units have poor thermal design and will throttle under sustained load. Look for reviews that test sustained performance.
- Firmware quality varies enormously; some have BIOS bugs affecting power states (which hurts idle power) or PCIe ASPM. The Intel-branded and major-OEM units are more predictable.
- 2.5 GbE is now standard; some boxes have two or four ports and are marketed as firewall appliances. They make excellent OPNsense boxes.

### Ryzen and Core mini PCs (the performance tier)

Minisforum, Beelink, GMKtec and others sell boxes around AMD Ryzen 7/9 mobile parts (7840HS, 8845HS, AI 9 HX 370, and successors) or Intel Core Ultra chips. These have 8–16 cores, support 64–96 GB of dual-channel RAM, have two or three NVMe slots, and often include USB4/Thunderbolt and 2.5 GbE ×2. They idle at 10–20 W and cost USD 400–900 barebones.

**Good for:** Proxmox hosts running many VMs, Tier 2 compute nodes, anything memory-hungry. Ryzen's iGPU (RDNA 3 in the 7840/8845 generation) transcodes competently via VAAPI, though Intel Quick Sync remains the more reliable choice for Jellyfin/Plex.

**Watch out for:** Ryzen mobile boxes have historically had more fiddly Linux support for iGPU passthrough and power management than Intel; this has improved a lot but check the community forums for your specific model. AMD's ECC story on these platforms is non-existent.

### Intel NUC and OEM ultra-small-form-factor

The Intel NUC line (now ASUS NUC) and the OEM "1-litre" machines (Lenovo ThinkCentre Tiny, Dell OptiPlex Micro, HP EliteDesk Mini) are the reliable, boring, well-documented option. New units cost more than the Chinese boxes for the same spec; used units cost less. They have proper firmware, vPro/AMT remote management on some models (a poor man's IPMI), and are supported by every Linux distribution without drama.

**Watch out for:** used units often come with the minimum RAM and a small SSD; budget for upgrades. Many OEM Tiny/Micro units have a single 2.5" SATA bay plus one NVMe slot; storage expansion means USB or a NAS.

### Mini PC as NAS?

A growing sub-category (Aoostar, Beelink ME mini, Ugreen NASync DXP, TerraMaster F-series, Minisforum N5) puts an N100/N305/Ryzen board in a case with 2–6 drive bays. These blur the line between mini PC and NAS and are excellent Tier 1–2 all-in-one machines when running TrueNAS, Unraid, or plain Debian.

## Category 2: Used business desktops (small form factor and towers)

One step up from the 1-litre Tiny units are the SFF (small form factor) and MT (mini tower) versions of the same corporate lines: Dell OptiPlex SFF/Tower, Lenovo ThinkCentre M-series SFF, HP EliteDesk/ProDesk SFF, and — very popular in the homelab community — the Lenovo ThinkStation P-series and Dell Precision workstations, and HP Z-series.

**Why they are excellent:** an SFF gives you a real PCIe slot or two (for a 10 GbE NIC, an HBA, or a small GPU), 2–3 internal 3.5"/2.5" drive bays, four RAM slots (64–128 GB), and still idles at 15–30 W. Used 8th–12th gen Core i5/i7 SFFs cost USD 120–300. Entry workstations (ThinkStation P340/P350/P360, Dell Precision 3640/3650/3660) add Xeon-E or Core options with ECC support on some configurations.

**Watch out for:** proprietary PSUs with limited wattage and odd connectors (adding a GPU may be impossible), limited drive bays (SFF usually maxes out at two 3.5" drives), and low-profile PCIe slots only. Check the exact model's spec sheet.

## Category 3: Used enterprise servers

Dell PowerEdge (R720, R730, R740, T-series towers), HPE ProLiant (DL360/DL380 Gen9/Gen10, ML towers), Lenovo/IBM System x, and Supermicro chassis are available used from USD 200 to USD 1,500 depending on generation. They offer dual sockets with 20–56 cores, 128–768 GB of registered ECC RAM, 8–24 hot-swap drive bays, redundant power supplies, and real out-of-band management (iDRAC, iLO, IPMI).

**Why people buy them:** the specs per dollar are absurd, they are built for 24/7 operation, hot-swap everything is genuinely convenient, IPMI is wonderful, and running one teaches you how real data centres work.

**Why people regret them:**

- **Power.** A dual-socket R730 with a few drives idles at 100–150 W. That is USD 130–500 a year. Older generations (R710, DL380 G7) are worse and should be avoided entirely.
- **Noise.** 1U servers are unbearable in living space — 40–60 dB at idle, screaming under load. 2U is better, towers (T-series, ML-series) are quite tolerable. Fan-speed hacks exist for some models via IPMI.
- **Heat.** Every watt is heat in the room.
- **Hardware RAID.** Enterprise controllers (PERC, Smart Array) in RAID mode hide disks from the OS, which is exactly what you do not want for ZFS. Most can be flashed to "IT mode" (pass-through) or replaced with an LSI 9211/9300-series HBA for USD 20–40; budget the time to research your model.
- **Proprietary parts.** Drive caddies, PSUs, and fans are vendor-specific. Some vendors (HPE notably) lock firmware updates behind support contracts.
- **Old CPUs are slow per-core.** A 2014-era Xeon E5-2680v3 has 12 cores but each is slower than a modern N100 core. Single-threaded tasks feel sluggish.

**If you want one anyway:** a tower (Dell T340/T350/T440, HPE ML350 Gen10) or a 2U (R730xd, DL380 Gen10) with a single CPU populated, an IT-mode HBA, and the fans on a quiet profile is livable in a basement or garage. Gen10/14th-gen (Skylake-SP) or newer is the sensible floor for power efficiency and remaining useful life.

## Category 4: Single-board computers

The Raspberry Pi launched a thousand home labs, and it remains a fine choice for specific roles — but it is no longer the default it once was.

### Raspberry Pi 5

The Pi 5 (4 or 8 GB, and 16 GB as of 2025) is a real computer: quad-core Cortex-A76, a PCIe 2.0 lane (used via HAT for NVMe), Gigabit Ethernet, USB 3. It idles at about 3 W and costs USD 60–120 plus case, power supply, and storage. The official M.2 HAT+ or third-party NVMe HATs make it robust; **do not run a Pi from a microSD card for anything you care about** — they wear out and corrupt.

**Good for:** Pi-hole/AdGuard, a WireGuard or Tailscale exit node, Home Assistant (very well supported), Uptime Kuma, a secondary DNS, Zigbee/Z-Wave coordinator host, a small Kubernetes learning cluster.

**Not good for:** media transcoding (no hardware encoder), anything x86-only (some Docker images have no ARM builds, though this is now rare), anything needing more than 8–16 GB RAM, NAS duty with multiple drives.

The cost argument for the Pi has largely evaporated: a Pi 5 8 GB with case, PSU, and an NVMe HAT and SSD costs USD 130–160, and an N100 mini PC with 16 GB and a 500 GB SSD costs about the same while being several times faster and having a transcoder. The Pi's advantages are now its 3 W idle, its GPIO, its size, and its exceptional documentation and community.

### Other SBCs

Orange Pi, Radxa Rock, ODROID, Banana Pi, and the Rockchip RK3588 boards (Orange Pi 5, Rock 5B) offer more cores, more RAM (up to 32 GB), and sometimes NVMe and 2.5 GbE at competitive prices. Software support is the weak point: kernels lag, images are vendor-specific, and hardware acceleration is often half-working. For a lab, they are for people who enjoy that kind of fight. The ODROID-H series is an exception — it is an x86 (Intel N-series) board in SBC form and is popular as a low-power NAS board.

## Category 5: Commercial NAS appliances

Synology, QNAP, and newer entrants (UGREEN, TerraMaster, Asustor) sell finished boxes with 2–12 bays, a polished OS, mobile apps, and an app store.

**Synology** has long been the default recommendation for "I want a NAS that just works." DSM is excellent, Synology Photos and Drive are genuinely good, Hyper Backup and Snapshot Replication are solid. Downsides: the hardware is weak and expensive for what it is (many current models still ship with years-old Celeron or Ryzen embedded parts and 2–4 GB of RAM), and as of 2025 Synology moved to requiring Synology-branded drives on Plus-series models for full functionality — a decision that alienated much of the enthusiast community and is worth checking the current state of before buying.

**QNAP** offers stronger hardware for the money (2.5 GbE standard, more RAM, HDMI out on some), a less polished OS, and a worse security track record — several ransomware campaigns have specifically targeted internet-exposed QNAP units. Never expose a QNAP (or any NAS) directly to the internet.

**UGREEN NASync** arrived in 2024 with strong hardware (Intel N-series or Core i5, 8–16 GB, 2.5/10 GbE, NVMe slots) at aggressive prices and an OS that is improving rapidly. Notably, UGREEN officially permits installing third-party OSes (TrueNAS, Unraid, Proxmox), making them attractive as DIY NAS hardware with a warranty.

**TerraMaster and Asustor** are similar propositions: decent hardware, less mature software, both tolerant of third-party OS installs.

**Should you buy one?** If you want an appliance and are willing to pay a premium for the software, Synology remains good (drive-lock caveat noted). If you want the hardware and will run TrueNAS or Unraid, UGREEN is the current value pick. If you want to learn and have the time, a DIY NAS (below) is cheaper and more capable.

## Category 6: DIY builds

Building your own gives you complete control over power, noise, expansion, and drive count. The two common patterns:

### The low-power NAS build

A Micro-ATX or ITX board with an efficient CPU (Intel Core i3-12100/13100/14100 or i5 non-K, or the Intel N-series on an ITX board), 16–64 GB RAM, a case with 6–12 drive bays (Fractal Design Node 304/804, Jonsbo N2/N3/N4/N5, Sagittarius, the venerable Fractal Define R5/7 with extra drive cages), a Gold or Platinum PSU sized *small* (a 450–550 W unit runs more efficiently at low load than an 850 W unit), and an LSI HBA if you need more SATA ports than the board provides. Such a build idles at 20–35 W with drives spun down and costs USD 500–900 before drives.

Intel 12th–14th gen with an iGPU is the community favourite here because Quick Sync is excellent, the C-state power management is good (C8–C10 idle achievable with care), and the platform is well-understood. See [Chapter 29](29-power-cost-environment.md) for tuning.

### The compute/virtualisation build

A Ryzen 7/9 or Core i7/i9 on a board with plenty of PCIe lanes, 64–128 GB RAM, several NVMe drives, a 2.5 or 10 GbE NIC, and space for a GPU. This is a Proxmox host or a workstation-class machine for AI work. Idle power is 40–80 W depending on discipline. If you want ECC, AMD Ryzen on a board that supports it (many ASRock and some ASUS boards do — check the QVL) with unbuffered ECC UDIMMs is the affordable path; Intel restricts ECC to Xeon-E/W and a few Core parts on W680 boards.

!!! tip "The 'one big box' vs 'compute + NAS' decision"
    Combining compute and storage in one machine (a DIY NAS running Proxmox or TrueNAS with apps) is simpler and cheaper. Separating them means you can reboot or rebuild the compute node without taking storage offline, and keeps your data on a machine that changes rarely. Tier 1: one box. Tier 2: usually two. Tier 3: definitely two or more.

## Storage drives

This section matters more than any other in the chapter. Drives are where your data lives, they are the component most likely to fail, and the market is full of traps.

### Hard drives: CMR vs SMR

This is the single most important thing to know when buying hard drives.

**CMR (Conventional Magnetic Recording)** writes tracks side by side. Performance is consistent for reads and writes. **SMR (Shingled Magnetic Recording)** overlaps tracks like roof shingles to increase density. Reads are fine; *sustained writes* are catastrophically slow once the drive's small CMR cache area fills, because rewriting one track means rewriting all the tracks that overlap it.

SMR drives in a RAID or ZFS array are a disaster: a rebuild/resilver, which is a sustained multi-terabyte write, can take days instead of hours, and the drive may time out and get kicked from the array during the process — leading to a second "failure" and potential data loss. Western Digital was caught quietly shipping SMR drives in its WD Red NAS line in 2020 and was sued over it; the industry now generally discloses.

**Rule: for any array, buy only CMR drives.** Currently CMR lines include WD Red Plus and Red Pro, Seagate IronWolf and IronWolf Pro, Toshiba N300, and essentially all enterprise drives (WD Ultrastar/Gold, Seagate Exos, Toshiba MG-series). SMR lines to avoid for arrays: WD Red (non-Plus), WD Blue at many capacities, Seagate Barracuda at many capacities, most "archive" drives. Manufacturers publish CMR/SMR lists; check the specific model number, not the product line.

### Which hard drive tier?

| Tier | Examples | Warranty | Workload rating | Notes |
|---|---|---|---|---|
| Desktop | WD Blue, Seagate Barracuda | 2 yr | ~55 TB/yr | Often SMR. Avoid for arrays. |
| NAS | WD Red Plus, Seagate IronWolf, Toshiba N300 | 3 yr | 180 TB/yr | CMR. Fine for home NAS. Rotational vibration sensors. |
| NAS Pro | WD Red Pro, IronWolf Pro | 5 yr | 300–550 TB/yr | 7200 rpm, louder, slightly more power. |
| Enterprise | WD Ultrastar / Gold, Seagate Exos, Toshiba MG | 5 yr | 550 TB/yr | Often *cheaper per TB* than NAS Pro. Louder. Best value at 16–24 TB. |

Enterprise drives are frequently the best buy for a home NAS: they are CMR, have five-year warranties, and because they are sold in volume to data centres they are often cheaper per terabyte than the consumer NAS lines. The downsides are noise (idle seek chatter is audible) and slightly higher power (7–9 W active, 5–6 W idle). Check reputable price trackers (diskprices.com is the community standard) and buy from a seller with a real return policy.

**Shucking** — buying external USB drives (WD Elements/My Book, Seagate Expansion) and removing the internal drive — used to be the cheapest route to CMR enterprise-class drives. It still sometimes is, but the discount has narrowed, warranties become murky, and some shucked WD drives need a 3.3 V pin mod (tape over pin 3) to spin up in some backplanes. It is a hobby within a hobby.

**Refurbished and recertified drives** from reputable sellers (ServerPartDeals and similar) offer manufacturer-recertified enterprise drives at 30–50% discounts with 2–5 year seller warranties. Community experience is largely positive; the key is buying from a seller who honours the warranty. Reasonable for replaceable data with parity protection; think twice for a single-copy archive of family photos.

### How many drives, what capacity?

Buy fewer, larger drives. Six 8 TB drives cost more, draw more power, and have more failure points than three 16 TB drives with the same usable capacity under RAIDZ1/RAID5. Larger drives do take longer to rebuild (a 20 TB drive resilvers in roughly 24–36 hours), which is the argument for two-drive redundancy (RAIDZ2/RAID6) at large capacities. [Chapter 6](06-storage.md) covers the arithmetic.

Buy from at least two different batches or vendors when buying a set. Drives from the same batch have correlated failure characteristics.

### SSDs

**Boot/OS and container storage**: any decent NVMe SSD (Samsung 980/990 Pro, WD SN770/SN850X, Crucial P3 Plus/T500, Kingston KC3000, SK Hynix P41/P44) is fine. 500 GB–1 TB is plenty. Docker images and container volumes on NVMe make everything feel snappy.

**Databases and VM storage**: endurance matters. Look at the TBW (terabytes written) rating; consumer drives are 300–1,200 TBW, enterprise drives are 3,000–20,000+. Used enterprise SATA/U.2/M.2 SSDs (Intel D3-S4510/S4610, Samsung PM883/PM893/PM9A3, Micron 5300/7450) are excellent value on eBay and have power-loss protection, which consumer drives lack.

**ZFS special vdevs, SLOG, L2ARC**: only enterprise drives with power-loss protection are appropriate for SLOG; a consumer drive here can *lose* the data it was meant to protect. Most home labs do not need any of these; see [Chapter 6](06-storage.md).

**All-flash NAS**: with 4 TB NVMe drives at USD 200–300 and 8 TB at USD 500–800, all-flash storage for everything but bulk media is now practical. Silence, low power, and speed are the payoff; cost per TB is 4–6× spinning rust.

!!! warning "QLC and DRAM-less SSDs"
    Cheap SSDs use QLC NAND and omit the DRAM cache. They are fine for a boot drive and for read-heavy media, and terrible for sustained writes and for anything database-like; write speed can fall below that of a hard drive once the SLC cache fills. For anything but the most cost-constrained cold storage, prefer TLC with DRAM.

### SMART and drive health

Every drive reports Self-Monitoring, Analysis and Reporting Technology data. The attributes that predict failure most reliably are **Reallocated Sectors Count (5)**, **Current Pending Sector Count (197)**, **Offline Uncorrectable (198)**, and **UDMA CRC Error Count (199, usually a cable problem)**. Any non-zero and rising value on 5, 197, or 198 means the drive is dying; replace it. Run `smartctl -a /dev/sdX` (from `smartmontools`) and set up automated monitoring with Scrutiny ([Chapter 12](12-monitoring.md)). Schedule a long self-test monthly.

## Memory

**How much?** 16 GB runs a Tier 1 lab comfortably. 32 GB runs a Tier 2 Docker host with room. 64 GB+ is for Proxmox hosts running several VMs, ZFS with large ARC, or AI workloads. RAM is cheap; over-provision.

**ZFS and RAM.** The old "1 GB per TB" rule is a myth for home use (it originated with deduplication, which you should not enable). ZFS uses free RAM as a read cache (ARC) and gives it back when needed. 8 GB is a workable minimum; 16 GB is comfortable; more just makes the cache bigger.

### ECC: the eternal argument

Error-Correcting Code memory detects and corrects single-bit errors caused by cosmic rays, electrical noise, and marginal hardware. Without it, a flipped bit in RAM can silently corrupt data before it is written to disk — and ZFS's checksums cannot help, because ZFS will faithfully checksum the corrupted data.

The community argument: "ZFS without ECC is dangerous" (a stance popularised on the FreeNAS forums circa 2013) versus "ECC is nice but the risk is overstated for home use" (the more measured modern view, which is also essentially Matt Ahrens' — ZFS co-creator — position: ZFS without ECC is no *worse* than any other filesystem without ECC, and the "scrub of death" scenario is a myth).

Practical guidance:

- ECC is genuinely better. If it costs you little to get it, get it.
- ECC is available cheaply on: used workstations and servers (registered DIMMs are very cheap used), AMD Ryzen on supporting motherboards with unbuffered ECC UDIMMs (verify with `dmidecode` and `edac-util` that it actually works — some boards accept ECC DIMMs without enabling ECC), and Intel Xeon-E / W680 platforms.
- ECC is essentially unavailable on: mini PCs, N-series boards, laptops, most consumer Intel desktop boards.
- If your only option is a mini PC without ECC, run ZFS or Btrfs anyway. Checksumming filesystems still protect against the far more common failure modes — bit rot on disk, bad cables, failing drives — which happen orders of magnitude more often than RAM-induced corruption.
- Do not let the absence of ECC stop you from starting. Do not let its presence make you complacent about backups.

## Network interfaces and switches

**1 GbE** is the baseline and remains adequate for most Tier 1 labs: it moves 110 MB/s, faster than most spinning drives sustain and enough for several simultaneous 4K streams.

**2.5 GbE** has become standard on mini PCs and mid-range motherboards and is the sensible current sweet spot. Unmanaged 2.5 GbE switches cost USD 50–100 for 5–8 ports; managed ones with VLAN support USD 100–250. Realtek 2.5 GbE chipsets (RTL8125) are ubiquitous and fine on Linux with a modern kernel; Intel i225/i226 had teething issues in early revisions but are stable now.

**10 GbE** is for moving large files between a NAS and a workstation, for storage networks between hypervisor nodes, and for all-flash arrays. Used Intel X520/X710 or Mellanox ConnectX-3/4 SFP+ cards cost USD 20–60; direct-attach copper (DAC) cables connect two machines without a switch. Switches with a few SFP+ ports (MikroTik CRS305/CRS309/CRS310, TP-Link TL-SX3008F, Zyxel, QNAP) cost USD 130–300. Note that 10GBase-T (RJ45) draws 2–5 W per port and runs hot; SFP+ with DAC or fibre is cooler and cheaper for short runs.

**Managed switches**: you want one as soon as you want VLANs ([Chapter 3](03-networking.md)). Popular choices: MikroTik (excellent hardware, RouterOS/SwOS have a learning curve), TP-Link Omada and Ubiquiti UniFi (controller-based, polished, popular), Netgear (fine, boring), Zyxel, and used enterprise (Cisco, Brocade/Ruckus ICX, Aruba — cheap, loud fans, CLI-driven, fantastic for learning). PoE ports are worth having if you plan Wi-Fi access points or cameras.

## Uninterruptible power supplies

A UPS gives you two things: continuity through brief outages and flicker (very common), and time to shut down cleanly during longer ones. The second matters enormously for storage: ZFS and Btrfs are robust against power loss by design, but drives with write caches, hardware RAID without a battery, and any database mid-transaction are not.

**Sizing**: measure your lab's draw (a plug-in power meter is USD 15–25), add 30% headroom, and buy a UPS whose *watt* rating (not VA — VA is roughly watts × 1.6 for these units) exceeds it. A Tier 1 lab at 30 W wants a 600–850 VA unit, which will run it for an hour or more. A Tier 2 lab at 100 W wants 1,000–1,500 VA for 15–30 minutes.

**Type**: line-interactive (APC Back-UPS Pro, CyberPower CP-series, Eaton 5E/5S) is right for home labs. Pure sine wave output is preferable for active-PFC power supplies (which is every modern PSU). Standby/offline units are cheaper and adequate for a mini PC. Online/double-conversion is overkill and inefficient for a home.

**Communication**: the UPS must talk to your servers so they shut down before the battery dies. USB is standard; the **NUT** (Network UPS Tools) daemon runs on one machine as master and notifies others over the network. [Chapter 29](29-power-cost-environment.md) has a NUT walkthrough. Some UPS units have a network management card slot; the cards are useful but cost more than the UPS.

**Batteries** last 3–5 years and are user-replaceable (USD 30–80). Lithium-ion UPS units (Eaton, CyberPower) are appearing with longer battery life and lower weight at a price premium.

Brands: APC (Schneider) and Eaton are the safe defaults; CyberPower is the value pick and its Linux support (via NUT or `pwrstat`) is good. Avoid no-name units.

## Racks and mounting

You do not need a rack until you have three or more rack-mount devices. Before that, a shelf, a wire rack from a hardware store, or an IKEA Lack table (the "Lack rack" — its inner width almost exactly fits 19" equipment — is a decades-old community joke that actually works) is fine.

When you do: a **wall-mount 6–12U** for a switch, patch panel, and a couple of shallow devices; an **open-frame 4-post 12–25U** for a mix of servers and shelves; an **enclosed cabinet** only if you need dust protection or noise dampening (and note that enclosed cabinets restrict airflow). Rack depth matters — many home-lab-friendly cases and used servers are 60–75 cm deep; short-depth racks will not fit them. Check before buying either.

Rack shelves let you mount mini PCs, NAS units, and anything else non-rack-format. Rack-mount PDUs are convenient; a smart PDU with per-outlet switching is a luxury that pays for itself the first time you need to power-cycle a hung machine remotely.

## GPUs

For most self-hosters, the integrated GPU in an Intel CPU is the only GPU needed: Quick Sync handles transcoding for Jellyfin/Plex/Emby, and Frigate can use OpenVINO on the iGPU for object detection. Discrete GPUs enter the picture for three reasons:

**Transcoding at scale.** An Intel Arc A310/A380 (USD 90–130, single-slot, low-profile options exist, ~5–20 W) adds AV1 encode and a second Quick Sync engine to any machine, including AMD-based ones. This is the best transcoding upgrade available.

**Local AI.** Large language models, image generation, speech models, and photo ML (Immich's smart search, Frigate's detection) benefit enormously from a GPU. Here VRAM is the constraint that matters: LLM size in parameters × bytes per parameter at your quantisation ≈ VRAM needed. A 7–8 B parameter model at 4-bit fits in 6 GB; a 14 B model needs 10–12 GB; 32 B needs 20–24 GB; 70 B needs 40+ GB or two cards. NVIDIA has the most mature software stack (CUDA is what everything targets first); the used RTX 3090 (24 GB, USD 600–800) and RTX 3060 12 GB (USD 200–250) are perennial value picks, and the RTX 4060 Ti 16 GB and 5060 Ti 16 GB are efficient mid-range choices. AMD's ROCm works for many workloads (Ollama, llama.cpp, Stable Diffusion) and the RX 7900 XTX at 24 GB is cheaper than NVIDIA equivalents; Intel Arc works via IPEX/SYCL for llama.cpp and Ollama with less polish. Apple Silicon Macs with unified memory (a Mac Mini/Studio with 64–192 GB) are an unconventional but effective LLM server. [Chapter 23](23-ai-llm.md) covers all of this in depth.

**Passing through to a VM or game-streaming.** A GPU passed to a Windows VM for a Sunshine/Moonlight streaming setup ([Chapter 24](24-gaming.md)), or to a Linux desktop VM. Requires IOMMU support (nearly universal now) and some Proxmox configuration.

**Power and PCIe.** A discrete GPU adds 10–30 W at idle and hundreds under load, and needs a real PCIe slot and often a PSU upgrade. Older NVIDIA cards (pre-Turing) idle poorly under Linux without `nvidia-persistenced` and tuning. Decide whether a GPU belongs in the always-on server or in a separate machine that sleeps when not in use.

## Sample builds

Three concrete configurations, with approximate 2026 prices, as anchors.

### Starter: silent all-in-one, ~USD 350 + drives

- Used Lenovo ThinkCentre M920q / Dell OptiPlex 7080 Micro, Core i5-8500T or better, 16 GB → USD 130–180
- Upgrade: 32 GB DDR4 SODIMM kit → USD 50; 1 TB NVMe → USD 60
- Storage: two 8 TB CMR drives in a two-bay USB 3 enclosure (Terramaster D2-310 or similar) as a mirrored Btrfs/ZFS pool → USD 320 + USD 80
- UPS: CyberPower CP600/CP850 → USD 80–110
- Idle: ~15 W. Runs Debian + Docker with 20–30 containers, Jellyfin with Quick Sync, Immich, Nextcloud, Vaultwarden, AdGuard.

### Intermediate: separate compute and storage, ~USD 1,200 + drives

- Compute: Minisforum/Beelink Ryzen 7 8845HS or Intel Core Ultra mini PC, 64 GB, 2× 1 TB NVMe → USD 550–700; runs Proxmox.
- NAS: Jonsbo N3 (8-bay) with Intel i3-12100, 32 GB, a 500 GB NVMe boot drive, an efficient 450 W PSU → USD 450–550; runs TrueNAS SCALE with 4–6 × 16–20 TB enterprise drives in RAIDZ2.
- Network: MikroTik CRS310-8G+2S+ (2.5 GbE ×8, SFP+ ×2) → USD 200; a small N100 dual-NIC box for OPNsense → USD 150.
- UPS: 1,000–1,500 VA → USD 150–220.
- Idle: 60–90 W total.

### Advanced: clustered, ~USD 3,000–6,000

- 3× compute nodes (mini PCs or SFF workstations with 64–128 GB, dual 2.5 or 10 GbE) in a Proxmox cluster with Ceph or ZFS replication.
- Storage server: 12–24 bay chassis (Supermicro 846, Fractal Define 7 XL, or a rack-mount Rosewill/Sliger) with Xeon-E or Ryzen ECC, 64–128 GB, HBA, 10 GbE, 8–16 drives.
- GPU node: a workstation or SFF with an RTX 3090/4090 or a pair of 16–24 GB cards for AI.
- Network: 10 GbE SFP+ switch as core, 2.5 GbE PoE access switch, OPNsense on dedicated hardware or as a VM with NIC passthrough.
- UPS: 2–3 kVA online or line-interactive, possibly with extended battery.
- Rack: 18–25U four-post, PDU, patch panel.
- Idle: 200–400 W. Electricity becomes a line item you notice.

## Buying checklist

- [ ] Idle power figure known from a measured review, not inferred from TDP.
- [ ] Transcoding requirement confirmed against CPU/iGPU capability (Intel Quick Sync for Jellyfin/Plex is the safe choice).
- [ ] RAM capacity ceiling and slot count checked; ECC decision made consciously.
- [ ] Every hard drive confirmed CMR by model number.
- [ ] Drive count and capacity derived from the redundancy scheme in [Chapter 6](06-storage.md), not the reverse.
- [ ] SSD endurance adequate for the workload (databases/VMs want TLC with DRAM, ideally enterprise with PLP).
- [ ] Network ports match the switch you have or plan to buy.
- [ ] UPS sized to measured draw plus headroom, with USB or network communication to the host.
- [ ] Physical location can handle the noise and heat of what you are buying.
- [ ] Budget includes the boring things: cables, a spare drive, a power meter.
