# SentinelX Server B installation runbook

## Authority and current decision

This runbook covers only the SentinelX Linux agent on the VICIdial/Asterisk
host at `65.21.67.207`. It does not authorize telephony activation, Ralph
account creation, business writes, firewall changes, SSH changes, or changes
to the `codestra-admin` sudo policy.

The 2026-09-05 review is **fail-closed**:

- `FINAL_STATUS=BLOCKED_ROOT_ACCESS` because direct root SSH is denied and
  `codestra-admin` has no non-interactive administrative command outside the
  restricted VICIdial operator;
- the current SentinelX schema has no supported switch that disables
  `script_run` or inline/chunked uploads, so the accompanying policy remains a
  blocked review template, not an approved production policy;
- no SentinelX installation, enrollment, service creation, or telephony
  configuration change was performed.

See `evidence-20260905.yaml` for the sanitized observed values.

## Reviewed sources

The review used only the owner-specified public sources:

- `https://get.sentinelx.app/install.sh`
- `https://github.com/pensados/sentinelx-cloud-installer`
- `https://github.com/pensados/sentinelx-cloud-core`

The endpoint installer downloaded on both the target and review host had
SHA-256 `56f5da769567a471ccf798fa11105f747738f26ee48d0d106922922e56d3acb9`
and passed `bash -n`. It is the exact `install.sh` blob at installer commit
`ee8628482a83959b9e1a7b99d1082f32b49e4196` (2026-08-14). Current installer
`main` was `e637b12c35e40a81fef3171394fe863235575dfb`; its `install.sh` differs
from the endpoint copy because a duplicated fallback configuration was later
removed.

The installer does not pin everything it executes. It shallow-clones core
`main` and downloads `enroll.py` from installer `main`. At review time those
commits were:

- core: `d6b33822b61e7fccf39547d5cce8add8bc7021f9`, package version `0.11.14`;
- installer: `e637b12c35e40a81fef3171394fe863235575dfb`.

Treat the checksum as evidence of reviewed bytes, not publisher
authentication. If any fetched checksum or commit changes, repeat the source
review before execution.

## Installer behavior reviewed

The Linux installer:

1. requires root, Linux on `x86_64`/`aarch64`/`arm64`, `curl`, `git`, a
   working systemd, and Python >=3.11 with both `pip` and `venv`;
2. creates or reuses `/etc/sentinelx/host_id`;
3. creates the non-login `sentinelx` system user if missing;
4. normally offers `sentinelx ALL=(ALL) NOPASSWD: ALL`, but skips creation
   when `SENTINELX_SKIP_SUDO=1`; an existing rule is not removed;
5. removes and re-clones `/opt/sentinelx-cloud-core`, creates a virtualenv,
   upgrades pip inside it, and installs the core editable;
6. downloads the unpinned enrollment helper to
   `/etc/sentinelx/sentinelx-enroll.py`;
7. preserves an existing `/etc/sentinelx/identity.json`, otherwise prompts
   for owner enrollment and writes the JWT-bearing identity there;
8. preserves an existing `/etc/sentinelx/config.yaml`, otherwise installs the
   broad example configuration;
9. creates and chowns `/var/lib/sentinelx` and `/var/log/sentinelx` to the
   agent user;
10. overwrites `/etc/systemd/system/sentinelx-cloud-core.service`, reloads
    systemd, and enables and starts it as `User=sentinelx`.

No distribution upgrade is needed on this host. Python 3.11.15, pip, venv,
git, curl, and systemd were present during review. `/usr/bin/python3` remains
Python 3.6.15; the installer correctly selects `/usr/bin/python3.11` and must
not change the system default.

## Policy compatibility hold

Static review and a bounded test against core commit
`d6b33822b61e7fccf39547d5cce8add8bc7021f9` established:

- `allowed_commands: []` rejects the `exec` operation;
- an `r`-only `file_ops.paths` list allows the selected health files and
  rejects `/etc/passwd` and non-`rw` writes;
- an empty `services` map rejects Asterisk service control;
- `security.trusted_fetch_hosts: []` blocks URL fetching only;
- `script_run` stays registered and executes arbitrary Bash/Python without
  consulting `allowed_commands`;
- inline and chunked uploads stay registered and can write under
  `upload_base` without consulting `trusted_fetch_hosts`;
- command entries are prefix-matched and executed through `bash -lc`, so an
  allowed prefix can be followed by a shell compound operator.

The blocked template sets `upload_base: /dev/null` as a defense-in-depth
backstop. The reviewed handlers then fail before creating a script or upload,
but with a generic `FileExistsError`; this is not a documented policy switch
and is not sufficient for approval. Installation may proceed only after a
reviewed core version provides explicit, host-enforced operation denial (or an
equivalent separately reviewed sandbox) and negative tests prove:

- `script_run` is rejected before a script file or process is created;
- inline, chunked, edit-staging, and cross-host uploads are rejected before
  bytes are written;
- shell compounds cannot extend an allowed command prefix;
- no sudo edit can bypass the no-write policy;
- only the exact `r` paths in the policy can be read.

## Existing-installation gate

An authorized root operator must complete this gate before copying or running
anything as root. Do not infer absence from the unprivileged checks alone.

```bash
set -eu
id
hostname -f || hostname
find /etc/sentinelx /opt/sentinelx-cloud-core /var/lib/sentinelx \
  -maxdepth 2 -printf '%M %u:%g %p\n' 2>/dev/null || true
systemctl cat sentinelx-cloud-core.service 2>/dev/null || true
systemctl show sentinelx-cloud-core.service \
  -p LoadState -p ActiveState -p UnitFileState -p User -p FragmentPath \
  --no-pager 2>/dev/null || true
getent passwd sentinelx || true
test ! -e /etc/sudoers.d/sentinelx || {
  stat -c '%A %U:%G %n' /etc/sudoers.d/sentinelx
  visudo -c -f /etc/sudoers.d/sentinelx
}
```

If any SentinelX state exists, stop and preserve its `host_id`, identity,
policy, unit/drop-ins, ownership, and dashboard association. Never print or
copy the contents of `identity.json` into evidence.

The exact root-only staging step still outstanding is:

```bash
install -d -m 0700 /root/sentinelx-install
install -m 0600 \
  /home/codestra-admin/sentinelx-install-review/install.sh \
  /root/sentinelx-install/install.sh
bash -n /root/sentinelx-install/install.sh
sha256sum /root/sentinelx-install/install.sh
```

The expected checksum applies only to the reviewed 2026-09-05 copy above.
This staging command is not permission to execute the installer while the
policy compatibility hold remains.

## Installation and owner enrollment after both gates clear

Before first connection, install the approved restricted policy as
`/etc/sentinelx/config.yaml`, owned by root and not writable by `sentinelx`.
Audit and remove any pre-existing broad SentinelX sudo rule only under a
separately reviewed root change; `SENTINELX_SKIP_SUDO=1` does not remove it.

Run from an authorized interactive root session:

```bash
SENTINELX_SKIP_SUDO=1 \
SENTINELX_ENROLL_MODE=paste \
  bash /root/sentinelx-install/install.sh
```

The owner opens only the official enrollment URL printed by `enroll.py`, logs
into the same SentinelX account connected to ChatGPT, and pastes the token
directly into the installer terminal. Never put the token in chat, shell
arguments, logs, Git, or this repository. If the prompt is not completed,
leave the install intact and report `BLOCKED_OWNER_ENROLLMENT`.

## Verification without telephony impact

Systemd health is not proof of enrollment. Collect each item separately:

```bash
systemctl is-active sentinelx-cloud-core.service
systemctl is-enabled sentinelx-cloud-core.service
systemctl show sentinelx-cloud-core.service -p User -p Group --no-pager
sudo -u sentinelx -n true  # must fail; no unrestricted sudo
```

Then use authenticated SentinelX/dashboard evidence to confirm the requested
label, host ID, intended hub, and owner account. Through the connected agent,
prove each allowed health-file read succeeds and all negative cases in the
policy compatibility gate fail before execution or I/O.

Do not restart, reload, start, or stop Asterisk, MariaDB, VICIdial, either
Codestra adapter, or the provisioning service. Do not open inbound ports or
place calls. Re-run the restricted VICIdial operator `status` action and
confirm its active states and write gates are unchanged.

## Rollback boundary

No rollback applies to the 2026-09-05 review because nothing was installed.
For a future approved install, capture the pre-install state first and define
a reviewed rollback that disables the SentinelX unit, revokes the host in the
owner dashboard, and removes only newly created SentinelX files/users/rules.
Never delete a pre-existing identity or policy.
