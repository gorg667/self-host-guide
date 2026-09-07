# Introduction: What Self-Hosting Is and Why It Matters

Self-hosting means running the software services you rely on — file storage, photo libraries, media streaming, password managers, home automation, chat, notes, even AI assistants — on hardware you own and control, rather than renting them from a cloud provider. A *home lab* is the environment where you do it: anything from a single Raspberry Pi under the TV to a rack of second-hand enterprise servers in the garage.

This guide is a comprehensive, opinionated, and deliberately deep treatment of both halves of that sentence: the **services** worth self-hosting (with honest reviews and comparisons), and the **everything else** — hardware, networking, storage, containers, reverse proxies, remote access, identity, backups, monitoring, security, automation, power, and the operational discipline that separates a hobby that brings joy from one that becomes a second job.

## Why people self-host

The reasons people give tend to fall into a handful of clusters. You will probably recognise yourself in more than one.

### Privacy and data ownership

When your photos live on someone else's servers, they are subject to that company's terms of service, its scanning policies, its data-retention practices, its acquisitions, and its bankruptcies. When they live on a disk you own, behind encryption you control, none of that applies. This is the most commonly cited reason and it is a good one, but be honest about what you are buying: privacy from *third parties*, not security in any absolute sense. A misconfigured self-hosted service exposed to the internet is a far bigger privacy risk than a competently run cloud service. [Chapter 13](13-security.md) exists for exactly this reason.

### Cost

The economics are genuinely favourable for storage-heavy workloads. 2 TB of cloud storage costs on the order of USD 100–120 per year from mainstream providers; a 4 TB NAS-grade hard drive costs about the same *once*, and a modest mini PC to serve it costs USD 150–400 used. Over a five-year horizon, self-hosting media, photos, and files is cheaper for almost everyone, even after electricity and replacement drives.

The economics are *not* favourable for compute-light, expertise-heavy services. Running your own email server saves you perhaps USD 50 per year and costs you a dozen hours of setup plus recurring deliverability headaches. [Chapter 20](20-communication.md) discusses this candidly. Be realistic: your time has value, and the point of a home lab should be that you *enjoy* spending it.

### Learning

A home lab is the best IT education money can buy. Concepts that are abstract in a textbook — subnets and VLANs, TLS certificates, reverse proxies, ZFS, containers, backup strategy, identity providers — become concrete when you have to make them work at 11 pm because the family cannot watch a film. Many professional systems administrators, DevOps engineers, and SREs credit a home lab for their career, and for good reason: the skills transfer directly.

### Independence from vendor decisions

Services get discontinued (Google has a well-documented graveyard), features get moved behind paywalls, prices get raised, APIs get closed, and terms of service get changed unilaterally. A self-hosted stack built on open-source software cannot be taken away from you. Even when a project is abandoned, you keep the last working version and your data in an open format.

### Capability

Some things are simply not available as a service, or are available only in a hobbled form. Local AI inference on your own GPU with no per-token cost and no content filters. A media server with lossless audio and full-quality 4K HDR remuxes. Home automation that works when the internet is down. Network-wide ad blocking for every device including smart TVs. Object storage with no egress fees. These are things the cloud either cannot or will not sell you.

### Fun

Do not underestimate this one. Tinkering is intrinsically rewarding for a certain kind of person. If you are reading a guide this long, you are probably that kind of person.

## Who this guide is for

This guide is written for three audiences at once, and the structure is designed so that each can find their path.

**The beginner** who has heard about Plex or Home Assistant, has a spare laptop or is thinking about buying a mini PC, and wants to understand what they are getting into before they start. If that is you, read Part I (Foundations) in order. It will take a few hours and it will save you weeks.

**The intermediate self-hoster** who already runs a few Docker containers on a Synology or an Ubuntu box, has hit the limits of port-forwarding-and-hope, and wants to do things properly: a reverse proxy with real certificates, a VPN, a backup strategy that has actually been tested, monitoring that alerts before the family does. Part II (Core Infrastructure) is written for you.

**The experienced administrator** who knows all of that and wants a well-researched, current comparison of what to run for a given need — which photo manager, which notes app, which identity provider — with the trade-offs laid out honestly. Part III (Application Services) is a set of category reviews written for you, and Part IV (Operations) covers the discipline of keeping it all running.

## What this guide is not

It is not a step-by-step tutorial for any single piece of software. Upstream documentation does that better and stays current; we link to it. What we add is *judgement*: which tool to pick, why, what it will cost you in time and resources, and what will go wrong.

It is not neutral. Where there is a clear best choice for most people, the guide says so. Where the choice genuinely depends on your situation, the guide says that too and tells you which questions to ask yourself. Opinions are flagged as opinions.

It is not a substitute for reading the documentation of the software you deploy. Nothing is.

## The philosophy of a sustainable home lab

Twenty years of collective community experience — visible in every "I gave up on self-hosting" post and every "here is my lab five years later" retrospective — distils into a few principles. They are opinions, but they are widely held ones.

### Start small and grow deliberately

The single most common failure mode is over-building. Someone reads about Proxmox clusters and Ceph and 10 GbE and buys three servers before running a single service. Six months later the rack is drawing 400 W, half the services are broken because an update was never finished, and the whole thing gets sold at a loss.

Start with one machine. Run three or four services that you will actually use daily. Learn to back them up and restore them. *Then* expand. Every chapter in this guide has a "starter" option for a reason.

### Boring is good

For infrastructure, prefer mature, widely deployed, well-documented software with a large community. Debian over the newest distribution. Docker Compose over a bleeding-edge orchestrator. PostgreSQL over whatever database was announced last quarter. WireGuard over a novel VPN protocol. The excitement in a home lab should come from *what you do* with the platform, not from fighting the platform itself.

This is also why this guide is somewhat conservative in its recommendations. There is always a shinier alternative. Shiny tends to be less documented, less tested, and more likely to be abandoned.

### Everything fails; plan for it

Drives die. Power goes out. Updates break things. You will fat-finger `rm -rf` on the wrong directory eventually. A home lab that has not planned for these events is a time bomb, and the fuse is usually shorter than people expect.

The corollary is the single most important sentence in this guide: **a backup you have not restored from is not a backup.** [Chapter 11](11-backups.md) is long for a reason.

### Complexity is a cost

Every service you run is a thing that needs updating, monitoring, backing up, and eventually migrating. Every network segment is a set of firewall rules to maintain. Every layer of abstraction is a place a bug can hide. Add complexity only when the benefit clearly exceeds the ongoing cost — and periodically ask whether that is still true. Decommissioning a service you no longer use is one of the most valuable things you can do.

### Write it down

Your future self, six months from now, will not remember why port 8096 is forwarded or which container owns that Postgres database. Document your setup as you build it. Keep your configuration in Git. [Chapter 28](28-maintenance-operations.md) covers documentation and runbooks; [Chapter 27](27-automation-iac.md) covers keeping configuration as code so that the documentation *is* the deployment.

### Security is a process, not a product

No single tool makes you secure. A reasonable posture for a home lab is: don't expose things to the internet unless you must; when you must, put them behind a reverse proxy with TLS and preferably authentication; keep software updated; segment your network so that a compromised IoT device cannot reach your NAS; and have backups that a ransomware event cannot reach. [Chapter 13](13-security.md) expands on each of these.

## How the guide is structured

The guide is organised into four parts and thirty-five chapters. Each chapter is self-contained enough to be read alone, with cross-references where concepts depend on each other.

**Part I — Foundations** (Chapters 0–6) covers the decisions you make before running a single service: what you want to achieve, what hardware to buy, how to lay out your network, which operating system or hypervisor to run, how containers work and why they matter, and how to store data safely.

**Part II — Core infrastructure** (Chapters 7–13) covers the services that every other service depends on: reverse proxies and TLS certificates, remote access and VPNs, DNS and ad-blocking, identity and single sign-on, backups, monitoring and alerting, and security.

**Part III — Application services** (Chapters 14–26) is the review section. Each chapter takes a category — media, photos, files, notes, home automation, communication, passwords, development tools, AI, gaming, and more — and compares the leading self-hostable options with recommendations.

**Part IV — Operations and reference** (Chapters 27–34) covers keeping it running: infrastructure as code, maintenance discipline, power and cost, legal and ethical considerations, complete reference architectures at three scales, troubleshooting, community resources, and appendices.

### Conventions used throughout

- Commands are shown for Debian/Ubuntu-family Linux unless stated. Almost everything translates directly to other distributions.
- `docker-compose.yml` snippets are *minimal working examples*. They deliberately omit reverse-proxy labels, external networks, and secrets handling, all of which are covered in the infrastructure chapters and would triple the length of every snippet. Treat them as starting points, not production configurations.
- Resource requirements (RAM, CPU, storage) are rough figures for a small household (one to five users) and are noted as such. Your mileage will vary.
- Prices are approximate USD figures as of 2026 and are given to convey order of magnitude, not to be quoted.
- "As of 2026" marks claims about software versions or project status that will age. Check upstream before relying on them.
- Callouts are used for tips, warnings, and notes:

!!! tip "Tip"
    Practical advice that will save you time.

!!! warning "Warning"
    Something that will cost you time, data, or money if ignored.

!!! danger "Danger"
    Something that can cause data loss or a security incident.

!!! note "Note"
    Context, nuance, or a tangent worth knowing.

## Responsibilities you are taking on

Self-hosting is an exchange: you give up someone else's operational competence in return for control. It is worth being explicit about what you are signing up for, because the people who burn out are usually the ones who did not.

**You are the sysadmin.** When a disk fails at 2 am, nobody else will replace it. When an update breaks the photo app your partner uses, nobody else will roll it back. If you are hosting services for other people — family, friends — you have implicitly promised them a level of availability, and you should think about what that promise is and whether you can keep it. [Chapter 30](30-legal-ethical.md) talks about hosting for others.

**You are the security team.** Every exposed port is your responsibility. Every CVE in software you run is yours to patch. The good news is that the baseline of "don't expose things, use a VPN, keep updated" gets you most of the way. The bad news is that there is no one to blame if you skip it.

**You are the backup administrator.** Cloud services have redundancy you never see. Your single NAS with a single copy of your family photos has none. Until you have an off-site copy and have tested restoring from it, you have not finished setting up.

**You are the documentation team.** See above.

None of this is meant to discourage. Tens of thousands of people run home labs successfully and enjoy them enormously. It is meant to set expectations so that you make choices — about scale, about which services to expose, about how much to promise others — that you can sustain.

## A note on the state of self-hosting in 2026

The landscape has matured remarkably. A few observations that inform the recommendations in this guide:

- **Docker Compose is the lingua franca.** Nearly every self-hostable project ships a `docker-compose.yml`. Kubernetes has a place in home labs for people who want to learn it, but it is not necessary and usually not advisable for running a household's services. [Chapter 5](05-containers.md) discusses when it makes sense.
- **Mini PCs have displaced both Raspberry Pis and enterprise servers** for most people. An Intel N100/N150 or a used business desktop draws 6–15 W idle, costs USD 120–300, and comfortably runs twenty containers. [Chapter 2](02-hardware.md) is largely about this shift.
- **Mesh VPNs solved remote access.** Tailscale (and its self-hosted coordinator Headscale), NetBird, and similar tools made "access my home lab from anywhere without port forwarding" a fifteen-minute task even behind CGNAT. Most people no longer need to expose anything to the internet. [Chapter 8](08-remote-access-vpn.md) covers them.
- **Local AI became a legitimate self-hosting category.** Running capable language models, image generation, speech-to-text, and text-to-speech on consumer GPUs is now practical and is one of the strongest reasons to add a GPU to a home lab. [Chapter 23](23-ai-llm.md) is new territory for many.
- **Immich made self-hosted photos viable for normal people.** For years the honest advice was "keep using Google Photos." That is no longer true. [Chapter 16](16-photos.md) explains why.
- **Licensing is a live issue.** Several popular projects have moved from open source to source-available or "fair" licences, and a few have been acquired or have added paywalled tiers. This guide notes the licence of each service reviewed and [Chapter 30](30-legal-ethical.md) explains what the distinctions mean for you.
- **The community is enormous and generous.** r/selfhosted, r/homelab, the awesome-selfhosted list, and countless blogs and Discord servers mean that whatever problem you hit, someone has hit it before. [Chapter 33](33-resources-community.md) points to the best of them.

## How to use this guide

If you are new: read Chapters 0 through 6, then set up one machine with Docker and three services from Part III that excite you. Then read Part II and retrofit the infrastructure properly. Then read Chapter 11 and set up backups before you add anything else. That sequence — services first for motivation, infrastructure second for sustainability, backups before growth — is the path that produces home labs still running five years later.

If you are intermediate: skim Part I to check for gaps, read Part II carefully, and browse Part III for services you had not considered.

If you are experienced: Part III and Part IV are for you. Chapter 31 (Reference Architectures) may be a useful sanity check against your own design.

Whatever your level, the appendix has a glossary, a port reference, and checklists that are useful to keep open in a tab.

Welcome. Let's build something that you own.
