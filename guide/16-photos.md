# Photos: Replacing Google Photos and iCloud

Photos are the data people care about most and the data most people have handed to a cloud provider without a second thought. For a decade the honest self-hosting advice was "there is no good replacement for Google Photos — keep using it." That changed. **Immich** has reached the point where, for a household willing to run a server, it is a genuine replacement: automatic phone backup, a fast timeline, face recognition, object and scene search, shared albums, and mobile apps that feel finished. This chapter reviews Immich in depth, then the alternatives — PhotoPrism, Nextcloud Memories, Ente, Lychee, LibrePhotos, Photoview, Piwigo, and Damselfly — and covers the operational realities: storage layout, the migration from Google/Apple, backup (photos are the most irreplaceable thing you own), and sharing with people outside your household.

## What a photo server must do

The bar Google Photos set, which any replacement must clear for a normal household to adopt it:

1. **Automatic background upload from phones**, reliably, over Wi-Fi and optionally cellular, including videos and Live Photos/motion photos, without the app being opened.
2. **A fast, infinite-scroll timeline** of tens of thousands of items, with a scrubber by year/month.
3. **Search that works**: by person (face recognition), by place (GPS/reverse geocoding), by content ("dog on beach," "birthday cake"), by date, by camera.
4. **Sharing**: albums shared with other users on the server; public links for people without accounts; partner sharing (see each other's libraries).
5. **Multi-user**, so each family member has a private library and shared albums.
6. **RAW support** (at least previews), HEIC/HEVC, 360°, and video playback with transcoding for compatibility.
7. **Memories/"on this day,"** duplicate detection, trash with retention, archive/hide, favourites.
8. **Getting the data out** in a normal folder structure with metadata intact — the anti-lock-in guarantee.

Anything that does 1–5 well is viable. Only one currently does all eight well.

## Immich

Immich (MIT, started 2022 by Alex Tran, now developed by a core team funded via FUTO since 2024, with a large contributor base) is a high-performance photo and video management server built explicitly to replace Google Photos. Architecture: a **server** (Node.js API and background jobs), a **machine-learning** container (CLIP for semantic search, face detection and recognition, optional on GPU), **PostgreSQL with the VectorChord/pgvecto.rs extension** for vector search, and **Valkey/Redis** for job queues. Web app, plus native **iOS and Android apps** (Flutter) with background backup.

**What it does exceptionally well:**

- **Mobile backup** that works like Google Photos: select albums to back up, it uploads in the background (with the usual iOS background-execution caveats, mitigated well), shows what is and is not backed up, handles Live Photos and motion photos, and can free up phone storage of backed-up items.
- **Timeline performance** on libraries of 100k+ items — smooth scrolling, instant year jumps.
- **Search**: CLIP-based natural-language search ("red car at sunset") that genuinely works; face recognition with naming, merging, and hiding; map view with clustering; metadata search; "smart search" across everything. All local, no cloud API.
- **Sharing**: albums with other users (view or edit), public links with optional password and expiry, **partner sharing** (your partner sees your timeline in theirs), and shared album activity (comments, likes).
- **External libraries**: point Immich at an existing folder tree (your 20 years of organised photos) read-only; it indexes without moving anything. Uploads from phones go to Immich's own managed storage. This is how most people migrate.
- **Storage template**: uploaded files are stored under a configurable path template (`{{y}}/{{MM}}/{{filename}}`) — human-readable folders, not opaque blobs — with original files untouched and sidecar XMP written.
- **Duplicate detection**, trash, archive, stacking (RAW+JPEG, bursts), memories, people, places, tags (since 2024), folders view, slideshow, 360° viewer, video transcoding with hardware acceleration (QSV, NVENC, VAAPI, RKMPP), HEIC/RAW preview generation, reverse geocoding (offline, bundled data).
- **Administration**: per-user quotas, OIDC login (with auto-registration and group-to-admin mapping), library and job management, a CLI for bulk upload (`immich upload`), a well-documented REST API, and **immich-go** (a community tool for bulk import from Google Takeout with metadata reconciliation — essential for migrations).

**What to know before running it:**

- **Resource needs** are the highest in this chapter: ~2–4 GB RAM for the stack with ML running (the ML container alone is 1–2 GB), several GB of disk for ML models, and real CPU during initial indexing of a large library (days for 100k items on a small CPU; hours with a GPU — Immich's ML supports CUDA, ROCm, OpenVINO, ARM NN, and RKNN). After indexing, idle is modest. ML can run on a *different* machine (point the server at it) — a GPU box that sleeps, or a Mac.
- **Update discipline.** Until the 2.0 release (late 2025), Immich carried a "breaking changes may occur" warning and lived up to it — releases occasionally required manual steps (database migrations, Compose changes, ML model re-downloads). **Read the release notes before every update** and pin the version tag (`ghcr.io/immich-app/immich-server:v2.x.y`) rather than `release`/`latest`. Post-2.0 stability is much improved, but the habit remains wise. Watch the GitHub releases page or subscribe via RSS.
- **PostgreSQL with a vector extension** means you cannot casually swap in your existing shared Postgres — the recommended image (`ghcr.io/immich-app/postgres`, based on `tensorchord/pgvecto-rs` / VectorChord) is specific. Run the dedicated one.
- **Backups**: the originals are plain files in the upload directory (back them up like any files); the database holds *everything else* — albums, faces, people names, favourites, sharing — and must be dumped consistently (`pg_dumpall` via a hook; Immich also has a built-in nightly DB dump to `backups/` in the upload location since 1.9x). Losing the DB with the files intact means re-indexing and losing curation. See [Chapter 11](11-backups.md).
- **Mobile apps and remote access**: the apps need to reach the server URL from anywhere. A mesh VPN with split DNS is the clean answer; exposing Immich publicly is done by many people (behind a proxy with CrowdSec and Immich's own auth) but is a meaningful exposure of your most private data. Cloudflare Tunnel's 100 MB upload limit breaks video backup; Pangolin or a direct proxy does not.
- **Not a photo editor** or a DAM. Basic edits (crop/rotate) exist; anything more means Darktable/digiKam on your originals.

```yaml
# immich/compose.yaml — based on the official file; pin versions
name: immich
services:
  immich-server:
    image: ghcr.io/immich-app/immich-server:v2.0.1
    container_name: immich_server
    restart: unless-stopped
    volumes:
      - /mnt/tank/photos/immich:/usr/src/app/upload      # managed uploads (precious!)
      - /mnt/tank/photos/archive:/mnt/archive:ro         # external library of existing photos
      - /etc/localtime:/etc/localtime:ro
    env_file: [.env]
    devices: ["/dev/dri:/dev/dri"]                       # hardware video transcoding (Intel/AMD)
    depends_on: [redis, database]
    networks: [proxy, default]
    healthcheck: { disable: false }
  immich-machine-learning:
    image: ghcr.io/immich-app/immich-machine-learning:v2.0.1   # -cuda / -rocm / -openvino / -armnn variants
    container_name: immich_machine_learning
    restart: unless-stopped
    volumes: ["model-cache:/cache"]
    env_file: [.env]
  redis:
    image: docker.io/valkey/valkey:8-bookworm
    container_name: immich_redis
    restart: unless-stopped
    healthcheck: { test: redis-cli ping || exit 1 }
  database:
    image: ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0
    container_name: immich_postgres
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_DB: ${DB_DATABASE_NAME}
      POSTGRES_INITDB_ARGS: '--data-checksums'
    volumes: ["/mnt/fast/immich-db:/var/lib/postgresql/data"]   # local SSD, not NFS
volumes:
  model-cache: {}
networks:
  proxy: { external: true }
```

**Verdict:** the recommendation for almost everyone. It is the first self-hosted photo solution that non-technical family members adopt without complaint.

## The alternatives

### PhotoPrism

The most mature alternative (Go + TensorFlow, since 2018): a polished web UI, AI-based labelling (object/scene classification, not natural-language CLIP search), face recognition, places with an interactive map, RAW conversion, live photos, video, duplicates, albums, sharing links, and excellent metadata handling (it is meticulous about EXIF/XMP and sidecars). It indexes an existing folder tree in place — PhotoPrism is fundamentally a **library indexer**, which makes it ideal for a curated archive you manage yourself. Single container + MariaDB (or SQLite), ~1–2 GB RAM, CPU-heavy on indexing (TensorFlow, no GPU acceleration for classification in the free edition).

**The trade-offs:** no first-party mobile app — mobile backup is via **PhotoSync** (paid, excellent, third-party) or a WebDAV/Syncthing/Nextcloud folder that PhotoPrism watches; this is the decisive gap versus Immich for households. Multi-user requires **PhotoPrism Plus** (a paid membership, from ~EUR 5/month — the Community Edition is single-user with a "guest/viewer" role only). Search is label-based, not semantic. Development pace is steady but slower than Immich's.

**Pick it if:** you are a single photographer with a large curated archive, you prefer indexing-in-place over an upload model, and metadata fidelity matters more than mobile backup.

### Nextcloud Memories (and Nextcloud Photos)

If you already run Nextcloud ([Chapter 17](17-files-sync-documents.md)), the **Memories** app (by Varun Patil) turns it into a very capable photo timeline: fast scrolling (it maintains its own index), albums, face recognition (via the **Recognize** app — runs on CPU, slowly, or on a GPU), places/map, tags, video with hardware transcoding (via **go-vod**), RAW previews, "on this day," sharing via Nextcloud's sharing model, and — because it is Nextcloud — the **Nextcloud mobile app's auto-upload** handles phone backup. No additional server. It is a *dramatically* better experience than the stock Nextcloud Photos app.

**The trade-offs:** performance and features trail Immich (search is tag-based, face recognition via Recognize is slower and less accurate, the mobile experience is Nextcloud's generic file app rather than a photos app — Memories has a PWA that works well); tied to Nextcloud's PHP performance and upgrade cadence. **Pick it if** Nextcloud is already your files platform and you want photos without a second system.

### Ente Photos

**Ente** is the privacy-maximalist option: **end-to-end encrypted** photo storage where the server never sees your photos in plaintext, with face recognition and semantic search running *on the client device*. Open source (AGPL, server and clients), excellent mobile and desktop apps, family plans, sharing, and — since 2024 — a documented **self-hosting** path for the server (Go + Postgres + S3-compatible object storage such as MinIO/Garage). It is a hosted commercial service first, with self-hosting as a supported option.

**The trade-offs:** E2EE means the *server* cannot do ML — search and faces work per device, and heavy processing happens on your phone/laptop; self-hosting requires object storage; the self-hosted setup is less turnkey than Immich's Compose file. **Pick it if** end-to-end encryption is non-negotiable — e.g., you want to host it on a VPS you do not fully trust.

### Lychee

A photo *gallery* rather than a Google Photos replacement: elegant album-based presentation, public and password-protected albums, per-user support, EXIF display, basic tagging, and a clean upload UI. PHP/Laravel, light. Perfect for a photographer sharing curated albums with clients or family; not for backing up 40,000 phone snapshots.

### LibrePhotos

A fork of the abandoned Ownphotos: face recognition, object detection, semantic search, timeline, places, events, multi-user, and indexing of existing folders. Python/Django with a heavy ML dependency set (~4+ GB RAM). Ambitious feature list, rougher execution, smaller community than Immich or PhotoPrism; development has been slow. Worth a look only if the others do not fit.

### Photoview, Piwigo, Damselfly, HomeGallery, Pigallery2

- **Photoview** — a fast, minimal, read-only gallery for an existing folder tree with face recognition and a map. Very low resources. Good for "browse my archive on the TV."
- **Piwigo** — the veteran (since 2002) PHP gallery with a huge plugin ecosystem and a Piwigo-hosted option; dated but complete; good for very large organised galleries.
- **Damselfly** — a .NET DAM/organiser oriented at photographers: tagging, keyword workflow, Lightroom-like exports, AI tagging, in-place indexing.
- **HomeGallery** — static-site-generator-style gallery with reverse image search; interesting and light.
- **Pigallery2** — a fast directory-based gallery with a map, faces via metadata, and video, running on a Pi.
- **Synology Photos / QNAP QuMagie** — the commercial NAS apps; Synology Photos is genuinely decent and has a mobile app with backup; it is why some people buy a Synology. Locked to the hardware.

### Comparison

| | Immich | PhotoPrism | Nextcloud Memories | Ente (self-hosted) | Lychee | LibrePhotos |
|---|---|---|---|---|---|---|
| Mobile auto-backup | **Native apps, excellent** | Third-party (PhotoSync) | Nextcloud app | **Native apps, excellent** | No | No |
| Timeline performance | **Excellent** | Good | Good | Good | n/a (albums) | Fair |
| Face recognition | **Yes (server)** | Yes (server) | Yes (Recognize) | Yes (on-device) | No | Yes |
| Semantic search | **Yes (CLIP)** | Labels only | Tags only | Yes (on-device) | No | Yes |
| Multi-user | **Free** | Paid (Plus) | Yes (Nextcloud users) | Yes | Yes | Yes |
| Partner sharing | **Yes** | No | Via NC sharing | Family plans | No | No |
| Index existing folders in place | Yes (external libraries) | **Yes (primary model)** | Yes (it's your NC files) | No (upload model) | Upload | Yes |
| E2E encryption | No | No | No (server-side enc. optional) | **Yes** | No | No |
| Hardware ML/transcode | Yes (many) | Transcode yes; ML no | Transcode yes | n/a | n/a | Partial |
| RAM (typical) | 2–4 GB | 1–2 GB | +0.5–1 GB on Nextcloud | 1–2 GB + object store | 200 MB | 4+ GB |
| Licence | MIT | AGPL (CE) + paid Plus | AGPL | AGPL | MIT | MIT |
| Best for | Households replacing Google Photos | Solo photographers with archives | Existing Nextcloud users | E2EE purists | Curated public galleries | (Niche) |

## Storage layout and workflow

A pattern that serves both "phone dump" and "curated archive" without conflict:

```
/mnt/tank/photos/
├── immich/            # Immich-managed uploads (phones, web). Storage template: {{y}}/{{y}}-{{MM}}/{{filename}}
│   ├── library/       #   originals, human-readable
│   ├── thumbs/        #   regenerable
│   ├── encoded-video/ #   regenerable
│   └── backups/       #   Immich's own nightly DB dumps
└── archive/           # Your curated, pre-existing collection, read-only external library in Immich
    ├── 2009/
    ├── 2010 Wedding/
    └── ...
```

- Everything under `photos/` is on redundant storage with snapshots and is **irreplaceable-class** for backup purposes. `thumbs/` and `encoded-video/` can be excluded from off-site backup (regenerable) to save space.
- The database lives on local SSD (`/mnt/fast/immich-db`) — never on NFS — and is dumped nightly to `photos/immich/backups/` (which *is* backed up).
- RAW workflows: shoot → import to `archive/YYYY/...` with your DAM (Darktable, digiKam, Lightroom) → Immich indexes the external library and shows RAW previews; edits/exports land as JPEGs alongside. Immich stacks RAW+JPEG pairs.
- **Do not point two indexers at the same writable directory** (e.g., Immich uploads *and* PhotoPrism import) unless one is read-only; sidecar and rename fights ensue.

## Migrating from Google Photos and iCloud

**From Google Photos:** request a **Google Takeout** export of Photos (it arrives as many multi-GB zips with photos alongside `.json` metadata files — and, infamously, with EXIF dates sometimes stripped or wrong). Use **immich-go** (`immich-go upload from-google-photos --server ... --key ... *.zip`) which reads the JSON sidecars to restore dates, GPS, albums, favourites, and archived state, deduplicates, and uploads straight from the zips. Do a dry run first. For other targets, **google-photos-takeout-helper** / **GPTH** fixes the metadata into the files themselves so any tool can index them. Budget a weekend for a large library; the upload itself is the slow part.

**From iCloud:** on a Mac, the Photos app can **Export Unmodified Originals** with IPTC/XMP sidecars; or use **icloudpd** (iCloud Photos Downloader, a Docker container that pulls your entire iCloud library incrementally and can keep running to sync new items — useful during a transition). Live Photos come as HEIC+MOV pairs; Immich pairs them. On the phone, install the Immich app and enable backup of the Camera Roll going forward.

**Going forward:** run both for a month. Verify counts match (Immich shows library statistics). Check a random sample of old photos for correct dates and locations. Then turn off Google/iCloud backup on the phones, keep the cloud copy for another six months as a safety net, and only then delete. **Keep the Takeout zips** in cold storage forever; they are a valid backup in themselves.

## Sharing outside the household

- **Immich shared links** — public URL, optional password and expiry, view or allow-upload (great for collecting event photos from guests). The link goes through your reverse proxy; it works only if Immich is reachable from the internet (exposed or via Cloudflare Tunnel/Pangolin for that hostname).
- **Immich partner sharing** for a spouse; **shared albums** for family members with accounts. Create accounts for grandparents and install the app on their phone with the VPN — they get a live feed of grandchildren.
- **Lychee** or **Photoview** in front of a curated export for public galleries, keeping Immich itself private.
- **Nextcloud public shares** if using Memories.
- **Ente's sharing** works even self-hosted, with E2EE preserved.

## Backup: the non-negotiable part

Photos are the single most irreplaceable dataset most people own. Apply the full [Chapter 11](11-backups.md) treatment without compromise:

- Redundant local storage (mirror or RAIDZ2) with snapshots.
- Nightly off-site encrypted backup of originals **and** the nightly DB dump (Restic/Borg/Kopia to B2/Hetzner/a friend's box).
- An **immutable or offline copy** — photos are what ransomware is aimed at.
- Phones keep local copies until the server backup is confirmed (do not "free up space" on the phone until the off-site job has run).
- **Test a restore quarterly**: restore a month's folder and the DB to a scratch Immich instance and confirm faces, albums, and dates survive.
- Keep the Google Takeout / iCloud export zips as a permanent cold copy.

## Recommendation

**Immich**, on its own Postgres, with the ML container (on a GPU if you have one, otherwise patience for the first index), external library for the archive, storage template on, version pinned, release notes read before updates, database dumped nightly, everything under `photos/` backed up off-site with an immutable copy. Mobile apps via a mesh VPN with split DNS; public share links via a single exposed hostname if you need them.

**PhotoPrism** for the solo photographer with a curated archive; **Nextcloud Memories** for the Nextcloud household; **Ente** for E2EE; **Lychee** for a public gallery.

## Checklist

- [ ] Photo storage on redundant, snapshotted storage; classified irreplaceable.
- [ ] Immich (or chosen server) running with database on local SSD, version pinned.
- [ ] Phones backing up automatically; verified after 48 hours that new photos appear and old ones are complete.
- [ ] External library for the existing archive indexed; a random sample checked for correct dates/places.
- [ ] Face recognition and smart search jobs completed; people named.
- [ ] Off-site encrypted backup of originals + DB dump nightly; immutable copy; restore tested.
- [ ] Takeout/iCloud exports retained in cold storage.
- [ ] Remote access via VPN (or a deliberately exposed, protected hostname); Cloudflare Tunnel upload limit understood if used.
- [ ] Cloud photo backup disabled on phones only after a month of parallel running and a verified count.
