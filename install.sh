#!/bin/bash
# Citizen Seed — Linux Nuclear Installer
# Detects previous installations, cleans everything, installs fresh.
# Zero friction. Zero leftover state. Zero errors.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

CITIZEN_HOME="$HOME/.citizen"
VENV_DIR="$HOME/.citizen-env"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_SERVICE="citizen-seed-living"
SYSTEMD_UNIT="$HOME/.config/systemd/user/${SYSTEMD_SERVICE}.service"
PORT=3434

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}    CITIZEN — INSTALADOR NUCLEAR (LINUX)          ${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# ─────────────────────────────────────────────────
# PHASE 1: DETECT PREVIOUS INSTALLATION
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[1/6] Detecting previous Citizen installation...${NC}"

FOUND_PREVIOUS=false
PREVIOUS_ITEMS=""

if [ -d "$CITIZEN_HOME" ]; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${CITIZEN_HOME} (citizen data)"
fi
if [ -d "$VENV_DIR" ]; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${VENV_DIR} (python environment)"
fi
if [ -L "$BIN_DIR/citizen" ] || [ -f "$BIN_DIR/citizen" ]; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${BIN_DIR}/citizen (binary link)"
fi
if [ -L "$BIN_DIR/citizen-seed" ] || [ -f "$BIN_DIR/citizen-seed" ]; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${BIN_DIR}/citizen-seed (binary link)"
fi
if [ -f "$SYSTEMD_UNIT" ]; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - ${SYSTEMD_UNIT} (systemd service)"
fi

# Check for pip-installed citizen outside venv
if pip3 show conrrad-citizen >/dev/null 2>&1; then
    FOUND_PREVIOUS=true
    PREVIOUS_ITEMS="${PREVIOUS_ITEMS}\n  - conrrad-citizen (system pip package)"
fi

if [ "$FOUND_PREVIOUS" = true ]; then
    echo -e "${YELLOW}Previous Citizen installation detected:${NC}"
    echo -e "$PREVIOUS_ITEMS"
    echo ""
    echo -e "${YELLOW}NOTE: Data directory ($CITIZEN_HOME) will be PRESERVED to maintain identity and memory.${NC}"
fi

# ─────────────────────────────────────────────────
# PHASE 2: CHECK PORT AVAILABILITY
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[2/6] Checking port ${PORT}...${NC}"

PORT_PID=""
if command -v ss >/dev/null 2>&1; then
    PORT_PID=$(ss -tlnp 2>/dev/null | grep ":${PORT} " | grep -oP 'pid=\K[0-9]+' | head -1)
elif command -v netstat >/dev/null 2>&1; then
    PORT_PID=$(netstat -tlnp 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f1 | head -1)
elif command -v lsof >/dev/null 2>&1; then
    PORT_PID=$(lsof -ti:${PORT} 2>/dev/null | head -1)
fi

if [ -n "$PORT_PID" ]; then
    PORT_CMD=$(ps -p "$PORT_PID" -o comm= 2>/dev/null || echo "unknown")
    echo -e "  Port ${PORT} is occupied by PID ${PORT_PID} (${PORT_CMD})"
    
    # If it's a previous citizen process, kill it
    if echo "$PORT_CMD" | grep -qi "python\|citizen"; then
        echo -e "  Stopping previous Citizen process..."
        kill "$PORT_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$PORT_PID" 2>/dev/null || true
        echo -e "  ${GREEN}Port ${PORT} freed.${NC}"
    else
        echo -e "${RED}Port ${PORT} is used by another program (${PORT_CMD}).${NC}"
        echo -e "${RED}Free port ${PORT} and try again.${NC}"
        exit 1
    fi
else
    echo -e "  ${GREEN}Port ${PORT} is available.${NC}"
fi

# ─────────────────────────────────────────────────
# PHASE 3: NUCLEAR CLEANUP
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[3/6] Cleaning previous installation...${NC}"

# Stop systemd service
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user stop "$SYSTEMD_SERVICE" 2>/dev/null || true
    systemctl --user disable "$SYSTEMD_SERVICE" 2>/dev/null || true
fi

# Remove systemd unit
rm -f "$SYSTEMD_UNIT" || true
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload 2>/dev/null || true
fi

# Remove binary links
rm -f "$BIN_DIR/citizen" "$BIN_DIR/citizen-seed" || true

# Remove venv
rm -rf "$VENV_DIR" || true

# Remove system pip package if present
pip3 uninstall -y conrrad-citizen 2>/dev/null || true

echo -e "  ${GREEN}Clean slate ready.${NC}"

# ─────────────────────────────────────────────────
# PHASE 4: INSTALL SYSTEM DEPENDENCIES
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[4/6] Verifying system dependencies...${NC}"

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "  Installing Python3..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm python python-pip
    else
        echo -e "${RED}Cannot install Python3 automatically. Install it manually and retry.${NC}"
        exit 1
    fi
fi

if ! python3 -c "import venv" >/dev/null 2>&1; then
    echo -e "  Installing python3-venv..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq python3-venv
    else
        echo -e "${RED}Install python3-venv for your distribution and retry.${NC}"
        exit 1
    fi
fi

echo -e "  ${GREEN}Dependencies OK.${NC}"

# ─────────────────────────────────────────────────
# PHASE 5: FRESH INSTALL
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[5/6] Installing Citizen...${NC}"

# Create isolated environment
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet conrrad-citizen==0.3.2

# Create binary links
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/citizen" "$BIN_DIR/citizen"
ln -sf "$VENV_DIR/bin/citizen-seed" "$BIN_DIR/citizen-seed"

# Ensure PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    export PATH="$BIN_DIR:$PATH"
    PROFILE_FILE="$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && PROFILE_FILE="$HOME/.zshrc"
    if ! grep -q "$BIN_DIR" "$PROFILE_FILE" 2>/dev/null; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$PROFILE_FILE"
    fi
fi

echo -e "  ${GREEN}Citizen installed.${NC}"

# ─────────────────────────────────────────────────
# PHASE 6: BIRTH + START SERVICE
# ─────────────────────────────────────────────────
echo -e "${YELLOW}[6/6] Starting Citizen Birth...${NC}"

# Run birth
"$BIN_DIR/citizen" install

echo ""
echo -e "${CYAN}=================================================${NC}"
echo -e "${GREEN}  CITIZEN INSTALLATION COMPLETE                   ${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# Verify the birth worked
if [ -f "$CITIZEN_HOME/identity/SEALED" ]; then
    CITIZEN_ID=$(python3 -c "import json; print(json.load(open('$CITIZEN_HOME/identity/identity.json'))['citizen_id'])" 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${NC} Identity: ${CYAN}${CITIZEN_ID}${NC}"
else
    echo -e "  ${RED}✗${NC} Identity: FAILED"
fi

if [ -f "$CITIZEN_HOME/manifest/current.json" ]; then
    echo -e "  ${GREEN}✓${NC} Manifest: sealed"
else
    echo -e "  ${RED}✗${NC} Manifest: MISSING"
fi

# Start background service or inform user
HAS_SYSTEMD=false
if command -v systemctl >/dev/null 2>&1 && systemctl --user status >/dev/null 2>&1; then
    HAS_SYSTEMD=true
fi

if [ "$HAS_SYSTEMD" = true ]; then
    # systemd is available - service was installed by citizen install
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user restart "$SYSTEMD_SERVICE" 2>/dev/null || true
    sleep 2
    if systemctl --user is-active --quiet "$SYSTEMD_SERVICE" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Service: running on port ${PORT}"
        echo -e "  ${GREEN}✓${NC} Console: ${CYAN}http://127.0.0.1:${PORT}/${NC}"
    else
        echo -e "  ${YELLOW}!${NC} Service failed to start. Starting manually..."
        nohup "$BIN_DIR/citizen" serve --port $PORT > "$CITIZEN_HOME/serve.log" 2>&1 &
        sleep 1
        echo -e "  ${GREEN}✓${NC} Console: ${CYAN}http://127.0.0.1:${PORT}/${NC}"
    fi
else
    # No systemd (Docker, WSL1, etc.) - start in background
    echo -e "  ${YELLOW}!${NC} No systemd detected. Starting server directly..."
    nohup "$BIN_DIR/citizen" serve --port $PORT > "$CITIZEN_HOME/serve.log" 2>&1 &
    sleep 2
    echo -e "  ${GREEN}✓${NC} Console: ${CYAN}http://127.0.0.1:${PORT}/${NC}"
fi

echo -e "\n${YELLOW}[7/7] Triggering remote synchronization...${NC}"
"$BIN_DIR/citizen" sync

echo ""
echo -e "  Commands: ${CYAN}citizen status${NC}  |  ${CYAN}citizen serve --port ${PORT}${NC}  |  ${CYAN}citizen sync${NC}"
echo ""
