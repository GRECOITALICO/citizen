"""Golden Client semantics — CITIZEN-P0-GOLDEN-CLIENT-SEMANTICS-REMEDIATION-001."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops"))
sys.path.insert(0, str(ROOT / "runtime"))

import living_server as ls  # noqa: E402
from citizen_seed import RUNTIME_VERSION  # noqa: E402
from citizen_seed.update_engine import UpdateState  # noqa: E402


@pytest.fixture
def citizen_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    home = tmp_path / "home"
    seed = tmp_path / "seed"
    for sub in ("manifest", "ops", "identity", "boot"):
        (home / sub).mkdir(parents=True)
    (seed / "assets" / "updates").mkdir(parents=True)
    (home / "boot" / "BOOTSTRAP_DISARMED").write_text("1\n", encoding="utf-8")
    (home / "identity" / "identity.json").write_text(
        json.dumps({"citizen_id": "cit_test_golden", "created_utc": "2026-08-16T00:00:00Z"}),
        encoding="utf-8",
    )
    (home / "ops" / "CURRENT_VERSION.txt").write_text("0.2.0\n", encoding="utf-8")
    monkeypatch.setattr(ls, "HOME", home)
    monkeypatch.setattr(ls, "SEED_ROOT", seed)
    return home, seed


def _write_current_manifest(home: Path, **extra: object) -> None:
    base = {
        "compatibility": "seed-2026.1",
        "citizen_id": "cit_test_golden",
        "runtime_version": RUNTIME_VERSION,
        "citizen_version": "0.2.0",
        "asset_version": "sha256:current",
        "release": "2026-08-01T00:00:00Z",
    }
    base.update(extra)
    (home / "manifest" / "current.json").write_text(json.dumps(base), encoding="utf-8")


def _write_update_package(seed: Path, name: str, **manifest_extra: object) -> None:
    pkg = seed / "assets" / "updates" / name
    pkg.mkdir(parents=True)
    manifest = {
        "compatibility": "seed-2026.1",
        "citizen_id": "",
        "runtime_version": "0.1.0",
        "citizen_version": "1.0.1-seed",
        "asset_version": "sha256:update",
        "release": "2026-08-02T00:00:00Z",
        "assets": [],
    }
    manifest.update(manifest_extra)
    (pkg / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_incompatible_runtime_version_rejected(citizen_env) -> None:
    home, seed = citizen_env
    _write_current_manifest(home)
    _write_update_package(seed, "seed-update-1")
    assert ls.scan_local_update_candidate() is None
    avail = ls.update_availability()
    assert avail["update_available"] is False


def test_compatible_runtime_version_accepted(citizen_env) -> None:
    home, seed = citizen_env
    _write_current_manifest(home)
    _write_update_package(
        seed,
        "seed-update-compatible",
        runtime_version=RUNTIME_VERSION,
        citizen_version="0.2.1-seed",
        release="2026-08-03T00:00:00Z",
    )
    cand = ls.scan_local_update_candidate()
    assert cand is not None
    assert cand["version"] == "0.2.1-seed"
    assert ls.update_availability()["update_available"] is True


def test_current_version_not_changed_when_update_rejected(citizen_env, monkeypatch) -> None:
    home, seed = citizen_env
    _write_current_manifest(home)
    _write_update_package(seed, "seed-update-1")
    monkeypatch.setattr(ls, "send_awake", lambda _hb: (True, "HTTP 200"))
    monkeypatch.setattr(ls, "http_post_json", lambda *_a, **_k: (False, "offline"))
    monkeypatch.setattr(
        ls,
        "run_cli",
        lambda *_a, **_k: (
            0,
            json.dumps({"state": UpdateState.CURRENT.value, "citizen_home": str(home)}),
        ),
    )
    ls.sync_cycle()
    assert (home / "ops" / "CURRENT_VERSION.txt").read_text(encoding="utf-8").strip() == "0.2.0"


def test_current_version_changed_only_after_updated(citizen_env, monkeypatch) -> None:
    home, _seed = citizen_env
    _write_current_manifest(home, citizen_version="0.2.1-seed")
    monkeypatch.setattr(ls, "send_awake", lambda _hb: (True, "HTTP 200"))
    monkeypatch.setattr(ls, "http_post_json", lambda *_a, **_k: (False, "offline"))
    monkeypatch.setattr(
        ls,
        "run_cli",
        lambda *_a, **_k: (
            0,
            json.dumps({"state": UpdateState.UPDATED.value, "citizen_home": str(home)}),
        ),
    )
    ls.sync_cycle()
    assert (home / "ops" / "CURRENT_VERSION.txt").read_text(encoding="utf-8").strip() == "0.2.1-seed"


def test_duplicate_evolution_suppressed(citizen_env, monkeypatch) -> None:
    home, _seed = citizen_env
    _write_current_manifest(home, citizen_version="0.2.1-seed")
    monkeypatch.setattr(ls, "send_awake", lambda _hb: (True, "HTTP 200"))
    monkeypatch.setattr(ls, "http_post_json", lambda *_a, **_k: (False, "offline"))
    monkeypatch.setattr(
        ls,
        "run_cli",
        lambda *_a, **_k: (
            0,
            json.dumps({"state": UpdateState.UPDATED.value, "citizen_home": str(home)}),
        ),
    )
    ls.sync_cycle()
    ls.sync_cycle()
    ls.sync_cycle()
    sync_rows = [
        row
        for row in ls.read_evolution_history()
        if row.get("kind") == "sync_evolution" and row.get("version") == "0.2.1-seed"
    ]
    assert len(sync_rows) == 1


def test_new_evolution_recorded_once(citizen_env, monkeypatch) -> None:
    home, _seed = citizen_env
    _write_current_manifest(home, citizen_version="0.2.2-seed")
    monkeypatch.setattr(ls, "send_awake", lambda _hb: (True, "HTTP 200"))
    monkeypatch.setattr(ls, "http_post_json", lambda *_a, **_k: (False, "offline"))
    monkeypatch.setattr(
        ls,
        "run_cli",
        lambda *_a, **_k: (
            0,
            json.dumps({"state": UpdateState.UPDATED.value, "citizen_home": str(home)}),
        ),
    )
    result = ls.sync_cycle()
    assert result["evolution"] is not None
    assert result["evolution"]["kind"] == "sync_evolution"


def test_parse_update_cli_output_handles_json_blob() -> None:
    payload = {"state": "UPDATED", "citizen_home": "/tmp/x"}
    assert ls.parse_update_cli_output(json.dumps(payload)) == payload
