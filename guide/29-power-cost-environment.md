# Power, Cost, and the Physical Environment

Electricity is the recurring cost of a home lab, heat is its by-product, noise is what gets it evicted from the living room, and a power cut is its most common unplanned outage. This chapter is the practical physics: how to measure what your lab draws, what it costs, where the watts go and how to cut them (C-states, ASPM, drive spin-down, right-sizing PSUs, GPU idle), how to manage heat and noise, and how to survive power problems with a UPS and Network UPS Tools so that a blackout means a clean shutdown rather than a corrupted pool. It ends with a worked cost model at each tier and the honest observation that a well-chosen lab costs less to run than a games console left on standby.

## Measure first

You cannot optimise what you have not measured, and spec sheets lie. Two tools:

- **A plug-in power meter** (Kill A Watt in the US; a TP-Link Tapo P110 or Shelly Plug S / Plus Plug with energy monitoring anywhere — the smart plugs also log to Home Assistant): USD 10–25. Plug the whole lab (or each device) in and read watts, and kWh over a day. Measure *idle* (nothing happening, drives spun down if applicable), *typical* (normal background activity), and *peak* (a transcode, a scrub, an LLM query).
- **Software** for what is happening *inside*: `powertop` (Intel/AMD: shows C-state residency — the percentage of time the CPU package spends in deep sleep — and lists tunables), `turbostat` (package power in watts on Intel), `s-tui`, `nvidia-smi` / `rocm-smi` / `intel_gpu_top` for GPUs, `hdparm -C /dev/sdX` (drive spin state), `sensors` (temperatures), and the UPS's own load reading via NUT.

Then the arithmetic:

```
annual kWh  = average watts × 8.76
annual cost = annual kWh × price per kWh
```

At USD 0.15/kWh: every **continuous watt costs USD 1.31/year**. At EUR 0.35/kWh (much of Europe in 2026): **EUR 3.07/year per watt**. A 100 W difference between two designs is USD 130–300 per year, every year. This is why [Chapter 2](02-hardware.md) obsesses over idle power.

## Where the watts go

A typical breakdown for a Tier 2 lab, measured at the wall:

| Component | Idle watts | Notes |
|---|---|---|
| Mini PC (N100, NVMe, 16 GB) | 6–10 | The reason mini PCs won |
| Used SFF desktop (i5 8th–12th gen, SSD) | 12–25 | Depends heavily on BIOS/C-state tuning |
| Custom NAS build (i3-12100, 6 HDD, ITX, Gold PSU) | 30–45 spun down; 60–80 spinning | Drives dominate |
| Each 3.5" HDD | 4–6 idle spinning; 0.5–1 spun down; 7–9 active | 7200 rpm and enterprise drives are the higher end |
| Each 2.5" SSD / NVMe | 0.3–2 | Some NVMe drives have poor idle (ASPM matters) |
| Used enterprise 2U server (dual Xeon, 8 drives) | 100–180 | Before any workload |
| Discrete GPU (RTX 3060/3090) | 10–25 | Higher if a display is attached or persistence mode is off; 300+ under load |
| Managed 8-port 2.5 GbE switch | 5–10 | 10GBase-T ports add 2–5 W each |
| OPNsense box (N100, 4× 2.5 GbE) | 8–15 | |
| Wi-Fi AP | 5–12 (PoE) | |
| UPS (line-interactive, self-consumption) | 5–15 | Yes, the UPS itself burns power |
| Raspberry Pi 5 | 3–5 | |

Two lessons: **drives and old servers** are where most of the power goes, and **the network gear and UPS** are a non-trivial floor that exists regardless of compute choices.

## Reducing idle power

### CPU package states (C-states)

Modern CPUs save most of their power by sleeping between tasks. `powertop` shows the percentage in each package C-state; a well-tuned Intel desktop system idles in **C8–C10** at 3–8 W package power; a poorly tuned one sits in C2–C3 at 20+ W. What prevents deep sleep:

- **BIOS settings**: enable "C-states," "Package C-state limit: Auto/C10," "ASPM: Auto/L1," "Native ASPM," disable "Above 4G Decoding" only if it causes issues (it usually should stay on for GPUs). Set "PCIe link state power management" to L1.
- **PCIe devices without ASPM**: a NIC, an HBA, an NVMe drive, or a GPU that does not support Active State Power Management pins the whole package at a shallow C-state. `lspci -vv | grep -i aspm` shows per-device status. The **LSI SAS HBAs** (9211/9300) are notorious for this — they cost 8–12 W themselves and block C-states; use motherboard SATA ports or an **ASMedia ASM1166**-based 6-port SATA card (which supports ASPM) instead where possible. Some NVMe drives (older Samsung, some Kioxia) block deep states; Solidigm and WD SN770/SN850X are generally fine. **10GBase-T NICs** are hungry and often block states; SFP+ with DAC is better.
- **Kernel parameters**: `pcie_aspm=force` (forces ASPM on devices that claim not to support it — try it, check `dmesg` for errors), the **`powertop --auto-tune`** tunables (which enable runtime PM on USB, SATA link power management, audio codec power saving — apply via a systemd service at boot), `ahci.mobile_lpm_policy=3` for SATA link power (can cause issues with some HBAs/backplanes; test), and the Intel `intel_idle` driver (default; do not disable).
- **Peripherals**: unplug USB devices that keep the bus awake; disable the audio codec; disable unused onboard controllers (a second NIC, Wi-Fi, Bluetooth) in BIOS.
- **The GPU**: NVIDIA cards need `nvidia-persistenced` and no attached display to idle properly; some models still refuse to go below 15–25 W. Consider whether the GPU should be in the always-on server at all.

A tuned Intel 12th–14th gen system (i3/i5, one NVMe, ITX board, Gold PSU) idles at **10–15 W at the wall with drives spun down** — the community's benchmark for a DIY NAS. The **"unRAID/Proxmox low power" threads** on the German Hardwareluxx forum and r/homelab document specific board/CPU/PSU combinations with measured results; the **Wolfgang's Channel** YouTube series is the best video treatment.

### Drives

- **Spin down idle HDDs**: `hdparm -S 241 /dev/sdX` (30 minutes) or the NAS OS's setting. MergerFS/SnapRAID and Unraid make this natural (only the drive holding the file spins); **ZFS pools spin all drives for any access**, so spin-down works only when nothing touches the pool for the timeout — which, with monitoring and indexing services, is rarer than you think. Check `hdparm -C` over a day to see if they actually stay down. Frequent spin-up/down cycles wear drives; set the timeout at 20–60 minutes, not 5.
- **Fewer, larger drives** ([Chapter 6](06-storage.md)): four 20 TB drives draw a third of what twelve 6 TB drives draw.
- **SSDs for the hot data**: the OS, containers, databases, and frequently accessed files on flash mean the spinning array is touched only for media — and can sleep.
- **Enterprise vs consumer**: enterprise HDDs idle 1–2 W higher and are louder; the trade is warranty and workload rating.

### Power supplies

A PSU's efficiency curve peaks at 40–60% load and falls off sharply below 10–20%. An 850 W Platinum unit powering a 25 W idle system may be running at 70% efficiency; a 450 W Gold unit at the same load is closer to 85%. **Size the PSU to the peak, not to the marketing** — a NAS with six drives and an i5 peaks under 200 W (drive spin-up is the spike); a 400–550 W unit is right. **PicoPSU** (12 V DC input, 90–160 W) with a laptop-style brick is the most efficient option for a mini-ITX box with few drives. **Corsair RM/SF Gold, Seasonic Focus, be quiet! Pure Power** have good low-load efficiency; check **Cybenetics** low-load ratings (the ETA/LAMBDA certification includes 2% and 10% load efficiency, which 80 PLUS does not).

### Right-sizing and consolidation

The lowest-power lab is the one with the fewest machines. Three mini PCs at 10 W each beat one 2U server at 150 W; but one 25 W SFF running Proxmox with everything beats three mini PCs. Consolidate where the isolation is not needed; separate only for the reasons in [Chapter 1](01-planning.md) (DNS on its own box; storage separate from compute at Tier 2+). The **GPU box** is the classic candidate for **suspend-on-idle + Wake-on-LAN**: a Home Assistant automation (or **UpSnap**, or a script) wakes it when someone opens the game-streaming or LLM front-end and suspends it after 30 idle minutes — a 25 W idle GPU machine that runs 3 hours a day costs a tenth of one that runs 24.

### Scheduled power

Things that need not run at night can be shut down: a desktop that only does game streaming, a backup target that only needs to be on during the backup window (Wake-on-LAN from the backup script, shut down after), a secondary Proxmox node used only for testing. Smart plugs with HA scheduling handle the dumb devices (a printer, a Raspberry Pi doing something occasional).

## Heat

Every watt becomes heat. 30 W is a warm shelf; 150 W in a cupboard raises the temperature by 5–10 °C with poor airflow; 400 W is a space heater. Consequences: drives above 40–45 °C sustained age faster (Backblaze's data shows modest effects up to ~45 °C and larger above); CPUs throttle; fans spin up (noise); PSUs and capacitors degrade.

- **Airflow over insulation**: a cupboard with the door ajar, or with a vent and a quiet exhaust fan (a USB-powered 120–140 mm Noctua on a smart plug/temperature automation), beats a sealed one. Racks want front-to-back airflow, not enclosed side panels.
- **Location**: basements and utility rooms are cooler; attics and south-facing rooms are not. Do not put the NAS beside the radiator or in a sunbeam.
- **Monitor it**: `sensors` for CPU/board, `smartctl -A` for drive temps (Scrutiny graphs them), a Zigbee temperature sensor in the cupboard feeding Home Assistant, with an alert at 30 °C ambient / 45 °C drive.
- **Fan curves**: set BIOS/IPMI fan curves for quiet at idle and aggressive under load; on used enterprise servers, `ipmitool raw` commands set manual fan speeds (each vendor has a community script — Dell iDRAC, Supermicro).
- **Summer**: expect 5–10 °C higher; if drives cross 50 °C in July, the location is wrong.

## Noise

Measured in dB(A) at 1 m; every 10 dB is roughly a doubling of perceived loudness. A silent room is ~30 dB; a quiet mini PC 0–20 dB (inaudible to fan-off); a 4-bay NAS with HDDs 25–35 dB (a low hum plus seek clicks — bedroom-hostile, office-tolerable); a tower server with 120 mm fans 30–40 dB; a 2U server 45–60 dB (a hair dryer); a 1U server 55–70 dB (unlivable). Enterprise switches with 40 mm fans are in the 2U class; many can be modded with Noctua fans if the firmware tolerates the lower RPM (some alarm; some do not).

Rules: **HDDs are the noise floor** of any NAS — enterprise drives seek loudly (Exos/Ultrastar), consumer NAS drives (WD Red Plus, IronWolf non-Pro) are quieter; rubber grommets and a case with drive dampening (Fractal Define) help. **Fewer, larger, slower fans** (120–140 mm at 600–900 rpm) over many small fast ones. **Never buy 1U** for a living space. **Put the noisy thing somewhere else** — a garage, basement, or utility room with a wired run back; noise, unlike heat, has no software fix.

## UPS and Network UPS Tools

### Why

Power flickers, brownouts, and short outages are common everywhere; long outages are regional. A UPS covers the flickers entirely (nothing even notices) and turns a long outage into a controlled event: the UPS tells the servers, the servers shut down cleanly, ZFS pools export intact, databases close their transactions, and everything comes back when power returns. Without one, a blackout during a write is a coin toss on corruption — modern filesystems survive it most of the time, which is exactly the problem: *most*.

### Sizing

Measure the lab's peak draw with the meter (or sum the idle figures and add 50%). Add the router, modem/ONT, and switch — they need to stay up for the servers to communicate with each other and for you to receive the alert. Buy a UPS whose **watt** rating (not VA) exceeds that by 30%. Then look at the **runtime chart** for your load: you want 10–15 minutes at least, long enough for the shutdown sequence plus a margin, and more if your outages are typically short (a 30-minute runtime rides through most flickers and brief cuts without shutting anything down).

Typical: a Tier 1 lab (30–50 W) on a 600–900 VA unit (300–500 W) gets 45–90 minutes. A Tier 2 lab (100–150 W) on a 1500 VA (900–1000 W) unit gets 20–40 minutes. Bigger is not better beyond that — a UPS burns 5–15 W itself, more for larger units, and oversizing wastes both money and electricity.

### Type and features

- **Line-interactive** with **pure sine wave** output (CyberPower CP-series PFC models, APC Back-UPS Pro / Smart-UPS, Eaton 5S/5P/Ellipse PRO): the right class for home labs; corrects brownouts without switching to battery; sine wave is preferable for active-PFC power supplies (all modern ones).
- **Standby/offline** (cheaper APC Back-UPS ES, CyberPower standby): fine for a mini PC and a router; simulated sine wave is usually acceptable for small loads.
- **Online/double-conversion** (Eaton 9-series, APC Smart-UPS Online): always on inverter, zero transfer time, cleanest power, 10–20% efficiency loss. Overkill for home.
- **Communication**: **USB** (universal; NUT supports nearly every model via `usbhid-ups`), **serial** (old), **network management card** (SNMP — great, expensive, usually only on Smart-UPS/Eaton 5P class). USB is fine: one server is the NUT master; the others are clients over the network.
- **Batteries**: sealed lead-acid (SLA/VRLA) lasts 3–5 years and is user-replaceable (USD 30–80; **buy the replacement cartridge, not a new UPS**); **lithium-ion** models (CyberPower's Li-ion line, Eaton 5P Li-ion, APC's newer lithium units) last 8–10 years, weigh half, and cost 50–100% more — increasingly worth it. Enable the UPS's periodic self-test and act when it fails.
- **Outlets**: enough for everything that must stay up; surge-only outlets for things that must not (a printer draws a huge spike and should never be on battery).
- **Brands**: APC (Schneider) and Eaton are the safe choices; **CyberPower** is the value pick with excellent Linux/NUT support; avoid no-name units.

### NUT (Network UPS Tools)

The standard Linux daemon set for talking to UPSes and coordinating shutdown across machines:

- **`nut-server` / `upsd`** runs on the machine the UPS is plugged into (USB), with a **driver** (`usbhid-ups` for most; `nutdrv_qx` for many cheap ones; `snmp-ups` for network cards) defined in `/etc/nut/ups.conf`. It publishes battery charge, load, runtime, status (`OL` online, `OB` on battery, `LB` low battery).
- **`upsmon`** runs on *every* machine (including the server): it polls `upsd` (locally or over the network), and when the UPS reports **on battery + low battery** it triggers a shutdown. The master (the machine with the USB cable) shuts down last and tells the UPS to power off its outlets so everything comes back when mains returns (`upsdrvctl shutdown`).
- **Configuration**: `/etc/nut/upsd.users` (a user for `upsmon`), `/etc/nut/upsmon.conf` (`MONITOR ups@localhost 1 monuser pass master` on the server; `... secondary` on clients), `/etc/nut/nut.conf` (`MODE=netserver` or `netclient`). `upsc ups@localhost` shows status. **Proxmox** (Debian) runs NUT natively; **TrueNAS**, **Unraid**, **OPNsense**, **Synology**, and **QNAP** all have NUT built in with UIs (and can act as master or slave); **Home Assistant** has a NUT integration to display and alert; **Peanut** is a small web UI for NUT; **Grafana** via the `nut_exporter`.
- **Shutdown policy**: the default (shut down at "low battery," typically 10–20% charge) is fine for short-runtime setups; for long runtimes, shut down VMs and non-essential hosts *earlier* (`upssched` timers — "if on battery for 5 minutes, shut down the media server and the GPU box; at low battery, shut down everything") to preserve runtime for the router and the NAS.
- **Test it**: pull the UPS's mains plug with everything running (during the maintenance window, after a backup). Watch `upsc`, watch the shutdown sequence, confirm everything comes back when you plug it in. An untested UPS shutdown is a hypothesis — like an untested backup.

```
# /etc/nut/ups.conf (server with the USB cable)
[ups]
  driver = usbhid-ups
  port = auto
  desc = "CyberPower CP1500PFCLCD"

# /etc/nut/upsmon.conf (server)
MONITOR ups@localhost 1 upsmon <password> master
SHUTDOWNCMD "/sbin/shutdown -h +0"
NOTIFYCMD /usr/sbin/upssched          # or a script that posts to ntfy
NOTIFYFLAG ONBATT SYSLOG+WALL+EXEC
NOTIFYFLAG ONLINE SYSLOG+WALL+EXEC
NOTIFYFLAG LOWBATT SYSLOG+WALL+EXEC

# /etc/nut/upsmon.conf (each client)
MONITOR ups@10.0.20.10 1 upsmon <password> secondary
```

**Alternatives**: `apcupsd` (APC-specific, older, still fine), CyberPower's `pwrstat` (proprietary), Eaton's IPP; NUT covers all of them and is the recommendation.

### Beyond the UPS

- **Surge protection**: a UPS provides some; a whole-house surge protector at the panel provides more; lightning is not survivable by either — unplug during severe storms if you live somewhere it matters.
- **Generators and solar/battery**: a Tier 3 lab in an outage-prone area may add an inverter generator or a home battery (Powerwall, Ecoflow/Bluetti units with UPS-mode passthrough — the portable power stations with <20 ms switchover work as a large, slow UPS for small loads). Beyond this guide's scope, but the NUT logic is the same: the lab must know when it is on battery.
- **Graceful start-up**: BIOS "power on after AC loss," Proxmox VM start order and delays, `docker restart: unless-stopped`, and `fstab` `nofail`/automount options for network mounts so a host boots even if the NAS is not up yet. Test a cold start of the whole lab once: does everything come back without you?

## Cost models

Assume USD 0.20/kWh (adjust for your tariff; Europeans multiply by ~1.5–2), 5-year horizon, hardware bought used/value where sensible.

### Tier 1: mini PC + 2 USB drives, ~25 W average

| | |
|---|---|
| Electricity | 25 W × 8.76 × 0.20 = **USD 44/year** |
| Hardware (mini PC, 2 drives, enclosure, UPS) | USD 700, amortised **USD 140/year** |
| Off-site backup (300 GB on B2) | **USD 22/year** |
| Domain | **USD 12/year** |
| **Total** | **~USD 218/year (USD 18/month)** |

For comparison: Google One 2 TB + a streaming service + a password manager family plan ≈ USD 300–400/year. Tier 1 breaks even and you own the hardware.

### Tier 2: Proxmox node + NAS + firewall + switch + UPS, ~90 W average

| | |
|---|---|
| Electricity | 90 W × 8.76 × 0.20 = **USD 158/year** |
| Hardware | USD 2,500, amortised **USD 500/year** |
| Off-site backup (2 TB) | **USD 144/year** |
| Domain + VPS for Pangolin/Headscale | **USD 60/year** |
| Drive replacements (1/year average) | **USD 150/year** |
| **Total** | **~USD 1,010/year (USD 84/month)** |

This is a hobby with hobby costs — comparable to a gym membership — that also replaces a household's cloud subscriptions and delivers capabilities (local AI, full-quality media, NVR, home automation) that the cloud does not sell.

### Tier 3: cluster + storage server + GPU + 10 GbE, ~300 W average

| | |
|---|---|
| Electricity | 300 W × 8.76 × 0.20 = **USD 526/year** (EUR 900+ in Europe) |
| Hardware | USD 6,000, amortised **USD 1,200/year** |
| Everything else | **USD 400/year** |
| **Total** | **~USD 2,100/year (USD 175/month)** |

At this tier, electricity is a line item you feel every month, and the power-tuning above is worth real money: getting 300 W down to 200 W saves USD 175/year — enough to pay for the off-site backups.

### The comparison nobody makes

A modern games console in standby draws 1–10 W; a smart TV 0.5–3 W in standby and 60–150 W on; a desktop PC left on 50–100 W; a fridge 100–200 kWh/year (~15–25 W average). A tuned Tier 1 lab at 25 W is *less* than many households' idle consumer electronics. A Tier 3 lab at 300 W is a second refrigerator running continuously — real, but not exotic.

## Checklist

- [ ] Idle, typical, and peak watts measured at the wall with a meter; annual cost calculated for your tariff.
- [ ] `powertop` shows deep package C-states (C6+ at minimum, C8–C10 ideal) on always-on x86 hosts; BIOS C-states and ASPM enabled; `powertop --auto-tune` applied at boot; offending PCIe devices identified.
- [ ] HDDs spin down when idle (verified with `hdparm -C` over a day) or the decision not to spin down is deliberate.
- [ ] PSUs sized to actual peak; efficient at low load.
- [ ] GPU/gaming/backup-target machines suspend or power off when idle, with WoL or scheduled wake.
- [ ] Ambient and drive temperatures monitored with alerts; airflow adequate; nothing above 45 °C sustained.
- [ ] Noise appropriate to location; noisy hardware relocated rather than tolerated.
- [ ] UPS sized to load with 10+ minutes runtime; pure sine wave for active-PFC PSUs; router/modem/switch on it.
- [ ] NUT (or equivalent) master + clients configured; shutdown tested by pulling the plug; `upssched` early-shutdown policy for non-essential hosts; ntfy notification on battery events.
- [ ] Cold-start tested: everything returns after a full power loss without intervention (BIOS AC-loss setting, VM start order, `nofail` mounts).
- [ ] UPS battery age recorded; self-test scheduled; replacement budgeted at year 3–4.
