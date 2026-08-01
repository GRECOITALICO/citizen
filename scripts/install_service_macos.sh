#!/usr/bin/env bash
# Install Citizen Seed 0.1 as a macOS LaunchAgent.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "${SCRIPT_DIR}/../citizen-seed/ops" ]]; then
  SEED_ROOT="$(cd "${SCRIPT_DIR}/../citizen-seed" && pwd)"
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
LABEL="${CITIZEN_LAUNCH_LABEL:-org.conrrad.citizen-seed-living}"
AGENTS_DIR="${HOME}/Library/LaunchAgents"
PLIST="${AGENTS_DIR}/${LABEL}.plist"
PY="$(command -v python3)"

mkdir -p "${AGENTS_DIR}" "${CITIZEN_HOME}/ops"

cat > "${PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PY}</string>
    <string>${SEED_ROOT}/ops/living_server.py</string>
  </array>
  <key>WorkingDirectory</key><string>${SEED_ROOT}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>CITIZEN_HOME</key><string>${CITIZEN_HOME}</string>
    <key>CITIZEN_UI_HOST</key><string>${HOST}</string>
    <key>CITIZEN_UI_PORT</key><string>${PORT}</string>
    <key>CITIZEN_OPEN_BROWSER</key><string>0</string>
    <key>PYTHONPATH</key><string>${SEED_ROOT}/runtime</string>
  </dict>
  <key>StandardOutPath</key><string>${CITIZEN_HOME}/ops/living.stdout.log</string>
  <key>StandardErrorPath</key><string>${CITIZEN_HOME}/ops/living.stderr.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${PLIST}" 2>/dev/null || launchctl load -w "${PLIST}"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl kickstart -k "gui/$(id -u)/${LABEL}" 2>/dev/null || true

echo "Installed LaunchAgent: ${PLIST}"
echo "UI: http://${HOST}:${PORT}/"
