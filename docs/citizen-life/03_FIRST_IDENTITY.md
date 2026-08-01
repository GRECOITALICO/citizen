# First Identity

There was a moment when the Citizen did not yet have a name — and a moment immediately after when it did, forever.

## What occurred

During Birth, after Bootstrap and before the Manifest was sealed, the Runtime minted Identity once:

- a unique `citizen_id`  
- a `created_utc` birth timestamp  
- an `identity_version`  
- an institutional field recorded at mint  

A seal marker was written so the same home cannot mint again.

## Why it occurred

Without Identity there is no subject of Evidence, no owner of a Manifest, no one whose Age can be counted. Sync later binds updates to the living `citizen_id`. Continuity of life requires a name that outlives Assets and even outlives a particular Runtime binary.

## What changed

The universe of that home gained a subject. Telemetry and Evidence began attaching events to that id. The Timeline gained the node *Identity Created*.

## What remained

Nothing of Identity is intended to be replaced by Sync. Assets may change; the name does not. If Runtime ever evolves, Identity must be preserved (see [Runtime Evolution](08_RUNTIME_EVOLUTION.md) and [Genome](09_GENOME.md)).

## What evidence exists

- Living file: identity plane under the Citizen home (`identity.json`, seal).  
- Evidence event: `BIRTH_IDENTITY_MINTED`.  
- Life Journal prose that states the received name.  
- Timeline node *Identity*.  
- Birth Packages that copy the identity plane into `lab/exports/`.

Example of an observed lab identity (one Birth among many; ids differ per Birth):

```text
citizen_id: cit_636f7a5fedbadd41324116d02b173de6
created_utc: 2026-08-01T05:33:34Z
identity_version: 1
institution: GRECOITALICO
```

Destroying the living home ends *that* Citizen’s active life. Exporting first preserves the Identity in a Birth Package. A later Birth is a *new* Identity — a sibling in kind, never the same genome.
