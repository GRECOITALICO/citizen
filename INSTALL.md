# Install CONRRAD Citizen

Current public runtime **package** = **0.4.2.1**
Runtime semantics remain **0.4.2**
Citizen after fresh Birth = **0.4.2**
Citizen after successful Sync = **0.4.3**

Those are not the same number.

`INSTALL` = Birth / Resume.
`SYNC` = Evolution. Install never Syncs automatically.

Requirements: Linux. `curl`. The installer prepares isolation infrastructure.

Do **not** run `pip install conrrad-citizen`. PyPI still serves 0.4.1.
Do **not** install Citizen into host Python or a venv.
Do **not** use `main` as the install URL. Use tag `citizen-managed-0.4.2.1`.

## Linux

STATUS=REFERENCE CERTIFIED

```bash
curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-managed-0.4.2.1/install.sh | bash
```

This is the primary public command. It:

1. prepares host isolation if it is missing
2. obtains the immutable Citizen environment image (`ghcr.io/grecoitalico/citizen@sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da`)
3. verifies the image digest
4. creates or reuses the persistent Citizen volume
5. starts the managed environment
6. Birth (empty volume) or Resume (existing sealed identity)
7. reaches READY without Sync

The wheel SHA256 `fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9`
is verified when the image is built. The installer does not pip-install it
onto the host.

It does not kill port 3434, does not kill processes, and does not call Sync.

Then open http://127.0.0.1:3434/

## Windows

STATUS=IMPLEMENTED / REAL VALIDATION PENDING

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-windows-wsl2-0.4.2.1/install/windows.ps1 | iex"
```

Trust reference: tag `citizen-windows-wsl2-0.4.2.1` — not `main`.

This is the same Citizen as Linux. It:

1. detects Windows and prepares WSL2
2. self-elevates (UAC) without asking the user to open an Administrator shell
3. resumes automatically after reboot
4. imports official Ubuntu WSL rootfs into managed distro `CONRRAD-Citizen`
5. pulls `ghcr.io/grecoitalico/citizen@sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da`
6. creates persistent volume `%LOCALAPPDATA%\CONRRAD\Citizen`
7. Birth (empty volume) or Resume (existing sealed identity)
8. reaches READY without Sync

Do not use CitizenSetup.py, NSSM, native Windows Python, or `1.4.0-alpha`.
Windows is **not certified** until P0.9H.2 runs on a real Windows machine.

`WINDOWS_STATUS=IMPLEMENTED_REAL_VALIDATION_PENDING`

## macOS

Not yet public. No public one-command is documented here.

`MACOS_STATUS=NOT_PUBLIC`

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

- Port 3434 in use: do not kill other processes. Free the port yourself.
- Environment not running: re-run the one-line installer (Resume)
- UI cannot connect: confirm http://127.0.0.1:3434/api/living
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
