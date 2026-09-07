# Notes, Knowledge, and Personal Productivity

This is the most crowded and most personal category in self-hosting. Notes apps are a matter of taste and workflow; what one person finds indispensable another finds unusable. The chapter is organised by *need* rather than by tool: personal notes (Obsidian with self-hosted sync, Joplin, Trilium, SilverBullet, Memos, Notesnook), team and household knowledge bases and wikis (Outline, BookStack, Wiki.js, DokuWiki, Docmost, AFFiNE, AppFlowy), collaborative editors (HedgeDoc, Etherpad), tasks and project boards (Vikunja, Planka, Focalboard, Kanboard), calendars and contacts (Radicale, Baikal, Nextcloud), bookmarks and read-later (Linkwarden, Linkding, Karakeep, Wallabag, Readeck), and RSS readers (FreshRSS, Miniflux, Tiny Tiny RSS, NetNewsWire-compatible servers). Each section ends with a recommendation.

## Personal notes

### Obsidian + self-hosted sync

**Obsidian** is not self-hosted software — it is a free (for personal use), closed-source, local-first Markdown editor with a graph view, backlinks, canvas, and a plugin ecosystem of thousands. Your notes are plain `.md` files in a folder ("vault"). What you self-host is the *sync*:

- **Obsidian LiveSync** (community plugin) — real-time sync through a self-hosted **CouchDB** (a single container) with end-to-end encryption, conflict resolution, and mobile support. The most popular self-hosted route; works well once configured; the setup wizard has improved.
- **Syncthing** ([Chapter 17](17-files-sync-documents.md)) — sync the vault folder between devices. Simple, no plugin, works with any app that reads the folder; conflicts are handled as `.sync-conflict` files; iOS requires Möbius Sync and does not run in the background reliably.
- **Nextcloud/WebDAV** via the **Remotely Save** plugin (also supports S3, Dropbox, OneDrive, WebDAV) — periodic sync rather than real-time.
- **Git** via the **Obsidian Git** plugin — commits and pushes on a timer to your Gitea/Forgejo ([Chapter 22](22-dev-git-automation.md)); gives full history; clunky on mobile.
- **Obsidian Sync** (official, paid, E2EE) — not self-hosted but excellent, and a legitimate choice for people who want zero maintenance.

**Pick Obsidian if** you want the richest personal knowledge tool, accept a closed editor over open files, and are happy to run CouchDB or Syncthing. The plain-Markdown-on-disk model is the anti-lock-in guarantee that makes the closed client acceptable to many self-hosters.

### Joplin (+ Joplin Server)

An open-source (AGPL) note app with desktop, mobile, and terminal clients, Markdown editing with a rich-text option, notebooks and tags, end-to-end encryption, web clipper, and plugins. Sync targets: **Joplin Server** (the self-hosted server with sharing and publishing), Nextcloud/WebDAV, S3, Syncthing (via the filesystem target), Dropbox, OneDrive. Notes are stored in the server/sync target in Joplin's own format (SQLite locally, encrypted blobs remotely) and *exported* as Markdown — so the files are not directly editable on disk the way Obsidian's are.

**Pick it if** you want a fully open Obsidian-like experience with first-party E2EE sync and mobile apps that "just work." Less flashy than Obsidian; more open; a very solid choice for a household's shared notebooks via Joplin Server.

### Trilium Notes

A hierarchical note-taking app (Electron desktop + self-hosted server for sync and web access) with a *tree* of notes where any note can be a child of any other, rich-text and code notes, attributes and relations (a lightweight database layer), scripting in JavaScript inside notes, note versioning, encryption of individual subtrees, a web clipper, and a canvas (Excalidraw). The original author stepped back in 2024; **TriliumNext** (now simply **Trilium** again after merging) continued development with an active community and modernised the stack.

**Pick it if** you think in hierarchies and want a programmable personal wiki in one self-hosted server with web access; the tree model and attributes are unique and powerful. The mobile experience is the web UI (usable, not native).

### SilverBullet

A newer (2022–) **server-side, web-first** Markdown notes app: plain `.md` files on the server, a fast PWA that works offline, wiki-links, tags, queries (a Lua/SQL-like query language over your notes' frontmatter and content — "list all notes tagged `book` with status `reading`"), templates, and a plug system. Single Deno binary. Think "Obsidian, but it runs on your server and you use it in a browser," with a strong programmable bent. Actively developed, small but enthusiastic community.

**Pick it if** you want plain Markdown files, a web-first workflow, and a database-like query layer, and you do not need a native mobile app.

### Memos

A lightweight **microblog-style** notes server: a stream of short Markdown "memos" with tags, attachments, and a clean timeline UI — closer to Twitter-for-yourself or Google Keep than to a wiki. Single Go binary + SQLite (or Postgres/MySQL), ~30 MB RAM, multi-user, public/private/protected visibility, API, and third-party mobile apps (MoeMemos). Perfect for quick capture, journaling, and a shared household scratchpad. Not for structured knowledge.

### Notesnook

An **end-to-end encrypted** note app (open-source clients and server, formerly closed server until 2024) with rich text, notebooks, tags, attachments, reminders, and apps on every platform. The self-hosted server (a few containers: identity, sync, SSE, monograph) arrived in 2024. **Pick it if** E2EE with polished native apps is the requirement — it is the closest self-hostable analogue to Standard Notes' proposition (Standard Notes itself was acquired by Proton in 2024 and remains self-hostable but with diminishing emphasis).

### Others

**Standard Notes** (E2EE, self-hostable server, now Proton), **Flatnotes** (a minimal web UI over a folder of Markdown files — refreshingly simple), **Quillpad/Carnet/Nextcloud Notes** (Nextcloud-synced simple notes), **Logseq** (outliner with local files; sync via Syncthing/Git; the official sync service is in beta), **Anytype** (local-first, P2P sync with an optional self-hosted "any-sync" network — powerful, complex), **Zettlr**, **Dendron**, **Foam** (VS Code-based), **QOwnNotes** (desktop + Nextcloud), **Blinko** (AI-assisted quick notes, 2024), **Siyuan** (block-based, Chinese origin, self-hosted sync), **Notea**, **Hedgedoc** (below, for collaborative).

### Personal notes recommendation

**Obsidian + LiveSync (or Syncthing)** for the individual who wants the best editor and plain files. **Joplin + Joplin Server** for the household that wants fully open, E2EE, and shared notebooks with good mobile apps. **Trilium** for the hierarchical programmable wiki. **Memos** for quick capture alongside any of the above. **SilverBullet** for the web-first tinkerer.

## Knowledge bases and wikis

For documentation that several people read and some edit — the household handbook, the home lab runbook ([Chapter 28](28-maintenance-operations.md)), a family recipe collection, a club's wiki.

### Outline

A modern, fast team knowledge base (Node.js + Postgres + Redis + S3-compatible or local file storage) with a beautiful Notion-like editor (Markdown-based, slash commands, embeds), collections and nested documents, real-time collaboration, full-text search, publishing/sharing, API, and **login exclusively via OIDC/SAML/Slack/Google** — there is no built-in username/password, which makes it a natural fit for labs with an IdP ([Chapter 10](10-identity-sso.md)) and an obstacle for labs without. BSL licence (source-available, converts to Apache after four years; free to self-host).

**Pick it if** you have an IdP and want the nicest editing experience for a shared knowledge base.

### BookStack

A PHP/Laravel wiki organised as **Shelves → Books → Chapters → Pages** — a deliberately simple hierarchy that non-technical people grasp instantly. WYSIWYG *and* Markdown editors, page revisions, diagrams (draw.io integration), attachments, permissions per shelf/book/chapter/page, full-text search, LDAP/SAML/OIDC, and exports (PDF, HTML, Markdown). Stable, well-documented, one primary developer with a long track record, MIT licence.

**Pick it if** you want a wiki that a spouse or parent will actually use, with strong permissions and a familiar book metaphor. The recommendation for a household wiki.

### Wiki.js

A Node.js wiki with a polished UI, multiple editors (Markdown, WYSIWYG, raw HTML, code), Git-backed storage option (pages as files in a repo — bidirectional sync), many auth providers, and a module system. Version 2 has been stable and maintained for years; the long-promised **v3** rewrite has been in development since 2020 with no stable release, which has frozen the project's evolution. Still a perfectly usable wiki; less momentum than Outline or BookStack.

### DokuWiki

The veteran (2004) flat-file PHP wiki: no database, pages are text files, hundreds of plugins, ACLs, and extreme simplicity to back up and migrate. Dated-looking by default (templates fix that) and uses its own markup rather than Markdown (a plugin adds it). **Pick it if** you value zero-dependency durability above polish — DokuWiki instances from 2008 are still running unchanged.

### Docmost

A 2024 arrival: an open-source (AGPL) Confluence/Notion-style knowledge base with real-time collaborative editing, spaces, nested pages, comments, diagrams (draw.io, Excalidraw, Mermaid), permissions, search, and MFA/SSO (SSO in the enterprise edition). Node + Postgres + Redis. Rapidly maturing and clean; the open-core split is worth checking against your needs.

### AFFiNE and AppFlowy

The **Notion alternatives**: block-based editors with databases/kanban/calendar views, whiteboards (AFFiNE), and local-first architectures. **AFFiNE** (self-hosted server available; Postgres + Redis; heavier) leans toward the whiteboard-plus-docs "everything canvas." **AppFlowy** (Flutter clients; self-hosted **AppFlowy Cloud** with Postgres/Redis/MinIO/GoTrue) leans toward Notion's databases. Both are ambitious and still maturing; both are heavier than a wiki. Try them if you want Notion's *databases* rather than a wiki's pages.

### Others

**MediaWiki** (Wikipedia's engine — overkill and PHP-heavy for home, but the most capable wiki that exists), **XWiki** (Java enterprise wiki), **Gollum** (Git-backed, minimal), **Otter Wiki** (Git-backed Markdown wiki, tiny, lovely), **TiddlyWiki** (a single HTML file wiki; self-host with a Node server), **Wiki.js**'s many forks, **Confluence** (no), **Nextcloud Collectives** (a wiki-style app inside Nextcloud — reasonable if you are there already).

### Wiki recommendation

**BookStack** for a household or small group; **Outline** if you have an IdP and want the best editor; **Otter Wiki** or **DokuWiki** for a minimal Git/flat-file runbook; **Docmost** to watch.

## Collaborative editors

**HedgeDoc** (formerly CodiMD, forked from HackMD) — real-time collaborative Markdown with live preview, slide mode (reveal.js), permissions per note, and optional accounts (or anonymous editing by link). The right tool for "let's write this together right now." **Etherpad** — the original real-time plain-text pad, plugin-rich, ancient and reliable. **CryptPad** ([Chapter 17](17-files-sync-documents.md)) for E2EE. **Excalidraw** and **draw.io/diagrams.net** self-hosted for collaborative diagrams ([Chapter 25](25-misc-apps.md)).
