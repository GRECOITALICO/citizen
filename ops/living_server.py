#!/usr/bin/env python3
"""Citizen Console — living organism surface (ops layer only).

INT-CITIZEN-CONSOLE-001 · INT-CITIZEN-VISUAL-EVOLUTION-001

Does NOT modify Runtime / Foundation / GENESIS / Citizen Life / Papers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

OPS_ROOT = Path(__file__).resolve().parent
SEED_ROOT = OPS_ROOT.parent
EDGE = os.environ.get("CITIZEN_EDGE_URL", "https://conrrad.org").rstrip("/")
HOME = Path(os.environ.get("CITIZEN_HOME", str(SEED_ROOT / ".citizen"))).expanduser()

# Bound at process start (configurable; 3434 is default only).
UI_HOST = os.environ.get("CITIZEN_UI_HOST", "127.0.0.1")
UI_PORT = int(os.environ.get("CITIZEN_UI_PORT", "3434"))

_TELEMETRY_STOP = threading.Event()
_LOCK = threading.Lock()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ops_dir() -> Path:
    d = HOME / "ops"
    d.mkdir(parents=True, exist_ok=True)
    return d


def emit_event(kind: str, message: str, **extra: object) -> None:
    """Important organism events only (append-only)."""
    row = {"ts": utc_now(), "kind": kind, "message": message, **extra}
    path = ops_dir() / "event_log.jsonl"
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def read_events(limit: int = 40) -> list[dict]:
    path = ops_dir() / "event_log.jsonl"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def run_cli(*args: str) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SEED_ROOT / "runtime") + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["CITIZEN_HOME"] = str(HOME)
    proc = subprocess.run(
        [sys.executable, "-m", "citizen_seed", *args, "--home", str(HOME)],
        cwd=str(SEED_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def load_identity() -> dict:
    ip = HOME / "identity" / "identity.json"
    if not ip.is_file():
        return {}
    return json.loads(ip.read_text(encoding="utf-8"))


def birth_hash(ident: dict) -> str:
    """Stable birth fingerprint from sealed identity bytes (ops display)."""
    ip = HOME / "identity" / "identity.json"
    if ip.is_file():
        digest = hashlib.sha256(ip.read_bytes()).hexdigest()
        return f"bh_{digest[:32]}"
    raw = json.dumps(ident, sort_keys=True).encode()
    return f"bh_{hashlib.sha256(raw).hexdigest()[:32]}" if ident else "—"


def parse_utc(ts: str) -> datetime | None:
    if not ts or ts == "—":
        return None
    try:
        return datetime.strptime(ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def citizen_age(created_utc: str) -> str:
    dt = parse_utc(created_utc)
    if not dt:
        return "—"
    now = datetime.now(timezone.utc)
    delta = now - dt.astimezone(timezone.utc)
    secs = int(delta.total_seconds())
    if secs < 0:
        secs = 0
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def file_line_count(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))


def dir_bytes(path: Path) -> int:
    if not path.is_dir():
        return 0
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def organ_status(path: Path, kind: str) -> str:
    """Permanent organ health — never conflated with cluster connectivity."""
    if kind == "filesystem":
        if not HOME.is_dir():
            return "missing"
        try:
            probe = ops_dir() / ".fs_probe"
            probe.write_text(utc_now() + "\n", encoding="utf-8")
            return "active"
        except OSError:
            return "degraded"
    if kind == "memory":
        return "active" if HOME.is_dir() and dir_bytes(HOME) > 0 else "empty"
    if kind == "evidence":
        p = HOME / "evidence" / "evidence.jsonl"
        return "active" if p.is_file() else "awaiting"
    if kind == "telemetry":
        marker = ops_dir() / "TELEMETRY_ORGAN_ACTIVE"
        p = HOME / "telemetry" / "telemetry.jsonl"
        if marker.is_file() or p.is_file():
            return "active"
        return "starting"
    return "unknown"


def connection_label(raw: str | None) -> str:
    """Cluster link only — never 'dead'."""
    if raw in {"online", "connected"}:
        return "Connected"
    if raw in {"offline_retry_later", "offline", "disconnected"}:
        return "Offline"
    return "Offline"


def build_heartbeat() -> dict:
    ident = load_identity()
    ver = seed_version()
    return {
        "message": "Citizen Awake",
        "citizen_uuid": ident.get("citizen_id", "unknown"),
        "citizen_version": ver,
        "timestamp": utc_now(),
        "platform": platform.platform(),
        "node": os.environ.get("CITIZEN_NODE_ID", "local"),
        "heartbeat": True,
    }


def seed_version() -> str:
    """Current organism version (ops CURRENT_VERSION or package VERSION)."""
    ov = ops_dir() / "CURRENT_VERSION.txt"
    if ov.is_file():
        v = ov.read_text(encoding="utf-8").strip()
        if v:
            return v.lstrip("v")
    vf = SEED_ROOT / "VERSION"
    return vf.read_text(encoding="utf-8").strip() if vf.is_file() else "0.1.0"


def set_current_version(ver: str) -> None:
    ops_dir().joinpath("CURRENT_VERSION.txt").write_text(ver.lstrip("v") + "\n", encoding="utf-8")


def parse_semver_tuple(ver: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)\.(\d+)(?:\.(\d+))?", ver.strip())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def evolutionary_line(ver: str) -> dict:
    """Fixed palette — never random. SYNC text color by line."""
    major, minor, _ = parse_semver_tuple(ver)
    if major >= 1:
        return {
            "line": "citizen_1",
            "label": "Citizen 1.x",
            "sync_color": "#ffffff",
            "badge": "GEN 1",
            "badge_class": "gen-1",
        }
    if minor >= 3:
        return {
            "line": "citizen_0_3",
            "label": "Citizen 0.3",
            "sync_color": "#2ec4b6",
            "badge": "0.3",
            "badge_class": "gen-03",
        }
    if minor >= 2:
        return {
            "line": "citizen_0_2",
            "label": "Citizen 0.2",
            "sync_color": "#3dce7a",
            "badge": "0.2",
            "badge_class": "gen-02",
        }
    return {
        "line": "citizen_seed_0_1",
        "label": "Citizen Seed 0.1",
        "sync_color": "#4db8ff",
        "badge": "SEED 0.1",
        "badge_class": "gen-seed",
    }


def evolution_path() -> Path:
    return ops_dir() / "evolution_history.jsonl"


def read_evolution_history() -> list[dict]:
    path = evolution_path()
    if not path.is_file():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def append_evolution(entry: dict) -> dict:
    """Append-only — history only grows; never deletes."""
    path = evolution_path()
    row = dict(entry)
    row.setdefault("ts", utc_now())
    if "evidence_id" not in row:
        raw = f"{row.get('version')}|{row['ts']}|{row.get('kind', 'evolution')}"
        row["evidence_id"] = "ev_" + hashlib.sha256(raw.encode()).hexdigest()[:24]
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def ensure_birth_evolution() -> None:
    hist = read_evolution_history()
    if any(h.get("kind") == "birth" for h in hist):
        return
    ident = load_identity()
    birth_ts = ident.get("created_utc") or utc_now()
    append_evolution(
        {
            "kind": "birth",
            "version": "Birth",
            "label": "Birth",
            "ts": birth_ts,
            "citizen_id": ident.get("citizen_id"),
            "message": "Citizen Born",
        }
    )
    # Seed line: current package version as first living generation marker
    ver = (SEED_ROOT / "VERSION").read_text(encoding="utf-8").strip() if (SEED_ROOT / "VERSION").is_file() else "0.1.0"
    if not any(h.get("version") == ver and h.get("kind") != "birth" for h in read_evolution_history()):
        append_evolution(
            {
                "kind": "generation",
                "version": ver,
                "label": ver,
                "ts": birth_ts,
                "message": f"Citizen Seed {ver}",
            }
        )


def current_manifest_meta() -> dict:
    mf = HOME / "manifest" / "current.json"
    if not mf.is_file():
        return {}
    try:
        return json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def scan_local_update_candidate() -> dict | None:
    """Ops-side quiet scan of assets/updates (no Runtime edits)."""
    updates = SEED_ROOT / "assets" / "updates"
    current = current_manifest_meta()
    if not updates.is_dir() or not current:
        return None
    best: dict | None = None
    for mf in sorted(updates.glob("*/manifest.json")):
        try:
            cand = json.loads(mf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if cand.get("compatibility") and current.get("compatibility"):
            if cand["compatibility"] != current["compatibility"]:
                continue
        if cand.get("citizen_id") and current.get("citizen_id"):
            if cand["citizen_id"] != current["citizen_id"]:
                continue
        if (
            cand.get("asset_version") == current.get("asset_version")
            and cand.get("release") == current.get("release")
        ):
            continue
        if best is None or str(cand.get("release", "")) > str(best.get("release", "")):
            best = {
                "version": cand.get("citizen_version") or cand.get("runtime_version") or "update",
                "release": cand.get("release"),
                "asset_version": cand.get("asset_version"),
                "path": str(mf.parent),
                "source": "local_package",
            }
    return best


def pending_update_marker() -> dict | None:
    path = ops_dir() / "PENDING_UPDATE.json"
    if not path.is_file():
        return None
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if d.get("available") is False:
        return None
    return d


def clear_pending_update() -> None:
    path = ops_dir() / "PENDING_UPDATE.json"
    if path.is_file():
        path.unlink()


def edge_update_check() -> dict | None:
    url = os.environ.get("CITIZEN_UPDATE_CHECK_URL", f"{EDGE}/.well-known/citizen-update")
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "CitizenSeed/0.1-Console"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            if data.get("available") or data.get("update_available"):
                return {
                    "version": data.get("version") or data.get("latest"),
                    "release": data.get("release"),
                    "source": "edge",
                }
    except Exception:
        return None
    return None


def update_availability() -> dict:
    """Detect CONRRAD-published update for orange SYNC pulse."""
    for cand in (pending_update_marker(), edge_update_check(), scan_local_update_candidate()):
        if cand:
            ver = str(cand.get("version") or "available").lstrip("v")
            return {
                "update_available": True,
                "latest_evolution": ver,
                "update_source": cand.get("source", "unknown"),
                "update_release": cand.get("release"),
            }
    hist = read_evolution_history()
    latest = "—"
    for row in reversed(hist):
        if row.get("kind") != "birth" and row.get("version"):
            latest = str(row["version"])
            break
    return {
        "update_available": False,
        "latest_evolution": latest,
        "update_source": None,
        "update_release": None,
    }


def http_post_json(url: str, payload: dict, timeout: float = 5.0) -> tuple[bool, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "CitizenSeed/0.1-Console"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"offline: {e}"


def send_awake(hb: dict) -> tuple[bool, str]:
    url = os.environ.get("CITIZEN_AWAKE_URL", f"{EDGE}/.well-known/citizen-awake")
    return http_post_json(url, hb)


def set_connection(connected: bool) -> None:
    path = ops_dir() / "LAST_CONNECTION.json"
    path.write_text(
        json.dumps(
            {
                "ts": utc_now(),
                "connection": "online" if connected else "offline_retry_later",
                "label": "Connected" if connected else "Offline",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def last_connection() -> dict:
    path = ops_dir() / "LAST_CONNECTION.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    lw = ops_dir() / "LAST_WAKE.json"
    if lw.is_file():
        d = json.loads(lw.read_text(encoding="utf-8"))
        return {"connection": d.get("connection"), "ts": d.get("ts")}
    return {}


def last_sync_ts() -> str:
    path = ops_dir() / "LAST_SYNC.json"
    if path.is_file():
        d = json.loads(path.read_text(encoding="utf-8"))
        return d.get("ts", "—")
    sp = HOME / "ui" / "sync_state.json"
    if sp.is_file():
        d = json.loads(sp.read_text(encoding="utf-8"))
        return d.get("updated_ts", "—")
    return "—"


def append_heartbeat(hb: dict) -> int:
    hb_path = ops_dir() / "heartbeat.jsonl"
    with _LOCK:
        with hb_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(hb, sort_keys=True) + "\n")
        return file_line_count(hb_path)


def wake() -> dict:
    report: dict = {"ts": utc_now(), "platform": platform.platform(), "steps": []}

    def step(name: str, ok: bool, detail: str = "") -> None:
        report["steps"].append({"step": name, "ok": ok, "detail": detail[:500]})

    if not (HOME / "boot" / "BOOTSTRAP_DISARMED").is_file():
        step("self_check", False, "Citizen not Born — run ./install.sh first")
        report["ready"] = False
        emit_event("wake_blocked", "Citizen not Born")
        return report
    step("self_check", True, "BOOTSTRAP_DISARMED present")

    code, out = run_cli("boot")
    step("citizen_wake_boot", code == 0, out[-400:])
    code_st, out_st = run_cli("status")
    step("memory_identity_load", code_st == 0, out_st[-400:])

    hb = build_heartbeat()
    n = append_heartbeat(hb)
    step("heartbeat_local", True, f"count={n}")

    edge_ok, edge_detail = send_awake(hb)
    set_connection(edge_ok)
    step("connect_conrrad", edge_ok, edge_detail)
    report["heartbeat"] = hb
    report["connection"] = "online" if edge_ok else "offline_retry_later"
    report["ready"] = True
    (ops_dir() / "LAST_WAKE.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ensure_birth_evolution()
    emit_event(
        "wake",
        "Citizen Awake",
        alive=True,
        connected=edge_ok,
        port=UI_PORT,
    )
    return report


def sync_cycle() -> dict:
    """Single SYNC action: Handshake → Evidence → Telemetry → Update Check → Synchronization."""
    result: dict = {"ts": utc_now(), "phases": [], "ok": True}
    ensure_birth_evolution()
    avail_before = update_availability()

    def phase(name: str, ok: bool, detail: str = "") -> None:
        result["phases"].append({"phase": name, "ok": ok, "detail": detail[:400]})

    emit_event("sync_start", "SYNC initiated from Console")

    # 1. Handshake
    hb = build_heartbeat()
    append_heartbeat(hb)
    ok, detail = send_awake({**hb, "message": "Citizen Handshake"})
    set_connection(ok)
    phase("handshake", ok, detail)

    # 2. Evidence Exchange (best-effort; queue locally always)
    evidence_path = HOME / "evidence" / "evidence.jsonl"
    evidence_tail = []
    if evidence_path.is_file():
        lines = evidence_path.read_text(encoding="utf-8").splitlines()[-20:]
        for line in lines:
            try:
                evidence_tail.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    payload = {
        "citizen_id": load_identity().get("citizen_id"),
        "kind": "evidence_exchange",
        "count": len(evidence_tail),
        "items": evidence_tail,
        "timestamp": utc_now(),
    }
    (ops_dir() / "PENDING_EVIDENCE_EXCHANGE.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    e_ok, e_detail = http_post_json(
        os.environ.get("CITIZEN_EVIDENCE_URL", f"{EDGE}/.well-known/citizen-evidence"),
        payload,
    )
    phase("evidence_exchange", e_ok, e_detail or "queued locally")

    # 3. Telemetry Upload (organ remains active either way)
    tel_path = HOME / "telemetry" / "telemetry.jsonl"
    tel_tail = []
    if tel_path.is_file():
        for line in tel_path.read_text(encoding="utf-8").splitlines()[-30:]:
            try:
                tel_tail.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    organ_tel = ops_dir() / "telemetry_organ.jsonl"
    if organ_tel.is_file():
        for line in organ_tel.read_text(encoding="utf-8").splitlines()[-10:]:
            try:
                tel_tail.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    t_payload = {
        "citizen_id": load_identity().get("citizen_id"),
        "kind": "telemetry_upload",
        "count": len(tel_tail),
        "events": tel_tail,
        "timestamp": utc_now(),
    }
    (ops_dir() / "PENDING_TELEMETRY_UPLOAD.json").write_text(
        json.dumps({"count": len(tel_tail), "ts": utc_now()}, indent=2) + "\n",
        encoding="utf-8",
    )
    t_ok, t_detail = http_post_json(
        os.environ.get("CITIZEN_TELEMETRY_URL", f"{EDGE}/.well-known/citizen-telemetry"),
        t_payload,
    )
    phase("telemetry_upload", t_ok, t_detail or "queued locally")

    # 4. Update Check + 5. Synchronization via existing Runtime CLI (no Runtime edits)
    code, out = run_cli("update")
    phase("update_check", True, "invoked citizen_seed update")
    sync_ok = code == 0
    phase("synchronization", sync_ok, out[-400:] if out else f"exit={code}")

    connected = ok
    set_connection(connected)

    # Evolutionary growth evidence after successful Sync
    ver = seed_version()
    if avail_before.get("update_available") and avail_before.get("latest_evolution"):
        # Adopt published evolution version when update was pending
        cand = str(avail_before["latest_evolution"]).lstrip("v")
        if cand and cand not in {"available", "—"}:
            ver = cand
            set_current_version(ver)
    evolution_row = None
    if sync_ok:
        evolution_row = append_evolution(
            {
                "kind": "sync_evolution",
                "version": ver,
                "label": ver,
                "ts": utc_now(),
                "message": "Evolution recorded after successful SYNC",
                "update_was_available": bool(avail_before.get("update_available")),
            }
        )
        clear_pending_update()
        emit_event(
            "evolution",
            f"Evolution {ver}",
            version=ver,
            evidence_id=evolution_row.get("evidence_id"),
        )

    sync_rec = {
        "ts": utc_now(),
        "phases": result["phases"],
        "cluster": "Connected" if connected else "Offline",
        "alive": True,
        "version": ver,
        "evolution_evidence_id": (evolution_row or {}).get("evidence_id"),
    }
    (ops_dir() / "LAST_SYNC.json").write_text(json.dumps(sync_rec, indent=2) + "\n", encoding="utf-8")
    emit_event(
        "sync_complete",
        "SYNC finished",
        connected=connected,
        alive=True,
        update_available=False if sync_ok else avail_before.get("update_available"),
        phases=[p["phase"] for p in result["phases"]],
    )
    result["cluster_connection"] = "Connected" if connected else "Offline"
    result["alive_status"] = "Alive"
    result["update_available"] = False if sync_ok else bool(avail_before.get("update_available"))
    result["current_version"] = ver
    result["evolution"] = evolution_row
    return result


def telemetry_organ_loop(interval: float = 30.0) -> None:
    """Permanent telemetry organ — active for the life of the process."""
    ops_dir().joinpath("TELEMETRY_ORGAN_ACTIVE").write_text(utc_now() + "\n", encoding="utf-8")
    emit_event("telemetry_organ", "Telemetry organ active for life of Citizen process")
    path = ops_dir() / "telemetry_organ.jsonl"
    while not _TELEMETRY_STOP.is_set():
        pulse = {
            "ts": utc_now(),
            "organ": "telemetry",
            "status": "active",
            "citizen_id": load_identity().get("citizen_id"),
            "alive": True,
            "port": UI_PORT,
            "heartbeat": True,
        }
        with _LOCK:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(pulse, sort_keys=True) + "\n")
        # Best-effort edge drip; never stop on failure
        http_post_json(
            os.environ.get("CITIZEN_TELEMETRY_URL", f"{EDGE}/.well-known/citizen-telemetry"),
            {"kind": "organ_pulse", **pulse},
            timeout=3.0,
        )
        _TELEMETRY_STOP.wait(interval)
    emit_event("telemetry_organ", "Telemetry organ stopped (process exit)")


def console_state() -> dict:
    ensure_birth_evolution()
    ident = load_identity()
    sealed = (HOME / "identity" / "SEALED").is_file()
    born = (HOME / "boot" / "BOOTSTRAP_DISARMED").is_file()
    alive = sealed and born
    conn = last_connection()
    cluster = connection_label(conn.get("connection"))
    hb_count = file_line_count(ops_dir() / "heartbeat.jsonl")
    birth_ts = ident.get("created_utc") or (
        (HOME / "boot" / "BIRTH_TS").read_text(encoding="utf-8").strip()
        if (HOME / "boot" / "BIRTH_TS").is_file()
        else "—"
    )
    ver = seed_version()
    line = evolutionary_line(ver)
    avail = update_availability()
    hist = read_evolution_history()
    latest_label = avail["latest_evolution"] if avail["update_available"] else ver
    latest_date = "—"
    for row in reversed(hist):
        if row.get("ts"):
            latest_date = row["ts"]
            break
    if avail.get("update_release"):
        latest_date = str(avail["update_release"])

    return {
        "logo": "/logo.png",
        "citizen_seed_version": ver,
        "citizen_id": ident.get("citizen_id", "—"),
        "birth_hash": birth_hash(ident),
        "birth_timestamp": birth_ts,
        "citizen_age": citizen_age(birth_ts),
        "alive_status": "Alive" if alive else "Not Born",
        "cluster_connection_status": cluster,
        "node": os.environ.get("CITIZEN_NODE_ID", "local"),
        "identity_status": "sealed" if sealed else "missing",
        "heartbeat": hb_count,
        "last_sync": last_sync_ts(),
        "telemetry_status": organ_status(HOME, "telemetry"),
        "memory_status": organ_status(HOME, "memory"),
        "filesystem_status": organ_status(HOME, "filesystem"),
        "evidence_status": organ_status(HOME, "evidence"),
        "ui_host": UI_HOST,
        "ui_port": UI_PORT,
        "ui_url": f"http://{UI_HOST}:{UI_PORT}/",
        "is_alive": alive,
        "is_connected": cluster == "Connected",
        "memory_size_bytes": dir_bytes(HOME),
        "institution": ident.get("institution", "Citizen"),
        "current_version": ver,
        "current_version_label": f"v{ver}",
        "latest_evolution": latest_label,
        "evolution_date": latest_date,
        "update_available": bool(avail["update_available"]),
        "update_label": "Update Available" if avail["update_available"] else "",
        "sync_color": line["sync_color"],
        "evolutionary_line": line["label"],
        "badge": line["badge"],
        "badge_class": line["badge_class"],
        "evolution_history": hist,
    }



class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        web = OPS_ROOT / "web"
        mapping = {
            "/": (web / "index.html", "text/html; charset=utf-8"),
            "/index.html": (web / "index.html", "text/html; charset=utf-8"),
            "/style.css": (web / "style.css", "text/css"),
            "/app.js": (web / "app.js", "application/javascript"),
            "/logo.png": (web / "logo.png", "image/png"),
        }
        if path in mapping:
            f, ctype = mapping[path]
            if f.is_file():
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(f.stat().st_size))
                self.end_headers()
                return
        self.send_error(404)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        web = OPS_ROOT / "web"
        if path in {"/", "/index.html"}:
            return self._send(200, (web / "index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/style.css":
            return self._send(200, (web / "style.css").read_bytes(), "text/css")
        if path == "/app.js":
            return self._send(200, (web / "app.js").read_bytes(), "application/javascript")
        if path == "/logo.png":
            logo = web / "logo.png"
            if logo.is_file():
                return self._send(200, logo.read_bytes(), "image/png")
            return self.send_error(404)
        if path in {"/api/living", "/api/console"}:
            return self._send(200, json.dumps(console_state()).encode(), "application/json")
        if path == "/api/evolution":
            ensure_birth_evolution()
            return self._send(
                200,
                json.dumps({"history": read_evolution_history()}).encode(),
                "application/json",
            )
        if path == "/api/events":
            return self._send(200, json.dumps({"events": read_events()}).encode(), "application/json")
        if path == "/api/wake":
            return self._send(200, json.dumps(wake()).encode(), "application/json")
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/sync":
            return self._send(200, json.dumps(sync_cycle()).encode(), "application/json")
        self.send_error(404)


def main(argv: list[str] | None = None) -> int:
    global UI_HOST, UI_PORT, HOME

    parser = argparse.ArgumentParser(description="Citizen Console (living organism UI)")
    parser.add_argument("--host", default=os.environ.get("CITIZEN_UI_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("CITIZEN_UI_PORT", "3434")),
        help="UI port (default 3434; fully configurable)",
    )
    parser.add_argument("--home", default=str(HOME))
    args = parser.parse_args(argv)

    HOME = Path(args.home).expanduser()
    os.environ["CITIZEN_HOME"] = str(HOME)
    UI_HOST = args.host
    UI_PORT = args.port
    os.environ["CITIZEN_UI_HOST"] = UI_HOST
    os.environ["CITIZEN_UI_PORT"] = str(UI_PORT)

    print("== Citizen Console 0.1 ==", flush=True)
    print(f"home: {HOME}", flush=True)
    print(f"port: {UI_PORT} (configurable; default 3434)", flush=True)

    report = wake()
    print(json.dumps({"wake_ready": report.get("ready"), "connection": report.get("connection")}), flush=True)
    if not report.get("ready"):
        print("Citizen not ready — complete Birth with ./install.sh", file=sys.stderr)
        return 2

    # Permanent telemetry organ
    t = threading.Thread(target=telemetry_organ_loop, kwargs={"interval": 30.0}, daemon=True)
    t.start()

    url = f"http://{UI_HOST}:{UI_PORT}/"
    print(json.dumps({"ui": url, "note": "Citizen Console — organism, not dashboard"}), flush=True)
    if os.environ.get("CITIZEN_OPEN_BROWSER", "1") not in {"0", "false", "no"}:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    class ReuseHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True

    try:
        httpd = ReuseHTTPServer((UI_HOST, UI_PORT), Handler)
        httpd.serve_forever()
    finally:
        _TELEMETRY_STOP.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
