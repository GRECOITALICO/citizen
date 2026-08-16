#!/usr/bin/env bash
# Idempotent: ensure /etc/wsl.conf enables systemd (PID 1).
# Fail-closed. Does not restart WSL — operator may need: wsl --shutdown
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=defaults.env
source "${SCRIPT_DIR}/defaults.env"

MARKER="${HOME}/.config/conrrad-citizen-wsl2/systemd-configured.ok"
WSL_CONF="/etc/wsl.conf"
NEED_WRITE=0

if [[ ! -f "${WSL_CONF}" ]]; then
  NEED_WRITE=1
elif ! grep -Eq '^[[:space:]]*systemd[[:space:]]*=[[:space:]]*true' "${WSL_CONF}"; then
  NEED_WRITE=1
fi

if [[ "${NEED_WRITE}" -eq 0 ]]; then
  echo "OK: ${WSL_CONF} already has systemd=true"
  mkdir -p "$(dirname "${MARKER}")"
  date -u +"%Y-%m-%dT%H:%M:%SZ" > "${MARKER}"
  exit 0
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "FATAL: configure-systemd requires root inside WSL (sudo)" >&2
  exit 1
fi

TMP="$(mktemp)"
cat > "${TMP}" <<'EOF'
[boot]
systemd=true
EOF

if [[ -f "${WSL_CONF}" ]]; then
  # Preserve unrelated stanzas; replace or append [boot] systemd=
  python3 - <<'PY' "${WSL_CONF}" "${TMP}"
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
text = path.read_text(encoding="utf-8") if path.is_file() else ""
if re.search(r"^\[boot\]", text, re.M):
    if re.search(r"^systemd\s*=", text, re.M):
        text = re.sub(r"^systemd\s*=.*$", "systemd=true", text, flags=re.M)
    else:
        text = re.sub(r"(\[boot\][^\[]*)", r"\1systemd=true\n", text, count=1, flags=re.S)
else:
    text = (text.rstrip() + "\n\n[boot]\nsystemd=true\n").lstrip()
out.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
PY
  install -m 0644 "${TMP}" "${WSL_CONF}"
else
  install -m 0644 "${TMP}" "${WSL_CONF}"
fi
rm -f "${TMP}"

mkdir -p "$(dirname "${MARKER}")"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${MARKER}"
echo "OK: wrote systemd=true to ${WSL_CONF}"
echo "NOTE: run 'wsl --shutdown' from Windows, then reopen the distro for systemd PID 1."
