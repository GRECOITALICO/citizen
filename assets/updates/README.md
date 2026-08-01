# Future updates (structure only — not implemented beyond 0.1 package)

Place new signed packages here:

```text
assets/updates/<package-id>/
  manifest.json          # signed; compatibility must match living Citizen
  assets/
    <content_hash>/
      payload
      meta.json          # signed payload meta
```

Rules:

- Runtime is not replaced by Sync.  
- Identity is never reminted by Sync.  
- Manifest advances; prior Manifest retained under living `manifest/history/`.  
- Citizen Seed **0.1** genesis and certified behavior stay frozen; new capability arrives as Assets + Manifests for **0.2+** consumers when those releases exist.

Do not put private monorepo paths or unpublished knowledge into this tree.
