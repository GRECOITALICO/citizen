# CONRRAD Citizen

A Citizen is a living local identity: born once, does Work, records Evidence,
keeps History, and can later Sync without becoming someone else.

## Install

### Linux

STATUS=REFERENCE CERTIFIED

```bash
curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-managed-0.4.2.1/install.sh | bash
```

That command is the public one-line installer. Trust reference: immutable tag
`citizen-managed-0.4.2.1` — not `main`.

It prepares host isolation if needed, verifies the immutable Citizen
environment image, creates or reuses the persistent Citizen volume, and
starts the managed environment. Birth happens only on an empty volume.
Resume reuses the existing identity. It does **not** Sync.

The wheel `conrrad_citizen-0.4.2.1-py3-none-any.whl` is an image build
input. It is not installed into host Python.

Then open http://127.0.0.1:3434/

### Windows

STATUS=IMPLEMENTED / REAL VALIDATION PENDING

One Citizen. Windows is host infrastructure. WSL2 is host infrastructure.
The managed Linux environment is the runtime boundary.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-windows-wsl2-0.4.2.2/install/windows.ps1 | iex"
```

Trust reference: immutable tag `citizen-windows-wsl2-0.4.2.2` — not `main`.
That one instruction detects Windows, self-elevates for UAC, resumes after
reboot, provisions WSL2 and the managed distro `CONRRAD-Citizen`, pulls the
same public image as Linux, and reaches READY. No second paste. No pip.
No native Windows Citizen.

Windows is **not certified**. Real Windows E2E is P0.9H.2.

`WINDOWS_STATUS=IMPLEMENTED_REAL_VALIDATION_PENDING`

### macOS

Not yet public. There is no public macOS host/VM installer here.

`MACOS_STATUS=NOT_PUBLIC`

## Versions

| Field | Value |
|---|---|
| Package (what you download) | **0.4.2.1** |
| Runtime (what the engine is) | **0.4.2** |
| Citizen after fresh Birth | **0.4.2** |
| Citizen after successful Sync | **0.4.3** |

These are not the same number.

`INSTALL` = Birth / Resume.
`SYNC` = Evolution. Explicit. Never automatic during install.

Do not use `pip install conrrad-citizen` from PyPI. That still resolves to 0.4.1.
Do not install Citizen into host Python, a venv, or systemd.

Do not use `main` as the install trust reference. Use tag `citizen-managed-0.4.2.1`.
The frozen wheel tag `citizen-runtime-0.4.2.1` remains the immutable wheel bytes.

## After install

Open http://127.0.0.1:3434/

The host command `citizen` is a dispatcher into the managed environment when
isolation is available. Sync remains explicit from that command or the UI.

Failed Sync leaves the current Citizen in place.

## Recovery

- Port 3434 in use: do not kill other processes. Free the port yourself.
- Environment not running: re-run the one-line installer (Resume, not Birth)
- UI cannot connect: confirm http://127.0.0.1:3434/api/living
- Sync failure: current Citizen is preserved; do not reinstall to recover

`citizen uninstall --purge` destroys identity and Evidence. That is not recovery.

See [INSTALL.md](INSTALL.md) for the same product path.

## Advanced

The frozen wheel remains at tag `citizen-runtime-0.4.2.1`. It is an OCI
image build input, not a host pip install.

Image provenance: [isolation/IMAGE_PROVENANCE.json](isolation/IMAGE_PROVENANCE.json)
and [release/0.4.2.1/IMAGE_PROVENANCE.json](release/0.4.2.1/IMAGE_PROVENANCE.json).

The previous venv installer is retained only as
[historical/install-0.4.2.1-venv.sh](historical/install-0.4.2.1-venv.sh).
It is not the primary command.

Frozen 0.4.2 (`conrrad_citizen-0.4.2-py3-none-any.whl`, SHA256
`0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce`,
tag `citizen-runtime-0.4.2`) is the historical canonical frozen artifact.
It is **not** the current new-user runtime. It auto-Synced on install.
Do not overwrite it.

The old destructive `install.sh` is retained only as
[historical/install-0.4.2-destructive.sh](historical/install-0.4.2-destructive.sh).
It is not the primary command.

## Historical 0.1 seed

The original certified 0.1 seed record remains in this repository
([CERTIFIED_0.1.md](CERTIFIED_0.1.md), [docs/citizen-life/](docs/citizen-life/)).
It is not the 0.4.2.1 install path.
