# Install CONRRAD Citizen

Current public runtime **package** = **0.4.2.1**
Runtime semantics remain **0.4.2**
Citizen after fresh Birth = **0.4.2**
Citizen after successful Sync = **0.4.3**

Those are not the same number.

`INSTALL` = Birth / Resume.
`SYNC` = Evolution. Install never Syncs automatically.

Requirements: Python **3.11+**, `curl`, `sha256sum`.

Do **not** run `pip install conrrad-citizen`. PyPI still serves 0.4.1.
Do **not** use `main` as the install URL. Use tag `citizen-runtime-0.4.2.1`.

## Linux

```bash
curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2.1/install.sh | bash
```

This is the primary public command. It:

1. downloads `conrrad_citizen-0.4.2.1-py3-none-any.whl` from the immutable tag
2. verifies SHA256 `fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9`
3. prepares an isolated venv (creates it if missing; does not `rm -rf` an existing one)
4. runs `citizen install`
5. reaches the READY path without Sync

It does not kill port 3434, does not kill Python processes, does not
`pip uninstall` first, and does not call `citizen sync`.

Then open http://127.0.0.1:3434/

Linux host: `citizen start` / `citizen status` (systemd user unit when available).

## Windows

Not yet public. No public one-command is documented here.

`WINDOWS_STATUS=IMPLEMENTED_NOT_PUBLIC`

Windows E2E is not claimed.

## macOS

Not yet public. No public one-command is documented here.

`MACOS_STATUS=IMPLEMENTED_NOT_PUBLIC`

## Canonical public artifact

- Artifact: `release/0.4.2.1/conrrad_citizen-0.4.2.1-py3-none-any.whl`
- Package: `0.4.2.1`
- Runtime: `0.4.2`
- SHA256: `fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9`
- Source: `GRECOITALICO/CONRRAD-CITIZEN` `44246a3ffa9f789c40fe023a0d72a053dc08088b`
- Tag: `citizen-runtime-0.4.2.1`
- Provenance: `release/0.4.2.1/PROVENANCE.json`
- Signing: none (SHA256 + source commit)

This is not the frozen 0.4.2 artifact.

## Frozen 0.4.2

Historical / canonical frozen artifact, unchanged:

- `release/0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl`
- SHA256: `0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce`
- Tag: `citizen-runtime-0.4.2`

Do not use it for a new install. Its install path auto-Synced.

## Recovery

- Port 3434 in use: do not kill other processes. Set `CITIZEN_UI_PORT` and run `citizen serve`, or free the port yourself
- Linux service not running: `citizen start`
- UI cannot connect: confirm `citizen status` or that `citizen serve` is running
- Sync failure: current Citizen is preserved; do not reinstall to recover

`citizen uninstall --purge` destroys identity and Evidence. That is not recovery.

## Advanced

Manual wheel path (not the first-user command):

```bash
WHEEL=conrrad_citizen-0.4.2.1-py3-none-any.whl
URL=https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2.1/release/0.4.2.1/${WHEEL}
curl -fsS --max-redirs 0 -o "$WHEEL" "$URL"
echo "fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9  $WHEEL" | sha256sum -c
python3 -m venv ~/.local/share/conrrad-citizen/venv
~/.local/share/conrrad-citizen/venv/bin/pip install "./$WHEEL"
~/.local/share/conrrad-citizen/venv/bin/citizen install
```

The old destructive installer is
[historical/install-0.4.2-destructive.sh](historical/install-0.4.2-destructive.sh)
only. It is not the primary documented path.
