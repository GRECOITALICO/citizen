# 04 — Timeline Model

## Purpose

A visual, irreversible spine of life — not only files.

## Nodes

Birth → Identity → Manifest → Projection → Evidence → Alive → Sync → Evolution

(Implementation order follows Birth Model; UI shows chronological append order.)

## Each node

- `node` / `label`  
- `parent`  
- `evidence_types` / `evidence_hashes`  
- Opens related Evidence via `/api/timeline/node?node=`

## Storage

`CITIZEN_HOME/timeline/timeline.jsonl` — append-only.
