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
