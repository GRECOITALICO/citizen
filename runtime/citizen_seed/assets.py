"""Asset Loader — all capability/knowledge enters only as signed Assets.

Runtime must not read ad-hoc TypeScript or internal knowledge JSON outside Assets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .crypto import sha256_bytes, sha256_file, sign_bytes, verify_bytes


@dataclass
class AssetRef:
    asset_id: str
    kind: str
    version: str
    content_hash: str
    signature: str


class AssetLoader:
    def __init__(self, assets_dir: Path, publisher_secret: bytes):
        self.assets_dir = Path(assets_dir)
        self.secret = publisher_secret

    def store_path(self, content_hash: str) -> Path:
        # content_hash may be bare hex or sha256:hex
        h = content_hash.removeprefix("sha256:")
        return self.assets_dir / h

    def install_payload(
        self,
        *,
        asset_id: str,
        kind: str,
        version: str,
        payload: bytes,
    ) -> AssetRef:
        content_hash = sha256_bytes(payload)
        dest = self.store_path(content_hash)
        dest.mkdir(parents=True, exist_ok=True)
        payload_path = dest / "payload"
        meta_path = dest / "meta.json"
        sig = sign_bytes(payload, self.secret)
        payload_path.write_bytes(payload)
        meta = {
            "asset_id": asset_id,
            "kind": kind,
            "version": version,
            "content_hash": content_hash,
            "signature": sig,
        }
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return AssetRef(**meta)

    def verify_asset(self, content_hash: str) -> AssetRef:
        dest = self.store_path(content_hash)
        meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
        payload = (dest / "payload").read_bytes()
        if sha256_bytes(payload) != meta["content_hash"].removeprefix("sha256:"):
            # meta stores bare hex
            if sha256_bytes(payload) != meta["content_hash"]:
                raise ValueError(f"asset hash mismatch: {content_hash}")
        if not verify_bytes(payload, meta["signature"], self.secret):
            raise ValueError(f"asset signature invalid: {meta.get('asset_id')}")
        return AssetRef(
            asset_id=meta["asset_id"],
            kind=meta["kind"],
            version=meta["version"],
            content_hash=meta["content_hash"],
            signature=meta["signature"],
        )

    def load_payload(self, content_hash: str) -> bytes:
        self.verify_asset(content_hash)
        return (self.store_path(content_hash) / "payload").read_bytes()

    def load_json(self, content_hash: str) -> Any:
        return json.loads(self.load_payload(content_hash).decode("utf-8"))

    def verify_manifest_assets(self, assets: list[dict[str, str]]) -> None:
        for a in assets:
            self.verify_asset(a["content_hash"])

    def iter_kinds(self, assets: list[dict[str, str]], kind: str) -> Iterator[tuple[AssetRef, bytes]]:
        for a in assets:
            ref = self.verify_asset(a["content_hash"])
            if ref.kind == kind:
                yield ref, self.load_payload(a["content_hash"])


def install_from_genesis_dir(
    loader: AssetLoader, genesis_dir: Path
) -> list[dict[str, str]]:
    """Install each genesis asset folder: meta.json + payload file."""
    entries: list[dict[str, str]] = []
    genesis_dir = Path(genesis_dir)
    if not genesis_dir.is_dir():
        return entries
    for child in sorted(genesis_dir.iterdir()):
        if not child.is_dir():
            continue
        meta = json.loads((child / "meta.json").read_text(encoding="utf-8"))
        payload = (child / "payload").read_bytes()
        # Re-sign with active publisher secret (seed packaging)
        ref = loader.install_payload(
            asset_id=meta["asset_id"],
            kind=meta["kind"],
            version=meta.get("version", "1"),
            payload=payload,
        )
        entries.append(
            {
                "asset_id": ref.asset_id,
                "kind": ref.kind,
                "content_hash": ref.content_hash,
                "version": ref.version,
            }
        )
    return entries
