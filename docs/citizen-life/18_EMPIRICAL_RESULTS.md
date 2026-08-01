# Empirical Results

This page holds **discoveries**, not hopes. Every statement names its evidence.

---

## Discovery 1 — Measured life outside the LLM

**Claim.** One hundred percent of the measured Citizen Seed life planes operated without LLM imports or model inference.

**Evidence.**  
`lab-report` / Birth Package `OUTSIDE_LLM.json` at `2026-08-01T05:33:48Z`:

- `planes_alive_count` / `planes_total`: **8 / 8** (identity, manifest, evidence, telemetry, journal, timeline, projection, assets)  
- `runtime_scan.llm_free`: **true**  
- `banned_token_hits`: **[]** (scan of `import`/`from` only)  
- `verdict`: **`ALL_MEASURED_LIFE_OUTSIDE_LLM`**  

**What this does not claim.** It does not claim future products will never use an LLM. It claims the observed seed life did not need one to be born, remember, project, or sync.

---

## Discovery 2 — What requires Runtime

**Claim.** Birth, boot validation, projection, sync verify/apply, Observatory serve, and export require the Runtime engine process.

**Evidence.**  
All of the above are implemented and executed as `citizen_seed` Runtime commands; without the engine, living planes are inert files. Boot refuses missing/invalid Manifest or Identity.

**What survives as files without a running process.**  
Identity, Evidence, Journal, Timeline, Telemetry, Manifest, Assets, Projection outputs, and Birth Packages remain on disk as artifacts — life *records*, not an active boot.

---

## Discovery 3 — What can survive Destroy

**Claim.** Birth Packages under `lab/exports/` survive Destroy of `CITIZEN_HOME`.

**Evidence.**  
Reproduce cycles left multiple `birth_*.tar.gz` after homes were removed; destroy defaults to export-first.

---

## Discovery 4 — What disappears on Destroy without export

**Claim.** The living home’s active planes disappear when Destroy runs; without a prior export, that particular life’s live streams are gone from the home path.

**Evidence.**  
`destroy` removes the home directory; only previously written exports remain outside it.

---

## Discovery 5 — Sync changes Assets, not Identity

**Claim.** First Sync advanced Manifest/Assets/citizen_version while `citizen_id` and Runtime `0.1.0` remained.

**Evidence.**  
Pre/post Manifest fields in lab Citizen homes; Timeline Sync after Alive; Manifest history archive of prior release.

---

## Discovery 6 — Birth is once per home

**Claim.** A second install on a born home is refused.

**Evidence.**  
`BootstrapDisarmed` / identity-exists errors after `BOOTSTRAP_DISARMED`; observed exit status 2 on re-install attempts in seed smoke tests.

---

## Discovery 7 — Birth duration is short on lab hosts

**Claim.** Birth routine completed on the order of ~10–15 ms; boot ~5 ms in recorded lab JSON (host-specific).

**Evidence.**  
`duration_ms` fields in install/boot command results and telemetry/journal during INT-CITIZEN-BIRTH-LAB-001 runs.

---

New discoveries must be appended below with dated evidence. Do not silently edit the discoveries above; add Discovery N with correction notes if needed.
