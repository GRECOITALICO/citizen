"""Identity plane — minted once at Birth; never recreated."""

from __future__ import annotations

import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Identity:
    citizen_id: str
    identity_version: str
    created_utc: str
    institution: str

    def to_dict(self) -> dict:
        return {
            "citizen_id": self.citizen_id,
            "identity_version": self.identity_version,
            "created_utc": self.created_utc,
            "institution": self.institution,
        }


def identity_path(identity_dir: Path) -> Path:
    return identity_dir / "identity.json"


def exists(identity_dir: Path) -> bool:
    return identity_path(identity_dir).is_file()


def mint(*, identity_dir: Path, institution: str = "GRECOITALICO") -> Identity:
    """Birth-only. Raises if identity already exists."""
    if exists(identity_dir):
        raise RuntimeError("IDENTITY_EXISTS: Birth denied — citizen_id already minted")
    identity_dir.mkdir(parents=True, exist_ok=True)
    cid = "cit_" + secrets.token_hex(16)
    ident = Identity(
        citizen_id=cid,
        identity_version="1",
        created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        institution=institution,
    )
    identity_path(identity_dir).write_text(
        json.dumps(ident.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # seal marker — recreation forbidden
    (identity_dir / "SEALED").write_text("birth_complete\n", encoding="utf-8")
    return ident


def load(identity_dir: Path) -> Identity:
    p = identity_path(identity_dir)
    if not p.is_file():
        raise FileNotFoundError("identity missing — Citizen not Born")
    d = json.loads(p.read_text(encoding="utf-8"))
    return Identity(
        citizen_id=d["citizen_id"],
        identity_version=d.get("identity_version", "1"),
        created_utc=d["created_utc"],
        institution=d.get("institution", "GRECOITALICO"),
    )
