# CONRRAD Citizen

A Citizen is a living local identity. It is born once, does Work, keeps
Evidence and History, and can later Sync to a new Citizen version without
becoming someone else.

Runtime package = **0.4.2**

Citizen can later evolve to **0.4.3**. Those are not the same number.

PyPI is not the install path. `pip install conrrad-citizen` currently
resolves to **0.4.1** and must not be used.

## Install

1. Download the canonical wheel from the immutable public tag.
2. Verify SHA256.
3. `pip install` that local file.
4. Run `citizen install`.

```bash
WHEEL=conrrad_citizen-0.4.2-py3-none-any.whl
URL=https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-runtime-0.4.2/release/0.4.2/${WHEEL}
curl -fsS -o "$WHEEL" "$URL"
echo "0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce  $WHEEL" | sha256sum -c
python3 -m venv ~/.citizen-env
~/.citizen-env/bin/pip install "./$WHEEL"
~/.citizen-env/bin/citizen install
```

Then open http://127.0.0.1:3434/

On Linux, `citizen install` starts the systemd user service.
On Windows and macOS there is no native service: run `citizen serve`.

See [INSTALL.md](INSTALL.md) for the same path with recovery notes.

## Versions

| Field | Value |
|---|---|
| Runtime / package | 0.4.2 |
| Embedded SOURCE_COMMIT | `73b2916458e671e9537f80500fd9e15fe9a4465b` |
| Release-cut tree | `19c30a5522815dadb9fb6a9d6f68fbac7b3f6074` |
| Artifact SHA256 | `0b4eb6d336352901e783f747bc5f2cc1775f0822ec1be17c145143ea6a4457ce` |
| Immutable tag | `citizen-runtime-0.4.2` |

A previous public rebuild (Wheel B, `0dbb7d…`) is historical only.
See `release/0.4.2-historical-public-rebuild/`.

## After install

- `citizen status` — living Citizen vs runtime
- `citizen work` — documented Work
- `citizen sync` — evolution when a verified package is available (not a reinstall)

Failed Sync leaves the current Citizen in place.

## Historical 0.1 seed

The original certified 0.1 seed record remains in this repository
([CERTIFIED_0.1.md](CERTIFIED_0.1.md), [docs/citizen-life/](docs/citizen-life/)).
It is not the 0.4.2 install path.
