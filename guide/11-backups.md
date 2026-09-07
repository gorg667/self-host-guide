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

## Destinations

### Local second device

A second machine on the LAN — the PBS box, a Raspberry Pi with a big USB drive, an old NAS, the other Proxmox node — receiving nightly backups. Fast to back up, fast to restore, cheap. Protects against drive/pool/host failure, not against fire, theft, or a whole-LAN ransomware event unless the copy is pull-based or append-only.

### Cloud object storage

**Backblaze B2** (~USD 6/TB/month, free egress up to 3× stored per month; S3-compatible; object lock supported) is the community default. **Hetzner Storage Box** (~EUR 4/1 TB, EUR 13/5 TB, EUR 26/10 TB — per month; SFTP/SMB/WebDAV/Borg/rsync; snapshots; no S3) is the value pick in Europe and excellent for Borg. **Wasabi** (~USD 7/TB, no egress fees, 1 TB minimum, 90-day retention minimum), **Storj** (decentralised, ~USD 4/TB), **Scaleway Glacier**, **AWS S3 Glacier Deep Archive** (~USD 1/TB/month but slow and expensive to restore — only for the disaster copy of something you hope never to restore), **Cloudflare R2** (no egress fees, 10 GB free), **iDrive e2** (aggressive pricing). Consumer clouds (Google Drive, OneDrive, Dropbox) work via rclone but have API rate limits, may terminate accounts for "abuse," and are poor targets for millions of small chunks — fine for a few hundred GB, not for TBs. **Always encrypt client-side** (every tool above does); the provider should see only ciphertext.

### A friend's or relative's house

The self-hoster's off-site: a small machine (Pi 5 + USB drive, or an N100 box) at another household, reachable over a mesh VPN ([Chapter 8](08-remote-access-vpn.md)), receiving Restic/Borg/ZFS pushes — or, better, *pulling* from you. Reciprocate: host theirs. Zero monthly cost, full control, real geographic separation. The catch is the human element (their internet goes down, they unplug it, they move house); monitor it.

### Cold offline media

External drives rotated off-site; **LTO tape** for people with 50+ TB and patience (a used LTO-6/7 drive costs USD 300–800, tapes are USD 5–15/TB, tapes last 30 years, and nothing is more ransomware-proof than a tape in a drawer — PBS supports tape natively); **M-Disc** Blu-ray for tiny precious sets (100 GB per disc, rated for centuries). Slow, manual, and the only truly air-gapped option.

## Backing up a Docker host: a worked pattern

A reference approach for a Tier 1–2 Docker host with data on a ZFS/Btrfs pool:

1. **Snapshots** hourly on the data pool (sanoid/btrbk): instant local undo for the last 48 hours, 30 days of dailies.
2. **02:30 — pre-backup hooks**: `pg_dumpall` / `mariadb-dump` / `sqlite3 .backup` for every database into `/opt/backups/dumps`; Home Assistant backup via its API; Vaultwarden `sqlite3 .backup`.
3. **03:00 — local**: PBS backs up the Docker-host VM (if on Proxmox), *or* ZFS replication sends the `tank/docker` and `tank/photos` datasets to the second machine.
4. **03:30 — off-site**: Restic (via Backrest) backs up `/opt/stacks`, `/opt/backups/dumps`, `/mnt/tank/photos`, `/mnt/tank/documents` to B2 (or Borg via Borgmatic to a Hetzner box / friend's machine). Retention: 7 daily, 4 weekly, 12 monthly, 3 yearly. Bucket has object lock / repo is append-only.
5. **Weekly**: `restic check --read-data-subset=5%` or `borg check`; ZFS scrub monthly.
6. **Monthly**: rsync the photo and document datasets to a rotating external drive; swap with the one at the office/parents'.
7. **Every run** pings **Healthchecks.io** (or self-hosted **Healthchecks**) / **Uptime Kuma push monitor**; a missed ping alerts via ntfy ([Chapter 12](12-monitoring.md)).
8. **Quarterly**: restore drill (below).

The media library is not in step 4. It has ZFS redundancy and snapshots; it is either re-acquirable or mirrored to a cheap cold copy separately.

## Testing restores

A backup that has never been restored is a hypothesis. Test it.

**Monthly, small:** pick a random file from a random snapshot and restore it to `/tmp`. Compare checksums. Takes two minutes. Backrest and Kopia make this a UI click; `restic restore latest --include /path/to/file --target /tmp/r`.

**Quarterly, medium:** restore a whole service. Spin up a fresh directory, restore its config and data from backup, restore the database dump into a fresh Postgres container, `docker compose up`, log in, verify the data is there and recent. Then throw it away. This catches the errors that matter: "the database dump was empty," "the bind mount path changed," "the `.env` was never backed up."

**Yearly, full:** the disaster drill. Pretend the primary host is gone. On a spare machine (or a VM), install the OS from scratch following your documentation, install Docker, restore `/opt/stacks` and the data from the *off-site* copy (not the local one — the local one burned too), bring up the stack. Time it. Write down every step you had forgotten to document. This is the only way to know your RTO and to discover that your documentation is fiction.

**Verify integrity automatically:** `restic check`, `borg check --verify-data` (slow), `kopia snapshot verify`, PBS verification jobs, ZFS scrubs on the replica pool. Schedule them.

**Watch for silent failure:** a job that runs but backs up nothing (a mount that was not mounted, so it backed up an empty directory — this is *very* common with NFS/SMB sources), a snapshot that is 0 bytes, a dump that contains only an error message. Alert on backup *size* anomalies, not just on job exit codes. Healthchecks-style dead-man's switches catch jobs that never ran; size checks catch jobs that ran and did nothing.

## Ransomware-specific defences

- **Pull, don't push**, where possible: the backup server fetches from the source with a read-only key; the source has no credentials to the backup store.
- **Append-only / immutable** for the off-site copy: Borg append-only mode, Restic `rest-server --append-only`, S3 Object Lock in compliance mode with a retention period, Hetzner Storage Box snapshots (which the client cannot delete).
- **Separate credentials**: the backup destination's credentials must not be reachable from the machines being backed up in a form that permits deletion. A B2 application key scoped to write-only (no `deleteFiles`) plus lifecycle rules for pruning, or prune from a separate trusted machine.
- **Offline copy**: the rotated external drive. Nothing beats unplugged.
- **Snapshot retention on the replica**: if ransomware encrypts your files, ZFS replication will faithfully replicate the encrypted files — but the replica's *older snapshots* still hold the clean data. Keep weeks of snapshots on the replica, and make sure the source cannot destroy them (pull model, or a restricted SSH key that permits `zfs recv` but not `zfs destroy`).

## Recommendations by tier

**Tier 1 (one machine, Tier-1 budget):** Btrfs/ZFS snapshots on the data drive (btrbk/sanoid). **Restic via Backrest** nightly to **Backblaze B2** (or Hetzner) for irreplaceable and painful data, with DB dump pre-hooks. A rotating **external USB drive** monthly for the offline copy. Healthchecks ping. Total cost: USD 3–10/month for a few hundred GB off-site. Restore test quarterly.

**Tier 2 (compute + NAS):** ZFS snapshots + **syncoid/zrepl replication** from the NAS to a second box (the PBS machine, or the Proxmox node's local pool) — pull-based. **PBS** for all VMs/LXCs, with a **sync job to a remote PBS** (a friend's, or a small VPS with a big disk) or PBS's own backups pushed off-site via Restic. **Restic/Borg** off-site for the irreplaceable datasets. Object lock on the bucket. Monthly external drive for photos.

**Tier 3:** all of the above, plus a **second PBS off-site**, raw encrypted ZFS replication to a remote pool, tape or Glacier Deep Archive for the yearly full, and automated restore testing (a script that restores last night's backup into a scratch VM and runs smoke tests).

## Checklist

- [ ] Data classified; irreplaceable data has three copies, two media, one off-site, one immutable/offline.
- [ ] Backup tool chosen; repository encrypted; **the repository password/key is stored somewhere that does not depend on the lab** (printed, in a second password manager, with a trusted person).
- [ ] Databases dumped or snapshotted consistently — never file-copied while running.
- [ ] `/opt/stacks` (all Compose files and configs) backed up nightly and in Git.
- [ ] Off-site destination configured; client-side encryption on; append-only or object lock enabled.
- [ ] Retention policy set and pruning automated.
- [ ] Every backup job reports to a dead-man's switch (Healthchecks/Uptime Kuma push); alerts go to your phone.
- [ ] Integrity checks (`restic check`/`borg check`/PBS verify/ZFS scrub) scheduled.
- [ ] Backup size monitored for anomalies (empty-mount problem).
- [ ] Monthly single-file restore; quarterly service restore; yearly full disaster drill from the off-site copy — **dates in the calendar**.
- [ ] Router/firewall/switch/hypervisor configs exported and included.
- [ ] Media library's protection level decided consciously (redundancy + snapshots, or a cold copy, or accepted loss with a manifest).
