# Security for the Home Lab

Security is not a product you install; it is a set of habits and a handful of decisions made in the right order. The good news is that a home lab's threat model is far simpler than an enterprise's, and the highest-value defences are cheap: expose little, segment the network, keep things updated, use strong authentication, and have backups an attacker cannot reach. This chapter builds a realistic threat model, then works through the layers — host hardening, SSH, firewalls and Docker, the reverse proxy edge, intrusion prevention with CrowdSec and fail2ban, container hardening, secrets, updates, and detection — and ends with a prioritised checklist.

## Threat model: who is actually attacking you

Be honest about the adversaries, because defending against the wrong one wastes effort.

**Automated scanners and bots.** The overwhelming majority of hostile traffic. Within minutes of opening a port, scanners find it; within hours, bots try default credentials and known exploits against whatever they fingerprint. They are indiscriminate and relentless, and they are entirely defeated by: not exposing services, strong unique passwords, MFA, and prompt patching. This is the adversary you *must* beat, and it is beatable.

**Opportunistic ransomware.** Malware that arrives via a phishing email on a family laptop or a compromised download, then spreads across the LAN looking for SMB shares to encrypt and backups to delete. Defeated by: network segmentation, SMB shares that require authentication and are not writable by every device, versioned/immutable/offline backups ([Chapter 11](11-backups.md)), and least privilege.

**Compromised IoT devices.** The cheap camera or plug with a known backdoor, enrolled in a botnet, scanning your LAN from the inside. Defeated by: an IoT VLAN with no access to anything internal ([Chapter 3](03-networking.md)).

**Supply-chain incidents.** A popular Docker image or npm package is compromised upstream. Rare, real (the 2024 xz backdoor; periodic malicious images on Docker Hub). Mitigated by: pulling from official/project sources, pinning versions, not running as root, not granting the Docker socket, egress filtering, and noticing anomalies.

**Targeted attackers.** Someone who wants *your* data specifically. For nearly all home labs this adversary does not exist, and the defences that stop bots and ransomware raise the bar high enough that a targeted attacker would need real effort. If you are a journalist, activist, or hold genuinely sensitive data, the general advice here is a floor, not a ceiling.

**You.** Accidental `rm -rf`, a misconfigured firewall rule that exposes a database, an `.env` file committed to a public repo, a port published on `0.0.0.0` on a VPS. Statistically the most likely cause of a security incident in a home lab. Defeated by: backups, review, and the habits below.

## The order of operations

If you do nothing else, do these, in this order:

1. **Expose nothing.** Use a mesh VPN for your own access ([Chapter 8](08-remote-access-vpn.md)). Zero forwarded ports is the strongest posture there is.
2. **Segment.** IoT and guests on their own VLANs, unable to reach servers ([Chapter 3](03-networking.md)).
3. **Update.** Unattended security updates on hosts; a notification-and-review cadence for containers ([Chapter 5](05-containers.md)).
4. **Authenticate strongly.** Unique passwords from a manager; MFA/passkeys on everything that supports it; an IdP in front of everything that does not ([Chapter 10](10-identity-sso.md)).
5. **Back up immutably.** A copy an attacker on your network cannot delete ([Chapter 11](11-backups.md)).
6. **Then** harden hosts, containers, and the edge, and add detection — the rest of this chapter.

A lab with steps 1–5 done and nothing else is more secure than most small businesses.

## Host hardening

### SSH

SSH is how you administer everything; it deserves care even on the LAN.

- **Keys, not passwords.** `ssh-keygen -t ed25519`; copy the public key; then in `/etc/ssh/sshd_config` (or a drop-in in `/etc/ssh/sshd_config.d/`): `PasswordAuthentication no`, `KbdInteractiveAuthentication no`, `PermitRootLogin no` (or `prohibit-password` if you must SSH as root, as on Proxmox), `PubkeyAuthentication yes`. Reload sshd. Test from a second terminal *before* closing the first.
- **Protect the private key** with a passphrase; use `ssh-agent` or a hardware key (YubiKey with `ed25519-sk`/FIDO2 keys are supported natively by OpenSSH 8.2+ and are the gold standard).
- **Never expose SSH to the internet.** Reach it via the VPN. If you absolutely must, use key-only auth, a non-standard port (which only reduces log noise, not risk), and fail2ban/CrowdSec. **Tailscale SSH** or an SSH certificate authority (step-ca, Smallstep) removes key sprawl for larger labs.
- `AllowUsers youruser` or `AllowGroups ssh-users` to whitelist accounts. `MaxAuthTries 3`. `ClientAliveInterval 300`.
- **SSH login notifications**: a tiny PAM hook or `sshrc` script posting to ntfy on every successful login is one of the highest-value detections available and takes five minutes.

### Users and sudo

One personal account per human, in the `sudo` group; root login disabled; `sudo` with a password (or with `NOPASSWD` only for specific automation commands). Docker group membership is root-equivalent — anyone in `docker` can mount the host filesystem into a container. Know that, and either accept it for your own account or use rootless Docker/Podman.

### Unattended updates

```bash
apt install unattended-upgrades apt-listchanges
dpkg-reconfigure -plow unattended-upgrades   # enable
# /etc/apt/apt.conf.d/50unattended-upgrades: security origin enabled by default on Debian/Ubuntu
# Consider: Unattended-Upgrade::Automatic-Reboot "true"; with Automatic-Reboot-Time "04:00";
# and Unattended-Upgrade::Mail or a script to ntfy for the report
```

Security updates for the host OS, automatically, nightly. This is non-negotiable for anything reachable from beyond the LAN and strongly advised for everything else. Reboots for kernel updates can be automated (with `needrestart` or the reboot option) or done on a weekly schedule; **livepatch**/**kpatch** avoid them on Ubuntu Pro (free for personal use on up to five machines) and RHEL-family.

### Minimal attack surface

Install only what you use; `ss -tulpn` to see what is listening and ask why for each entry. Disable or remove Avahi, CUPS, rpcbind, and anything else that came with a "server" tasksel and that you do not need. A Docker host should listen on 22 (LAN/VPN only), 80/443 (the proxy), and nothing else on the LAN interface.

### Filesystem and kernel

Full-disk encryption (LUKS) on the OS drive protects against physical theft — worth it on a laptop, debatable on a server in your house that must reboot unattended (requires a TPM2 auto-unlock setup — `systemd-cryptenroll` — or network unlock via **Tang/Clevis** or **dropbear-initramfs** for SSH-unlock at boot). ZFS native encryption on data datasets with a key loaded at boot from a file on the encrypted root is a common compromise. **AppArmor** (Debian/Ubuntu) is on by default and Docker uses it; leave it. **SELinux** (Fedora/RHEL) likewise; do not set it to permissive to fix a problem — fix the label. Kernel hardening via `sysctl` (disable IP forwarding where not needed, `kernel.kptr_restrict=2`, `net.ipv4.conf.all.rp_filter=1`) is low-effort; **Lynis** audits a host and tells you what to tighten.
