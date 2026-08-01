# RELEASE NOTES — Citizen Seed 0.1

**Citizen Seed 0.1 — First Empirical Birth — Certified**

## Purpose

Provide a third party a self-contained tree to clone, install, and Birth one Citizen. Living knowledge enters only as signed Assets. The Runtime does not hold business knowledge.

## Pipeline

```text
git clone → ./install.sh → Birth → Alive → Sync → UI
```

## Versions

| Item | Value |
|------|--------|
| Seed release | 0.1 |
| Runtime | 0.1.0 |
| Compatibility | seed-2026.1 |
| Example post-Sync citizen_version | 1.0.1-seed (from packaged update) |

## Sync lifecycle (UI)

Current → Update Available → Updating → Updated → Evidence Stored (evidence event)

## Isolation

Stdlib Python only. No dependency on a private monorepo at runtime. Canonical Assets live under `assets/`. Legacy `seed_package/` is not required for Birth.

## Integrity

Journal and Timeline are append-only. Destroy does not rewrite prior Birth Packages under `lab/exports/`.

## Next releases

0.2 / 0.3 / 1.0 must not rewrite 0.1. See `CERTIFIED_0.1.md`.
