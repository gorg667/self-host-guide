# Containers: Docker, Compose, Podman, and Kubernetes

Containers are how self-hosted software is distributed and run in 2026. Nearly every project reviewed in Part III ships a container image and a `docker-compose.yml`; the community's shared vocabulary — volumes, bind mounts, networks, `PUID`/`PGID`, `restart: unless-stopped` — is Docker's vocabulary. This chapter explains what containers actually are, how to run them well, the patterns that keep a stack of forty services manageable, the update problem, the Docker-and-firewall trap, and when (rarely) Kubernetes is the right call.

## What a container is

A container is an ordinary Linux process (or process tree) that the kernel has been told to lie to. **Namespaces** give it a private view of the filesystem, network interfaces, process IDs, hostname, and users. **cgroups** limit how much CPU and memory it can use. An **image** — a stack of read-only filesystem layers built from a `Dockerfile` — provides the private filesystem: the application, its libraries, and nothing else. Start a container and you get a process that believes it is alone on a minimal machine, but is actually sharing your kernel with everything else and started in a few milliseconds.

This has three consequences that matter to self-hosters:

1. **Dependency isolation.** Service A needs Python 3.9 and service B needs 3.12; each brings its own. Nothing you install for one service can break another.
2. **Reproducibility.** The image is the same bytes on your machine as on the developer's. "Works on my machine" mostly stops being a thing.
3. **Disposability.** The container's own filesystem is ephemeral by design. Anything you want to keep — configuration, databases, uploaded files — must live in a **volume** or **bind mount** outside the container. Once you internalise this, upgrading becomes "pull new image, recreate container, data untouched," and disaster recovery becomes "restore the volumes, run `docker compose up`."

Containers are not virtual machines. They share the host kernel, so a kernel exploit from inside a container is a host compromise; a container running as root that is given the Docker socket or `--privileged` *is* root on the host. Treat them as a packaging and isolation convenience, not a security boundary — then harden accordingly ([Chapter 13](13-security.md)).

## Docker Engine

Docker is the runtime that popularised containers and remains the default. Install it from Docker's own repository, not your distribution's (which lags badly and, on Ubuntu, may hand you a snap):

```bash
# Debian/Ubuntu — official convenience script (read it first if you are cautious)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # optional: run docker without sudo (this is root-equivalent; see Security)
# Verify
docker version && docker compose version
```

`docker compose` (with a space — the v2 plugin written in Go) replaced the old Python `docker-compose` (with a hyphen) in 2022. If a tutorial says `docker-compose`, mentally substitute.

### The daemon configuration

`/etc/docker/daemon.json` is where you set host-wide options. A sensible starting point:

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "default-address-pools": [
    { "base": "172.20.0.0/14", "size": 24 }
  ],
  "live-restore": true
}
```

- **Log rotation.** Without `log-opts`, container logs grow without bound and eventually fill your disk. This is the single most common "why is my root filesystem full" cause on Docker hosts.
- **Address pools.** Docker's default `172.17.0.0/16` and subsequent `/16`s for each Compose network can collide with your LAN, a VPN, or a corporate network you connect from. Choosing an explicit pool of `/24`s avoids both the collision and the waste of a `/16` per project.
- **`live-restore`** keeps containers running while the daemon restarts (e.g., during a Docker upgrade).
- **Storage driver**: `overlay2` is the default and correct. On ZFS you can use the `zfs` driver, but `overlay2` on a ZFS dataset works fine and is simpler.
- **Data root**: `"data-root": "/mnt/fast/docker"` moves `/var/lib/docker` (images, layers, named volumes) to another disk. Do this at install time, before pulling images.

## Docker Compose

Compose describes a *stack* — one or more containers plus their networks and volumes — in a YAML file, and manages them as a unit. It is the correct tool for essentially every self-hosted deployment on a single host, and it is what every project's README gives you.

### Anatomy of a Compose file

```yaml
# /opt/stacks/vaultwarden/compose.yaml
services:
  vaultwarden:
    image: vaultwarden/server:1.33.2        # pin a version; see Updates
    container_name: vaultwarden
    restart: unless-stopped
    environment:
      DOMAIN: https://vault.example.com
      SIGNUPS_ALLOWED: "false"
      ADMIN_TOKEN: ${VW_ADMIN_TOKEN}         # from .env, never committed
    volumes:
      - ./data:/data                        # bind mount: config + SQLite DB live here
    ports:
      - "127.0.0.1:8080:80"                 # bind to localhost only; reverse proxy fronts it
    networks:
      - proxy
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost/alive"]
      interval: 30s
      timeout: 5s
      retries: 3
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          memory: 256M

networks:
  proxy:
    external: true                          # created once: docker network create proxy
```

Line by line, the decisions that matter:

- **`image` tag.** `latest` is convenient and dangerous: you have no idea what version you are running and `docker compose pull` may bring a breaking change at 3 am. Pin to at least a major version (`postgres:16`) and ideally a specific version, then update deliberately. See the Updates section.
- **`restart: unless-stopped`** brings the container back after a crash or a host reboot, but respects a manual `docker stop`. `always` ignores the manual stop. `on-failure` is for one-shot jobs.
- **`environment` and `.env`.** Compose reads `${VAR}` from a `.env` file next to the Compose file. Secrets go there, and `.env` goes in `.gitignore`. For anything more serious, Docker secrets or an external secrets manager ([Chapter 21](21-passwords-secrets.md)).
- **Bind mounts vs named volumes.** `./data:/data` is a bind mount: the data is in a directory you can see, back up with any tool, and move to another host by copying. `vaultwarden_data:/data` (declared under a top-level `volumes:`) is a named volume: Docker manages it under `/var/lib/docker/volumes`, it survives `docker compose down`, and it is slightly faster on some filesystems. **For self-hosting, bind mounts win** for almost everything because backups and migrations are simpler. The exception is database data on macOS/Windows Docker Desktop (irrelevant for a Linux server) and cases where a project's docs insist.
- **Ports.** `"8080:80"` publishes on *all* host interfaces — including the internet-facing one if the host is exposed — and, critically, **bypasses `ufw`/`firewalld`** because Docker inserts its own iptables rules ahead of them. `"127.0.0.1:8080:80"` binds to localhost only, so only a reverse proxy on the same host can reach it. Better still: put the container and the reverse proxy on the same Docker network and publish *no* ports at all — the proxy reaches the container by service name on the internal network. See the Firewall section below.
- **Networks.** A dedicated `proxy` network that the reverse proxy and every web-facing service join, plus per-stack default networks for internal traffic (a service and its database). Containers on the same network resolve each other by service name; containers on different networks cannot talk at all.
- **Healthcheck.** Lets Docker (and Uptime Kuma, and Compose's `depends_on: condition: service_healthy`) know whether the service is actually working, not merely running.
- **`no-new-privileges`** and **memory limits** are cheap hardening. More in [Chapter 13](13-security.md).

### Users and permissions: PUID/PGID

Many images — the whole **LinuxServer.io** (`lscr.io/linuxserver/*`) catalogue and many others — accept `PUID` and `PGID` environment variables and drop privileges to that user after starting. Set them to a dedicated host user (e.g., `id dockeruser` → `1000:1000`) that owns the bind-mounted directories, and files the container writes will be owned by that user on the host. Images that do not support this either run as root (and write root-owned files into your bind mounts — annoying) or accept a Compose-level `user: "1000:1000"` directive (which works only if the image does not need root at startup). Permission errors on bind mounts are the most common first-day Docker problem; they are almost always a mismatch between the container's UID and the directory's owner.

### Layout on disk

A convention that scales:

```
/opt/stacks/                     # or ~/docker, /srv/docker — anywhere, but one place
├── traefik/
│   ├── compose.yaml
│   ├── .env
│   └── config/
├── media/
│   ├── compose.yaml             # jellyfin + sonarr + radarr + prowlarr + qbittorrent
│   ├── .env
│   └── config/{jellyfin,sonarr,radarr,...}/
├── immich/
│   ├── compose.yaml
│   ├── .env
│   └── postgres/
└── vaultwarden/
    ├── compose.yaml
    └── data/
/mnt/data/                       # bulk storage on the big disks (NAS mount or local pool)
├── media/{movies,tv,music}/
├── photos/
└── documents/
```

One directory per stack; the stack's *configuration and small state* in bind mounts next to its Compose file; *bulk data* on the big storage, mounted into containers at consistent paths. Back up `/opt/stacks` nightly (it is small and precious); back up `/mnt/data` per the data classification in [Chapter 1](01-planning.md). Keep `/opt/stacks` in Git (with `.env` and `data/` gitignored) and you have infrastructure as code for free.

Group services into stacks by lifecycle, not by category alone: things that are always upgraded together and share a network belong in one Compose file (the *arr media stack); things that are independent get their own (Vaultwarden should not restart because you edited the media stack).

### Essential commands

```bash
docker compose up -d              # create/start (in the directory with compose.yaml)
docker compose down               # stop and remove containers + default network; volumes untouched
docker compose pull && docker compose up -d   # update to whatever the tags now point at
docker compose logs -f --tail=100 servicename
docker compose ps
docker compose exec servicename sh # shell inside
docker compose restart servicename
docker stats                      # live CPU/RAM per container
docker system df                  # disk usage
docker system prune -a --volumes  # DANGER: removes all unused images, networks, AND volumes not attached to a container
docker image prune -a             # safer: only unused images
```

`docker compose down -v` deletes named volumes. `docker system prune --volumes` deletes named volumes not currently in use. Both have destroyed people's data. Bind mounts are immune to both, which is another argument for them.

## Managing many stacks: GUIs and tools

Compose files and SSH are enough. Many people want a web UI; these are the good ones.

**Dockge** — a lightweight, Compose-centric UI by the Uptime Kuma author. Shows each stack as its YAML, lets you edit and deploy, converts `docker run` commands to Compose, streams logs. It does not abstract anything away: the files on disk are the source of truth, and you can switch between Dockge and the CLI freely. The best fit for people who want a UI *and* want to understand Compose.

**Portainer** — the long-standing full-featured container management UI: stacks, containers, images, volumes, networks, users and RBAC, multiple environments (remote Docker hosts, Swarm, Kubernetes). Business Edition is paid; Community Edition is free and sufficient. Its "stacks" store Compose content in its own database unless you point it at Git, which is a lock-in irritation. Heavier than Dockge but more capable, especially for managing several hosts.

**Komodo** — a newer Rust-based platform for managing Compose stacks across many servers with Git-backed configuration, builds, and alerting. Popular with people who outgrew Portainer and want GitOps-ish workflows without Kubernetes. See [Chapter 22](22-dev-git-automation.md).

**Yacht**, **Arcane**, **Dockhand**, **Lazydocker** (a terminal UI — excellent) — alternatives worth a look.

**Dozzle** — not a manager but a live log viewer for all containers on a host (or several). Indispensable for troubleshooting; covered in [Chapter 12](12-monitoring.md).

## Updates: the hardest operational problem

Every container is a bundle of software with its own CVEs and its own breaking changes. Keeping forty of them current without breaking anything is the ongoing cost of self-hosting.

### The approaches

**Pin nothing, `latest` everywhere, auto-update with Watchtower.** Watchtower polls registries and recreates containers when a new image appears. Maximum currency, zero effort, and periodically something breaks at 4 am because a major version changed its database schema or config format. Immich, Nextcloud, Paperless, and most database images have all bitten people this way. **Watchtower itself is no longer actively maintained** (the original project was archived in 2025; a community fork, `nickfedor/watchtower`, continues). This approach is defensible only for stateless, low-risk services.

**Pin major versions, notify, update manually.** `image: postgres:16`, `image: ghcr.io/immich-app/immich-server:v1` (where the project offers a major tag). Run **Diun** (Docker Image Update Notifier) or Watchtower in monitor-only mode to get a notification (ntfy, Gotify, email, Discord…) when a new image is available. Read the release notes. Update when convenient. This is the guide's recommendation for anything with a database.

**Pin exact versions, manage with Renovate.** `image: vaultwarden/server:1.33.2`. Keep the Compose files in a Git repository (Gitea/Forgejo/GitHub). Run **Renovate** (self-hosted or via its GitHub app) against the repo; it opens a pull request for each image bump with the changelog linked. Merge the PR; a webhook or a cron `git pull && docker compose up -d` (or Komodo, or a small script) applies it. This is GitOps for Compose, gives you a complete audit trail, and is how many advanced self-hosters run. It is more setup than the other two; [Chapter 27](27-automation-iac.md) walks through it.

**Whatever you do:**

- Take a snapshot (Proxmox/ZFS/Btrfs) or a backup before updating anything with a database.
- Read the release notes for major version bumps. Projects with a history of breaking changes: Immich (pre-1.0 semantics until 2025's v2), Nextcloud (one major at a time, never skip), Paperless-ngx, Authelia/Authentik, Traefik (v2→v3), Home Assistant (monthly; check the "breaking changes" section).
- Update databases separately and deliberately. A PostgreSQL major upgrade needs `pg_upgrade` or a dump/restore; the `postgres:16` → `postgres:17` image swap will simply refuse to start. Pin the Postgres major and upgrade it once a year on purpose. (Tools like `pgautoupgrade/pgautoupgrade` automate this; still take a backup.)
- Rebuild-from-scratch is a legitimate update strategy for the whole host every year or two. If your Compose files and data are cleanly separated, it takes an afternoon and clears out accumulated cruft.

### Image provenance

Prefer images from the project itself (`ghcr.io/immich-app/...`, `jellyfin/jellyfin`), from LinuxServer.io (consistent conventions, weekly rebuilds, good documentation), or from official Docker Hub library images (`postgres`, `redis`, `nginx`). Be wary of random `someuser/coolapp` images with no linked Dockerfile. Docker Hub's anonymous pull rate limits (as of 2025, 10 pulls per IP per hour for unauthenticated users) can bite a host that pulls many images at once; log in with a free account (`docker login`) or mirror through a pull-through cache to raise the limit. Many projects have moved to GHCR (GitHub Container Registry) partly for this reason.

## Networking in depth

### The default bridge and Compose networks

Docker creates a bridge `docker0` (`172.17.0.0/16` by default) and each Compose project gets its own bridge network (`projectname_default`). Containers on a bridge get a private IP, reach the internet via NAT through the host, and can be reached from the host by published port only. Containers on the same user-defined network resolve each other by name via Docker's embedded DNS (`127.0.0.11`).

### The reverse-proxy network pattern

Create one shared network: `docker network create proxy`. The reverse proxy container joins it. Every web-facing service joins it too (`networks: [proxy, default]` — it stays on its own stack's default network for talking to its database, and on `proxy` for being reached). Publish **no ports** on services; publish only 80/443 on the proxy. The proxy reaches `http://jellyfin:8096` by name. Nothing else can reach anything, and the host firewall is irrelevant to inter-container traffic. This is the cleanest and most secure topology on a single host and is assumed throughout [Chapter 7](07-reverse-proxy-tls.md).

### `network_mode: host`

The container shares the host's network stack directly: no NAT, no port publishing, it just listens on the host's interfaces. Required or strongly preferred for: Home Assistant (device discovery), Plex/Jellyfin DLNA and some discovery features, Pi-hole/AdGuard when you want them to see real client IPs without macvlan, Frigate in some configurations, anything using mDNS/SSDP. The cost is loss of network isolation and port conflicts with the host.

### `network_mode: "service:gluetun"` (the VPN sidecar)

A container can share *another container's* network namespace. The standard pattern for torrent clients: run **Gluetun** (a VPN client container supporting dozens of providers, with a built-in kill switch) and set `network_mode: "service:gluetun"` on qBittorrent. All of qBittorrent's traffic leaves through the VPN or not at all; ports for qBittorrent's web UI are published *on the Gluetun container*. Covered in [Chapter 15](15-media.md).

### macvlan and ipvlan

A macvlan network gives each container its own MAC and IP on your physical LAN (or a VLAN sub-interface), so it appears as a separate device to your router and switch. Use it when a service needs a dedicated IP — a second DNS server, Home Assistant on the IoT VLAN, anything a device must reach by a fixed address on port 53 or 80 without conflicting with the host.

```yaml
networks:
  iot_vlan:
    driver: macvlan
    driver_opts:
      parent: eth0.30          # VLAN 30 sub-interface (create with ip link / netplan / systemd-networkd first)
    ipam:
      config:
        - subnet: 10.0.30.0/24
          gateway: 10.0.30.1
          ip_range: 10.0.30.64/27   # Docker assigns from here; exclude from DHCP
services:
  homeassistant:
    networks:
      iot_vlan:
        ipv4_address: 10.0.30.70
```

The known gotcha: **the host cannot talk to its own macvlan containers** (a kernel limitation of macvlan). If you need that, create a macvlan sub-interface on the host with its own IP and a route (a five-line script), or use `ipvlan` in L2 mode instead, which does not have the restriction on some configurations. Also, Wi-Fi interfaces generally cannot be macvlan parents.

### The Docker-and-firewall problem

Docker manages its own `iptables`/`nftables` chains (`DOCKER`, `DOCKER-USER`) and inserts them *before* the `INPUT`/`FORWARD` rules that `ufw` and `firewalld` manage. Consequence: `ufw deny 8080` does nothing to a container publishing `8080:80`; the port is open to whatever can reach the host. Countless people have unwittingly exposed databases and admin panels this way on VPSes.

Solutions, from simplest to most thorough:

1. **Publish on `127.0.0.1` only** (or not at all — use the proxy network). No published port on `0.0.0.0`, no problem.
2. **Use the `DOCKER-USER` chain**, which Docker guarantees to evaluate first and never touches. Rules there (e.g., `iptables -I DOCKER-USER -i eth0 ! -s 10.0.0.0/8 -j DROP`) genuinely filter container traffic. The `ufw-docker` script automates this for `ufw` users.
3. **Set `"iptables": false`** in `daemon.json` and manage everything yourself. Advanced; breaks Docker's networking unless you know exactly what you are doing.
4. **Rely on the network firewall.** On a home LAN behind a router with no port forwards, Docker's host-level exposure only matters to other LAN devices. Still fix it — the IoT VLAN should not be able to reach your Postgres — but it is not the emergency it is on a VPS.

Podman (below) does not have this problem, since it does not manipulate host firewall rules the same way in rootless mode.

## Storage considerations

- **Bind mounts on NFS/SMB.** Works for media (Jellyfin reading files) and mostly works for config, but **SQLite databases on network filesystems corrupt**. Sonarr, Radarr, Jellyfin, Home Assistant, Vaultwarden, and dozens of other apps use SQLite. Keep their config/database bind mounts on local disk; mount only bulk media over the network.
- **Docker on ZFS or Btrfs.** Fine with `overlay2`. Consider a dedicated dataset/subvolume for `/var/lib/docker` with `recordsize=128k` (or default) and exclude it from snapshots (it is rebuildable). Do snapshot `/opt/stacks`.
- **Database performance.** Postgres and MariaDB want their data on local SSD, not spinning disk and never a network share.
- **`tmpfs` mounts** for transcoding scratch directories keep writes off your SSD: `tmpfs: [/transcode]` or `volumes: [type: tmpfs, target: /transcode, tmpfs: {size: 4g}]`.

## Hardware access

- **Intel/AMD GPU for transcoding or ML**: pass `/dev/dri` — `devices: ["/dev/dri:/dev/dri"]` — and add the container's user to the `render`/`video` group (`group_add: ["render"]` or the numeric GID). Jellyfin, Plex, Frigate, Immich ML, and Tdarr all use this.
- **NVIDIA GPU**: install the NVIDIA Container Toolkit on the host; then `deploy: resources: reservations: devices: [{driver: nvidia, count: 1, capabilities: [gpu]}]` (or the legacy `runtime: nvidia`). Ollama, Frigate (TensorRT), Jellyfin NVENC, Immich, and the whole AI chapter rely on it.
- **USB devices** (Zigbee/Z-Wave sticks, Coral TPU): `devices: ["/dev/ttyUSB0:/dev/ttyUSB0"]` or, more robustly, by-id paths under `/dev/serial/by-id/`, which survive reboots and re-plugging.
- **`privileged: true`** gives the container every device and capability. It is the lazy fix and a security hole. Almost nothing genuinely needs it; Home Assistant's container docs ask for it (for full device access) and people grant it — accept the trade-off consciously or run HAOS in a VM instead.

## Podman

Podman is Red Hat's daemonless, rootless-by-default container engine with a Docker-compatible CLI (`alias docker=podman` works for most things). Its differences from Docker are its selling points:

- **Rootless.** Containers run as your unprivileged user; a container breakout yields your user, not root. Docker has a rootless mode too but it is not the default and has rough edges.
- **No daemon.** Each container is a child of the user's process tree, managed by systemd. No single point of failure, no socket to protect.
- **Quadlets.** Since Podman 4.4, you describe containers as systemd unit files (`~/.config/containers/systemd/vaultwarden.container`) and systemd starts, restarts, and depends them like any service. Elegant for people who like systemd; the `podlet` tool converts Compose files to Quadlets.
- **Compose support** via `podman compose` (wrapping either `docker-compose` or `podman-compose`). Works for most stacks; edge cases exist, especially around networking and `depends_on` health conditions.
- **Pods** — groups of containers sharing a network namespace, Kubernetes-style; `podman generate kube` and `podman play kube` bridge to Kubernetes YAML.

**Pick Podman if:** you run Fedora/RHEL-family hosts where it is native, you want rootless as the default posture, or you like the systemd integration. **Stick with Docker if:** you want zero friction with every project's documentation, GUI tools (Dockge, Portainer, Watchtower/Diun), and community help. The Docker-compatible surface is good but not perfect, and the self-hosting ecosystem's centre of gravity is firmly Docker.

## Kubernetes: when, and which

Kubernetes (k8s) is the industry standard for orchestrating containers across many machines: declarative desired-state, self-healing, rolling updates, service discovery, secrets, storage abstraction. It is also enormously more complex than Compose, and for a household's services on one to three machines, that complexity buys very little that Proxmox HA plus Compose does not.

**Run Kubernetes at home if:** you want to learn it (a genuinely good career reason), you already run it at work and want a matching lab, or you have many nodes and want workloads to reschedule automatically when one dies. **Do not run it because** you think it is what "real" infrastructure looks like — Compose is real infrastructure too, and most of the internet's small services run on it.

Distributions suited to home use:

- **k3s** (SUSE/Rancher) — a single-binary, lightweight, fully conformant Kubernetes with SQLite or embedded etcd, Traefik and a local-path storage provisioner included. Runs on a Pi. The most popular home-lab k8s by far.
- **Talos Linux** (Sidero) — an immutable, API-only Linux distribution that *is* a Kubernetes node: no SSH, no shell, configured entirely through `talosctl` and machine configs. Security-focused and beloved by the GitOps crowd; steeper initial learning but very stable to operate.
- **MicroK8s** (Canonical) — snap-packaged, add-ons for common components, easy on Ubuntu.
- **kind** / **minikube** — single-node clusters for local development and learning; not for running services.
- **Kubeadm on Debian VMs** — the "learn it properly" route, closest to the certification exams.

The home-lab Kubernetes stack that has emerged as standard: **Talos or k3s** nodes on Proxmox VMs; **Flux** or **Argo CD** for GitOps (the cluster state lives in Git, the controller applies it); **Longhorn** or **democratic-csi** (against a TrueNAS box) or **Rook-Ceph** for persistent storage; **MetalLB** or **kube-vip** for LoadBalancer IPs on a LAN; **Traefik**, **ingress-nginx**, or **Cilium**'s Gateway API for ingress; **cert-manager** for TLS; **External Secrets** or **Sealed Secrets**; **Renovate** to bump chart and image versions via PRs. The "home-operations" community (a GitHub org and Discord) maintains a widely-copied template repository for exactly this. Budget several weekends to get there and expect to learn a great deal. [Chapter 27](27-automation-iac.md) touches on the GitOps side.

**Docker Swarm** — Docker's own orchestrator — deserves a mention as the middle path: Compose-file syntax, multi-node scheduling, overlay networks, secrets, rolling updates, a fraction of Kubernetes' complexity. It is in maintenance mode (Docker Inc. has not invested in it for years) but works, and some people happily run three-node Swarms. It is a reasonable choice if you want multi-node without the k8s learning curve, with the caveat that its future is uncertain and the ecosystem around it is thin.

## Best-practice checklist

- [ ] Docker installed from Docker's repository; `daemon.json` sets log rotation and a non-conflicting address pool.
- [ ] One directory per stack under a single root, in Git; `.env` and data directories gitignored.
- [ ] Bind mounts for config and data; bulk data on the big storage mounted at consistent paths.
- [ ] SQLite-backed apps have their config on local disk, not NFS/SMB.
- [ ] Image tags pinned to at least major version; a notifier (Diun) or Renovate in place; no blind `latest` on anything with a database.
- [ ] No ports published on `0.0.0.0` except the reverse proxy's 80/443 (and things that genuinely need host networking); web services reach the proxy via a shared Docker network.
- [ ] The Docker/`ufw` interaction understood and handled (`DOCKER-USER` rules or localhost binding).
- [ ] `PUID`/`PGID` or `user:` set to a dedicated non-root host user; `no-new-privileges: true`; memory limits on anything that might leak; `privileged: true` only where unavoidable and understood.
- [ ] Healthchecks defined; something watches them ([Chapter 12](12-monitoring.md)).
- [ ] Backups cover `/opt/stacks` (or equivalent) and every bind-mounted data directory; databases dumped, not just file-copied ([Chapter 11](11-backups.md)).
- [ ] A snapshot or backup is taken before every update of a stateful service.
