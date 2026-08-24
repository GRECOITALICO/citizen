#!/bin/bash
# CONRRAD Citizen — public Linux one-command installer.
# Trust reference: immutable tag citizen-managed-0.4.2.1 — not main.
#
# Host = infrastructure. Environment = runtime. Volume = life.
# INSTALL != SYNC. BIRTH != EVOLUTION.
set -euo pipefail

PACKAGE_VERSION="0.4.2.1"
RUNTIME_VERSION="0.4.2"
WHEEL_SHA256="fe8f06d10219655bd0ebf84a1f8a08c955d65fa22a76316c3887d29fcede51e9"
IMAGE_NAME="ghcr.io/grecoitalico/citizen"
IMAGE_TAG="0.4.2.1"
IMAGE_DIGEST="sha256:64df202d553c5aaff9cc0c74b01b8617e5877253778c9766d51dd59febd840da"
BOOTSTRAP_TAG="citizen-managed-0.4.2.1"

DATA_DIR="${CITIZEN_DATA_DIR:-$HOME/.local/share/conrrad-citizen}"
VOLUME="${CITIZEN_HOME:-$DATA_DIR/.citizen}"
BIN_DIR="${CITIZEN_BIN_DIR:-$HOME/.local/bin}"
HOST="${CITIZEN_UI_HOST:-127.0.0.1}"
PORT="${CITIZEN_UI_PORT:-3434}"
NAME="${CITIZEN_CONTAINER_NAME:-conrrad-citizen}"
STATE_FILE="$DATA_DIR/bootstrap-state.json"
OPEN_BROWSER="${CITIZEN_OPEN_BROWSER:-1}"
DIAGNOSTICS="${CITIZEN_DIAGNOSTICS:-0}"

if [ -n "${CITIZEN_IMAGE:-}" ]; then
  IMAGE_REF="$CITIZEN_IMAGE"
else
  IMAGE_REF="${IMAGE_NAME}@${IMAGE_DIGEST}"
fi

diag() {
  case "$DIAGNOSTICS" in
    1|true|TRUE|yes|YES) echo "$*" ;;
  esac
}

product() { echo "$*"; }

write_state() {
  mkdir -p "$DATA_DIR"
  local phase="$1"
  cat > "$STATE_FILE" <<EOF
{
  "phase": "$phase",
  "package_version": "$PACKAGE_VERSION",
  "runtime_version": "$RUNTIME_VERSION",
  "image": "$IMAGE_REF",
  "image_digest": "$IMAGE_DIGEST",
  "volume": "$VOLUME",
  "environment": "$NAME",
  "host": "$HOST",
  "port": "$PORT",
  "sync": false
}
EOF
}

fail_stop() {
  echo "$1" >&2
  write_state "failed"
  exit 1
}

user_action() {
  echo "USER_ACTION_REQUIRED: $1" >&2
  write_state "user_action_required"
  exit 2
}

engine=""

detect_engine() {
  if command -v podman >/dev/null 2>&1; then
    if podman info --format json >/dev/null 2>&1; then
      if podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null | grep -qi true; then
        engine="podman"
        return 0
      fi
    fi
  fi
  if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
      engine="docker"
      return 0
    fi
  fi
  engine=""
  return 1
}

provision_podman() {
  if detect_engine; then
    return 0
  fi
  if [ ! -f /etc/debian_version ]; then
    fail_stop "This installer prepares Linux isolation automatically on Debian-like hosts only."
  fi
  local pkgs="podman uidmap slirp4netns passt fuse-overlayfs crun"
  local apt=(env DEBIAN_FRONTEND=noninteractive apt-get)
  if command -v pkexec >/dev/null 2>&1; then
    pkexec "${apt[@]}" update >/dev/null
    pkexec "${apt[@]}" install -y --no-install-recommends $pkgs >/dev/null
  elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    sudo -n "${apt[@]}" update >/dev/null
    sudo -n "${apt[@]}" install -y --no-install-recommends $pkgs >/dev/null
  elif command -v sudo >/dev/null 2>&1; then
    sudo "${apt[@]}" update >/dev/null
    sudo "${apt[@]}" install -y --no-install-recommends $pkgs >/dev/null
  else
    fail_stop "Host isolation packages are missing and cannot be installed without authorization."
  fi
  hash -r 2>/dev/null || true
  if ! detect_engine; then
    fail_stop "Host isolation could not be prepared."
  fi
}

port_listener_pid() {
  if command -v ss >/dev/null 2>&1; then
    local text
    text="$(ss -ltnp "sport = :${PORT}" 2>/dev/null || true)"
    if echo "$text" | grep -q "pid="; then
      echo "$text" | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1
      return 0
    fi
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti "tcp:${PORT}" 2>/dev/null | head -n1 || true
    return 0
  fi
  return 0
}

port_free() {
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$HOST" "$PORT" <<'PY'
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
s = socket.socket()
s.settimeout(0.3)
try:
    raise SystemExit(0 if s.connect_ex((host, port)) != 0 else 1)
finally:
    s.close()
PY
    return $?
  fi
  ! ss -ltn "sport = :${PORT}" 2>/dev/null | grep -q LISTEN
}

our_pid() {
  "$engine" inspect --format '{{.State.Pid}}' "$NAME" 2>/dev/null || true
}

ensure_image() {
  local got=""
  if "$engine" image inspect --format '{{.Digest}}' "$IMAGE_REF" >/dev/null 2>&1; then
    got="$("$engine" image inspect --format '{{.Digest}}' "$IMAGE_REF" 2>/dev/null || true)"
    if [ -z "${CITIZEN_IMAGE:-}" ] && [ -n "$got" ] && [ "$got" != "$IMAGE_DIGEST" ]; then
      fail_stop "Image digest mismatch. Stopped. Citizen volume was not modified."
    fi
    if [ -n "$got" ]; then
      return 0
    fi
  fi
  if ! "$engine" pull "$IMAGE_REF" >/dev/null; then
    fail_stop "Image retrieval failed. Stopped. No Birth. Citizen volume was not modified."
  fi
  got="$("$engine" image inspect --format '{{.Digest}}' "$IMAGE_REF" 2>/dev/null || true)"
  if [ -z "${CITIZEN_IMAGE:-}" ] && [ "$got" != "$IMAGE_DIGEST" ]; then
    fail_stop "Image digest mismatch. Stopped. Citizen volume was not modified."
  fi
}

create_or_reuse_environment() {
  mkdir -p "$VOLUME"
  if "$engine" inspect "$NAME" >/dev/null 2>&1; then
    return 0
  fi
  local vol_opt="${VOLUME}:/citizen"
  if [ "$engine" = "podman" ]; then
    vol_opt="${VOLUME}:/citizen:Z"
  fi
  if ! "$engine" create \
      --name "$NAME" \
      --replace \
      --restart unless-stopped \
      --publish "${HOST}:${PORT}:3434" \
      --volume "$vol_opt" \
      --env CITIZEN_HOME=/citizen \
      --env CITIZEN_UI_HOST=0.0.0.0 \
      --env CITIZEN_UI_PORT=3434 \
      --env CITIZEN_OPEN_BROWSER=0 \
      "$IMAGE_REF" >/dev/null; then
    fail_stop "Could not create the Citizen environment. The Citizen volume was preserved."
  fi
}

wait_ready() {
  local i
  for i in $(seq 1 90); do
    if curl -fsS --max-time 1 "http://${HOST}:${PORT}/api/living" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  fail_stop "Citizen environment started but is not READY. The Citizen volume was preserved."
}

install_dispatcher() {
  mkdir -p "$BIN_DIR"
  cat > "$BIN_DIR/citizen" <<EOF
#!/bin/bash
exec ${engine} exec -i ${NAME} citizen "\$@"
EOF
  chmod +x "$BIN_DIR/citizen"
}

open_ui() {
  local url="http://${HOST}:${PORT}/"
  if [ "$OPEN_BROWSER" = "0" ]; then
    return 0
  fi
  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 || true
  fi
}

# docker create --replace is podman-specific; docker uses rm if exists
create_docker_safe() {
  mkdir -p "$VOLUME"
  if docker inspect "$NAME" >/dev/null 2>&1; then
    return 0
  fi
  if ! docker create \
      --name "$NAME" \
      --restart unless-stopped \
      --publish "${HOST}:${PORT}:3434" \
      --volume "${VOLUME}:/citizen" \
      --env CITIZEN_HOME=/citizen \
      --env CITIZEN_UI_HOST=0.0.0.0 \
      --env CITIZEN_UI_PORT=3434 \
      --env CITIZEN_OPEN_BROWSER=0 \
      "$IMAGE_REF" >/dev/null; then
    fail_stop "Could not create the Citizen environment. The Citizen volume was preserved."
  fi
}

product "CONRRAD Citizen"
write_state "started"

if [ "$(uname -s)" != "Linux" ]; then
  fail_stop "This public installer is Linux-only."
fi
if ! command -v curl >/dev/null 2>&1; then
  fail_stop "curl is required."
fi

product "Preparing host..."
write_state "infra"
provision_podman
diag "engine=${engine}"

if ! port_free; then
  pid="$(port_listener_pid || true)"
  ours="$(our_pid || true)"
  if [ -n "$pid" ] && [ -n "$ours" ] && [ "$pid" = "$ours" ]; then
    diag "port ${PORT} owned by this Citizen"
  elif [ -n "$ours" ] && [ "$ours" != "0" ] && [ "$ours" != "" ]; then
    diag "reusing running environment"
  else
    user_action "Port ${PORT} is in use by process ${pid:-unknown}, which is not this Citizen. Free the port. The process was not stopped."
  fi
fi

product "Preparing Citizen environment..."
write_state "image"
ensure_image
write_state "volume"
mkdir -p "$VOLUME"
write_state "environment"
if [ "$engine" = "docker" ]; then
  create_docker_safe
else
  create_or_reuse_environment
fi

product "Starting Citizen..."
if ! "$engine" start "$NAME" >/dev/null; then
  fail_stop "Could not start the Citizen environment. The Citizen volume was preserved."
fi
wait_ready
install_dispatcher
open_ui
write_state "ready"

product "READY"
product "Version: ${RUNTIME_VERSION}"
product "Open: http://${HOST}:${PORT}/"
product "UI: http://${HOST}:${PORT}/"
exit 0
