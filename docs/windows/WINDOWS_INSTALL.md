# Windows install (Citizen 0.2 via WSL2)

**Preflight bundle — not a public release.**

## Prerequisites

- Windows Server 2022 or Windows 11 with **nested virtualization** (or bare metal)
- EC2: supported family with `NestedVirtualization=enabled` (e.g. `m7i-flex.large`)
- Administrator access
- Outbound Internet (WSL kernel + Linux distro download)
- RDP access for operator setup

## Architecture

```text
Windows boot
  → Scheduled Task (Register-CitizenAutoStart.ps1)
  → wsl.exe
  → systemd (PID 1 inside WSL)
  → citizen-seed-living.service
  → http://127.0.0.1:3434/
```

Citizen Core runs **inside WSL2 on the Linux filesystem**. No Windows-native Citizen runtime.

## Install steps

1. Extract `citizen-0.2.0-windows-wsl2.tar.gz` inside the WSL Linux filesystem (not `/mnt/c`).
2. Verify bundle (optional, offline):

   ```powershell
   python3 scripts/verify_release_bundle.py <bundle-dir> --allow-pending-signature
   ```

3. From elevated PowerShell on Windows:

   ```powershell
   .\windows\Install-CitizenWsl2.ps1 -RepoLinuxPath /home/<user>/citizen-0.2.0
   .\windows\Register-CitizenAutoStart.ps1
   ```

4. If `systemd=true` was just written to `/etc/wsl.conf`, run `wsl --shutdown` once, then re-run setup.
5. Open UI: `.\windows\Launch-CitizenUI.ps1`

## Network

- RDP from authorized IP only (operator choice)
- Citizen UI binds **127.0.0.1:3434** only — no public Citizen ports

## Known limitations

- UPDATE / ROLLBACK remain **PARTIAL** on the certified 0.2.0 line
- Requires real Windows + WSL2 hardware certification before production use
- Bundle signature is **PENDING_AUTHORITY** until external release review

See also: [WSL2_ADAPTER.md](WSL2_ADAPTER.md)
