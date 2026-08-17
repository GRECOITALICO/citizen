#!/usr/bin/env python3
"""Windows CitizenSetup — installer logic (freeze with PyInstaller as CitizenSetup.exe)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path

def is_windows() -> bool:
    return sys.platform.startswith("win")

def install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "CONRRAD" / "Citizen"

def citizen_home() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / "CONRRAD" / "CitizenData"

def source_seed() -> Path:
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        cand = meipass / "citizen-seed"
        if cand.is_dir():
            return cand
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]

def nuclear_clean(dest: Path, home: Path) -> None:
    # Kill any python process on port 3434
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if "3434" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception:
        pass
        
    if dest.exists():
        try:
            shutil.rmtree(dest)
        except Exception:
            pass
    if home.exists():
        try:
            shutil.rmtree(home)
        except Exception:
            pass

def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        try:
            shutil.rmtree(dst)
        except Exception:
            pass
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(".citizen", "dist", "__pycache__", ".git", "*.pyc"),
    )

def write_autostart(seed: Path, home: Path) -> None:
    py = sys.executable
    bat = seed / "start_citizen.bat"
    bat.write_text(
        "@echo off\r\n"
        f'set CITIZEN_HOME={home}\r\n'
        "set CITIZEN_CLUSTER_ROOT_URL=https://conrrad.org\r\n"
        f"set PYTHONPATH={seed};{seed}\\runtime\r\n"
        f'cd /d "{seed}"\r\n'
        f'start "CitizenService" /MIN "{py}" -m citizen_seed serve --port 3434 --home "{home}"\r\n',
        encoding="utf-8",
    )
    run_cmd = f'"{bat}"'
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    )
    winreg.SetValueEx(key, "CONRRADCitizen", 0, winreg.REG_SZ, run_cmd)
    winreg.CloseKey(key)

def birth(seed: Path, home: Path) -> None:
    env = os.environ.copy()
    env["CITIZEN_HOME"] = str(home)
    env["CITIZEN_CLUSTER_ROOT_URL"] = "https://conrrad.org"
    env["PYTHONPATH"] = str(seed / "runtime") + os.pathsep + str(seed)
    home.mkdir(parents=True, exist_ok=True)
    for args in (["install"], ["boot"]):
        subprocess.run(
            [sys.executable, "-m", "citizen_seed", *args, "--home", str(home)],
            cwd=str(seed),
            env=env,
            check=False,
        )

def main() -> int:
    if not is_windows():
        print("CitizenSetup.exe targets Windows.")
        seed = source_seed()
        out = seed / "dist" / "CitizenSetup_payload"
        out.mkdir(parents=True, exist_ok=True)
        return 0

    seed_src = source_seed()
    dest = install_dir()
    home = citizen_home()
    nuclear_clean(dest, home)
    copy_tree(seed_src, dest)
    os.environ["PYTHONPATH"] = str(dest) + os.pathsep + str(dest / "runtime")
    birth(dest, home)
    write_autostart(dest, home)
    
    bat = dest / "start_citizen.bat"
    subprocess.Popen(["cmd", "/c", str(bat)], cwd=str(dest), creationflags=subprocess.CREATE_NO_WINDOW)
    
    # Open browser
    import time
    time.sleep(2)
    import webbrowser
    webbrowser.open("http://127.0.0.1:3434/")
    
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
