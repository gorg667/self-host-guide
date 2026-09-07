# Passwords, Secrets, and Two-Factor Codes

A password manager is the single most important piece of personal security software, and self-hosting it is one of the most popular first projects — the data is tiny, the value is enormous, and the idea of a company holding every credential you own is uncomfortable to many. This chapter reviews Vaultwarden (the community's overwhelming choice), the official Bitwarden server, Passbolt, Psono, and the file-based KeePass approach; covers TOTP/2FA code management (2FAuth, Ente Auth, Aegis backups); and then turns to *machine* secrets — the API keys, database passwords, and tokens that a lab accumulates — with Infisical, OpenBao, SOPS, and the pragmatic middle ground.

## First principles

- **The vault is the most irreplaceable and most sensitive data you have.** Back it up with more care than anything else ([Chapter 11](11-backups.md)); keep an *encrypted export* somewhere outside the lab (a USB stick in a safe, a printed emergency sheet for the master password and 2FA recovery codes); and protect the server as if losing it locks you out of everything — because it does.
- **Clients cache the vault**, so a server outage does not lock you out immediately — but new devices cannot enrol and changes cannot sync. Availability matters less than integrity.
- **Exposure**: the classic dilemma. A password manager needs to sync to your phone wherever you are. The options are a mesh VPN (nothing exposed; sync happens when the VPN is up — Bitwarden clients handle this gracefully) or exposing it behind the reverse proxy with the app's own strong auth (the Bitwarden protocol is well-hardened; Vaultwarden exposed with fail2ban/CrowdSec and admin panel disabled is a common, defensible setup). The guide's preference: **VPN-only, with the mobile client's cached vault covering the gaps.**
- **MFA on the vault itself** (TOTP, WebAuthn/passkey, Duo, email) is mandatory. Store *those* recovery codes somewhere that is not the vault.

## Password managers

### Vaultwarden

An unofficial, **Rust** reimplementation of the Bitwarden server API, compatible with every official Bitwarden client (browser extensions, desktop, iOS, Android, CLI) and providing nearly every feature — including ones Bitwarden puts behind its paid tiers: organisations and collections (shared vaults for the household), **passkey storage**, TOTP authenticator in the vault, emergency access, Send (encrypted text/file sharing), attachments, WebAuthn/YubiKey/Duo 2FA, and an admin panel. Single binary + SQLite (or Postgres/MySQL), ~20–50 MB RAM, one container. It has been the community standard since 2018 (as bitwarden_rs), is actively maintained with a large contributor base, and receives security attention proportional to its popularity. **SSO/OIDC login** landed in 2025 via a long-running fork merged upstream.

**Watch out for:** it is *not* Bitwarden's code — Bitwarden Inc. neither supports nor audits it; the client apps occasionally ship features before Vaultwarden implements them (usually a week or two of lag, sometimes a broken feature until the next release — pin the version and read release notes); the admin panel must be protected or disabled (`ADMIN_TOKEN` as an Argon2 hash, and never exposed publicly); disable signups after creating your accounts (`SIGNUPS_ALLOWED=false`), or restrict by domain; **back up the SQLite database with `sqlite3 .backup`**, not a file copy, plus the `attachments/` and `sends/` directories and the `rsa_key*` files (the JWT signing keys — losing them logs everyone out). Icons are fetched from the internet by default (a privacy leak of which sites you have accounts on) — set `ICON_SERVICE=internal` or disable.

```yaml
services:
  vaultwarden:
    image: vaultwarden/server:1.34.1
    container_name: vaultwarden
    restart: unless-stopped
    environment:
      DOMAIN: https://vault.example.com
      SIGNUPS_ALLOWED: "false"
      INVITATIONS_ALLOWED: "true"
      ADMIN_TOKEN: ${VW_ADMIN_TOKEN_ARGON2}     # generate with: vaultwarden hash  (or disable admin entirely by omitting)
      SHOW_PASSWORD_HINT: "false"
      ICON_SERVICE: internal
      PUSH_ENABLED: "true"                      # mobile push via Bitwarden's relay; needs PUSH_INSTALLATION_ID/KEY from bitwarden.com/host
      PUSH_INSTALLATION_ID: ${VW_PUSH_ID}
      PUSH_INSTALLATION_KEY: ${VW_PUSH_KEY}
      SMTP_HOST: smtp.example.com
      SMTP_FROM: vault@example.com
      SMTP_USERNAME: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASS}
      LOG_FILE: /data/vaultwarden.log          # for fail2ban/CrowdSec
    volumes:
      - ./data:/data
    networks: [proxy]
    security_opt: [no-new-privileges:true]
```

**Verdict:** the recommendation for almost everyone. Tiny, complete, mature, and it unlocks the entire polished Bitwarden client ecosystem for free.

### Bitwarden (official self-hosted)

Bitwarden Inc. publishes its full server for self-hosting: the traditional deployment is ~11 containers (web, API, identity, SQL Server, nginx, admin, icons, notifications, events, attachments, MSSQL) at several GB of RAM; the newer **Bitwarden Unified** (beta since 2022, still labelled so) collapses it to one container with SQLite/Postgres/MySQL at ~500 MB. Features match the hosted product exactly; **paid features (organisations beyond the free tier, TOTP, emergency access, etc.) require a licence** — a personal Premium licence (USD 10/year) or a Families plan (USD 40/year) that you apply to the self-hosted instance. Official support and audits.

**Pick it if:** you want Bitwarden's own code and support, are willing to pay for the licence, and do not mind the heavier footprint. For a household, Vaultwarden's feature parity for free makes this a hard sell; for a small business wanting vendor support, it is the right choice.

### Passbolt

An open-source password manager **built for teams**: fine-grained sharing by user and group, folders, audit logs, an admin panel, LDAP/SSO (Pro), browser extensions and mobile apps, and — its distinctive design — **OpenPGP-based** end-to-end encryption where each user's private key lives in the browser extension. PHP + MariaDB + a mail relay (email is required for account setup). Community Edition is free and capable; Pro adds SSO, LDAP, and more. It is more "credential sharing for a company" than "personal vault," and its per-item PGP model makes it less convenient than Bitwarden for a household's everyday use. **Pick it if** you manage shared credentials for a team and want strong audit/sharing controls.

### Psono

An open-source enterprise password manager (Python + Postgres) with client-side encryption, sharing, groups, LDAP/SAML/OIDC (some Enterprise-only), browser extensions, mobile apps, and a "Community Edition" that is fully featured for up to 10 users. Solid, less known, a reasonable alternative to Passbolt for teams.

### KeePass (KeePassXC, KeePassDX, Strongbox) + sync

The **file-based** approach: a single encrypted `.kdbx` database file opened by a desktop client (**KeePassXC** — excellent, cross-platform, with browser integration, TOTP, SSH agent, passkeys), an Android client (**KeePassDX**, **Keepass2Android**), or an iOS client (**Strongbox** — polished, paid pro tier; **KeePassium**). There is *no server*: you sync the file with **Syncthing** ([Chapter 17](17-files-sync-documents.md)), Nextcloud/WebDAV, or any file sync. Zero attack surface, zero services to maintain, works fully offline, and the format is an open standard readable by dozens of tools for decades. The costs: sync conflicts if two devices edit simultaneously (KeePassXC merges databases; mobile clients handle it variably), no sharing model beyond "share the file," and no browser autofill as slick as Bitwarden's. **Pick it if** you want the minimum possible infrastructure, you are one person (or a couple with a shared file), and you value offline-first. Many people run KeePassXC *and* Vaultwarden — the former as a cold backup export of the latter.

### Others

**Padloc**, **Buttercup**, **Passky**, **Pass** (the Unix command-line manager — GPG-encrypted files in a Git repo; **passforios** and **Android Password Store** as clients; for terminal people), **gopass**, **Proton Pass / 1Password / Dashlane** (hosted; excellent; not self-hostable), **Nextcloud Passwords** (an app inside Nextcloud — decent, but why not Vaultwarden), **Teampass** (old PHP team manager; avoid).

### Comparison

| | Vaultwarden | Bitwarden (official) | Passbolt CE | KeePassXC + Syncthing |
|---|---|---|---|---|
| Server | 1 container, ~30 MB | 11 containers or Unified (~500 MB) | PHP + MariaDB + SMTP | **None** (file sync) |
| Clients | All official Bitwarden apps | All official Bitwarden apps | Extension + mobile | KeePassXC, KeePassDX, Strongbox, many |
| Sharing (household) | **Organisations, free** | Organisations (licence for >2 users) | Groups, granular | Share the file |
| Passkeys | Yes | Yes | Limited | Yes (KeePassXC) |
| TOTP in vault | **Yes, free** | Premium licence | Yes | Yes |
| 2FA on vault | TOTP, WebAuthn, Duo, email | Same | TOTP, YubiKey | n/a (file is the secret) |
| SSO | OIDC (2025+) | Enterprise licence | Pro | n/a |
| Audit / official support | Community | **Vendor** | Vendor (Pro) | n/a |
| Licence | AGPL | AGPL/BSL mix + licence keys | AGPL / Pro | GPL |
| Best for | Households; most people | Businesses wanting support | Teams sharing credentials | Minimalists; offline-first |

## Two-factor codes

Where do your TOTP seeds live? Options, from most to least convenient:

- **In the password manager** (Vaultwarden/Bitwarden's built-in authenticator, KeePassXC). Convenient — one app, autofill of the code. The criticism: it collapses two factors into one (whoever has your vault has both). The counter-argument: for most people the realistic threat is a phished password, not a compromised vault, and vault-with-MFA is still far better than SMS codes. A reasonable compromise: TOTP in the vault for everyday sites; a *separate* authenticator for the vault itself, your email, and your bank.
- **A dedicated authenticator app** with encrypted backups: **Aegis** (Android — open source, encrypted export, the best), **2FAS**, **Ente Auth** (open source, E2EE cross-device sync via Ente's service or your own self-hosted Ente server, Android/iOS/desktop — the best cross-platform choice), **Raivo** (iOS; acquired and enshittified in 2023 — migrate), **Bitwarden Authenticator** (standalone app, separate from the vault). Back the seeds up: an encrypted export stored with your other cold backups.
- **A self-hosted TOTP web app**: **2FAuth** (a clean PHP app that stores your seeds server-side with a web UI and PWA, import from Aegis/Google Authenticator/etc.) — useful as a household-shared or "any-device" authenticator; you are trusting your server with the seeds, so VPN-only.
- **Hardware keys** (YubiKey, Nitrokey, Google Titan, SoloKeys) for FIDO2/WebAuthn where supported — the strongest factor, phishing-resistant, no seeds to back up (but buy **two** and register both everywhere; a lost single key is a lockout). Also store TOTP seeds on the YubiKey via Yubico Authenticator if you like.

## Passkeys

Passkeys (FIDO2 credentials synced across devices) are replacing passwords on major sites. Where they live matters for self-hosters: **Vaultwarden/Bitwarden** store them in the vault (cross-platform, self-hosted, portable), **KeePassXC** too; Apple/Google/Microsoft platform passkeys are synced via their clouds. Storing passkeys in your self-hosted vault keeps them under your control and works on every OS — the recommendation. Your own services should *accept* passkeys via the IdP ([Chapter 10](10-identity-sso.md)).

## Machine secrets

A home lab accumulates hundreds of non-human secrets: database passwords, API tokens for Cloudflare and B2, SMTP credentials, OIDC client secrets, Restic repository keys, Home Assistant tokens. They end up in `.env` files. That is where most people should leave them — with discipline:

### The pragmatic baseline

- One `.env` per stack, `chmod 600`, owned by the deploying user, `.gitignore`d.
- `*_FILE` variables and Docker secrets where the image supports them ([Chapter 13](13-security.md)).
- A copy of every `.env` in the **password manager** (as a secure note attached to a "Homelab: stackname" entry) — so a lost host does not mean lost credentials, and so the vault's backup covers them.
- Scoped tokens; rotation when anything leaks.

### SOPS + age: secrets in Git

**SOPS** (Mozilla, now CNCF) encrypts *values* in YAML/JSON/`.env` files while leaving keys readable — you see `DB_PASSWORD: ENC[AES256_GCM,...]` and can diff the file meaningfully. Encryption keys: **age** (a small modern tool; one keypair per admin/host), GPG, or cloud KMS. Commit encrypted files; decrypt on deploy (`sops -d .env.enc > .env`, or `sops exec-env`). Integrates with Ansible (community.sops), Kubernetes (via Flux/Argo), NixOS (sops-nix, agenix), Komodo. **This is how you get a fully reproducible lab in Git *including* its secrets**, and the recommendation for anyone doing infrastructure-as-code ([Chapter 27](27-automation-iac.md)). `git-crypt` is the older whole-file alternative.

### Secrets managers

For labs that want a *service* to hold secrets, inject them at runtime, rotate them, and audit access:

- **Infisical** — a modern open-source secrets platform (Node + Postgres + Redis): projects/environments, a clean UI, a CLI (`infisical run -- docker compose up`, which injects secrets as env vars), SDKs, an agent, a Kubernetes operator, secret rotation, PKI/certificates, SSH CA, and audit logs. MIT-licensed core with an enterprise tier. The most approachable full secrets manager and the current community favourite.
- **OpenBao** — the Linux Foundation fork of **HashiCorp Vault** after its 2023 licence change (Vault itself is BSL; OpenBao is MPL). The enterprise standard: key/value secrets, dynamic database credentials, PKI, transit encryption, SSH CA, policies, audit. Powerful, complex, a real learning curve; single-node "dev" mode is fine at home. **Pick it if** you want to learn Vault for career reasons.
- **Bitwarden Secrets Manager** — a machine-secrets product alongside the password manager; free tier for personal use on the hosted service; Vaultwarden does not implement it.
- **Doppler**, **1Password Secrets Automation / Connect** — hosted; excellent; not self-hosted.
- **Teller**, **envchain**, **direnv** with encrypted files — lightweight CLI wrappers.

**Recommendation for machine secrets:** `.env` files with copies in Vaultwarden for Tier 1; **SOPS + age in Git** for anyone with their Compose files versioned (which should be everyone at Tier 2+); **Infisical** if you want a UI-driven manager with runtime injection; **OpenBao** to learn Vault.

## Backing up the vault (specifically)

- Nightly `sqlite3 /data/db.sqlite3 ".backup '/data/backups/db-$(date +%F).sqlite3'"` (Vaultwarden), plus `attachments/`, `sends/`, `rsa_key*`, and `config.json`, into the normal encrypted off-site backup.
- Monthly **encrypted JSON export** from a Bitwarden client (Settings → Export → password-protected) saved to cold storage. This is the format-independent recovery: it can be imported into *any* Bitwarden server, or into KeePassXC.
- A **printed emergency sheet**: master password (or a hint only you understand), 2FA recovery codes for the vault, the location of the export and its password. In a safe, a bank box, or with a trusted person. Bitwarden's **emergency access** feature (Vaultwarden supports it) lets a trusted contact request access after a waiting period — configure it for your partner.
- **Test**: restore the SQLite backup into a scratch Vaultwarden and log in. Import the JSON export into KeePassXC and open it. Once a year.

## Checklist

- [ ] Vaultwarden (or chosen manager) deployed; signups disabled; admin token hashed or admin disabled; icons internal.
- [ ] Every household member enrolled; shared credentials in an organisation collection; emergency access configured for partners.
- [ ] MFA on every vault account with recovery codes stored *outside* the vault; passkeys stored in the vault.
- [ ] Access via VPN (or exposed with CrowdSec/fail2ban reading its log, rate limits, and no admin panel); push notifications configured if desired.
- [ ] Vault DB backed up via `sqlite3 .backup` nightly + keys + attachments; monthly encrypted export in cold storage; printed emergency sheet exists; annual restore test.
- [ ] TOTP strategy decided (vault vs separate authenticator); authenticator seeds backed up encrypted; two hardware keys registered where FIDO2 is supported.
- [ ] Machine secrets: `.env` files `600` and gitignored with copies in the vault; SOPS+age for Git-managed configs; scoped tokens; rotation on leak.
