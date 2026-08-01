# Citizen Seed 0.1

**First Empirical Birth — Certified**

Public, self-contained seed. No private founder environment required.

```bash
git clone <url>
cd citizen-seed
./install.sh
```

→ Birth → permanent OS service → living UI `http://127.0.0.1:3434/`

After install, Citizen wakes on OS boot (systemd / LaunchAgent / Windows Service). Do not re-run `install.sh` for daily life. Terminal is debug-only.

| Doc | Role |
|-----|------|
| [INSTALL.md](INSTALL.md) | Install steps |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | What 0.1 is |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [CERTIFIED_0.1.md](CERTIFIED_0.1.md) | Freeze law |
| [docs/citizen-life/GENESIS.md](docs/citizen-life/GENESIS.md) | Constitution of the Citizen |
| [docs/citizen-life/](docs/citizen-life/) | Citizen Life record |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Planes diagram |

Living ops (this tree): `ops/living_server.py` · service scripts under `scripts/` · CONRRAD docs `docs/runtime/` (repo).

Legacy Observatory debug serve remains: `python3 -m citizen_seed serve` (port **8787**).

## Law

Runtime executes Assets only. Business knowledge lives in Assets, never in Runtime.

## Not in 0.1

CONRRAD · Builder · HARLEMM · Planner · Scheduler · IA

## Versions

See `VERSION` (`0.1.0`). Future lines: 0.2, 0.3, 1.0 — without rewriting 0.1.
