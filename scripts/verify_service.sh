#!/usr/bin/env bash
# Verify Citizen Console / living service (Citizen 0.2 operational layer).
set -euo pipefail

HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-3434}"
URL="http://${HOST}:${PORT}/api/console"
UNIT="${CITIZEN_UNIT_NAME:-citizen-seed-living.service}"
FAIL=0

echo "== verify_service =="
echo "ui: ${URL}"

if command -v systemctl >/dev/null 2>&1; then
  if systemctl --user is-enabled "${UNIT}" >/dev/null 2>&1; then
    echo "systemd: enabled ${UNIT}"
  else
    echo "systemd: unit not enabled (ok if using LaunchAgent/Windows or foreground)"
  fi
  if systemctl --user is-active "${UNIT}" >/dev/null 2>&1; then
    echo "systemd: active ${UNIT}"
  else
    echo "systemd: not active"
  fi
fi

if ! curl -fsS --max-time 5 "${URL}" >/tmp/citizen_living_verify.json 2>/dev/null; then
  echo "FAIL: console API not reachable at ${URL}"
  FAIL=1
else
  echo "OK: /api/console reachable"
  python3 - <<'PY' || FAIL=1
import json, sys
d = json.load(open("/tmp/citizen_living_verify.json"))
need = [
  "citizen_seed_version","citizen_id","birth_hash","birth_timestamp","citizen_age",
  "alive_status","cluster_connection_status","node","identity_status","heartbeat",
  "last_sync","telemetry_status","memory_status","filesystem_status","evidence_status",
  "ui_port",
]
missing = [k for k in need if k not in d]
if missing:
    print("FAIL: missing console fields:", missing)
    sys.exit(1)
conn = d.get("cluster_connection_status")
if conn == "Dead":
    print("FAIL: Offline must never appear as Dead")
    sys.exit(1)
print("OK: console fields present")
print("alive:", d.get("alive_status"), "cluster:", conn, "id:", d.get("citizen_id"), "port:", d.get("ui_port"))
print("telemetry organ:", d.get("telemetry_status"))
PY
fi

if [[ "${FAIL}" -ne 0 ]]; then
  echo "VERIFY FAILED"
  exit 1
fi
echo "VERIFY OK — Citizen Console ready"
exit 0
