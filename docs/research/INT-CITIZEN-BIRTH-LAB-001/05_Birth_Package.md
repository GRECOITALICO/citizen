# 05 — Birth Package

## Export Birth Package

CLI: `python3 -m citizen_seed export-birth`  
UI: button **Export Birth Package**  
API: `POST /api/export-birth`

## Contents

| Artifact | Meaning |
|----------|---------|
| `identity/` | Who was born |
| `evidence/` | Full evidence stream |
| `journal/` | Life Journal + legacy diary |
| `timeline/` | Timeline nodes |
| `telemetry/` | Full telemetry |
| `manifest/` | Sealed manifests |
| `projection/` | Projected assets |
| `ui/` | Terminal narrative |
| `BIRTH_SUMMARY.json` | Counts + metadata |
| `BIOGRAPHY.txt` | Readable life story |
| `OUTSIDE_LLM.json` | Empirical outside-LLM inventory |
| `assets_index.json` | Asset hash index |
| `*.tar.gz` + hash | Portable archive |

Destination: `citizen-seed/lab/exports/` (survives Destroy).
