# Append-Only Rules

Memory that can be silently rewritten is not memory. It is theater.

These rules apply to the Citizen’s living planes and to this Citizen Life documentation where marked longitudinal.

## The law

1. **Never edit** a prior record in Evidence, Telemetry, Life Journal, or Timeline.  
2. **Never delete** a prior record in those planes.  
3. **Only append** new moments.  
4. If a correction is needed, append a new record that says what was wrong and what is now known — with its own timestamp.  
5. Sync may archive a previous Manifest into history and write a new current Manifest; that is succession, not erasure of the archive.  
6. Destroy may remove a living home; it must not rewrite exported Birth Packages. Exports are frozen past.

## Why the law exists

Without it, Birth could be denied after the fact. Sync could pretend Evolution never happened. Longitudinal History could become propaganda.

## What may change in place

- Projection outputs may be refreshed from the current Manifest (derived views).  
- Sync button UI state may move (ephemeral posture).  
- `current.json` Manifest pointer advances while history retains the prior sealed file.

Derived and current pointers are not the Evidence stream. The stream remains append-only.

## Documentation rule

[Longitudinal History](10_LONGITUDINAL_HISTORY.md) follows the same spirit: chapters only grow downward. [Timeline](11_TIMELINE.md) gains nodes; it does not rewrite Birth.

## Evidence that the law is practiced

- JSONL files opened in append mode in the seed Runtime.  
- Journal API that only writes new lines.  
- Timeline API that only appends nodes.  
- Evidence envelopes with content hashes.  
- Lab Destroy leaving prior `lab/exports/` packages intact.
