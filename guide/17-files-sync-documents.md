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

## Peer-to-peer sync: Syncthing

**Syncthing** is a different thing entirely and one of the best pieces of software in self-hosting. It synchronises folders **directly between your devices** — laptop, desktop, phone, NAS — with no central server required, over an encrypted protocol, using a global discovery and relay network (which you can self-host) to find peers behind NAT. Every device holds a full copy. Conflicts produce `.sync-conflict` files rather than silent overwrites. **File versioning** (trash-can, simple, staggered, external) on any device keeps old copies. Send-only, receive-only, and send-receive folder modes; ignore patterns; per-folder rescan intervals with inotify; bandwidth limits; a web UI per device; Android app (the official one was discontinued from the Play Store in late 2024 — **Syncthing-Fork** on F-Droid/Play is the maintained one); iOS via **Möbius Sync** (third-party, paid).

**Where it fits:** keeping a documents folder identical on three computers; pushing phone photos to the NAS (as a Syncthing folder that Immich then watches as an external library, or that PhotoPrism imports); syncing an **Obsidian** or **KeePassXC** database across devices ([Chapter 18](18-notes-productivity.md), [Chapter 21](21-passwords-secrets.md)); replicating a folder to a friend's machine as a poor man's off-site copy (with versioning on their end). Include the NAS as an always-on peer so devices that are never online simultaneously still converge.

**Where it does not:** it is *sync*, not *backup* — a deletion (or ransomware encryption) propagates everywhere; versioning mitigates but does not replace [Chapter 11](11-backups.md). No web-based file access or sharing links (it moves files; it does not serve them). No selective sync on mobile beyond folder granularity. Many small files or huge trees are fine; very large single files that change constantly (VM images, databases) are not a good fit.

**Pick it:** always, for something. Almost every self-hoster runs Syncthing for at least one folder. It is complementary to Nextcloud, not a competitor — Nextcloud for sharing and web access, Syncthing for device convergence.

## Document management: Paperless-ngx

**Paperless-ngx** turns paper into a searchable archive: scan (or photograph, or email, or drop into a consume folder) a document; it OCRs it (Tesseract, any language), extracts the date, auto-assigns a **correspondent**, **document type**, and **tags** using machine learning that trains on your corrections, stores the original plus an archived PDF/A, and makes everything full-text searchable. Custom fields, workflows (rules that fire on consumption or tagging), storage paths (organise files on disk by year/correspondent), sharing links, a solid mobile-friendly web UI, the **Paperless Mobile** app (Android/iOS) and **Swift Paperless** (iOS) for scanning directly, mail fetching (poll an inbox for attachments), OIDC login, permissions per user/group, and an API. Python/Django with Postgres (or SQLite) and Redis; ~500 MB–1 GB RAM; Tika + Gotenberg containers optional for Office documents.

It is the standard for a reason: after a month of use it *learns* — new bank statements get tagged and filed without intervention. Feed it every letter, bill, receipt, contract, and manual; throw the paper away (where legally permitted). Pair with a document scanner that can save to a network folder or email (Brother ADS series, Fujitsu/Ricoh ScanSnap via a computer, or the phone app).

Alternatives: **Papra** (2025, a lighter, simpler take on document archiving), **Docspell** (similar goals, Scala/Elm, smaller community), **Mayan EDMS** (heavyweight enterprise DMS), **Teedy** (Java, lighter), **Paperless-AI** and **Paperless-GPT** (companions that use an LLM — local via Ollama or remote — to title, tag, and summarise documents; genuinely useful add-ons), **Stirling PDF** (below) for manipulation, **Nextcloud** with full-text search for people who want documents in their drive rather than a DMS. **Paperless-ngx** remains the recommendation.

```yaml
services:
  paperless:
    image: ghcr.io/paperless-ngx/paperless-ngx:latest
    container_name: paperless
    restart: unless-stopped
    depends_on: [broker, db]
    environment:
      PAPERLESS_REDIS: redis://broker:6379
      PAPERLESS_DBHOST: db
      PAPERLESS_DBPASS: ${PAPERLESS_DB_PASSWORD}
      PAPERLESS_URL: https://paperless.example.com
      PAPERLESS_SECRET_KEY: ${PAPERLESS_SECRET}
      PAPERLESS_OCR_LANGUAGE: eng
      PAPERLESS_OCR_LANGUAGES: deu fra          # extra languages to install
      PAPERLESS_TIME_ZONE: Europe/London
      PAPERLESS_FILENAME_FORMAT: "{{ created_year }}/{{ correspondent }}/{{ title }}"
      USERMAP_UID: "1000"
      USERMAP_GID: "1000"
    volumes:
      - ./data:/usr/src/paperless/data             # index, ML model, SQLite if used (precious)
      - /mnt/tank/documents/paperless/media:/usr/src/paperless/media   # originals + archive (precious)
      - /mnt/tank/documents/paperless/export:/usr/src/paperless/export
      - /mnt/tank/documents/paperless/consume:/usr/src/paperless/consume  # drop scans here
    networks: [proxy, default]
  broker:
    image: redis:7-alpine
    restart: unless-stopped
  db:
    image: postgres:17
    restart: unless-stopped
    environment: { POSTGRES_DB: paperless, POSTGRES_USER: paperless, POSTGRES_PASSWORD: "${PAPERLESS_DB_PASSWORD}" }
    volumes: ["/mnt/fast/paperless-db:/var/lib/postgresql/data"]
```

Back up `media/` (the documents) *and* the database *and* `data/`; the `document_exporter` management command produces a complete, restorable export and is the recommended backup format — run it nightly to a folder that your file backup then picks up.

## PDF tooling: Stirling PDF

**Stirling PDF** is a web app with ~50 PDF operations — merge, split, rotate, compress, OCR, convert to/from images and Office formats, sign, redact, add watermarks, remove pages, repair, flatten, compare, extract images, and more — running locally so nothing is uploaded to a random website. Java, ~500 MB with all features (a slimmer image exists), optional login and OIDC. Every household needs this at some point; it replaces a dozen sketchy online tools. **Gotenberg** (an API for document → PDF conversion, used by Paperless) and **BentoPDF** are alternatives with different focuses.

## Office suites in the browser

For collaborative editing of documents, spreadsheets, and presentations inside Nextcloud/OpenCloud/Seafile:

**Collabora Online** — LibreOffice in the browser (the CODE container is the free "Development Edition," fully functional with a connection-count nag). Best fidelity with ODF and good with Office formats; the interface is LibreOffice's, which some find dated; heavier (~1–2 GB RAM). Integrates natively with Nextcloud via the "Nextcloud Office" app, and is what AIO bundles.

**OnlyOffice Docs** — a Microsoft-Office-like interface with excellent DOCX/XLSX/PPTX fidelity (it uses OOXML natively), real-time co-editing, and a Community Edition limited to 20 simultaneous connections (fine at home). Integrates with Nextcloud, OpenCloud, Seafile, and standalone. Lighter than Collabora; the licensing (AGPL for Docs; some features Enterprise-only) and the company's history draw occasional criticism. **Pick OnlyOffice if** your household lives in .docx/.xlsx; **Collabora if** you prefer ODF and LibreOffice.

**CryptPad** — end-to-end encrypted collaborative documents, spreadsheets, kanban, forms, and whiteboards, with the server never seeing plaintext. A separate platform (not a Nextcloud plugin) with its own accounts and sharing. The right choice for privacy-sensitive collaboration with people outside the household; less integrated.

**Etherpad** and **HedgeDoc** are real-time collaborative *text* editors (plain and Markdown respectively) — lightweight, instant, no accounts needed for a shared pad; see [Chapter 18](18-notes-productivity.md).

## Web file browsers and quick sharing

Sometimes you just want a web UI on a directory.

- **FileBrowser** — a single Go binary that serves a folder tree with upload/download/edit/preview, multiple users with scoped roots and permissions, and share links. Light, fast, done. The **FileBrowser Quantum** fork adds indexing/search and OIDC. The right tool for "give the family a web view of the NAS share."
- **Copyparty** — a remarkable single-file Python server: HTTP(S) file server with upload (resumable, deduplicated), WebDAV, FTP, SMB, TFTP, an audio player with transcoding, thumbnails, search, per-folder permissions, and zero dependencies. Runs on anything. Extremely fast at accepting uploads from many devices. The Swiss Army knife.
- **Sharry**, **Pingvin Share**, **Send** (the community fork of Firefox Send), **Gokapi**, **PsiTransfer**, **Dumbdrop**, **Erugo** — "upload a file, get an expiring link" tools for sending large files to people. Pingvin Share and Sharry are the most polished; Send offers E2EE.
- **PairDrop / Snapdrop** — AirDrop-in-a-browser for devices on the same network; self-hostable; wonderful for phone-to-laptop transfers.
- **SFTPGo** — a full-featured SFTP/FTPS/WebDAV/HTTP file server with virtual users, quotas, S3/Azure/GCS backends, a web admin and client UI, and event hooks. The professional answer when you need to give external parties SFTP access.
- **Dufs**, **miniserve**, **Caddy `file_server browse`** — one-liners for a read-only directory listing.
- **SMB/NFS** remain the right answer for LAN access from desktops ([Chapter 6](06-storage.md)); web browsers are for phones, remote access, and sharing.

## Recommendations

- **A household drive with web UI, sharing, and mobile apps:** Nextcloud (accept the weight, tune it, pin the major). If you only need files and want speed: **OpenCloud**.
- **Device convergence:** Syncthing, with the NAS as an always-on peer and versioning on.
- **Paper and PDFs:** Paperless-ngx (+ Paperless-AI if you run Ollama); Stirling PDF alongside.
- **Browser office editing:** OnlyOffice for Microsoft-format households, Collabora for LibreOffice/ODF; CryptPad for E2EE collaboration with outsiders.
- **A web view on a directory:** FileBrowser or Copyparty. **Sending big files to people:** Pingvin Share.
- Keep the *canonical* copy of files on the NAS filesystem where every tool (and every backup) can see them; let Nextcloud/Syncthing/Paperless be views and workflows on top, not opaque vaults — which is the one real argument against Seafile.

## Checklist

- [ ] Files live on redundant storage as plain files; the platform's data directory and database are on local disk and backed up ([Chapter 11](11-backups.md)).
- [ ] Nextcloud (if used): major pinned; Redis and cron configured; admin warnings cleared; `.well-known` redirects at the proxy; mobile auto-upload tested.
- [ ] Syncthing: NAS as always-on peer; versioning on for important folders; device IDs verified out-of-band; discovery/relay settings understood.
- [ ] Paperless: consume folder wired to the scanner; `document_exporter` nightly; media + DB + data in backup.
- [ ] Office suite reachable by the drive platform over the internal network with the correct public URL configured.
- [ ] Share links and public file tools behind the reverse proxy; upload limits raised at the proxy for large files.
- [ ] Nothing that stores SQLite (Syncthing index, Paperless SQLite mode, FileBrowser DB) lives on NFS.
