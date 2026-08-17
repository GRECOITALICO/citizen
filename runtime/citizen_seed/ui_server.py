"""Citizen Console — living organism surface. Integrated into runtime."""
from __future__ import annotations

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

from . import RUNTIME_VERSION
from .update_engine import UpdateState
from .paths import citizen_home, seed_root

EDGE = os.environ.get("CITIZEN_EDGE_URL", "https://conrrad.org").rstrip("/")

_TELEMETRY_STOP = threading.Event()
_LOCK = threading.Lock()

class ServerGlobals:
    HOME: Path = Path()
    UI_HOST: str = "127.0.0.1"
    UI_PORT: int = 3434

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ops_dir() -> Path:
    d = ServerGlobals.HOME / "ops"
    d.mkdir(parents=True, exist_ok=True)
    return d

def emit_event(kind: str, message: str, **extra: object) -> None:
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
    env["CITIZEN_HOME"] = str(ServerGlobals.HOME)
    proc = subprocess.run(
        [sys.executable, "-m", "citizen_seed", *args, "--home", str(ServerGlobals.HOME)],
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")

def load_identity() -> dict:
    ip = ServerGlobals.HOME / "identity" / "identity.json"
    if not ip.is_file():
        return {}
    return json.loads(ip.read_text(encoding="utf-8"))

def birth_hash(ident: dict) -> str:
    ip = ServerGlobals.HOME / "identity" / "identity.json"
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
    if kind == "filesystem":
        if not ServerGlobals.HOME.is_dir():
            return "missing"
        try:
            probe = ops_dir() / ".fs_probe"
            probe.write_text(utc_now() + "\n", encoding="utf-8")
            return "active"
        except OSError:
            return "degraded"
    if kind == "memory":
        return "active" if ServerGlobals.HOME.is_dir() and dir_bytes(ServerGlobals.HOME) > 0 else "empty"
    if kind == "evidence":
        p = ServerGlobals.HOME / "evidence" / "evidence.jsonl"
        return "active" if p.is_file() else "awaiting"
    if kind == "telemetry":
        marker = ops_dir() / "TELEMETRY_ORGAN_ACTIVE"
        p = ServerGlobals.HOME / "telemetry" / "telemetry.jsonl"
        if marker.is_file() or p.is_file():
            return "active"
        return "starting"
    return "unknown"

def connection_label(raw: str | None) -> str:
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
    ov = ops_dir() / "CURRENT_VERSION.txt"
    if ov.is_file():
        v = ov.read_text(encoding="utf-8").strip()
        if v:
            return v.lstrip("v")
    vf = seed_root().parent / "VERSION"
    return vf.read_text(encoding="utf-8").strip() if vf.is_file() else RUNTIME_VERSION

def set_current_version(ver: str) -> None:
    ops_dir().joinpath("CURRENT_VERSION.txt").write_text(ver.lstrip("v") + "\n", encoding="utf-8")

def parse_semver_tuple(ver: str) -> tuple[int, int, int]:
    m = re.match(r"v?(\d+)\.(\d+)(?:\.(\d+))?", ver.strip())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))

def evolutionary_line(ver: str) -> dict:
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
        "label": "Citizen 0.2",
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

def parse_update_cli_output(out: str) -> dict:
    text = (out or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    return {}

def latest_non_birth_evolution_version() -> str | None:
    for row in reversed(read_evolution_history()):
        if row.get("kind") != "birth" and row.get("version"):
            return str(row["version"]).lstrip("v")
    return None

def append_evolution(entry: dict) -> dict:
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
    ver = seed_version()
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
    mf = ServerGlobals.HOME / "manifest" / "current.json"
    if not mf.is_file():
        return {}
    try:
        return json.loads(mf.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

def scan_local_update_candidate() -> dict | None:
    updates = seed_root() / "assets" / "updates"
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
        if cand.get("runtime_version") != RUNTIME_VERSION:
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
    sp = ServerGlobals.HOME / "ui" / "sync_state.json"
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

    if not (ServerGlobals.HOME / "boot" / "BOOTSTRAP_DISARMED").is_file():
        step("self_check", False, "Citizen not Born")
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
    emit_event("wake", "Citizen Awake", alive=True, connected=edge_ok, port=ServerGlobals.UI_PORT)
    return report

def sync_cycle() -> dict:
    result: dict = {"ts": utc_now(), "phases": [], "ok": True}
    ensure_birth_evolution()
    avail_before = update_availability()

    def phase(name: str, ok: bool, detail: str = "") -> None:
        result["phases"].append({"phase": name, "ok": ok, "detail": detail[:400]})

    emit_event("sync_start", "SYNC initiated from Console")

    hb = build_heartbeat()
    append_heartbeat(hb)
    ok, detail = send_awake({**hb, "message": "Citizen Handshake"})
    set_connection(ok)
    phase("handshake", ok, detail)

    evidence_path = ServerGlobals.HOME / "evidence" / "evidence.jsonl"
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
    e_ok, e_detail = http_post_json(
        os.environ.get("CITIZEN_EVIDENCE_URL", f"{EDGE}/.well-known/citizen-evidence"),
        payload,
    )
    phase("evidence_exchange", e_ok, e_detail or "queued locally")

    tel_path = ServerGlobals.HOME / "telemetry" / "telemetry.jsonl"
    tel_tail = []
    if tel_path.is_file():
        for line in tel_path.read_text(encoding="utf-8").splitlines()[-30:]:
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
    t_ok, t_detail = http_post_json(
        os.environ.get("CITIZEN_TELEMETRY_URL", f"{EDGE}/.well-known/citizen-telemetry"),
        t_payload,
    )
    phase("telemetry_upload", t_ok, t_detail or "queued locally")

    code, out = run_cli("update")
    update_payload = parse_update_cli_output(out)
    update_state = str(update_payload.get("state") or "")
    updated = update_state == UpdateState.UPDATED.value
    phase("update_check", True, f"state={update_state or 'unknown'}")
    sync_ok = code == 0
    phase("synchronization", sync_ok, out[-400:] if out else f"exit={code}")

    connected = ok
    set_connection(connected)

    ver = seed_version()
    evolution_row = None
    if updated:
        meta = current_manifest_meta()
        new_ver = str(meta.get("citizen_version") or ver).lstrip("v")
        if new_ver:
            set_current_version(new_ver)
            ver = new_ver
        if latest_non_birth_evolution_version() != ver:
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
            emit_event("evolution", f"Evolution {ver}", version=ver, evidence_id=evolution_row.get("evidence_id"))
        clear_pending_update()

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
        update_available=False if updated else avail_before.get("update_available"),
    )
    result["cluster_connection"] = "Connected" if connected else "Offline"
    result["alive_status"] = "Alive"
    avail_after = update_availability()
    result["update_available"] = (False if updated else bool(avail_after.get("update_available")))
    result["current_version"] = ver
    result["evolution"] = evolution_row
    return result

def telemetry_organ_loop(interval: float = 30.0) -> None:
    ops_dir().joinpath("TELEMETRY_ORGAN_ACTIVE").write_text(utc_now() + "\n", encoding="utf-8")
    path = ops_dir() / "telemetry_organ.jsonl"
    while not _TELEMETRY_STOP.is_set():
        pulse = {
            "ts": utc_now(),
            "organ": "telemetry",
            "status": "active",
            "citizen_id": load_identity().get("citizen_id"),
            "alive": True,
            "port": ServerGlobals.UI_PORT,
            "heartbeat": True,
        }
        with _LOCK:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(pulse, sort_keys=True) + "\n")
        http_post_json(
            os.environ.get("CITIZEN_TELEMETRY_URL", f"{EDGE}/.well-known/citizen-telemetry"),
            {"kind": "organ_pulse", **pulse},
            timeout=3.0,
        )
        _TELEMETRY_STOP.wait(interval)

def console_state() -> dict:
    ensure_birth_evolution()
    ident = load_identity()
    sealed = (ServerGlobals.HOME / "identity" / "SEALED").is_file()
    born = (ServerGlobals.HOME / "boot" / "BOOTSTRAP_DISARMED").is_file()
    alive = sealed and born
    conn = last_connection()
    cluster = connection_label(conn.get("connection"))
    hb_count = file_line_count(ops_dir() / "heartbeat.jsonl")
    birth_ts = ident.get("created_utc") or (
        (ServerGlobals.HOME / "boot" / "BIRTH_TS").read_text(encoding="utf-8").strip()
        if (ServerGlobals.HOME / "boot" / "BIRTH_TS").is_file()
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
        "telemetry_status": organ_status(ServerGlobals.HOME, "telemetry"),
        "memory_status": organ_status(ServerGlobals.HOME, "memory"),
        "filesystem_status": organ_status(ServerGlobals.HOME, "filesystem"),
        "evidence_status": organ_status(ServerGlobals.HOME, "evidence"),
        "ui_host": ServerGlobals.UI_HOST,
        "ui_port": ServerGlobals.UI_PORT,
        "ui_url": f"http://{ServerGlobals.UI_HOST}:{ServerGlobals.UI_PORT}/",
        "is_alive": alive,
        "is_connected": cluster == "Connected",
        "memory_size_bytes": dir_bytes(ServerGlobals.HOME),
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

    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        web = seed_root() / "ui"
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

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        web = seed_root() / "ui"
        proj_ui = ServerGlobals.HOME / "projection" / "ui"

        def _get_file(name: str) -> Path:
            return proj_ui / name if (proj_ui / name).is_file() else web / name

        if path in {"/", "/index.html"}:
            return self._send(200, _get_file("index.html").read_bytes(), "text/html; charset=utf-8")
        if path == "/style.css":
            return self._send(200, _get_file("style.css").read_bytes(), "text/css")
        if path == "/app.js":
            return self._send(200, _get_file("app.js").read_bytes(), "application/javascript")
        if path in {"/logo.png", "/favicon.png"}:
            logo = _get_file("logo.png")
            if logo.is_file():
                return self._send(200, logo.read_bytes(), "image/png")
            return self.send_error(404)
        if path in {"/api/living", "/api/console", "/api/state"}:
            return self._send(200, json.dumps(console_state()).encode(), "application/json")
        if path == "/api/evolution":
            ensure_birth_evolution()
            return self._send(200, json.dumps({"history": read_evolution_history()}).encode(), "application/json")
        if path == "/api/events":
            return self._send(200, json.dumps({"events": read_events()}).encode(), "application/json")
        if path == "/api/wake":
            return self._send(200, json.dumps(wake()).encode(), "application/json")
        self.send_error(404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/sync":
            return self._send(200, json.dumps(sync_cycle()).encode(), "application/json")
        self.send_error(404)

def serve(*, home: Path | None = None, host: str = "127.0.0.1", port: int = 3434) -> None:
    ServerGlobals.HOME = citizen_home(home)
    ServerGlobals.UI_HOST = host
    ServerGlobals.UI_PORT = port

    print("== Citizen UI Server ==", flush=True)
    report = wake()
    if not report.get("ready"):
        print("Citizen not ready — complete Birth with ./install.sh", file=sys.stderr)

    t = threading.Thread(target=telemetry_organ_loop, kwargs={"interval": 30.0}, daemon=True)
    t.start()

    class ReuseHTTPServer(ThreadingHTTPServer):
        allow_reuse_address = True

    try:
        httpd = ReuseHTTPServer((host, port), Handler)
        url = f"http://{host}:{port}/"
        print(json.dumps({"ui": url, "citizen_home": str(ServerGlobals.HOME)}), flush=True)
        httpd.serve_forever()
    finally:
        _TELEMETRY_STOP.set()
