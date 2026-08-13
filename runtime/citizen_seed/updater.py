"""Updater — one-button façade over the signed Update Engine."""
from __future__ import annotations

from pathlib import Path

from .crypto import load_publisher_secret
from .paths import layout
from .sync_bridge import SyncBridgeError, check_and_stage_from_node
from .update_engine import UpdateEngine, UpdateState


def one_click_update(*, home: Path, updates_dir: Path | None = None) -> dict:
    """CHECK → fetch from CONRRAD Node → verify → atomically apply.

    The network bridge is best-effort only when CONRRAD_NODE_URL is absent.
    Once an update is staged, UpdateEngine remains the sole activation path.
    """
    home = Path(home).resolve()
    paths = layout(home)
    secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
    engine = UpdateEngine(home, secret)
    updates = Path(updates_dir) if updates_dir else _default_updates(home)

    remote: dict = {"checked": False, "update_available": False}
    if updates_dir is None:
        try:
            remote = check_and_stage_from_node(home)
        except SyncBridgeError as exc:
            remote = {"checked": True, "update_available": False, "remote_error": str(exc)}

    final = engine.one_click(updates)
    return {
        "state": final.value,
        "citizen_home": str(home),
        "updates_dir": str(updates),
        "remote_sync": remote,
    }


def status(*, home: Path) -> dict:
    home = Path(home).resolve()
    paths = layout(home)
    from .manifest import load_manifest, verify_manifest

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
        "node_url_configured": bool(__import__("os").environ.get("CONRRAD_NODE_URL")),
    }


def _default_updates(home: Path) -> Path:
    return layout(home)["updates"]
