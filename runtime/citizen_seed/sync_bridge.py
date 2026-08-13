"""External Node sync bridge.

The Citizen is localhost-first and self-surviving. SYNC may fetch a complete
release package from the CONRRAD Node, but it never trusts the network response
as governance authority: the package hash and signed manifest are verified
before UpdateEngine is allowed to activate anything.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .manifest import load_manifest, verify_manifest
from .paths import layout


class SyncBridgeError(RuntimeError):
    pass


def _get(url: str, token: str | None = None, timeout: int = 30) -> bytes:
    headers = {"User-Agent": "CONRRAD-Citizen-Sync/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        raise SyncBridgeError(f"NODE_HTTP_{exc.code}") from exc
    except Exception as exc:
        raise SyncBridgeError(f"NODE_UNREACHABLE:{exc}") from exc


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                target = (destination / member.filename).resolve()
                if target != root and root not in target.parents:
                    raise SyncBridgeError("ARCHIVE_PATH_TRAVERSAL")
            zf.extractall(destination)
        return
    if archive.name.endswith((".tar.gz", ".tgz", ".tar")):
        with tarfile.open(archive) as tf:
            for member in tf.getmembers():
                target = (destination / member.name).resolve()
                if target != root and root not in target.parents:
                    raise SyncBridgeError("ARCHIVE_PATH_TRAVERSAL")
                if member.issym() or member.islnk():
                    raise SyncBridgeError("ARCHIVE_LINK_FORBIDDEN")
            tf.extractall(destination)
        return
    raise SyncBridgeError("UNSUPPORTED_RELEASE_ARCHIVE")


def _locate_package_root(stage: Path) -> Path:
    if (stage / "manifest.json").is_file() and (stage / "assets").is_dir():
        return stage
    children = [p for p in stage.iterdir() if p.is_dir()]
    for child in children:
        if (child / "manifest.json").is_file() and (child / "assets").is_dir():
            return child
    raise SyncBridgeError("RELEASE_PACKAGE_LAYOUT_INVALID")


def check_and_stage_from_node(home: Path, *, node_url: str | None = None) -> dict:
    """Ask the Azure Node for the release and stage it under Citizen HOME.

    Expected Node sync response fields:
      update_available, available_version, compatible, artifact_url,
      artifact_sha256, manifest_url, release_id.
    """
    home = Path(home).resolve()
    paths = layout(home)
    current_manifest = paths["manifest"] / "current.json"
    if not current_manifest.is_file():
        raise SyncBridgeError("CURRENT_MANIFEST_MISSING")
    current = load_manifest(current_manifest)

    base = (node_url or os.environ.get("CONRRAD_NODE_URL", "")).rstrip("/")
    if not base:
        return {"checked": False, "update_available": False, "reason": "NODE_URL_NOT_CONFIGURED"}
    citizen_id = current.citizen_id
    endpoint = f"{base}/citizens/{citizen_id}/sync?current_version={current.citizen_version}"
    token = os.environ.get("CONRRAD_CITIZEN_TOKEN")
    payload = json.loads(_get(endpoint, token=token).decode("utf-8"))

    if not payload.get("compatible", False):
        raise SyncBridgeError("NODE_RELEASE_INCOMPATIBLE")
    if not payload.get("update_available", False):
        return {"checked": True, "update_available": False, "mode": payload.get("mode", "CHECK")}

    artifact_url = payload.get("artifact_url")
    expected_hash = str(payload.get("artifact_sha256") or "").lower()
    if not artifact_url or len(expected_hash) != 64:
        raise SyncBridgeError("NODE_SYNC_METADATA_INCOMPLETE")

    updates = paths["updates"]
    updates.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="citizen-sync-", dir=updates) as td:
        td_path = Path(td)
        archive = td_path / "release.bin"
        archive.write_bytes(_get(str(artifact_url), token=token, timeout=120))
        actual = _sha256(archive)
        if actual != expected_hash:
            raise SyncBridgeError("ARTIFACT_SHA256_MISMATCH")
        extract = td_path / "extract"
        _safe_extract(archive, extract)
        package = _locate_package_root(extract)

        manifest_url = payload.get("manifest_url")
        if manifest_url:
            remote_manifest = json.loads(_get(str(manifest_url), token=token).decode("utf-8"))
            if remote_manifest.get("release") != payload.get("release_id"):
                raise SyncBridgeError("MANIFEST_RELEASE_MISMATCH")

        staged = updates / str(payload.get("available_version") or payload.get("release_id") or "incoming")
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(package, staged)
        marker = {
            "available": True,
            "version": payload.get("available_version"),
            "release": payload.get("release_id"),
            "artifact_sha256": expected_hash,
            "source": "conrrad_node",
            "staged_dir": str(staged),
        }
        (updates / "REMOTE_UPDATE.json").write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")
        return marker
