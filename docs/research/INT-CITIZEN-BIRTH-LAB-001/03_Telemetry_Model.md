# 03 — Telemetry Model

## Law (lab phase)

Capture **everything**. No privacy. No optimization. No reduction.

## Every event includes

- Clock time + epoch  
- Level (info / warning / error)  
- Event name  
- Duration when applicable  
- Citizen ID when known  
- **Host sample**: CPU user/system, RSS, page faults, context switches, loadavg, MemAvailable, disk free, VmRSS  

## Stream

`CITIZEN_HOME/telemetry/telemetry.jsonl` — append-only.

Production sampling is **out of scope** for this lab.
