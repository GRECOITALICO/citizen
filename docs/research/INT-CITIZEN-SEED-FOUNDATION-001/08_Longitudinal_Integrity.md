# 08 — Longitudinal Integrity

## Journal

Append-only (`life_journal.jsonl` / legacy `life.jsonl`). No edit API. No truncate API.

## Timeline

Append-only (`timeline.jsonl`). Grows indefinitely; never reset by Sync or Boot.

## Evidence

Append-only JSONL with content hashes. Sync lifecycle emits `UPDATE_STATE_*` and `SYNC_EVIDENCE_STORED`.

## Sync UI lifecycle ↔ evidence

| UI / posture | Evidence |
|--------------|----------|
| Current | prior complete / check-none |
| Update Available | UPDATE_STATE_UPDATE_AVAILABLE |
| Updating | CHECKING/DOWNLOADING/VERIFYING/READY/APPLY… |
| Updated | UPDATE_STATE_UPDATED |
| Evidence Stored | SYNC_EVIDENCE_STORED |

## Destroy

May remove living home; must not rewrite prior `lab/exports/` Birth Packages.
