# Security for the Home Lab

Security is not a product you install; it is a set of habits and a handful of decisions made in the right order. The good news is that a home lab's threat model is far simpler than an enterprise's, and the highest-value defences are cheap: expose little, segment the network, keep things updated, use strong authentication, and have backups an attacker cannot reach. This chapter builds a realistic threat model, then works through the layers — host hardening, SSH, firewalls and Docker, the reverse proxy edge, intrusion prevention with CrowdSec and fail2ban, container hardening, secrets, updates, and detection — and ends with a prioritised checklist.

## Threat model: who is actually attacking you

Be honest about the adversaries, because defending against the wrong one wastes effort.

**Automated scanners and bots.** The overwhelming majority of hostile traffic. Within minutes of opening a port, scanners find it; within hours, bots try default credentials and known exploits against whatever they fingerprint. They are indiscriminate and relentless, and they are entirely defeated by: not exposing services, strong unique passwords, MFA, and prompt patching. This is the adversary you *must* beat, and it is beatable.

**Opportunistic ransomware.** Malware that arrives via a phishing email on a family laptop or a compromised download, then spreads across the LAN looking for SMB shares to encrypt and backups to delete. Defeated by: network segmentation, SMB shares that require authentication and are not writable by every device, versioned/immutable/offline backups ([Chapter 11](11-backups.md)), and least privilege.

**Compromised IoT devices.** The cheap camera or plug with a known backdoor, enrolled in a botnet, scanning your LAN from the inside. Defeated by: an IoT VLAN with no access to anything internal ([Chapter 3](03-networking.md)).

**Supply-chain incidents.** A popular Docker image or npm package is compromised upstream. Rare, real (the 2024 xz backdoor; periodic malicious images on Docker Hub). Mitigated by: pulling from official/project sources, pinning versions, not running as root, not granting the Docker socket, egress filtering, and noticing anomalies.

**Targeted attackers.** Someone who wants *your* data specifically. For nearly all home labs this adversary does not exist, and the defences that stop bots and ransomware raise the bar high enough that a targeted attacker would need real effort. If you are a journalist, activist, or hold genuinely sensitive data, the general advice here is a floor, not a ceiling.

**You.** Accidental `rm -rf`, a misconfigured firewall rule that exposes a database, an `.env` file committed to a public repo, a port published on `0.0.0.0` on a VPS. Statistically the most likely cause of a security incident in a home lab. Defeated by: backups, review, and the habits below.

## The order of operations

If you do nothing else, do these, in this order:

1. **Expose nothing.** Use a mesh VPN for your own access ([Chapter 8](08-remote-access-vpn.md)). Zero forwarded ports is the strongest posture there is.
2. **Segment.** IoT and guests on their own VLANs, unable to reach servers ([Chapter 3](03-networking.md)).
3. **Update.** Unattended security updates on hosts; a notification-and-review cadence for containers ([Chapter 5](05-containers.md)).
4. **Authenticate strongly.** Unique passwords from a manager; MFA/passkeys on everything that supports it; an IdP in front of everything that does not ([Chapter 10](10-identity-sso.md)).
5. **Back up immutably.** A copy an attacker on your network cannot delete ([Chapter 11](11-backups.md)).
6. **Then** harden hosts, containers, and the edge, and add detection — the rest of this chapter.

A lab with steps 1–5 done and nothing else is more secure than most small businesses.

## Host hardening

### SSH

SSH is how you administer everything; it deserves care even on the LAN.

- **Keys, not passwords.** `ssh-keygen -t ed25519`; copy the public key; then in `/etc/ssh/sshd_config` (or a drop-in in `/etc/ssh/sshd_config.d/`): `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no` (or `prohibit-password` if you must SSH as root, as on Proxmox), `PubkeyAuthentication yes`. Reload sshd. Test from a second terminal *before* closing the first.
- **Protect the private key** with a passphrase; use `ssh-agent` or a hardware key (YubiKey with `ed25519-sk`/FIDO2 keys are supported natively by OpenSSH 8.2+ and are the gold standard).
- **Never expose SSH to the internet.** Reach it via the VPN. If you absolutely must, use key-only auth, a non-standard port (which only reduces log noise, not risk), and fail2ban/CrowdSec. **Tailscale SSH** or an SSH certificate authority (step-ca, Smallstep) removes key sprawl for larger labs.
- `AllowUsers youruser` or `AllowGroups ssh-users` to whitelist accounts. `MaxAuthTries 3`. `ClientAliveInterval 300`.
- **SSH login notifications**: a tiny PAM hook or `sshrc` script posting to ntfy on every successful login is one of the highest-value detections available and takes five minutes.

### Users and sudo

One personal account per human, in the `sudo` group; root login disabled; `sudo` with a password (or with `NOPASSWD` only for specific automation commands). Docker group membership is root-equivalent — anyone in `docker` can mount the host filesystem into a container. Know that, and either accept it for your own account or use rootless Docker/Podman.

### Unattended updates

```bash
apt install unattended-upgrades apt-listchanges
dpkg-reconfigure -plow unattended-upgrades   # enable
# /etc/apt/apt.conf.d/50unattended-upgrades: security origin enabled by default on Debian/Ubuntu
# Consider: Unattended-Upgrade::Automatic-Reboot "true"; with Automatic-Reboot-Time "04:00";
# and Unattended-Upgrade::Mail or a script to ntfy for the report
```

Security updates for the host OS, automatically, nightly. This is non-negotiable for anything reachable from beyond the LAN and strongly advised for everything else. Reboots for kernel updates can be automated (with `needrestart` or the reboot option) or done on a weekly schedule; **livepatch**/**kpatch** avoid them on Ubuntu Pro (free for personal use on up to five machines) and RHEL-family.

### Minimal attack surface

Install only what you use; `ss -tulpn` to see what is listening and ask why for each entry. Disable or remove Avahi, CUPS, rpcbind, and anything else that came with a "server" tasksel and that you do not need. A Docker host should listen on 22 (LAN/VPN only), 80/443 (the proxy), and nothing else on the LAN interface.

### Filesystem and kernel

Full-disk encryption (LUKS) on the OS drive protects against physical theft — worth it on a laptop, debatable on a server in your house that must reboot unattended (requires a TPM2 auto-unlock setup — `systemd-cryptenroll` — or network unlock via **Tang/Clevis** or **dropbear-initramfs** for SSH-unlock at boot). ZFS native encryption on data datasets with a key loaded at boot from a file on the encrypted root is a common compromise. **AppArmor** (Debian/Ubuntu) is on by default and Docker uses it; leave it. **SELinux** (Fedora/RHEL) likewise; do not set it to permissive to fix a problem — fix the label. Kernel hardening via `sysctl` (disable IP forwarding where not needed, `kernel.kptr_restrict=2`, `net.ipv4.conf.all.rp_filter=1`) is low-effort; **Lynis** audits a host and tells you what to tighten.

## Firewalls

### Network firewall

The router/firewall ([Chapter 3](03-networking.md)) is the primary control: default-deny inbound from the internet, default-deny between VLANs with explicit allows, egress rules for IoT. Review the rule set twice a year and delete rules whose purpose you cannot remember.

### Host firewall

A host firewall on each server is defence in depth: if a VLAN rule is wrong or a device on the server VLAN is compromised, the host still refuses connections to ports that should not be reachable. `ufw` (Ubuntu/Debian), `firewalld` (Fedora/RHEL), or `nftables` directly.

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from 10.0.10.0/24 to any port 22 proto tcp     # SSH from trusted VLAN only
ufw allow from 100.64.0.0/10 to any port 22 proto tcp    # ...and from the tailnet
ufw allow 80,443/tcp                                     # the reverse proxy
ufw enable
```

**And then the Docker problem** ([Chapter 5](05-containers.md)): Docker's published ports bypass `ufw`. On a LAN-only host behind a router with no forwards this is a nuisance; on a VPS it is a critical exposure. The fixes: publish container ports on `127.0.0.1` only (or not at all — use the proxy network), *or* install `ufw-docker` which adds the right rules to the `DOCKER-USER` chain, *or* add `DOCKER-USER` rules by hand:

```bash
# Drop anything to Docker containers that did not come from the LAN or the tailnet
iptables -I DOCKER-USER -i eth0 ! -s 10.0.0.0/8 -m conntrack --ctstate NEW -j DROP
iptables -I DOCKER-USER -i eth0 -s 100.64.0.0/10 -j RETURN
```

Verify from another machine with `nmap -p- <host>`: only the ports you intend should answer. Do this after every new stack.

## The edge: exposed services

If you forward 443 to a reverse proxy, that proxy and everything behind it are on the internet. The layered defences, from outermost in:

1. **Geo-blocking** at the firewall or proxy for countries you will never log in from. Crude, effective against the bulk of scanner traffic. OPNsense (GeoIP aliases), Traefik/Caddy/Nginx plugins, CrowdSec's geo scenarios, Cloudflare's WAF rules if fronted by Cloudflare.
2. **CrowdSec or fail2ban** (below) watching the proxy's access logs and banning IPs that probe, brute-force, or hit known exploit paths.
3. **Rate limiting** at the proxy on login endpoints.
4. **Authentication before the app** — forward-auth to the IdP with MFA for anything that is not deliberately public ([Chapter 10](10-identity-sso.md)). The app's own login page is the *second* line, not the first.
5. **A separate proxy entrypoint or instance for public hosts** so that forwarding 443 exposes only the hostnames you intend, not all forty internal ones.
6. **Security headers, TLS 1.2+, HSTS**, a catch-all default host returning 404 ([Chapter 7](07-reverse-proxy-tls.md)).
7. **A Web Application Firewall** — **ModSecurity with the OWASP Core Rule Set** (via BunkerWeb, or the SWAG mod, or Nginx directly) or **Coraza** (Caddy plugin, Traefik plugin) — blocks known attack patterns (SQL injection, path traversal) generically. Adds false positives and CPU; worthwhile for a public site, optional for a proxy that only fronts authenticated services.
8. **The app itself** kept updated, with its own MFA on, admin accounts renamed from defaults, and registration disabled.

**Or**: do not forward 443 at all. Cloudflare Tunnel with Access, or Pangolin with its built-in auth ([Chapter 8](08-remote-access-vpn.md)), moves the edge to a relay and gives you an identity wall before traffic even reaches your network. For most households that need to expose one or two things to non-technical friends, this is the better model.

## CrowdSec and fail2ban

### fail2ban

The classic: watches log files, matches regexes ("Failed password for"), and after N matches in T seconds adds a firewall rule banning the source IP for a duration. Jails exist for sshd, Nginx, Postfix, Dovecot, Vaultwarden, Nextcloud, and hundreds more; writing a filter for a new log format is a regex. Simple, effective against brute force, no external dependencies. Limitations: purely reactive and local (it learns nothing from other people's attackers), and Docker's log locations and iptables chains need configuration (`chain = DOCKER-USER`, log paths bind-mounted in).

### CrowdSec

A modern successor: a local **agent** parses logs (via "collections" — pre-built parsers and scenarios for sshd, Nginx, Traefik, Caddy, HAProxy, Vaultwarden, Nextcloud, Jellyfin, Home Assistant, OPNsense, and many more) and detects behaviours (brute force, scanning, HTTP probing for `/wp-admin` and `.env`, credential stuffing, CVE exploitation attempts); **bouncers** enforce decisions at the firewall (iptables/nftables, OPNsense plugin), the proxy (Traefik plugin, Caddy module, Nginx module, Cloudflare WAF), or the application. Crucially, the agent optionally **shares** signals with the CrowdSec community and receives a **community blocklist** of IPs currently attacking other CrowdSec users — so you preemptively block the botnet that has not yet reached you. A local API, a web console (hosted, optional), `cscli` for management, Prometheus metrics. Free for the community edition; the company sells premium blocklists and enterprise features.

**Recommendation:** CrowdSec for anything exposed to the internet — the community blocklist is a real advantage. The Traefik/Caddy bouncer plugins are the cleanest integration: the proxy asks CrowdSec's local API "is this IP banned?" on each request and returns 403 before the request reaches any app. fail2ban remains fine for SSH on a host that is not exposed, or when you want zero external dependencies.

```yaml
# crowdsec/compose.yaml (agent reading Traefik logs; bouncer is a Traefik plugin)
services:
  crowdsec:
    image: crowdsecurity/crowdsec:latest
    container_name: crowdsec
    restart: unless-stopped
    environment:
      COLLECTIONS: "crowdsecurity/traefik crowdsecurity/http-cve crowdsecurity/base-http-scenarios crowdsecurity/sshd"
      GID: "1000"
    volumes:
      - ./config:/etc/crowdsec
      - ./data:/var/lib/crowdsec/data
      - /opt/stacks/traefik/logs:/var/log/traefik:ro
      - /var/log/auth.log:/var/log/auth.log:ro
    networks: [proxy]
# then: docker exec crowdsec cscli bouncers add traefik-bouncer   -> key for the Traefik plugin
# and:  docker exec crowdsec cscli decisions list                 -> who is banned right now
```

Honeypot-style additions: **endlessh** (a tarpit that holds SSH scanners in a slow banner for hours on port 22 while your real SSH is elsewhere) and **CrowdSec's own "honeypot" scenarios**. Fun, low value, harmless.

## Container hardening

Containers are not a security boundary by default; they can be made a reasonable one.

- **Don't run as root inside the container.** `user: "1000:1000"` where the image allows it; `PUID/PGID` for LinuxServer images; images that drop privileges themselves. A root process in a container that escapes is root on the host.
- **`security_opt: [no-new-privileges:true]`** on every service. Prevents setuid escalation inside the container. Almost never breaks anything.
- **Drop capabilities.** `cap_drop: [ALL]` then `cap_add` only what is needed (most web apps need none; `NET_BIND_SERVICE` if binding <1024 as non-root; `NET_ADMIN` for VPN containers). Start with `cap_drop: [ALL]` and add back until it works.
- **Read-only root filesystem** where the app tolerates it: `read_only: true` plus `tmpfs: [/tmp, /run]`. Many Go/Rust single-binary apps work this way; most PHP/Python apps do not without effort.
- **Never mount the Docker socket into an internet-facing container.** The socket is root on the host. For tools that need it (Traefik, Portainer, Watchtower/Diun, Dozzle, Uptime Kuma's Docker monitor, Homepage's Docker widget), use a **socket proxy** (`tecnativa/docker-socket-proxy` or `wollomatic/socket-proxy`) that exposes only the read-only API endpoints each tool needs. Or run those tools with `--group-add` and a read-only socket mount, accepting the reduced protection.
- **`privileged: true` is a last resort.** Home Assistant, Frigate with certain hardware, and a few others ask for it. Prefer specific `devices:` and `cap_add:` entries; if you must, isolate that container (own network, no socket, minimal mounts).
- **Resource limits** (`mem_limit`, `cpus`, `pids_limit`) so a compromised or buggy container cannot starve the host.
- **Isolated networks.** A database should be on a network that only its application can reach; nothing else. The `proxy` network carries only web-facing containers.
- **Egress control.** Containers can reach the internet by default. For things that should not need to (databases, internal tools), `internal: true` on their network, or firewall rules in `DOCKER-USER`. Cuts off data exfiltration and C2 callbacks from a compromised image.
- **Image hygiene.** Official/project images; pinned tags; `docker scout` / **Trivy** / **Grype** to scan images for known CVEs (Trivy in a cron job with ntfy output is a fine weekly habit); Renovate for controlled updates ([Chapter 27](27-automation-iac.md)).
- **Rootless Docker or Podman** for the strongest default posture, at the cost of some friction ([Chapter 5](05-containers.md)).
- **gVisor (`runsc`)** as an alternative runtime adds a user-space kernel between container and host — real isolation for an untrusted workload (a public-facing app, a code-execution sandbox) with a performance cost. Niche at home; good to know exists.
