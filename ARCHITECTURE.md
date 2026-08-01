# Architecture Diagram — Citizen Seed

```text
                         ┌──────────────────────────┐
                         │   Bootstrap Installer    │
                         │   (one-click Birth)      │
                         └────────────┬─────────────┘
                                      │ mints once
                                      │ then DISARMS
                                      ▼
┌─────────────┐   boot    ┌───────────────────────┐   one-click   ┌──────────────┐
│  Identity   │◄──────────│   Citizen Runtime     │◄──────────────│   Updater    │
│  (sealed)   │           │   Manifest·Assets·Ev  │               └──────┬───────┘
└─────────────┘           └───────────┬───────────┘                      │
                                      │                                  ▼
                                      │                         ┌────────────────┐
                    ┌─────────────────┼─────────────────┐       │ Update Engine  │
                    ▼                 ▼                 ▼       │ signed only    │
              ┌──────────┐     ┌──────────┐     ┌────────────┐ └───────┬────────┘
              │  Assets  │     │ Evidence │     │ Projection │         │
              │  Loader  │     │ append   │     │ Engine     │◄────────┘
              └────┬─────┘     └──────────┘     └─────┬──────┘
                   │                                  │
                   │         ┌────────────────────────┤
                   │         ▼                        ▼
                   │   Website / Status / Docs / Citizen UI
                   │   (projection slots — never TS hardcode)
                   ▼
              Manifest (signed)
```

## Planes

| Plane | Mutability |
|-------|------------|
| Runtime | Rare |
| Assets | Daily Evolution |
| Identity | Never re-mint |
| Evidence | Append only |
| Manifest | Replace on signed Update |
| Projection | Regenerated from Assets |
| Installer | Gone after Birth |
| Updater | Lives with Citizen |

## Trust boundary

Update Engine + Asset Loader accept **HMAC-signed** Manifest and Asset payloads only (Seed). Arbitrary code paths are rejected.
