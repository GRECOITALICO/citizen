# WSL2 adapter (Windows portability)

Mission: `CITIZEN-P0-WINDOWS-WSL2-IMPLEMENTATION-002`

## Purpose

Provide a **minimal** Windows-side adapter so Citizen runs unchanged inside WSL2:

| Layer | Responsibility |
|-------|----------------|
| `windows/*.ps1` | WSL distro registration, scheduled autostart, browser launcher |
| `windows/wsl2/*.sh` | systemd enablement, environment checks, reuse `scripts/install_service_linux.sh` |
| Linux Citizen Core | Birth, living UI, sync, release verification (unchanged) |

## Files

| Path | Role |
|------|------|
| `Install-CitizenWsl2.ps1` | Windows entry: WSL2 check, distro install, invoke `setup.sh` |
| `Register-CitizenAutoStart.ps1` | One scheduled task → WSL → `systemctl --user start` |
| `Launch-CitizenUI.ps1` | Open `http://127.0.0.1:3434/` |
| `wsl2/setup.sh` | Idempotent WSL-side install |
| `wsl2/configure-systemd.sh` | Write `[boot] systemd=true` to `/etc/wsl.conf` |
| `wsl2/verify-environment.sh` | Fail-closed WSL2/systemd/CITIZEN_HOME checks |
| `wsl2/adapter.py` | Pure helpers for tests and command generation |

## Release verifier / sync

The adapter **does not** alter trust roots, manifest schema, signatures, or KMS. Release verification and sync remain the Linux paths invoked inside WSL.

## Known limitations

1. **Real Windows runtime UNTESTED** — integration mission runs on physical Windows.
2. **UPDATE=PARTIAL, ROLLBACK=PARTIAL** — inherited from certified 0.2.0 line; not fixed here.
3. First `systemd=true` change requires `wsl --shutdown` before PID 1 is systemd.
4. Repository must live on Linux FS inside WSL for performant I/O and state boundary.

## Next mission

`CITIZEN-P0-WINDOWS-WSL2-INTEGRATION-001` (Antigravity, real Windows machine).
