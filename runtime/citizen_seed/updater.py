"""Updater — single button façade over Update Engine."""

from __future__ import annotations

from pathlib import Path

from .crypto import load_publisher_secret
from .paths import layout
from .update_engine import UpdateEngine, UpdateState


def one_click_update(*, home: Path, updates_dir: Path | None = None) -> dict:
    """One-click UPDATE. States + Evidence owned by UpdateEngine."""
    home = Path(home).resolve()
    paths = layout(home)
    secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
    engine = UpdateEngine(home, secret)
    updates = Path(updates_dir) if updates_dir else (_default_updates())
    final = engine.one_click(updates)
    return {
        "state": final.value,
        "citizen_home": str(home),
        "updates_dir": str(updates),
    }


def status(*, home: Path) -> dict:
    home = Path(home).resolve()
    paths = layout(home)
    from .manifest import load_manifest, verify_manifest
    from .crypto import load_publisher_secret

    secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
    m = load_manifest(paths["manifest"] / "current.json")
    return {
        "state": UpdateState.CURRENT.value,
        "manifest_ok": verify_manifest(m, secret),
        "citizen_version": m.citizen_version,
        "runtime_version": m.runtime_version,
        "asset_version": m.asset_version,
        "release": m.release,
        "citizen_id": m.citizen_id,
    }


def _default_updates() -> Path:
    from .paths import seed_root

    return seed_root() / "assets" / "updates"
