# CONRRAD Citizen

A Citizen is a living local identity: born once, does Work, records Evidence,
keeps History, and can later Sync without becoming someone else.

## Install

### Linux

```bash
curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2.1/install.sh | bash
```

That command fetches package **0.4.2.1** from the immutable tag
`citizen-runtime-0.4.2.1`, verifies SHA256, prepares an isolated venv,
and runs `citizen install`.

`citizen install` = **Birth** (first time) or **Resume** (existing identity).
It does **not** Sync.

Then open http://127.0.0.1:3434/

### Windows

Not yet public. The Windows WSL2 host path exists in the private runtime
source. It is **not** a public one-command in this repository.

`WINDOWS_STATUS=IMPLEMENTED_NOT_PUBLIC`

### macOS

Not yet public. There is no public macOS host/VM installer here.

`MACOS_STATUS=IMPLEMENTED_NOT_PUBLIC`

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

Do not use `main` as the install trust reference. Use tag `citizen-runtime-0.4.2.1`.

## After install

- `citizen status` — living Citizen vs runtime
- `citizen work` — documented Work
- `citizen sync` — evolution when a verified package is available

Failed Sync leaves the current Citizen in place.

## Recovery

- Port 3434 in use: do not kill other processes. Use `CITIZEN_UI_PORT` and `citizen serve`, or free the port yourself
- Linux service not running: `citizen start`
- UI cannot connect: confirm `citizen status` or that `citizen serve` is running
- Sync failure: current Citizen is preserved; do not reinstall to recover

`citizen uninstall --purge` destroys identity and Evidence. That is not recovery.

See [INSTALL.md](INSTALL.md) for the same product path.

## Advanced

Manual wheel install (not the first-user path):

```bash
WHEEL=conrrad_citizen-0.4.2.1-py3-none-any.whl
URL=https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2.1/release/0.4.2.1/${WHEEL}
curl -fsS --max-redirs 0 -o "$WHEEL" "$URL"
echo "fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9  $WHEEL" | sha256sum -c
python3 -m venv ~/.local/share/conrrad-citizen/venv
~/.local/share/conrrad-citizen/venv/bin/pip install "./$WHEEL"
~/.local/share/conrrad-citizen/venv/bin/citizen install
```

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
