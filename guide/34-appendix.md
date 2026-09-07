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
