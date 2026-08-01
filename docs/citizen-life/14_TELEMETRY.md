# Telemetry

Telemetry is the Citizen’s continuous sensing — the instrumented pulse of life.

## What occurred

From PreBirth and Birth onward, events were appended to `telemetry.jsonl` in the living home. In the birth-lab phase, sensing was unrestricted: no privacy trimming, no sampling reduction.

## What a telemetry event holds (observed)

- Clock time and epoch time  
- Level (info, warning, error)  
- Event name  
- Citizen id when known  
- Duration when measured  
- Event-specific fields (asset counts, releases, slots, errors)  
- **Host sample**: CPU user/system time, RSS, page faults, context switches, load averages, memory info, disk free when available, process status fields on Linux  

## Why it exists

Evidence answers “what was decided.” Telemetry answers “what the body was doing while deciding” — load, duration, failures, and environment.

## What changed across life

The stream only lengthens. Sync and boot add more beats. Destroy ends the living stream unless exported.

## What remained

Append-only discipline. Host sampling on emit in the lab implementation.

## What evidence exists

- Living `telemetry/` plane.  
- Birth Package copy.  
- Events such as `prebirth`, `birth.*`, `telemetry.started`, `boot.*`, `sync.*`.  
- Empirical runs showing Birth durations on the order of ~10–15 ms for the install routine and boot on the order of ~5 ms in lab measurements (host-dependent).

Telemetry is not the Life Journal. Telemetry is the sensor log; the Journal is the biography.
