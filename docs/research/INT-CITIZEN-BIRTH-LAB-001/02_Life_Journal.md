# 02 — Life Journal

## Concept

**Citizen Life Journal** — a biography, not a log.

Path: `CITIZEN_HOME/journal/life_journal.jsonl`

## Fields

| Field | Role |
|-------|------|
| `epoch` | Life chapter (PreBirth, Identity, Alive, Sync, Evolution…) |
| `prose` | Narrative sentence reconstructing meaning |
| `ts` / `ts_epoch` | Exact time |
| `duration_ms` | How long the moment took |
| `evidence_refs` | Links into Evidence hashes |
| `versions` | Version seals at that moment |

## Rules

- Append-only  
- Never edit  
- Never delete  

Legacy `life.jsonl` may co-exist for continuity; biography rendering prefers `life_journal.jsonl`.
