"""Evidence plane — append-only JSONL. Never modify or delete records."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .crypto import sha256_bytes, canonical_json


def evidence_log(evidence_dir: Path) -> Path:
    return evidence_dir / "evidence.jsonl"


def append(
    evidence_dir: Path,
    *,
    citizen_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    log = evidence_log(evidence_dir)
    envelope = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "citizen_id": citizen_id,
        "event_type": event_type,
        "payload": payload or {},
    }
    envelope["content_hash"] = "sha256:" + sha256_bytes(canonical_json(envelope))
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(envelope, sort_keys=True) + "\n")
    return envelope


def read_all(evidence_dir: Path) -> list[dict[str, Any]]:
    log = evidence_log(evidence_dir)
    if not log.is_file():
        return []
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out
