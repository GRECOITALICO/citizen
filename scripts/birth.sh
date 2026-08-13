#!/usr/bin/env bash
# CONRRAD Citizen BIRTH: install a self-contained Citizen, then remove this installer.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${CITIZEN_INSTALL_ROOT:-$HOME/.conrrad/citizen}"
HOME_DIR="${CITIZEN_HOME:-${BASE}/home}"
VERSION="$(tr -d '[:space:]' < "${ROOT}/VERSION")"
HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-3434}"
RELEASE="${BASE}/releases/${VERSION}"

[[ -d "${ROOT}/runtime/citizen_seed" ]] || { echo "BIRTH_RUNTIME_MISSING" >&2; exit 1; }
[[ -f "${ROOT}/ops/living_server.py" ]] || { echo "BIRTH_CONSOLE_MISSING" >&2; exit 1; }
[[ ! -e "${BASE}/home/identity/identity.json" ]] || { echo "CITIZEN_ALREADY_BORN:${HOME_DIR}" >&2; exit 2; }

mkdir -p "${BASE}/releases" "${HOME_DIR}"
rm -rf "${RELEASE}"
mkdir -p "${RELEASE}/runtime" "${RELEASE}/ops" "${RELEASE}/assets"

# Copy executable runtime only. Never make the checkout the runtime dependency.
cp -a "${ROOT}/runtime/." "${RELEASE}/runtime/"
cp -a "${ROOT}/ops/living_server.py" "${RELEASE}/ops/living_server.py"
cp -a "${ROOT}/assets/genesis" "${RELEASE}/assets/genesis"
if [[ -f "${ROOT}/assets/publisher.secret.example" ]]; then
  cp -a "${ROOT}/assets/publisher.secret.example" "${RELEASE}/assets/publisher.secret.example"
fi
printf '%s\n' "${VERSION}" > "${RELEASE}/VERSION"

# Runtime memory is deliberately outside releases.
export PYTHONPATH="${RELEASE}/runtime"
export CITIZEN_HOME="${HOME_DIR}"
export CITIZEN_UI_HOST="${HOST}"
export CITIZEN_UI_PORT="${PORT}"
export CITIZEN_OPEN_BROWSER=0

python3 -m citizen_seed install --home "${HOME_DIR}"

# Keep the publisher material in the Citizen's private home, never in the checkout.
if [[ -f "${HOME_DIR}/runtime/publisher.secret" ]]; then
  chmod 600 "${HOME_DIR}/runtime/publisher.secret"
fi

python3 -m citizen_seed boot --home "${HOME_DIR}"

# Register the active release before the service starts.
python3 - <<'PY'
from pathlib import Path
from citizen_seed.release_manager import activate
home = Path(__import__('os').environ['CITIZEN_HOME'])
release = home.parent / 'releases' / Path(__import__('os').environ['VERSION']).read_text().strip() if False else None
PY

# Service points only to ~/.conrrad/citizen/current; the checkout is no longer needed.
export CITIZEN_INSTALL_ROOT="${BASE}"
export CITIZEN_HOME="${HOME_DIR}"
export CITIZEN_UI_HOST="${HOST}"
export CITIZEN_UI_PORT="${PORT}"
"${ROOT}/scripts/install_service_linux.sh"

# Activate after the release has passed boot validation.
PYTHONPATH="${RELEASE}/runtime" CITIZEN_HOME="${HOME_DIR}" python3 - <<'PY'
import os
from pathlib import Path
from citizen_seed.release_manager import activate
home = Path(os.environ['CITIZEN_HOME'])
release = home.parent / 'releases' / Path(os.environ['VERSION']).read_text().strip() if False else None
# VERSION is supplied by the shell below through the environment.
release = home.parent / 'releases' / os.environ['CITIZEN_RELEASE_VERSION']
print(activate(home, release, os.environ['CITIZEN_RELEASE_VERSION']))
PY

# Reinstall/restart service now that current exists.
"${ROOT}/scripts/install_service_linux.sh"

mkdir -p "${HOME_DIR}/boot" "${HOME_DIR}/ops"
cat > "${HOME_DIR}/boot/BIRTH_COMPLETE.json" <<EOF
{"version":"${VERSION}","localhost":"http://${HOST}:${PORT}/","release":"${VERSION}","installer":"gone"}
EOF
chmod 600 "${HOME_DIR}/boot/BIRTH_COMPLETE.json"

# The installer destroys itself. No post-install dependency on this checkout remains.
rm -f -- "${BASH_SOURCE[0]}"
echo "CITIZEN_BIRTH_COMPLETE"
echo "Citizen: ${HOME_DIR}"
echo "UI: http://${HOST}:${PORT}/"
echo "Release: ${VERSION}"
echo "Installer: gone"
