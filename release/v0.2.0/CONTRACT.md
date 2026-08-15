# Citizen 0.2 Canonical Release Contract

This document defines release provenance for the Citizen 0.2 source line. It is
not a release, approval, tag, signature, or publication.

Runtime manifests remain in `runtime/citizen_seed/manifest.py`. They bind a
living Citizen to its assets. Release manifests are separate JSON documents
created by `scripts/build_release.py`; they bind a distributable artifact to
an immutable source tree.

## Release manifest v1

`release-manifest.json` has exactly these versioned fields:

```text
schema_version
version
tag
source_commit
source_tree
build_id
platform
artifact
artifact_sha256
created_at
toolchain
runtime_version
compatibility
manifest_digest
signature
release_decision_id
```

`manifest_digest` is SHA-256 of canonical JSON with the
`manifest_digest` and detached `signature` fields excluded. A protected
Ed25519 signer signs that digest later, without altering what it attests to.

## Decision v1

`release-decision.json` is a separate authorization object. Its status is
one of `PROPOSED`, `APPROVED`, or `REJECTED`. The builder emits only
`PROPOSED`. Build success never authorizes a release.

## Signing boundary

The builder writes the signature state `PENDING_AUTHORITY`. It has no
private-key option and does not read or write private keys. An external
protected Ed25519 authority must provide the signed digest and a public trust
root during an authorized release mission.

## Linux build recipe

From a clean checkout and an output directory outside that checkout:

```bash
python3 scripts/build_release.py --platform linux --output-dir /tmp/citizen-build-1
python3 scripts/build_release.py --platform linux --output-dir /tmp/citizen-build-2
sha256sum /tmp/citizen-build-1/citizen-0.2.0-linux.tar.gz \
          /tmp/citizen-build-2/citizen-0.2.0-linux.tar.gz
python3 scripts/verify_release_bundle.py /tmp/citizen-build-1 --allow-pending-signature
```

The source archive uses tracked files only, sorted Git paths, the source commit
timestamp, and normalized ownership. The builder rejects a dirty source tree
and records the source commit/tree, declared toolchain, dependencies, command,
environment, artifact path, artifact hash, and deterministic build ID.

The generated artifact contains `install.sh` and
`scripts/install_service_linux.sh`. This verifies packaging only; it is not
native Linux certification.
