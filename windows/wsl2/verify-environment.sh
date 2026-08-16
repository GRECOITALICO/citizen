#!/usr/bin/env bash
# Read-only environment checks inside WSL. Fail-closed for adapter setup.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/defaults.env"

FAIL=0

if [[ ! -f /proc/version ]] || ! grep -qi microsoft /proc/version; then
  echo "FAIL: not running under WSL (/proc/version)" >&2
  FAIL=1
else
  echo "OK: WSL detected"
fi

if grep -qi "WSL1" /proc/version 2>/dev/null; then
  echo "FAIL: WSL1 detected — WSL2 required" >&2
  FAIL=1
fi

if [[ "${CITIZEN_HOME}" == /mnt/* ]]; then
  echo "FATAL: CITIZEN_HOME must not live under /mnt/c (Windows mount)" >&2
  exit 2
fi

if [[ "${CITIZEN_UI_HOST}" != "127.0.0.1" ]]; then
  echo "FATAL: CITIZEN_UI_HOST must be 127.0.0.1 only" >&2
  exit 2
fi

if command -v systemctl >/dev/null 2>&1; then
  if ps -p 1 -o comm= 2>/dev/null | grep -qx systemd; then
    echo "OK: systemd is PID 1"
  else
    echo "WARN: systemd not PID 1 — configure-systemd.sh + wsl --shutdown required"
    FAIL=1
  fi
else
  echo "WARN: systemctl missing"
  FAIL=1
fi

if [[ "${FAIL}" -ne 0 ]]; then
  echo "VERIFY FAILED"
  exit 1
fi
echo "VERIFY OK"
exit 0
