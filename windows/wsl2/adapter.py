"""Pure helpers for the Windows → WSL2 → Linux Citizen adapter.

No runtime side effects. Used by scripts and deterministic tests.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_DISTRO = "CONRRAD-Citizen"
DEFAULT_CITIZEN_HOME = "/home/citizen/.local/share/conrrad-citizen"
DEFAULT_UNIT = "citizen-seed-living.service"
DEFAULT_UI_HOST = "127.0.0.1"
DEFAULT_UI_PORT = 3434
WSL_CONF_PATH = "/etc/wsl.conf"
MARKER_DIR = "/home/citizen/.config/conrrad-citizen-wsl2"


@dataclass(frozen=True)
class WslConf:
    systemd: bool = True
    boot_command: str = ""

    def render(self) -> str:
        lines = ["[boot]", f"systemd={'true' if self.systemd else 'false'}"]
        if self.boot_command.strip():
            lines.append(f'command="{self.boot_command.strip()}"')
        return "\n".join(lines) + "\n"


def validate_ui_host(host: str) -> None:
    if host != "127.0.0.1":
        raise ValueError(f"Citizen UI must bind localhost only, got {host!r}")


def scheduled_task_action(*, distro: str = DEFAULT_DISTRO, unit: str = DEFAULT_UNIT) -> str:
    """Windows Scheduled Task action: start WSL, ensure user systemd unit."""
    distro_q = distro.replace('"', "")
    unit_q = unit.replace('"', "")
    return (
        f'wsl.exe -d "{distro_q}" --exec /bin/bash -lc '
        f'"systemctl --user start {unit_q} 2>/dev/null || true"'
    )


def launcher_command(*, distro: str = DEFAULT_DISTRO, url: str | None = None) -> str:
    host = DEFAULT_UI_HOST
    port = DEFAULT_UI_PORT
    validate_ui_host(host)
    target = url or f"http://{host}:{port}/"
    distro_q = distro.replace('"', "")
    return (
        f'wsl.exe -d "{distro_q}" --exec /bin/true && '
        f'powershell.exe -NoProfile -Command "Start-Process \\"{target}\\""'
    )


def wsl_setup_command(*, repo_linux_path: str, citizen_home: str = DEFAULT_CITIZEN_HOME) -> str:
    """Command run inside WSL to invoke bounded setup (idempotent)."""
    repo = repo_linux_path.replace('"', "")
    home = citizen_home.replace('"', "")
    return f'CITIZEN_HOME="{home}" bash "{repo}/windows/wsl2/setup.sh"'


def is_wsl2_proc_version(text: str) -> bool:
    return "microsoft" in text.lower() and "wsl2" in text.lower()


def is_systemd_pid1(status_text: str) -> bool:
    return bool(re.search(r"^/sbin/init\s+1\s", status_text, re.MULTILINE)) or bool(
        re.search(r"^systemd\s+1\s", status_text, re.MULTILINE)
    )


def marker_path(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return f"{MARKER_DIR}/{safe}.ok"
