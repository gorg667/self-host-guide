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
