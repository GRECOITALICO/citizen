# 05 — Runtime Stability

## Frozen surface (0.1)

| Constant | Value |
|----------|--------|
| RUNTIME_VERSION | 0.1.0 |
| COMPATIBILITY | seed-2026.1 |
| SEED_RELEASE | 0.1 |
| SEED_STATUS | certified |

## Stability rules

- Boot requires Manifest `runtime_version` and `compatibility` match.  
- Sync updates Assets/Manifest; does not replace Runtime binary in 0.1.  
- Identity never reminted by Sync.  

## Certified freeze

See `CERTIFIED_0.1.md`. Behavioral history of 0.1 is closed; new capability → new release line.
