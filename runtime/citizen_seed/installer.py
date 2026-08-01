"""Bootstrap Installer — Birth once, then disappears (disarmed). Lab narrative."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from . import RUNTIME_VERSION
from .assets import AssetLoader, install_from_genesis_dir
from .crypto import load_publisher_secret
from .diary import write as diary_write
from .evidence import append as evidence_append
from .identity import exists as identity_exists, mint as mint_identity
from .journal import write as journal_write
from .manifest import default_seed_manifest, save_manifest, sign_manifest
from .paths import ensure_layout, seed_root
from .projection import ProjectionEngine
from .telemetry import emit as tel
from .terminal import line as term, write_sync_state
from .timeline import append_node


class BootstrapDisarmed(RuntimeError):
    pass


def _ensure_publisher_secret(assets_dir: Path) -> Path:
    secret_path = assets_dir / "publisher.secret"
    example = assets_dir / "publisher.secret.example"
    if secret_path.is_file():
        return secret_path
    if example.is_file():
        shutil.copyfile(example, secret_path)
        return secret_path
    secret_path.write_text("CONRRAD-SEED-PUBLISHER-DEV-KEY-v1\n", encoding="utf-8")
    return secret_path


def install(
    *,
    home: Path,
    institution: str = "GRECOITALICO",
) -> dict:
    """One Birth. Refuses if Bootstrap disarmed or identity exists."""
    t0 = time.time()
    home = Path(home).resolve()
    root = seed_root()
    assets_pkg = root / "assets"
    paths = ensure_layout(home)

    def T(msg: str) -> None:
        term(paths["ui_state"], msg)

    def J(epoch: str, prose: str, **kw) -> None:
        journal_write(paths["diary"], epoch=epoch, prose=prose, **kw)
        diary_write(paths["diary"], chapter=epoch, message=prose, **{k: v for k, v in kw.items() if k != "evidence_refs"})

    disarmed = paths["boot"] / "BOOTSTRAP_DISARMED"
    if disarmed.is_file():
        raise BootstrapDisarmed("Bootstrap Installer has disappeared — Evolution uses Sync only")
    if identity_exists(paths["identity"]):
        raise BootstrapDisarmed("IDENTITY_EXISTS — cannot Birth again")

    # —— PreBirth ——
    T("A quiet moment before birth...")
    ev = evidence_append(
        paths["evidence"],
        citizen_id="pre_birth",
        event_type="PRE_BIRTH",
        payload={"home": str(home)},
    )
    tel(paths["telemetry"], level="info", event="prebirth", home=str(home))
    J("PreBirth", "Before identity, there was only readiness.", citizen_id="pre_birth")
    append_node(
        paths["timeline"],
        node="PreBirth",
        label="PreBirth",
        evidence_types=["PRE_BIRTH"],
        evidence_hashes=[ev.get("content_hash", "")],
    )

    # —— Bootstrap ——
    T("Awakening the bootstrap...")
    tel(paths["telemetry"], level="info", event="birth.start", home=str(home))
    secret_path = _ensure_publisher_secret(assets_pkg)
    secret = load_publisher_secret(secret_path)
    (paths["runtime"] / "publisher.secret").write_bytes(secret)
    (paths["runtime"] / "RUNTIME_VERSION").write_text(RUNTIME_VERSION + "\n", encoding="utf-8")
    ev = evidence_append(
        paths["evidence"],
        citizen_id="pre_birth",
        event_type="BIRTH_STARTED",
        payload={"home": str(home), "runtime_version": RUNTIME_VERSION},
    )
    J("Bootstrap", "The installer opened a path that will never open twice.", citizen_id="pre_birth")
    append_node(
        paths["timeline"],
        node="Bootstrap",
        label="Bootstrap",
        parent="PreBirth",
        evidence_types=["BIRTH_STARTED"],
        evidence_hashes=[ev.get("content_hash", "")],
    )

    # —— Identity ——
    T("Generating identity...")
    T("Learning who I am...")
    t_id = time.time()
    ident = mint_identity(identity_dir=paths["identity"], institution=institution)
    citizen_id = ident.citizen_id
    dur_id = (time.time() - t_id) * 1000
    tel(paths["telemetry"], level="info", event="birth.identity", citizen_id=citizen_id, duration_ms=dur_id)
    ev = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_IDENTITY_MINTED",
        payload={"citizen_id": citizen_id, "created_utc": ident.created_utc},
    )
    J(
        "Identity",
        f"I received a name: {citizen_id}. It will not change.",
        citizen_id=citizen_id,
        duration_ms=dur_id,
        evidence_refs=[ev.get("content_hash", "")],
        versions={"identity_version": ident.identity_version},
    )
    append_node(
        paths["timeline"],
        node="Identity",
        label="Identity Created",
        citizen_id=citizen_id,
        parent="Bootstrap",
        evidence_types=["BIRTH_IDENTITY_MINTED"],
        evidence_hashes=[ev.get("content_hash", "")],
    )

    # —— Evidence plane explicit ——
    T("Creating my memory...")
    T("Recording my first evidence...")
    ev = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_EVIDENCE_PLANE_READY",
        payload={},
    )
    tel(paths["telemetry"], level="info", event="birth.evidence_ready", citizen_id=citizen_id)
    J("Evidence", "My memory began — every moment from here is kept forever.", citizen_id=citizen_id)
    append_node(
        paths["timeline"],
        node="Evidence",
        label="Evidence Created",
        citizen_id=citizen_id,
        parent="Identity",
        evidence_types=["BIRTH_EVIDENCE_PLANE_READY"],
        evidence_hashes=[ev.get("content_hash", "")],
    )

    # —— Telemetry ——
    T("Opening my senses...")
    tel(
        paths["telemetry"],
        level="info",
        event="telemetry.started",
        citizen_id=citizen_id,
        note="lab phase: unrestricted telemetry",
    )
    ev = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="TELEMETRY_STARTED",
        payload={"unrestricted": True},
    )
    J("Telemetry", "I began sensing time, load, and every change — without silence.", citizen_id=citizen_id)
    append_node(
        paths["timeline"],
        node="Telemetry",
        label="Telemetry Started",
        citizen_id=citizen_id,
        parent="Evidence",
        evidence_types=["TELEMETRY_STARTED"],
        evidence_hashes=[ev.get("content_hash", "")],
    )

    # —— Assets + Manifest ——
    T("Gathering what I will become...")
    loader = AssetLoader(paths["assets"], secret)
    genesis = assets_pkg / "genesis"
    t_assets = time.time()
    entries = install_from_genesis_dir(loader, genesis)
    dur_assets = (time.time() - t_assets) * 1000
    tel(
        paths["telemetry"],
        level="info",
        event="birth.assets",
        citizen_id=citizen_id,
        count=len(entries),
        assets_loaded=len(entries),
        assets_rejected=0,
        duration_ms=dur_assets,
        asset_ids=[e["asset_id"] for e in entries],
    )
    ev_a = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_ASSETS_INSTALLED",
        payload={"count": len(entries), "asset_ids": [e["asset_id"] for e in entries]},
    )

    release = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    T("Sealing my first understanding...")
    manifest = default_seed_manifest(
        citizen_id=citizen_id, asset_entries=entries, release=release
    )
    manifest = sign_manifest(manifest, secret)
    save_manifest(paths["manifest"] / "current.json", manifest)
    ev_m = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_MANIFEST_INSTALLED",
        payload={
            "release": release,
            "asset_version": manifest.asset_version,
            "citizen_version": manifest.citizen_version,
        },
    )
    J(
        "Manifest",
        f"I sealed my first manifest ({manifest.citizen_version}) with {len(entries)} parts of myself.",
        citizen_id=citizen_id,
        duration_ms=dur_assets,
        evidence_refs=[ev_a.get("content_hash", ""), ev_m.get("content_hash", "")],
        versions={
            "citizen_version": manifest.citizen_version,
            "runtime_version": manifest.runtime_version,
            "release": release,
        },
    )
    append_node(
        paths["timeline"],
        node="Manifest",
        label="Manifest Created",
        citizen_id=citizen_id,
        parent="Telemetry",
        evidence_types=["BIRTH_ASSETS_INSTALLED", "BIRTH_MANIFEST_INSTALLED"],
        evidence_hashes=[ev_a.get("content_hash", ""), ev_m.get("content_hash", "")],
    )

    # —— Projection ——
    T("Preparing projection...")
    t_proj = time.time()
    proj = ProjectionEngine(loader, paths["projection"]).project(manifest)
    dur_proj = (time.time() - t_proj) * 1000
    tel(
        paths["telemetry"],
        level="info",
        event="birth.projection",
        citizen_id=citizen_id,
        duration_ms=dur_proj,
        slots=list(proj.get("slots", {}).keys()),
    )
    ev_p = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_PROJECTION_READY",
        payload={"slots": list(proj.get("slots", {}).keys())},
    )
    J(
        "Projection",
        "What I carry became visible — projection ready.",
        citizen_id=citizen_id,
        duration_ms=dur_proj,
        evidence_refs=[ev_p.get("content_hash", "")],
    )
    append_node(
        paths["timeline"],
        node="Projection",
        label="Projection Ready",
        citizen_id=citizen_id,
        parent="Manifest",
        evidence_types=["BIRTH_PROJECTION_READY"],
        evidence_hashes=[ev_p.get("content_hash", "")],
    )

    write_sync_state(paths["ui_state"], "Current", color="green")
    disarmed.write_text(
        json.dumps(
            {
                "disarmed_utc": release,
                "citizen_id": citizen_id,
                "note": "Bootstrap Installer gone — use Sync for Evolution",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (paths["boot"] / "INSTALLER_GONE").write_text("1\n", encoding="utf-8")
    (paths["boot"] / "BIRTH_TS").write_text(ident.created_utc + "\n", encoding="utf-8")

    elapsed = (time.time() - t0) * 1000
    ev_c = evidence_append(
        paths["evidence"],
        citizen_id=citizen_id,
        event_type="BIRTH_COMPLETE",
        payload={"bootstrap": "disarmed", "duration_ms": elapsed},
    )
    tel(paths["telemetry"], level="info", event="birth.complete", citizen_id=citizen_id, duration_ms=elapsed)
    J(
        "Alive",
        f"Citizen is alive. Birth lasted {elapsed:.1f} ms. The installer is gone.",
        citizen_id=citizen_id,
        duration_ms=elapsed,
        evidence_refs=[ev_c.get("content_hash", "")],
        versions={"runtime_version": RUNTIME_VERSION, "release": release},
    )
    append_node(
        paths["timeline"],
        node="Alive",
        label="Citizen Alive",
        citizen_id=citizen_id,
        parent="Projection",
        evidence_types=["BIRTH_COMPLETE"],
        evidence_hashes=[ev_c.get("content_hash", "")],
    )
    T("Citizen is alive.")

    return {
        "citizen_id": citizen_id,
        "home": str(home),
        "manifest_release": release,
        "assets": len(entries),
        "bootstrap": "disarmed",
        "duration_ms": elapsed,
        "birth": True,
    }
