# Windows upgrade (Citizen 0.2 WSL2 adapter)

**Preflight — not a public release.**

## Upgrade path

1. Stop Citizen inside WSL:

   ```bash
   systemctl --user stop citizen-seed-living.service
   ```

2. Extract the new bundle over the existing Linux-filesystem checkout (preserve `CITIZEN_HOME`).
3. Re-run bounded adapter setup:

   ```powershell
   .\windows\Install-CitizenWsl2.ps1 -RepoLinuxPath /home/<user>/citizen-0.2.0
   ```

4. Verify release manifest locally (offline):

   ```powershell
   python3 scripts/verify_release_bundle.py <bundle-dir> --allow-pending-signature
   ```

## Identity and state

- `CITIZEN_HOME` remains on the Linux filesystem
- Identity, evidence, and sync semantics are unchanged from the Linux-certified core
- Platform metadata in `build.json` tracks adapter version separately from Citizen identity

## Limitations

- No in-place Windows Store WSL migration is performed by this bundle
- Rollback uses existing Linux mechanisms inside WSL (PARTIAL on 0.2.0 line)
