"""Canonical release provenance contracts, separate from runtime manifests.

This module intentionally creates release metadata only.  It neither authorizes a
release nor signs one: protected signing remains an external authority action.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

MANIFEST_SCHEMA_VERSION = "citizen-release-manifest/v1"
DECISION_SCHEMA_VERSION = "citizen-release-decision/v1"
SIGNATURE_ALGORITHM = "Ed25519"
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DECISION_STATUSES = frozenset({"PROPOSED", "APPROVED", "REJECTED"})

MANIFEST_FIELDS = (
    "schema_version",
    "version",
    "tag",
    "source_commit",
    "source_tree",
    "build_id",
    "platform",
    "artifact",
    "artifact_sha256",
    "created_at",
    "toolchain",
    "runtime_version",
    "compatibility",
    "manifest_digest",
    "signature",
    "release_decision_id",
)

DECISION_FIELDS = (
    "schema_version",
    "status",
    "release_decision_id",
    "version",
    "tag",
    "source_commit",
    "source_tree",
    "build_id",
    "artifact_sha256",
    "manifest_digest",
    "signature",
)


class ContractError(ValueError):
    """Raised when release provenance is incomplete or internally inconsistent."""


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def sha256_prefixed(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def pending_signature() -> dict[str, Any]:
    """Return the only signature state allowed before protected authority acts."""
    return {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": None,
        "status": "PENDING_AUTHORITY",
        "value": None,
    }


def release_manifest_digest(manifest: Mapping[str, Any]) -> str:
    """Digest release provenance, excluding the self-reference and detached signature.

    A future Ed25519 authority signs this digest.  Excluding the signature lets
    it be attached without changing the bytes that it attests to.
    """
    body = dict(manifest)
    body.pop("manifest_digest", None)
    body.pop("signature", None)
    return sha256_prefixed(canonical_json_bytes(body))


def release_decision_id(
    *, version: str, source_commit: str, source_tree: str, build_id: str
) -> str:
    material = {
        "build_id": build_id,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "version": version,
    }
    return "rd-" + hashlib.sha256(canonical_json_bytes(material)).hexdigest()[:20]


def build_manifest(
    *,
    version: str,
    tag: str,
    source_commit: str,
    source_tree: str,
    build_id: str,
    platform: str,
    artifact: str,
    artifact_sha256: str,
    created_at: str,
    toolchain: Mapping[str, str],
    runtime_version: str,
    compatibility: str,
) -> dict[str, Any]:
    decision_id = release_decision_id(
        version=version,
        source_commit=source_commit,
        source_tree=source_tree,
        build_id=build_id,
    )
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "version": version,
        "tag": tag,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "build_id": build_id,
        "platform": platform,
        "artifact": artifact,
        "artifact_sha256": artifact_sha256,
        "created_at": created_at,
        "toolchain": dict(toolchain),
        "runtime_version": runtime_version,
        "compatibility": compatibility,
        "manifest_digest": "",
        "signature": pending_signature(),
        "release_decision_id": decision_id,
    }
    manifest["manifest_digest"] = release_manifest_digest(manifest)
    validate_manifest(manifest)
    return manifest


def build_release_decision(manifest: Mapping[str, Any]) -> dict[str, Any]:
    validate_manifest(manifest)
    decision = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "status": "PROPOSED",
        "release_decision_id": manifest["release_decision_id"],
        "version": manifest["version"],
        "tag": manifest["tag"],
        "source_commit": manifest["source_commit"],
        "source_tree": manifest["source_tree"],
        "build_id": manifest["build_id"],
        "artifact_sha256": manifest["artifact_sha256"],
        "manifest_digest": manifest["manifest_digest"],
        "signature": pending_signature(),
    }
    validate_release_decision(decision)
    return decision


def _require_exact_fields(
    value: Mapping[str, Any], fields: tuple[str, ...], label: str
) -> None:
    actual = set(value)
    expected = set(fields)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ContractError(f"{label} fields mismatch: missing={missing}, extra={extra}")


def _require_nonempty_string(value: Mapping[str, Any], field: str, label: str) -> None:
    if not isinstance(value.get(field), str) or not value[field]:
        raise ContractError(f"{label} {field} must be a non-empty string")


def _validate_signature(signature: Any, label: str) -> None:
    if not isinstance(signature, Mapping):
        raise ContractError(f"{label} signature must be an object")
    if signature.get("algorithm") != SIGNATURE_ALGORITHM:
        raise ContractError(f"{label} signature algorithm must be Ed25519")
    status = signature.get("status")
    if status == "PENDING_AUTHORITY":
        if signature.get("key_id") is not None or signature.get("value") is not None:
            raise ContractError(f"{label} pending signature must not contain key material")
        return
    if status != "SIGNED":
        raise ContractError(f"{label} signature status is invalid")
    _require_nonempty_string(signature, "key_id", f"{label} signature")
    _require_nonempty_string(signature, "value", f"{label} signature")


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    _require_exact_fields(manifest, MANIFEST_FIELDS, "release manifest")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ContractError("release manifest schema_version is invalid")
    for field in (
        "version",
        "tag",
        "source_commit",
        "source_tree",
        "build_id",
        "platform",
        "artifact",
        "artifact_sha256",
        "created_at",
        "runtime_version",
        "compatibility",
        "manifest_digest",
        "release_decision_id",
    ):
        _require_nonempty_string(manifest, field, "release manifest")
    if not DIGEST_PATTERN.fullmatch(manifest["artifact_sha256"]):
        raise ContractError("release manifest artifact_sha256 is invalid")
    if not DIGEST_PATTERN.fullmatch(manifest["manifest_digest"]):
        raise ContractError("release manifest manifest_digest is invalid")
    if not isinstance(manifest["toolchain"], Mapping) or not manifest["toolchain"]:
        raise ContractError("release manifest toolchain must be a non-empty object")
    _validate_signature(manifest["signature"], "release manifest")
    if release_manifest_digest(manifest) != manifest["manifest_digest"]:
        raise ContractError("release manifest digest mismatch")


def validate_release_decision(decision: Mapping[str, Any]) -> None:
    _require_exact_fields(decision, DECISION_FIELDS, "release decision")
    if decision.get("schema_version") != DECISION_SCHEMA_VERSION:
        raise ContractError("release decision schema_version is invalid")
    if decision.get("status") not in DECISION_STATUSES:
        raise ContractError("release decision status is invalid")
    for field in (
        "release_decision_id",
        "version",
        "tag",
        "source_commit",
        "source_tree",
        "build_id",
        "artifact_sha256",
        "manifest_digest",
    ):
        _require_nonempty_string(decision, field, "release decision")
    for field in ("artifact_sha256", "manifest_digest"):
        if not DIGEST_PATTERN.fullmatch(decision[field]):
            raise ContractError(f"release decision {field} is invalid")
    _validate_signature(decision["signature"], "release decision")


def apply_external_signature(
    manifest: Mapping[str, Any], *, key_id: str, signature: str
) -> dict[str, Any]:
    """Attach an externally-produced Ed25519 detached signature.

    This deliberately accepts a signature value only; private-key handling and
    cryptographic verification belong to the protected signing authority.
    """
    validate_manifest(manifest)
    if manifest["signature"]["status"] != "PENDING_AUTHORITY":
        raise ContractError("release manifest already has a signature state")
    signed = dict(manifest)
    signed["signature"] = {
        "algorithm": SIGNATURE_ALGORITHM,
        "key_id": key_id,
        "status": "SIGNED",
        "value": signature,
    }
    validate_manifest(signed)
    return signed
