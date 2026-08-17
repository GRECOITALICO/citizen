import os
import sys
import subprocess
from pathlib import Path

class SystemdManager:
    @staticmethod
    def install_user_service():
        if sys.platform != "linux":
            return
        
        executable = sys.executable
        
        service_content = f"""[Unit]
Description=Citizen Seed Living Runtime
After=network.target

[Service]
Type=simple
ExecStart={executable} -m citizen_seed serve --port 3434
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""
        
        systemd_dir = Path.home() / ".config" / "systemd" / "user"
        systemd_dir.mkdir(parents=True, exist_ok=True)
        
        service_path = systemd_dir / "citizen-seed-living.service"
        service_path.write_text(service_content, encoding="utf-8")
        
        try:
            subprocess.run(["systemctl", "--user", "stop", "citizen-seed-living"], capture_output=True)
            subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", "citizen-seed-living"], capture_output=True)
        except FileNotFoundError:
            pass

    @staticmethod
    def uninstall_user_service():
        if sys.platform != "linux":
            return
        
        try:
            subprocess.run(["systemctl", "--user", "stop", "citizen-seed-living"], capture_output=True)
            subprocess.run(["systemctl", "--user", "disable", "citizen-seed-living"], capture_output=True)
        except FileNotFoundError:
            pass
            
        service_path = Path.home() / ".config" / "systemd" / "user" / "citizen-seed-living.service"
        if service_path.exists():
            service_path.unlink()
            try:
                subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
            except FileNotFoundError:
                pass
