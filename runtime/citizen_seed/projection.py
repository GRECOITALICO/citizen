"""Projection Engine (minimal) — Website / Citizen UI / Docs / Status / Manifest from Assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .assets import AssetLoader
from .manifest import Manifest


class ProjectionEngine:
    """Emit projection artifacts solely from Manifest-listed Assets + Manifest itself."""

    def __init__(self, loader: AssetLoader, out_dir: Path):
        self.loader = loader
        self.out_dir = Path(out_dir)

    def project(self, manifest: Manifest) -> dict[str, Any]:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        report: dict[str, Any] = {"slots": {}, "manifest": manifest.to_dict()}

        # Always project Manifest + Status skeleton
        status = {
            "citizen_id": manifest.citizen_id,
            "citizen_version": manifest.citizen_version,
            "runtime_version": manifest.runtime_version,
            "asset_version": manifest.asset_version,
            "knowledge_version": manifest.knowledge_version,
            "compatibility": manifest.compatibility,
            "release": manifest.release,
            "surface": "citizen-seed",
            "invented_metrics": False,
        }
        self._write_json("status.json", status)
        report["slots"]["status"] = "status.json"

        self._write_json("manifest.json", manifest.to_dict())
        report["slots"]["manifest"] = "manifest.json"

        # Projection Assets (kind=projection|website|documentation|citizen_ui|status)
        for a in manifest.assets:
            ref = self.loader.verify_asset(a["content_hash"])
            if ref.kind not in {"projection", "website", "documentation", "citizen_ui", "status"}:
                continue
            payload = self.loader.load_payload(a["content_hash"])
            name = f"{ref.kind}__{ref.asset_id}"
            # JSON payloads preferred
            try:
                data = json.loads(payload.decode("utf-8"))
                fname = f"{name}.json"
                self._write_json(fname, data)
            except (UnicodeDecodeError, json.JSONDecodeError):
                fname = f"{name}.bin"
                (self.out_dir / fname).write_bytes(payload)
            report["slots"][ref.asset_id] = fname

        index = {
            "website": report["slots"].get("website") or report["slots"].get("status"),
            "citizen_ui": [v for k, v in report["slots"].items() if "citizen_ui" in k or k.startswith("citizen_ui")],
            "documentation": [v for k, v in report["slots"].items() if "documentation" in k],
            "status": "status.json",
            "manifest": "manifest.json",
        }
        # Collect by kind more cleanly
        index["citizen_ui"] = [
            report["slots"][a["asset_id"]]
            for a in manifest.assets
            if a.get("kind") == "citizen_ui" and a["asset_id"] in report["slots"]
        ]
        index["documentation"] = [
            report["slots"][a["asset_id"]]
            for a in manifest.assets
            if a.get("kind") == "documentation" and a["asset_id"] in report["slots"]
        ]
        index["website"] = [
            report["slots"][a["asset_id"]]
            for a in manifest.assets
            if a.get("kind") in {"website", "projection"} and a["asset_id"] in report["slots"]
        ]
        self._write_json("index.json", index)
        report["slots"]["index"] = "index.json"
        return report

    def _write_json(self, name: str, data: Any) -> None:
        (self.out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
