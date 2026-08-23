# Install CONRRAD Citizen 0.4.2

Requirements: Python **3.11+**.

Do **not** run `pip install conrrad-citizen`. PyPI still serves 0.4.1.

## Official path

Download the canonical wheel, verify SHA256, install that file, then birth.

```bash
WHEEL=conrrad_citizen-0.4.2-py3-none-any.whl
URL=https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2/release/0.4.2/${WHEEL}

curl -fsS -o "$WHEEL" "$URL"
echo "0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce  $WHEEL" | sha256sum -c

python3 -m venv ~/.citizen-env
~/.citizen-env/bin/pip install "./$WHEEL"
~/.citizen-env/bin/citizen install
```

Open http://127.0.0.1:3434/

Runtime package = **0.4.2**. Citizen can later evolve to **0.4.3**.
Do not treat those as the same version.

## What you get

install → birth → identity sealed → service or `citizen serve` → READY → local UI

Linux: `citizen start` / `citizen status` (systemd user unit).
Windows / macOS: no native service; use `citizen serve`.

## Optional Linux helper

`install.sh` in this repository downloads the **same canonical wheel**,
verifies the same SHA256, then runs `citizen install`.
It is a convenience wrapper, not a second artifact.

```bash
curl -fsSL https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2/install.sh | bash
```

## Provenance

- Artifact: `release/0.4.2/conrrad_citizen-0.4.2-py3-none-any.whl`
- SHA256: `0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce`
- SOURCE_COMMIT (inside the wheel): `73b2916458e671e9537f80500fd9e15fe9a4465b`
- Release-cut tree: `19c30a5522815dadb9fb6a9d6f68fbac7b3f6074`
- Details: `release/0.4.2/PROVENANCE.json`

## Historical rebuild

Wheel B (`0dbb7d46958575759ea90122dc38177066f812210c2496572ec35e1d8280e65c`)
was a previous public rebuild. It is retained under
`release/0.4.2-historical-public-rebuild/` and the old tag
`artifact-conrrad-citizen-0.4.2`. Do not use it for a new install.

## Recovery

- Port 3434 in use: choose another port with `CITIZEN_UI_PORT` and `citizen serve`
- Service not running (Linux): `citizen start`
- UI cannot connect: confirm `citizen status` or that `citizen serve` is running
- Sync failure: current Citizen is preserved; do not reinstall to recover

`citizen uninstall --purge` destroys identity and Evidence. That is not recovery.
