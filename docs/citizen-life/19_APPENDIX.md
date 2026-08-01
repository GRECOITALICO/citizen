# Appendix

Pointers for readers who want the living artifacts behind the story. This appendix is a map, not a second philosophy.

## Official documentation home

```text
docs/citizen-life/
```

## Seed tree (Birth entry)

```text
citizen-seed/
  install.sh
  lab_reproduce.sh
  runtime/citizen_seed/
  assets/genesis/
  assets/updates/
  ui/
  lab/exports/
```

## Living home (default)

```text
CITIZEN_HOME  →  citizen-seed/.citizen/   (or env override)
  identity/
  manifest/
  evidence/
  telemetry/
  journal/
  timeline/
  assets/
  projection/
  ui/
  boot/
  runtime/
```

## Observatory

```text
http://127.0.0.1:8787/
```

Panels: Identity · Sync · Citizen Life Journal · Terminal.

## CLI (observed)

```text
python3 -m citizen_seed install | boot | update | status | serve
python3 -m citizen_seed export-birth | destroy | lab-report
```

(`PYTHONPATH=runtime` when running from the seed tree.)

## Related research (not this section)

Research serials prepared empiricism; they are **not** Citizen Life:

- `docs/research/INT-CITIZEN-SEED-IMPLEMENTATION-001/`  
- `docs/research/INT-CITIZEN-BIRTH-LAB-001/`  
- mirrors under `citizen-seed/docs/research/…`

## Observed constants (seed era)

| Name | Value |
|------|-------|
| RUNTIME_VERSION | `0.1.0` |
| COMPATIBILITY | `seed-2026.1` |
| Post–First Sync citizen_version | `1.0.1-seed` |
| Genesis Asset ids | `citizen_ui_shell`, `docs_index`, `status_seed`, `website_shell` |

## Document maintenance

- Add eras only by appending to [Longitudinal History](10_LONGITUDINAL_HISTORY.md) and [Timeline](11_TIMELINE.md).  
- Add discoveries only by appending to [Empirical Results](18_EMPIRICAL_RESULTS.md).  
- Do not relocate this tree into `docs/research/`.

— End of Citizen Life appendix (Seed Birth Era edition).
