# The Self-Hosting & Home Lab Guide

A comprehensive, opinionated, in-depth guide to the services worth self-hosting on a home lab — and everything around them: hardware, networking, storage, containers, reverse proxies, remote access, identity, backups, monitoring, security, and operations.

## Read it

- **Web version:** `docs/` — served by GitHub Pages at `https://gorg667.github.io/self-host-guide/` once Pages is enabled (Settings → Pages → Deploy from branch → `main` → `/docs`).
- **Single-file Markdown:** [`SELF-HOSTING-GUIDE.md`](SELF-HOSTING-GUIDE.md)
- **Per-chapter Markdown sources:** [`guide/`](guide/)

## Structure

| Part | Chapters | Content |
|---|---|---|
| I — Foundations | 00–06 | Planning, hardware, networking, OS & hypervisors, containers, storage |
| II — Core infrastructure | 07–13 | Reverse proxy & TLS, remote access/VPN, DNS & ad-blocking, identity/SSO, backups, monitoring, security |
| III — Application services | 14–26 | Category-by-category reviews: dashboards, media, photos, files, notes, home automation, communication, passwords, dev tools, AI/LLM, gaming, misc, databases |
| IV — Operations & reference | 27–34 | IaC, maintenance, power & cost, legal/ethical, reference architectures, troubleshooting, community, appendix |

## Build

```bash
pip install markdown pymdown-extensions
python3 build.py        # regenerates SELF-HOSTING-GUIDE.md and docs/
```

The build has no network dependency. `docs/` is committed so the site is live immediately after push.

## Contributing / status

All 35 chapters are complete (~125,000 words). Corrections and updates are welcome as issues or pull requests; see [`AGENT_NOTES.md`](AGENT_NOTES.md) for the chapter list, writing conventions and build notes.

## Licence

Text: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Build tooling (`build.py`, `site/`): MIT.
