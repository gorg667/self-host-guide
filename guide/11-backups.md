# Backups: The Chapter That Matters Most

Everything else in this guide is recoverable. Hardware can be replaced, operating systems reinstalled, containers redeployed from a Compose file in twenty minutes. Data — the photos, the documents, the years of notes, the password vault — cannot be recreated. A home lab without a tested backup strategy is not a home lab; it is a countdown.

This chapter covers the strategy (3-2-1 and its modern refinements), what to back up and how (files, databases, VMs, configuration), the tools (Restic, Borg, Kopia, Duplicati, Proxmox Backup Server, ZFS replication, rclone, and the simple ones), the destinations (local, a second machine, a friend's house, cloud object storage), the specific problem of backing up running containers and databases correctly, and — the part almost everyone skips — how to *test* that you can restore.

## The strategy

### 3-2-1

The classic rule: **3** copies of your data, on **2** different media/devices, **1** of them off-site.

- The live copy on your NAS is copy 1.
- A backup to a different device — a second machine, an external drive, a Proxmox Backup Server — is copy 2 and medium 2.
- A copy somewhere geographically distant — cloud storage, a drive at a relative's house, a server at a friend's — is copy 3 and the off-site.

RAID/ZFS mirroring is **not** a copy: it protects against drive failure only. A ZFS snapshot on the same pool is **not** a copy: it protects against deletion and ransomware-on-the-share, but not pool loss. A `cp` to another directory on the same drive is **not** a copy.

### Modern refinements: 3-2-1-1-0

- **+1**: one copy **offline or immutable** — something that a compromised machine cannot delete or encrypt. An external drive that is unplugged after each backup; an object-storage bucket with **object lock** (S3 Object Lock, B2's file-lock) or **append-only** credentials (Borg's `--append-only`, Restic's `rest-server --append-only`, rclone to a bucket whose key cannot delete); a ZFS snapshot on a *pull*-based replica that the source cannot touch. Ransomware in 2026 hunts for and destroys backups first; this is the countermeasure.
- **0**: **zero errors on verification** — you have actually restored from the backup and checked the result. Not "the job said success."

### What to protect, and how hard

Return to the classification from [Chapter 1](01-planning.md):

| Class | Examples | Strategy |
|---|---|---|
| **Irreplaceable** | Photos/videos, documents, password vault, notes, source code, Home Assistant config, tax records | Full 3-2-1-1-0. Nightly. Off-site encrypted. Immutable copy. Quarterly restore test. |
| **Painful** | Service configs (`/opt/stacks`), databases, VM/LXC images, Immich/Paperless metadata, Git repos, email | Nightly to a second device; off-site if cheap (configs and DBs are small — they always are cheap). Snapshot before every upgrade. |
| **Replaceable** | Media library, downloaded ISOs, Docker images, transcodes, thumbnails | Redundant storage; snapshots; optionally a slow, cheap replica (a second MergerFS box, a cold external drive). Or accept the loss and keep the *list* of what you had (Radarr/Sonarr databases, a `find > files.txt`). |

Spend on protection in proportion to irreplaceability. Most people spend too much backing up 20 TB of films and too little on 200 GB of photos.

### RPO and RTO

Two questions per data class: **how much can I lose** (Recovery Point Objective — nightly backups mean up to 24 hours) and **how long can I be down** (Recovery Time Objective — restoring 2 TB from cloud storage at 50 Mbps takes four days). For a household, nightly RPO and a day or two of RTO for bulk data is fine; for the password vault, hourly RPO is cheap; for configs, a snapshot before every change. Knowing these numbers tells you whether a local fast copy is needed *in addition to* the slow off-site one (it usually is).

## What to back up

### Files

The obvious part. Bind-mount directories from Docker stacks, NAS shares, home directories. The rule: **back up the data directories, not the containers.** Containers are ephemeral and rebuilt from images; the data is in the volumes.

### Databases

The part people get wrong. Copying a database's files (`/var/lib/postgresql/data`) while the database is running produces a *possibly* corrupt backup — the files may be mid-write. Three correct approaches:

1. **Dump** it: `pg_dump`/`pg_dumpall`, `mysqldump`/`mariadb-dump`, `sqlite3 .backup`, `mongodump`, `redis-cli --rdb`. Produces a consistent logical export. Run it as a pre-backup hook, then back up the dump file. Slightly slower to restore for huge databases; perfect for everything at home.
2. **Stop the container**, copy the files, start it. Simple, consistent, causes a brief outage. Fine for nightly at 3 am.
3. **Filesystem snapshot** (ZFS/Btrfs/LVM) of the database's dataset, then back up from the snapshot. Crash-consistent — equivalent to a power loss — which every modern database recovers from cleanly (Postgres via WAL, MariaDB InnoDB, SQLite journal). Zero downtime. The best option if your data is on a snapshotting filesystem.

A one-liner pattern for approach 1, run by cron or as a Restic/Borg pre-hook:

```bash
# Dump every Postgres container to a dumps/ directory before the file backup runs
for c in $(docker ps --filter "ancestor=postgres:16" --format '{{.Names}}'); do
  docker exec "$c" pg_dumpall -U postgres | zstd > "/opt/backups/dumps/${c}-$(date +%F).sql.zst"
done
find /opt/backups/dumps -mtime +7 -delete
```

Tools that automate this: **docker-db-backup** (tiredofit — dumps Postgres/MariaDB/Mongo/Redis/InfluxDB on a schedule, with notifications), **postgres-backup-local** (prodrigestivill), **db-backup** sidecars per stack, or **Backrest**/**Kopia** pre-hooks.

**SQLite** deserves a special note because it is everywhere (Sonarr, Radarr, Jellyfin, Vaultwarden, Home Assistant, Uptime Kuma, Grafana, Gitea by default, Paperless optionally). Copying a `.db` file while the app is writing can catch it mid-transaction; the `-wal` and `-shm` sidecar files must be captured together. Use `sqlite3 file.db ".backup '/backups/file.db'"` for a consistent copy, stop the container first, or snapshot the filesystem. Vaultwarden's docs specifically recommend `.backup`.

### Containers and configuration

`/opt/stacks` (or wherever your Compose files live) plus every bind-mounted config directory. Small, precious, changes often. Keep it in **Git** as well — that is a backup with history and a diff of every change. `.env` files with secrets: encrypted in the backup (all the tools below encrypt) and *not* in the Git repo unless encrypted with **SOPS**/**age** or **git-crypt** ([Chapter 21](21-passwords-secrets.md)).

### Virtual machines and LXCs

Two philosophies. **Back up the whole VM** (Proxmox Backup Server, `vzdump`, Veeam) — restore is trivial and complete, files are large, and databases inside are crash-consistent (with the QEMU guest agent, the filesystem is quiesced, which is better). **Or treat the VM as rebuildable** and back up only its data (Restic inside the VM) — smaller backups, but restoring means reinstalling the OS. For a Docker-host VM, doing *both* is cheap: PBS nightly for the whole VM (fast, complete restore) plus Restic for the data directories (granular file restore, off-site).

### The things people forget

- **The OS/hypervisor config**: Proxmox `/etc/pve`, OPNsense's XML backup (it has a built-in scheduled export — to Git, Nextcloud, or Google Drive), switch configs, UniFi controller backups, Home Assistant snapshots, the router's DDNS credentials.
- **Secrets that unlock the backups**: the Restic/Borg repository password, the ZFS encryption key, the Bitwarden master password. If these live *only* inside the thing being backed up, you cannot restore. Print them. Put them in a safe, a bank box, or a sealed envelope with a trusted person. Store a copy in a *different* password manager or an encrypted USB stick kept off-site.
- **Documentation**: the notes on how everything is set up ([Chapter 28](28-maintenance-operations.md)).
- **Phone photos not yet uploaded**: Immich/Nextcloud/Syncthing auto-upload closes this gap.
- **Email**, if you self-host it ([Chapter 20](20-communication.md)) — Mailcow has a backup script; back up the mail store *and* the config.
- **Data in SaaS you still use**: exports from Google Takeout, GitHub repos (Gitea mirrors), Spotify playlists. A home lab is a good place to keep copies of your cloud data too.

## The tools

### Restic

A single Go binary; content-defined chunking with deduplication; AES-256 encryption always on; snapshots; dozens of backends natively (local, SFTP, S3/B2/Wasabi/MinIO/Garage, Azure, Google Cloud, **rclone** for everything else — Google Drive, OneDrive, Dropbox, Hetzner Storage Box via SFTP or WebDAV, Proton Drive). `restic backup /data`, `restic snapshots`, `restic restore latest --target /tmp/r`, `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune`, `restic check`, `restic mount` (browse any snapshot as a filesystem). Every snapshot is a full view; storage grows only by changed chunks.

**Strengths:** the most flexible backends; simple mental model; excellent for pushing to cloud object storage and to a friend's SFTP server; `rest-server` (its own tiny server) supports **append-only mode** for the immutable copy; very active development and a large community.

**Weaknesses:** memory use during backup and prune scales with repository size (a multi-TB repo wants several GB of RAM; better since v0.14's compression and index improvements); prune can be slow; no built-in scheduler or UI (see below).

**Frontends:** **Backrest** (a modern web UI and scheduler for Restic — repositories, plans, hooks, retention, restore browsing; the current community favourite), **resticprofile** (a config-file-driven wrapper with schedules and hooks), **autorestic**, **restic-exporter** for Prometheus, **Resticker**.

```yaml
# Backrest: Restic with a web UI
services:
  backrest:
    image: garethgeorge/backrest:latest
    container_name: backrest
    restart: unless-stopped
    volumes:
      - ./data:/data
      - ./config:/config
      - ./cache:/cache
      - /opt/stacks:/userdata/stacks:ro       # what to back up
      - /mnt/tank/photos:/userdata/photos:ro
      - /mnt/tank/documents:/userdata/documents:ro
      - /var/run/docker.sock:/var/run/docker.sock  # optional: for pre-hook docker exec pg_dump
    environment:
      BACKREST_DATA: /data
      BACKREST_CONFIG: /config/config.json
      XDG_CACHE_HOME: /cache
      TZ: Europe/London
    ports:
      - "127.0.0.1:9898:9898"
```

### BorgBackup (Borg)

The other deduplicating, encrypting, chunking backup tool, older (2015, forked from Attic) and equally respected. Repositories are local paths or SSH (`user@host:/path`) — **no native cloud object-storage backend** (Borg 2, in beta as of 2025–2026, adds rclone/S3-style backends). Excellent compression options (zstd, lz4, lzma), `borg mount` to browse, `borg check`, and **append-only mode** on the server side. Borg's dedup and compression are typically a bit more space-efficient than Restic's; its memory use is lower.

**Frontends:** **Borgmatic** (YAML-configured wrapper with schedules, database dump hooks for Postgres/MySQL/SQLite/Mongo built in, healthchecks.io/ntfy integration, retention — the standard way to run Borg), **Vorta** (desktop GUI), **BorgWarehouse** (a web UI for *hosting* Borg repositories for many clients), **Borgbase** (a commercial hosted Borg/Restic target run by the Vorta author — popular and reasonably priced). **Hetzner Storage Box** supports Borg over SSH natively, making it the classic cheap off-site target (~EUR 4/month for 1 TB, EUR 13 for 5 TB as of 2026).

**Pick Borg if:** your target is SSH-reachable (a second machine, a Hetzner box, a friend's server) and you want the most storage-efficient repository with database hooks handled by Borgmatic.

### Kopia

A newer (2019) Go tool combining Restic's cloud-backend breadth with **a built-in web UI and scheduler** (KopiaUI / the `kopia server` mode), policies per path (retention, compression, ignore rules, actions/hooks), encryption, dedup, error-correction option, snapshot mounting, and **repository server** mode for multiple clients sharing one repository with per-user access. Backends: local, SFTP, S3, B2, GCS, Azure, WebDAV, rclone.

**Strengths:** the UI and policies make it the most approachable "serious" tool; multi-client repository server is elegant for backing up several machines to one deduplicated store; fast.

**Weaknesses:** smaller community than Restic/Borg; the UI is functional rather than polished; occasional rough edges in repository maintenance.

**Pick Kopia if:** you want Restic's flexibility with an integrated UI and scheduler, without a separate frontend.

### Duplicati

A .NET tool with a web UI, incremental block-based backups, encryption, and a very long list of cloud backends (including consumer services like Google Drive, OneDrive, Dropbox, Mega, Jottacloud). Long-running beta status (2.0.x for many years; a 2.1 stable series arrived in 2024–2025), a history of database-corruption complaints in older versions, and slow restores on large sets — it is the tool people used before Restic/Kopia matured and the one they most often migrate away from. Fine for small backups to consumer cloud storage; not the first choice for a NAS.

### Duplicacy

A lock-free dedup backup tool (Go) with a CLI (free for personal use) and a paid web UI. Notable for supporting multiple clients backing up to one repository *without* a server and for cross-client dedup. Solid and fast; a smaller community and the paid GUI keep it niche.

### Proxmox Backup Server (PBS)

Covered in [Chapter 4](04-os-and-hypervisors.md): the purpose-built backup server for Proxmox VE VMs and LXCs (and, via `proxmox-backup-client`, arbitrary Linux directories). Deduplicated chunks, incremental with dirty-bitmap tracking (a 100 GB VM with 1 GB of changes backs up in seconds), client-side encryption, scheduled verification, prune and garbage collection, **sync jobs** to a remote PBS (off-site — pull or push), namespaces, tape support, and single-file restore from VM images. Runs on its own hardware or as a VM on a *different* host. If you run Proxmox, this is the backup layer for the VM level; pair with Restic/Borg/Kopia for file-level off-site.

### ZFS and Btrfs replication

Snapshots + `zfs send | zfs recv` (or `btrfs send | btrfs receive`) over SSH to another pool. Incremental, block-level, extremely efficient, preserves every property, and with raw encrypted sends the target never sees plaintext. Tools: **sanoid/syncoid**, **zrepl**, **znapzend**, TrueNAS replication tasks, **btrbk**. The replica is a *live filesystem* on another machine — restore is `zfs clone` or just mount it and copy back. Combine with a **pull** model (the backup server SSHes *into* the source with a restricted key and pulls snapshots) so a compromised source cannot destroy the replica.

This is the fastest and most complete method for a second-machine copy and for keeping the *whole history* (every hourly/daily snapshot) off-box. It requires ZFS/Btrfs on both ends. It does **not** get you to cloud object storage directly (though `zfs send | restic`/`rclone` to a file is possible and awkward — use Restic for that leg).

### rclone

Not a backup tool — a **sync/copy tool for cloud storage** ("rsync for the cloud") with 70+ backends and a `crypt` overlay for client-side encryption. `rclone sync /mnt/tank/photos b2crypt:photos` mirrors a directory to an encrypted bucket. No versioning or dedup by itself (use `--backup-dir` for a poor man's versioning, or rely on bucket versioning/object lock). Ideal for: mirroring bulk media to cheap storage, serving as Restic's backend for exotic providers, and *pulling* your cloud data (Google Drive, OneDrive) home. Also mounts cloud storage as a filesystem.

### rsync, Syncthing, and simple copies

**rsync** to an external drive or another host (`rsync -aHAX --delete`), especially with `--link-dest` for hard-linked incremental snapshots (the classic "rsnapshot" pattern; **rsnapshot** and **BackInTime** package it) is a perfectly good *local* backup with no encryption or dedup. It produces plain files you can browse without any tool — a real advantage for a decade from now.

**Syncthing** is *sync*, not backup: a deletion propagates instantly to every device. With **file versioning** (staggered) enabled on the receiving side it becomes a passable backup for documents; do not rely on it as your only copy.

**Cold external drives**: a monthly `rsync` or Restic run to a USB drive that is then unplugged and put in a drawer (or a fireproof box, or your desk at work) is the cheapest immutable-offline copy there is. Two drives, rotated, one always off-site: 3-2-1-1 for USD 200.

### Comparison

| | Restic | Borg | Kopia | Duplicati | PBS | ZFS replication | rclone |
|---|---|---|---|---|---|---|---|
| Dedup + encryption | Yes | Yes (best ratio) | Yes | Yes (block) | Yes (chunk) | Snapshots; encryption via dataset | `crypt` only, no dedup |
| Cloud object storage | **Native, many** | Borg 2 only (beta) | Native, many | Native, very many | No (sync to remote PBS) | No | **Everything** |
| SSH / second machine | Yes (SFTP, rest-server) | **Yes (native)** | Yes | Yes | PBS-to-PBS | **Yes** | Yes |
| Built-in UI/scheduler | No (Backrest) | No (Borgmatic/Vorta) | **Yes** | Yes | Yes | TrueNAS UI; else CLI | No |
| DB dump hooks | Via wrapper/pre-hooks | **Borgmatic built in** | Actions | Scripts | Guest agent fsfreeze | Snapshot = crash-consistent | n/a |
| Append-only / immutable | rest-server, S3 lock | **Yes (server-side)** | Server ACLs, S3 lock | Bucket features | Namespaces/ACLs | Pull model | Bucket lock |
| Browse/mount snapshots | Yes | Yes | Yes | Restore UI | Yes (file restore) | It's a filesystem | n/a |
| RAM (multi-TB repo) | Medium–high | Low | Medium | Medium | Low | Low | Low |
| Best for | Cloud + friend SFTP + flexibility | SSH targets, Hetzner box, efficiency | UI + multi-client | Consumer clouds, small sets | Proxmox VMs/LXCs | ZFS-to-ZFS second machine | Bulk mirrors; exotic backends |
