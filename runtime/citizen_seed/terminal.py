"""Birth terminal — narrative lines for the UI console (not developer debug)."""

from __future__ import annotations

import json
import time
from pathlib import Path


def terminal_path(ui_dir: Path) -> Path:
    return Path(ui_dir) / "terminal.jsonl"


def line(ui_dir: Path, text: str) -> None:
    ui_dir = Path(ui_dir)
    ui_dir.mkdir(parents=True, exist_ok=True)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "text": text}
    with terminal_path(ui_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


def read_lines(ui_dir: Path, n: int = 500) -> list[str]:
    path = terminal_path(ui_dir)
    if not path.is_file():
        return []
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines()[-n:]:
        if not raw.strip():
            continue
        out.append(json.loads(raw).get("text", raw))
    return out


def write_sync_state(ui_dir: Path, state: str, **extra) -> None:
    ui_dir = Path(ui_dir)
    ui_dir.mkdir(parents=True, exist_ok=True)
    payload = {"state": state, "updated_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **extra}
    (ui_dir / "sync_state.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
