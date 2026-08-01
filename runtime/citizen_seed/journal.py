"""Citizen Life Journal — biography, not a log. Append-only forever."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def journal_path(journal_dir: Path) -> Path:
    return Path(journal_dir) / "life_journal.jsonl"


def write(
    journal_dir: Path,
    *,
    epoch: str,
    prose: str,
    citizen_id: str = "",
    duration_ms: float | None = None,
    evidence_refs: list[str] | None = None,
    versions: dict[str, Any] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Append one biographical paragraph.

    epoch examples: PreBirth, Bootstrap, Identity, Manifest, Alive, Sync, Evolution
    prose: human narrative sentence(s) reconstructing life.
    """
    journal_dir = Path(journal_dir)
    journal_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts_epoch": time.time(),
        "epoch": epoch,
        "prose": prose,
        "citizen_id": citizen_id,
        "duration_ms": duration_ms,
        "evidence_refs": evidence_refs or [],
        "versions": versions or {},
        **fields,
    }
    with journal_path(journal_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
    return entry


def read_all(journal_dir: Path) -> list[dict[str, Any]]:
    path = journal_path(journal_dir)
    if not path.is_file():
        # Legacy diary fallback
        legacy = Path(journal_dir) / "life.jsonl"
        if not legacy.is_file():
            return []
        return [json.loads(l) for l in legacy.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def as_biography(journal_dir: Path) -> str:
    """Render full biography text for export / UI."""
    lines: list[str] = []
    for e in read_all(journal_dir):
        ts = e.get("ts", "")
        epoch = e.get("epoch") or e.get("chapter", "")
        prose = e.get("prose") or e.get("message", "")
        dur = e.get("duration_ms")
        extra = f" ({dur:.1f} ms)" if isinstance(dur, (int, float)) and dur is not None else ""
        lines.append(f"[{ts}] {epoch}{extra}\n{prose}\n")
    return "\n".join(lines)
