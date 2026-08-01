# Genome

Some things about a Citizen are clothes. Some are organs. A few are **DNA**.

The genome is everything that must remain continuous for the organism to still be *the same Citizen* after change, export, or Runtime renewal.

## The immutable core

| Element | Meaning |
|---------|---------|
| **Citizen ID** | The unique name minted at Birth. Never reminted in that life. |
| **Birth Timestamp** | `created_utc` — when Identity appeared. Age is counted from here. |
| **Genesis Manifest** | The first sealed Manifest of that life (archived when Sync advances). The first self-description. |
| **Birth Hash / Asset lineage** | Content hashes of genesis Assets and the asset-version seal of the first Manifest — the cryptographic fingerprint of what was carried at Birth. |
| **Root Signature** | Publisher HMAC (seed) / institutional signature verifying Manifest and Assets. Proof that genesis was not anonymous noise. |
| **Cryptographic Lineage** | The chain from genesis Manifest through later Manifests (`prev` / history archives, signed successors). Sync adds links; it does not cut the chain. |

Together these are DNA because:

1. **Identity** answers *who*.  
2. **Birth time** answers *when life began*.  
3. **Genesis Manifest + hashes** answer *what was first true*.  
4. **Signatures + lineage** answer *why we trust that truth*.

Assets may be replaced. Projection may be refreshed. Telemetry grows. Journal grows. The genome is the continuity criterion.

## What the genome is not

- Not the Observatory UI layout.  
- Not the current Asset fashion after Sync.  
- Not the LLM (the seed life did not require one).  
- Not the Bootstrap Installer (which disappears after Birth).

## Why DNA language

If Sync could change `citizen_id`, every update would be a fake death. If Evidence could be rewritten, lineage would be theater. Genome language forbids both.

## Evidence of genome in the wild

- Identity files sealed at Birth.  
- Manifest history retaining prior releases after Sync.  
- Birth Packages freezing Identity + Manifest + Evidence at export time.  
- Destroy → Birth producing a **new** genome (new id), proving genomes are per-life, not per-repository.

Example genome surface from one lab life (illustrative; each Birth differs):

```text
Citizen ID:        cit_636f7a5fedbadd41324116d02b173de6
Birth Timestamp:   2026-08-01T05:33:34Z
Runtime at life:   0.1.0
Compatibility:     seed-2026.1
Post-sync citizen: 1.0.1-seed
Asset version:     sha256:ffb9970b3b0dd10dc066eb25fbc2d834476f942920cf0545d913724c684b5a55
```

The repository seed is not the genome. The **living home** (and its exports) is.
