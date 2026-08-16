"""Deterministic tests for Windows → WSL2 adapter (no Windows runtime required)."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "windows" / "wsl2"))

import adapter  # noqa: E402


def test_wsl_conf_generation():
    text = adapter.WslConf(systemd=True).render()
    assert "[boot]" in text
    assert "systemd=true" in text


def test_wsl_conf_idempotent_marker_path():
    p = adapter.marker_path("systemd-configured")
    assert p.startswith(adapter.MARKER_DIR)


def test_scheduled_task_action_uses_wsl_and_systemctl():
    cmd = adapter.scheduled_task_action()
    assert "wsl.exe" in cmd
    assert "systemctl --user start" in cmd
    assert adapter.DEFAULT_UNIT in cmd


def test_launcher_localhost_only():
    cmd = adapter.launcher_command()
    assert "127.0.0.1" in cmd
    assert "3434" in cmd
    with pytest.raises(ValueError):
        adapter.validate_ui_host("0.0.0.0")


def test_wsl_setup_command_points_at_setup_sh():
    cmd = adapter.wsl_setup_command(repo_linux_path="/home/citizen/citizen-wsl2")
    assert "windows/wsl2/setup.sh" in cmd
    assert adapter.DEFAULT_CITIZEN_HOME in cmd


def test_invalid_environment_detection_wsl2():
    assert adapter.is_wsl2_proc_version("Linux version ... microsoft ... WSL2 ...")
    assert not adapter.is_wsl2_proc_version("Linux version 6.1.0-generic")


def test_systemd_pid1_detection():
    assert adapter.is_systemd_pid1("systemd         1  ...")
    assert adapter.is_systemd_pid1("/sbin/init      1  ...")
    assert not adapter.is_systemd_pid1("init            1  ...")


def test_defaults_env_rejects_mnt_c_in_verify_script():
    script = (ROOT / "windows" / "wsl2" / "verify-environment.sh").read_text()
    assert "/mnt/" in script
    assert "FATAL" in script


def test_configure_systemd_idempotent_marker():
    script = (ROOT / "windows" / "wsl2" / "configure-systemd.sh").read_text()
    assert "already has systemd=true" in script
    assert "NEED_WRITE" in script


def test_setup_reuses_linux_service_installer():
    script = (ROOT / "windows" / "wsl2" / "setup.sh").read_text()
    assert "install_service_linux.sh" in script
    assert "citizen_seed install" in script or "citizen_seed boot" in script


def test_ps1_autostart_idempotent():
    ps1 = (ROOT / "windows" / "Register-CitizenAutoStart.ps1").read_text()
    assert "already exists" in ps1
    assert "Get-ScheduledTask" in ps1


def test_ps1_launcher_localhost_guard():
    ps1 = (ROOT / "windows" / "Launch-CitizenUI.ps1").read_text()
    assert "127.0.0.1" in ps1
    assert "localhost only" in ps1.lower() or "127.0.0.1" in ps1


def test_no_core_modules_modified():
    """Adapter must not touch release verifier / sync core."""
    touched = list((ROOT / "windows").rglob("*")) + list((ROOT / "docs" / "windows").rglob("*"))
    paths = {p for p in touched if p.is_file()}
    forbidden = {"release_contract.py", "release_verifier.py", "living_server.py"}
    for p in paths:
        assert p.name not in forbidden


def test_adapter_py_compile():
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(ROOT / "windows" / "wsl2" / "adapter.py")],
        check=True,
    )


def test_windows_runtime_untested_marker():
    """Document that real Windows execution is UNTESTED in this mission."""
    readme = (ROOT / "windows" / "README.md").read_text()
    assert "UNTESTED" in readme
