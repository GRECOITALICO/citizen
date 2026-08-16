#!/usr/bin/env python3
"""Build deterministic Citizen source-distribution artifacts (Linux / Windows WSL2).

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
LINUX_PLATFORM = "linux"
WINDOWS_WSL2_PLATFORM = "windows-wsl2"
BUNDLE_PATHS_FILE = ROOT / "release" / "windows-wsl2" / "bundle-paths.txt"
ADAPTER_VERSION_FILE = ROOT / "release" / "windows-wsl2" / "ADAPTER_VERSION"
SIGNING_INPUT_SCHEMA = "citizen-release-signing-input/v1"


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


def load_bundle_paths() -> list[Path]:
    if not BUNDLE_PATHS_FILE.is_file():
        raise BuildError(f"missing bundle manifest: {BUNDLE_PATHS_FILE}")
    paths: list[Path] = []
    for line in BUNDLE_PATHS_FILE.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        paths.append(Path(item))
    if not paths:
        raise BuildError("bundle manifest is empty")
    return sorted(set(paths), key=lambda p: p.as_posix())


def parse_porcelain_path(line: str) -> str:
    line = line.rstrip("\r\n")
    if len(line) < 3:
        return ""
    return line[2:].lstrip().strip('"')


def require_windows_bundle_inputs(paths: list[Path]) -> None:
    missing = [p for p in paths if not (ROOT / p).is_file()]
    if missing:
        raise BuildError(f"bundle paths missing: {missing[:5]}")
    allowed = {p.as_posix() for p in paths}
    outside_ok_prefixes = ("tests/",)
    dirty = git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    for line in dirty:
        if not line.strip():
            continue
        path = parse_porcelain_path(line)
        if not path:
            continue
        if path in allowed:
            continue
        if any(path.startswith(prefix) for prefix in outside_ok_prefixes):
            continue
        raise BuildError(f"source_dirty outside bundle: {path}")


def adapter_version() -> str:
    if not ADAPTER_VERSION_FILE.is_file():
        raise BuildError(f"missing adapter version: {ADAPTER_VERSION_FILE}")
    value = ADAPTER_VERSION_FILE.read_text(encoding="utf-8").strip()
    if not value:
        raise BuildError("adapter version must be non-empty")
    return value


def archive_bundle(
    *,
    destination: Path,
    version: str,
    source_epoch: int,
    relative_paths: list[Path],
) -> None:
    root_name = f"citizen-{version}"
    with destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=source_epoch) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.GNU_FORMAT) as archive:
                for relative in relative_paths:
                    source = ROOT / relative
                    if not source.is_file():
                        raise BuildError(f"bundle file missing: {relative}")
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


def signing_input(
    manifest: dict[str, Any],
    *,
    build_sidecar_digest: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": SIGNING_INPUT_SCHEMA,
        "manifest_digest": manifest["manifest_digest"],
        "signature_message_encoding": "ascii",
        "signature_message": manifest["manifest_digest"],
        "signature_algorithm": "Ed25519",
        "status": "READY_FOR_AUTHORITY",
        "notes": "Authority signs manifest_digest ASCII bytes; no KMS mutation in preflight.",
    }
    if build_sidecar_digest is not None:
        payload["build_sidecar_digest"] = build_sidecar_digest
    return payload


def build(output_dir: Path, platform: str) -> dict[str, Any]:
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

    if platform == LINUX_PLATFORM:
        require_clean_source()
        relative_paths = source_files()
        artifact_name = f"citizen-{version}-{platform}.tar.gz"
        build_command = (
            "python3 scripts/build_release.py --platform linux --output-dir <outside-checkout>"
        )
        platform_metadata: dict[str, Any] = {}
    elif platform == WINDOWS_WSL2_PLATFORM:
        relative_paths = load_bundle_paths()
        require_windows_bundle_inputs(relative_paths)
        artifact_name = f"citizen-{version}-{platform}.tar.gz"
        build_command = (
            "python3 scripts/build_release.py --platform windows-wsl2 --output-dir <outside-checkout>"
        )
        platform_metadata = {
            "adapter_version": adapter_version(),
            "adapter_branch": "codex/citizen-windows-wsl2-adapter-v2",
            "bundle_type": "windows-wsl2-archive",
            "bundle_path_count": len(relative_paths),
        }
    else:
        raise BuildError(f"unsupported platform: {platform}")

    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / artifact_name
    archive_bundle(
        destination=artifact_path,
        version=version,
        source_epoch=source_epoch,
        relative_paths=relative_paths,
    )
    artifact_sha256 = sha256_prefixed(artifact_path.read_bytes())
    build_id_material = {
        "artifact_sha256": artifact_sha256,
        "platform": platform,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "version": version,
    }
    if platform_metadata:
        build_id_material["platform_metadata"] = platform_metadata
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
        "build_command": build_command,
        "build_environment": {"SOURCE_DATE_EPOCH": str(source_epoch)},
        "build_id": build_id,
        "dependencies": ["Python >=3.11", "Python standard library", "Git"],
        "platform": platform,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "toolchain": toolchain,
        "version": version,
    }
    if platform_metadata:
        build_sidecar["platform_metadata"] = platform_metadata
    build_sidecar_bytes = canonical_json_bytes(build_sidecar)
    build_sidecar_digest = sha256_prefixed(build_sidecar_bytes)
    write_json(output_dir / "build.json", build_sidecar)
    write_json(output_dir / "release-manifest.json", manifest)
    write_json(output_dir / "release-decision.json", decision)
    write_json(
        output_dir / "signing-input.json",
        signing_input(manifest, build_sidecar_digest=build_sidecar_digest),
    )
    bundle_sha256 = sha256_prefixed(
        canonical_json_bytes(
            {
                "artifact_sha256": artifact_sha256,
                "build_id": build_id,
                "manifest_digest": manifest["manifest_digest"],
                "platform": platform,
                "platform_metadata": platform_metadata,
            }
        )
    )
    return {
        "artifact": artifact_path,
        "artifact_sha256": artifact_sha256,
        "build_id": build_id,
        "bundle_sha256": bundle_sha256,
        "manifest_digest": manifest["manifest_digest"],
        "signing_input_ready": "YES",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        default=LINUX_PLATFORM,
        choices=(LINUX_PLATFORM, WINDOWS_WSL2_PLATFORM),
    )
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
