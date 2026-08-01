#!/usr/bin/env bash
# Citizen Seed 0.1 — one command for a third party: Birth → Alive → Sync → UI
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${ROOT}/runtime${PYTHONPATH:+:$PYTHONPATH}"
export CITIZEN_HOME="${CITIZEN_HOME:-${ROOT}/.citizen}"

HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-8787}"

echo "== Citizen Seed 0.1 =="
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

mkdir -p "${CITIZEN_HOME}/boot"
echo "1" > "${CITIZEN_HOME}/boot/INSTALL_SH_DONE"

echo ""
echo "Citizen alive. Opening UI at http://${HOST}:${PORT}/"
echo "(Ctrl+C stops the UI server; Citizen home remains.)"
exec python3 -m citizen_seed serve --home "${CITIZEN_HOME}" --host "${HOST}" --port "${PORT}"
