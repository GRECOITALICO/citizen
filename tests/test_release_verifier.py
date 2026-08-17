from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from citizen_seed.release_contract import (
    ContractError,
    apply_external_signature,
    build_manifest,
    build_release_decision,
    canonical_json_bytes,
)
from citizen_seed.release_verifier import (
    load_trust_root,
    release_signature_message,
    trust_root_from_mapping,
    verify_release_signature,
)

ROOT = Path(__file__).resolve().parents[1]


def manifest() -> dict:
    return build_manifest(
        version="0.0.0-test",
        tag="v0.0.0-test",
        source_commit="a" * 40,
        source_tree="b" * 40,
        build_id="build-test-only-release-verifier",
        platform="linux",
        artifact="citizen-0.0.0-test-linux.tar.gz",
        artifact_sha256="sha256:" + "c" * 64,
        created_at="2026-08-15T00:00:00Z",
        toolchain={"python": "3.13.5"},
        runtime_version="0.0.0-test",
        compatibility="test-only",
    )


def trust_root(private_key: Ed25519PrivateKey, *, key_id: str = "test-root") -> dict:
    public_der = private_key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return {
        "schema_version": "citizen-release-trust-root/v1",
        "key_id": key_id,
        "algorithm": "Ed25519",
        "public_key_format": "spki_der_base64",
        "public_key": base64.b64encode(public_der).decode("ascii"),
        "status": "ACTIVE",
    }


def signed_manifest(
    private_key: Ed25519PrivateKey, *, key_id: str = "test-root", message: bytes | None = None
) -> tuple[dict, dict]:
    unsigned = manifest()
    message = release_signature_message(unsigned) if message is None else message
    signature = base64.b64encode(private_key.sign(message)).decode("ascii")
    return apply_external_signature(unsigned, key_id=key_id, signature=signature), trust_root(
        private_key, key_id=key_id
    )


def test_external_ed25519_signature_and_spki_trust_root_verify() -> None:
    private_key = Ed25519PrivateKey.generate()
    signed, root = signed_manifest(private_key)

    verify_release_signature(signed, trust_root_from_mapping(root))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["signature"].update(value=base64.b64encode(b"x" * 64).decode("ascii")),
        lambda value: value["signature"].update(value=base64.b64encode(b"x" * 63).decode("ascii")),
        lambda value: value["signature"].update(value=base64.b64encode(b"x" * 65).decode("ascii")),
        lambda value: value["signature"].update(value="not-base64"),
        lambda value: value["signature"].update(key_id="wrong-key-id"),
        lambda value: value["signature"].update(algorithm="wrong-algorithm"),
        lambda value: value.update(source_tree="d" * 40),
    ],
    ids=[
        "modified-signature",
        "truncated-signature",
        "trailing-signature-bytes",
        "non-base64-signature",
        "wrong-key-id",
        "wrong-algorithm",
        "modified-manifest",
    ],
)
def test_release_signature_rejects_invalid_values(mutate) -> None:
    private_key = Ed25519PrivateKey.generate()
    signed, root = signed_manifest(private_key)
    mutate(signed)

    with pytest.raises(ContractError):
        verify_release_signature(signed, trust_root_from_mapping(root))


def test_release_signature_rejects_wrong_public_key_and_message_bytes() -> None:
    signing_key = Ed25519PrivateKey.generate()
    signed, root = signed_manifest(signing_key)
    wrong_root = trust_root(Ed25519PrivateKey.generate())

    with pytest.raises(ContractError, match="verification failed"):
        verify_release_signature(signed, trust_root_from_mapping(wrong_root))

    unsigned = manifest()
    newline_signature = base64.b64encode(
        signing_key.sign(release_signature_message(unsigned) + b"\n")
    ).decode("ascii")
    newline_signed = apply_external_signature(
        unsigned, key_id="test-root", signature=newline_signature
    )
    with pytest.raises(ContractError, match="verification failed"):
        verify_release_signature(newline_signed, trust_root_from_mapping(root))

    canonical_json_signature = base64.b64encode(signing_key.sign(canonical_json_bytes(unsigned))).decode(
        "ascii"
    )
    canonical_json_signed = apply_external_signature(
        unsigned, key_id="test-root", signature=canonical_json_signature
    )
    with pytest.raises(ContractError, match="verification failed"):
        verify_release_signature(canonical_json_signed, trust_root_from_mapping(root))


def test_release_signature_rejects_missing_signature_and_invalid_trust_root() -> None:
    private_key = Ed25519PrivateKey.generate()
    root = trust_root(private_key)

    with pytest.raises(ContractError, match="no authority signature"):
        verify_release_signature(manifest(), trust_root_from_mapping(root))

    malformed = copy.deepcopy(root)
    malformed["public_key_format"] = "raw_base64"
    with pytest.raises(ContractError, match="public_key_format"):
        trust_root_from_mapping(malformed)


def _write_bundle(path: Path, signed: dict) -> None:
    path.mkdir()
    artifact = path / signed["artifact"]
    with tarfile.open(artifact, "w:gz") as archive:
        for name, data in {
            "citizen-0.0.0-test/install.sh": b"#!/bin/sh\n",
            "citizen-0.0.0-test/scripts/install_service_linux.sh": b"#!/bin/sh\n",
            "citizen-0.0.0-test/VERSION": b"0.0.0-test\n",
        }.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    signed["artifact_sha256"] = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
    unsigned = dict(signed)
    unsigned["signature"] = {
        "algorithm": "Ed25519",
        "key_id": None,
        "status": "PENDING_AUTHORITY",
        "value": None,
    }
    # Rebuild so the digest binds the real TEST_ONLY artifact hash before signing.
    rebuilt = manifest()
    rebuilt["artifact_sha256"] = signed["artifact_sha256"]
    rebuilt["manifest_digest"] = ""
    from citizen_seed.release_contract import release_manifest_digest

    rebuilt["manifest_digest"] = release_manifest_digest(rebuilt)
    signed.update(rebuilt)
    (path / "release-manifest.json").write_text(json.dumps(signed), encoding="utf-8")
    (path / "release-decision.json").write_text(
        json.dumps(build_release_decision(rebuilt)), encoding="utf-8"
    )
    (path / "build.json").write_text(
        json.dumps(
            {
                "artifact_sha256": rebuilt["artifact_sha256"],
                "source_commit": rebuilt["source_commit"],
                "source_tree": rebuilt["source_tree"],
                "build_id": rebuilt["build_id"],
                "version": rebuilt["version"],
                "platform": rebuilt["platform"],
                "toolchain": rebuilt["toolchain"],
            }
        ),
        encoding="utf-8",
    )


def test_cli_verifier_accepts_valid_signature_and_rejects_tampering(tmp_path: Path) -> None:
    private_key = Ed25519PrivateKey.generate()
    signed, root = signed_manifest(private_key)
    root_path = tmp_path / "trust-root.json"
    root_path.write_text(json.dumps(root), encoding="utf-8")

    # Re-sign after the artifact hash is finalized in the TEST_ONLY bundle.
    bundle = tmp_path / "bundle"
    _write_bundle(bundle, signed)
    release_manifest = json.loads((bundle / "release-manifest.json").read_text(encoding="utf-8"))
    release_manifest["signature"] = {
        "algorithm": "Ed25519",
        "key_id": "test-root",
        "status": "SIGNED",
        "value": base64.b64encode(
            private_key.sign(release_signature_message(release_manifest))
        ).decode("ascii"),
    }
    (bundle / "release-manifest.json").write_text(json.dumps(release_manifest), encoding="utf-8")

    command = [
        sys.executable,
        str(ROOT / "scripts" / "verify_release_bundle.py"),
        str(bundle),
        "--trust-root",
        str(root_path),
    ]
    valid = subprocess.run(command, text=True, capture_output=True)
    assert valid.returncode == 0, valid.stderr

    missing_root = subprocess.run(command[:3], text=True, capture_output=True)
    assert missing_root.returncode == 2
    assert "bundle has no external trust root" in missing_root.stderr

    release_manifest["signature"]["value"] = base64.b64encode(b"x" * 64).decode("ascii")
    (bundle / "release-manifest.json").write_text(json.dumps(release_manifest), encoding="utf-8")
    tampered = subprocess.run(command, text=True, capture_output=True)
    assert tampered.returncode == 2
    assert "release signature verification failed" in tampered.stderr

    (bundle / "release-manifest.json").write_text(
        json.dumps(
            {
                **release_manifest,
                "signature": {
                    "algorithm": "Ed25519",
                    "key_id": "test-root",
                    "status": "SIGNED",
                    "value": base64.b64encode(
                        private_key.sign(release_signature_message(release_manifest))
                    ).decode("ascii"),
                },
            }
        ),
        encoding="utf-8",
    )
    with (bundle / "citizen-0.0.0-test-linux.tar.gz").open("ab") as artifact:
        artifact.write(b"tampered")
    artifact_mismatch = subprocess.run(command, text=True, capture_output=True)
    assert artifact_mismatch.returncode == 2
    assert "artifact hash does not match release manifest" in artifact_mismatch.stderr
