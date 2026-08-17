# Windows → WSL2 → Linux Citizen adapter

Bounded lifecycle bridge only. **Citizen Core stays Linux-certified.**

## Architecture

```text
Windows boot
  → Scheduled Task (Register-CitizenAutoStart.ps1)
  → wsl.exe -d CONRRAD-Citizen
  → systemd (PID 1, wsl.conf)
  → citizen-seed-living.service (existing Linux unit)
  → http://127.0.0.1:3434/
```

Launcher (`Launch-CitizenUI.ps1`) opens the existing UI in the default browser. No Windows-native Citizen runtime.

## End-user installer

`CitizenSetup-0.2.0.exe` (see [docs/windows/WINDOWS_BOOTSTRAPPER.md](../docs/windows/WINDOWS_BOOTSTRAPPER.md)) wraps these scripts. Double-click; no Git/Python/cloud CLIs on Windows.

## Quick start (scripts — operators)

1. Clone this repository **inside the WSL Linux filesystem** (not `/mnt/c`).
2. From elevated PowerShell on Windows:

   ```powershell
   .\windows\Install-CitizenWsl2.ps1 -RepoLinuxPath /home/<user>/citizen
   .\windows\Register-CitizenAutoStart.ps1
   ```

3. Double-click or run `Launch-CitizenUI.ps1` to open the UI.

If `systemd=true` was just written, run `wsl --shutdown` once, then reopen the distro and re-run setup.

## State boundary

- `CITIZEN_HOME` defaults to `/home/citizen/.local/share/conrrad-citizen` (Linux FS).
- Do **not** place Citizen state under `/mnt/c`.

## Idempotency

All scripts are safe to run twice: markers, existing scheduled tasks, and existing `wsl.conf` entries are detected before mutation.

## Limits (audit)

- UPDATE / ROLLBACK remain **PARTIAL** on the certified line — this adapter does not fix them.
- No Windows public release, tag, or KMS changes.
- Runtime Windows certification is **UNTESTED** in this mission.

See also: [docs/windows/WSL2_ADAPTER.md](../docs/windows/WSL2_ADAPTER.md)
