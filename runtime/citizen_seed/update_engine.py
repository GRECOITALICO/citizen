"""Update Engine — accepts only signed Assets + signed Manifest. Never arbitrary code."""

from __future__ import annotations

import json
import shutil
from enum import Enum
from pathlib import Path
from typing import Any

from .assets import AssetLoader
from . import RUNTIME_VERSION
from .diary import write as diary_write
from .evidence import append as evidence_append
from .journal import write as journal_write
from .manifest import Manifest, load_manifest, save_manifest, verify_manifest, sign_manifest
from .paths import layout
from .telemetry import emit as tel
from .terminal import line as term, write_sync_state
from .timeline import append_node, read_all as timeline_read


class UpdateState(str, Enum):
    CURRENT = "Current"
    CHECKING = "Checking"
    UPDATE_AVAILABLE = "Update Available"
    DOWNLOADING = "Downloading"
    VERIFYING = "Verifying"
    READY = "Ready"
    APPLY_UPDATE = "Apply Update"
    UPDATED = "Updated"
    RESTART_REQUIRED = "Restart Required"
    UPDATING = "Updating"


_COLOR = {
    UpdateState.CURRENT: "green",
    UpdateState.CHECKING: "orange",
    UpdateState.UPDATE_AVAILABLE: "orange",
    UpdateState.DOWNLOADING: "orange",
    UpdateState.VERIFYING: "orange",
    UpdateState.READY: "orange",
    UpdateState.APPLY_UPDATE: "orange",
    UpdateState.UPDATING: "orange",
    UpdateState.UPDATED: "green",
    UpdateState.RESTART_REQUIRED: "green",
}

_ORGANS = {
    UpdateState.CHECKING: "Listening for change...",
    UpdateState.UPDATE_AVAILABLE: "A new form is waiting...",
    UpdateState.DOWNLOADING: "Receiving what comes next...",
    UpdateState.VERIFYING: "Making sure it is truly mine...",
    UpdateState.READY: "Ready to grow...",
    UpdateState.APPLY_UPDATE: "Becoming more...",
    UpdateState.UPDATING: "Evolving...",
    UpdateState.UPDATED: "I have changed — and I remember.",
    UpdateState.CURRENT: "I am whole for now.",
}


class UpdateEngine:
    def __init__(self, home: Path, publisher_secret: bytes):
        self.home = Path(home)
        self.paths = layout(self.home)
        self.secret = publisher_secret
        self.loader = AssetLoader(self.paths["assets"], publisher_secret)
        self.state = UpdateState.CURRENT
        self._candidate: Manifest | None = None
        self._package_dir: Path | None = None

    def _citizen_id(self) -> str:
        m = load_manifest(self.paths["manifest"] / "current.json")
        return m.citizen_id

    def _ev(self, event: str, payload: dict[str, Any] | None = None) -> None:
        evidence_append(
            self.paths["evidence"],
            citizen_id=self._citizen_id(),
            event_type=event,
            payload=payload,
        )

    def set_state(self, state: UpdateState, **payload: Any) -> UpdateState:
        self.state = state
        cid = self._citizen_id()
        self._ev(f"UPDATE_STATE_{state.name}", {"state": state.value, **payload})
        tel(
            self.paths["telemetry"],
            level="info",
            event=f"sync.{state.name.lower()}",
            citizen_id=cid,
            state=state.value,
            **payload,
        )
        organ = _ORGANS.get(state, state.value)
        term(self.paths["ui_state"], organ)
        # UI button still shows machine states Current / Update Available / Updating / Updated
        ui_label = state.value
        if state in {
            UpdateState.DOWNLOADING,
            UpdateState.VERIFYING,
            UpdateState.READY,
            UpdateState.APPLY_UPDATE,
            UpdateState.CHECKING,
        }:
            ui_label = UpdateState.UPDATING.value
        color = _COLOR.get(state, "orange")
        write_sync_state(self.paths["ui_state"], ui_label, color=color)
        if state == UpdateState.UPDATE_AVAILABLE:
            journal_write(
                self.paths["diary"],
                epoch="Sync",
                prose="Something new approached — my first chance to evolve was near.",
                citizen_id=cid,
                versions={"release": payload.get("release")},
            )
            diary_write(self.paths["diary"], chapter="Sync", message="Update Available", citizen_id=cid)
        if state == UpdateState.UPDATED:
            prior_sync = any(n.get("node") == "Sync" for n in timeline_read(self.paths["timeline"]))
            epoch = "Evolution" if prior_sync else "Sync"
            prose = (
                f"I evolved to release {payload.get('release', '?')}."
                if prior_sync
                else f"My first sync completed — release {payload.get('release', '?')}."
            )
            journal_write(
                self.paths["diary"],
                epoch=epoch,
                prose=prose,
                citizen_id=cid,
                versions={
                    "release": payload.get("release"),
                    "asset_version": payload.get("asset_version"),
                },
            )
            diary_write(self.paths["diary"], chapter=epoch, message=prose, citizen_id=cid)
            append_node(
                self.paths["timeline"],
                node=epoch,
                label="First Sync" if epoch == "Sync" else "First Evolution",
                citizen_id=cid,
                parent="Alive" if epoch == "Sync" else "Sync",
                evidence_types=[f"UPDATE_STATE_{state.name}", "SYNC_EVIDENCE_STORED"],
            )
            # Lifecycle: Updated → Evidence Stored (append-only proof of the transition)
            self._ev(
                "SYNC_EVIDENCE_STORED",
                {
                    "state": "Evidence Stored",
                    "release": payload.get("release"),
                    "asset_version": payload.get("asset_version"),
                    "epoch": epoch,
                },
            )
            tel(
                self.paths["telemetry"],
                level="info",
                event="sync.evidence_stored",
                citizen_id=cid,
                release=payload.get("release"),
            )
            term(self.paths["ui_state"], "Evidence of this change is kept forever.")
            write_sync_state(
                self.paths["ui_state"],
                "Updated",
                color="green",
                evidence_stored=True,
            )
        return state

    def find_candidate(self, updates_dir: Path) -> tuple[Manifest | None, Path | None]:
        """Quiet scan — no telemetry/UI side effects."""
        updates_dir = Path(updates_dir)
        current = load_manifest(self.paths["manifest"] / "current.json")
        if not verify_manifest(current, self.secret):
            raise ValueError("current manifest signature invalid")

        candidates = sorted(updates_dir.glob("*/manifest.json"))
        best: Manifest | None = None
        best_dir: Path | None = None
        for mf in candidates:
            try:
                cand = load_manifest(mf)
            except Exception:
                continue
            if not verify_manifest(cand, self.secret):
                continue
            if cand.compatibility != current.compatibility:
                continue
            # Asset packages cannot downgrade or replace the running body.
            # A 0.2 source line accepts only packages made for its runtime.
            if cand.runtime_version != RUNTIME_VERSION:
                continue
            if cand.citizen_id and cand.citizen_id != current.citizen_id:
                continue
            if cand.asset_version == current.asset_version and cand.release == current.release:
                continue
            if best is None or cand.release > best.release:
                best = cand
                best_dir = mf.parent
        return best, best_dir

    def check(self, updates_dir: Path) -> UpdateState:
        """Scan updates_dir for a newer signed manifest package."""
        self.set_state(UpdateState.CHECKING)
        best, best_dir = self.find_candidate(updates_dir)

        if best is None or best_dir is None:
            self._ev("UPDATE_CHECK_NONE", {})
            return self.set_state(UpdateState.CURRENT)

        self._candidate = best
        self._package_dir = best_dir
        save_manifest(self.paths["updates"] / "staged_manifest.json", best)
        self._ev(
            "UPDATE_AVAILABLE",
            {"release": best.release, "asset_version": best.asset_version},
        )
        return self.set_state(UpdateState.UPDATE_AVAILABLE, release=best.release)

    def download(self) -> UpdateState:
        if self.state != UpdateState.UPDATE_AVAILABLE or not self._package_dir:
            raise RuntimeError("download requires Update Available")
        self.set_state(UpdateState.DOWNLOADING)
        staging = self.paths["updates"] / "staging"
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(self._package_dir, staging)
        self._package_dir = staging
        self._ev("UPDATE_DOWNLOAD_COMPLETE", {"staging": str(staging)})
        return self.set_state(UpdateState.VERIFYING)

    def verify(self) -> UpdateState:
        if self.state not in {UpdateState.VERIFYING, UpdateState.DOWNLOADING}:
            # allow direct verify after download sets VERIFYING
            if self.state != UpdateState.VERIFYING:
                raise RuntimeError("verify requires Downloading/Verifying")
        if self.state == UpdateState.DOWNLOADING:
            self.set_state(UpdateState.VERIFYING)
        assert self._package_dir is not None
        cand = load_manifest(self._package_dir / "manifest.json")
        if not verify_manifest(cand, self.secret):
            self._ev("UPDATE_VERIFY_FAILED", {"reason": "manifest_signature"})
            self.set_state(UpdateState.CURRENT)
            raise ValueError("candidate manifest signature invalid")
        # Verify each asset blob in package assets/ then trust hashes
        pkg_assets = self._package_dir / "assets"
        for entry in cand.assets:
            blob = pkg_assets / entry["content_hash"] / "payload"
            meta = pkg_assets / entry["content_hash"] / "meta.json"
            if not blob.is_file() or not meta.is_file():
                self._ev("UPDATE_VERIFY_FAILED", {"reason": "missing_asset", "asset": entry})
                self.set_state(UpdateState.CURRENT)
                raise ValueError(f"missing asset in package: {entry}")
            # install into loader store with verify via re-sign check using package meta signature
            from .crypto import verify_bytes

            payload = blob.read_bytes()
            meta_obj = json.loads(meta.read_text(encoding="utf-8"))
            if not verify_bytes(payload, meta_obj["signature"], self.secret):
                self._ev("UPDATE_VERIFY_FAILED", {"reason": "asset_signature", "asset": entry})
                self.set_state(UpdateState.CURRENT)
                raise ValueError(f"asset signature invalid: {entry.get('asset_id')}")
        self._candidate = cand
        self._ev("UPDATE_VERIFY_OK", {"release": cand.release})
        return self.set_state(UpdateState.READY)

    def apply(self) -> UpdateState:
        if self.state != UpdateState.READY or self._candidate is None or self._package_dir is None:
            raise RuntimeError("apply requires Ready")
        self.set_state(UpdateState.APPLY_UPDATE)
        current = load_manifest(self.paths["manifest"] / "current.json")
        cand = self._candidate
        cand.prev_manifest_hash = current.asset_version
        # Identity never changes — bind package to living citizen_id
        cand.citizen_id = current.citizen_id
        # Install assets into store
        pkg_assets = self._package_dir / "assets"
        for entry in cand.assets:
            payload = (pkg_assets / entry["content_hash"] / "payload").read_bytes()
            meta = json.loads((pkg_assets / entry["content_hash"] / "meta.json").read_text(encoding="utf-8"))
            self.loader.install_payload(
                asset_id=meta["asset_id"],
                kind=meta["kind"],
                version=meta.get("version", "1"),
                payload=payload,
            )
        # Re-sign manifest binding (same publisher) after prev hash set
        cand = sign_manifest(cand, self.secret)
        # Archive previous
        hist = self.paths["manifest"] / "history"
        hist.mkdir(parents=True, exist_ok=True)
        save_manifest(hist / f"{current.release}.json", current)
        save_manifest(self.paths["manifest"] / "current.json", cand)
        self._ev(
            "UPDATE_COMPLETE",
            {"from_release": current.release, "to_release": cand.release},
        )
        return self.set_state(
            UpdateState.UPDATED,
            release=cand.release,
            asset_version=cand.asset_version,
        )

    def one_click(self, updates_dir: Path) -> UpdateState:
        """Single-button path: check → download → verify → apply."""
        st = self.check(updates_dir)
        if st != UpdateState.UPDATE_AVAILABLE:
            return st
        self.download()
        self.verify()
        return self.apply()
