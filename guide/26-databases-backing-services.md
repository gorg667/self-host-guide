# Databases and Backing Services

Behind almost every application in this guide sits a database, a cache, or an object store. Most of the time you never think about them — the project's Compose file includes a `postgres` service and it just works. But when forty applications each bring their own Postgres, MariaDB, Redis, and MongoDB, you are running a small data centre's worth of backing services, and the decisions you make about them — one shared instance or many, which versions, how to back up, how to upgrade — determine whether your lab is tidy or a swamp. This chapter covers the relational databases (PostgreSQL, MariaDB/MySQL, SQLite), key-value caches (Redis and its fork Valkey), document and time-series stores (MongoDB, InfluxDB, VictoriaMetrics, TimescaleDB), object storage (Garage, MinIO, SeaweedFS, RustFS), search (Meilisearch, Typesense, OpenSearch), message queues, the no-code database tools (NocoDB, Baserow, Teable), and the admin UIs (pgAdmin, Adminer, CloudBeaver, DBeaver, phpMyAdmin) — with the operational guidance that matters: shared vs per-app, upgrades, and backups.

## The central question: shared or per-app?

**Per-app** (each Compose stack has its own `db` service) is what every project's example gives you and what most people run.

- Pros: total isolation (one app's bad query cannot hurt another); each app pins the version it was tested with; the stack is self-contained and portable; `docker compose down -v` on one app touches only its data; upgrades are per-app.
- Cons: ten Postgres containers use ~10× the baseline RAM (each idles at 30–100 MB — so 0.5–1 GB total, which is fine on most hosts); ten things to back up (but a loop over containers handles it); ten major-version upgrades to do eventually.

**Shared** (one Postgres, one MariaDB, one Redis for everything, each app with its own database/user):

- Pros: one thing to tune, monitor, back up, and upgrade; less RAM; a single pgAdmin.
- Cons: a single point of failure for everything; version conflicts (Immich wants its own extension-laden image; an app that needs Postgres 17 features while another is untested on 17); restarting the DB for maintenance takes down every app; blast radius of a mistake is total; a `depends_on` across Compose projects is awkward (external network, no health-condition ordering).

**The guide's position:** **per-app by default**, with a shared instance only for the apps that are small, numerous, and boring (a dozen tiny apps that each want a Postgres for a few tables can share one), never for Immich (its extensions), Nextcloud (its scale), or anything whose upgrade cadence you want to control separately. The RAM argument for sharing was compelling when hosts had 8 GB; with 32–64 GB it rarely is. **Redis is the exception in the other direction**: an app-specific Redis is almost always the right call because Redis is trivially light and apps use it as a cache/queue with database-number collisions if shared.

## PostgreSQL

The default relational database of the self-hosting world and the right choice whenever an app offers it. Mature, standards-compliant, extensible (pgvector for embeddings, PostGIS for geo, TimescaleDB for time-series, pg_trgm for fuzzy search), excellent documentation, and the most predictable behaviour under load. Immich, Nextcloud (recommended), Paperless, Gitea/Forgejo, Authentik, Synapse, Mastodon, Outline, Vikunja, Miniflux, Linkwarden, n8n, Umami, Firefly III, and most modern apps prefer it.

**Operational notes:**

- **Pin the major version** in the image tag (`postgres:17`, not `postgres:latest`). Postgres major upgrades are *not* automatic: a `postgres:17` data directory will not start under `postgres:18`. The upgrade is `pg_dumpall` → new container → `psql < dump`, or `pg_upgrade` (via the `pgautoupgrade/pgautoupgrade` image, which does it on start — take a backup first). Minor versions (17.1 → 17.2) upgrade in place. Do one major upgrade per app per year; it is a fifteen-minute job.
- **Alpine vs Debian images**: `postgres:17-alpine` is smaller; the Debian variant has better locale/collation compatibility. Collation changes between glibc versions can silently corrupt indexes on upgrade (`REINDEX` after a major host or image OS bump). Debian is the safer default.
- **Data on local SSD**, never NFS/SMB. `POSTGRES_INITDB_ARGS: "--data-checksums"` to detect corruption.
- **Tuning** for home scale is mostly unnecessary; if an app is slow, `shared_buffers` (25% of the RAM you give it), `work_mem`, and `effective_cache_size` via a mounted `postgresql.conf` or command flags. **PGTune** generates sane values.
- **Backups**: `pg_dumpall -U postgres | zstd` nightly (logical, portable across versions — the restore format), plus filesystem snapshots (crash-consistent). For point-in-time recovery, **pgBackRest** or **Barman** with WAL archiving — overkill for a home lab except for a self-hosted email or business database.
- **Extensions**: Immich's image (`ghcr.io/immich-app/postgres`) bundles VectorChord; `pgvector/pgvector` images bundle pgvector; `timescale/timescaledb` bundles Timescale; `postgis/postgis` bundles PostGIS. Use the pre-built image rather than compiling extensions into a shared instance.
- **Connection pooling** (**PgBouncer**) matters for apps that open many connections (Nextcloud with many PHP workers); rarely needed otherwise.

```yaml
# a well-behaved per-app Postgres
  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: app
      POSTGRES_USER: app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
      POSTGRES_INITDB_ARGS: "--data-checksums"
    volumes: ["/mnt/fast/app-db:/var/lib/postgresql/data"]
    secrets: [db_password]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 10s
      retries: 5
    # no ports: — only the app on the same network reaches it
```

## MariaDB and MySQL

**MariaDB** is the community fork of MySQL (2009, after Oracle's acquisition) and what most self-hosted apps mean when they say "MySQL": WordPress, Ghost (MySQL 8 specifically), Nextcloud (supported; Postgres preferred), Photoprism, Mealie (SQLite/Postgres actually), Bookstack, Kanboard, Matomo, Firefly III (either), Mailcow (bundled), Piwigo, and the PHP world generally. Fast for simple read-heavy workloads, familiar, and fine. **MySQL 8** (Oracle's) is required by a few apps (Ghost); the two have diverged enough since 2020 that "MariaDB is a drop-in MySQL replacement" is no longer reliably true — use what the app documents.

Operational notes mirror Postgres: pin the major (`mariadb:11`), data on local SSD, `mariadb-dump --all-databases --single-transaction | zstd` nightly (`--single-transaction` for InnoDB consistency), in-place minor upgrades, major upgrades usually work in place with `mariadb-upgrade` but back up first. The `MARIADB_AUTO_UPGRADE=1` env var runs it automatically. InnoDB is the only storage engine you should use. `utf8mb4` everywhere.

## SQLite

Not a server — a library that stores a whole database in one file. It is inside more self-hosted apps than any other database: Sonarr/Radarr/Prowlarr/Bazarr, Jellyfin, Home Assistant (default), Vaultwarden (default), Uptime Kuma, Grafana (default), Gitea/Forgejo (default), Navidrome, Audiobookshelf, Linkding, Memos, Homebox, Actual, Miniflux (no — Postgres), Paperless (optional), FreshRSS (default), Wallabag (default), Syncthing's index, and hundreds more. It is fast, zero-config, and perfectly adequate for a household's write volume.

**The three rules:**

1. **Never on a network filesystem** (NFS/SMB). File locking over the network is unreliable and corrupts databases — this is the most common cause of "my Sonarr database is malformed." Local disk only; bind-mount from local SSD even when media is on the NAS.
2. **Back up with `sqlite3 db.sqlite3 ".backup 'copy.sqlite3'"`** (or stop the app, or snapshot the filesystem), not `cp` while running — the `-wal`/`-shm` sidecar files hold uncommitted state.
3. **WAL mode** (most apps enable it) improves concurrency; the `-wal` file can grow if checkpoints do not run; it is normal to see it.

For apps that offer both, choose SQLite when the app is single-user or low-write (most of the list above) and Postgres when it is multi-user with heavy writes (Gitea with CI, Paperless with large ingests, Home Assistant with hundreds of chatty sensors — where MariaDB/Postgres for the recorder is the standard advice). **Litestream** and **LiteFS** stream SQLite changes to S3/another host for continuous backup — an elegant addition for the SQLite apps you care most about (Vaultwarden).

## Redis and Valkey

**Redis** is the in-memory key-value store used as a cache, session store, job queue, and pub/sub broker by Nextcloud, Immich, Paperless, Authentik, Synapse, Mastodon, Outline, Gitea (optional), and many more. In March 2024 Redis Ltd. changed the licence from BSD to the source-available RSALv2/SSPL; the Linux Foundation forked the last BSD version as **Valkey**, which Immich, many distributions, and much of the community adopted. In May 2025 Redis added the AGPLv3 as an option for Redis 8, becoming open source again. Both work identically for every self-hosted app; **Valkey** (`valkey/valkey:8`) is the community default for new deployments; `redis:7`/`redis:8` is fine. **KeyDB** (a multithreaded fork) and **Dragonfly** (a high-performance drop-in) exist for scale you do not have.

Operational notes: one Redis per app (they are ~5–10 MB each); persistence is optional (a cache can be rebuilt — set `--save ""` to disable RDB writes and reduce disk churn, unless the app uses Redis as a *queue* whose loss matters, in which case keep AOF/RDB and back it up); `maxmemory` with an eviction policy for caches; never expose port 6379 (no auth by default).

## Document, time-series, and search

- **MongoDB** — required by Rocket.Chat, Unifi Controller (the network application — a notorious dependency that pins old MongoDB versions), Nightscout, Cronicle, and a few others. Licence is SSPL (source-available); AVX-capable CPU required since 5.0 (an issue on some older mini PCs — use 4.4 or the `mongo:4.4` tag where the app allows). Pin the major; `mongodump` for backups. Prefer apps that use Postgres where you have the choice. **FerretDB** provides a MongoDB-compatible API over Postgres for apps with simple needs.
- **InfluxDB** — the time-series database Home Assistant users ran for long-term history (v1 and v2 differ significantly; v3 changed the model again with the OSS "Core" edition limited to 72 hours of queryable history — check current status before adopting). **VictoriaMetrics** (Prometheus-compatible, very efficient, also accepts InfluxDB line protocol) and **TimescaleDB** (Postgres extension) are the modern recommendations for HA long-term stats ([Chapter 19](19-home-automation.md)) and for Prometheus retention ([Chapter 12](12-monitoring.md)). **QuestDB** and **ClickHouse** (Plausible's backend) are the heavyweights.
- **Search engines**: **Meilisearch** (fast, typo-tolerant, easy — used by Karakeep, Immich's earlier versions, many apps; ~200 MB), **Typesense** (similar niche, also excellent), **OpenSearch/Elasticsearch** (heavy — 2–4 GB minimum; required by Mastodon's full-text search, Nextcloud's full-text search app, Graylog, Wazuh; avoid unless an app demands it), **Sonic** (tiny), **Zinc/ZincSearch** (a light Elasticsearch-API-compatible alternative), **Tantivy/Quickwit** (Rust). Postgres full-text search (`tsvector`) covers many needs without another service.
- **Vector databases** for AI: **pgvector** (in Postgres — the pragmatic choice), **Qdrant** (excellent, Rust, easy), **Chroma**, **Weaviate**, **Milvus** ([Chapter 23](23-ai-llm.md)).

## Object storage (S3-compatible)

Many modern apps can store blobs in S3 rather than on a filesystem: Immich (partial), Mastodon media, Synapse media (via plugin), Outline attachments, Ghost images, Nextcloud primary storage (possible; not recommended), Restic/Kopia backups, Ente, Plane, Docmost, and anything built cloud-first. An S3-compatible server at home lets you run them without a filesystem dependency and gives you an S3 target for backups from other machines.

- **Garage** — a lightweight, geo-distributed-capable S3 server (Rust, Deuxfleurs) designed for small self-hosters: single-binary, runs on a Pi, replicates across a few nodes with no central coordinator, ~50 MB RAM, simple config, and a tiny admin surface. **The recommendation for a home lab** that wants S3 without MinIO's weight or drama.
- **MinIO** — the long-time standard: high-performance, single or distributed, a full web console, IAM/policies, versioning, object lock, replication, and the reference for S3 compatibility. In 2025 MinIO **removed most of the management features from the community web console** (leaving essentially only an object browser) and shifted development emphasis to the paid AIStor product; the server remains AGPL and functional via `mc` (the CLI) and the API, but the direction alienated many self-hosters. Still the most compatible; less recommended for new home deployments than it was.
- **SeaweedFS** — a distributed file/object store with S3, FUSE mount, WebDAV, and filer features; very capable, more complex; good for many small files.
- **RustFS** (2025, a MinIO-API-compatible Rust server aiming to be the community MinIO successor — young, watch it), **Zenko CloudServer** (Scality's S3 implementation, single-node), **Ceph RGW** (if you run Ceph — [Chapter 6](06-storage.md)), **LocalStack** (AWS emulator — for development, not storage), **rclone serve s3** (expose any rclone remote — including a plain directory — as an S3 endpoint; a surprisingly useful shim), **Versitygw** (S3 gateway over a POSIX filesystem — put S3 in front of an existing directory tree).

For most people: **Garage** for S3-native apps and as a Restic target; or skip S3 entirely and bind-mount filesystems, which every app in this guide also supports.

## Message queues and brokers

Rarely needed directly at home — apps bundle what they need — but you will meet them: **Mosquitto** (MQTT — [Chapter 19](19-home-automation.md)), **RabbitMQ** (required by Zulip and some others; heavy Erlang), **NATS** (light, fast, used by some Go apps), **Apache Kafka/Redpanda** (only if you are learning them for work — Redpanda is the single-binary Kafka-compatible option), **Redis Streams/Lists** (what most small apps actually use as a queue), **Gearman/Beanstalkd** (legacy). Run what the app requires; do not add one speculatively.

## No-code databases and internal tools

The Airtable/Notion-database category — spreadsheet-like UIs over real databases, with forms, views, and APIs — useful for household inventories, trackers, and small business data without writing an app:

- **NocoDB** — turns any Postgres/MySQL/SQLite into an Airtable-style interface: grid/gallery/kanban/calendar/form views, links between tables, formulas, roles, webhooks, API, and the ability to connect to an *existing* database (e.g., browse your Immich or Paperless tables — carefully). Node + SQLite/Postgres. **The recommendation.**
- **Baserow** — a closer Airtable clone (Django + Postgres) with a polished UI, forms, row comments, automations/workflows (newer), and an application builder; a free tier with some premium features. Very approachable for non-technical users.
- **Teable** — a 2024 entrant built on Postgres with high performance on large tables and a clean UI; each table is a real Postgres table you can query directly. Promising.
- **Grist** — spreadsheet-database hybrid with Python formulas, access rules, and a strong data-model story; excellent for people who think in spreadsheets; self-hostable (Grist Core).
- **Appsmith**, **ToolJet**, **Budibase**, **Appwrite/Supabase/PocketBase** (backend-as-a-service — Supabase is Postgres + auth + storage + realtime as a self-hostable stack, heavy; PocketBase is a single Go binary with SQLite, auth, realtime, and an admin UI — a delightful backend for small personal apps and what Beszel is built on), **Directus** (headless CMS/data platform over any SQL database with a beautiful admin — arguably the best "admin UI for my existing database" tool), **Mathesar** (a spreadsheet-like Postgres UI with a data-modelling focus).

## Admin UIs

- **pgAdmin 4** — the official, comprehensive Postgres admin (web); heavy (~300 MB), powerful, dated UI. Every DBA knows it.
- **Adminer** — a *single PHP file* that administers Postgres, MySQL/MariaDB, SQLite, MongoDB, MS SQL, and more. Tiny, fast, ugly, indispensable. Run it as a container, LAN/VPN-only, and only when needed. The community-maintained **AdminerEvo** fork is current.
- **CloudBeaver** — the web version of **DBeaver** (the excellent desktop universal database tool): connections to everything, SQL editor, data browser, ER diagrams, users and permissions. Community Edition is free. **The recommendation for a web UI over many databases.**
- **DBeaver** (desktop), **DataGrip** (JetBrains, paid), **Beekeeper Studio** (desktop, pleasant, partly open), **TablePlus** (desktop, paid) — connecting over SSH tunnel/VPN to your databases is often better than hosting a web admin at all.
- **phpMyAdmin** — the ancient MySQL/MariaDB admin; still works; Adminer or CloudBeaver are lighter and cover more.
- **Redis**: **RedisInsight** (official, web/desktop), **Redis Commander**, **redis-cli**. **MongoDB**: **Mongo Express**, **Compass** (desktop). **SQLite**: **sqlite-web**, **DB Browser for SQLite** (desktop), **Datasette** (publish/explore SQLite as a website — wonderful for read-only exploration of app databases). **InfluxDB/Victoria**: their own UIs or Grafana.

**Do not leave admin UIs running** on a network anyone else can reach; they are a full-control surface over your data with, often, weak or no auth. Start them when needed, or forward-auth them and bind to LAN/VPN.

## Backups, once more

Databases are where file-copy backups silently fail. The pattern ([Chapter 11](11-backups.md)):

```bash
#!/usr/bin/env bash
# /opt/backups/dump-databases.sh — run nightly before the file backup
set -euo pipefail
OUT=/opt/backups/dumps; mkdir -p "$OUT"; DATE=$(date +%F)
for c in $(docker ps --format '{{.Names}}' --filter "ancestor=postgres:17" --filter "ancestor=postgres:16"); do
  docker exec "$c" pg_dumpall -U postgres | zstd -q > "$OUT/$c-$DATE.sql.zst"
done
for c in $(docker ps --format '{{.Names}}' --filter "ancestor=mariadb:11"); do
  docker exec "$c" sh -c 'mariadb-dump --all-databases --single-transaction -uroot -p"$MARIADB_ROOT_PASSWORD"' | zstd -q > "$OUT/$c-$DATE.sql.zst"
done
# Immich uses a custom image; name it explicitly
docker exec immich_postgres pg_dumpall -U postgres | zstd -q > "$OUT/immich-$DATE.sql.zst"
# SQLite apps: consistent copies
docker exec vaultwarden sqlite3 /data/db.sqlite3 ".backup '/data/db-backup.sqlite3'"
find "$OUT" -name '*.zst' -mtime +7 -delete
curl -fsS -m 10 --retry 3 https://hc.example.com/ping/<uuid> >/dev/null
```

Tools that do this for you: **docker-db-backup** (tiredofit), **Borgmatic**'s database hooks, **Backrest** pre-hooks, **Offen docker-volume-backup** (stops containers, archives volumes, uploads — a simple all-in-one), **pg_back**, per-app sidecars (**prodrigestivill/postgres-backup-local**). Restore-test quarterly: `zstdcat dump.sql.zst | docker exec -i scratch-postgres psql -U postgres`.

## Recommendations

- **Per-app databases** by default; pin majors; data on local SSD with checksums; no published ports; healthchecks so `depends_on` works.
- **Postgres** whenever the app offers it; **MariaDB** for the PHP apps that want it; **SQLite** for single-user apps — on local disk, backed up with `.backup`.
- **Valkey** (or Redis) per app; persistence off for pure caches.
- **Garage** if you want S3 at home; **pgvector** for embeddings; **VictoriaMetrics** for time-series; **Meilisearch** if an app needs search and offers it.
- **NocoDB** or **Baserow** for household data you would otherwise put in a spreadsheet; **PocketBase** for small personal apps.
- **CloudBeaver** (or Adminer on demand) for a web admin UI, LAN/VPN-only.
- **Nightly logical dumps of every database** plus filesystem snapshots; quarterly restore tests.

## Checklist

- [ ] Every database container has a pinned major version tag and its data on local SSD (not NFS); Postgres initialised with data checksums.
- [ ] No database ports published to the host/LAN; databases on isolated Compose networks with only their app.
- [ ] Nightly logical dumps (`pg_dumpall`, `mariadb-dump --single-transaction`, `sqlite3 .backup`, `mongodump`) into the file-backup path; Healthchecks ping; quarterly restore test.
- [ ] A plan (and a calendar entry) for annual Postgres/MariaDB major upgrades per app.
- [ ] Redis/Valkey instances have persistence configured deliberately (off for caches, on for queues).
- [ ] Admin UIs (pgAdmin/Adminer/CloudBeaver) not left exposed; started on demand or behind forward-auth on LAN/VPN.
- [ ] Object storage (if run) has bucket policies, versioning/object-lock on the backup bucket, and its own backup.
