#!/usr/bin/env bash
# Citizen Seed 0.1 — Birth → permanent OS service → living Web UI (localhost:3434)
# Operational layer only; does not modify Runtime / Foundation / GENESIS / Life / Papers.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${ROOT}/runtime${PYTHONPATH:+:$PYTHONPATH}"
export CITIZEN_HOME="${CITIZEN_HOME:-${ROOT}/.citizen}"

HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-3434}"

# Repo scripts/ (when seed lives inside CONRRAD) or sibling
SCRIPTS=""
if [[ -x "${ROOT}/../scripts/install_service_linux.sh" ]]; then
  SCRIPTS="$(cd "${ROOT}/../scripts" && pwd)"
elif [[ -x "${ROOT}/scripts/install_service_linux.sh" ]]; then
  SCRIPTS="${ROOT}/scripts"
fi

echo "== Citizen Seed 0.1 (Living) =="
echo "home: ${CITIZEN_HOME}"

if [[ -f "${CITIZEN_HOME}/boot/BOOTSTRAP_DISARMED" ]]; then
  echo "Installer already gone. Booting existing Citizen..."
  python3 -m citizen_seed boot --home "${CITIZEN_HOME}"
else
  echo "Birth..."
  python3 -m citizen_seed install --home "${CITIZEN_HOME}"
  python3 -m citizen_seed boot --home "${CITIZEN_HOME}"
fi

echo "Sync..."
python3 -m citizen_seed update --home "${CITIZEN_HOME}" || true

mkdir -p "${CITIZEN_HOME}/boot" "${CITIZEN_HOME}/ops"
echo "1" > "${CITIZEN_HOME}/boot/INSTALL_SH_DONE"
echo "1" > "${CITIZEN_HOME}/ops/LIVING_ENABLED"

install_service() {
  local os
  os="$(uname -s 2>/dev/null || echo unknown)"
  if [[ -z "${SCRIPTS}" ]]; then
    echo "WARN: service installers not found; starting living UI in foreground."
    return 1
  fi
  case "${os}" in
    Linux)
      bash "${SCRIPTS}/install_service_linux.sh" || return 1
      ;;
    Darwin)
      bash "${SCRIPTS}/install_service_macos.sh" || return 1
      ;;
    MINGW*|MSYS*|CYGWIN*)
      echo "Windows: run scripts/install_service_windows.ps1 as Administrator."
      return 1
      ;;
    *)
      echo "WARN: unsupported OS for auto service: ${os}"
      return 1
      ;;
  esac
  return 0
}

echo ""
if install_service; then
  echo "Citizen registered as permanent OS service."
  echo "Living UI: http://${HOST}:${PORT}/"
  echo "(Reboot will Wake Citizen; no need to re-run ./install.sh)"
  # Best-effort open browser once for the operator
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://${HOST}:${PORT}/" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "http://${HOST}:${PORT}/" >/dev/null 2>&1 || true
  fi
  # Wait briefly for API then exit (organism lives in the service)
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if curl -fsS --max-time 1 "http://${HOST}:${PORT}/api/living" >/dev/null 2>&1; then
      echo "Living API ready."
      exit 0
    fi
    sleep 0.5
  done
  echo "Service started; UI may still be coming up. Check: scripts/verify_service.sh"
  exit 0
fi

echo "Citizen alive. Opening living UI at http://${HOST}:${PORT}/"
echo "(Ctrl+C stops this foreground process; prefer OS service install when available.)"
export CITIZEN_UI_HOST="${HOST}"
export CITIZEN_UI_PORT="${PORT}"
export CITIZEN_OPEN_BROWSER="${CITIZEN_OPEN_BROWSER:-1}"
exec python3 "${ROOT}/ops/living_server.py"
