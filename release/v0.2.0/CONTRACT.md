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

## External signature verification v1

The authority message is the ASCII bytes of the frozen `manifest_digest`
string (for example, `sha256:<64 lowercase hex>`). The signer and verifier do
not prehash it, add a newline, or reserialize the manifest. The standard
Ed25519 operation retains its defined internal cryptographic processing.

`signature.value` is standard Base64 encoding of exactly 64 raw Ed25519
signature bytes. The algorithm identifier remains `Ed25519`.

The verifier receives an external JSON trust root; no production public key is
hardcoded in Citizen:

```json
{
  "schema_version": "citizen-release-trust-root/v1",
  "key_id": "<authority key id>",
  "algorithm": "Ed25519",
  "public_key_format": "spki_der_base64",
  "public_key": "<AWS KMS GetPublicKey DER SPKI Base64>",
  "status": "ACTIVE"
}
```

For a signed bundle, `scripts/verify_release_bundle.py` requires
`--trust-root <path>`. It fails closed for a missing, malformed, inactive, or
mismatched trust root; wrong key ID or algorithm; non-Base64, truncated, or
trailing signature bytes; changed manifest digest; and invalid Ed25519
signatures. Pending authority manifests remain explicitly verifiable only with
`--allow-pending-signature`.

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
