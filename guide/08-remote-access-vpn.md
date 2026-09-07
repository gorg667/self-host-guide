# Remote Access and VPNs

You will want to reach your home lab from outside the house: your photos from a hotel, your password vault from work, your media on a train. There are two fundamentally different ways to do this. **Expose** the service to the internet — forward a port, put it behind the reverse proxy, let anyone connect and rely on authentication. Or **tunnel** into your network — a VPN that makes your phone or laptop a member of your LAN, after which everything works as if you were home and nothing is exposed at all. This chapter argues for the second, explains the technologies (WireGuard, Tailscale and Headscale, NetBird, ZeroTier, OpenVPN, IPsec), covers the tunnel-through-a-relay options (Cloudflare Tunnel, Pangolin, a VPS with WireGuard) for CGNAT and public services, and gives a decision framework.

## The two models

```mermaid
flowchart TB
    subgraph expose["Model 1: Expose"]
        I1((Internet)) -->|"443 forwarded"| RP[Reverse proxy + auth] --> S1[Services]
    end
    subgraph tunnel["Model 2: Tunnel"]
        Phone[Your phone] -->|"encrypted tunnel"| VPN[VPN endpoint] --> LAN[Entire LAN<br/>as if at home]
    end
```

**Exposing** is right when the audience is people you cannot ask to install a VPN client: a public blog, a Jellyfin server for extended family, a Nextcloud share link for a colleague, a game server for friends. It costs you an attack surface that must be patched, monitored, and defended forever.

**Tunnelling** is right for *you and your household* — the people who own devices you can configure. It costs an app on each device and ten minutes of setup, and exposes nothing. Since 2020 or so, mesh VPNs (Tailscale first, then others) have made it so easy that the calculus has shifted decisively: **the default should be a mesh VPN, with public exposure reserved for the few services that genuinely need it.**

Most labs end up with both — a mesh VPN for personal access to everything, plus one or two services exposed via the reverse proxy for other people. That is a healthy pattern.

## WireGuard: the protocol underneath

WireGuard is a VPN protocol and kernel module (in Linux since 5.6, with userspace implementations everywhere else) designed around simplicity: about 4,000 lines of code versus OpenVPN's 100,000+, a single modern cipher suite (ChaCha20-Poly1305, Curve25519, BLAKE2s), UDP only, and a configuration model based purely on public keys. Each peer has a key pair; you tell each side the other's public key and which IP ranges to route through the tunnel. Handshakes take one round trip; roaming between networks is seamless; throughput is near line rate on modest hardware; a Raspberry Pi 4 pushes 300–500 Mbps. It is the foundation of every mesh VPN below, and the right protocol for anything new.

### Plain WireGuard (self-hosted, hub-and-spoke)

The classic setup: a WireGuard server on your router (OPNsense, OpenWrt, MikroTik, UniFi all have it built in) or on a Linux box, a UDP port forwarded to it (51820 by convention; any port works), and a config per client device. Clients connect to your public IP (via a dynamic DNS name), get an address in a tunnel subnet (`10.8.0.0/24`), and route your LAN (`10.0.0.0/16`) — or all traffic (`0.0.0.0/0`, for a privacy VPN when on hotel Wi-Fi) — through the tunnel.

**Requires:** a public IP (dynamic is fine with DDNS) and one forwarded UDP port. Does not work behind CGNAT without a relay.

**Strengths:** no third party at all, no coordination server, no accounts. Runs on hardware you already have. Trivially auditable. The forwarded UDP port is close to invisible — WireGuard does not respond to unauthenticated packets, so a port scan sees nothing.

**Weaknesses:** manual key and config management per device (tooling below helps). Hub-and-spoke: all traffic between two remote clients goes via the hub. No NAT traversal — the server needs a reachable port. Changing the server IP or key means touching every client.

**Tooling:** **wg-easy** (a Docker container with a web UI to create clients and show QR codes; the easiest self-hosted WireGuard), **WGDashboard**, **Firezone** (a more complete product with SSO, now pivoted toward a zero-trust model), the built-in UIs on OPNsense/OpenWrt/UniFi/MikroTik, and **PiVPN** (a script for Raspberry Pi that sets up WireGuard or OpenVPN).

```yaml
services:
  wg-easy:
    image: ghcr.io/wg-easy/wg-easy:15
    container_name: wg-easy
    restart: unless-stopped
    environment:
      INIT_ENABLED: "true"
      INIT_HOST: vpn.example.com          # your DDNS name
      INIT_PORT: "51820"
      INIT_DNS: 10.0.20.5                 # your Pi-hole/AdGuard
      INIT_IPV4_CIDR: 10.8.0.0/24
    volumes:
      - ./data:/etc/wireguard
      - /lib/modules:/lib/modules:ro
    ports:
      - "51820:51820/udp"                 # forward this on the router
      - "127.0.0.1:51821:51821/tcp"       # web UI, LAN/proxy only
    cap_add: [NET_ADMIN, SYS_MODULE]
    sysctls:
      net.ipv4.ip_forward: 1
      net.ipv4.conf.all.src_valid_mark: 1
```

## Mesh VPNs

A mesh VPN adds a **coordination (control) server** to WireGuard. Every device authenticates to the control server, which distributes public keys and endpoint information; devices then connect **directly to each other** (peer to peer) wherever NAT traversal permits, falling back to **relay servers** (DERP in Tailscale's terminology, TURN in NetBird's) when it does not. The control server never sees your traffic — only keys and metadata. Results: no port forwarding, works behind CGNAT and hotel Wi-Fi and cellular, every device can reach every other device, and adding a device is "install the app and log in."

### Tailscale

The product that defined the category. A Tailscale client on each device (Linux, Windows, macOS, iOS, Android, Synology, QNAP, pfSense/OPNsense, Unraid, Home Assistant, Docker, even Apple TV), a hosted control plane at Tailscale Inc., login via an existing identity provider (Google, Microsoft, GitHub, Apple, or any OIDC). Free tier: 100 devices and 3 users, which covers most households. Features that matter for self-hosters:

- **MagicDNS**: every device gets a name (`nas.tailnet-name.ts.net`) and Tailscale-provided DNS for them.
- **Subnet routers**: one device advertises your LAN (`10.0.0.0/16`) so that devices *without* Tailscale (your TV, printer, IoT) are reachable through it. Your phone can reach `10.0.20.5` from anywhere.
- **Exit nodes**: route all internet traffic through a device at home (or a VPS) — a privacy VPN for hotel Wi-Fi.
- **ACLs**: a JSON policy defining which users/devices/tags may reach which others. Give your partner's phone access to Immich and Jellyfin, not the Proxmox UI.
- **Tailscale SSH**: SSH between devices authenticated by Tailscale identity, no keys to manage.
- **Funnel**: expose a service on a device to the public internet through Tailscale's relays (with TLS) — a quick way to make one thing public without touching your router.
- **Tailscale Serve** and **HTTPS certificates** for `*.ts.net` names.
- **Split DNS**: tell Tailscale that `example.com` should resolve via your Pi-hole at `10.0.20.5` — so your split-horizon DNS ([Chapter 7](07-reverse-proxy-tls.md)) works remotely and `photos.example.com` resolves to your internal proxy from anywhere.
- **Mullvad exit nodes** (paid add-on), **Taildrop** (file transfer between your devices), **Tailscale on Docker** (a sidecar container that puts a single service on the tailnet).

**Watch out for:** the control plane is a third-party SaaS. Tailscale cannot read your traffic (it never has the private keys and traffic goes peer-to-peer or through DERP encrypted end-to-end), but it knows your device list, IPs, and connection metadata, and if Tailscale's control plane is down, *new* connections cannot be established (existing ones keep working via cached keys). Pricing and free-tier limits could change (they have been stable and were made more generous in 2023). If a hard dependency on a company is unacceptable, see Headscale.

### Headscale

An open-source reimplementation of Tailscale's *control server*, run on your own machine. The official Tailscale clients connect to it instead of Tailscale Inc. You get most of the Tailscale experience — MagicDNS, subnet routers, exit nodes, ACLs, split DNS — with no third party, no device limits, no account required. It needs a **publicly reachable host** for the control server (a small VPS is ideal; it can be at home if you have a public IP and forward a port), because clients must reach it to coordinate. Relaying uses Tailscale's public DERP servers by default (you can run your own embedded DERP in Headscale).

**Watch out for:** it is a community project tracking a proprietary protocol; occasional client updates break things until Headscale catches up (rarer now — Tailscale has been cooperative). No web UI officially (community UIs exist: headscale-ui, headplane, headscale-admin). Login is via pre-auth keys or your own OIDC provider ([Chapter 10](10-identity-sso.md)). Missing a few Tailscale features (Funnel, some newer ACL features). Operating a control server is a small but real responsibility.

**Pick Headscale if:** you want Tailscale's polish with full sovereignty and are willing to run one more service on a VPS.

### NetBird

An open-source mesh VPN (management server, signal server, relay, and clients all open, AGPL/BSD) with a hosted option and a straightforward self-hosting path (a Docker Compose stack). WireGuard underneath, peer-to-peer with relay fallback, a full web UI, SSO via any OIDC provider (Zitadel bundled by default in the self-hosted quick start, or bring your own — Authentik, Keycloak, Pocket ID), ACLs with groups and posture checks, DNS management, subnet routing, exit nodes, and a clean client for every platform including Docker. It is the closest **fully open, self-hostable, UI-driven** equivalent to Tailscale, and has been growing steadily.

**Watch out for:** self-hosting involves several components (management, signal, relay/TURN, dashboard, an IdP) and needs a public host with a handful of ports open; the quick-start script handles it but you are running more moving parts than Headscale. Younger than Tailscale; occasional rough edges on iOS/macOS.

**Pick NetBird if:** you want a self-hosted mesh with a real web UI and SSO integration out of the box, or you want an open-source hosted option.

### ZeroTier

The elder statesman of mesh networking (2015). Different architecture: it builds a virtual **layer 2** Ethernet network rather than a layer 3 IP mesh, with its own protocol (not WireGuard), which makes it uniquely good at things like broadcast/multicast across the mesh (Chromecast discovery, some games, mDNS). Hosted controller with a free tier (10 devices as of the 2023 pricing change, down from 25/50), a self-hostable controller (via the open-source `ztncui` or ZeroNSD tooling), a very mature client on every platform including many routers (MikroTik has it built in). Licence is a BSL (Business Source Licence) — source-available with a non-compete clause, converting to Apache after four years.

**Watch out for:** the smaller free tier makes it less attractive than Tailscale for households; performance and NAT traversal are good but generally a step behind WireGuard-based options; the self-hosted controller is less turnkey than Headscale/NetBird.

**Pick ZeroTier if:** you need layer 2 (bridging two sites into one broadcast domain, or an application that requires it), or you have MikroTik gear and want it native.

### Others

**Netmaker** (WireGuard mesh with a UI, pivoted toward enterprise; the community edition is fine but has moved features to paid tiers), **Innernet** (a minimal WireGuard coordinator in Rust, CLI-only), **Nebula** (Slack's overlay network; certificate-based, no central controller at runtime, excellent for people who want to understand every part; used for the Defined Networking product), **Tinc** (an old and still-working mesh), **Husarnet**, **Twingate** and **Cloudflare WARP/Zero Trust** (hosted zero-trust access products with free tiers; corporate-flavoured), **Firezone** (WireGuard-based, open-source, now zero-trust-oriented with a hosted control plane and self-hosted gateways).

### Mesh VPN comparison

| | Tailscale | Headscale | NetBird | ZeroTier |
|---|---|---|---|---|
| Control plane | Hosted (Tailscale Inc.) | Self-hosted | Hosted or self-hosted | Hosted or self-hosted |
| Protocol | WireGuard | WireGuard (Tailscale clients) | WireGuard | Custom (L2) |
| Open source | Clients: yes (BSD); server: no | Yes (BSD) | Yes (AGPL/BSD) | BSL (source-available) |
| Free tier | 100 devices / 3 users | Unlimited | Hosted: 5 users/100 peers as of 2025; self-hosted unlimited | 10 devices |
| Web UI | Yes (excellent) | Community projects | Yes | Yes (hosted) |
| SSO/IdP | Google/MS/GitHub/Apple/OIDC | OIDC (your own) | OIDC (bundled Zitadel or your own) | Own accounts |
| Subnet router | Yes | Yes | Yes | Yes (managed routes) |
| Exit node | Yes | Yes | Yes | Yes (default route) |
| Split DNS | Yes | Yes | Yes | Via ZeroNSD |
| Public exposure | Funnel | No | No | No |
| Setup effort | Minutes | An hour (needs public host) | An hour (needs public host) | Minutes (hosted) |
| Best for | Most people | Tailscale without the company | Fully open with UI | Layer 2 needs |
