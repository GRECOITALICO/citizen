"""Deterministic Windows WSL2 release preflight tests."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_release.py"
VERIFY = ROOT / "scripts" / "verify_release_bundle.py"
BUNDLE_PATHS = ROOT / "release" / "windows-wsl2" / "bundle-paths.txt"


def run_build(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--platform", "windows-wsl2", "--output-dir", str(output_dir)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout.strip())


def run_verify(bundle_dir: Path, *, allow_pending: bool = True) -> None:
    args = [sys.executable, str(VERIFY), str(bundle_dir)]
    if allow_pending:
        args.append("--allow-pending-signature")
    subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True)


def test_bundle_paths_exist_and_no_secrets() -> None:
    paths = [
        line.strip()
        for line in BUNDLE_PATHS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(paths) == len(set(paths))
    assert sorted(paths, key=str) == sorted(set(paths), key=str)
    forbidden = {".pem", ".key", "credentials"}
    allowed_secret_like = ("publisher.secret.example", "defaults.env")
    for rel in paths:
        assert (ROOT / rel).is_file(), rel
        lower = rel.lower()
        if any(name in lower for name in allowed_secret_like):
            continue
        assert ".env" not in lower
        assert not any(part in lower for part in forbidden)


def test_two_reproducible_builds_match(tmp_path: Path) -> None:
    b1 = tmp_path / "build1"
    b2 = tmp_path / "build2"
    r1 = run_build(b1)
    r2 = run_build(b2)
    a1 = (b1 / "citizen-0.2.0-windows-wsl2.tar.gz").read_bytes()
    a2 = (b2 / "citizen-0.2.0-windows-wsl2.tar.gz").read_bytes()
    assert hashlib.sha256(a1).hexdigest() == hashlib.sha256(a2).hexdigest()
    assert r1["artifact_sha256"] == r2["artifact_sha256"]
    assert r1["manifest_digest"] == r2["manifest_digest"]


def test_verify_bundle_passes(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    run_verify(bundle)


def test_signing_input_ready(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    manifest = json.loads((bundle / "release-manifest.json").read_text(encoding="utf-8"))
    signing = json.loads((bundle / "signing-input.json").read_text(encoding="utf-8"))
    assert signing["status"] == "READY_FOR_AUTHORITY"
    assert signing["manifest_digest"] == manifest["manifest_digest"]
    assert signing["signature_message"] == manifest["manifest_digest"]


def test_anti_tamper_rejects_corrupt_artifact(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    artifact = bundle / "citizen-0.2.0-windows-wsl2.tar.gz"
    data = bytearray(artifact.read_bytes())
    data[-1] ^= 0xFF
    artifact.write_bytes(data)
    with pytest.raises(subprocess.CalledProcessError):
        run_verify(bundle)


def test_anti_tamper_rejects_corrupt_manifest(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    manifest_path = bundle / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_tree"] = "f" * 40
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with pytest.raises(subprocess.CalledProcessError):
        run_verify(bundle)


def test_anti_tamper_rejects_wrong_trust_root(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    manifest = json.loads((bundle / "release-manifest.json").read_text(encoding="utf-8"))
    from citizen_seed.release_contract import apply_external_signature

    sys.path.insert(0, str(ROOT / "runtime"))
    signed = apply_external_signature(
        manifest,
        key_id="test-key",
        signature=hashlib.sha256(b"sig").hexdigest(),
    )
    (bundle / "release-manifest.json").write_bytes(
        json.dumps(signed, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    )
    bad_trust = tmp_path / "bad-trust.json"
    bad_trust.write_text(
        json.dumps(
            {
                "schema_version": "citizen-release-trust-root/v1",
                "key_id": "wrong-key",
                "algorithm": "Ed25519",
                "public_key_format": "spki_der_base64",
                "public_key": "AA==",
                "status": "ACTIVE",
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(VERIFY), str(bundle), "--trust-root", str(bad_trust)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_windows_paths_normalized_in_archive(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    run_build(bundle)
    with tarfile.open(bundle / "citizen-0.2.0-windows-wsl2.tar.gz", "r:gz") as archive:
        names = archive.getnames()
    assert all("/" not in name or "\\" not in name for name in names)
    assert any(name.endswith("windows/wsl2/setup.sh") for name in names)
