"""Windows WSL2 EXE bootstrapper — orchestration tests (no Windows host required)."""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "windows" / "wsl2"))

import adapter  # noqa: E402


def test_bootstrapper_version_and_exe_name() -> None:
    assert adapter.BOOTSTRAPPER_VERSION.startswith("0.2.0")
    assert adapter.INSTALLER_BASENAME.endswith(".exe")
    assert "CitizenSetup" in adapter.INSTALLER_BASENAME


def test_required_bootstrapper_files_exist() -> None:
    for rel in adapter.required_bootstrapper_windows_files():
        assert (ROOT / rel).is_file(), rel


def test_bootstrapper_reuses_adapter_scripts() -> None:
    text = (ROOT / "windows" / "bootstrapper" / "Install-CitizenBootstrap.ps1").read_text()
    assert "Install-CitizenWsl2.ps1" in text
    assert "Register-CitizenAutoStart.ps1" in text
    assert "Launch-CitizenUI.ps1" in text
    assert "Detect-CitizenPrerequisites.ps1" in text
    assert "aws" not in text.lower() or "Assert-NoCloudToolsRequired" in text


def test_bootstrapper_does_not_call_cloud_clis() -> None:
    text = (ROOT / "windows" / "bootstrapper" / "Install-CitizenBootstrap.ps1").read_text().lower()
    for forbidden in ("aws.exe", "az.cmd", "az.exe", "gh.exe", "git.exe"):
        assert forbidden not in text
    assert "aws s3" not in text
    assert "git clone" not in text


def test_prereq_fail_closed_messages() -> None:
    text = (ROOT / "windows" / "bootstrapper" / "Detect-CitizenPrerequisites.ps1").read_text()
    assert "fail-closed" in text.lower() or "FAIL-CLOSED" in text
    assert "WSL1" in text
    assert "Nested" in text or "nested" in text
    assert "reboot" in text.lower()


def test_uninstall_refuses_unrelated_distros() -> None:
    text = (ROOT / "windows" / "bootstrapper" / "Uninstall-CitizenWsl2.ps1").read_text()
    for name in adapter.uninstall_must_not_touch():
        assert name in text
    assert "CONRRAD-Citizen" in text
    assert "RemoveCitizenDistro" in text


def test_nsi_is_exe_admin_and_localhost_not_public() -> None:
    nsi = (ROOT / "windows" / "bootstrapper" / "citizen-setup.nsi").read_text()
    assert "RequestExecutionLevel admin" in nsi
    assert "OutFile" in nsi
    assert "Install-CitizenBootstrap.ps1" in nsi
    launcher = (ROOT / "windows" / "Launch-CitizenUI.ps1").read_text()
    assert "127.0.0.1" in launcher


def test_no_secrets_in_bootstrapper_tree() -> None:
    forbidden = (".pem", ".pfx", "BEGIN PRIVATE")
    for path in (ROOT / "windows" / "bootstrapper").rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        lower = path.name.lower()
        assert not lower.endswith(".pem")
        assert not lower.endswith(".pfx")
        for token in forbidden:
            assert token.encode() not in data


def test_bootstrapper_builder_compiles() -> None:
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(ROOT / "scripts" / "build_windows_bootstrapper.py")],
        check=True,
    )


def test_payload_staged_on_linux_fs_not_mnt_c_home() -> None:
    text = (ROOT / "windows" / "bootstrapper" / "Install-CitizenBootstrap.ps1").read_text()
    assert adapter.DEFAULT_LINUX_INSTALL_ROOT in text
    assert "/mnt/c" not in text or "wslpath" in text
    assert adapter.DEFAULT_CITIZEN_HOME in text
