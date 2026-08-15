# RELEASE SOURCE NOTES — Citizen 0.2

**Citizen 0.2 source line — no official release has been created**

## Purpose

Provide a third party a self-contained tree to clone, install, and Birth one Citizen. Living knowledge enters only as signed Assets. The Runtime does not hold business knowledge.

## Pipeline

```text
git clone → ./install.sh → Birth → Alive → Sync → UI
```

## Versions

| Item | Value |
|------|--------|
| Source version | 0.2.0 |
| Runtime | 0.2.0 |
| Compatibility | seed-2026.1 |
| Release authorization | Not established |

## Sync lifecycle (UI)

Current → Update Available → Updating → Updated → Evidence Stored (evidence event)

## Isolation

Stdlib Python only. No dependency on a private monorepo at runtime. Canonical Assets live under `assets/`. Legacy `seed_package/` is not required for Birth.

## Integrity

Journal and Timeline are append-only. Destroy does not rewrite prior Birth Packages under `lab/exports/`.

## Historical preservation

The 0.1 certified line remains historical evidence. This source line does not
rewrite it; see `CERTIFIED_0.1.md` and `release/v0.1.0/`.
