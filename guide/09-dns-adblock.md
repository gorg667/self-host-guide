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

## Blocklists

The blocker is only as good as its lists. Guidance that has stabilised over the years:

- **Start with one curated list, not twenty.** **Hagezi's** lists (Multi Normal / Pro / Pro++ / Ultimate, in increasing aggressiveness) and **OISD** (Big / Small) are the modern community standards: well-maintained, deduplicated, low false-positive rates, with a "Pro" or "Big" tier that blocks most ads and trackers without breaking sites. Steven Black's unified hosts is the classic and still good. The old approach of stacking twenty lists with a million entries produced more breakage than blocking.
- **Add targeted lists** for specific goals: Hagezi's **TIF** (threat intelligence feeds — malware, phishing), a **native tracker** list for your device brands (Samsung/LG TVs, Xiaomi, Apple, Windows telemetry — Hagezi publishes these per vendor), a **DoH bypass** list (blocks known DoH servers so devices with hardcoded DoH — some TVs, browsers — fall back to your resolver).
- **Allowlist, don't disable.** When something breaks, find the blocked domain in the query log and allowlist it. Common ones: `s.youtube.com` (history), `spclient.wg.spotify.com`, `app-measurement.com` (some apps refuse to work), Microsoft/Xbox/PlayStation telemetry domains that games need, `clients4.google.com`.
- **Update lists weekly** (the default in every blocker).
- **Know what you cannot block**: YouTube ads (served from the same domains as video), Twitch ads, in-app ads that use the app's own API domain, and anything on a device that hardcodes `8.8.8.8` — for that last one, **redirect or block outbound port 53** at the firewall so every device is forced through your resolver ([Chapter 3](03-networking.md)). DoH-hardcoded devices need the DoH blocklist plus, ideally, firewall blocking of known DoH IPs.

## Local DNS and the reverse-proxy pattern

This is where DNS meets [Chapter 7](07-reverse-proxy-tls.md). You want `*.example.com` to resolve to your reverse proxy's LAN IP for every device on the network and via VPN.

**AdGuard Home:** Filters → DNS rewrites → add `*.example.com` → `10.0.20.5`. Done. Individual overrides (`nas.example.com` → `10.0.20.10`) take precedence over the wildcard.

**Pi-hole v6:** Settings → Local DNS Records for individual hosts. For a wildcard, add to `/etc/dnsmasq.d/99-wildcard.conf` (or the v6 `misc.dnsmasq_lines` setting): `address=/example.com/10.0.20.5`. Note this also captures `example.com` itself; if your public site lives there, add an explicit record for it.

**Blocky:** `customDNS: mapping: example.com: 10.0.20.5` — matches the domain and all subdomains.

**Unbound:** `local-zone: "example.com." redirect` + `local-data: "example.com. A 10.0.20.5"` — the `redirect` type applies to all subdomains. Or, on OPNsense, Services → Unbound → Overrides → Host Override with a wildcard (`*` host).

**Technitium:** create a primary zone `example.com` with an `A` record for `*`.

For **device hostnames** (`nas.home.arpa`), the DHCP server's lease table is the source: Pi-hole/AdGuard/Technitium as DHCP server register leases automatically; if the router is DHCP, enable **conditional forwarding** (Pi-hole: Settings → DNS → Conditional forwarding; AdGuard: "private reverse DNS servers" + "use private reverse DNS resolvers") so the blocker asks the router to resolve `.lan` names and reverse lookups, and the query log shows hostnames instead of IPs.

## Redundancy: DNS must not have a single point of failure

When your only DNS server is on a Docker host that you reboot for updates, every device in the house loses the internet for the duration — and the household learns to hate your lab. Rules:

1. **Run two resolvers on two physical machines.** A Raspberry Pi or an N100 box as the second is ideal — something you never reboot on a whim. Hand out both via DHCP.
2. **Understand that DHCP "secondary DNS" is not failover.** Clients pick either server arbitrarily and may stick to one; if the two have different blocklists or local records, behaviour becomes inconsistent. **Keep both identical.** Tools: **Gravity Sync** (deprecated with Pi-hole v6) / **Nebula Sync** (Pi-hole v6 sync via the API), **Orbital Sync**; for AdGuard Home, **AdGuardHome-Sync**; for Blocky, the same YAML file on both hosts; for Technitium, secondary zones and cluster sync. Or run both as identical containers from the same Compose file on two hosts and deploy changes to both.
3. **Alternatively, a floating IP with keepalived**: two resolvers, one virtual IP (VRRP) that moves to whichever is alive. Clients see one address. Slightly more setup, cleanest client experience. This is what the OPNsense HA (CARP) crowd gets for free.
4. **Do not use a public resolver as the "secondary."** Clients will use it some of the time and your blocking becomes random.
5. **Keep the DNS host lean.** Don't put the resolver on the same machine as the media server that you rebuild monthly.

## Encrypted DNS for your own clients

On the LAN, plain port 53 to your resolver is fine. Off the LAN, your phone on cellular uses whatever DNS the carrier hands out — your blocking and local names disappear. Options:

- **Mesh VPN with split DNS** ([Chapter 8](08-remote-access-vpn.md)) — the recommended approach: Tailscale/NetBird tell the device to use your resolver for everything (or for your domain), traffic is inside the tunnel, no exposure needed.
- **Serve DoT/DoH publicly** from AdGuard Home or Technitium behind your reverse proxy, and configure Android's "Private DNS" (DoT hostname) or iOS's DNS profile (via a `.mobileconfig`, or an app like DNSecure) to point at it. Works everywhere without a VPN; exposes your resolver to the internet (rate-limit it; it is not authenticated, so anyone can use it — AdGuard's ClientID feature `clientid.dns.example.com` gives per-device identification and can be combined with allow-listing known ClientIDs).
- **A hosted filtered resolver** (NextDNS, Control D, AdGuard DNS) as a fallback for devices you cannot VPN. Not self-hosting, but pragmatic.

## Dynamic DNS

If your public IP changes and you need a name for it (plain WireGuard, Headscale at home, an exposed reverse proxy, a game server), a **DDNS** client updates a DNS record whenever the IP changes. Every router OS has a DDNS client for the common providers; in Docker, **ddns-updater** (qdm12) supports dozens of providers with a status UI; **cloudflare-ddns** variants for Cloudflare specifically; **inadyn** and **ddclient** are the traditional CLI tools. Point a hostname (`home.example.com`) at your IP; everything else CNAMEs to it. Update interval of 5 minutes is plenty. With a mesh VPN and no exposed services, you do not need DDNS at all.

## Operational notes

- **Port 53 conflicts.** Ubuntu's `systemd-resolved` listens on `127.0.0.53:53`, which blocks Docker from publishing `0.0.0.0:53`. Fix: disable the stub listener (`DNSStubListener=no` in `/etc/systemd/resolved.conf`, then `ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf`), or bind the container to the host's LAN IP only (`10.0.20.5:53:53`).
- **The DNS host must not depend on itself.** Set the Docker host's own `/etc/resolv.conf` to the router or a public resolver, not to the Pi-hole container it runs — otherwise, when Docker is down, the host cannot resolve `ghcr.io` to pull the image to bring Pi-hole back.
- **Real client IPs.** A blocker in Docker bridge mode sees every query from the Docker gateway IP, killing per-client stats. Fix with `network_mode: host` (simplest; the container binds port 53 on the host directly) or a macvlan network giving it its own LAN IP ([Chapter 5](05-containers.md)).
- **TTL and caching.** Blockers cache; Unbound caches (enable `prefetch: yes` and `serve-expired: yes` for snappier browsing). Local record changes may take a minute to propagate to clients that cached the old answer.
- **Logging and privacy.** The query log is a complete record of everyone's browsing. Set retention appropriately (Pi-hole: Settings → Privacy; AdGuard: Settings → General → query log retention), or anonymise, and think about who in the household can see the dashboard.
- **Test it:** from a client, `nslookup doubleclick.net` should return `0.0.0.0` (or NXDOMAIN); `nslookup photos.example.com` should return your proxy's LAN IP; `dig +dnssec example.com` via Unbound should show the `ad` flag; `dnsleaktest.com` should show only your resolver's upstream (or nothing but your ISP's IP if fully recursive).

## Recommendations

- **Default:** AdGuard Home (encrypted upstreams and wildcard rewrites in the UI) → Unbound recursive, or straight to Quad9/Cloudflare over DoT if you prefer fewer containers. Two instances on two machines, synced with AdGuardHome-Sync. Hagezi Pro + TIF lists.
- **If you love the dashboard or already know it:** Pi-hole v6 + Unbound. Two instances, Nebula Sync.
- **If you run OPNsense:** Unbound on the firewall with the built-in blocklists and host overrides may be all you need — it is one fewer thing to run, and the firewall is the one box that is always on.
- **If your config lives in Git:** Blocky.
- **If you want one server to rule them all (blocking + recursion + real zones):** Technitium.

## Checklist

- [ ] A self-hosted resolver handed out via DHCP to every VLAN; the router's DNS pointed at it too (or the router itself is the resolver).
- [ ] Upstream is recursive (Unbound) or encrypted (DoT/DoH); plain-53 to a public resolver is not the upstream.
- [ ] A curated blocklist (Hagezi/OISD) plus threat-intel; not twenty overlapping lists.
- [ ] `*.example.com` (or explicit records) → reverse proxy; device hostnames resolvable via DHCP integration or conditional forwarding.
- [ ] Two resolvers on two physical machines, kept identical by a sync tool or shared config; DHCP hands out both (or a keepalived VIP).
- [ ] The DNS host's own `resolv.conf` does not point at its own container.
- [ ] Outbound port 53/853 from other devices blocked or redirected at the firewall so hardcoded DNS cannot bypass you; DoH blocklist enabled.
- [ ] Remote devices get your DNS via mesh VPN split DNS (preferred) or a rate-limited DoT/DoH listener.
- [ ] Query log retention set consciously.
- [ ] DDNS configured if — and only if — you have a public IP that something needs to find.
