#!/usr/bin/env python3
"""Verify a prepared Citizen 0.2 Linux bundle without requiring a signature."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from citizen_seed.release_contract import (  # noqa: E402
    ContractError,
    validate_manifest,
    validate_release_decision,
)


def sha256_prefixed(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(bundle: Path, *, allow_pending_signature: bool) -> None:
    manifest = load_json(bundle / "release-manifest.json")
    decision = load_json(bundle / "release-decision.json")
    build = load_json(bundle / "build.json")
    validate_manifest(manifest)
    validate_release_decision(decision)

    artifact = bundle / manifest["artifact"]
    if not artifact.is_file():
        raise ContractError("artifact missing from bundle")
    if sha256_prefixed(artifact) != manifest["artifact_sha256"]:
        raise ContractError("artifact hash does not match release manifest")
    if build["artifact_sha256"] != manifest["artifact_sha256"]:
        raise ContractError("build metadata hash does not match release manifest")
    for field in ("source_commit", "source_tree", "build_id"):
        if build[field] != manifest[field]:
            raise ContractError(f"build metadata {field} does not match release manifest")
        if decision[field] != manifest[field]:
            raise ContractError(f"release decision {field} does not match release manifest")
    if decision["manifest_digest"] != manifest["manifest_digest"]:
        raise ContractError("release decision manifest digest mismatch")
    if decision["artifact_sha256"] != manifest["artifact_sha256"]:
        raise ContractError("release decision artifact digest mismatch")
    if not allow_pending_signature and manifest["signature"]["status"] != "SIGNED":
        raise ContractError("bundle has no authority signature")

    with tarfile.open(artifact, "r:gz") as archive:
        names = set(archive.getnames())
    root = f"citizen-{manifest['version']}"
    required = {
        f"{root}/install.sh",
        f"{root}/scripts/install_service_linux.sh",
        f"{root}/VERSION",
    }
    missing = sorted(required - names)
    if missing:
        raise ContractError(f"Linux installer paths missing from artifact: {missing}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--allow-pending-signature", action="store_true")
    args = parser.parse_args()
    try:
        verify(args.bundle, allow_pending_signature=args.allow_pending_signature)
    except (ContractError, OSError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"VERIFICATION_FAILED: {exc}", file=sys.stderr)
        return 2
    print("VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
