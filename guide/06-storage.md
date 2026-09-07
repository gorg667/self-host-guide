# Storage: Filesystems, Redundancy, and Sharing

Storage is where your data lives, and data is the only part of a home lab that cannot be re-downloaded or rebuilt. Every other component — the hardware, the OS, the containers — is replaceable in an afternoon. This chapter covers the technologies that keep data intact: ZFS in depth (because it is the community's default and deserves the space), Btrfs, traditional mdadm/LVM, the MergerFS + SnapRAID pattern for media, Ceph for clusters, the network protocols for sharing storage (NFS, SMB, iSCSI), drive health monitoring, and capacity planning.

One principle to carry through the chapter: **redundancy is not backup.** RAID, mirrors, and parity protect against *drive failure*. They do nothing against accidental deletion, ransomware, a bug that corrupts files, a fire, or a fat-fingered `rm`. Every technology here should be paired with [Chapter 11](11-backups.md).

## Concepts first

**Bit rot** is the silent corruption of data at rest: a bit flips on a platter or in flash, the drive does not notice, and years later a photo has a grey band across it. Traditional filesystems (ext4, XFS, NTFS) cannot detect this. **Checksumming filesystems** (ZFS, Btrfs) store a hash of every block and verify it on read; with redundancy, they can *repair* it from a good copy. This is the main reason the community pushes ZFS and Btrfs for anything precious.

**Redundancy levels**: a **mirror** (RAID1) writes every block to two or more drives; capacity is one drive's worth, survives n−1 failures. **Single parity** (RAID5, RAIDZ1) stripes data across n drives with one drive's worth of parity; capacity n−1, survives one failure. **Double parity** (RAID6, RAIDZ2) survives two. **Triple parity** (RAIDZ3) survives three. **Striping** (RAID0) has no redundancy and is not for data you care about.

**Rebuild risk**: when a drive fails, the array rebuilds onto a replacement by reading *every other drive in full*. With 16–24 TB drives this takes one to two days, during which a second failure (statistically more likely because the surviving drives are the same age and under stress) is fatal for single-parity arrays. This is why the modern recommendation is **RAIDZ2/RAID6 for arrays of large drives**, and why mirrors remain popular: a mirror rebuild reads one drive, not all of them.

**URE (unrecoverable read error)** rates on consumer drives (~1 in 10^14 bits ≈ every 12.5 TB read) mean that a RAID5 rebuild across 40 TB of surviving drives has a meaningful chance of hitting an unreadable sector. Traditional RAID controllers kill the array; ZFS loses only the affected file and tells you which one. Another reason for ZFS and for double parity.

**Snapshots** are point-in-time, read-only views of a filesystem that cost almost nothing to create (they share blocks with the live data via copy-on-write). They are the fastest defence against "I deleted the wrong thing" and, when sent to another machine, a fast incremental backup mechanism. ZFS and Btrfs have them natively; LVM has them awkwardly; ext4/XFS do not.

## ZFS

ZFS (via OpenZFS on Linux and FreeBSD) is a combined volume manager and filesystem designed at Sun in the early 2000s for data integrity above all else. It is the storage layer under TrueNAS, is native in Proxmox, and is a first-class option on Debian/Ubuntu (via the `zfs-dkms` or Ubuntu's in-tree module). For anyone storing irreplaceable data on more than one drive, it is the default recommendation of this guide.

### Vocabulary

- **vdev** (virtual device): a group of drives with a redundancy type — a mirror of 2–3 drives, a RAIDZ1/2/3 group of 3–12 drives, or a single drive (no redundancy). Redundancy exists *within* a vdev.
- **pool** (zpool): one or more vdevs striped together. Data is spread across vdevs; **losing any vdev loses the pool**. So every vdev should be redundant.
- **dataset**: a filesystem within the pool, with its own properties (compression, record size, quotas, snapshots) and mount point. Create many: `tank/media`, `tank/photos`, `tank/docker`, `tank/backups`. Datasets are free; they let you snapshot, replicate, and tune each kind of data separately.
- **zvol**: a block device carved from the pool, for VM disks or iSCSI.
- **ARC**: the in-RAM read cache. ZFS uses up to half of system RAM by default and releases it under pressure. **L2ARC**: an optional SSD extension of ARC; rarely useful at home (you need more RAM first). **SLOG**: an optional separate device for the ZFS intent log, which accelerates *synchronous* writes only (NFS with `sync`, databases, VM disks); needs an enterprise SSD with power-loss protection; useless for normal file copies. **Special vdev**: an SSD vdev holding metadata and optionally small files; dramatically speeds directory listings on large spinning pools; *must be redundant* because losing it loses the pool.
- **scrub**: reads every block in the pool and verifies checksums, repairing from redundancy. Schedule monthly.
- **resilver**: rebuilding a replaced drive.

### Choosing a layout

| Layout | Drives | Usable | Survives | Read perf | Write perf | Rebuild stress | Expandability |
|---|---|---|---|---|---|---|---|
| 2-way mirror | 2 | 50% | 1 | 2× | 1× | Low (reads one drive) | Add another mirror vdev; replace both drives with larger |
| 3-way mirror | 3 | 33% | 2 | 3× | 1× | Low | Same |
| Striped mirrors (RAID10) | 4, 6, 8… | 50% | 1 per mirror | n× | n/2× | Low | Add mirror pairs |
| RAIDZ1 | 3–5 | (n−1)/n | 1 | Good | Good | High | Add another vdev; **RAIDZ expansion** (OpenZFS 2.3+, 2025) adds single drives |
| RAIDZ2 | 5–10 | (n−2)/n | 2 | Good | Good | High | Same |
| RAIDZ3 | 8–15 | (n−3)/n | 3 | Good | OK | High | Same |

Guidance:

- **Two drives**: a mirror. Simple, fast rebuild, easy to grow (replace one drive with a bigger one, resilver, replace the other, resilver, pool grows).
- **Four drives**: striped mirrors if you value performance and flexible growth; RAIDZ2 if you value capacity (both give 50% usable with four drives, but RAIDZ2 survives *any* two failures while striped mirrors survive two only if they are in different pairs). RAIDZ1 with four drives is acceptable for replaceable data and not for precious data.
- **Six to eight drives**: RAIDZ2. This is the home NAS sweet spot: 6×16 TB in RAIDZ2 = ~58 TB usable, survives two failures.
- **More than ten drives**: two RAIDZ2 vdevs, or RAIDZ3, or striped mirrors.
- **RAIDZ1 with drives over ~8 TB** is discouraged for precious data because of rebuild time and URE risk.
- **Mixed sizes**: a vdev uses the size of its smallest member. ZFS is not the tool for a pile of random drives — that is Unraid or MergerFS+SnapRAID territory.
- **Do not use dedup.** It needs enormous RAM (the "1 GB per TB" myth came from here), rarely saves much at home, and is hard to turn off. Compression, by contrast, is free — enable it everywhere.

### RAIDZ expansion

OpenZFS 2.3 (released January 2025; in TrueNAS 24.10+ and Proxmox 8.4/9+) added the long-awaited ability to add a single drive to an existing RAIDZ vdev. Caveats: existing data keeps its old parity ratio until rewritten (so usable space grows less than you would expect until you rewrite files — a `zfs send | zfs recv` to a new dataset or a rebalancing script does this), and the operation takes as long as a resilver. It removes the biggest historical objection to RAIDZ for home users who grow gradually.

### Creating a pool

```bash
# Identify drives by stable IDs, never by /dev/sdX (which can change between boots)
ls -l /dev/disk/by-id/ | grep -v part

# A 6-drive RAIDZ2 pool named 'tank'
zpool create -o ashift=12 \
  -O compression=lz4 -O atime=off -O xattr=sa -O acltype=posixacl \
  -O normalization=formD -O mountpoint=/mnt/tank \
  tank raidz2 \
  /dev/disk/by-id/ata-WDC_WD160EDGZ-11B2DA0_XXXXXXXX \
  /dev/disk/by-id/ata-WDC_WD160EDGZ-11B2DA0_YYYYYYYY \
  ... (6 total)

# Datasets for different data
zfs create tank/media      # large sequential files
zfs set recordsize=1M tank/media
zfs create tank/photos
zfs create tank/documents
zfs create tank/docker     # container config/data
zfs create -o recordsize=16k tank/db   # databases (match the DB page size; 8k–16k)
zfs create tank/backups

# Status
zpool status -v
zfs list -o name,used,avail,compressratio,mountpoint
```

Property notes:

- **`ashift=12`** (4 KiB sectors) is correct for every modern drive, including "512e" drives that lie about their sector size. `ashift=13` for some SSDs. Getting this wrong is permanent and hurts performance.
- **`compression=lz4`** (or `zstd` for slightly better ratios at more CPU) costs nothing on incompressible media and saves real space on everything else. Always on.
- **`atime=off`** avoids a write on every read. Always.
- **`xattr=sa`, `acltype=posixacl`** are needed for Docker, Samba ACLs, and general sanity on Linux.
- **`recordsize`**: default 128K is fine; 1M for media/backups; 16K for database datasets; 64K for VM zvols (`volblocksize`).
- **`sync=disabled`** on a dataset trades safety for speed; only on scratch data.
- **Encryption**: `-O encryption=aes-256-gcm -O keyformat=passphrase` (or a keyfile) at dataset creation. Native ZFS encryption encrypts data and most metadata; dataset names and sizes remain visible. Encrypted datasets can be replicated raw (`zfs send -w`) to an untrusted backup target that never sees the key — the ideal off-site pattern. The alternative is LUKS underneath ZFS, which encrypts everything but loses the raw-send trick.

### Snapshots and replication

```bash
zfs snapshot tank/photos@2026-09-07
zfs list -t snapshot
zfs rollback tank/photos@2026-09-07          # revert (destroys later snapshots unless -r)
ls /mnt/tank/photos/.zfs/snapshot/2026-09-07/  # browse a snapshot read-only
zfs destroy tank/photos@2026-09-07
```

Automate with **sanoid** (policy-based snapshot creation and pruning — "keep 48 hourly, 30 daily, 6 monthly") and **syncoid** (its companion for incremental replication to another pool or host over SSH). Alternatives: **zrepl** (a single Go daemon doing both, with a push/pull model and good for many datasets), **zfs-auto-snapshot** (older, simpler), **pyznap**, and TrueNAS's built-in periodic snapshot and replication tasks. A replicated snapshot chain on a second machine is a real backup of the *files*; it is still on the same site until you replicate off-site too.

### ZFS on what?

- **TrueNAS**: the UI for all of this. The right choice if you do not want to type `zpool`.
- **Proxmox**: ZFS root and data pools in the installer and UI; snapshots/replication of VMs between nodes built in.
- **Debian/Ubuntu**: `apt install zfsutils-linux` (Ubuntu) or `zfs-dkms` from contrib (Debian). Perfectly viable as a bare-metal NAS OS with Samba/NFS installed by hand; Cockpit with the 45Drives ZFS/Samba plugins gives it a web UI.
- **Memory**: 8 GB minimum, 16 GB comfortable, more if you want a bigger ARC. ECC preferred, not required ([Chapter 2](02-hardware.md)).
- **Controllers**: an HBA in IT mode or motherboard SATA. **Never** hardware RAID (ZFS must see the raw drives). **USB** enclosures work for a mirror of two drives on a Tier 1 box, with the caveat that USB bridges occasionally drop and resilver; avoid USB for larger arrays.

### ZFS gotchas

- **Never fill past 80–85%.** Performance drops sharply and fragmentation becomes permanent.
- **`/dev/sdX` names change.** Always use `/dev/disk/by-id/`.
- **Pool import on a new machine**: `zpool import -f tank`. Your pool is portable — this is disaster recovery.
- **Feature flags**: a pool upgraded with newer features cannot be imported by an older OpenZFS. Do not `zpool upgrade` casually if you might move the pool to an older system.
- **Removing a vdev** from a pool is possible only for mirrors and single drives (device removal), not RAIDZ. Plan vdev layout before adding data.
- **`zfs destroy` is immediate and permanent.** Type dataset names carefully. `-n` does a dry run.

## Btrfs

Btrfs is the Linux-native copy-on-write filesystem with checksums, snapshots, transparent compression, and built-in multi-device support. It is the default on Fedora and openSUSE, powers Synology's newer models (on top of mdadm), and is the backing store for Unraid's cache pools.

**Where it shines:** single-disk and mirror (`raid1`, and the `raid1c3`/`raid1c4` variants for three and four copies) setups. Btrfs `raid1` is unusual — it means "two copies of every block on any two devices," which means you *can* mix drive sizes and it will use the space sensibly. Add and remove devices from a live filesystem; convert between profiles with `btrfs balance`; snapshot subvolumes instantly; send/receive incremental snapshots like ZFS. Lighter on RAM than ZFS, in the mainline kernel (no DKMS), and well suited to a Tier 1 box with two USB drives or a mini PC with two NVMe slots.

**Where it does not:** **Btrfs RAID5/6 is still not safe for production** (the "write hole" problem remains documented in the kernel's own status page as of 2026; improvements in recent kernels help but the upstream recommendation is still to avoid it for metadata). If you want parity, use ZFS or mdadm. Btrfs's tooling for diagnosing and repairing problems is less friendly than ZFS's; `btrfs check --repair` comes with a warning to ask on the mailing list first. Quotas (`qgroups`) have performance implications. Databases and VM images on Btrfs want `nodatacow` (`chattr +C`), which disables checksumming for those files — a trade-off ZFS does not force.

**Tooling:** **snapper** (openSUSE's snapshot manager, with timeline and pre/post-package-update snapshots) and **btrbk** (snapshot + send/receive backups, excellent for the "snapshot hourly, replicate nightly to a USB drive or another host" workflow). Synology's Snapshot Replication and Unraid's cache-pool snapshots are Btrfs underneath.

**Verdict:** Btrfs mirror is the right choice for a Tier 1 machine that wants checksumming without ZFS's RAM appetite or out-of-tree module; ZFS is the right choice for anything with parity or more than a handful of drives.

## mdadm, LVM, ext4, and XFS: the traditional stack

**mdadm** is Linux software RAID: assemble drives into a `/dev/md0` device with RAID 0/1/5/6/10, then put any filesystem on it. **LVM** adds a volume layer (resize, thin provisioning, snapshots of a sort). **ext4** and **XFS** are the mature, fast, non-checksumming filesystems that go on top. Synology, QNAP, and every Linux server from 2005–2015 used this stack, and it still works.

**Why you would:** you know it; you want maximum compatibility; you want the flexibility of adding a drive to an mdadm RAID5/6 with `--grow` (which ZFS only recently matched); you are on a low-memory device; or you want a boot drive setup (mdadm RAID1 for the OS on two SSDs is dead simple).

**Why you would not:** no bit-rot detection or repair. A silently corrupted block on one mirror member is a coin toss at read time. LVM snapshots are heavy and slow compared with CoW filesystems. Rebuilds hit URE problems on large drives. For a NAS holding precious data in 2026, this stack is a step down from ZFS or Btrfs, and the only remaining argument for it is familiarity.

**dm-integrity** (a device-mapper layer adding checksums under mdadm) and **`dm-crypt`/LUKS** for encryption can be layered in, at the cost of complexity. If you find yourself building that stack, you probably want ZFS.

## MergerFS + SnapRAID: the media-library pattern

For large libraries of *replaceable* files that change rarely — movies, TV, music, ISOs — a different approach optimises for flexibility and idle power rather than real-time redundancy.

**MergerFS** is a FUSE union filesystem: point it at any number of drives, each with its own ordinary filesystem (ext4/XFS/Btrfs), and it presents one merged directory tree. Files live whole on one drive; a policy decides where new files go (e.g., "the drive with the most free space" or "keep this directory's files together"). Drives can be any size, added or removed at any time. Losing a drive loses only what was on it; every other drive is still a plain readable filesystem. Only the drive holding the file being read spins up.

**SnapRAID** adds *scheduled* parity: run `snapraid sync` nightly and it computes parity across all drives onto one or more dedicated parity drives (one parity drive survives one failure, two survive two, up to six). It also checksums every file and can `scrub` to detect bit rot, and `fix` to restore a failed drive's contents or a corrupted file from parity. Because parity is a batch job, the array is *not* protected for changes since the last sync — irrelevant for a media library where files are added and then never modified, unacceptable for live documents or databases.

The combination gives you: mix any drives, add one at a time, spin down idle drives, survive 1–6 failures (after the last sync), detect bit rot, and never rebuild a whole array — at the cost of no real-time protection and slow-ish single-drive write speed. **OpenMediaVault** has plugins for both; **Unraid** is the commercial analogue with real-time parity; plain Debian with a `mergerfs` mount in `fstab` and a `snapraid` cron job is the DIY route. For a Tier 1–2 media server with a dozen mismatched drives, this is often the right answer — keep the precious data (photos, documents, configs) on a separate ZFS or Btrfs mirror.

```
# /etc/fstab example
/dev/disk/by-id/ata-DRIVE1-part1  /mnt/disk1  xfs   defaults  0 2
/dev/disk/by-id/ata-DRIVE2-part1  /mnt/disk2  xfs   defaults  0 2
/dev/disk/by-id/ata-PARITY-part1  /mnt/parity1 xfs  defaults  0 2
/mnt/disk*  /mnt/storage  fuse.mergerfs  cache.files=partial,dropcacheonclose=true,category.create=mfs,minfreespace=50G,fsname=mergerfs  0 0
```

## Ceph and distributed storage

**Ceph** is a distributed storage system providing block (RBD), object (S3-compatible RGW), and file (CephFS) storage across many nodes with configurable replication or erasure coding, self-healing, and no single point of failure. Proxmox integrates it: three or more nodes each contribute drives (OSDs), and VM disks on Ceph RBD can live-migrate and survive node failures. It is genuinely enterprise-grade and genuinely heavy: **three nodes minimum** (five for comfort), a dedicated 10 GbE (ideally 25 GbE) network for replication, enterprise SSDs (consumer SSDs will be destroyed by Ceph's write patterns and their lack of PLP causes latency spikes), and a real learning investment. Performance on three consumer-grade nodes over 1 GbE is poor. Run it if you want to learn Ceph or genuinely need HA storage for a Tier 3 cluster; do not run it as your NAS.

**GlusterFS** is in maintenance mode and not recommended for new deployments. **SeaweedFS**, **Garage**, and **MinIO** are object stores rather than general filesystems; see [Chapter 26](26-databases-backing-services.md). **Longhorn** and **Rook** are Kubernetes-native storage; see [Chapter 5](05-containers.md). **Proxmox ZFS replication** (scheduled `zfs send` of VM disks between nodes, with HA failover to the replica) is the pragmatic alternative to Ceph for two- and three-node home clusters — asynchronous (you lose changes since the last replication interval, which can be as short as a minute) but simple and fast.

## Sharing storage over the network

### NFS

Network File System is the Unix-native protocol: simple, fast, stateless, and the right choice for Linux-to-Linux sharing — a NAS exporting media to a Docker host, Proxmox storage backends, Kubernetes persistent volumes. NFSv4 (with `sec=sys` at home; Kerberos is available but nobody does it) has a single port (2049) and better locking than v3. Permissions are by UID/GID — the same numeric IDs must mean the same thing on both ends, or you use `all_squash`/`anonuid` to map everything to one user. `/etc/exports` on the server:

```
/mnt/tank/media  10.0.20.0/24(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)
```

Mount with `nfs4` in `fstab` or, better, as a **systemd automount** or with `x-systemd.automount,noauto` options so a NAS that is down does not hang the client's boot. Docker containers reading media over NFS is standard; **SQLite databases over NFS is corruption waiting to happen** — keep app configs on local disk.

### SMB / CIFS

Server Message Block is the Windows-native protocol (and macOS's preferred one since Apple abandoned AFP). Use it for anything a Windows or Mac client touches, and for Time Machine backups (Samba supports the `fruit` VFS module for this). **Samba** is the Linux implementation; TrueNAS, OMV, Synology, and Unraid all put a UI on it. SMB3 is encrypted-capable and multichannel-capable; performance on a modern Samba is near line rate. User-based authentication (Samba users mapped to Linux users, or Active Directory) rather than NFS's host-based trust. Guest/anonymous shares should be disabled on any network with untrusted devices. SMB from Linux clients works (`cifs-utils`) but NFS is usually a better choice between Linux machines.

### iSCSI

Block-level: the NAS exports a LUN (a zvol or a file), the client sees a raw disk and formats it itself. Used for VM disk storage (Proxmox and ESXi backends), Windows machines wanting a "local" drive on the NAS, and game libraries. The client owns the filesystem, so only one client can mount a LUN read-write at a time (unless a cluster filesystem is used). Faster than SMB for random I/O; less flexible. Over 10 GbE it is excellent; over 1 GbE it is fine for VMs and a poor fit for bulk data.

### Others

**WebDAV** (HTTP-based; Nextcloud speaks it, useful for mobile apps and across the internet); **SFTP** (SSH file transfer; universal, secure, slow-ish; fine for occasional use); **rsync daemon** (for bulk sync); **S3-compatible object storage** (Garage/MinIO/SeaweedFS — for applications that speak S3 rather than for people; [Chapter 26](26-databases-backing-services.md)); **9p/virtiofs** (for sharing host directories into VMs on Proxmox/KVM without a network protocol — virtiofs is fast and increasingly well supported).

### Which protocol

| Client | Protocol |
|---|---|
| Linux server / Docker host reading bulk data | NFS |
| Proxmox VM storage backend | NFS (simple) or iSCSI/ZFS-over-iSCSI (performance) |
| Windows PC, Mac, or phone browsing files | SMB |
| Time Machine | SMB with Samba `fruit` |
| Application needing a "local" disk | iSCSI |
| Application built for the cloud | S3 |
| Over the internet | Don't; use a VPN, or WebDAV/SFTP behind the reverse proxy, or Nextcloud/Seafile |

## Drive health and SMART

Every drive reports SMART attributes; every serious lab monitors them.

```bash
apt install smartmontools
smartctl -a /dev/sda                   # everything
smartctl -H /dev/sda                   # overall health
smartctl -t long /dev/sda              # start an extended self-test (hours)
smartctl -a /dev/nvme0                 # NVMe drives report differently (percentage_used, media_errors)
```

Attributes that predict failure (from Backblaze's and Google's published studies): **5 Reallocated Sector Count**, **187 Reported Uncorrectable**, **188 Command Timeout**, **197 Current Pending Sector**, **198 Offline Uncorrectable**. A non-zero and *rising* value on any of these means replace the drive; do not wait for it to fail. **199 UDMA CRC Errors** rising means a bad cable or port, not a bad drive. For NVMe, watch `percentage_used`, `media_and_data_integrity_errors`, and `critical_warning`. Temperature persistently over 45 °C for HDDs shortens life.

Configure `smartd` (part of smartmontools) to run short self-tests weekly and long tests monthly and email/notify on changes, or — much better — run **Scrutiny**, a web UI that collects SMART data from all your hosts, applies Backblaze's failure-rate thresholds, and shows trends and alerts ([Chapter 12](12-monitoring.md)). ZFS `zpool status` also reports read/write/checksum error counters per drive; any non-zero value deserves investigation, and a monthly scrub is what surfaces them.

**Burn-in new drives** before trusting them: a `badblocks -wsv /dev/sdX` (destructive, takes a day or two on a large drive) or at minimum a long SMART self-test. Infant mortality is real; better to discover it before the drive is in an array with data.

## Capacity planning

- **Start from your data classification** ([Chapter 1](01-planning.md)). Precious data (photos, documents, configs) is usually under 2 TB per household and grows slowly; put it on a mirror or RAIDZ2 with snapshots and off-site backup. Media is usually the bulk and grows fast; put it on RAIDZ2 or MergerFS+SnapRAID with more relaxed backup.
- **Account for the 80% rule** on ZFS: a "58 TB usable" RAIDZ2 pool is really ~46 TB of comfortable capacity.
- **Account for snapshots**: they consume space as data changes. A dataset with 30 daily snapshots of a busy directory can use 20–50% more than the live data. Media libraries snapshot cheaply (files rarely change); Docker config and databases less so.
- **Fewer, larger drives.** Per-terabyte cost is lowest around 16–24 TB in 2026; each drive is a failure point, a SATA port, and 5–8 W.
- **Plan growth for three years**, not ten. Drives get cheaper; buy what you need plus a year's growth, and plan how you will expand (add a vdev; RAIDZ expansion; replace drives with bigger ones in a mirror).
- **Leave a slot free** for a hot spare or for the replacement drive during a resilver.
- **Boot drive**: separate, small, mirrored if convenient. Never put the OS on the data pool.

## Recommendations by tier

**Tier 1 (one machine):** OS on the internal NVMe. Data on two large drives as a **ZFS or Btrfs mirror** (internal SATA bays if the machine has them; a two-bay USB 3 enclosure if not). Snapshots via sanoid or btrbk. Off-site backup of the precious datasets ([Chapter 11](11-backups.md)). If media dominates and drives are mismatched: MergerFS+SnapRAID for media, a small mirror for precious data.

**Tier 2 (dedicated NAS):** **TrueNAS** (or Debian + ZFS, or OMV) with **6–8 drives in RAIDZ2**, an NVMe boot mirror, 16–32 GB RAM. Datasets per data type; NFS to the Docker/Proxmox hosts; SMB to desktops. Sanoid/syncoid or TrueNAS replication to a second box or off-site. Scrutiny watching SMART. Monthly scrubs.

**Tier 3 (cluster):** **Proxmox ZFS replication** between nodes for VM disks (or Ceph if you have the nodes, the network, and the appetite); a **separate storage server** with RAIDZ2 pools and 10 GbE for bulk data and PBS; encrypted raw ZFS replication off-site. Special vdev on mirrored enterprise SSDs if directory listings on huge pools are slow.

## Storage checklist

- [ ] Data classified; precious data on a checksumming filesystem with redundancy.
- [ ] Every array drive is CMR ([Chapter 2](02-hardware.md)); drives from mixed batches; burned in before use.
- [ ] Layout chosen: mirror for 2–4 drives, RAIDZ2 for 5–10; no RAIDZ1 on large drives for precious data; no Btrfs RAID5/6.
- [ ] ZFS: `ashift=12`, `compression=lz4`, `atime=off`, `xattr=sa`; drives referenced by `/dev/disk/by-id`; no dedup; pool kept under 80%.
- [ ] Datasets/subvolumes per data type with appropriate `recordsize`; databases and SQLite apps on local disk, not network shares.
- [ ] Automated snapshots (sanoid/zrepl/btrbk/TrueNAS tasks) with a retention policy; replication to a second machine if possible.
- [ ] Monthly scrub scheduled; SMART monitored by smartd or Scrutiny; alerts go somewhere you will see them.
- [ ] Sharing protocol matched to client (NFS for Linux, SMB for Windows/Mac); no guest SMB shares; network mounts use automount so a down NAS does not hang clients.
- [ ] UPS communicating with the storage host so it shuts down cleanly ([Chapter 29](29-power-cost-environment.md)).
- [ ] You have read [Chapter 11](11-backups.md) and understand that none of the above is a backup.
