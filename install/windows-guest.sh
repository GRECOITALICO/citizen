#!/bin/bash
# WSL guest: prepare isolation, then run the public Linux installer.
# Not a second Citizen lifecycle. Not a Windows runtime. Never Sync.
set -euo pipefail

LINUX_INSTALL_URL="${CITIZEN_LINUX_INSTALL_URL:-https://raw.githubusercontent.com/GRECOITALICO/citizen/citizen-managed-0.4.2.1/install.sh}"
IMAGE_NAME="${CITIZEN_IMAGE_NAME:-ghcr.io/grecoitalico/citizen}"
IMAGE_DIGEST="${CITIZEN_IMAGE_DIGEST:-sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da}"
VOLUME="${CITIZEN_HOME:?CITIZEN_HOME must be the persistent Citizen volume}"
DATA_DIR="${CITIZEN_DATA_DIR:-$(dirname "$VOLUME")}"
export CITIZEN_OPEN_BROWSER="${CITIZEN_OPEN_BROWSER:-0}"
export CITIZEN_HOME="$VOLUME"
export CITIZEN_DATA_DIR="$DATA_DIR"
export CITIZEN_IMAGE="${CITIZEN_IMAGE:-${IMAGE_NAME}@${IMAGE_DIGEST}}"

fail() { echo "$1" >&2; exit 1; }

if [ "$(uname -s)" != "Linux" ]; then
  fail "Guest bootstrap runs only inside the managed Linux environment."
fi

verify_public_image() {
  command -v podman >/dev/null 2>&1 || fail "The managed environment runtime could not be prepared. No Citizen was created."
  podman pull "$CITIZEN_IMAGE" >/dev/null
  got="$(podman image inspect --format '{{.Digest}}' "$CITIZEN_IMAGE" 2>/dev/null || true)"
  expected="$IMAGE_DIGEST"
  if [ -z "$got" ] || [ "$got" != "$expected" ]; then
    fail "The public Citizen image digest did not match. Local images were not used. No Citizen was created."
  fi
}

run_public_linux_install() {
  command -v curl >/dev/null 2>&1 || fail "curl is required inside the managed distro."
  mkdir -p "$VOLUME" "$DATA_DIR"
  if [ -f "$VOLUME/CitizenSetup.py" ]; then
    echo "UNKNOWN_LEGACY_INSTALLATION: volume was not migrated or overwritten." >&2
    exit 3
  fi
  verify_public_image
  curl -fsSL "$LINUX_INSTALL_URL" | bash
}

if [ "$(id -u)" -eq 0 ]; then
  if ! id -u citizen >/dev/null 2>&1; then
    useradd -m -s /bin/bash citizen
  fi
  grep -q '^citizen:' /etc/subuid 2>/dev/null || echo 'citizen:100000:65536' >> /etc/subuid
  grep -q '^citizen:' /etc/subgid 2>/dev/null || echo 'citizen:100000:65536' >> /etc/subgid
  mkdir -p "$VOLUME" "$DATA_DIR"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends \
    podman uidmap slirp4netns passt fuse-overlayfs crun curl ca-certificates python3
  printf 'CONRRAD-Citizen\n' > /etc/conrrad-citizen-managed
  grep -q 'CONRRAD-managed' /etc/wsl.conf 2>/dev/null || \
    printf '\n# CONRRAD-managed=CONRRAD-Citizen\n[user]\ndefault=citizen\n' >> /etc/wsl.conf
  chown -R citizen:citizen "$VOLUME" 2>/dev/null || true
  exec su -s /bin/bash citizen -c \
    "export CITIZEN_HOME='$VOLUME' CITIZEN_DATA_DIR='$DATA_DIR' CITIZEN_IMAGE='$CITIZEN_IMAGE' CITIZEN_OPEN_BROWSER=0 CITIZEN_LINUX_INSTALL_URL='$LINUX_INSTALL_URL' VOLUME='$VOLUME' DATA_DIR='$DATA_DIR' LINUX_INSTALL_URL='$LINUX_INSTALL_URL' IMAGE_DIGEST='$IMAGE_DIGEST'; $(declare -f fail verify_public_image run_public_linux_install); run_public_linux_install"
fi

run_public_linux_install
