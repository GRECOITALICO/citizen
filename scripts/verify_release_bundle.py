#!/usr/bin/env python3
"""Verify a Citizen 0.2 Linux bundle and its external release signature."""

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
from citizen_seed.release_verifier import load_trust_root, verify_release_signature  # noqa: E402

LINUX_PLATFORM = "linux"
WINDOWS_WSL2_PLATFORM = "windows-wsl2"


def sha256_prefixed(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_signing_input(bundle: Path, manifest: dict, build: dict) -> None:
    path = bundle / "signing-input.json"
    if not path.is_file():
        raise ContractError("signing-input.json missing from bundle")
    payload = load_json(path)
    if payload.get("manifest_digest") != manifest["manifest_digest"]:
        raise ContractError("signing input digest mismatch")
    if payload.get("status") != "READY_FOR_AUTHORITY":
        raise ContractError("signing input is not ready")
    expected_sidecar_digest = payload.get("build_sidecar_digest")
    if expected_sidecar_digest:
        actual = "sha256:" + hashlib.sha256(
            (json.dumps(build, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
            .encode("utf-8")
        ).hexdigest()
        if actual != expected_sidecar_digest:
            raise ContractError("build sidecar digest mismatch")


def verify_artifact_layout(manifest: dict, archive: tarfile.TarFile) -> None:
    names = set(archive.getnames())
    root = f"citizen-{manifest['version']}"
    platform = manifest["platform"]
    if platform == LINUX_PLATFORM:
        required = {
            f"{root}/install.sh",
            f"{root}/scripts/install_service_linux.sh",
            f"{root}/VERSION",
        }
    elif platform == WINDOWS_WSL2_PLATFORM:
        required = {
            f"{root}/VERSION",
            f"{root}/install.sh",
            f"{root}/scripts/install_service_linux.sh",
            f"{root}/scripts/verify_release_bundle.py",
            f"{root}/windows/Install-CitizenWsl2.ps1",
            f"{root}/windows/Register-CitizenAutoStart.ps1",
            f"{root}/windows/Launch-CitizenUI.ps1",
            f"{root}/windows/wsl2/setup.sh",
            f"{root}/windows/wsl2/configure-systemd.sh",
            f"{root}/docs/windows/WINDOWS_INSTALL.md",
            f"{root}/release/windows-wsl2/bundle-paths.txt",
        }
    else:
        raise ContractError(f"unsupported platform: {platform}")
    missing = sorted(required - names)
    if missing:
        raise ContractError(f"installer paths missing from artifact: {missing}")


def verify(
    bundle: Path, *, allow_pending_signature: bool, trust_root_path: Path | None
) -> None:
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
    for field in ("version", "platform"):
        if build.get(field) != manifest[field]:
            raise ContractError(f"build sidecar {field} does not match release manifest")
    if build.get("toolchain") != manifest.get("toolchain"):
        raise ContractError("build sidecar toolchain does not match release manifest")
    if decision["manifest_digest"] != manifest["manifest_digest"]:
        raise ContractError("release decision manifest digest mismatch")
    if decision["artifact_sha256"] != manifest["artifact_sha256"]:
        raise ContractError("release decision artifact digest mismatch")
    if manifest["platform"] == WINDOWS_WSL2_PLATFORM:
        metadata = build.get("platform_metadata")
        if not isinstance(metadata, dict) or not metadata.get("adapter_version"):
            raise ContractError("windows bundle missing platform metadata")
        verify_signing_input(bundle, manifest, build)
    if manifest["signature"]["status"] == "PENDING_AUTHORITY":
        if not allow_pending_signature:
            raise ContractError("bundle has no authority signature")
    else:
        if trust_root_path is None:
            raise ContractError("bundle has no external trust root")
        verify_release_signature(manifest, load_trust_root(trust_root_path))

    with tarfile.open(artifact, "r:gz") as archive:
        verify_artifact_layout(manifest, archive)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--allow-pending-signature", action="store_true")
    parser.add_argument(
        "--trust-root",
        type=Path,
        help="External JSON trust root required to verify a signed release manifest.",
    )
    args = parser.parse_args()
    try:
        verify(
            args.bundle,
            allow_pending_signature=args.allow_pending_signature,
            trust_root_path=args.trust_root,
        )
    except (ContractError, OSError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"VERIFICATION_FAILED: {exc}", file=sys.stderr)
        return 2
    print("VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
