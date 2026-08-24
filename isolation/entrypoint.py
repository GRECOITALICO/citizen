"""Environment entrypoint — runs INSIDE the managed Citizen environment.

Host adapters must not call this on the host as a substitute for isolation.
A fake backend may invoke boot_environment(..., serve=False) to simulate
in-environment Birth/boot during tests.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from conrrad_citizen.host.isolation.volume import volume_is_born
except ImportError:  # frozen 0.4.2.1 wheel has no isolation package
    def volume_is_born(root: Path) -> bool:
        root = Path(root)
        return (
            (root / "identity" / "SEALED").is_file()
            and (root / "identity" / "identity.json").is_file()
        )


def boot_environment(
    *,
    home: Path,
    serve: bool = False,
    host: str = "0.0.0.0",
    port: str | int = "3434",
) -> dict:
    """Birth only when the volume is unborn, then boot. Never Sync."""
    home = Path(home)
    os.environ["CITIZEN_HOME"] = str(home)
    born_before = volume_is_born(home)
    birth = False
    if not born_before:
        from citizen_seed.installer import BootstrapDisarmed, install

        try:
            install(home=home)
            birth = True
        except BootstrapDisarmed:
            birth = False

    from citizen_seed.runtime import BootError, boot

    try:
        boot(home=home)
        booted = True
        boot_error = ""
    except BootError as e:
        booted = False
        boot_error = str(e)

    result = {
        "home": str(home),
        "birth": birth,
        "born_before": born_before,
        "boot": booted,
        "boot_error": boot_error,
        "sync": False,
    }
    if not serve:
        return result

    from conrrad_citizen._ops import living_server as living_server

    living_server.main([
        "--home", str(home),
        "--host", str(host),
        "--port", str(port),
    ])
    return result


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    home = Path(os.environ.get("CITIZEN_HOME", "/citizen"))
    host = os.environ.get("CITIZEN_UI_HOST", "0.0.0.0")
    port = os.environ.get("CITIZEN_UI_PORT", "3434")
    boot_environment(home=home, serve=True, host=host, port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
