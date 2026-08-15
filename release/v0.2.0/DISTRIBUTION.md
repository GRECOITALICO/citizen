# Citizen 0.2 Distribution Contract

No distribution destination is configured by this source line.

A future authorized immutable release location must contain one directory per
release identity and must refuse overwrite. Its required contents are:

```text
citizen-<version>-linux.tar.gz
build.json
release-manifest.json
release-decision.json
manifest.sig
trust-root.ed25519.pub
```

`manifest.sig` and `trust-root.ed25519.pub` are intentionally absent from
an unsigned source-line build. They must come from the protected signing
authority, never from the artifact itself. Publication, tagging, cloud stores,
and infrastructure changes are outside this contract.

`trust-root.ed25519.pub` is an externally supplied JSON trust-root document in
the `citizen-release-trust-root/v1` format defined by `CONTRACT.md`. Its public
key uses the authority's DER SPKI Base64 representation; Citizen converts it
only at the verification boundary. The filename is a distribution artifact
name, not permission to embed a production key in source.
