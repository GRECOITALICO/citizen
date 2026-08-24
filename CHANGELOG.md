# CHANGELOG — Citizen Seed

## [windows-wsl2-0.4.2.1] — 2026-08-24 — Public Windows WSL2 install door

### Added

- Public one-instruction Windows bootstrap: `install/windows.ps1`
- Guest bootstrap: `install/windows-guest.sh`
- Same public OCI image as Linux (`ghcr.io/grecoitalico/citizen@sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da`)
- Provenance: `install/WINDOWS_PROVENANCE.json`

Windows is implemented, not certified. Real Windows E2E is P0.9H.2.


## [0.1.0] — 2026-08-01 — Certified / First Empirical Birth

### Added

- Installable Birth via `./install.sh`  
- Minimal Runtime: load / validate / project / sync / update Assets  
- Identity, Manifest, Evidence, Telemetry, Life Journal, Timeline  
- Observatory UI: Identity, Sync, Journal, Terminal  
- Local update package path `assets/updates/`  
- Birth Package export and Destroy for reproducibility  
- Outside-LLM lab report  

### Frozen

- Citizen Seed **0.1** certified; do not alter this line’s history. Next: 0.2+

### Not included

- CONRRAD, Builder, HARLEMM, Planner, Scheduler, IA  
- Network update channel  
- Production PKI (dev HMAC only)
