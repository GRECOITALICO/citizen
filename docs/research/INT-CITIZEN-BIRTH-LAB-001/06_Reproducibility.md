# 06 — Reproducibility

## Cycle

```
Destroy Citizen  (export first)
  → Install Citizen (Birth)
  → Boot
  → Sync (optional)
  → Export Birth Package
  → lab-report
```

Script: `./lab_reproduce.sh`

## What must differ

- New `citizen_id`  
- New Birth timestamps  

## What must match structurally

- Same Timeline epoch set through Alive  
- Same Evidence event types through BIRTH_COMPLETE  
- Same outside-LLM verdict when planes are complete  

## Proof

Two Birth Packages under `lab/exports/` with different `citizen_id` and `archive_sha256` demonstrate repeated Birth.
