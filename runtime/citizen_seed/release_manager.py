"""Self-contained Citizen release manager."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from pathlib import Path

from .paths import layout

class ReleaseError(RuntimeError):
    pass

def install_root(home: Path) -> Path:
    return Path(home).resolve().parent

def releases_dir(home: Path) -> Path:
    p = install_root(home) / "releases"; p.mkdir(parents=True, exist_ok=True); return p

def current_link(home: Path) -> Path:
    return install_root(home) / "current"

def current_release(home: Path) -> Path | None:
    link = current_link(home)
    if link.is_symlink():
        try: return link.resolve(strict=True)
        except OSError: return None
    return link.resolve() if link.is_dir() else None

def tree_sha256(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel, data = p.relative_to(root).as_posix().encode(), p.read_bytes()
        h.update(len(rel).to_bytes(8, "big")); h.update(rel); h.update(len(data).to_bytes(8, "big")); h.update(data)
    return h.hexdigest()

def _record(home: Path, data: dict) -> None:
    p = layout(home)["home"] / "ops" / "release_state.json"; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def validate_release(home: Path, release_dir: Path) -> dict:
    home, release_dir = Path(home).resolve(), Path(release_dir).resolve()
    if not (release_dir / "ops" / "living_server.py").is_file(): raise ReleaseError("RELEASE_CONSOLE_MISSING")
    if not (release_dir / "runtime" / "citizen_seed" / "__main__.py").is_file(): raise ReleaseError("RELEASE_RUNTIME_MISSING")
    env = os.environ.copy(); env["PYTHONPATH"] = str(release_dir / "runtime"); env["CITIZEN_HOME"] = str(home); env["CITIZEN_OPEN_BROWSER"] = "0"
    proc = subprocess.run([sys.executable, "-m", "citizen_seed", "boot", "--home", str(home)], cwd=str(release_dir), env=env, capture_output=True, text=True, timeout=30)
    if proc.returncode: raise ReleaseError("RELEASE_BOOT_VALIDATION_FAILED: " + (proc.stderr or proc.stdout)[-1000:])
    return {"boot_valid": True}

def activate(home: Path, release_dir: Path, version: str) -> dict:
    home, release_dir = Path(home).resolve(), Path(release_dir).resolve(); validate_release(home, release_dir)
    link, nxt = current_link(home), install_root(home) / ".current.next"
    if nxt.exists() or nxt.is_symlink(): nxt.unlink()
    nxt.symlink_to(release_dir, target_is_directory=True); os.replace(nxt, link)
    data = {"version": version, "release_dir": str(release_dir), "tree_sha256": tree_sha256(release_dir), "status": "active"}; _record(home, data); return data

def rollback(home: Path) -> dict:
    cur = current_release(home); candidates = [p for p in releases_dir(home).iterdir() if p.is_dir() and (not cur or p.resolve() != cur.resolve())]
    if not candidates: raise ReleaseError("NO_ROLLBACK_RELEASE")
    previous = sorted(candidates, key=lambda p: p.name, reverse=True)[0]; return activate(home, previous, previous.name)

def state(home: Path) -> dict:
    cur = current_release(home); return {"current": str(cur) if cur else None, "releases": sorted(p.name for p in releases_dir(home).iterdir() if p.is_dir())}
