from __future__ import annotations

import copy
import hashlib

import pytest

from citizen_seed.release_contract import (
    ContractError,
    apply_external_signature,
    build_manifest,
    build_release_decision,
    release_manifest_digest,
    validate_manifest,
    validate_release_decision,
)


def manifest() -> dict:
    return build_manifest(
        version="0.2.0",
        tag="v0.2.0",
        source_commit="a" * 40,
        source_tree="b" * 40,
        build_id="build-example",
        platform="linux",
        artifact="citizen-0.2.0-linux.tar.gz",
        artifact_sha256="sha256:" + "c" * 64,
        created_at="2026-08-15T00:00:00Z",
        toolchain={"python": "3.11.0"},
        runtime_version="0.2.0",
        compatibility="seed-2026.1",
    )


def test_manifest_is_self_consistent() -> None:
    value = manifest()

    validate_manifest(value)
    assert value["manifest_digest"] == release_manifest_digest(value)
    assert value["signature"]["status"] == "PENDING_AUTHORITY"
    assert value["release_decision_id"].startswith("rd-")


def test_manifest_digest_rejects_provenance_change() -> None:
    value = manifest()
    changed = copy.deepcopy(value)
    changed["source_tree"] = "d" * 40

    with pytest.raises(ContractError, match="digest mismatch"):
        validate_manifest(changed)


def test_external_signature_does_not_rewrite_attested_digest() -> None:
    value = manifest()
    digest = value["manifest_digest"]

    signed = apply_external_signature(
        value,
        key_id="citizen-release-root-1",
        signature=hashlib.sha256(b"detached-signature-fixture").hexdigest(),
    )

    assert signed["manifest_digest"] == digest
    assert signed["signature"]["status"] == "SIGNED"
    validate_manifest(signed)


def test_release_decision_is_proposed_and_bound_to_manifest() -> None:
    value = manifest()
    decision = build_release_decision(value)

    validate_release_decision(decision)
    assert decision["status"] == "PROPOSED"
    assert decision["manifest_digest"] == value["manifest_digest"]
    assert decision["artifact_sha256"] == value["artifact_sha256"]


def test_pending_signature_cannot_contain_key_material() -> None:
    value = manifest()
    value["signature"]["key_id"] = "not-allowed"

    with pytest.raises(ContractError, match="pending signature"):
        validate_manifest(value)
