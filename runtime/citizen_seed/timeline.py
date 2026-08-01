"""Timeline — irreversible life nodes with evidence links. Append-only."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def timeline_path(timeline_dir: Path) -> Path:
    return Path(timeline_dir) / "timeline.jsonl"


def append_node(
    timeline_dir: Path,
    *,
    node: str,
    label: str,
    citizen_id: str = "",
    evidence_types: list[str] | None = None,
    evidence_hashes: list[str] | None = None,
    parent: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    timeline_dir = Path(timeline_dir)
    timeline_dir.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts_epoch": time.time(),
        "node": node,
        "label": label,
        "citizen_id": citizen_id,
        "parent": parent,
        "evidence_types": evidence_types or [],
        "evidence_hashes": evidence_hashes or [],
        **fields,
    }
    with timeline_path(timeline_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    return rec


def read_all(timeline_dir: Path) -> list[dict[str, Any]]:
    path = timeline_path(timeline_dir)
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
