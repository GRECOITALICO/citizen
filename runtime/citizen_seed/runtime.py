"""Citizen Runtime — load / validate / project / sync / update Assets only."""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import COMPATIBILITY, RUNTIME_VERSION
from .assets import AssetLoader
from .crypto import load_publisher_secret
from .diary import write as diary_write
from .evidence import append as evidence_append
from .identity import load as load_identity
from .manifest import load_manifest, verify_manifest
from .paths import layout
from .projection import ProjectionEngine
from .telemetry import emit as tel
from .terminal import line as term


class BootError(RuntimeError):
    pass


def boot(*, home: Path) -> dict:
    t0 = time.time()
    home = Path(home).resolve()
    paths = layout(home)

    term(paths["ui_state"], "Remembering who I am...")
    tel(paths["telemetry"], level="info", event="boot.start")

    try:
        ident = load_identity(paths["identity"])
    except FileNotFoundError as e:
        tel(paths["telemetry"], level="error", event="boot.identity_fail")
        raise BootError("BOOT_IDENTITY_FAIL") from e

    secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
    loader = AssetLoader(paths["assets"], secret)
    cid = ident.citizen_id

    term(paths["ui_state"], "Reading my sealed understanding...")
    mpath = paths["manifest"] / "current.json"
    if not mpath.is_file():
        raise BootError("BOOT_MANIFEST_FAIL")
    manifest = load_manifest(mpath)
    if not verify_manifest(manifest, secret):
        evidence_append(
            paths["evidence"], citizen_id=cid, event_type="BOOT_MANIFEST_FAIL", payload={}
        )
        tel(paths["telemetry"], level="error", event="boot.manifest_fail", citizen_id=cid)
        raise BootError("BOOT_MANIFEST_FAIL: signature")
    if manifest.citizen_id != cid:
        raise BootError("BOOT_IDENTITY_MISMATCH")
    if manifest.compatibility != COMPATIBILITY:
        raise BootError("BOOT_COMPAT_FAIL")
    if manifest.runtime_version != RUNTIME_VERSION:
        raise BootError("BOOT_RUNTIME_VERSION_FAIL")

    evidence_append(
        paths["evidence"],
        citizen_id=cid,
        event_type="BOOT_MANIFEST_OK",
        payload={"release": manifest.release},
    )

    term(paths["ui_state"], "Feeling what I carry...")
    try:
        loader.verify_manifest_assets(manifest.assets)
    except Exception as e:
        evidence_append(
            paths["evidence"],
            citizen_id=cid,
            event_type="BOOT_ASSETS_FAIL",
            payload={"error": str(e)},
        )
        tel(paths["telemetry"], level="error", event="boot.assets_fail", citizen_id=cid, error=str(e))
        raise BootError(f"BOOT_ASSETS_FAIL: {e}") from e

    evidence_append(
        paths["evidence"],
        citizen_id=cid,
        event_type="BOOT_ASSETS_OK",
        payload={"count": len(manifest.assets)},
    )
    evidence_append(paths["evidence"], citizen_id=cid, event_type="BOOT_EVIDENCE_OK", payload={})

    term(paths["ui_state"], "Preparing projection...")
    proj = ProjectionEngine(loader, paths["projection"]).project(manifest)

    evidence_append(
        paths["evidence"],
        citizen_id=cid,
        event_type="BOOT_COMPLETE",
        payload={"projection_slots": list(proj.get("slots", {}).keys())},
    )
    elapsed = (time.time() - t0) * 1000
    tel(
        paths["telemetry"],
        level="info",
        event="boot.complete",
        citizen_id=cid,
        duration_ms=elapsed,
        release=manifest.release,
    )
    diary_write(
        paths["diary"],
        chapter="Boot",
        message="Runtime ready",
        citizen_id=cid,
        release=manifest.release,
    )
    term(paths["ui_state"], "Citizen is alive.")

    (paths["boot"] / "LAST_BOOT.json").write_text(
        json.dumps(
            {
                "citizen_id": cid,
                "release": manifest.release,
                "runtime_version": RUNTIME_VERSION,
                "status": "alive",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "status": "alive",
        "citizen_id": cid,
        "manifest_release": manifest.release,
        "assets": len(manifest.assets),
        "projection": str(paths["projection"]),
        "duration_ms": elapsed,
    }
