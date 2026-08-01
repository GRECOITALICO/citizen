"""Citizen home layout (planes)."""

from __future__ import annotations

import os
from pathlib import Path


def seed_root() -> Path:
    """Repo root: citizen-seed/ (parent of runtime/)."""
    return Path(__file__).resolve().parents[2]


def citizen_home(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root).resolve()
    env = os.environ.get("CITIZEN_HOME")
    if env:
        return Path(env).resolve()
    return (seed_root() / ".citizen").resolve()


def layout(home: Path) -> dict[str, Path]:
    h = Path(home)
    return {
        "home": h,
        "identity": h / "identity",
        "evidence": h / "evidence",
        "assets": h / "assets",
        "manifest": h / "manifest",
        "updates": h / "updates",
        "runtime": h / "runtime",
        "projection": h / "projection",
        "boot": h / "boot",
        "telemetry": h / "telemetry",
        "diary": h / "journal",  # Citizen Life Journal plane
        "timeline": h / "timeline",
        "ui_state": h / "ui",
    }


def ensure_layout(home: Path) -> dict[str, Path]:
    paths = layout(home)
    for key, p in paths.items():
        p.mkdir(parents=True, exist_ok=True)
    return paths
