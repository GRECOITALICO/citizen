#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${CITIZEN_INSTALL_ROOT:-$HOME/.conrrad/citizen}"
HOME_DIR="${CITIZEN_HOME:-${BASE}/home}"
VERSION="$(tr -d '[:space:]' < "${ROOT}/VERSION")"
HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-3434}"
RELEASE="${BASE}/releases/${VERSION}"
[[ -d "${ROOT}/runtime/citizen_seed" ]] || { echo BIRTH_RUNTIME_MISSING >&2; exit 1; }
[[ -f "${ROOT}/ops/living_server.py" ]] || { echo BIRTH_CONSOLE_MISSING >&2; exit 1; }
[[ ! -e "${HOME_DIR}/identity/identity.json" ]] || { echo "CITIZEN_ALREADY_BORN:${HOME_DIR}" >&2; exit 2; }
mkdir -p "${BASE}/releases" "${HOME_DIR}"
rm -rf "${RELEASE}"
mkdir -p "${RELEASE}/runtime" "${RELEASE}/ops" "${RELEASE}/assets"
cp -a "${ROOT}/runtime/." "${RELEASE}/runtime/"
cp -a "${ROOT}/ops/living_server.py" "${RELEASE}/ops/living_server.py"
cp -a "${ROOT}/assets/genesis" "${RELEASE}/assets/genesis"
[[ ! -f "${ROOT}/assets/publisher.secret.example" ]] || cp -a "${ROOT}/assets/publisher.secret.example" "${RELEASE}/assets/publisher.secret.example"
printf '%s\n' "${VERSION}" > "${RELEASE}/VERSION"
export PYTHONPATH="${RELEASE}/runtime" CITIZEN_HOME="${HOME_DIR}" CITIZEN_UI_HOST="${HOST}" CITIZEN_UI_PORT="${PORT}" CITIZEN_OPEN_BROWSER=0 CITIZEN_INSTALL_ROOT="${BASE}" CITIZEN_RELEASE_VERSION="${VERSION}"
python3 -m citizen_seed install --home "${HOME_DIR}"
[[ -f "${HOME_DIR}/identity/identity.json" ]] || { echo BIRTH_IDENTITY_MISSING >&2; exit 1; }
[[ ! -f "${HOME_DIR}/runtime/publisher.secret" ]] || chmod 600 "${HOME_DIR}/runtime/publisher.secret"
python3 - <<'PY'
import os
from pathlib import Path
from citizen_seed.release_manager import activate
home = Path(os.environ['CITIZEN_HOME'])
release = home.parent / 'releases' / os.environ['CITIZEN_RELEASE_VERSION']
print(activate(home, release, os.environ['CITIZEN_RELEASE_VERSION']))
PY
"${ROOT}/scripts/install_service_linux.sh"
PYTHONPATH="${RELEASE}/runtime" CITIZEN_HOME="${HOME_DIR}" python3 -m citizen_seed boot --home "${HOME_DIR}"
mkdir -p "${HOME_DIR}/boot" "${HOME_DIR}/ops"
printf '{"version":"%s","localhost":"http://%s:%s/","release":"%s","installer":"gone"}\n' "${VERSION}" "${HOST}" "${PORT}" "${VERSION}" > "${HOME_DIR}/boot/BIRTH_COMPLETE.json"
chmod 600 "${HOME_DIR}/boot/BIRTH_COMPLETE.json"
rm -f -- "${BASH_SOURCE[0]}"
echo "CITIZEN_BIRTH_COMPLETE"
echo "Citizen: ${HOME_DIR}"
echo "UI: http://${HOST}:${PORT}/"
echo "Release: ${VERSION}"
echo "Installer: gone"
