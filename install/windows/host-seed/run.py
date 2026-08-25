#!/usr/bin/env python3
"""Host-seed runner copied into CitizenHost. WSL, not the Citizen container."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for candidate in (HERE / "lib", HERE.parent.parent.parent / "src"):
    if candidate.is_dir():
        sys.path.insert(0, str(candidate))

from conrrad_citizen.host.seed_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
