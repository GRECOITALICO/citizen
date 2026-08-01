# 04 — Birth Pipeline

## Automated path

`install.sh`:

1. `install` (Birth) if not disarmed  
2. `boot`  
3. `update` (Sync; no-op safe if already current)  
4. `serve` Observatory  

## Manual-free criterion

No founder MFA, no private Redis, no monorepo scripts, no interactive prompts in the happy path.

## Refusal

Second Birth on same home → Bootstrap disarmed / identity exists.
