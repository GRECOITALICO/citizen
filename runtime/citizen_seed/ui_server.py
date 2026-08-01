"""Birth Observatory — Identity · Sync · Life Journal · Terminal."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .birth_lab import export_birth_package, outside_llm_report
from .crypto import load_publisher_secret
from .evidence import read_all as evidence_read
from .identity import load as load_identity
from .journal import as_biography, read_all as journal_read
from .manifest import load_manifest
from .paths import citizen_home, layout, seed_root
from .telemetry import read_tail
from .terminal import read_lines
from .timeline import read_all as timeline_read
from .updater import one_click_update, status as update_status
from .update_engine import UpdateEngine


def _ui_static() -> Path:
    return seed_root() / "ui"


def _age_seconds(created_utc: str) -> float:
    try:
        born = datetime.strptime(created_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - born).total_seconds())
    except ValueError:
        return 0.0


def _fmt_age(secs: float) -> str:
    s = int(secs)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    h = s // 3600
    return f"{h}h {(s % 3600) // 60}m"


class Handler(BaseHTTPRequestHandler):
    home: Path

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _json(self, code: int, obj) -> None:
        body = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, ctype: str) -> None:
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        home = self.home
        paths = layout(home)

        if path in {"/", "/index.html"}:
            return self._file(_ui_static() / "index.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._file(_ui_static() / "app.js", "application/javascript")
        if path == "/style.css":
            return self._file(_ui_static() / "style.css", "text/css")

        if path == "/api/state":
            try:
                ident = load_identity(paths["identity"])
                m = load_manifest(paths["manifest"] / "current.json")
                sync = {}
                sp = paths["ui_state"] / "sync_state.json"
                if sp.is_file():
                    sync = json.loads(sp.read_text(encoding="utf-8"))
                st = update_status(home=home)
                color = sync.get("color", "green")
                state = sync.get("state", "Current")
                try:
                    secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
                    eng = UpdateEngine(home, secret)
                    best, _ = eng.find_candidate(seed_root() / "assets" / "updates")
                    if best is not None and state not in {"Updating", "Updated"}:
                        state = "Update Available"
                        color = "orange"
                except Exception:
                    pass
                age_s = _age_seconds(ident.created_utc)
                return self._json(
                    200,
                    {
                        "citizen_id": ident.citizen_id,
                        "status": "alive",
                        "age_seconds": age_s,
                        "age": _fmt_age(age_s),
                        "born_utc": ident.created_utc,
                        "runtime_version": m.runtime_version,
                        "manifest_version": m.citizen_version,
                        "citizen_version": m.citizen_version,
                        "release": m.release,
                        "sync_state": state,
                        "sync_color": color,
                        "manifest_ok": st.get("manifest_ok"),
                    },
                )
            except Exception as e:
                return self._json(500, {"error": str(e)})

        if path == "/api/terminal":
            return self._json(200, {"lines": read_lines(paths["ui_state"])})

        if path == "/api/journal":
            return self._json(
                200,
                {
                    "entries": journal_read(paths["diary"]),
                    "biography": as_biography(paths["diary"]),
                },
            )

        if path == "/api/timeline":
            return self._json(200, {"nodes": timeline_read(paths["timeline"])})

        if path == "/api/timeline/node":
            qs = parse_qs(parsed.query)
            node = (qs.get("node") or [""])[0]
            nodes = [n for n in timeline_read(paths["timeline"]) if n.get("node") == node]
            types = set()
            for n in nodes:
                types.update(n.get("evidence_types") or [])
            related = [
                e
                for e in evidence_read(paths["evidence"])
                if e.get("event_type") in types
                or (node and node.lower() in str(e.get("event_type", "")).lower())
            ]
            return self._json(200, {"node": node, "timeline": nodes, "evidence": related})

        if path == "/api/telemetry":
            return self._json(200, {"events": read_tail(paths["telemetry"], 400)})

        if path == "/api/lab-report":
            return self._json(200, outside_llm_report(home))

        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/sync":
            try:
                return self._json(200, one_click_update(home=self.home))
            except Exception as e:
                return self._json(500, {"error": str(e)})
        if parsed.path == "/api/export-birth":
            try:
                return self._json(200, export_birth_package(home=self.home))
            except Exception as e:
                return self._json(500, {"error": str(e)})
        self.send_error(404)


def serve(*, home: Path | None = None, host: str = "127.0.0.1", port: int = 8787) -> None:
    home = citizen_home(home)
    Handler.home = home
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"ui": f"http://{host}:{port}/", "citizen_home": str(home)}))
    httpd.serve_forever()
