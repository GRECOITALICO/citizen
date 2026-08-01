"""Content addressing + HMAC signatures (stdlib only).

Seed publisher key verifies Manifests and Assets. Never executes unsigned payloads.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def sign_bytes(data: bytes, secret: bytes) -> str:
    return hmac.new(secret, data, hashlib.sha256).hexdigest()


def verify_bytes(data: bytes, signature: str, secret: bytes) -> bool:
    expected = sign_bytes(data, secret)
    return hmac.compare_digest(expected, signature)


def load_publisher_secret(path: Path) -> bytes:
    text = path.read_text(encoding="utf-8")
    lines = [
        ln.strip()
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not lines:
        raise ValueError(f"empty publisher secret: {path}")
    return lines[-1].encode("utf-8")


def sign_obj(obj: Any, secret: bytes) -> str:
    return sign_bytes(canonical_json(obj), secret)


def verify_obj(obj: Any, signature: str, secret: bytes) -> bool:
    body = {k: v for k, v in obj.items() if k != "signature"}
    return verify_bytes(canonical_json(body), signature, secret)
