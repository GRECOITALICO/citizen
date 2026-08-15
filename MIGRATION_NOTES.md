# Isolation notes — Citizen 0.2 source line

## Public artifact

This tree is intended to run **alone**: clone the seed directory (or a future public repository that contains only this tree), run `./install.sh`, Birth a Citizen.

## No runtime dependency on private monorepo

| Check | Result |
|-------|--------|
| Python third-party packages | None (stdlib only) |
| Imports of CONRRAD / HARLEMM / Builder | None |
| Absolute founder paths in Runtime | None |
| Birth Assets source | `assets/genesis/` inside this tree |
| Update packages source | `assets/updates/` inside this tree |

## Legacy

- `seed_package/` — duplicate residue; **not** used by Runtime Birth path.  
- Research packs under `docs/research/` — evidence of how 0.1 was built; not required to Birth.  
- Official life narrative (separate): monorepo `docs/citizen-life/` may accompany publication later; Seed Birth does not read it.

## Publisher secret

Dev HMAC material comes from `assets/publisher.secret.example` at Birth. The
separate release contract accepts only externally supplied Ed25519 signing;
private production key material is out of scope for this source line.
