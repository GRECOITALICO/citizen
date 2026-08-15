# Public tree — Citizen 0.2 source line

```text
citizen-seed/
  VERSION                 # 0.2.0
  CERTIFIED_0.1.md
  INSTALL.md
  CHANGELOG.md
  RELEASE_NOTES.md
  README.md
  install.sh              # Birth → Alive → Sync → UI
  lab_reproduce.sh
  pyproject.toml
  runtime/citizen_seed/   # Runtime (stdlib)
  assets/genesis/         # Birth Assets
  assets/updates/         # Sync packages (+ README for future)
  assets/publisher.secret.example
  ui/                     # Observatory static
  identity|evidence|manifest|telemetry/  # placeholders (living state = .citizen/)
  docs/citizen-life/      # GENESIS + official life record (ships with 0.1)
  docs/research/          # foundation & lab serials
  release/v0.1.0/         # Historical 0.1 material (preserved)
  release/v0.2.0/         # 0.2 release/distribution contracts (not a release)
  ARCHITECTURE.md
```

Living state after Birth: `.citizen/` (gitignored).  
Exports: `lab/exports/` (gitignored).

Do not require files outside this tree to Birth.
