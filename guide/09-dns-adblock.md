# DNS and Network-Wide Ad Blocking

DNS is the service everything else depends on and the one most people never think about until it breaks. Running your own resolver gives you three things: **network-wide ad and tracker blocking** for every device including the ones that cannot run a blocker (smart TVs, consoles, IoT), **local names** for your services (the split-horizon DNS that makes the reverse-proxy-with-real-certificates pattern work), and **privacy** — your ISP no longer sees every domain your household visits. This chapter compares Pi-hole, AdGuard Home, Blocky, Technitium, and Unbound, explains recursive versus forwarding resolution and encrypted DNS, and covers the operational side: redundancy (because when DNS is down, *everything* is down), DHCP integration, and dynamic DNS for your public address.

## How DNS resolution works, briefly

When a device asks for `photos.example.com`, its configured **resolver** answers. Two kinds:

- A **forwarding resolver** (Pi-hole, AdGuard Home by default, your router) checks its cache and, if it does not know, asks an **upstream** resolver — Cloudflare `1.1.1.1`, Quad9 `9.9.9.9`, Google `8.8.8.8`, your ISP — and relays the answer. The upstream sees every query.
- A **recursive resolver** (Unbound, Knot Resolver, BIND, PowerDNS Recursor) does the work itself: asks a root server for `.com`, asks the `.com` servers for `example.com`, asks `example.com`'s nameservers for `photos`. No single upstream sees your full query history; each authoritative server sees only its slice. Slightly slower on a cold cache (tens of milliseconds), then equal.

**DNSSEC** cryptographically validates answers so a poisoned response is rejected; recursive resolvers do it natively, forwarders rely on the upstream. **Encrypted DNS** — DNS-over-TLS (DoT, port 853), DNS-over-HTTPS (DoH, port 443), DNS-over-QUIC (DoQ, port 853/UDP) — protects the query on the wire between you and the upstream. Plain DNS on port 53 is unencrypted; on your own LAN that is acceptable, across the internet it is not.

A common and good home architecture: **blocker (Pi-hole/AdGuard) → Unbound (recursive) on the same machine**. The blocker filters and serves local names; Unbound resolves the rest itself. No upstream sees your queries, DNSSEC is validated, and ad blocking is network-wide. Alternative: blocker → encrypted upstream (Quad9 over DoT) — simpler, still private from the ISP, one trusted third party.

## The blockers

### Pi-hole

The project that made network-wide ad blocking a household word (2015). A DNS forwarder (built on `dnsmasq`, forked as `FTL`) with blocklists, a web dashboard showing every query, per-client statistics, and — since **v6 (February 2025)** — a rewritten core that dropped the PHP/lighttpd dependency, added a REST API, native HTTPS for the admin UI, and folded most of what used to require config-file editing into the UI. Runs on anything: Raspberry Pi, Docker, an LXC, a VM. Uses ~50 MB RAM.

**Strengths:** the largest community and the most tutorials; the dashboard is excellent for understanding what your network is doing; group management lets you apply different blocklists to different clients (unblock everything for the work laptop, block hard on the kids' tablets); built-in DHCP server (handy — it means Pi-hole knows every client's hostname); local DNS records and CNAMEs in the UI; conditional forwarding to your router for reverse lookups; `pihole -up` and it stays out of your way.

**Weaknesses:** no encrypted upstream built in — you pair it with Unbound (recursive) or `cloudflared`/`dnscrypt-proxy`/`stubby` (DoH/DoT forwarder), which is one more container. No wildcard local records in the UI (v6 supports `dnsmasq` config lines for it — `address=/example.com/10.0.20.5`). No DNS rewrites by regex (blocking by regex, yes). Per-client DoH/DoT to *clients* is not supported (nor does it matter much on a LAN). The v6 migration surprised some users; if you see old tutorials referencing `/etc/lighttpd`, they predate it.

```yaml
services:
  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "127.0.0.1:8053:80/tcp"      # admin UI via reverse proxy
      # - "67:67/udp"                # only if using Pi-hole's DHCP (needs NET_ADMIN and host or macvlan networking)
    environment:
      TZ: Europe/London
      FTLCONF_webserver_api_password: ${PIHOLE_PASSWORD}
      FTLCONF_dns_upstreams: 127.0.0.1#5335   # Unbound sidecar below; or 9.9.9.9;149.112.112.112
      FTLCONF_dns_listeningMode: all
    volumes:
      - ./etc-pihole:/etc/pihole
    cap_add: [NET_ADMIN]
  unbound:
    image: mvance/unbound:latest       # or klutchell/unbound; both well-maintained
    container_name: unbound
    restart: unless-stopped
    network_mode: "service:pihole"     # share Pi-hole's namespace so 127.0.0.1#5335 works
    volumes:
      - ./unbound:/opt/unbound/etc/unbound
```

### AdGuard Home

AdGuard's open-source (GPLv3) DNS server, a single Go binary with a modern web UI. Functionally a superset of Pi-hole for most people: blocklists (AdGuard's own syntax plus hosts files), per-client settings, parental controls and safe search, query log, statistics — **plus** built-in **encrypted upstreams** (DoH, DoT, DoQ, DNSCrypt, all configurable in the UI, with parallel or load-balanced querying), built-in **encrypted listeners** (serve DoH/DoT/DoQ to your own clients — useful for phones off-network via a mesh VPN, or Android's Private DNS setting), **DNS rewrites** (including `*.example.com → 10.0.20.5` wildcards, in the UI), and a DHCP server. Uses ~40–80 MB RAM.

**Strengths:** encrypted upstreams and wildcard rewrites in the UI are exactly the two things Pi-hole makes you work for; a single binary with no dependencies; excellent on low-power hardware; the client identification (by IP, MAC, or ClientID for DoH/DoT clients) is more flexible. Actively developed by a company with a commercial product built on the same engine.

**Weaknesses:** the dashboard is less granular than Pi-hole's (no per-client "top blocked" breakdowns as rich, though it has improved); the community is smaller (still large); the blocklist syntax differences occasionally matter; upstream recursion still requires Unbound alongside if you want no third party at all. AdGuard as a company sells a VPN and ad-blocker — some prefer a purely community project.

```yaml
services:
  adguardhome:
    image: adguard/adguardhome:latest
    container_name: adguardhome
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "127.0.0.1:3000:3000/tcp"   # first-run setup wizard
      - "127.0.0.1:8080:80/tcp"     # admin UI after setup, via reverse proxy
      # - "853:853/tcp"             # DoT listener, if serving encrypted DNS to clients
    volumes:
      - ./work:/opt/adguardhome/work
      - ./conf:/opt/adguardhome/conf
```

### Blocky

A Go DNS proxy configured entirely by a **YAML file** — no web UI, no query database by default (optional Prometheus metrics and Grafana dashboards, or logging to a database/CSV). Blocklists, allowlists, per-client-group filtering, custom DNS (with wildcards), conditional forwarding, encrypted upstreams (DoH/DoT), caching with prefetching, and about 20 MB RAM. It starts in a second and its configuration lives in Git like everything else.

**Pick it if:** you want your DNS blocker to be infrastructure-as-code, you already run Prometheus/Grafana for observability, and you do not want a stateful UI. Popular with the Kubernetes and NixOS crowds and with people running two or three redundant instances from one config file.

**Watch out for:** no UI means no quick "why was this blocked" without querying logs/metrics; smaller community.

### Technitium DNS Server

A full **authoritative + recursive + forwarding** DNS server (C#/.NET, cross-platform) with a web UI, blocklists, DoH/DoT/DoQ on both sides, DNSSEC signing and validation, zone management (primary/secondary zones, dynamic updates, zone transfers), split-horizon via "APP" plugins, DHCP, query logging, clustering via zone transfer. It is what you run when you want *one* piece of software to be the blocker, the recursive resolver, and the authoritative server for `home.arpa` with proper zones — and you want a UI for all of it.

**Pick it if:** you want the most complete feature set in one package, or you want to learn real DNS (zones, records, SOA, transfers) with a UI that exposes them. It is quietly excellent and under-appreciated.

**Watch out for:** heavier (~150 MB RAM with .NET); the UI is dense; one primary developer.

### Unbound (and Knot Resolver, BIND, PowerDNS)

**Unbound** is the recursive resolver most people pair with Pi-hole or AdGuard. Small, fast, secure (NLnet Labs), DNSSEC-validating, with local-data directives for static records and, since 1.x, RPZ support for blocklists (so Unbound *alone* can do basic blocking without a frontend, if you do not need a dashboard). Its config is a text file; it has no UI. On OPNsense it is the default resolver with a UI, blocklists ("Unbound DNS Blocklist" feature), and host overrides — for many OPNsense users, **Unbound on the firewall is the whole DNS solution** and no Pi-hole is needed.

**Knot Resolver** (CZ.NIC) is the other modern recursive resolver, scriptable in Lua, excellent performance. **BIND 9** is the reference implementation of everything, still the right answer for people who need a full authoritative server and know it. **PowerDNS** (Recursor + Authoritative + dnsdist) is the ISP-grade modular choice; PowerDNS-Admin gives it a UI. **CoreDNS** is the Kubernetes cluster DNS and rarely used elsewhere at home. **dnsmasq** is the tiny DHCP+DNS forwarder inside most routers, OpenWrt, and Pi-hole.

### Comparison

| | Pi-hole | AdGuard Home | Blocky | Technitium | Unbound (alone) |
|---|---|---|---|---|---|
| Type | Forwarder + blocker | Forwarder + blocker | Forwarder + blocker | Full DNS server | Recursive resolver |
| Web UI | Yes (excellent stats) | Yes (modern) | No (YAML + metrics) | Yes (dense) | No (OPNsense wraps it) |
| Encrypted upstream built in | No (add Unbound/cloudflared) | **Yes** (DoH/DoT/DoQ) | Yes (DoH/DoT) | Yes | DoT yes; recursion is the point |
| Serve DoH/DoT to clients | No | **Yes** | No | Yes | DoT yes |
| Wildcard local records | Via dnsmasq config line | **Yes (UI)** | Yes (YAML) | Yes (zones) | Yes (`local-zone`) |
| Per-client rules | Groups (good) | Yes | Client groups | Yes | No |
| DHCP server | Yes | Yes | No | Yes | No |
| Authoritative zones | No | No | No | **Yes** | Limited (`local-data`) |
| RAM | ~50 MB | ~60 MB | ~20 MB | ~150 MB | ~30 MB |
| Config as code | Partial (teleporter export; v6 TOML) | YAML file (editable) | **Fully** | Partial (API) | Fully |
| Best for | Beginners; best dashboard | Most people; encrypted DNS + wildcards in UI | GitOps/Prometheus users | One-server-does-everything; learning DNS | Recursion behind a blocker; OPNsense users |
