# 08 — Longitudinal Evidence

## Reconstructible life

From Journal + Timeline + Evidence + Telemetry alone, an auditor can rebuild:

| Moment | Source |
|--------|--------|
| Nacimiento | Timeline PreBirth→Alive + Evidence BIRTH_* |
| Tiempo exacto | `ts` / `ts_epoch` on every plane |
| Duración | `duration_ms` on Journal / Telemetry |
| Errores | Telemetry `level=error` + Evidence FAIL events |
| Sync / Evolution | Timeline Sync/Evolution + UPDATE_* Evidence |
| Versiones | Journal `versions` + Manifest history |

## Continuity across Destroy

Living home is wiped; longitudinal **lab** memory persists in Birth Packages (`lab/exports/`).
