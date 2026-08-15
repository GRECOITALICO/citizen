"""Manifest plane — signed version authority."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import COMPATIBILITY, RUNTIME_VERSION
from .crypto import sign_obj, verify_obj


REQUIRED_FIELDS = (
    "citizen_version",
    "runtime_version",
    "asset_version",
    "knowledge_version",
    "compatibility",
    "signature",
    "release",
)


@dataclass
class Manifest:
    citizen_version: str
    runtime_version: str
    asset_version: str
    knowledge_version: str
    compatibility: str
    signature: str
    release: str
    citizen_id: str = ""
    assets: list[dict[str, str]] = field(default_factory=list)
    prev_manifest_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "citizen_version": self.citizen_version,
            "runtime_version": self.runtime_version,
            "asset_version": self.asset_version,
            "knowledge_version": self.knowledge_version,
            "compatibility": self.compatibility,
            "signature": self.signature,
            "release": self.release,
            "citizen_id": self.citizen_id,
            "assets": self.assets,
            "prev_manifest_hash": self.prev_manifest_hash,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Manifest":
        for f in REQUIRED_FIELDS:
            if f not in d:
                raise ValueError(f"manifest missing field: {f}")
        return cls(
            citizen_version=str(d["citizen_version"]),
            runtime_version=str(d["runtime_version"]),
            asset_version=str(d["asset_version"]),
            knowledge_version=str(d["knowledge_version"]),
            compatibility=str(d["compatibility"]),
            signature=str(d["signature"]),
            release=str(d["release"]),
            citizen_id=str(d.get("citizen_id", "")),
            assets=list(d.get("assets") or []),
            prev_manifest_hash=str(d.get("prev_manifest_hash", "")),
        )


def unsigned_body(m: Manifest | dict[str, Any]) -> dict[str, Any]:
    d = m.to_dict() if isinstance(m, Manifest) else dict(m)
    d.pop("signature", None)
    return d


def sign_manifest(m: Manifest, secret: bytes) -> Manifest:
    body = unsigned_body(m)
    m.signature = sign_obj(body, secret)
    return m


def verify_manifest(m: Manifest, secret: bytes) -> bool:
    return verify_obj(m.to_dict(), m.signature, secret)


def save_manifest(path: Path, m: Manifest) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(m.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> Manifest:
    return Manifest.from_dict(json.loads(path.read_text(encoding="utf-8")))


def default_seed_manifest(*, citizen_id: str, asset_entries: list[dict[str, str]], release: str) -> Manifest:
    asset_version = _merkle(asset_entries)
    return Manifest(
        citizen_version=RUNTIME_VERSION,
        runtime_version=RUNTIME_VERSION,
        asset_version=asset_version,
        knowledge_version=asset_version,
        compatibility=COMPATIBILITY,
        signature="",
        release=release,
        citizen_id=citizen_id,
        assets=asset_entries,
    )


def _merkle(entries: list[dict[str, str]]) -> str:
    from .crypto import sha256_bytes

    parts = sorted(f"{e.get('asset_id','')}:{e.get('content_hash','')}" for e in entries)
    return "sha256:" + sha256_bytes("\n".join(parts).encode("utf-8"))
