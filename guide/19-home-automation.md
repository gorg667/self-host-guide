# Home Automation

Home automation is where a home lab stops being about files and starts controlling the physical world: lights that respond to presence, heating that follows the weather forecast, cameras that recognise a person but ignore the cat, a doorbell that announces itself on every speaker, and none of it dependent on a cloud that can be shut down or breached. **Home Assistant** is the centre of gravity — the most active open-source project on GitHub in some years — and this chapter covers it in depth: how to run it, the radio protocols (Zigbee, Z-Wave, Thread/Matter, Wi-Fi, Bluetooth) and the software that bridges them (Zigbee2MQTT, ZHA, Z-Wave JS), MQTT and Mosquitto, ESPHome for DIY devices, cameras and NVR with Frigate and Scrypted, voice assistants, Music Assistant, and the design principles that keep a smart home from becoming a dumb one.

## Home Assistant

Home Assistant (HA) is an open-source (Apache 2.0) home automation platform, Python-based, developed by Nabu Casa (a company founded by the project's creators, funded by an optional subscription) and thousands of contributors. It integrates with **~3,000 devices and services** — every major smart-home brand, most cloud services, media players, weather, calendars, presence, and your own DIY hardware — and provides automations (visual editor or YAML), scripts, scenes, dashboards (Lovelace, highly customisable), energy monitoring, voice control (local or cloud), a mobile app with presence detection and notifications, and a huge add-on and custom-integration ecosystem (HACS).

### Installation methods

This matters more than for any other service in the guide, because HA's install method determines which features you get.

| Method | What it is | Add-ons (Supervisor) | Backups/updates in UI | Best for |
|---|---|---|---|---|
| **Home Assistant OS (HAOS)** | A dedicated appliance OS (buildroot-based) running HA in Docker with the **Supervisor** | **Yes** | **Yes** | **Most people.** Run as a VM on Proxmox, or on a Pi/Green/Yellow/ODROID |
| **Home Assistant Container** | HA alone in a Docker container on your existing host | No | Backups yes; updates via image | People who run Mosquitto, Zigbee2MQTT, etc. as their own Compose services anyway |
| **Home Assistant Supervised** | Supervisor on a Debian host you manage | Yes | Yes | Rarely; strict requirements; not recommended |
| **Home Assistant Core** | Python venv | No | No | Developers |

**HAOS as a Proxmox VM** is the community's default (the Proxmox community helper script creates one in a minute): you get the full add-on store (Mosquitto, Zigbee2MQTT, Z-Wave JS UI, ESPHome, Node-RED, Frigate, Music Assistant, Piper/Whisper, Studio Code Server, Samba, Terminal, Tailscale — all one-click), the built-in backup system, OS/Supervisor/Core updates from the UI, and USB passthrough for radios. Give it 2 vCPU, 4 GB RAM, 32 GB disk. Pass through the Zigbee/Z-Wave USB sticks (or, better, use network coordinators — below).

**Container** is right if you already run Docker Compose and prefer to manage MQTT/Zigbee2MQTT/Frigate as your own stacks with your own reverse proxy and backups — HA becomes one more service. You lose the add-on store (irrelevant, since you run those things yourself) and gain uniformity with the rest of your lab. Either is fine; the guide leans HAOS-in-a-VM for households and Container for people who already run everything in Compose.

**Hardware**: HA is light — a Pi 4 works; a Pi 5, an N100, or a VM with 2 cores and 4 GB is comfortable. Nabu Casa sells **Home Assistant Green** (~USD 100, an appliance) and **Home Assistant Yellow** (with a Zigbee/Thread radio built in) for people who want a box. Storage: **not a microSD card** for anything long-term — HA's database (SQLite by default) writes constantly and kills cards; use an SSD (USB or NVMe HAT on a Pi) or a VM disk.

### Key concepts

- **Integrations** connect to devices/services and create **entities** (a light, a sensor, a switch) grouped under **devices** in **areas**. **Helpers** are virtual entities (toggles, counters, timers, template sensors). **Automations** are trigger → condition → action. **Scripts** are reusable action sequences. **Scenes** are entity-state snapshots. **Blueprints** are shareable automation templates.
- **The recorder** stores history in SQLite (fine for most; **MariaDB** or **PostgreSQL** via `recorder:` for heavy setups); set `purge_keep_days` and exclude chatty entities. **InfluxDB + Grafana** or **VictoriaMetrics** for long-term history ([Chapter 12](12-monitoring.md)). The **Energy dashboard** needs sensors with proper `device_class` and `state_class`.
- **HACS** (Home Assistant Community Store) installs custom integrations, cards, and themes from GitHub — the ecosystem of things not yet (or never) in core. Essential; read what you install.
- **Nabu Casa cloud** (USD 6.50/month) funds development and provides remote access without a VPN, Alexa/Google Assistant integration without manual OAuth setup, and cloud text-to-speech. Optional; everything works without it (remote access via your VPN/proxy, Alexa/Google via a fiddlier manual route). Many self-hosters subscribe simply to fund the project.

```yaml
# Home Assistant Container (if not using HAOS)
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    privileged: true                 # for full device access; or enumerate devices: explicitly (preferred)
    network_mode: host               # required for discovery (mDNS, SSDP, Bluetooth, HomeKit)
    volumes:
      - ./config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro       # Bluetooth
    # devices: ["/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_...:/dev/ttyUSB0"]
```

Behind a reverse proxy, add to `configuration.yaml`:

```yaml
http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 172.20.0.0/14      # Docker pool
    - 10.0.20.5          # proxy host IP if not in Docker
```

## Radio protocols and coordinators

The devices — bulbs, switches, sensors, plugs, locks, blinds — speak one of a few protocols. Choosing well is the biggest determinant of a reliable smart home.

### Zigbee

A low-power mesh protocol (2.4 GHz) used by Philips Hue, IKEA Trådfri, Aqara, Sonoff, Tuya, and hundreds of others. Devices are cheap (USD 5–30), battery sensors last years, and mains-powered devices act as **routers** that extend the mesh. You need a **coordinator** — a USB stick or a network device — and software to run the network:

- **Zigbee2MQTT (Z2M)** — the community favourite: a standalone service (add-on or container) that runs the Zigbee network and publishes every device to **MQTT**, from which HA (via MQTT discovery) or anything else consumes them. Supports ~4,000 devices with a database of quirks, exposes every feature, has an excellent web UI (map, OTA firmware updates, device configuration), and decouples the Zigbee network from HA (restart HA without dropping the mesh). **The recommendation.**
- **ZHA (Zigbee Home Automation)** — HA's built-in integration; simpler (no MQTT), fewer supported devices and exposed features than Z2M, but improving and adequate for mainstream devices. Fine for a small setup; most people outgrow it.
- **deCONZ/Phoscon** — the older Dresden Elektronik stack for ConBee sticks; superseded.

**Coordinators**: **Sonoff Zigbee 3.0 USB Dongle Plus** (ZBDongle-P with CC2652P — the budget standard; the ZBDongle-E with EFR32 is also good), **SMLIGHT SLZB-06** family (**network/PoE coordinators** — Ethernet-connected, placed centrally rather than next to the server, USB-free; excellent and now the community's preferred form factor), **Home Assistant Connect ZBT-1** (formerly SkyConnect; Zigbee or Thread), **TubesZB**, **ConBee III**. Avoid: CC2531 sticks (obsolete), and plugging any USB coordinator directly into a server without a **USB extension cable** — USB 3 ports emit 2.4 GHz interference that cripples Zigbee.

**Design rules**: mains-powered routers spread through the house (smart plugs are cheap routers); keep the coordinator away from USB 3 and Wi-Fi APs; choose a Zigbee channel (15, 20, or 25) that avoids your Wi-Fi channels (Zigbee 11–26 overlaps Wi-Fi 1–11); pair devices *in place*, not next to the coordinator; Aqara devices are fussy about which routers they join through (IKEA and Sonoff routers are known-good).

### Z-Wave

A sub-GHz (868/908 MHz) mesh protocol with certified interoperability, less interference (no 2.4 GHz contention), longer range per hop, and higher device prices (USD 30–70). Strong for locks, thermostats, and in-wall switches; weaker for cheap sensors. **Z-Wave JS** (with the **Z-Wave JS UI** add-on/container for the full web interface) is the software; controllers: **Zooz 800 series (ZST39)**, **Aeotec Z-Stick 7/10**, **Home Assistant Connect ZWA-2** (2025). Z-Wave Long Range (ZWLR) on 800-series controllers gives star-topology kilometre range for outdoor devices. **Pick Z-Wave for** locks, garage doors, and critical switches where certified reliability matters; Zigbee for everything else. Many homes run both.

### Thread and Matter

**Thread** is an IPv6 mesh protocol (also 802.15.4, same radios as Zigbee) designed for the smart home; **Matter** is the application-layer standard on top (running over Thread, Wi-Fi, or Ethernet) that Apple, Google, Amazon, Samsung, and the CSA agreed on in 2022 to end the interoperability wars. In principle: buy a Matter device, commission it with any ecosystem, done — and it works locally with no cloud. In practice, as of 2026: Matter works and HA supports it well (the **Matter Server** add-on and the Connect ZBT-1 or any Thread border router — Apple TV, HomePod, Nest Hub, or HA's own); the device selection is growing but smaller than Zigbee's; multi-admin (sharing a device between HA and Apple Home) works; firmware updates and some device features lag; Thread networks from different vendors historically did not merge (improving with credential sharing). **Buy Matter-over-Thread devices** where available for future-proofing; keep Zigbee for the long tail and the cheap sensors.

### Wi-Fi

Cheap smart plugs, bulbs, and switches (Tuya, Shelly, Tasmota-flashed devices, Kasa, Meross) use Wi-Fi. Pros: no hub, high bandwidth. Cons: each device is a Wi-Fi client (50 devices strain consumer APs), draws more power (no battery sensors), and *many are cloud-dependent by default*. Strong preference for **local-control** Wi-Fi devices: **Shelly** (excellent local HTTP/MQTT APIs, no cloud required, quality hardware — the community's favourite Wi-Fi brand), **ESPHome** or **Tasmota**-compatible devices (many Tuya-based devices can be reflashed, though newer Tuya chips resist it — check for "ESP" chips), **Athom** (sells pre-flashed ESPHome/Tasmota devices). Put them all on the IoT VLAN ([Chapter 3](03-networking.md)); block internet for those that do not need it.

### Bluetooth

For BLE sensors (Xiaomi/Aqara temperature, plant sensors, Govee, SwitchBot), HA uses a Bluetooth adapter on the host or **ESPHome Bluetooth proxies** — any ESP32 running ESPHome can relay BLE to HA over Wi-Fi, so USD 5 boards scattered around the house give whole-home BLE coverage. The **Shelly Plus** devices can also act as BLE proxies. This is the right way to do Bluetooth in HA; a single USB adapter on the server is not.

## MQTT: Mosquitto

**MQTT** is the lightweight pub/sub messaging protocol that glues home automation together: Zigbee2MQTT publishes device states to topics; HA subscribes; Frigate publishes detections; Tasmota/ESPHome devices can speak it; Node-RED flows use it. **Eclipse Mosquitto** is the broker — tiny, reliable, the standard. Run it as the HAOS add-on or a container; enable authentication (`allow_anonymous false`, a password file), optionally TLS on the LAN; use **MQTT Explorer** (desktop) to inspect topics when debugging. Alternatives (**EMQX**, **NanoMQ**, **HiveMQ CE**) are for scale you do not have.

```yaml
services:
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    restart: unless-stopped
    ports: ["1883:1883"]           # LAN/IoT VLAN; add 8883 for TLS
    volumes:
      - ./config:/mosquitto/config   # mosquitto.conf + passwd (mosquitto_passwd -c passwd user)
      - ./data:/mosquitto/data
      - ./log:/mosquitto/log
  zigbee2mqtt:
    image: koenkk/zigbee2mqtt:latest
    container_name: zigbee2mqtt
    restart: unless-stopped
    depends_on: [mosquitto]
    volumes: ["./z2m:/app/data", "/run/udev:/run/udev:ro"]
    ports: ["127.0.0.1:8080:8080"]
    environment: { TZ: Europe/London }
    # USB coordinator:
    # devices: ["/dev/serial/by-id/usb-ITead_Sonoff_Zigbee_3.0_USB_Dongle_Plus_XXXX-if00-port0:/dev/ttyACM0"]
    # Network coordinator (SLZB-06): set serial.port: tcp://10.0.30.50:6638 in configuration.yaml instead
```

## ESPHome: DIY devices

**ESPHome** turns USD 3–10 ESP8266/ESP32 boards into custom sensors and controllers using a YAML file — no programming: declare the board, the Wi-Fi, and the components (a DHT22 temperature sensor on GPIO4, a relay on GPIO5, a PIR, a display, an LED strip, a BLE proxy, a CO₂ sensor, a power meter…), and ESPHome compiles and flashes firmware that integrates natively with HA (auto-discovery, encrypted API, OTA updates from the dashboard). Run the ESPHome dashboard as an add-on or container; flash the first time over USB (via the browser with Web Serial), thereafter wirelessly.

Popular projects: multi-sensors (temperature/humidity/lux/motion in one), presence detection with **mmWave radar** (LD2410/LD2450 — detects a still person, unlike PIR; the **Everything Presence** boards by Everything Smart Home are pre-built), air quality (SCD40/SCD41 CO₂, PMS5003 particulates), energy monitoring (clamp CTs, or the **Shelly EM**/**Emporia Vue** reflashed), garage door controllers, irrigation, pool chemistry, e-paper displays, LED matrices, and the **Athom** and **Apollo Automation** pre-flashed hardware lines for people who want ESPHome without soldering. **Tasmota** is the alternative firmware (web UI on the device rather than YAML; MQTT-centric); **WLED** is the specialist for addressable LED strips (excellent, with HA integration). **OpenBeken** for the non-ESP Tuya chips.

## Cameras and NVR

### Frigate

**Frigate** is the open-source NVR built around **local AI object detection**: it ingests RTSP streams from IP cameras, runs detection (person, car, dog, cat, package, …) on every motion event, records continuously or on events, and publishes rich events to HA via MQTT — so "notify me when a person is in the driveway after 10 pm, but not the neighbour's cat" is a simple automation. Features: 24/7 and event recording with retention rules, zones and masks, object tracking, snapshot and clip export, a review UI with a timeline, **face recognition and licence-plate recognition** (since 0.15/0.16), semantic search over events using CLIP (describe what you're looking for), audio detection (glass breaking, barking, speech), two-way talk on supported cameras, go2rtc built in for restreaming (WebRTC/MSE low-latency live view, and one camera connection shared by everything), a HA integration with cameras/sensors/switches, and **Frigate+** (optional paid custom model training on your own images).

**Hardware for detection**: detection runs on a **detector** — CPU (slow, a few cameras at most), **Google Coral TPU** (USB or M.2/PCIe; the long-time standard at ~100 inferences/second for a few watts; supply and driver friction increased 2023–2025), **OpenVINO on an Intel iGPU** (6th gen+; now the community's pragmatic default — no extra hardware, good performance, and Intel Arc works too), **NVIDIA TensorRT** (a discrete GPU — overkill but fast and also does the semantic-search embeddings), **Rockchip NPU** (RK3588 boards), **Hailo-8** (Pi AI HAT and M.2), **AMD ROCm** and **Apple** (experimental). Video *decoding* uses the iGPU/GPU via hardware acceleration flags. A Frigate box with 6–8 cameras at 1080p detect streams is comfortable on an N100 with OpenVINO or any Intel 8th-gen+ machine.

**Cameras**: anything with **RTSP** and ideally a low-resolution **substream** (Frigate detects on the substream — 640×360 or 1280×720 — and records the main stream). Community favourites: **Reolink** (many models; use RTSP or the newer http-flv/`rtmp` paths that go2rtc handles; avoid Wi-Fi-only battery models for continuous NVR), **Amcrest/Dahua** (excellent RTSP, ONVIF, well-documented), **Hikvision** (good hardware; geopolitical and firmware concerns for some), **Annke**, **Empire Tech** (Dahua rebrands), **Ubiquiti UniFi Protect** cameras (work via RTSPS if you run a UniFi console; excellent but ecosystem-locked), **Wyze** (with the `wz_mini_hacks` or docker-wyze-bridge — hobbyist), **Eufy** (avoid for local NVR), doorbells: **Reolink Video Doorbell PoE**, **Amcrest AD410**, **Ubiquiti G4 Doorbell**. **PoE cameras on a cameras VLAN with no internet access** is the standard, secure setup — cameras are notoriously insecure, and a camera that cannot reach the internet cannot leak.

```yaml
services:
  frigate:
    image: ghcr.io/blakeblackshear/frigate:stable
    container_name: frigate
    restart: unless-stopped
    shm_size: 512mb                          # scale with camera count/resolution (see docs formula)
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128    # Intel iGPU: hwaccel decode + OpenVINO detector
      # - /dev/bus/usb:/dev/bus/usb                 # Coral USB
      # - /dev/apex_0:/dev/apex_0                   # Coral PCIe/M.2
    volumes:
      - ./config:/config
      - /mnt/tank/frigate:/media/frigate         # recordings (replaceable; plan retention/disk)
      - type: tmpfs
        target: /tmp/cache
        tmpfs: { size: 1000000000 }
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "127.0.0.1:8971:8971"       # authenticated UI (via proxy)
      - "8554:8554"                 # RTSP restreams from go2rtc
      - "8555:8555/tcp"             # WebRTC
      - "8555:8555/udp"
    environment:
      FRIGATE_RTSP_PASSWORD: ${CAM_PASSWORD}
```

### Scrypted

**Scrypted** is a different animal: a **camera integration hub** whose killer feature is bridging any camera into **Apple HomeKit Secure Video** (with hardware-accelerated transcoding and near-zero-latency streams), Google Home, and Alexa, plus NVR (paid "Scrypted NVR" plugin), object detection, and a plugin architecture. If you live in Apple Home and want your Reolink/Amcrest cameras to appear natively with HKSV recording, Scrypted is the way; many people run **Scrypted for HomeKit and Frigate for detection/recording**, fed by the same cameras via go2rtc restreams.

### Others

**go2rtc** (the streaming Swiss Army knife — bundled in Frigate, also standalone: restream, transcode, WebRTC, two-way audio, HomeKit; by the author of WebRTC Camera for HA), **Viseron**, **Shinobi**, **ZoneMinder** (the ancient NVR; still maintained), **MotionEye** (motion-based, light, dated), **Blue Iris** (Windows, paid, excellent, the traditional choice — many run it in a Windows VM with **CodeProject.AI** for detection), **UniFi Protect** (if you buy the console), **Synology Surveillance Station** (licensed per camera; competent), **Agent DVR**. For most self-hosters, **Frigate** is the answer.

## Voice assistants

HA's **Assist** pipeline provides fully local voice control: **wake word** (**openWakeWord** or **microWakeWord** on the device), **speech-to-text** (**Whisper** via the `faster-whisper` add-on, or **Speech-to-Phrase** for constrained fast local recognition on small hardware), **intent recognition** (HA's built-in sentence matching, optionally extended by an **LLM** via Ollama/OpenAI for natural conversation — "it's a bit dark in here"), and **text-to-speech** (**Piper**, fast local neural voices). Hardware: the **Home Assistant Voice Preview Edition** (Nabu Casa, ~USD 60, late 2024 — a purpose-built satellite that works well), **ESP32-S3-BOX-3** with ESPHome voice firmware, **Wyoming satellites** on a Raspberry Pi with a ReSpeaker mic array, or an old Android phone with the companion app's Assist. Quality in 2026: good for commands ("turn off the kitchen lights," "set a timer"), improving for conversation with an LLM attached, still behind Alexa/Google for far-field recognition in noisy rooms. Entirely local, no cloud, and improving every release. **Rhasspy** (by the same author, Michael Hansen, now at Nabu Casa) was the predecessor; **Willow** was an alternative that stalled. Alexa/Google can still be *bridged* to HA (via Nabu Casa cloud or manual skill setup) if you want their microphones with your automations.

## Music Assistant

**Music Assistant** is a music library and streaming server built for HA: it pulls from local files, Jellyfin/Plex/Navidrome/Subsonic, Spotify, Tidal, Qobuz, YouTube Music, Deezer, radio, and podcasts, and plays to nearly anything — Sonos, Chromecast, AirPlay, DLNA, Snapcast, Squeezebox, Bluesound, HA media players, and **ESPHome/Voice PE speakers** — with multi-room sync groups, queue management, and full HA integration (announce, TTS over music, automations). It solves "play *this* on *that* speaker" across brands. Runs as an add-on or container.

## Node-RED and automation tooling

HA's built-in automation editor is good and has improved enormously; most people never need more. **Node-RED** (visual flow-based programming, runs as an add-on/container, integrates via the HA WebSocket nodes) remains popular for complex flows with many branches, external API calls, and debugging by watching messages flow. **AppDaemon** and **Pyscript** are for people who prefer Python. **NetDaemon** for C#. **Blueprints** (community-shared automation templates via the HA forum's Blueprint Exchange) cover the common cases — motion-activated lights with luminance and timeout, low-battery notifications, etc.

## HomeKit, Google, Alexa bridging

HA's **HomeKit Bridge** integration exposes any HA entities to Apple Home (so Siri controls your Zigbee lights); **Homebridge** is the standalone alternative for people without HA. Google Home and Alexa integration via **Nabu Casa** (one click) or manually (create a developer project — an hour of fiddling that breaks occasionally). **Matter Bridge** (via the Matter Hub add-on, 2024–) exposes HA entities as Matter devices to any Matter controller — the modern route.

## Design principles for a smart home that stays smart

1. **Local control or nothing.** Every device should work with the internet down. Prefer Zigbee/Z-Wave/Thread/local Wi-Fi (Shelly, ESPHome); avoid cloud-only devices; when you must have one, isolate it and plan for its cloud to die.
2. **Manual override always.** Every light must work from a wall switch when HA is down. Use smart *switches/relays* (Shelly behind the existing switch, Zigbee in-wall modules) rather than smart *bulbs* where a household shares the space; smart bulbs plus decoupled switches (Hue dimmer, IKEA remote) where colour matters.
3. **The IoT VLAN** ([Chapter 3](03-networking.md)): everything on it; internet blocked by default; HA allowed to reach it; mDNS reflected for Chromecast/HomeKit discovery.
4. **Automations should be boring.** Lights on with motion at night, off after timeout. Heating schedule. Notifications for the things that matter (leak sensor, door left open, freezer temperature). Resist the urge to automate everything; a smart home that surprises its occupants gets turned off.
5. **Name and area everything** on day one. `light.kitchen_ceiling`, not `light.0x00158d0004a2b3c4`.
6. **Back up HA** (its built-in backups to a network share or Nabu Casa cloud; plus the VM via PBS) and **back up the Zigbee/Z-Wave network keys** (Z2M's `coordinator_backup.json`, Z-Wave JS's NVM backup) — losing them means re-pairing every device.
7. **Update deliberately.** HA releases monthly (`2026.x`), each with a "Breaking Changes" section. Read it. Update the HAOS/Supervisor freely; update Core after skimming the notes; snapshot the VM first.
8. **Presence detection** is the foundation of good automation: the companion app (GPS + Wi-Fi), router-based device tracking (UniFi, OPNsense ARP), BLE room presence (**ESPresense**, **Bermuda**), and mmWave sensors per room. Layer them.

## Recommendations

- **HAOS in a Proxmox VM** (or on a Pi 5/HA Green for a standalone appliance); Container if your lab is all-Compose.
- **Zigbee via Zigbee2MQTT** with an **SLZB-06 network coordinator**; Z-Wave for locks; Matter-over-Thread for new purchases where available; Shelly for Wi-Fi.
- **Mosquitto** as the broker.
- **ESPHome** for anything custom; **ESPresense/Bluetooth proxies** for BLE.
- **Frigate** with OpenVINO on an Intel iGPU (or a Coral) and PoE cameras on an isolated VLAN; **Scrypted** alongside if you want HKSV.
- **Assist + Voice PE** for local voice; **Music Assistant** for whole-home audio.
- Read the HA release notes monthly; back up the radio network keys.

## Checklist

- [ ] HA installed (HAOS VM or Container) on SSD storage, not microSD; behind the reverse proxy with `trusted_proxies` set; mobile app connected via VPN or proxy.
- [ ] Zigbee coordinator on a USB extension or network-attached; channel chosen to avoid Wi-Fi; routers distributed; Z2M (or ZHA) running; network key backed up.
- [ ] Mosquitto with authentication; Z2M and Frigate publishing to it.
- [ ] All IoT devices on the IoT VLAN; cameras on a no-internet VLAN; HA permitted to reach both; mDNS reflection configured.
- [ ] Every light has a physical override; automations reviewed for "what if HA is down."
- [ ] HA backups scheduled to a network share/PBS; Z2M/Z-Wave JS key backups included.
- [ ] Frigate detection on hardware (OpenVINO/Coral); retention sized to disk; events feeding HA notifications.
- [ ] Monthly HA update ritual: snapshot → read breaking changes → update → verify.
