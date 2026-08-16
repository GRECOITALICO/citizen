#!/usr/bin/env bash
# Bounded WSL2 setup: systemd → install Citizen Core → reuse Linux service unit.
# Idempotent. Fail-closed. Does NOT modify release verifier, sync, or identity semantics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/defaults.env"

MARKER="${HOME}/.config/conrrad-citizen-wsl2/setup-complete.ok"
export CITIZEN_HOME
export CITIZEN_UI_HOST
export CITIZEN_UI_PORT
export CITIZEN_UNIT_NAME

echo "== Citizen WSL2 adapter setup =="
echo "repo: ${REPO_ROOT}"
echo "home: ${CITIZEN_HOME}"

bash "${SCRIPT_DIR}/verify-environment.sh" || {
  echo "-> configuring systemd (may require sudo once)"
  sudo bash "${SCRIPT_DIR}/configure-systemd.sh"
  echo "FATAL: re-run after 'wsl --shutdown' and reopening distro" >&2
  exit 3
}

if [[ -f "${MARKER}" ]] && systemctl --user is-active "${CITIZEN_UNIT_NAME}" >/dev/null 2>&1; then
  echo "OK: already configured ($(cat "${MARKER}"))"
  exit 0
fi

mkdir -p "${CITIZEN_HOME}/ops" "$(dirname "${MARKER}")"

# Reuse Linux-certified install path (Birth + service). No Windows-native runtime.
export PYTHONPATH="${REPO_ROOT}/runtime${PYTHONPATH:+:${PYTHONPATH}}"

if [[ -f "${CITIZEN_HOME}/boot/BOOTSTRAP_DISARMED" ]]; then
  echo "Citizen already born — boot only"
  python3 -m citizen_seed boot --home "${CITIZEN_HOME}"
else
  echo "Birth (first install)"
  python3 -m citizen_seed install --home "${CITIZEN_HOME}"
  python3 -m citizen_seed boot --home "${CITIZEN_HOME}"
fi

# Reuse certified Linux systemd user service — adapter does not invent new service architecture
export CITIZEN_SEED_ROOT="${REPO_ROOT}"
bash "${REPO_ROOT}/scripts/install_service_linux.sh"

if ! curl -fsS --max-time 8 "http://${CITIZEN_UI_HOST}:${CITIZEN_UI_PORT}/api/living" >/dev/null; then
  echo "WARN: living API not yet reachable (service may still be starting)"
fi

date -u +"%Y-%m-%dT%H:%M:%SZ" > "${MARKER}"
echo "OK: WSL2 adapter setup complete"
echo "UI: http://${CITIZEN_UI_HOST}:${CITIZEN_UI_PORT}/"
