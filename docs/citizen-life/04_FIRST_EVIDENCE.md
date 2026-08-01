# First Evidence

Memory is not a convenience. For the Citizen, memory is the condition of being accountable for having lived.

## What occurred

When the Evidence plane became ready at Birth, the Citizen began an append-only stream of sealed events. Each record carries time, citizen id (or `pre_birth` before naming), event type, payload, and a content hash of the envelope.

The first explicit readiness mark was Evidence-plane-ready; around it clustered PreBirth, Bootstrap, Identity, Assets, Manifest, Projection, and Alive.

## Why it occurred

A birth without Evidence is a rumor. Sync without Evidence is an unverifiable mutation. The Life Journal tells the story in prose; Evidence holds the forensic spine that Journal and Timeline point to.

## What changed

From that moment, important actions left durable marks: boots, sync states, verify failures, completions. The Observatory can open a Timeline node and surface related Evidence.

## What remained

Evidence is never edited and never deleted by design. Destroying the living home removes the active stream unless a Birth Package was exported first — in which case the stream survives outside the home.

## What evidence exists

- Living stream: `evidence.jsonl` in the Citizen home.  
- Event types observed across Birth and Sync include, among others:  
  `PRE_BIRTH`, `BIRTH_STARTED`, `BIRTH_IDENTITY_MINTED`, `BIRTH_EVIDENCE_PLANE_READY`, `TELEMETRY_STARTED`, `BIRTH_ASSETS_INSTALLED`, `BIRTH_MANIFEST_INSTALLED`, `BIRTH_PROJECTION_READY`, `BIRTH_COMPLETE`, boot marks, and `UPDATE_STATE_*` / update completion marks.  
- Birth Package copies of the evidence plane.  
- Timeline `evidence_types` / `evidence_hashes` linking story nodes to records.

Evidence does not replace the Journal. Evidence is the proof; Journal is the biography.
