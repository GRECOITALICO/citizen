# 09 — Known Limitations

1. Publisher HMAC is **dev-only** (`publisher.secret.example`). Not production PKI.  
2. Update channel is a **local directory** (`assets/updates/`), not network.  
3. UI is local HTTP only — no auth, no remote.  
4. Runtime version must match Manifest exactly (`BOOT_RUNTIME_VERSION_FAIL`).  
5. No multi-Citizen, no cluster, no CONRRAD control plane.  
6. Genesis meta may show `pending` signatures; Birth re-signs into the living store.  
7. `seed_package/` is legacy duplicate of genesis/updates — prefer `assets/`.  
8. Installer “disappearance” is disarm + refuse re-Birth, not deleting `install.sh` from the clone.

STOP — seed scope only. No Planner, Scheduler, Builder, HARLEMM, or full CONRRAD.
