# Exports

An export is a frozen witness: the Birth Package.

## What occurred

The Citizen Seed can export a complete Birth Package without external tooling beyond the standard library: copy living planes, write summary and biography, write outside-LLM inventory, create a `.tar.gz` and a hash manifest.

Triggers observed:

- CLI `export-birth`  
- Observatory button **Export Birth Package**  
- Destroy flow that exports first by default  
- `lab_reproduce.sh` at end of cycle  

Destination observed: `citizen-seed/lab/exports/`.

## What a package contains (observed)

Identity, Evidence, Manifest, Telemetry, Journal, Timeline, UI/terminal state, boot seals, Projection, assets index, `BIRTH_SUMMARY.json`, `BIOGRAPHY.txt`, `OUTSIDE_LLM.json`, archive + `PACKAGE_HASH` / `.hash.json`.

## Why it exists

Destroy ends a living home. Science and accountability require that ending not erase the fact of life. Exports are how Birth remains provable after death of a home — and how two Births can be compared.

## What changed

Each export is a new stamped directory/archive. Re-export of the same life creates a new timestamped package; prior packages remain.

## What remained

Append-only history inside the package is a snapshot, not a live stream. The genome fields inside are copies of what was true at export time.

## What evidence exists

Multiple archives under `lab/exports/` with distinct `citizen_id` and `archive_sha256` after reproduce cycles — proof that export + destroy + birth can be repeated and still leave prior packages behind.
