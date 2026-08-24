#!/bin/bash
# Public Linux bootstrap for Citizen runtime package 0.4.2.1.
# Trust reference: immutable tag citizen-runtime-0.4.2.1 — not main.
set -euo pipefail

PACKAGE_VERSION="0.4.2.1"
RUNTIME_VERSION="0.4.2"
WHEEL_NAME="conrrad_citizen-${PACKAGE_VERSION}-py3-none-any.whl"
ARTIFACT_TAG="citizen-runtime-${PACKAGE_VERSION}"
WHEEL_URL="https://raw.githubusercontent.com/GRECOITALICO/citizen/${ARTIFACT_TAG}/release/${PACKAGE_VERSION}/${WHEEL_NAME}"
EXPECTED_SHA256="fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9"
SOURCE_COMMIT_EXPECTED="44246a3ffa9f789c40fe023a0d72a053dc08088b"

DATA_DIR="${CITIZEN_DATA_DIR:-$HOME/.local/share/conrrad-citizen}"
VENV_DIR="${CITIZEN_VENV_DIR:-$DATA_DIR/venv}"
BIN_DIR="${CITIZEN_BIN_DIR:-$HOME/.local/bin}"
export CITIZEN_HOME="${CITIZEN_HOME:-$DATA_DIR/.citizen}"
export CITIZEN_DATA_DIR="$DATA_DIR"
export CITIZEN_OPEN_BROWSER="${CITIZEN_OPEN_BROWSER:-0}"

echo "CONRRAD Citizen — Linux install"
echo "  package : ${PACKAGE_VERSION}"
echo "  runtime : ${RUNTIME_VERSION}"
echo "  tag     : ${ARTIFACT_TAG}"
echo "  contract: install = Birth/Resume; sync = Evolution (not this script)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required (3.11+)." >&2
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required." >&2
  exit 1
fi
if ! command -v sha256sum >/dev/null 2>&1; then
  echo "sha256sum is required." >&2
  exit 1
fi
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 2)' \
  || { echo "Python 3.11+ is required." >&2; exit 1; }
python3 -c 'import venv' >/dev/null 2>&1 \
  || { echo "python3 venv module is required." >&2; exit 1; }

if [ -d "$CITIZEN_HOME/identity" ]; then
  echo "Existing Citizen home detected; identity will be preserved (Resume, not rebirth)."
fi

mkdir -p "$DATA_DIR/artifact" "$BIN_DIR"
WHEEL_PATH="$DATA_DIR/artifact/${WHEEL_NAME}"

echo "Fetching ${WHEEL_NAME} from ${ARTIFACT_TAG}"
curl -fsS --max-redirs 0 -A "citizen-installer/${PACKAGE_VERSION}" -o "$WHEEL_PATH" "$WHEEL_URL"
GOT_SHA256="$(sha256sum "$WHEEL_PATH" | awk '{print $1}')"
if [ "$GOT_SHA256" != "$EXPECTED_SHA256" ]; then
  echo "Artifact SHA256 mismatch." >&2
  echo "  expected: ${EXPECTED_SHA256}" >&2
  echo "  got:      ${GOT_SHA256}" >&2
  rm -f "$WHEEL_PATH"
  exit 1
fi
echo "SHA256 verified."

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Preparing isolated venv at ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --no-cache-dir --no-input "$WHEEL_PATH"

INSTALLED_PACKAGE="$("$VENV_DIR/bin/python" -c "from importlib.metadata import version; print(version('conrrad-citizen'))")"
if [ "$INSTALLED_PACKAGE" != "$PACKAGE_VERSION" ]; then
  echo "Installed package ${INSTALLED_PACKAGE}; expected ${PACKAGE_VERSION}." >&2
  exit 1
fi
INSTALLED_RUNTIME="$("$VENV_DIR/bin/python" -c "import citizen_seed as cs; print(cs.RUNTIME_VERSION)")"
if [ "$INSTALLED_RUNTIME" != "$RUNTIME_VERSION" ]; then
  echo "Runtime ${INSTALLED_RUNTIME}; expected ${RUNTIME_VERSION}." >&2
  exit 1
fi
INSTALLED_COMMIT="$("$VENV_DIR/bin/python" -c "import citizen_seed as cs; print(getattr(cs,'SOURCE_COMMIT',''))")"
if [ "$INSTALLED_COMMIT" != "$SOURCE_COMMIT_EXPECTED" ]; then
  echo "SOURCE_COMMIT mismatch: ${INSTALLED_COMMIT} != ${SOURCE_COMMIT_EXPECTED}" >&2
  exit 1
fi

ln -sfn "$VENV_DIR/bin/citizen" "$BIN_DIR/citizen"
export PATH="$BIN_DIR:$PATH"
export CITIZEN_PYTHON="$VENV_DIR/bin/python"

echo "Running citizen install (Birth or Resume). This does not Sync."
"$VENV_DIR/bin/citizen" install

if [ ! -f "$CITIZEN_HOME/identity/SEALED" ]; then
  echo "Citizen identity was not sealed." >&2
  exit 1
fi

echo "Citizen READY path complete."
echo "  package : ${INSTALLED_PACKAGE}"
echo "  runtime : ${INSTALLED_RUNTIME}"
echo "  home    : ${CITIZEN_HOME}"
echo "  UI      : http://127.0.0.1:3434/"
echo "  next    : citizen status"
echo "Evolution is explicit: citizen sync"
