"""Telemetry — unrestricted capture from t=0. No privacy. No reduction. Append-only."""

from __future__ import annotations

import json
import os
import resource
import time
from pathlib import Path
from typing import Any


def _log(telemetry_dir: Path) -> Path:
    return Path(telemetry_dir) / "telemetry.jsonl"


def host_sample() -> dict[str, Any]:
    """Capture CPU/RAM/process metrics (lab phase: everything)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    mem_rss_kb = getattr(usage, "ru_maxrss", 0)
    # Linux ru_maxrss is KB; macOS is bytes — normalize best-effort
    sample: dict[str, Any] = {
        "cpu_user_s": usage.ru_utime,
        "cpu_system_s": usage.ru_stime,
        "rss_kb": mem_rss_kb,
        "pid": os.getpid(),
        "page_faults_soft": usage.ru_minflt,
        "page_faults_hard": usage.ru_majflt,
        "voluntary_ctx": usage.ru_nvcsw,
        "involuntary_ctx": usage.ru_nivcsw,
    }
    try:
        st = os.statvfs("/")
        sample["disk_free_bytes"] = st.f_bavail * st.f_frsize
    except OSError:
        pass
    status = Path("/proc/self/status")
    if status.is_file():
        for line in status.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("VmRSS:") or line.startswith("VmSize:") or line.startswith("Threads:"):
                k, v = line.split(":", 1)
                sample[k.strip()] = v.strip()
    loadavg = Path("/proc/loadavg")
    if loadavg.is_file():
        parts = loadavg.read_text(encoding="utf-8").split()
        if len(parts) >= 3:
            sample["loadavg_1"] = parts[0]
            sample["loadavg_5"] = parts[1]
            sample["loadavg_15"] = parts[2]
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith(("MemTotal:", "MemAvailable:", "MemFree:")):
                k, v = line.split(":", 1)
                sample[k.strip()] = v.strip()
    return sample


def emit(
    telemetry_dir: Path,
    *,
    level: str,
    event: str,
    citizen_id: str = "",
    duration_ms: float | None = None,
    include_host: bool = True,
    **fields: Any,
) -> dict[str, Any]:
    telemetry_dir = Path(telemetry_dir)
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    rec: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ts_epoch": time.time(),
        "level": level,
        "event": event,
        "citizen_id": citizen_id,
        "duration_ms": duration_ms,
        **fields,
    }
    if include_host:
        rec["host"] = host_sample()
    with _log(telemetry_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    return rec


def read_tail(telemetry_dir: Path, n: int = 500) -> list[dict[str, Any]]:
    path = _log(telemetry_dir)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-n:]:
        if line.strip():
            out.append(json.loads(line))
    return out


def read_all(telemetry_dir: Path) -> list[dict[str, Any]]:
    path = _log(telemetry_dir)
    if not path.is_file():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
