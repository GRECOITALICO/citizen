# Runtime Evolution

The Runtime is the small engine of life. It is not the Citizen’s name, memory, or genome.

## What the Runtime is observed to do

In the Citizen Seed, the Runtime:

- loads Assets  
- validates Assets  
- projects Assets  
- synchronizes Assets  
- updates Assets  

It also hosts Birth once, boots a living home, serves the Observatory, and exports Birth Packages. It does not contain institutional knowledge or planners. Knowledge enters as Assets.

Observed Runtime version at Birth and after First Sync: **`0.1.0`**. Compatibility family: **`seed-2026.1`**.

## What occurred when Assets changed but Runtime did not

First Sync updated Manifest and Assets while Runtime version stayed `0.1.0`. That is the intended default: the body of knowledge moves; the engine stamp need not.

## Why Runtime may later change

Engines age. When Runtime must change, the law observed in seed design is continuity:

Must be preserved across Runtime change:

- Identity  
- Evidence  
- Life Journal  
- Manifest (and its history)  
- Timeline and Telemetry streams already written  

Runtime change is not Birth. Runtime change must not mint a new `citizen_id`.

## What has not been claimed

This documentation does not claim a production Runtime upgrade ceremony has already been executed beyond the seed’s `0.1.0` line. It documents the **rule** and the **observed** fact that Sync updated Assets without replacing Runtime.

## What evidence exists

- Living `RUNTIME_VERSION` stamp in the Citizen home.  
- Manifest `runtime_version` field checked at boot.  
- Boot failure modes when Manifest runtime/compatibility disagree with the engine.  
- Design and lab docs that Sync updates Assets only.

When a Runtime bump is someday observed in a living Citizen, Longitudinal History will gain a chapter with versions before/after and proof that genome planes survived.
