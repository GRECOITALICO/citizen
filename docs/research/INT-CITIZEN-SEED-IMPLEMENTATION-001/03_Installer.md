# 03 — Installer

## Lifetime

Exists **only** during Birth.

After Birth:

- Writes `BOOTSTRAP_DISARMED` + `INSTALLER_GONE`
- Never Births again
- Citizen continues via Runtime + Sync

## Entry

`install.sh` — single public command.

Internally: `python3 -m citizen_seed install` then `boot` then `serve`.

## Disappearance

The Installer is not a long-running service. After disarm, `install` raises `BootstrapDisarmed`. The shell script may still boot + serve an existing Citizen; it does not re-Birth.
