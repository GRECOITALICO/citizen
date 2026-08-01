"""Legacy diary bridge — prefer journal.py (Citizen Life Journal)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _path(diary_dir: Path) -> Path:
    return Path(diary_dir) / "life.jsonl"


def write(
    diary_dir: Path,
    *,
    chapter: str,
    message: str,
    citizen_id: str = "",
    **fields: Any,
) -> dict[str, Any]:
    """Append legacy line (kept for longitudinal continuity). Never edit/delete."""
    diary_dir = Path(diary_dir)
    diary_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "chapter": chapter,
        "message": message,
        "citizen_id": citizen_id,
        **{k: v for k, v in fields.items() if k != "evidence_refs"},
    }
    with _path(diary_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
    return entry


def read_all(diary_dir: Path) -> list[dict[str, Any]]:
    path = _path(diary_dir)
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
