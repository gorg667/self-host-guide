# The Long Tail: Household, Finance, Web, and Utility Apps

Every home lab accumulates a layer of small, delightful, single-purpose applications that do not fit a big category but make daily life better: a recipe manager the family actually uses, a budget tool that is not a subscription, an inventory of what is in the garage, a website change-watcher, a privacy-respecting YouTube front-end, analytics for a blog, the blog itself. This chapter is a curated survey — grouped by need, with a recommendation in each group — of the applications worth knowing in the categories that did not get their own chapter: recipes and groceries, personal finance, inventory and household management, web monitoring and archiving, privacy front-ends, websites and blogs, analytics, forms and scheduling, whiteboards, and a grab-bag of oddities that people run and love.

## Recipes and groceries

- **Mealie** — the recipe manager most households settle on: import from any URL (scraper), a clean recipe view with scaling, meal planning, shopping lists (with aisle grouping), tags and categories, multi-user with households, OIDC, an API, and a good mobile PWA. Python + SQLite/Postgres. **The recommendation.**
- **Tandoor Recipes** — the power-user alternative: import from URLs and PDFs/images (OCR), highly structured ingredients and steps, meal planning, shopping lists, a space/multi-tenant model, keyword hierarchy, and integration with Bring! and Home Assistant. Django + Postgres. More features, denser UI.
- **Grocy** — not a recipe app first but an **ERP for your household**: stock tracking with barcodes and expiry dates, shopping lists driven by minimum stock, recipes that consume stock, chores, tasks, batteries, equipment with manuals — the "know what is in the pantry" tool. PHP + SQLite. Steep to maintain data discipline; rewarding for people who will. Companion **Barcode Buddy** scans into Grocy.
- **KitchenOwl** (shopping-list-first with recipes and meal planning; excellent shared shopping lists with native mobile apps), **Recipya**, **RecipeSage**, **Bar Assistant** (cocktail recipes and bar inventory — a niche gem), **Cooklang** (recipes as a plain-text markup with tooling).

## Personal finance

- **Actual Budget** — envelope/zero-based budgeting (the YNAB model), local-first with a sync server you self-host, bank import via files or **SimpleFIN/GoCardless** bridges, reports, rules, schedules, a fast UI, and mobile PWA. Node, tiny. **The recommendation for budgeting** and the best YNAB replacement.
- **Firefly III** — the comprehensive personal finance manager: accounts, transactions, budgets, categories, tags, bills, rules, piggy banks, recurring transactions, reports, multi-currency, and a large API; imports via the **Firefly III Data Importer** (CSV, camt, and GoCardless/Salt Edge bank connections). PHP + database. Less "budgeting method," more "complete ledger." **The recommendation for tracking everything.**
- **Ghostfolio** — investment portfolio tracking: holdings, performance, allocation, dividends, benchmarks, with market data from Yahoo/CoinGecko and a polished UI. **The recommendation for investments.**
- **Wallos** — subscription tracking: what recurring charges you pay, when, and totals — the "why is my card statement so high" tool. Small PHP app, lovely.
- **Maybe Finance** (an ambitious personal-finance app that went open source in 2024 — accounts, budgets, investments, AI assistant; the company later pivoted, community continues), **Beancount/Fava** and **hledger** (plain-text accounting with web UIs — for people who like double-entry in a text file), **GnuCash** (desktop, with optional shared DB), **Invoice Ninja** and **Crater** and **InvoicePlane** (invoicing for freelancers), **Kimai** and **Traggo** (time tracking), **Akaunting** (small-business accounting), **Money Manager Ex**, **Paisa** (Ledger-based with a UI), **Budget Zero**.

## Inventory and household management

- **Homebox** — inventory of your possessions: items with photos, locations (nested — house → garage → shelf), labels, purchase info, warranty dates, manuals, QR-code labels to print and stick on bins, and a simple, fast UI. Go + SQLite, tiny. **The recommendation**; the actively maintained fork is under `sysadminsmedia/homebox`.
- **Grocy** (above) for consumables and chores; **Snipe-IT** (IT asset management — serious, for people with a lot of hardware or a small business); **Shelf**, **Inventree** (parts inventory for makers — components, BOMs, stock, suppliers; excellent for electronics hobbyists), **PartDB** (electronic parts), **Spoolman** (3D-printer filament tracking; integrates with Klipper/OctoPrint), **Homarr**'s inventory-ish widgets, **Manyfold** (3D model library for printing), **Papra/Paperless** for the receipts and manuals.
- **Home maintenance**: **HomeBox**'s maintenance log, **Donetick** (recurring chores with assignments — [Chapter 18](18-notes-productivity.md)), **Grocy** chores, **Maintainerr** (for media — different thing), **Reminders via HA**.
- **Vehicles**: **LubeLogger** — vehicle maintenance records, fuel economy, reminders, documents; excellent and the standard. **Hammond** (fuel/expenses).
- **Plants**: **Plant-it**, **HortusFox**; **Home Assistant** with soil sensors for the automated version.
- **Family organisation**: **Nextcloud** calendars, **Vikunja**, **Homarr** boards ([Chapter 18](18-notes-productivity.md)); **Baby Buddy** (feeding/sleep/nappy tracking for new parents — genuinely useful, with HA integration); **Wger** (workout and nutrition tracking — a self-hosted fitness log with a large exercise database); **FitTrackee** (GPS activity tracking — a Strava-ish self-hosted log); **Endurain**; **Fasten Health** (aggregating medical records from providers — US-centric).
- **Pets**: **Petkeeper**-style apps are thin; Grocy/Homebox/HA cover most.

## Web monitoring, archiving, and downloading

- **Changedetection.io** — watch any web page (or JSON API) for changes and alert via 70+ notification services: price drops, restock, a job listing, a government page, a changelog. Visual selector for the region to watch, browser-rendering (Playwright) for JS pages, price-tracking mode, and scheduling. **The recommendation**; one of the highest-utility small apps in self-hosting.
- **ArchiveBox** — save web pages in every format (HTML, PDF, screenshot, WARC, media via yt-dlp, readability text) into a browsable local archive; the "keep this forever" tool ([Chapter 18](18-notes-productivity.md) has the bookmark-oriented alternatives — Linkwarden/Karakeep archive too).
- **Wallabag/Readeck** (read-later), **Linkwarden** (bookmarks with archiving) — [Chapter 18](18-notes-productivity.md).
- **yt-dlp** front-ends: **MeTube** (paste a URL, get the video/audio — the simplest), **Tube Archivist** (subscribe to YouTube channels, download and index everything with a Jellyfin-style UI and Jellyfin/Plex integration — the "own my YouTube subscriptions" tool), **Pinchflat** (channel/playlist downloader designed to feed a media server, lighter than Tube Archivist; the current favourite for that use), **ytdl-sub**, **TubeSync**, **Podgrab/Podfetch** for podcasts ([Chapter 15](15-media.md) has Audiobookshelf), **Cobalt** (self-hosted media downloader UI for many sites), **gallery-dl** (image galleries).
- **Speedtest Tracker** — scheduled Ookla/LibreSpeed tests with history graphs and alerts when your ISP under-delivers; ammunition for support calls. **The recommendation** for ISP accountability. **MySpeed** is the alternative.
- **Uptime and status**: [Chapter 12](12-monitoring.md).
- **Web scraping/RSS generation**: **RSS-Bridge**, **RSSHub**, **Huginn** ([Chapter 18](18-notes-productivity.md), [Chapter 22](22-dev-git-automation.md)).

## Privacy front-ends

Self-hosted proxies that let you use big platforms without their tracking, ads, or accounts. They work by fetching content server-side and re-rendering it; platforms periodically break them and they periodically recover.

- **Invidious** — YouTube: no ads, no tracking, subscriptions without an account, audio-only mode, RSS for channels, SponsorBlock, and a lightweight UI. The most established; YouTube's countermeasures have made public instances unreliable, but a *private* instance for a household works well most of the time (a companion **Invidious companion**/**inv_sig_helper** and occasionally a proxy or PO-token setup are needed as of 2025). Apps: **Clipious**, **FreeTube** (desktop, uses Invidious/local), **Yattee** (iOS).
- **Piped** — the other YouTube front-end (Kotlin backend + Vue front-end, SponsorBlock, DeArrow, subscriptions, playlists); similar cat-and-mouse dynamics. **LibreTube** is its Android app.
- **Redlib** (formerly Libreddit) — Reddit without JavaScript, ads, or tracking; browse subreddits and users; no posting. Works; Reddit rate-limits aggressively.
- **Nitter** — Twitter/X; largely non-functional since X's 2023–2024 API and login-wall changes; private instances with session tokens limp along. Effectively dead for most.
- **ProxiTok** (TikTok), **Rimgo** (Imgur), **Scribe** (Medium), **BreezeWiki** (Fandom wikis without the bloat), **AnonymousOverflow** (Stack Overflow), **Quetre** (Quora), **Dumb** (Genius lyrics), **Wikiless**, **Photon/Voyager** (Lemmy front-ends), **SearXNG** (search — [Chapter 23](23-ai-llm.md)).
- **LibRedirect** (a browser extension) redirects links to your instances automatically. **Farside** does the same server-side.

Honest assessment: these are valuable and fragile. YouTube front-ends in particular require occasional maintenance. Run them for yourself; do not run public instances unless you enjoy IP bans.

## Websites, blogs, and static sites

- **Static site generators** — **Hugo** (Go, blazing fast, the most popular), **Astro** (modern, component-based, islands), **Eleventy/11ty** (flexible JS), **Zola** (Rust, Hugo-like, single binary), **MkDocs Material** (documentation — this guide's stylistic cousin), **Docusaurus**, **Jekyll** (the classic). Build in CI ([Chapter 22](22-dev-git-automation.md)) and serve the output from **Caddy**/**Nginx** — the most secure and lowest-maintenance website possible: no database, no PHP, no admin login to attack. **The recommendation for a personal site.**
- **Ghost** — the modern publishing platform: a beautiful editor, memberships and newsletters (paid subscriptions via Stripe), themes, SEO, and a Node + MySQL backend. Excellent for a real blog with subscribers. The self-hosted version is fully featured; Ghost(Pro) is their hosted offering.
- **WordPress** — powers a third of the web; runs anywhere; every plugin imaginable; and is the most attacked application on the internet by volume. If you self-host it: keep core/plugins/themes updated automatically, minimise plugins, put it behind the reverse proxy with a WAF, use strong auth and 2FA (WordFence or similar), disable XML-RPC, and consider **WP2Static**/**Simply Static** to publish a static copy publicly while keeping the WordPress admin LAN-only — the best of both worlds.
- **WriteFreely** (minimalist, federated via ActivityPub — your blog appears in the fediverse), **Hexo**, **Grav** (flat-file CMS with an admin UI — a good middle ground between static and WordPress), **Kirby** (paid, flat-file, superb), **Publii** (desktop static CMS), **Bear Blog**-style minimal engines, **Pico CMS**, **Bludit**, **Typemill**, **Decap CMS** (a Git-based admin UI for static sites — edit Markdown in a browser, commits to your repo, CI rebuilds; pairs with Hugo/Astro), **Sveltia CMS** (Decap's modern successor), **Payload/Strapi/Directus** (headless CMSes — for developers building sites), **Wagtail** (Django CMS).
- **Fediverse servers** — **Mastodon** (heavy: Ruby + Postgres + Redis + Sidekiq + Elasticsearch optional; ~4 GB for a single-user instance), **GoToSocial** (a lightweight Go ActivityPub server — the single-user Mastodon alternative at ~200 MB), **Akkoma/Pleroma**, **Misskey/Sharkey/Iceshrimp**, **Lemmy** and **PieFed** (Reddit-like), **Pixelfed** (Instagram-like), **PeerTube** (video), **Funkwhale** (audio), **Mobilizon** (events), **Bookwyrm** (Goodreads-like). Running your own fediverse instance is a real commitment (moderation, federation storage growth, spam); GoToSocial for a personal presence is the sane entry point.
- **Comments for static sites**: **Isso**, **Remark42**, **Commento/Comentario**, **Cusdis**, **Giscus** (GitHub Discussions-backed, hosted).
- **Link-in-bio / landing**: **LinkStack**, **LittleLink**.

## Analytics

Privacy-respecting alternatives to Google Analytics — no cookies, no cross-site tracking, GDPR-friendly, and often no consent banner needed:

- **Umami** — a clean, fast, cookie-less analytics dashboard (Node + Postgres/MySQL): pageviews, referrers, countries, devices, events, funnels, retention; multi-site; team access. ~100 MB. **The recommendation.**
- **Plausible CE** — the other favourite: simple, beautiful, cookie-less, with goals/events, funnels, and a Community Edition that is fully self-hostable (Elixir + Postgres + ClickHouse — heavier than Umami at ~1–2 GB). Some features arrive in the hosted version first.
- **Matomo** — the full Google-Analytics replacement: everything GA does (heatmaps and session recording via plugins, e-commerce, funnels, A/B tests, tag manager), PHP + MySQL, heavier and more complex; the choice when you need depth.
- **GoatCounter** (tiny, single-binary, minimal), **Shynet**, **Ackee**, **Rybbit** (2025, polished Umami/Plausible-style with session replay), **Swetrix**, **Counter**, **PostHog** (product analytics + feature flags + session replay — heavy, developer-oriented, self-hostable "hobby" deployment), **GoAccess** (log-file analytics — no JavaScript at all, works on your Caddy/Nginx logs).

## Forms, scheduling, and signatures

- **Cal.com** — the Calendly replacement: booking pages, availability from your CalDAV/Google/Outlook calendars, event types, round-robin, video integrations (Jitsi, Cal Video, Zoom), workflows. Self-hosting is supported but heavy (Next.js + Postgres + Redis + many env vars); the open-core split moves some features to paid. **Easy!Appointments** (PHP, simpler, for a small business), **Rallly** (Doodle-style group scheduling — light and lovely), **Zitadel/…** no.
- **Forms**: **Formbricks** (surveys and in-app feedback, open source), **HeyForm**, **Typebot** (conversational forms/chatbots — excellent), **OhMyForm**, **LimeSurvey** (the academic-survey heavyweight), **Formspree alternatives** like **Formio**; **Nextcloud Forms** if you run Nextcloud; **Baserow**/**NocoDB**/**Teable** (Airtable-style databases with forms — see [Chapter 26](26-databases-backing-services.md)).
- **E-signatures**: **DocuSeal** — sign and send documents for signature, templates, audit trail, API; the self-hosted DocuSign, and genuinely good. **Documenso** is the other strong option (TypeScript, polished).
- **Polls/decisions**: **Rallly**, **Framadate**, **Polls** in Nextcloud.

## Whiteboards, diagrams, and design

- **Excalidraw** — the hand-drawn-style collaborative whiteboard; self-hostable with the **excalidraw-room** collaboration server; exports to PNG/SVG; embeds in Obsidian/Docmost/HedgeDoc. **The recommendation.**
- **draw.io / diagrams.net** — the full diagramming tool (network diagrams, flowcharts, UML, AWS/Azure icon sets); a single self-hosted container; integrates with Nextcloud/BookStack/Outline.
- **tldraw** (self-hostable modern whiteboard), **Penpot** (open-source Figma — design and prototyping; heavy but complete), **Kroki** (text → diagram service for Mermaid/PlantUML/D2/Graphviz), **PlantUML server**, **Mermaid Live** (static), **Ludwig**, **wbo** (a minimal shared whiteboard).

## Oddities people love

- **Actual Budget** and **Mealie** have already appeared; these did not fit anywhere but earn their keep:
- **Kiwix** — offline Wikipedia (and StackExchange, Project Gutenberg, TED, and more) served from ZIM files. The full English Wikipedia with images is ~100 GB; the whole knowledge of the internet on your NAS, available when the internet is not. Doomsday-prepper approved.
- **Stirling PDF** ([Chapter 17](17-files-sync-documents.md)), **IT-Tools**, **CyberChef** ([Chapter 22](22-dev-git-automation.md)).
- **Dawarich** — a self-hosted Google Timeline replacement: location history from your phone (via OwnTracks, Overland, or Google Takeout import), maps, stats, trips; **Reitti** and **OwnTracks Recorder** are alternatives; **Traccar** is the fleet-grade GPS tracker.
- **PhotoPrism/Immich** ([Chapter 16](16-photos.md)) aside, **Immich Public Proxy** shares Immich albums publicly without exposing Immich.
- **Wakapi** (WakaTime-compatible coding-time tracker), **Umami** for your own dashboards, **Beaver Habit Tracker** and **Habitica** (habit tracking), **Monica** (personal CRM — remember birthdays and conversations with friends and family), **Twenty** (open-source CRM for a small business), **Fider** (feature-request voting board), **Zammad**/**FreeScout**/**Helpy**/**UVdesk** (help desks — FreeScout is the light one), **Peppermint** and **Zammad** (ticketing), **Statamic**…
- **Home lab specifics**: **NetBox** (the network/infrastructure source of truth — IPAM, racks, devices, cables; enterprise-grade, and many home labbers document their lab in it; heavy), **Netbox's** lighter cousins **phpIPAM** and **NIPAP** (IP address management only), **Rack Elevation** tools, **WatchYourLAN** (ARP-based device discovery and new-device alerts on your LAN — light and useful), **Fing** alternatives **NetAlertX** (formerly PiAlert — new-device detection with notifications; the recommendation for "who just joined my Wi-Fi"), **Nmap web UIs**, **Speedtest Tracker** (above), **Smokeping** (latency graphs — ancient and still unmatched), **ntopng** (traffic analysis), **LibreNMS** ([Chapter 12](12-monitoring.md)), **Oxidized** (network device config backup — pairs with LibreNMS), **PhpMyAdmin**-style tools in [Chapter 26](26-databases-backing-services.md), **Guacamole** (browser-based RDP/SSH/VNC gateway — a clientless remote desktop to every machine in the lab, behind forward-auth; excellent), **RustDesk** (self-hosted TeamViewer — relay + ID server for remote support of family PCs; genuinely useful), **MeshCentral** (remote management of many machines with an agent — the free RMM), **Tactical RMM**, **Semaphore UI** (a web UI for Ansible/Terraform — [Chapter 27](27-automation-iac.md)), **Cockpit** ([Chapter 12](12-monitoring.md)), **Webmin** (the ancient server admin UI; still works), **Wake-on-LAN** dashboards (**UpSnap** — a clean WoL UI with device discovery and scheduled wakes; useful for the gaming/GPU box).
- **Printing and scanning**: **CUPS** in a container for AirPrint/network printing of a USB printer; **scanservjs** or **Scanopy** for a web UI on a USB scanner (pairs with Paperless's consume folder); **OctoPrint**/**Klipper + Mainsail/Fluidd** for 3D printers (with **Spoolman** and **Obico** for AI failure detection).
- **Weather**: a personal weather station (Ecowitt, Ambient) feeding **WeeWX** or **Home Assistant**; **Windy/Open-Meteo** for data.
- **Education**: **Moodle** (heavy LMS), **Kolibri** (offline education content), **Anki sync server** (self-hosted AnkiWeb — small and useful for flashcard users), **Kiwix** (above).
- **Genealogy**: **Gramps Web** (the desktop genealogy app's web version — multi-user family tree with photos and sources; excellent), **webtrees**.
- **Music practice and misc**: **Navidrome** ([Chapter 15](15-media.md)), **Snapcast** (multi-room audio), **Owntone** (iTunes/DAAP/AirPlay server), **Mopidy**, **Volumio**/**moOde** (Pi audio players).
- **Ham radio, aviation, and hobby feeds**: **ADS-B** receivers (tar1090/readsb with a USD 25 SDR dongle — watch the planes overhead), **AIS** for ships, **WSJT-X/Wavelog** for amateur radio logging, **OpenWebRX** (a web SDR).

## Recommendations (one per category)

| Need | Pick |
|---|---|
| Recipes | Mealie (Tandoor for power users) |
| Groceries & pantry | KitchenOwl (lists) / Grocy (stock) |
| Budget | Actual Budget |
| Full finance ledger | Firefly III |
| Investments | Ghostfolio |
| Subscriptions | Wallos |
| Home inventory | Homebox |
| Vehicles | LubeLogger |
| Page change alerts | Changedetection.io |
| YouTube archiving | Pinchflat (or Tube Archivist) |
| ISP accountability | Speedtest Tracker |
| YouTube front-end | Invidious (private instance) |
| Personal website | Hugo/Astro static, built in CI, served by Caddy |
| Blog with subscribers | Ghost |
| Analytics | Umami |
| Scheduling | Cal.com (or Rallly for group polls) |
| E-signatures | DocuSeal |
| Whiteboard | Excalidraw |
| Diagrams | draw.io |
| Offline knowledge | Kiwix |
| Location history | Dawarich |
| "Who joined my Wi-Fi" | NetAlertX |
| Browser remote desktop | Apache Guacamole |
| Remote support for family | RustDesk |
| Wake-on-LAN | UpSnap |

## Checklist

- [ ] Each small app runs from its own Compose stack with pinned versions and data on local disk; SQLite apps not on NFS.
- [ ] Household-facing apps (recipes, lists, budget) have friendly hostnames on the family dashboard and, where supported, OIDC login.
- [ ] Anything with financial or location data (Actual, Firefly, Dawarich) is VPN-only or behind forward-auth; never public.
- [ ] Public-facing sites are static where possible; dynamic CMSes (WordPress/Ghost) are updated automatically, behind the proxy with WAF/CrowdSec, admin restricted to LAN/VPN.
- [ ] Privacy front-ends run as private instances and are expected to need occasional fixes.
- [ ] Every app's export format checked before committing years of data (recipes → JSON/Markdown; finance → CSV/OFX; inventory → CSV).
- [ ] Small-app data directories included in the nightly backup — they are small, precious, and easy to forget.
