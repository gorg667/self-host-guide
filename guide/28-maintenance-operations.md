# Maintenance and Operations

Building a home lab is a project; running one is a practice. The difference between labs that are still humming after five years and labs that were quietly abandoned after eighteen months is almost never the hardware or the software — it is the operational habits: a sane update cadence, documentation that exists, a runbook for the things that go wrong at 11 pm, a way to know something broke before someone tells you, and a plan for the day you are not there. This chapter is about that practice: update strategy and cadence, the maintenance calendar, documentation and runbooks, change management for a one-person team, incident habits, capacity and lifecycle planning, the "bus factor" and hosting for others, and — importantly — knowing when to simplify or shut something down.

## The maintenance mindset

Three principles that make everything else easier:

**Make changes boring.** Every update, migration, or config change follows the same small ritual: snapshot or backup first, read the release notes, change one thing, verify, note it down. Boring is the goal. Excitement in operations means something went wrong.

**Prefer fewer things.** Every service is a maintenance obligation forever. The most effective operational improvement most labs can make is to *remove* the six services nobody used in the last three months. Complexity is a cost paid monthly.

**Automate the routine, hand-do the risky.** Security updates, snapshots, backups, scrubs, certificate renewals, and update *notifications* should be automatic. Major version upgrades, storage changes, network changes, and anything touching the IdP or the backups should be deliberate, scheduled, and done with attention.

## Update strategy

### Cadence

| Layer | Cadence | Method |
|---|---|---|
| Host OS security updates | Automatic, nightly | `unattended-upgrades` / `dnf-automatic`; reboot window weekly or with `needrestart` |
| Host OS non-security updates | Monthly | `apt full-upgrade` during the maintenance window |
| Host OS major release (Debian 12→13) | When you have an afternoon; within a year of release | Snapshot, read the release notes, `apt full-upgrade` / `do-release-upgrade`; or rebuild via Ansible |
| Hypervisor (Proxmox) | Monthly for point releases; majors after community feedback settles (~2 months) | `apt` via the no-subscription repo; PBS backup of every VM first |
| Firewall (OPNsense) | Point releases within a couple of weeks; majors after a month | Built-in updater; config export first |
| Container images — stateless / low-risk | Weekly, semi-automatic | Renovate auto-merge patch/minor, or Diun notification + `compose pull` |
| Container images — stateful (databases, Nextcloud, Immich, Paperless, HA) | On notification, after reading release notes; within a month | Snapshot → `pull` → `up -d` → verify |
| Database majors (Postgres 17→18) | Yearly, per app | Dump → new image → restore, or pgautoupgrade; backup first |
| Firmware (BIOS, NIC, drives, switches, APs) | Twice a year, or for a specific fix/CVE | Vendor procedure; not during a storm |
| Home Assistant | Monthly release; wait ~a week for `.x` bugfixes | Read "Breaking Changes"; snapshot; update |

**Do not** update everything on the same day. Stagger: infrastructure (host, hypervisor, proxy) one week, applications the next. When something breaks you know which change did it.

### The pre-update ritual

1. **Read the release notes.** Every stateful app, every time. Look for "breaking," "migration," "manual step," "deprecated."
2. **Snapshot.** Proxmox VM snapshot, ZFS/Btrfs snapshot of the data directory, or at minimum a fresh database dump. Thirty seconds that turns a disaster into an inconvenience.
3. **Update one thing.** `docker compose pull && docker compose up -d` for that stack.
4. **Verify.** Log in. Check the thing the app is for. Check the logs (`docker compose logs --tail 100`) for errors and migration messages. Check Uptime Kuma went green.
5. **Note it.** A line in the changelog: date, what, version from → to, anything noticed.
6. **Delete the snapshot** after a few days if all is well (snapshots on Proxmox slow VMs over time; ZFS snapshots consume space as data changes).

### When an update breaks something

Roll back first, investigate second. The snapshot from step 2 makes this a two-minute decision: revert, restore service, then read the issue tracker at leisure. Pin the previous image tag in the Compose file until the fix lands. Do not debug a broken production service while the family waits.

## The maintenance calendar

Put these in an actual calendar with reminders. Things that are "whenever" never happen.

**Weekly (15 minutes)**
- Glance at the dashboard/Beszel/Grafana: disk trends, anything red.
- Review update notifications; apply low-risk ones.
- Check the backup job ran and the size is sane (Healthchecks green; Backrest/PBS shows last night's snapshot).
- Skim CrowdSec/fail2ban decisions if anything is exposed.

**Monthly (1–2 hours — the maintenance window)**
- Host OS updates and reboots (staggered).
- Stateful app updates with the ritual above.
- Home Assistant update.
- Restore test: one random file from the off-site backup ([Chapter 11](11-backups.md)).
- Check ZFS scrub results and SMART/Scrutiny for anything trending.
- Review Uptime Kuma incident history — anything flapping?
- Review alerts: delete or tune any that fired and were ignored.
- Prune: `docker image prune`, old snapshots, old backups beyond retention, stale VMs.
- Update the changelog and any documentation touched.

**Quarterly (an afternoon)**
- Service-level restore test: restore one whole application from backup to a scratch location and confirm it works.
- Database major upgrades due.
- Review the service inventory: what has nobody used? Decommission it (export data, archive config, remove).
- Review firewall rules and forwarded ports; remove what is no longer needed.
- Rotate anything that should rotate: API tokens with expiry, the DKIM key if self-hosting mail, admin passwords if shared.
- Check UPS battery health (self-test); clean dust filters and fans.
- Review disk capacity trend: at 70% full, plan expansion.
- Verify the emergency sheet (master passwords, recovery codes, encryption keys) is current and where it should be.

**Yearly (a weekend)**
- Full disaster-recovery drill from the off-site copy on scratch hardware or a VM ([Chapter 11](11-backups.md)). Time it. Fix what the documentation got wrong.
- Firmware updates across hardware.
- Review the architecture: does the lab still match your needs? Is the tier right? What would you drop or consolidate?
- Renew the domain (auto-renew on, payment method current). Check the registrar and DNS provider accounts have 2FA and a working recovery email.
- Replace the UPS battery if 3–4 years old; consider drive age (5+ years for spinning drives is borrowed time even without SMART warnings).
- Review the bus-factor plan (below) and update the "if I'm not here" document.

## Documentation

You will not remember. Six months is enough for "why is port 8096 forwarded" to become a mystery. Documentation is the load-bearing habit.

### What to document

- **Inventory**: every host (hardware, OS, IP, role, how to reach it, out-of-band access), every VM/LXC, every service (URL, host, stack directory, what it is for, who uses it, data location, backup status), every network (VLANs, subnets, DHCP ranges, reservations), every account (where the admin credentials are — in the password manager, referenced by entry name, never the credentials themselves).
- **Architecture**: one diagram (Mermaid in Markdown so it lives in Git) showing hosts, networks, and the flow from the internet to a service.
- **Procedures (runbooks)**: how to do the things you do — add a service, update a stack, restore from backup, rebuild a host, replace a failed drive, rotate a certificate, add a user to the IdP, onboard a family member's phone.
- **Decisions (ADRs)**: short dated notes of *why*. "2026-02: Chose Caddy over Traefik: fewer services, readable config; revisit if we exceed 40 hosts." Future you will otherwise re-litigate every choice.
- **Changelog**: a running dated log of changes. The single most useful troubleshooting document: "it broke around the 14th — what changed on the 13th?"
- **Vendor/account details**: ISP account and support number, domain registrar, DNS provider, backup provider, VPS provider, hardware warranties and purchase dates, UPS model and battery replacement date.

### Where to document

- **In the Git repo** alongside the code (Markdown; `docs/` directory; rendered by MkDocs/Otter Wiki if you want a UI) — the recommendation, because documentation next to configuration stays current and is versioned.
- **A wiki** (BookStack, Outline, DokuWiki — [Chapter 18](18-notes-productivity.md)) — friendlier for non-technical household members and for procedures with screenshots.
- **Comments in the Compose files themselves** — the cheapest documentation; a one-line `# why:` on every non-obvious setting.
- **Homepage/Homarr dashboard descriptions** — a sentence per service is documentation too.
- **NetBox** for people who want a real source of truth for IPs, racks, and cables (heavy; Tier 3).

**Not** in the lab alone. If the wiki is on the server that died, it is useless. Mirror the docs repo to GitHub/Codeberg, keep a PDF export in the off-site backup, and keep the *bootstrap* procedure — how to get from nothing to "the docs are readable again" — printed or on a phone.

### The runbook template

For each procedure, a short page:

```
# Replace a failed drive in the ZFS pool

When: zpool status shows DEGRADED / Scrutiny alert / SMART failure
Impact while running: none (pool degraded but online); DO NOT reboot unnecessarily
Time: 20 min hands-on + resilver (12–36 h)

1. Identify: zpool status -v; note the failed device's by-id name
2. Identify physical slot: ledctl locate /dev/sdX  (or match serial: smartctl -i)
3. Offline it: zpool offline tank <dev>
4. Pull, insert replacement (same or larger size, CMR)
5. Find new by-id: ls -l /dev/disk/by-id | grep <serial>
6. Replace: zpool replace tank <old-id> /dev/disk/by-id/<new-id>
7. Watch: zpool status; resilver progress; Scrutiny picks up the new drive
8. After resilver: zpool clear tank; scrub next week; update inventory (serial, purchase date)

Gotchas: 4Kn vs 512e mismatch; a shucked drive may need the 3.3V pin mod; never replace during a scrub
Last performed: 2026-04-12 (drive 3, WD160EDGZ, took 19 h)
```

## Change management for one person

Enterprise change management exists because changes cause outages. A one-person lab needs a lightweight version of the same discipline:

- **Change window**: a regular time (Sunday morning, Tuesday evening) when the household expects things might be down. Announce anything outside it.
- **One change at a time** where possible; when not, write down the list *before* starting.
- **Rollback plan before you begin**: the snapshot, the previous image tag, the config backup.
- **Test in staging** — which at home means a scratch VM or a second Compose project with a `-test` suffix and a copy of the data — for anything scary (Nextcloud majors, IdP changes, storage layout).
- **Do not change the network and a service at the same time.** When both break, you cannot tell which.
- **Do not start a risky change when tired, rushed, or when the family needs the service in the next hour.** Most home-lab disasters are timing, not skill.

## Incident habits

When something breaks:

1. **Restore service first.** Roll back, restart, fail over. Understanding can wait; the family cannot.
2. **Then understand.** Logs (`docker compose logs`, `journalctl -u`, Dozzle, the app's own log), recent changes (the changelog), the upstream issue tracker.
3. **Write a short post-mortem** — three lines: what happened, why, what will prevent it. Add the prevention to the runbook or the automation. The lab gets more reliable with every incident *only* if this step happens.
4. **Fix the class, not the instance.** "Disk filled up from container logs" → set `max-size` in `daemon.json` on *every* host and add a disk alert, not just clear this one.

Keep a **break-glass** path: a local admin account on every host that does not depend on the IdP; a way to reach the hypervisor console when the network is broken (IPMI, a KVM, a monitor and keyboard in the cupboard, or **PiKVM/JetKVM/NanoKVM** — cheap IP-KVMs that are among the best home-lab purchases); the router's local admin credentials in the password manager *and* on the emergency sheet.

## Capacity and lifecycle

- **Watch trends, not snapshots.** Disk at 60% is fine; disk at 60% growing 5% a month is a purchase decision in six months. Grafana/Beszel graphs over months tell you this.
- **Plan hardware lifecycle**: spinning drives 5–7 years, SSDs by TBW and age, UPS batteries 3–5 years, fans and thermal paste 5+ years, mini PCs and SFFs a decade if they still meet needs. Buy replacements before failure when possible; a spare drive on the shelf is cheap insurance.
- **Grow deliberately** ([Chapter 1](01-planning.md)): add a service because it is needed, a host because the current one is genuinely full, a VLAN because there is a trust boundary to draw. Not because it is Saturday.
- **Decommission properly**: export the data in an open format, archive the Compose file and config to a `retired/` directory in the repo with a dated note, remove the DNS record and proxy route and IdP client, remove the backup job (or keep the last backup for a year), update the inventory. A half-removed service is worse than a running one.

## The bus factor

If you were unavailable — travelling, ill, or worse — what happens?

- **Short term (a week):** the lab keeps running if it is boring; the household needs to know *nothing* except "if it is broken, wait" or "turn it off and on again." Write a one-page "if the internet/TV/photos stop working" for the fridge: which box to power-cycle, in what order, and when to give up and call someone.
- **Medium term (months):** someone technically competent should be able to keep it running or wind it down. The documentation, the repo, the password manager's emergency access ([Chapter 21](21-passwords-secrets.md)), and a named person who knows they are that person. Walk them through it once.
- **Long term (permanently):** the household should be able to *get the data out*. Photos, documents, and passwords in open formats, with the location and the keys in the emergency sheet. This is the real test of the anti-lock-in argument for self-hosting — make sure it holds for your family and not only for you.

Concretely: an **"If I'm not here" document** (printed, in the safe, and a copy with the trusted person) containing: what the lab is and where; how to log into the password manager (emergency access or the sealed master password); where the backups are and how to restore the photos and documents *without* the lab (the Restic/Borg command, the repo password, a cloud login); the domain and DNS account details so nothing lapses; who to call; and an explicit permission to shut it all down and put the photos on a USB drive if that is easier. Revisit it yearly.

## Hosting for others

Once family or friends depend on your services, you have made an implicit promise. Make it explicit — to yourself if not to them:

- **Set expectations**: "it is a hobby; it may be down for a day; I will tell you before planned work; do not put your only copy of anything here."
- **Give them an exit**: they can export their data (Immich albums, Nextcloud files, Vaultwarden vault) at any time; show them how once.
- **Do not host things you cannot walk away from** for people who cannot walk away from them — someone's business email, a friend's only backup. Point them at a paid provider, or run it *for* them in a way they own (their account, their domain).
- **Separate their access** (IdP groups, Tailscale ACLs) so a compromise of their device does not reach your admin surfaces.
- **Consider the legal side** ([Chapter 30](30-legal-ethical.md)) — for family it is trivial; for a club or acquaintances, think about what data you hold and why.

## Knowing when to stop

Some services should be retired. Some whole labs should be scaled back. Signs: you dread the maintenance window; updates pile up for months; the family has quietly gone back to the cloud service; you spend more time fixing than using; a service has had no login in 90 days. Shrinking a lab is not failure — it is operations. The people who run labs for decades are the ones who periodically cut them in half.

## Checklist

- [ ] Automatic security updates on every host; a defined cadence for everything else; staggered by layer.
- [ ] The pre-update ritual (notes → snapshot → one change → verify → log) is habit; rollback is the first response to breakage.
- [ ] Weekly/monthly/quarterly/yearly tasks are in a calendar with reminders.
- [ ] Inventory, architecture diagram, runbooks, ADRs, and changelog exist in Git, mirrored off the lab; a PDF/printout of the bootstrap procedure exists.
- [ ] Every non-obvious Compose setting has a `# why:` comment.
- [ ] Break-glass access: local admin accounts, console/IP-KVM access, router credentials on the emergency sheet.
- [ ] Post-mortem habit: every incident produces a prevention (automation, alert, or runbook update).
- [ ] Capacity trends visible; hardware lifecycle dates in the inventory; a spare drive on the shelf.
- [ ] Decommission procedure followed for retired services; a `retired/` archive in the repo.
- [ ] "If I'm not here" document written, printed, shared with a named person, reviewed yearly; emergency access configured in the password manager.
- [ ] Expectations set with anyone who depends on your services; their data exportable; their access separated.
- [ ] The service inventory reviewed quarterly and pruned honestly.
