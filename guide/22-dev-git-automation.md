# Developer Tools, Git Hosting, and Automation

A home lab is also a development environment: a place to keep your code, run CI, host container images, spin up a browser-based IDE, manage the containers themselves, and glue services together with workflow automation. This chapter covers Git hosting (Gitea, Forgejo, GitLab, OneDev, Gogs), CI/CD (Gitea/Forgejo Actions, Woodpecker, Drone, Jenkins), container registries (Harbor, the Distribution registry, Zot, Gitea's built-in), remote development (code-server, Coder, Gitpod's successors, JupyterHub), container and stack management UIs (Portainer, Dockge, Komodo, Arcane), workflow automation (n8n, Windmill, Activepieces, Node-RED, Huginn), and the grab-bag of developer utilities (IT-Tools, Cyberchef, pastebins, URL shorteners) that earn a place on every lab.

## Git hosting

### Gitea and Forgejo

**Gitea** is a lightweight, single-binary Go Git server with a GitHub-like UI: repositories, issues, pull requests, wikis, projects/kanban, organisations and teams, webhooks, **Gitea Actions** (a GitHub Actions-compatible CI runner — most GitHub workflow files run unchanged), a **package registry** (Docker/OCI, npm, PyPI, Maven, NuGet, Cargo, Helm, Debian/RPM, generic, and more), OIDC/LDAP login, SSH and HTTPS access, mirroring (pull and push), and migration from GitHub/GitLab/Bitbucket. ~100–300 MB RAM with SQLite; Postgres/MySQL for larger installs.

**Forgejo** is the **community fork** of Gitea, created in late 2022 by Codeberg e.V. and contributors after Gitea's maintainers formed a for-profit company (Gitea Ltd.) and took ownership of the domain and trademark. Forgejo is a **hard fork** since 2024 (no longer tracking Gitea commit-for-commit), governed by a non-profit, with a focus on **federation** (ActivityPub/ForgeFed — in progress), a stricter release process, and a commitment to remaining copyleft (it moved to GPLv3+ for new contributions). Feature-wise the two remain very close; Forgejo powers **Codeberg**, the largest non-profit Git host. Forgejo Actions is compatible with Gitea Actions and GitHub Actions syntax.

**Pick Forgejo if** governance and community ownership matter to you (the guide's lean). **Pick Gitea if** you want the larger commercial ecosystem and slightly faster feature velocity. Either is the right Git server for a home lab; migration between them is straightforward for now, harder as they diverge.

```yaml
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:11
    container_name: forgejo
    restart: unless-stopped
    environment:
      USER_UID: "1000"
      USER_GID: "1000"
      FORGEJO__server__ROOT_URL: https://git.example.com/
      FORGEJO__server__SSH_DOMAIN: git.example.com
      FORGEJO__server__SSH_PORT: "2222"
      FORGEJO__service__DISABLE_REGISTRATION: "true"
      FORGEJO__actions__ENABLED: "true"
    volumes:
      - ./data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "2222:22"                      # SSH for git; publish on the host; or use an SSH passthrough
    networks: [proxy, default]
  runner:
    image: code.forgejo.org/forgejo/runner:6
    container_name: forgejo-runner
    restart: unless-stopped
    depends_on: [forgejo]
    volumes:
      - ./runner:/data
      - /var/run/docker.sock:/var/run/docker.sock   # runner needs Docker to run job containers (DinD alternative exists)
    command: forgejo-runner daemon
    networks: [default]
    # register once: docker compose exec runner forgejo-runner register --instance https://git.example.com --token <token from Site Administration → Actions → Runners>
```

### GitLab

The **full DevOps platform**: everything Gitea does plus a far deeper CI/CD system (pipelines, environments, review apps, auto-DevOps), a container registry, package registries, security scanning (some Premium/Ultimate), Kubernetes integration, wikis, issue boards, epics (paid), and an enormous feature surface. **GitLab CE** (Community Edition, MIT) is free and self-hostable via the Omnibus package or a Docker image; **it wants 4–8 GB of RAM** and a few cores at idle, starts slowly, and its monthly releases need attention. If you use GitLab at work and want to mirror it at home, or you want the most powerful CI available, run it; for a household's personal projects, it is a battleship where a dinghy would do.

### OneDev

A single-container Java Git server with a distinctive feature set: **CI/CD with a visual pipeline editor** (no YAML required, though YAML is available), code search with symbol navigation, issue tracking with custom fields and boards, code review, package registry, Kanban, and SSO. Around 500 MB–1 GB RAM. Quietly excellent, especially for people who dislike YAML-driven CI; a much smaller community than Gitea/Forgejo.

### Gogs, Soft Serve, Gitolite, and the tiny ones

**Gogs** is the project Gitea forked from in 2016; still maintained by one developer, minimal, fine for a personal server with no CI. **Soft Serve** (Charm) is a **TUI-first** Git server over SSH — beautiful, minimal, no web UI. **Gitolite** is pure access control over SSH for people who want *only* Git with authorised keys. **cgit**/**gitweb**/**Klaus** are read-only web viewers over bare repositories. Bare repos on a server with SSH (`git init --bare`) and no software at all is a perfectly valid personal Git host — many people run exactly that plus Forgejo for the projects that want issues.

### Comparison

| | Forgejo / Gitea | GitLab CE | OneDev | Bare repos over SSH |
|---|---|---|---|---|
| RAM | ~150–300 MB | **4–8 GB** | ~700 MB | ~0 |
| CI | Actions (GitHub-syntax) | **GitLab CI (deepest)** | Visual + YAML | External |
| Package/container registry | **Yes (many formats)** | Yes | Yes | No |
| Issues / PRs / wiki | Yes | Yes (richer) | Yes | No |
| SSO | OIDC/LDAP | OIDC/LDAP/SAML | OIDC/LDAP | n/a |
| Mirroring GitHub repos | **Yes (pull mirror)** | Yes | Yes | Manual |
| Governance | Non-profit (Forgejo) / company (Gitea) | Company | One developer | n/a |
| Best for | Most home labs | GitLab-at-work people; heavy CI | YAML-averse CI fans | Minimalists |

**Use case: mirror your GitHub.** Whatever you choose, set up pull mirrors of every GitHub/GitLab repository you care about (yours and the open-source projects you depend on). A code-hosting outage or an account suspension then costs you nothing, and your lab's Compose files, dotfiles, and documentation have a home you own.

## CI/CD

- **Forgejo Actions / Gitea Actions** — built into the Git server; register a runner (one container with Docker access), write `.forgejo/workflows/*.yml` in GitHub Actions syntax, and most GitHub marketplace actions work (fetched from GitHub, or mirror them). **The default** if you run Forgejo/Gitea: nothing extra to operate.
- **Woodpecker CI** — a lightweight, container-native CI (a community fork of Drone before Drone went proprietary): pipelines as YAML, each step a container, plugins, multi-server agents, integrates with Gitea/Forgejo/GitLab/GitHub. Simple and pleasant; the choice if you want CI *separate* from the forge or dislike the Actions model.
- **Drone** — the original; the OSS edition has limits and the project was acquired by Harness; Woodpecker is its spiritual continuation.
- **Jenkins** — the ancient, infinitely pluggable Java CI. Runs anything, looks like 2010, requires babysitting. Run it to learn it for work; not for joy.
- **GitLab CI** — the deepest and most polished, if you run GitLab.
- **Concourse**, **Buildbot**, **Argo Workflows** and **Tekton** (Kubernetes-native) — niche at home.

Typical home-lab CI jobs: build and push your custom Docker images to your registry on a schedule; lint and validate Compose files and Ansible playbooks on every commit; run Renovate; build a static site (Hugo/Astro) and deploy it; run backups or scripts with a visible log. It is also a fine place to learn CI for professional purposes.

## Container registries

You need one when you build your own images, mirror upstream images to escape Docker Hub rate limits, or want a pull-through cache so twenty containers pulling `postgres:17` hit the internet once.

- **Forgejo/Gitea's built-in registry** — already there; `docker push git.example.com/user/image:tag`. Sufficient for most.
- **Distribution (the CNCF `registry:2`/`registry:3` image)** — the reference registry: tiny, no UI, supports **pull-through cache mode** (`proxy.remoteurl: https://registry-1.docker.io`) — point Docker's `registry-mirrors` at it and every Hub pull is cached locally. Pair with a UI (**Joxit's docker-registry-ui**) if you want to browse.
- **Harbor** — the enterprise registry: projects, RBAC, vulnerability scanning (Trivy built in), image signing (Cosign/Notation), replication between registries, proxy cache projects, retention policies, OIDC, and a full UI. Several containers, ~2 GB RAM. **Pick it if** you want scanning and a proper UI — it is excellent, and heavy.
- **Zot** — a minimal OCI-native registry (CNCF) with optional UI, scanning, and sync; lighter than Harbor.
- **Nexus Repository OSS** and **Artifactory OSS** — universal artefact repositories (Maven, npm, Docker, apt…); Nexus OSS is heavy but useful if you need many formats in one place.
- **Spegel** (Kubernetes P2P image cache), **Kraken** — cluster-scale only.

## Remote development

- **code-server** (Coder's open-source VS Code in the browser) — run VS Code on your server, open it in any browser (an iPad, a Chromebook, a locked-down work laptop), with extensions from Open VSX, terminals on the server, and your projects where the compute and data are. One container per user/workspace. Put it behind forward-auth ([Chapter 10](10-identity-sso.md)) — it is a shell on your server.
- **VS Code Remote-SSH / Tunnels** — no server software: VS Code on your laptop connects over SSH (or Microsoft's tunnel service) to the box and runs its server component there. For most individuals this is *better* than code-server (native client, all extensions) and needs only SSH. **Remote Tunnels** work through Microsoft's relay without any port forwarding.
- **Coder** — the platform version: workspaces defined with Terraform templates (Docker, Kubernetes, VMs), per-user provisioning, OIDC, dotfiles, multiple IDEs (VS Code, JetBrains Gateway, Jupyter, terminal). For a team or someone who wants disposable dev environments on demand; heavier than code-server.
- **DevPod** (client-side, spins up devcontainers on any backend including your Docker host), **Gitpod** (went hosted-only; its self-hosted successor is **Gitpod Flex**/**Ona** — enterprise), **Eclipse Che** (Kubernetes, heavy), **JupyterHub/JupyterLab** (notebooks; multi-user via JupyterHub; the data-science standard), **Theia**, **Zed**/**Neovim** over SSH with **tmux** (the terminal purist's answer, and a very good one).
- **Devcontainers** (`.devcontainer/devcontainer.json`) in your repos let VS Code — local or remote — build the exact toolchain in a container; combine with Remote-SSH to your Docker host for reproducible environments without polluting anything.

## Managing Docker itself

Introduced in [Chapter 5](05-containers.md); the fuller picture:

- **Dockge** — Compose-file-centric, one host (or an agent per host in newer versions), edits the YAML on disk, converts `docker run` to Compose, streams logs, tiny. **The recommendation for a single Docker host** for people who want a UI without abstraction.
- **Portainer CE** — the full manager: containers, images, volumes, networks, stacks, users/teams/RBAC, multiple environments (Docker, Swarm, Kubernetes, remote agents), templates, GitOps stack deployment from a repo. Heavier; stores stack YAML in its own DB unless Git-backed; the Business Edition nags. **The recommendation for several hosts** or when RBAC for other people matters.
- **Komodo** — a Rust platform for managing servers, stacks, builds, and deployments across many hosts, with Git-backed resource definitions (everything is a TOML "resource" that can be synced from a repo), periphery agents per host, alerting, and a fast UI. The GitOps-flavoured successor many people move to from Portainer once they have three or more hosts and want configuration in Git. **Watch this one**; it has matured quickly.
- **Arcane**, **Dockhand**, **Yacht**, **Dweebui**, **Cosmos** (a whole platform — [Chapter 4](04-os-and-hypervisors.md)), **Lazydocker** (terminal), **ctop** (terminal `top` for containers), **dive** (inspect image layers), **Watchtower/Diun** (updates — [Chapter 5](05-containers.md)), **What's Up Docker (WUD)** (update notifications with a UI and trigger actions).
- **Ansible**, **Terraform/OpenTofu**, **NixOS** — the code-first alternatives to any UI ([Chapter 27](27-automation-iac.md)).

## Workflow automation

The "if this then that" layer: connect APIs, react to webhooks, schedule jobs, transform data, glue services that were never meant to talk.

- **n8n** — the most popular self-hosted automation platform: a visual node-based editor, 400+ integrations, HTTP/webhook/cron triggers, JavaScript/Python code nodes, AI/LLM nodes (agents, vector stores, Ollama/OpenAI), sub-workflows, error handling, credentials management, and a huge template library. Node + SQLite/Postgres, ~500 MB. **Licence: Sustainable Use Licence** (source-available, free for internal/personal use, restrictions on offering it as a service) — not OSI open source; fine for a home lab. **The recommendation** for most people.
- **Activepieces** — an MIT-licensed, Zapier-like alternative with a friendlier no-code UI, hundreds of "pieces" (integrations), AI steps, and a TypeScript framework for custom pieces. Lighter on power users' features than n8n; genuinely open source. **The recommendation if licensing purity matters** or for non-developers.
- **Windmill** — a developer-oriented platform: write scripts in Python/TypeScript/Go/Bash/SQL, compose them into flows with a visual editor, auto-generate UIs and forms, schedule, and get observability — "internal tools + workflows + jobs" in one. AGPL core. Excellent for people who would rather write a function than drag nodes.
- **Node-RED** — the IoT/home-automation flow tool ([Chapter 19](19-home-automation.md)); also fine for general webhook glue; weaker on SaaS integrations.
- **Huginn** (the Ruby veteran — "agents" that watch and act; still maintained, dated UI), **Automatisch**, **Trigger.dev** (developer background jobs), **Kestra** (data-orchestration-flavoured), **Apache Airflow / Prefect / Dagster** (data pipelines — heavy, for people who do data engineering), **Cronicle** (a cron replacement with a UI and multi-server support — the answer to "I want to see my cron jobs"), **Healthchecks** for making sure they ran ([Chapter 12](12-monitoring.md)), **Ofelia** (cron for Docker containers via labels).

Typical lab automations: "when Sonarr imports an episode, post to the family Matrix room"; "every night, dump databases and ping Healthchecks"; "when a GitHub release appears for X, open an issue in Forgejo"; "when the doorbell rings, snapshot Frigate and send to ntfy"; "parse incoming invoices from email into Paperless and Firefly III"; "summarise my RSS unread with a local LLM each morning."

## Utilities every lab ends up with

- **IT-Tools** — a single static page with ~100 developer utilities: base64, JWT decoder, hash generators, UUID, cron parser, chmod calculator, Docker run → Compose converter, colour picker, QR codes, regex tester… Zero backend. Replaces a dozen ad-laden websites.
- **CyberChef** — GCHQ's "cyber Swiss Army knife" for data transformation and analysis; also a static page.
- **Pastebins**: **PrivateBin** (zero-knowledge, E2EE, burn-after-reading — the standard), **Microbin**, **Opengist** (Gist clone with Git backing), **Hastebin**, **Wastebin**, **rustypaste**.
- **URL shorteners**: **Shlink** (full-featured with analytics and API), **Kutt**, **YOURLS** (the PHP classic), **Dub** (self-hostable, marketing-oriented), **Chhoto URL** (tiny).
- **Diagramming**: **Excalidraw** (self-hostable whiteboard, wonderful), **draw.io/diagrams.net** (self-hosted container), **Kroki** (text-to-diagram server for Mermaid/PlantUML/Graphviz/D2), **PlantUML server**, **tldraw**.
- **Speed/latency**: **LibreSpeed** (a self-hosted speed test — measure LAN and VPN throughput to your server, not to the internet), **OpenSpeedTest**.
- **API/HTTP**: **Hoppscotch** (a Postman alternative; self-hostable), **Bruno** (local-first client, no server), **Webhook.site** alternatives (**webhook-tester**, **Requestbin** clones), **Mockoon**.
- **Docs and static sites**: **Hugo**, **Astro**, **MkDocs Material**, **Docusaurus** built by CI and served by Caddy/Nginx ([Chapter 25](25-misc-apps.md)).
- **Databases and admin tools**: [Chapter 26](26-databases-backing-services.md).

## Recommendations

- **Git:** Forgejo (or Gitea) with Actions enabled and a runner; pull-mirror everything you depend on from GitHub.
- **CI:** Forgejo Actions; Woodpecker if you want it separate.
- **Registry:** Forgejo's built-in for your images + a `registry:2` pull-through cache for Docker Hub.
- **Remote dev:** VS Code Remote-SSH/Tunnels first; code-server behind forward-auth for browser-only devices; Coder for a team.
- **Docker UI:** Dockge (one host), Komodo or Portainer (several).
- **Automation:** n8n (or Activepieces for pure open source; Windmill for code-first); Cronicle for visible scheduled jobs; Healthchecks to prove they ran.
- **Utilities:** IT-Tools, PrivateBin, Excalidraw, LibreSpeed — all trivial to run and used weekly.

## Checklist

- [ ] Forgejo/Gitea running; registration disabled; SSH on a non-22 host port or via passthrough; OIDC login; backups of `data/` (`forgejo dump` produces a consistent archive).
- [ ] Pull mirrors of your GitHub repos and critical upstream projects.
- [ ] A CI runner registered with Docker access; at least one workflow (lint your Compose files) running.
- [ ] Pull-through registry cache configured in `daemon.json` (`registry-mirrors`) on every Docker host.
- [ ] code-server (if used) behind forward-auth or VPN-only — it is a shell.
- [ ] Docker management UI (Dockge/Komodo/Portainer) restricted to LAN/VPN with auth; socket access via a proxy where possible.
- [ ] n8n/Activepieces/Windmill credentials stored in its encrypted credential store; its database backed up (workflows are precious).
- [ ] Every scheduled automation reports to Healthchecks/Uptime Kuma.
