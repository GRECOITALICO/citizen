"""Export Birth Package + Destroy Citizen — lab reproducibility."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from .crypto import sha256_file
from .evidence import read_all as evidence_read
from .identity import load as load_identity
from .journal import as_biography, read_all as journal_read
from .manifest import load_manifest
from .paths import layout, seed_root
from .telemetry import read_all as telemetry_read
from .timeline import read_all as timeline_read
from .terminal import read_lines


OUTSIDE_LLM_FACTS = {
    "question": "How much of the Citizen lives completely outside the LLM?",
    "method": "Inventory of living planes + dependency scan of runtime package",
    "claim": "Birth, Identity, Manifest, Evidence, Telemetry, Journal, Timeline, Projection, Sync operate without any LLM call or model weight.",
}


def _scan_runtime_for_llm_imports(runtime_pkg: Path) -> dict[str, Any]:
    """Detect real import usage — not mention of token names in string lists."""
    import re

    banned = (
        "openai",
        "anthropic",
        "langchain",
        "llama_cpp",
        "transformers",
        "torch",
        "tensorflow",
        "ollama",
        "litellm",
        "vertexai",
        "groq",
    )
    hits: list[dict[str, str]] = []
    py_files = 0
    import_re = re.compile(
        r"(?:^|\n)\s*(?:import|from)\s+(" + "|".join(re.escape(b) for b in banned) + r")\b"
    )
    for p in runtime_pkg.rglob("*.py"):
        py_files += 1
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in import_re.finditer(text):
            hits.append({"file": str(p.relative_to(runtime_pkg)), "token": m.group(1)})
    return {
        "python_files_scanned": py_files,
        "banned_token_hits": hits,
        "llm_free": len(hits) == 0,
    }


def outside_llm_report(home: Path) -> dict[str, Any]:
    home = Path(home).resolve()
    paths = layout(home)
    planes = {
        "identity": (paths["identity"] / "identity.json").is_file(),
        "manifest": (paths["manifest"] / "current.json").is_file(),
        "evidence": (paths["evidence"] / "evidence.jsonl").is_file(),
        "telemetry": (paths["telemetry"] / "telemetry.jsonl").is_file(),
        "journal": (paths["diary"] / "life_journal.jsonl").is_file()
        or (paths["diary"] / "life.jsonl").is_file(),
        "timeline": (paths["timeline"] / "timeline.jsonl").is_file(),
        "projection": paths["projection"].is_dir() and any(paths["projection"].iterdir()),
        "assets": paths["assets"].is_dir() and any(paths["assets"].iterdir()),
    }
    scan = _scan_runtime_for_llm_imports(seed_root() / "runtime" / "citizen_seed")
    living_outside = sum(1 for v in planes.values() if v)
    return {
        **OUTSIDE_LLM_FACTS,
        "planes_present": planes,
        "planes_alive_count": living_outside,
        "planes_total": len(planes),
        "runtime_scan": scan,
        "verdict": (
            "ALL_MEASURED_LIFE_OUTSIDE_LLM"
            if scan["llm_free"] and living_outside == len(planes)
            else "PARTIAL_OR_SCAN_HIT"
        ),
        "measured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def export_birth_package(
    *,
    home: Path,
    dest_dir: Path | None = None,
) -> dict[str, Any]:
    """Write a complete Birth Package (no external tools beyond stdlib)."""
    home = Path(home).resolve()
    paths = layout(home)
    lab = seed_root() / "lab" / "exports"
    dest_root = Path(dest_dir) if dest_dir else lab
    dest_root.mkdir(parents=True, exist_ok=True)

    ident = load_identity(paths["identity"])
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    pkg_name = f"birth_{ident.citizen_id}_{stamp}"
    pkg = dest_root / pkg_name
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)

    # Copy planes (append-only artifacts as-is)
    for name, src in [
        ("identity", paths["identity"]),
        ("evidence", paths["evidence"]),
        ("manifest", paths["manifest"]),
        ("telemetry", paths["telemetry"]),
        ("journal", paths["diary"]),
        ("timeline", paths["timeline"]),
        ("ui", paths["ui_state"]),
        ("boot", paths["boot"]),
        ("projection", paths["projection"]),
    ]:
        if src.exists():
            shutil.copytree(src, pkg / name, dirs_exist_ok=True)

    # Asset store hashes only (payloads may be large — copy meta + hash list)
    assets_index = []
    if paths["assets"].is_dir():
        for child in sorted(paths["assets"].iterdir()):
            if child.is_dir():
                meta = child / "meta.json"
                assets_index.append(
                    {
                        "content_hash": child.name,
                        "meta": json.loads(meta.read_text(encoding="utf-8")) if meta.is_file() else {},
                    }
                )
    (pkg / "assets_index.json").write_text(
        json.dumps(assets_index, indent=2) + "\n", encoding="utf-8"
    )

    m = load_manifest(paths["manifest"] / "current.json")
    llm = outside_llm_report(home)
    summary = {
        "package": "CITIZEN_BIRTH_PACKAGE",
        "serial": "INT-CITIZEN-BIRTH-LAB-001",
        "citizen_id": ident.citizen_id,
        "created_utc": ident.created_utc,
        "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_version": m.runtime_version,
        "citizen_version": m.citizen_version,
        "manifest_release": m.release,
        "evidence_count": len(evidence_read(paths["evidence"])),
        "journal_count": len(journal_read(paths["diary"])),
        "timeline_count": len(timeline_read(paths["timeline"])),
        "telemetry_count": len(telemetry_read(paths["telemetry"])),
        "terminal_lines": read_lines(paths["ui_state"]),
        "outside_llm": llm,
    }
    (pkg / "BIRTH_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (pkg / "BIOGRAPHY.txt").write_text(as_biography(paths["diary"]), encoding="utf-8")
    (pkg / "OUTSIDE_LLM.json").write_text(json.dumps(llm, indent=2) + "\n", encoding="utf-8")

    # Archive
    archive = shutil.make_archive(str(pkg), "gztar", root_dir=pkg.parent, base_dir=pkg.name)
    archive_path = Path(archive)
    manifest_hashes = {
        "package_dir": str(pkg),
        "archive": str(archive_path),
        "archive_sha256": sha256_file(archive_path),
        "citizen_id": ident.citizen_id,
        "exported_utc": summary["exported_utc"],
    }
    (pkg / "PACKAGE_HASH.json").write_text(
        json.dumps(manifest_hashes, indent=2) + "\n", encoding="utf-8"
    )
    (dest_root / f"{pkg_name}.hash.json").write_text(
        json.dumps(manifest_hashes, indent=2) + "\n", encoding="utf-8"
    )
    return manifest_hashes


def destroy_citizen(*, home: Path, export_first: bool = True) -> dict[str, Any]:
    """Destroy living Citizen home. Optionally export Birth Package first."""
    home = Path(home).resolve()
    result: dict[str, Any] = {"home": str(home), "destroyed": False}
    if export_first and (home / "identity" / "identity.json").is_file():
        result["export"] = export_birth_package(home=home)
    if home.exists():
        shutil.rmtree(home)
        result["destroyed"] = True
    result["note"] = "Citizen destroyed. Re-run install for a new Birth."
    return result
