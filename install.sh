#!/bin/bash
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
export CITIZEN_HOME="$HOME/.citizen"
VENV_DIR="$HOME/.citizen-env"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_SERVICE="citizen-seed-living"
SYSTEMD_UNIT="$HOME/.config/systemd/user/${SYSTEMD_SERVICE}.service"
PORT=3434
EXPECTED_VERSION="0.4.2"
# Published artifact for 0.4.2 is the GitHub Release wheel (PyPI token blocked at cut).
RELEASE_WHEEL_URL="https://github.com/GRECOITALICO/CONRRAD-CITIZEN/releases/download/v${EXPECTED_VERSION}/conrrad_citizen-${EXPECTED_VERSION}-py3-none-any.whl"
SOURCE="${RELEASE_WHEEL_URL}"

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}    CITIZEN — INSTALADOR LINUX                 ${NC}"
echo -e "${CYAN}=================================================${NC}"
FOUND_PREVIOUS=false
PREVIOUS_ITEMS=""
if [ -d "$CITIZEN_HOME" ]; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${CITIZEN_HOME} (citizen data)"; fi
if [ -d "$VENV_DIR" ]; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${VENV_DIR} (python environment)"; fi
if [ -e "$BIN_DIR/citizen" ]; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${BIN_DIR}/citizen (binary link)"; fi
if [ -e "$BIN_DIR/citizen-seed" ]; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${BIN_DIR}/citizen-seed (binary link)"; fi
if [ -f "$SYSTEMD_UNIT" ]; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${SYSTEMD_UNIT} (systemd service)"; fi
if pip3 show conrrad-citizen >/dev/null 2>&1; then FOUND_PREVIOUS=true; PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - conrrad-citizen (system pip package)"; fi
if [ "$FOUND_PREVIOUS" = true ]; then
  echo -e "${YELLOW}Previous Citizen installation detected:${NC}"
  echo -e "$PREVIOUS_ITEMS"
  echo -e "${YELLOW}Data directory ($CITIZEN_HOME) will be PRESERVED to maintain identity and memory.${NC}"
fi

PORT_PID=""
if command -v ss >/dev/null 2>&1; then PORT_PID=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1); elif command -v netstat >/dev/null 2>&1; then PORT_PID=$(netstat -tlnp 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f1 | head -1); elif command -v lsof >/dev/null 2>&1; then PORT_PID=$(lsof -ti:${PORT} 2>/dev/null | head -1); fi
if [ -n "$PORT_PID" ]; then
  PORT_CMD=$(ps -p "$PORT_PID" -o comm= 2>/dev/null || echo unknown)
  if echo "$PORT_CMD" | grep -qi "python\|citizen"; then kill "$PORT_PID" 2>/dev/null || true; sleep 1; kill -9 "$PORT_PID" 2>/dev/null || true; else echo -e "${RED}Port ${PORT} is used by ${PORT_CMD}; free it and retry.${NC}"; exit 1; fi
fi

if command -v systemctl >/dev/null 2>&1; then systemctl --user stop "$SYSTEMD_SERVICE" 2>/dev/null || true; systemctl --user disable "$SYSTEMD_SERVICE" 2>/dev/null || true; fi
rm -f "$SYSTEMD_UNIT" "$BIN_DIR/citizen" "$BIN_DIR/citizen-seed" || true
if command -v systemctl >/dev/null 2>&1; then systemctl --user daemon-reload 2>/dev/null || true; fi
rm -rf "$VENV_DIR"
pip3 uninstall -y conrrad-citizen 2>/dev/null || true

if ! command -v python3 >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv python3-pip; elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y python3 python3-pip; elif command -v pacman >/dev/null 2>&1; then sudo pacman -S --noconfirm python python-pip; else echo -e "${RED}Python3 required.${NC}"; exit 1; fi
fi
if ! python3 -c "import venv" >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv; else echo -e "${RED}python3-venv required.${NC}"; exit 1; fi
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
export PIP_NO_INPUT=1
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir --no-input "${SOURCE}"
INSTALLED_VERSION=$("$VENV_DIR/bin/python" -c "from importlib.metadata import version; print(version('conrrad-citizen'))")
if [ "$INSTALLED_VERSION" != "$EXPECTED_VERSION" ]; then echo -e "${RED}Installed ${INSTALLED_VERSION}; expected ${EXPECTED_VERSION}.${NC}"; exit 1; fi

echo -e "${GREEN}Citizen ${INSTALLED_VERSION} installed from GitHub tag v${EXPECTED_VERSION}.${NC}"
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/citizen" "$BIN_DIR/citizen"
ln -sf "$VENV_DIR/bin/citizen-seed" "$BIN_DIR/citizen-seed"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then export PATH="$BIN_DIR:$PATH"; PROFILE_FILE="$HOME/.bashrc"; [ -f "$HOME/.zshrc" ] && PROFILE_FILE="$HOME/.zshrc"; grep -q "$BIN_DIR" "$PROFILE_FILE" 2>/dev/null || echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$PROFILE_FILE"; fi

"$BIN_DIR/citizen" install
if [ ! -f "$CITIZEN_HOME/identity/SEALED" ] || [ ! -f "$CITIZEN_HOME/manifest/current.json" ]; then echo -e "${RED}Citizen birth/install verification failed.${NC}"; exit 1; fi
HAS_SYSTEMD=false
if command -v systemctl >/dev/null 2>&1 && systemctl --user status >/dev/null 2>&1; then HAS_SYSTEMD=true; fi
if [ "$HAS_SYSTEMD" = true ]; then
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user restart "$SYSTEMD_SERVICE" 2>/dev/null || true
  sleep 2
  if ! systemctl --user is-active --quiet "$SYSTEMD_SERVICE" 2>/dev/null; then nohup "$BIN_DIR/citizen" serve --port "$PORT" > "$CITIZEN_HOME/serve.log" 2>&1 & sleep 1; fi
else
  nohup "$BIN_DIR/citizen" serve --port "$PORT" > "$CITIZEN_HOME/serve.log" 2>&1 & sleep 2
fi

echo -e "${YELLOW}[7/7] Triggering remote synchronization...${NC}"
SYNC_OUT=$("$BIN_DIR/citizen" sync 2>&1 || echo "SYNC_FAILED")
if echo "$SYNC_OUT" | grep -qi '"state": "Current"'; then
  echo -e "${GREEN}SYNC_SUCCESS_CURRENT${NC}"
elif echo "$SYNC_OUT" | grep -qi '"state": "Updated"'; then
  echo -e "${GREEN}SYNC_SUCCESS_UPDATED${NC}"
else
  echo -e "${RED}SYNC_FAILED${NC}"
  echo "$SYNC_OUT"
fi

echo -e "${GREEN}Citizen ${EXPECTED_VERSION} installed and initial SYNC requested.${NC}"
echo "Identity: $(python3 -c "import json; print(json.load(open('$CITIZEN_HOME/identity/identity.json'))['citizen_id'])" 2>/dev/null || echo unknown)"
echo "Console: http://127.0.0.1:${PORT}/"
echo "Commands: citizen status | citizen sync"
