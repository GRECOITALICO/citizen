# Windows EXE bootstrapper (Citizen 0.2.0 via WSL2)

**Not a public release.** Built from `codex/citizen-windows-wsl2-adapter-v2`.

The user-facing artifact is `CitizenSetup-0.2.0.exe`. It is **not** a native Citizen.exe runtime.

## What the EXE does

```text
double-click CitizenSetup-0.2.0.exe
→ UAC (once, to enable WSL features if needed)
→ prerequisite detection (fail-closed)
→ WSL2 + dedicated distro CONRRAD-Citizen
→ extract payload onto the Linux filesystem (/opt/conrrad-citizen)
→ existing windows/wsl2/setup.sh (Birth + systemd user unit)
→ Register-CitizenAutoStart.ps1
→ Launch-CitizenUI.ps1 → http://127.0.0.1:3434/ in the default browser
```

The installer does **not** require Git, Python on Windows, AWS CLI, Azure CLI, GitHub CLI, Cursor, or KMS credentials. Python runs **inside** WSL.

## Build (operator, Linux)

```bash
python3 scripts/build_windows_bootstrapper.py --output-dir /tmp/citizen-bootstrapper
```

Produces:

- `CitizenSetup-0.2.0.exe`
- `installer-build.json`
- `installer-signing-input.json` (Authenticode by authority later; not runtime KMS)

## Uninstall

Add/Remove Programs or:

```powershell
& "$env:ProgramData\CONRRAD\Citizen\windows\bootstrapper\Uninstall-CitizenWsl2.ps1"
```

Pass `-RemoveCitizenDistro` only to unregister **CONRRAD-Citizen**. Ubuntu and Docker distros are never removed implicitly.

## Limits

- Real Windows double-click certification is the independent Antigravity mission
- Authenticode signature is prepared, not applied here
- Nested virtualization is required for WSL2 on virtual machines
