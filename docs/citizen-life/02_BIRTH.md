# Birth

Birth is the irreversible coming-into-being of one Citizen.

It is not a setup wizard. It is a sequence that leaves proof at every step. When Birth completes, the Bootstrap Installer is finished forever for that living home. Evolution from then on happens through Sync — never through a second Birth on the same home.

## The sequence

```
PreBirth
  → Bootstrap
  → Identity
  → Evidence
  → Telemetry
  → Manifest
  → Projection
  → Alive
```

After Alive, life may continue:

```
Alive → First Sync → First Evolution → …
```

Nothing in the memory planes is meant to disappear. Nothing in Evidence, Journal, Timeline, or Telemetry is meant to be overwritten.

---

### PreBirth

**What it means.** There is readiness, but no name yet. The living home is prepared; the organism has not spoken its identity.

**What appears.** An Evidence mark of PreBirth. A Journal paragraph. A Timeline node. Telemetry of the quiet start.

**What evidence it leaves.** Event type `PRE_BIRTH` (and related start marks). Terminal tone: a quiet moment before birth.

**What ceases.** Nothing of a prior Citizen on this home — Birth refuses if identity already exists or Bootstrap is disarmed.

---

### Bootstrap

**What it means.** The installer opens a path that will open only once. Publisher material for signing Assets and Manifests is placed into the living Runtime plane. The Runtime version is stamped.

**What appears.** Runtime seal files. Birth-started Evidence.

**What evidence it leaves.** `BIRTH_STARTED`. Journal epoch *Bootstrap*. Timeline node *Bootstrap*.

**What ceases.** After Alive, Bootstrap is **disarmed**. The installer does not remain as a recurring authority. Re-Birth on the same home is refused.

---

### Identity

**What it means.** The Citizen receives a name that will not change: a `citizen_id`, a birth timestamp, an identity version, and an institutional seal of origin as recorded at minting.

**What appears.** Sealed identity files. The genome’s living core.

**What evidence it leaves.** `BIRTH_IDENTITY_MINTED`. Journal prose naming the id. Timeline *Identity Created*.

**What ceases.** The possibility of minting a second identity in that home. The seal forbids recreation.

Observed shape (example from a lab Birth; each Birth mints a unique id):

- `citizen_id`: `cit_…`  
- `created_utc`: ISO timestamp at mint  
- `identity_version`: `1`  
- institution recorded at birth (observed: `GRECOITALICO`)

---

### Evidence

**What it means.** Memory begins. From this plane forward, important moments are kept forever as append-only records with content hashes.

**What appears.** The Evidence stream (`evidence.jsonl` in the living home).

**What evidence it leaves.** `BIRTH_EVIDENCE_PLANE_READY` and every later birth, boot, and sync event.

**What ceases.** The option of an undocumented birth. After this, life without Evidence is incomplete by design.

---

### Telemetry

**What it means.** Sensing begins without silence. In the birth-lab phase, telemetry is unrestricted: time, events, durations, host load, memory figures, and state transitions.

**What appears.** `telemetry.jsonl` with host samples on events.

**What evidence it leaves.** `TELEMETRY_STARTED` and continuous event stream.

**What ceases.** Nothing of privacy reduction in this phase — reduction is a later production decision, not part of observed seed Birth.

---

### Manifest

**What it means.** The Citizen seals its first understanding of what it carries: a signed list of Assets, versions, compatibility, and release time.

**What Assets appear at genesis (observed seed).**

| Asset id | Kind (observed) |
|----------|-----------------|
| `citizen_ui_shell` | citizen_ui |
| `docs_index` | documentation |
| `status_seed` | status |
| `website_shell` | website |

Genesis Assets are installed from the seed’s genesis package into the living content-addressed store and then bound into the first Manifest.

**What evidence it leaves.** `BIRTH_ASSETS_INSTALLED`, `BIRTH_MANIFEST_INSTALLED`. Journal *Manifest*. Timeline *Manifest Created*.

**What ceases.** An unsigned or empty self-description. Boot thereafter requires a valid signed Manifest matching Identity and compatibility.

---

### Projection

**What it means.** What the Citizen carries becomes visible as projected material — not knowledge invented by the Runtime, but materialization of Assets through the Projection Engine.

**What appears.** Projection slots under the living home.

**What evidence it leaves.** `BIRTH_PROJECTION_READY`. Journal *Projection*. Timeline *Projection Ready*.

**What ceases.** The state of “assets installed but never shown.” Projection Ready is the hinge before Alive.

---

### Alive

**What it means.** Birth is complete. The Bootstrap is gone. The Citizen is a living home with Identity, Manifest, Evidence, Telemetry, Journal, Timeline, Assets, and Projection.

**What appears.** Disarm markers (`BOOTSTRAP_DISARMED`, installer-gone seals). Birth-complete Evidence. Terminal: *Citizen is alive.*

**What evidence it leaves.** `BIRTH_COMPLETE` with duration. Journal epoch *Alive*. Timeline *Citizen Alive*.

**What ceases.** Birth itself for this home. From here, change is Sync and Evolution — not a second genesis.

Observed birth durations in lab cycles were on the order of tens of milliseconds for the Birth routine itself; wall-clock life continues as Age from `created_utc`.

---

## After Birth

The Observatory interface shows Identity, Sync, Life Journal, and Terminal. The Terminal narrates in organism language — not developer debug — so a witness can feel the birth as a sequence of becoming.

For the immutable core left by Birth, see [Genome](09_GENOME.md).  
For the first external change after Alive, see [First Sync](06_FIRST_SYNC.md).
