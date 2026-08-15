"""Fail-closed verification for externally signed Citizen release manifests."""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .release_contract import ContractError, validate_manifest

TRUST_ROOT_SCHEMA_VERSION = "citizen-release-trust-root/v1"
TRUST_ROOT_ALGORITHM = "Ed25519"
TRUST_ROOT_PUBLIC_KEY_FORMAT = "spki_der_base64"
ED25519_SIGNATURE_LENGTH = 64


@dataclass(frozen=True)
class TrustRoot:
    """External public verification material for one authorized release key."""

    key_id: str
    public_key: Ed25519PublicKey


def _require_exact_fields(value: Mapping[str, Any]) -> None:
    expected = {
        "schema_version",
        "key_id",
        "algorithm",
        "public_key_format",
        "public_key",
        "status",
    }
    actual = set(value)
    if actual != expected:
        raise ContractError("trust root fields mismatch")


def _decode_base64(value: Any, *, label: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label} must be a non-empty Base64 string")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ContractError(f"{label} is not valid Base64") from exc


def trust_root_from_mapping(value: Mapping[str, Any]) -> TrustRoot:
    """Parse an external KMS SPKI trust root without accepting ambiguous forms."""

    _require_exact_fields(value)
    if value.get("schema_version") != TRUST_ROOT_SCHEMA_VERSION:
        raise ContractError("trust root schema_version is invalid")
    if value.get("algorithm") != TRUST_ROOT_ALGORITHM:
        raise ContractError("trust root algorithm must be Ed25519")
    if value.get("public_key_format") != TRUST_ROOT_PUBLIC_KEY_FORMAT:
        raise ContractError("trust root public_key_format must be spki_der_base64")
    if value.get("status") != "ACTIVE":
        raise ContractError("trust root status must be ACTIVE")
    key_id = value.get("key_id")
    if not isinstance(key_id, str) or not key_id:
        raise ContractError("trust root key_id must be a non-empty string")

    der = _decode_base64(value.get("public_key"), label="trust root public_key")
    try:
        public_key = serialization.load_der_public_key(der)
    except ValueError as exc:
        raise ContractError("trust root public_key is not DER SPKI") from exc
    if not isinstance(public_key, Ed25519PublicKey):
        raise ContractError("trust root public_key is not Ed25519")
    return TrustRoot(key_id=key_id, public_key=public_key)


def load_trust_root(path: Path) -> TrustRoot:
    """Load one externally configured public trust root from JSON."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"trust root cannot be loaded: {path}") from exc
    if not isinstance(value, Mapping):
        raise ContractError("trust root must be a JSON object")
    return trust_root_from_mapping(value)


def release_signature_message(manifest: Mapping[str, Any]) -> bytes:
    """Return the frozen authority message: the ASCII manifest digest string."""

    validate_manifest(manifest)
    return str(manifest["manifest_digest"]).encode("ascii")


def verify_release_signature(manifest: Mapping[str, Any], trust_root: TrustRoot) -> None:
    """Verify a detached Ed25519 release signature or raise ContractError."""

    validate_manifest(manifest)
    signature_data = manifest["signature"]
    if signature_data["status"] != "SIGNED":
        raise ContractError("release manifest has no authority signature")
    if signature_data["key_id"] != trust_root.key_id:
        raise ContractError("release signature key_id does not match trust root")
    signature = _decode_base64(signature_data["value"], label="release signature")
    if len(signature) != ED25519_SIGNATURE_LENGTH:
        raise ContractError("release signature must be exactly 64 bytes")
    try:
        trust_root.public_key.verify(signature, release_signature_message(manifest))
    except InvalidSignature as exc:
        raise ContractError("release signature verification failed") from exc
