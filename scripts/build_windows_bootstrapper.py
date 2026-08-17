#!/usr/bin/env python3
"""Build a deterministic Windows EXE bootstrapper (NSIS) wrapping the WSL2 adapter.

Does not sign, tag, or publish. Does not mutate KMS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "windows" / "wsl2"))

from citizen_seed.release_contract import canonical_json_bytes, sha256_prefixed  # noqa: E402
from adapter import BOOTSTRAPPER_VERSION, INSTALLER_BASENAME  # noqa: E402

NSI = ROOT / "windows" / "bootstrapper" / "citizen-setup.nsi"
BUILD_RELEASE = ROOT / "scripts" / "build_release.py"


class BuildError(RuntimeError):
    pass


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def require_makensis() -> Path:
    candidates = []
    which = shutil.which("makensis")
    if which:
        candidates.append(Path(which))
    extracted = Path("/tmp/nsis-extract/usr/bin/makensis")
    if extracted.is_file():
        candidates.append(extracted)
    share = Path("/tmp/nsis-extract/usr/share/nsis")
    if share.is_dir():
        os.environ.setdefault("NSISDIR", str(share))
    for cand in candidates:
        try:
            subprocess.run([str(cand), "-VERSION"], check=True, capture_output=True, text=True)
            return cand
        except (OSError, subprocess.CalledProcessError):
            continue
    raise BuildError("makensis not found; extract nsis .deb or install nsis")


def zero_pe_timestamp(path: Path, epoch: int) -> None:
    data = bytearray(path.read_bytes())
    if data[:2] != b"MZ":
        raise BuildError("installer is not a PE/MZ executable")
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    if data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise BuildError("PE signature missing")
    struct.pack_into("<I", data, e_lfanew + 8, int(epoch) & 0xFFFFFFFF)
    path.write_bytes(data)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes(canonical_json_bytes(value))


def build(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise BuildError("output_dir_inside_source: use a directory outside the checkout")

    share = Path("/tmp/nsis-extract/usr/share/nsis")
    if share.is_dir():
        os.environ["NSISDIR"] = str(share)
    makensis = require_makensis()
    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    source_epoch = int(git("show", "-s", "--format=%ct", "HEAD"))
    os.environ["SOURCE_DATE_EPOCH"] = str(source_epoch)

    payload_dir = output_dir / "_payload"
    if payload_dir.exists():
        shutil.rmtree(payload_dir)
    payload_dir.mkdir(parents=True)
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILD_RELEASE),
            "--platform",
            "windows-wsl2",
            "--output-dir",
            str(payload_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload_meta = json.loads(proc.stdout.strip())
    tar_name = "citizen-0.2.0-windows-wsl2.tar.gz"
    tar_path = payload_dir / tar_name
    if not tar_path.is_file():
        raise BuildError(f"missing payload {tar_path}")

    outfile = output_dir / INSTALLER_BASENAME
    nsi_args = [
        str(makensis),
        "-V2",
        f"-DCITIZEN_VERSION=0.2.0",
        f"-DBOOTSTRAPPER_VERSION={BOOTSTRAPPER_VERSION}",
        f"-DPAYLOAD_TAR={tar_path}",
        f"-DBOOTSTRAPPER_DIR={ROOT / 'windows' / 'bootstrapper'}",
        f"-DWINDOWS_DIR={ROOT / 'windows'}",
        f"-DOUTFILE={outfile}",
        str(NSI),
    ]
    built = subprocess.run(nsi_args, cwd=ROOT, capture_output=True, text=True)
    if built.returncode != 0:
        raise BuildError(built.stdout + "\n" + built.stderr)
    zero_pe_timestamp(outfile, source_epoch)
    sha = sha256_prefixed(outfile.read_bytes())
    sidecar = {
        "artifact": INSTALLER_BASENAME,
        "artifact_sha256": sha,
        "bootstrapper_version": BOOTSTRAPPER_VERSION,
        "build_command": "python3 scripts/build_windows_bootstrapper.py --output-dir <outside-checkout>",
        "installer_type": "EXE",
        "nsis": subprocess.run([str(makensis), "-VERSION"], capture_output=True, text=True).stdout.strip(),
        "payload_artifact_sha256": payload_meta.get("artifact_sha256"),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "status": "READY_FOR_AUTHORITY",
        "notes": "Authority may Authenticode-sign the EXE; do not use Citizen runtime KMS.",
    }
    write_json(output_dir / "installer-build.json", sidecar)
    write_json(
        output_dir / "installer-signing-input.json",
        {
            "schema_version": "citizen-windows-bootstrapper-signing-input/v1",
            "artifact": INSTALLER_BASENAME,
            "artifact_sha256": sha,
            "signature_algorithm": "Authenticode-to-be-applied-by-authority",
            "status": "READY_FOR_AUTHORITY",
            "source_commit": source_commit,
        },
    )
    return {
        "artifact": str(outfile),
        "artifact_sha256": sha,
        "bootstrapper_version": BOOTSTRAPPER_VERSION,
        "installer_type": "EXE",
        "payload_artifact_sha256": payload_meta.get("artifact_sha256"),
        "source_commit": source_commit,
        "source_tree": source_tree,
        "created_at": datetime.fromtimestamp(source_epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.output_dir)
    except (BuildError, subprocess.CalledProcessError) as exc:
        print(f"BUILD_FAILED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
