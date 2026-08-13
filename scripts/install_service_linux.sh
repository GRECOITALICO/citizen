#!/usr/bin/env bash
# Permanent Citizen service. The service points only to ~/.conrrad/citizen/current.
set -euo pipefail
BASE="${CITIZEN_INSTALL_ROOT:-$HOME/.conrrad/citizen}"
HOME_DIR="${CITIZEN_HOME:-${BASE}/home}"
PORT="${CITIZEN_UI_PORT:-3434}"
HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
UNIT_NAME="${CITIZEN_UNIT_NAME:-citizen.service}"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT_PATH="${UNIT_DIR}/${UNIT_NAME}"
[[ -f "${BASE}/current/ops/living_server.py" ]] || { echo "Citizen release missing: ${BASE}/current" >&2; exit 1; }
mkdir -p "${UNIT_DIR}"
cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=CONRRAD Citizen
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=${BASE}/current
Environment=CITIZEN_HOME=${HOME_DIR}
Environment=CITIZEN_UI_HOST=${HOST}
Environment=CITIZEN_UI_PORT=${PORT}
Environment=CITIZEN_OPEN_BROWSER=0
ExecStart=/usr/bin/env python3 ${BASE}/current/ops/living_server.py --home ${HOME_DIR} --host ${HOST} --port ${PORT}
Restart=on-failure
RestartSec=3
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now "${UNIT_NAME}"
for _ in {1..20}; do curl -fsS --max-time 1 "http://${HOST}:${PORT}/api/living" >/dev/null 2>&1 && exit 0; sleep .5; done
echo "Citizen service did not become healthy" >&2
exit 1
