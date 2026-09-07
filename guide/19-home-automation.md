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
