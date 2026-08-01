# 01 — Runtime

## Role

Extremely small. Responsibilities only:

1. Load Assets  
2. Validate Assets  
3. Project Assets  
4. Synchronize Assets  
5. Update Assets  

## Forbidden in Runtime

- Institutional knowledge  
- Policies / planners / schedulers  
- CONRRAD / Builder Gen2 / HARLEMM logic  

Knowledge arrives later **only** as signed Assets.

## Package

`runtime/citizen_seed/` — Python 3.11+, stdlib HTTP UI.

Constants: `RUNTIME_VERSION`, `COMPATIBILITY` (`seed-2026.1`).

## Continuity

If Runtime ever changes, Identity, Evidence, Diary, and Manifest must be preserved. This seed updates Assets only; it does not replace the living home.
