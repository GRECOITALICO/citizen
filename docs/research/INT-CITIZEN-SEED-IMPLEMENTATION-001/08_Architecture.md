# 08 — Architecture

```
Public tree (citizen-seed/)
├── install.sh          # Birth entry (then gone)
├── runtime/            # Tiny Runtime (Python)
├── assets/
│   ├── genesis/        # Birth Assets
│   └── updates/        # Sync packages
├── ui/                 # Minimal GUI static
├── identity/ …         # Placeholders (living state ≠ here)
└── docs/research/…

Living home (CITIZEN_HOME, default .citizen/)
├── identity/
├── manifest/
├── evidence/
├── telemetry/
├── diary/
├── assets/
├── projection/
├── updates/
├── runtime/            # publisher secret + version stamp
├── boot/               # DISARMED, LAST_BOOT
└── ui/                 # terminal + sync_state
```

Asset-First: capability enters only as signed Assets. Runtime has no institutional knowledge.
