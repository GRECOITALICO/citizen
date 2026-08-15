#!/usr/bin/env python3
"""Build the deterministic Linux Citizen source-distribution artifact.

This builder creates provenance records with a pending signature and a proposed
release decision.  It never creates a tag, signs, publishes, or authorizes a
release.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from citizen_seed.release_contract import (  # noqa: E402
    build_manifest,
    build_release_decision,
    canonical_json_bytes,
    sha256_prefixed,
)

VERSION_PATTERN = re.compile(r'^(?:__version__|RUNTIME_VERSION) = "([^"]+)"$')
COMPATIBILITY_PATTERN = re.compile(r'^COMPATIBILITY = "([^"]+)"$')


class BuildError(RuntimeError):
    """Raised when the source checkout cannot produce a trusted build."""


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def require_clean_source() -> None:
    dirty = git("status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise BuildError("source_dirty: build requires a clean checkout")


def source_versions() -> tuple[str, str]:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    init = (ROOT / "runtime" / "citizen_seed" / "__init__.py").read_text(
        encoding="utf-8"
    )
    versions = [
        match.group(1)
        for line in init.splitlines()
        if (match := VERSION_PATTERN.match(line))
    ]
    compatibility = next(
        (match.group(1) for line in init.splitlines() if (match := COMPATIBILITY_PATTERN.match(line))),
        None,
    )
    if not version or versions != [version, version] or not compatibility:
        raise BuildError("version_mismatch: VERSION and runtime constants must agree")
    return version, compatibility


def source_files() -> list[Path]:
    tracked = git("ls-files", "-z").split("\0")
    return [Path(item) for item in tracked if item]


def archive_source(*, destination: Path, version: str, source_epoch: int) -> None:
    root_name = f"citizen-{version}"
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=source_epoch) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.GNU_FORMAT) as archive:
                for relative in source_files():
                    source = ROOT / relative
                    if not source.is_file():
                        raise BuildError(f"unsupported tracked source entry: {relative}")
                    info = tarfile.TarInfo(f"{root_name}/{relative.as_posix()}")
                    source_stat = source.stat()
                    info.size = source_stat.st_size
                    info.mode = stat.S_IMODE(source_stat.st_mode)
                    info.mtime = source_epoch
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    with source.open("rb") as handle:
                        archive.addfile(info, handle)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_bytes(canonical_json_bytes(value))


def build(output_dir: Path, platform: str) -> dict[str, Any]:
    require_clean_source()
    if platform != "linux":
        raise BuildError("platform_mismatch: Citizen 0.2 build contract is Linux-first")
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise BuildError("output_dir_inside_source: use a directory outside the checkout")

    source_commit = git("rev-parse", "HEAD")
    source_tree = git("rev-parse", "HEAD^{tree}")
    source_epoch = int(git("show", "-s", "--format=%ct", "HEAD"))
    version, compatibility = source_versions()
    artifact_name = f"citizen-{version}-{platform}.tar.gz"
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / artifact_name
    archive_source(
        destination=artifact_path,
        version=version,
        source_epoch=source_epoch,
    )
    artifact_sha256 = sha256_prefixed(artifact_path.read_bytes())
    build_id_material = {
        "artifact_sha256": artifact_sha256,
        "platform": platform,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "version": version,
    }
    build_id = "build-" + hashlib.sha256(
        canonical_json_bytes(build_id_material)
    ).hexdigest()[:20]
    created_at = datetime.fromtimestamp(source_epoch, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    toolchain = {
        "builder": "scripts/build_release.py",
        "git": git("--version"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }
    manifest = build_manifest(
        version=version,
        tag=f"v{version}",
        source_commit=source_commit,
        source_tree=source_tree,
        build_id=build_id,
        platform=platform,
        artifact=artifact_name,
        artifact_sha256=artifact_sha256,
        created_at=created_at,
        toolchain=toolchain,
        runtime_version=version,
        compatibility=compatibility,
    )
    decision = build_release_decision(manifest)
    build_sidecar = {
        "artifact_path": artifact_name,
        "artifact_sha256": artifact_sha256,
        "build_command": "python3 scripts/build_release.py --platform linux --output-dir <outside-checkout>",
        "build_environment": {"SOURCE_DATE_EPOCH": str(source_epoch)},
        "build_id": build_id,
        "dependencies": ["Python >=3.11", "Python standard library", "Git"],
        "platform": platform,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "toolchain": toolchain,
        "version": version,
    }
    write_json(output_dir / "build.json", build_sidecar)
    write_json(output_dir / "release-manifest.json", manifest)
    write_json(output_dir / "release-decision.json", decision)
    return {
        "artifact": artifact_path,
        "artifact_sha256": artifact_sha256,
        "build_id": build_id,
        "manifest_digest": manifest["manifest_digest"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", default="linux", choices=("linux",))
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.output_dir, args.platform)
    except (BuildError, subprocess.CalledProcessError) as exc:
        print(f"BUILD_FAILED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({key: str(value) for key, value in result.items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
