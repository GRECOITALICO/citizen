#!/usr/bin/env bash
# Install Citizen 0.2 as a permanent systemd --user service (Linux).
# Does not modify Runtime / Foundation / GENESIS / Citizen Life / Papers.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer repo scripts/ calling into citizen-seed; also work when invoked from ops/
if [[ -d "${SCRIPT_DIR}/../citizen-seed/ops" ]]; then
  SEED_ROOT="$(cd "${SCRIPT_DIR}/../citizen-seed" && pwd)"
elif [[ -d "${SCRIPT_DIR}/../ops" ]]; then
  SEED_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [[ -f "${SCRIPT_DIR}/living_server.py" ]]; then
  SEED_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
  SEED_ROOT="${CITIZEN_SEED_ROOT:-}"
fi
if [[ -z "${SEED_ROOT}" || ! -f "${SEED_ROOT}/ops/living_server.py" ]]; then
  echo "Cannot locate citizen-seed/ops/living_server.py" >&2
  exit 1
fi

export CITIZEN_HOME="${CITIZEN_HOME:-${SEED_ROOT}/.citizen}"
PORT="${CITIZEN_UI_PORT:-3434}"
HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
UNIT_NAME="${CITIZEN_UNIT_NAME:-citizen-seed-living.service}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_PATH="${UNIT_DIR}/${UNIT_NAME}"
PY="$(command -v python3)"

mkdir -p "${UNIT_DIR}" "${CITIZEN_HOME}/ops"

cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=Citizen 0.2 Living Runtime
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${SEED_ROOT}
Environment=CITIZEN_HOME=${CITIZEN_HOME}
Environment=CITIZEN_UI_HOST=${HOST}
Environment=CITIZEN_UI_PORT=${PORT}
Environment=CITIZEN_OPEN_BROWSER=0
Environment=PYTHONPATH=${SEED_ROOT}/runtime
ExecStart=${PY} ${SEED_ROOT}/ops/living_server.py
Restart=on-failure
RestartSec=8
# Offline is not failure of the organism: keep restarting the process only if it exits.

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable "${UNIT_NAME}"
systemctl --user restart "${UNIT_NAME}" || systemctl --user start "${UNIT_NAME}"

# Linger so user services survive logout (best-effort; may need privileges)
if command -v loginctl >/dev/null 2>&1; then
  loginctl enable-linger "$(id -un)" 2>/dev/null || true
fi

echo "Installed systemd user unit: ${UNIT_PATH}"
echo "UI: http://${HOST}:${PORT}/"
systemctl --user is-active "${UNIT_NAME}" || true
