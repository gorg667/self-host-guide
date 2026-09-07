# Files, Sync, and Documents

"Files" covers several distinct needs that people lump together: a **cloud drive** with a web UI, sharing links, and mobile apps (the Dropbox/Google Drive role); **device-to-device sync** without a central server (the "keep my laptop and desktop in step" role); **document management** for scanned paper and PDFs; **collaborative office editing** in the browser; and the humble **web file browser** for a directory on the NAS. Each has a best-in-class tool, and they are not the same tool. This chapter covers Nextcloud (and its contenders OpenCloud, ownCloud, Seafile, and Pydio Cells), Syncthing, Paperless-ngx, OnlyOffice and Collabora, Stirling PDF, FileBrowser and Copyparty, and the quick-share tools.

## Cloud drive platforms

### Nextcloud

The 800-pound gorilla: a PHP platform (forked from ownCloud in 2016) that started as file sync and share and grew into a full groupware suite — files with versioning, sharing (users, groups, public links with passwords/expiry, federated sharing between instances), desktop sync clients for every OS, mobile apps with auto-upload, WebDAV/CalDAV/CardDAV, and a vast **app store**: Calendar, Contacts, Mail, Talk (chat and video calls), Deck (kanban), Notes, Tasks, Photos/Memories, Office integration (Collabora or OnlyOffice), Forms, Polls, Bookmarks, News (RSS), Passwords, Maps, Cookbook, Tables, external storage mounting (SMB, S3, another Nextcloud), LDAP/SAML/OIDC login, end-to-end encryption (optional, app-level), server-side encryption, and Nextcloud **Assistant** with local or remote AI. **Nextcloud Hub** is the branding for the whole suite; **Nextcloud Files** is the core.

**Strengths:** it does everything, and doing everything in one system with one login and one sharing model is genuinely valuable for a household — a single place for documents, calendars, contacts, photos, and notes that syncs to every device. Enormous community, extensive documentation, commercial backing (Nextcloud GmbH, enterprise subscriptions fund development), a decade of maturity, OIDC/LDAP, and an app for nearly anything.

**Weaknesses — stated honestly, because Nextcloud provokes strong opinions:**

- **Performance.** PHP with a Postgres/MariaDB backend and Redis for locking and caching. On a mini PC it is *fine* for a household; it is never *fast*. Large directories, many small files, and the mobile app's initial sync can feel sluggish. Tuning (PHP-FPM workers, opcache, Redis, `cron` not AJAX for background jobs, HTTP/2, the notify_push app for instant client updates, imaginary for previews) matters and is documented but is real work.
- **Upgrade discipline.** Major versions arrive roughly twice a year; you *must* upgrade one major at a time (28 → 29 → 30, never 28 → 30); apps sometimes lag the core release and are disabled on upgrade; the occasional upgrade breaks something. Pin the major version and upgrade deliberately with a backup taken first.
- **Complexity.** The admin settings "Security & setup warnings" list is a rite of passage. Reverse proxy headers, `overwrite.cli.url`, trusted domains, and the `.well-known` redirects for CalDAV/CardDAV all need setting up.
- **Feature sprawl** means the core files experience has historically received less polish than the breadth suggests; the desktop client has had rough patches; the "Hub" direction is toward enterprise collaboration, not home file sync.
- **The AIO image** (`nextcloud/all-in-one`) bundles Nextcloud, database, Redis, Collabora, Talk, Imaginary, ClamAV, Borg backup, and a management UI into a mastercontainer that runs other containers via the Docker socket. It is the officially recommended deployment and is genuinely the smoothest way to get a *complete, tuned* Nextcloud — at the cost of an unusual architecture that fights with your own reverse proxy and Compose conventions. The **LinuxServer** or official `nextcloud:apache`/`nextcloud:fpm` images with your own Postgres and Redis are the conventional Compose path and integrate cleanly with Traefik/Caddy; expect to do the tuning yourself. **Nextcloud Community Docker** (the `nextcloud-docker` community repo) offers a middle ground.

**Pick Nextcloud if:** you want *one* platform for files, calendar, contacts, and a household of apps, and you accept PHP-scale performance and a twice-yearly upgrade ritual. It remains the most complete answer to "replace Google Drive/Workspace for my family," and for that role it is the recommendation despite its flaws.

```yaml
# nextcloud/compose.yaml (conventional path; AIO is the alternative)
services:
  nextcloud:
    image: nextcloud:31-apache            # pin the major; upgrade one at a time
    container_name: nextcloud
    restart: unless-stopped
    depends_on: [db, redis]
    environment:
      POSTGRES_HOST: db
      POSTGRES_DB: nextcloud
      POSTGRES_USER: nextcloud
      POSTGRES_PASSWORD: ${NC_DB_PASSWORD}
      REDIS_HOST: redis
      NEXTCLOUD_TRUSTED_DOMAINS: cloud.example.com
      OVERWRITEPROTOCOL: https
      OVERWRITECLIURL: https://cloud.example.com
      TRUSTED_PROXIES: 172.20.0.0/14       # your Docker address pool
      PHP_MEMORY_LIMIT: 1G
      PHP_UPLOAD_LIMIT: 16G
    volumes:
      - ./html:/var/www/html               # app code + config (small, precious)
      - /mnt/tank/nextcloud-data:/var/www/html/data   # user files (large, precious)
    networks: [proxy, default]
  cron:
    image: nextcloud:31-apache
    restart: unless-stopped
    entrypoint: /cron.sh
    depends_on: [db, redis]
    volumes_from: [nextcloud]              # same volumes
    networks: [default]
  db:
    image: postgres:17
    restart: unless-stopped
    environment:
      POSTGRES_DB: nextcloud
      POSTGRES_USER: nextcloud
      POSTGRES_PASSWORD: ${NC_DB_PASSWORD}
    volumes: ["/mnt/fast/nextcloud-db:/var/lib/postgresql/data"]
  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

Post-install: `occ db:add-missing-indices`, `occ maintenance:repair --include-expensive`, set `default_phone_region`, configure the `.well-known/caldav` and `carddav` redirects at the proxy, enable `notify_push`, and work through the admin warnings. The Nextcloud docs' "Server tuning" page is required reading.

### OpenCloud and ownCloud Infinite Scale (oCIS)

**ownCloud Infinite Scale** was ownCloud's ground-up rewrite in **Go** (2020–2023): a stateless microservice architecture, no PHP, no database (metadata in the filesystem via its "decomposedFS" or in a posixfs mode that stores files as plain files), built-in OIDC (or external), spaces (shared project drives), fast and light (~200 MB RAM). After ownCloud's acquisition by Kiteworks in 2023, most of the oCIS team left and founded **OpenCloud** (2024, Heinlein Group), forking oCIS as an Apache-licensed project with active development, a clean web UI, desktop and mobile clients (forked from ownCloud's, maturing), Collabora/OnlyOffice integration, full-text search via Tika, and a roadmap focused on files-and-collaboration rather than groupware sprawl.

**Strengths:** dramatically faster and lighter than Nextcloud; simple deployment; modern architecture; posixfs mode means your files are real files on disk that other tools can see; strong OIDC-first identity. **Weaknesses:** young (OpenCloud 1.0 in early 2025); far fewer apps — this is files, sharing, and office, not calendars/contacts/chat/RSS; mobile and desktop clients are less mature than Nextcloud's; a smaller community. **Pick it if:** you want a fast, focused Dropbox replacement without Nextcloud's weight, and you handle calendar/contacts elsewhere (Radicale/Baikal — [Chapter 18](18-notes-productivity.md)). OpenCloud is the project to watch in this category.

### Seafile

A file sync and share system (C server core, Python web) with an unusual design: files are stored in a **content-addressed, chunked, deduplicated repository** ("libraries"), not as plain files on disk. This makes sync *extremely* fast and efficient — Seafile's sync client is widely regarded as the best in the category, handling huge trees and large files gracefully — and enables per-library client-side encryption, file versioning, and snapshots. Web UI, mobile apps, desktop sync and drive (virtual drive) clients, sharing, WebDAV, Markdown editor, OnlyOffice/Collabora integration, LDAP/OIDC (Pro).

**Weaknesses:** the storage model means your files are *not* browsable on the server filesystem — you must use Seafile's tools (or FUSE mount) to get at them, which is a lock-in and disaster-recovery concern (`seaf-fsck` and the FUSE export exist and work, but it is not `ls`); the **Community Edition** lacks some features (full-text search, audit, some auth options) reserved for the paid **Pro** (free for up to 3 users); development is by a small company (Seafile Ltd, China/Germany) with a less transparent roadmap. **Pick it if:** sync speed and reliability are paramount and you are comfortable with the opaque storage model.

### Pydio Cells

A Go-based enterprise file platform with a polished UI, workspaces, fine-grained ACLs, workflows, and OIDC. Capable but heavy, enterprise-oriented, and with a small self-hosting community. Rarely the right choice at home.

### Others

**FileRun** (PHP, single-user free tier, excellent UI over an existing folder tree — think "Nextcloud Files for a directory you already have"; paid for multi-user), **Filestash** (a web client for any backend: SFTP, S3, WebDAV, FTP, Git; not a sync platform), **Cloudreve**, **Kodbox**, **Sandstorm** (a different model — sandboxed apps per document; largely dormant).

### Comparison

| | Nextcloud | OpenCloud | Seafile | FileRun |
|---|---|---|---|---|
| Language / weight | PHP; 1–2 GB RAM with DB + Redis | Go; ~200–400 MB | C + Python; ~500 MB | PHP; ~300 MB |
| Files on disk as plain files | **Yes** | Yes (posixfs) | **No** (chunked repo) | **Yes** (indexes existing tree) |
| Desktop sync client | Good | Maturing | **Excellent** | Via Nextcloud client (compatible) |
| Mobile apps | Good, auto-upload | Maturing | Good | Via Nextcloud app |
| Sharing (links, users, federated) | **Most complete** | Good | Good | Good |
| Calendar/contacts/chat/apps | **Yes (huge app store)** | No | No | No |
| Office integration | Collabora, OnlyOffice | Collabora, OnlyOffice | OnlyOffice, Collabora | OnlyOffice |
| Photos | Memories app (good) | Basic | Basic | Good gallery |
| OIDC/LDAP | Yes | **OIDC-first** | LDAP; OIDC in Pro | Paid |
| Multi-user free | Yes | Yes | Yes (CE) / Pro ≤3 free | **No** (single user free) |
| Upgrade burden | High (majors twice/yr, one at a time) | Low | Medium | Low |
| Licence | AGPL | Apache 2.0 | AGPL (server) / proprietary Pro | Proprietary (free tier) |
| Best for | Full household suite | Fast files-only | Sync performance | Web UI over an existing folder |
