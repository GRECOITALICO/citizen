# 01 — Birth Model

## Principle

Every installation is a **Birth**, not an install.

## Irreversible sequence

```
PreBirth
  → Bootstrap
  → Identity Created
  → Evidence Created
  → Telemetry Started
  → Manifest Created
  → Projection Ready
  → Citizen Alive
  → First Sync
  → First Evolution
```

## Laws

- Nothing disappears from Evidence / Journal / Timeline / Telemetry.
- Nothing is overwritten in those planes (append-only).
- Bootstrap disarms after Alive; Birth cannot repeat on the same home.
- Destroy Citizen clears the living home; prior Birth Packages remain under `lab/exports/`.

## Implementation

`installer.py` emits Terminal prose, Journal epochs, Timeline nodes, Evidence events, and Telemetry (with host metrics) at each step.
