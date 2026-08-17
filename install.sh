#!/bin/bash
# Citizen Seed — Linux Native Installer
# This installer completely abstracts Python environment nuances (PEP 668)
# and seamlessly bootstraps the Citizen runtime without requiring user friction.

set -e

# ANSI colors for UI
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=================================================${NC}"
echo -e "${CYAN}    CITIZEN NATIVE INSTALLER (LINUX)             ${NC}"
echo -e "${CYAN}=================================================${NC}"
echo ""

# 1. Dependency Check
echo -e "-> Checking system dependencies..."
if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Python3 is not installed. Attempting automatic installation...${NC}"
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    else
        echo -e "${RED}Unsupported package manager. Please install Python3 manually.${NC}"
        exit 1
    fi
fi

# Debian/Ubuntu specifically strips venv from the core python package
if ! python3 -c "import venv" >/dev/null 2>&1; then
    echo -e "-> Installing python3-venv (Required for isolated environments)..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3-venv
    else
        echo -e "${RED}Please install the python3-venv package manually for your distribution.${NC}"
        exit 1
    fi
fi

# 2. Virtual Environment Setup (Frictionless isolation to avoid PEP 668)
VENV_DIR="$HOME/.citizen-env"
echo -e "-> Creating dedicated biological environment at ${CYAN}$VENV_DIR${NC}..."
python3 -m venv "$VENV_DIR"

# 3. Installation
echo -e "-> Downloading and installing Citizen core..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet --upgrade conrrad-citizen

# 4. PATH integration
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/citizen" "$BIN_DIR/citizen"
ln -sf "$VENV_DIR/bin/citizen-seed" "$BIN_DIR/citizen-seed"

# Ensure ~/.local/bin is in PATH for the current session
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    export PATH="$BIN_DIR:$PATH"
    echo -e "-> Appending $BIN_DIR to PATH for this session."
    
    # Attempt to permanently add to PATH if missing
    PROFILE_FILE="$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        PROFILE_FILE="$HOME/.zshrc"
    fi
    if ! grep -q "$BIN_DIR" "$PROFILE_FILE"; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$PROFILE_FILE"
        echo -e "-> Added $BIN_DIR to $PROFILE_FILE."
    fi
fi

echo -e "-> Environment ready."
echo ""

# 5. Bootstrapping
echo -e "${GREEN}Starting Citizen Birth sequence...${NC}"
citizen install

echo -e "${CYAN}=================================================${NC}"
echo -e "${GREEN}Citizen has been successfully installed and awakened.${NC}"
echo -e "${CYAN}=================================================${NC}"
echo -e "You can now check the status at any time by typing: ${CYAN}citizen status${NC}"
