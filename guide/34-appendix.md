# Appendix

Reference material to keep open in another tab: a glossary of the jargon used throughout the guide, a port table for the services it covers, the checklists that were scattered across chapters gathered in one place, a Docker Compose cheat-sheet, and a handful of command references (ZFS, Docker, systemd, networking) that you'll reach for repeatedly.

## Glossary

| Term | Meaning |
|---|---|
| **3-2-1(-1-0)** | Backup rule: 3 copies, 2 media, 1 off-site (+1 offline/immutable, 0 verification errors). See [Backups](11-backups.md) |
| **ACME** | Protocol for automated certificate issuance (Let's Encrypt, ZeroSSL). Challenges: HTTP-01, DNS-01, TLS-ALPN-01 |
| **AGPL** | GNU Affero GPL; copyleft that also triggers when software is offered over a network. See [Legal](30-legal-ethical.md) |
| **ARC / L2ARC / SLOG** | ZFS read cache in RAM / on SSD / separate intent log for sync writes. Most home labs need only ARC |
| **ARM64 / amd64** | CPU architectures (Raspberry Pi, Apple Silicon / Intel & AMD). Images must match or be multi-arch |
| **Bind mount** | Host directory mapped into a container (`/srv/appdata/x:/config`) vs a Docker-managed **named volume** |
| **Bus factor** | How many people can be hit by a bus before a project (or your home lab) dies |
| **CARP / VRRP** | Router failover protocols (OPNsense/pfSense, Keepalived) |
| **CGNAT** | Carrier-grade NAT: your ISP shares one public IPv4 among many customers; inbound port forwarding impossible |
| **CMR / SMR** | Conventional vs Shingled Magnetic Recording. SMR drives have terrible sustained-write/rewrite performance; avoid for RAID/ZFS |
| **Copyleft / permissive** | Licence families: GPL/AGPL require sharing derivative source; MIT/Apache/BSD do not |
| **CrowdSec** | Collaborative IPS: parses logs, shares reputation, "bouncers" block at proxy/firewall |
| **DDNS** | Dynamic DNS: updates a hostname when your public IP changes |
| **DERP** | Tailscale's relay servers used when direct NAT traversal fails |
| **DNS-01** | ACME challenge proving domain control via a TXT record; enables wildcards and needs no open ports |
| **DoH / DoT / DoQ** | DNS over HTTPS / TLS / QUIC — encrypted DNS transport |
| **Docker socket** | `/var/run/docker.sock`; mounting it grants root-equivalent on the host. Use a socket proxy |
| **ECC** | Error-correcting RAM; detects/corrects bit flips. Nice for ZFS, not mandatory |
| **Forward auth** | Reverse proxy asks an auth service (Authelia, TinyAuth, Authentik outpost) whether to allow each request |
| **GitOps** | Desired state lives in Git; a tool (Komodo, Flux, Argo) reconciles the running system to match |
| **HBA** | Host Bus Adapter — a SAS/SATA controller in "IT mode" (no RAID) presenting raw disks to ZFS |
| **Headless** | No monitor/keyboard; managed over SSH/web |
| **IaC** | Infrastructure as Code: Ansible, OpenTofu/Terraform, cloud-init, Compose |
| **IdP / OIDC / OAuth2 / SAML / LDAP** | Identity Provider; the protocols apps use to delegate login (OIDC is the modern default; LDAP is the legacy directory protocol) |
| **iGPU / Quick Sync / VA-API / NVENC** | Integrated GPU; Intel's hardware codec engine; Linux video-acceleration API; NVIDIA's encoder |
| **IOMMU / VFIO** | CPU feature and kernel framework for passing PCI devices to VMs |
| **IPMI / iDRAC / iLO** | Out-of-band management (remote console/power) on server boards |
| **LXC** | Linux Containers — OS-level virtualisation; Proxmox "CT" |
| **mDNS / Avahi / Bonjour** | Multicast local name resolution (`*.local`); doesn't cross VLANs without a reflector |
| **MergerFS** | Union filesystem pooling disks into one mount; pair with **SnapRAID** for parity |
| **Mesh VPN / overlay** | Tailscale, NetBird, ZeroTier, Nebula: peer-to-peer WireGuard-based networks with a coordination server |
| **NAT / hairpin NAT / NAT reflection** | Address translation; hairpin lets LAN clients reach the public IP of their own router |
| **NUT** | Network UPS Tools — monitors a UPS and shuts hosts down cleanly |
| **OOM** | Out of memory; the kernel kills the largest process (`OOMKilled` in Docker) |
| **Passkey / WebAuthn / FIDO2** | Phishing-resistant public-key login (Pocket ID is passkey-only) |
| **PBS** | Proxmox Backup Server — deduplicating, incremental backups of VMs/CTs/hosts |
| **PoE** | Power over Ethernet (802.3af/at/bt) for APs and cameras |
| **PUID / PGID** | LinuxServer.io convention: run the app as this user/group so bind-mount ownership works |
| **QDevice / quorum** | Tie-breaker for two-node Proxmox clusters; majority needed to operate |
| **RAIDZ1/2/3, mirror, stripe** | ZFS redundancy levels (1/2/3 disks' parity; identical copies; none) |
| **Resilver / scrub** | ZFS rebuilding redundancy after disk replacement / verifying every block's checksum |
| **Reverse proxy** | Terminates TLS and routes `host.example.com` to the right backend (Traefik, Caddy, nginx, NPM) |
| **RTO / RPO** | How long until service is back / how much data you can lose (time since last backup) |
| **SBC** | Single-board computer (Raspberry Pi, Orange Pi, Rock 5) |
| **SFF / USFF / 1L / TinyMiniMicro** | Small-form-factor PCs; Lenovo Tiny, HP Mini, Dell Micro |
| **Snapshot** | Point-in-time filesystem/volume copy (ZFS, Btrfs, LVM, Proxmox) — cheap rollback, **not** a backup |
| **Split-horizon DNS** | Same name resolves to a private IP internally and a public IP (or nothing) externally |
| **SR-IOV** | PCI feature letting one device (NIC, Intel iGPU 12th-gen+) appear as several virtual functions for VMs |
| **SSO** | Single sign-on — one login for many apps via an IdP |
| **Subnet router / exit node** | Tailscale node that advertises a LAN / routes all internet traffic |
| **Tailnet** | Your private Tailscale network |
| **TBW / DWPD** | SSD endurance: total terabytes written / drive writes per day |
| **Trunk / access port / PVID** | Switch port carrying multiple tagged VLANs / one untagged VLAN / the untagged VLAN ID |
| **UPS** | Uninterruptible power supply; line-interactive is the home-lab sweet spot |
| **VLAN (802.1Q)** | Virtual LAN tags to segment one physical network |
| **Wildcard certificate** | `*.home.example.com` — one cert for all first-level subdomains; requires DNS-01 |
| **WireGuard** | Modern minimal VPN protocol; basis of Tailscale, NetBird, Pangolin's Newt |
| **ZFS dataset / zvol** | Filesystem within a pool / block device within a pool (used for VM disks, iSCSI) |

## Default port reference

Container-internal ports; publish or proxy as needed. Where two are listed, the second is HTTPS or an alternate.

### Infrastructure

| Service | Port(s) | Proto | Notes |
|---|---|---|---|
| SSH | 22 | TCP | Change only if you like; use keys and fail2ban/CrowdSec |
| DNS (AdGuard Home, Pi-hole, Unbound, Blocky, Technitium) | 53 | TCP+UDP | AdGuard UI 3000 (setup) → 80; Pi-hole UI 80/443; Unbound as upstream often 5335; Technitium 5380 |
| DHCP | 67/68 | UDP | |
| HTTP / HTTPS | 80 / 443 | TCP (+UDP 443 for HTTP/3) | Owned by the reverse proxy |
| DoT / DoH / DoQ | 853 / 443 / 853 | TCP / TCP / UDP | |
| Traefik dashboard | 8080 | TCP | Route via `api@internal` instead of exposing |
| Nginx Proxy Manager | 81 (UI), 80, 443 | TCP | |
| Caddy admin API | 2019 | TCP | Keep on localhost |
| Portainer | 9443 / 9000 (legacy) / 8000 (agent tunnel) | TCP | |
| Dockge | 5001 | TCP | |
| Komodo Core / Periphery | 9120 / 8120 | TCP | |
| Proxmox VE | 8006 (UI), 5900–5999 (VNC), 3128 (SPICE), 5405–5412 (corosync UDP), 60000–60050 (migration) | TCP/UDP | |
| Proxmox Backup Server | 8007 | TCP | |
| TrueNAS SCALE | 80 / 443 | TCP | |
| Unraid | 80 / 443 | TCP | |
| Cockpit | 9090 | TCP | |
| Webmin | 10000 | TCP | |
| NUT (upsd) | 3493 | TCP | |
| SNMP | 161 | UDP | |
| Syslog | 514 | UDP/TCP | |
| NTP | 123 | UDP | |

### Storage & file sharing

| Service | Port(s) | Notes |
|---|---|---|
| SMB/CIFS | 445 (139 legacy) | |
| NFS | 2049 (+111 rpcbind for v3) | v4 needs only 2049 |
| iSCSI | 3260 | |
| SFTP/SCP | 22 | |
| FTP/FTPS | 21 (+ passive range) | Don't |
| rsync daemon | 873 | |
| WebDAV | 80/443 (path) | |
| Syncthing | 8384 (UI), 22000 (TCP+UDP sync), 21027 (UDP discovery) | |
| MinIO | 9000 (S3), 9001 (console) | |
| Garage | 3900 (S3), 3902 (web), 3903 (admin) | |
| SeaweedFS | 9333 (master), 8080 (volume), 8888 (filer) | |
| FileBrowser | 80 (image) / 8080 | |
| Nextcloud | 80 (Apache image) / 9000 (FPM) | AIO: 8080 (setup), 11000 (Apache) |
| Seafile | 80 | |
| Copyparty | 3923 | |

### Remote access & networking

| Service | Port(s) | Notes |
|---|---|---|
| WireGuard | 51820 UDP (convention) | Any UDP port works |
| OpenVPN | 1194 UDP/TCP | |
| Tailscale | 41641 UDP (outbound; forward for direct connections) | Control plane over 443 |
| Headscale | 8080 (API), 9090 (metrics), 50443 (gRPC) | Put behind proxy on 443 |
| NetBird | 80/443 (mgmt), 33073 (mgmt gRPC), 10000 (signal), 3478 (STUN), 49152–65535 (TURN) | |
| ZeroTier | 9993 UDP | |
| Pangolin | 80/443 (Traefik), 51820 UDP (Gerbil/WireGuard), 3001–3003 internal | On the VPS |
| Cloudflare Tunnel (cloudflared) | outbound 7844 | No inbound |
| Guacamole | 8080 | |
| RustDesk (hbbs/hbbr) | 21115–21117 TCP, 21116 UDP, 21118–21119 (web) | |
| MeshCentral | 443 (or 4430) | |
| Wazuh | 1514/1515 (agents), 55000 (API), 443 (dashboard) | |
| Speedtest Tracker | 80 | |
| LibreSpeed | 80 | |
| UniFi Controller | 8443 (UI), 8080 (inform), 3478 UDP (STUN), 10001 UDP (discovery) | |
| Omada Controller | 8043 (UI), 8088, 29810–29814 | |

### Identity, security, monitoring

| Service | Port(s) | Notes |
|---|---|---|
| Authelia | 9091 | |
| Authentik | 9000 / 9443 | Outposts: 9000 |
| Pocket ID | 1411 | |
| TinyAuth | 3000 | |
| Kanidm | 8443 (HTTPS), 636 (LDAPS) | |
| LLDAP | 17170 (UI), 3890 (LDAP), 6360 (LDAPS) | |
| Keycloak | 8080 / 8443 | |
| Zitadel | 8080 | |
| Vaultwarden | 80 (3012 legacy WS) | |
| Bitwarden (official) | 80/443 | |
| Psono | 80 | |
| HashiCorp Vault / OpenBao | 8200 | |
| Infisical | 8080 | |
| CrowdSec LAPI | 8080 | Metrics 6060 |
| Uptime Kuma | 3001 | |
| Gatus | 8080 | |
| Beszel hub / agent | 8090 / 45876 | |
| Prometheus | 9090 | |
| Alertmanager | 9093 | |
| Grafana | 3000 | |
| Loki | 3100 | |
| Alloy / Promtail | 12345 / 9080 | |
| node_exporter | 9100 | |
| cAdvisor | 8080 | |
| Netdata | 19999 | |
| Zabbix | 10051 (server), 10050 (agent), 8080 (web) | |
| InfluxDB | 8086 | |
| VictoriaMetrics | 8428 | |
| Dozzle | 8080 | |
| Glances | 61208 | |
| ntfy | 80 | |
| Gotify | 80 | |
| Apprise API | 8000 | |
| Scrutiny | 8080 | Collector talks to 8080 |
| Diun | — | No UI |
| Watchtower | 8080 (metrics, optional) | |
| Healthchecks.io | 8000 | |
| Changedetection.io | 5000 | |

### Media & downloads

| Service | Port(s) | Notes |
|---|---|---|
| Jellyfin | 8096 (HTTP), 8920 (HTTPS), 1900 UDP (DLNA), 7359 UDP (discovery) | |
| Plex | 32400, 32410–32414 UDP (GDM), 1900 UDP, 32469 (DLNA) | |
| Emby | 8096 / 8920 | |
| Jellyseerr / Overseerr | 5055 | |
| Radarr / Sonarr / Lidarr / Readarr / Whisparr | 7878 / 8989 / 8686 / 8787 / 6969 | |
| Prowlarr | 9696 | |
| Bazarr | 6767 | |
| Tdarr | 8265 (UI), 8266 (server) | |
| qBittorrent | 8080 (UI), 6881 TCP+UDP (peers) | |
| Transmission | 9091 (UI), 51413 | |
| Deluge | 8112 (UI), 58846 (daemon), 6881 | |
| SABnzbd | 8080 | |
| NZBGet | 6789 | |
| Gluetun | 8888 (HTTP proxy), 8388 (Shadowsocks), 8000 (control) | Route download clients through it |
| Audiobookshelf | 80 (image) / 13378 | |
| Navidrome | 4533 | |
| Kavita | 5000 | |
| Komga | 25600 | |
| Calibre-Web | 8083 | |
| Tautulli | 8181 | |
| Stash | 9999 | |
| Tube Archivist | 8000 | |
| MeTube | 8081 | |
| Pinchflat | 8945 | |
| Lidarr | 8686 | |
| ErsatzTV | 8409 | |
| Threadfin / xTeVe | 34400 | |

### Photos, documents, productivity, communication

| Service | Port(s) | Notes |
|---|---|---|
| Immich | 2283 | ML 3003 internal |
| PhotoPrism | 2342 | |
| Ente (Museum API) | 8080 | |
| Paperless-ngx | 8000 | |
| Docspell | 7880 | |
| Stirling-PDF | 8080 | |
| Homepage | 3000 | |
| Homarr | 7575 | |
| Dashy | 8080 | |
| Heimdall | 80/443 | |
| Glance | 8080 | |
| Miniflux | 8080 | |
| FreshRSS | 80 | |
| Wallabag | 80 | |
| Linkding | 9090 | |
| Karakeep (Hoarder) | 3000 | |
| Joplin Server | 22300 | |
| Trilium | 8080 | |
| Outline | 3000 | |
| Docmost | 3000 | |
| BookStack | 80 | |
| Wiki.js | 3000 | |
| SilverBullet | 3000 | |
| Memos | 5230 | |
| Vikunja | 3456 | |
| Planka | 1337 | |
| Actual Budget | 5006 | |
| Firefly III | 8080 | |
| Grocy | 80 (LSIO: 9283) | |
| Mealie | 9000 | |
| Tandoor | 8080 | |
| Radicale | 5232 | |
| Baïkal | 80 | |
| Matrix Synapse | 8008 (client), 8448 (federation) | |
| Conduwuit / Conduit | 6167 | |
| Element Web | 80 | |
| Mattermost | 8065 | |
| Rocket.Chat | 3000 | |
| Jitsi | 443, 10000 UDP (JVB) | |
| Mumble | 64738 TCP+UDP | |
| TeamSpeak | 9987 UDP, 10011, 30033 | |
| Mailcow | 25, 465, 587, 143, 993, 110, 995, 4190, 80/443 | |
| Stalwart | 25, 465, 587, 143, 993, 4190, 8080 | |
| Postfix / Dovecot | 25/587/465 / 143/993 | |
| Roundcube | 80 | |
| ntfy | 80 | (listed above) |
| Home Assistant | 8123 | |
| Mosquitto (MQTT) | 1883, 8883 (TLS), 9001 (WS) | |
| Zigbee2MQTT | 8080 | |
| Z-Wave JS UI | 8091 (UI), 3000 (WS) | |
| Node-RED | 1880 | |
| ESPHome | 6052 | |
| Frigate | 5000 (UI), 8971 (auth UI), 8554 (RTSP), 8555 (WebRTC) | |
| Scrypted | 10443 | |
| go2rtc | 1984 (API), 8554 (RTSP), 8555 (WebRTC) | |

### Dev, AI, gaming, databases

| Service | Port(s) | Notes |
|---|---|---|
| Forgejo / Gitea | 3000 (HTTP), 22 or 2222 (SSH) | |
| GitLab | 80/443, 22 | |
| Woodpecker CI | 8000 (UI), 9000 (gRPC) | |
| Drone | 80 | |
| Jenkins | 8080, 50000 (agents) | |
| code-server / OpenVSCode | 8080 / 3000 | |
| Coder | 7080 | |
| Harbor | 80/443 | |
| Docker Registry | 5000 | |
| Verdaccio | 4873 | |
| n8n | 5678 | |
| Activepieces | 80 | |
| Windmill | 8000 | |
| Huginn | 3000 | |
| Ollama | 11434 | |
| Open WebUI | 8080 | |
| LocalAI | 8080 | |
| llama.cpp server | 8080 | |
| vLLM | 8000 | |
| text-generation-webui | 7860, 5000 (API) | |
| ComfyUI | 8188 | |
| AUTOMATIC1111 | 7860 | |
| SearXNG | 8080 | |
| Whisper ASR / Speaches | 9000 / 8000 | |
| Piper / Wyoming | 10200 | Whisper-Wyoming 10300 |
| Minecraft Java / Bedrock | 25565 TCP / 19132 UDP | |
| Valheim | 2456–2458 UDP | |
| Palworld | 8211 UDP | |
| Satisfactory | 7777 UDP+TCP | |
| Terraria | 7777 | |
| Factorio | 34197 UDP | |
| Pterodactyl / Pelican | 80/443 (panel), 8080 (Wings), 2022 (SFTP) | |
| Crafty | 8443 | |
| Steam cache (LanCache) | 80, 443, 53 | |
| RomM | 8080 | |
| Sunshine | 47984–47990 TCP, 47998–48000 UDP, 48010 | |
| PostgreSQL | 5432 | |
| MariaDB / MySQL | 3306 | |
| Redis / Valkey | 6379 | |
| MongoDB | 27017 | |
| InfluxDB | 8086 | |
| ClickHouse | 8123 (HTTP), 9000 (native) | |
| Elasticsearch / OpenSearch | 9200, 9300 | |
| Meilisearch | 7700 | |
| Typesense | 8108 | |
| RabbitMQ | 5672, 15672 (UI) | |
| NATS | 4222, 8222 (monitoring) | |
| pgAdmin | 80 | |
| Adminer | 8080 | |
| CloudBeaver | 8978 | |

---

## Consolidated checklists

### New host bootstrap

- [ ] Static IP or DHCP reservation; hostname set; `/etc/hosts` correct
- [ ] Non-root user with sudo; SSH keys; `PasswordAuthentication no`; `PermitRootLogin no`
- [ ] `unattended-upgrades` (security only) enabled; reboot policy decided
- [ ] Time sync verified (`timedatectl`)
- [ ] Firewall default-deny inbound; allow SSH from LAN/VPN only, 80/443, 53 if DNS
- [ ] Docker installed from the official repo; user in `docker` group (or rootless); `daemon.json` with log rotation and `default-address-pools`
- [ ] Directory layout created (`/srv/stacks`, `/srv/appdata`, data mounts) with correct ownership
- [ ] Network mounts in `fstab` with `nofail,_netdev,x-systemd.automount`
- [ ] Tailscale/WireGuard installed on the host (not in a container)
- [ ] Monitoring agent (Beszel/node_exporter) + `smartd` + ntfy notifications
- [ ] Host added to the backup plan **before** the first service goes live
- [ ] Documented in your notes/Git: what, why, IP, purpose

### New service deployment

- [ ] Evaluated (activity, licence, backup docs — see [Resources](33-resources-community.md))
- [ ] Compose file in Git; secrets in `.env`/secret files, gitignored
- [ ] Image tag pinned for stateful apps; `restart: unless-stopped`
- [ ] Bind mounts under `/srv/appdata/<app>`; ownership matches `PUID/PGID`/`user:`
- [ ] No published ports unless required; joined the `proxy` network; proxy labels/route added
- [ ] `security_opt: no-new-privileges`, `read_only` where possible, `cap_drop: [ALL]` + `cap_add` as needed, `mem_limit`
- [ ] Healthcheck defined; `depends_on` with conditions for DB/cache
- [ ] Behind SSO/forward-auth if it lacks solid native auth; `lan-only` if it should never be public
- [ ] DNS name added (rewrite or record); certificate verified
- [ ] Added to Uptime Kuma/Gatus and dashboard
- [ ] Data paths added to backup script; DB dump added if applicable
- [ ] **Restore tested once**
- [ ] Release-notes feed subscribed (`releases.atom`) / Renovate tracking it

### Before an upgrade

- [ ] Read the release notes / migration guide
- [ ] Snapshot (ZFS/Proxmox) or fresh backup taken **and** verified
- [ ] Know the rollback: previous image tag, DB dump, snapshot name
- [ ] Off-peak time; household warned if it's a shared service
- [ ] After: check logs, run the app's post-upgrade tasks (`occ upgrade`, migrations), verify from a client, update the pinned tag in Git, commit

### Quarterly maintenance

- [ ] Restore test (different app each quarter); PBS/Restic `check`
- [ ] Review SMART, ZFS scrub results, disk fill trends
- [ ] Prune Docker images/volumes; check log sizes
- [ ] Rotate secrets that were exposed or are > 1 year old (API tokens, ACME DNS token)
- [ ] Review who has access (IdP users, Tailscale devices, SSH keys, Vaultwarden org)
- [ ] Test UPS: pull the plug, watch NUT shut things down
- [ ] Update the break-glass sheet; verify offline copy of recovery codes
- [ ] Firmware: router, switch, UPS, BIOS (if there's a reason)
- [ ] Re-read your own docs; fix what's outdated

### Incident / outage

1. Don't reboot yet. Capture: `docker ps -a`, `journalctl -b -p err`, `dmesg -T | tail`, `zpool status`, `df -h`.
2. What changed? (updates, power, network, cert expiry, disk full)
3. Restore service first (rollback, restart, failover), root-cause second.
4. Write three lines in the notes: symptom, cause, fix. Add a monitor that would have caught it.

---

## Docker Compose cheat-sheet

### Skeleton with the good defaults

```yaml
services:
  app:
    image: ghcr.io/org/app:1.2.3            # pin for stateful apps
    container_name: app
    restart: unless-stopped
    user: "1000:1000"                        # or PUID/PGID for LSIO images
    environment:
      TZ: Europe/Berlin
      APP_SECRET: ${APP_SECRET}              # from .env
    env_file: .env                           # or everything from here
    volumes:
      - /srv/appdata/app:/config
      - /srv/media:/media:ro
    networks: [proxy, app-internal]
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 30s
    security_opt: [no-new-privileges:true]
    cap_drop: [ALL]
    cap_add: [CHOWN, SETUID, SETGID]         # only what it needs; many images need none
    read_only: true
    tmpfs: [/tmp, /run]
    mem_limit: 1g
    logging:
      driver: json-file
      options: { max-size: "10m", max-file: "3" }
    labels:
      traefik.enable: "true"
      traefik.http.routers.app.rule: Host(`app.home.example.com`)
      traefik.http.services.app.loadbalancer.server.port: 8080

  db:
    image: postgres:16-alpine
    container_name: app-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - /srv/appdata/app/postgres:/var/lib/postgresql/data
    networks: [app-internal]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 10s
      retries: 5

networks:
  proxy:
    external: true
  app-internal:
    internal: true                           # no internet from the DB
```

### Snippets

```yaml
# Hardware
devices: [/dev/dri:/dev/dri]                       # Intel/AMD GPU
group_add: ["render", "video"]
deploy: { resources: { reservations: { devices: [{ driver: nvidia, count: all, capabilities: [gpu] }] } } }
devices: [/dev/ttyUSB0:/dev/ttyUSB0]              # Zigbee stick; prefer /dev/serial/by-id/...

# Networking
network_mode: host                                 # mDNS/discovery apps (HA, Plex, Jellyfin DLNA)
network_mode: service:gluetun                      # route through a VPN container
ports: ["127.0.0.1:8080:80"]                       # localhost only
ports: ["53:53/udp", "53:53/tcp"]
extra_hosts: ["host.docker.internal:host-gateway"]
dns: [192.168.1.10]

# Storage
volumes:
  - type: bind
    source: /srv/media
    target: /media
    read_only: true
  - type: tmpfs
    target: /transcode
    tmpfs: { size: 4g }
shm_size: 256m                                     # Postgres, Chromium-based apps

# Secrets (Compose file-based secrets)
secrets:
  db_password:
    file: ./secrets/db_password
services:
  db:
    secrets: [db_password]
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password

# Reuse
x-common: &common
  restart: unless-stopped
  logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
services:
  a:
    <<: *common
    image: ...

# Profiles (optional services)
services:
  debug-tool:
    profiles: [debug]        # docker compose --profile debug up
```

### Commands

```bash
docker compose up -d                       # start/update (recreates changed services)
docker compose pull && docker compose up -d # update images
docker compose down                        # stop and remove containers (keeps volumes)
docker compose down -v                     # ALSO deletes named volumes — data loss
docker compose logs -f --tail 100 app
docker compose ps; docker compose top
docker compose config                      # resolved file with env substituted
docker compose exec app sh                 # shell in running container
docker compose run --rm app <cmd>          # one-off
docker compose restart app
docker compose up -d --force-recreate app  # recreate without changes
docker compose --profile debug up -d
docker compose -f a.yaml -f override.yaml up -d
docker system df; docker system prune      # space; remove stopped/unused (asks)
docker image prune -a                      # remove ALL unused images
docker network create proxy
docker inspect app | jq '.[0].Mounts, .[0].NetworkSettings.Networks'
docker stats --no-stream
docker events --since 1h
```

---

## Command references

### ZFS

```bash
zpool create -o ashift=12 -O compression=zstd -O atime=off -O xattr=sa -O acltype=posixacl \
    tank mirror /dev/disk/by-id/ata-A /dev/disk/by-id/ata-B
zpool create ... tank raidz1 A B C D
zpool status -v; zpool list -v; zpool iostat -v 5
zpool scrub tank; zpool replace tank OLD NEW; zpool clear tank
zpool import; zpool import -f tank; zpool export tank
zfs create tank/media; zfs create -o recordsize=1M tank/media   # large files
zfs set compression=zstd tank; zfs get all tank/media | grep -v default
zfs list -o name,used,avail,refer,mountpoint
zfs snapshot tank/appdata@pre-upgrade; zfs list -t snapshot -r tank/appdata
zfs rollback tank/appdata@pre-upgrade; zfs destroy tank/appdata@pre-upgrade
zfs send -R tank/photos@snap | zfs recv -F backup/photos           # local
zfs send -w tank/photos@snap | ssh nas zfs recv backup/photos      # raw/encrypted
zfs send -i @old tank/photos@new | ssh nas zfs recv backup/photos  # incremental
zfs diff tank/appdata@a tank/appdata@b
arc_summary | head -40
# Sanoid/Syncoid: /etc/sanoid/sanoid.conf templates; syncoid tank/photos nas:backup/photos
```

### Systemd

```bash
systemctl status docker; systemctl restart docker
systemctl enable --now foo.timer; systemctl list-timers
journalctl -u docker -f; journalctl -b -p err; journalctl --since "1 hour ago"
journalctl --disk-usage; journalctl --vacuum-size=500M
systemctl daemon-reload
systemd-analyze blame                     # slow boot
# minimal service + timer
# /etc/systemd/system/backup.service   [Service] Type=oneshot ExecStart=/srv/stacks/backup/backup.sh EnvironmentFile=/srv/stacks/backup/.env
# /etc/systemd/system/backup.timer     [Timer] OnCalendar=*-*-* 03:00:00 Persistent=true  [Install] WantedBy=timers.target
```

### Networking

```bash
ip -br a; ip r; ip -6 r                    # addresses, routes
ss -tlnpu                                  # listening sockets
dig @1.1.1.1 example.com; dig +trace example.com; dig -x 192.168.1.10
resolvectl status; resolvectl flush-caches
curl -vkI https://x.home.example.com; curl --resolve host:443:IP https://host/
openssl s_client -connect host:443 -servername host </dev/null | openssl x509 -noout -dates -subject
nmap -sT -p- 192.168.1.10                  # what's actually open
tcpdump -ni eth0 port 53                   # watch DNS
mtr 1.1.1.1; tracepath
iperf3 -s   /   iperf3 -c server -R        # throughput between two hosts
wg show; wg-quick up wg0
tailscale status; tailscale netcheck; tailscale ping peer
nft list ruleset; iptables -L DOCKER-USER -n -v
```

### Disks & SMART

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
ls -l /dev/disk/by-id/
smartctl -a /dev/sda; smartctl -t long /dev/sda; smartctl -l selftest /dev/sda
nvme smart-log /dev/nvme0
hdparm -S 241 /dev/sdb                     # spin down after 30 min (media disks only)
fio --name=t --rw=randrw --bs=4k --size=1G --numjobs=4 --iodepth=32 --direct=1 --runtime=30 --time_based
badblocks -wsv /dev/sdX                    # destructive burn-in for new disks
```

### Restic

```bash
export RESTIC_REPOSITORY=b2:bucket:path RESTIC_PASSWORD_FILE=~/.restic
restic init
restic backup /srv/appdata --exclude-file=excludes.txt --tag daily
restic snapshots; restic ls latest; restic find 'db.sqlite3'
restic restore latest --target /tmp/restore --include /srv/appdata/vaultwarden
restic mount /mnt/restic                   # browse snapshots
restic forget --keep-daily 14 --keep-weekly 8 --keep-monthly 12 --prune
restic check; restic check --read-data-subset=5%
restic stats; restic unlock
```

## Sample `.env.example`

Commit *this*, never `.env`:

```dotenv
# Domain & proxy
DOMAIN=home.example.com
ACME_EMAIL=you@example.com
CF_DNS_API_TOKEN=            # Cloudflare token: Zone.DNS edit on example.com

# Identity
TINYAUTH_SECRET=             # openssl rand -hex 32
TINYAUTH_OIDC_CLIENT_ID=
TINYAUTH_OIDC_CLIENT_SECRET=

# Databases
IMMICH_DB_PASSWORD=          # openssl rand -base64 32
NC_DB_PASSWORD=
PL_DB_PASSWORD=

# Apps
IMMICH_VERSION=v1.135.3
VW_ADMIN_TOKEN=              # vaultwarden hash (argon2)
PL_SECRET_KEY=

# Notifications
NTFY_TOPIC_URL=https://ntfy.home.example.com/alerts
SHOUTRRR_URL=ntfy://ntfy.home.example.com/alerts

# Backups
RESTIC_PASSWORD=
B2_ACCOUNT_ID=
B2_ACCOUNT_KEY=
```

## Break-glass sheet template

Print it. Put it in the safe with the recovery codes. Update it quarterly.

```
HOME LAB — EMERGENCY SHEET                          updated: YYYY-MM-DD

Router admin ...........  https://10.0.10.1     user/pass: ________  (2FA backup codes attached)
Proxmox ................  https://10.0.10.2:8006  root@pam: ________
NAS ....................  https://10.0.10.5      admin: ________
IdP admin recovery .....  https://id.home.example.com  codes attached
Vaultwarden admin token   ________   (emergency access set up for: ________)
Domain registrar .......  ________   2FA backup codes attached
Backups
  PBS: datastore ______  password ______  encryption key: on USB key #1
  Restic repo(s): ______ password: on USB key #1 / in sealed envelope
  B2: account ______ key: sealed envelope
Where the data is
  Photos: NAS tank/photos + B2 bucket "______" + cold disk in ______
  Documents: Paperless export in tank/backups + B2
  Passwords: Vaultwarden (Bitwarden clients keep an offline copy)
If I'm gone
  1. Photos & documents: restore from B2 with rclone (instructions: ______)
  2. Passwords: emergency access in Bitwarden app → ______
  3. Everything else can be switched off.
```

---

*End of the guide. Start with [Introduction](00-introduction.md), or jump to the [Reference Architectures](31-reference-architectures.md) and build something.*
