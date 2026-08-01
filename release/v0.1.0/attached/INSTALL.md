# INSTALL — Citizen Seed 0.1

Requirements: Python **3.11+**, a POSIX shell, network only if cloning from remote.

## Third-party Birth

```bash
git clone <citizen-seed-repository-url>
cd citizen-seed
./install.sh
```

This runs, without further prompts:

1. Birth (once)  
2. Boot → Citizen Alive  
3. Sync (applies local update package if present)  
4. Observatory UI at `http://127.0.0.1:8787/`

Stop the UI with Ctrl+C. The living Citizen remains under `.citizen/` (or `CITIZEN_HOME`).

## Manual commands

```bash
export PYTHONPATH=runtime
python3 -m citizen_seed install
python3 -m citizen_seed boot
python3 -m citizen_seed update
python3 -m citizen_seed serve
```

## Reproducibility lab

```bash
./lab_reproduce.sh
```

Destroy (export first) → Birth → Sync → Export → lab-report.

## Notes

- Re-running Birth on the same home is refused after Bootstrap disarms.  
- Publisher secret for seed verification is derived from `assets/publisher.secret.example` at Birth (dev HMAC).  
- No private monorepo, VPN, or founder machine is required.
