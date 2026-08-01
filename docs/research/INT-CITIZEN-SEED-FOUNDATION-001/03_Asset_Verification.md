# 03 — Asset Verification

## Law

```text
Runtime → Loader → Assets → Projection
```

Never the reverse. Runtime does not embed business catalogs.

## Genesis Assets (0.1)

| asset_id | role |
|----------|------|
| citizen_ui_shell | citizen_ui |
| docs_index | documentation |
| status_seed | status |
| website_shell | website |

Installed at Birth from `assets/genesis/`, content-addressed and HMAC-signed into the living store, bound by Manifest, then projected.

## Update Assets

Signed packages under `assets/updates/<id>/` with `manifest.json` + per-hash payloads. Sync verifies signatures before apply.

## Verification method

- Boot: `verify_manifest` + `verify_manifest_assets`  
- Sync: verify candidate Manifest and each Asset signature  
- Reject unsigned / mismatched compatibility / wrong citizen binding when set
