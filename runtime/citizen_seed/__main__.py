"""CLI: install | boot | update | status | project | serve | export-birth | destroy | lab-report"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .paths import citizen_home


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="citizen-seed", description="Citizen Seed Birth Lab")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_home(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--home",
            type=Path,
            default=None,
            help="CITIZEN_HOME (default ./.citizen or env)",
        )

    inst = sub.add_parser("install", help="Birth once — Installer then disappears")
    add_home(inst)
    bt = sub.add_parser("boot", help="Boot living Citizen")
    add_home(bt)
    up = sub.add_parser("update", help="One-click Sync / Evolution")
    add_home(up)
    up.add_argument("--updates", type=Path, default=None)
    st = sub.add_parser("status", help="Manifest / sync posture")
    add_home(st)
    pr = sub.add_parser("project", help="Re-project Assets")
    add_home(pr)
    sv = sub.add_parser("serve", help="Birth Observatory UI")
    add_home(sv)
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8787)

    ex = sub.add_parser("export-birth", help="Export Birth Package")
    add_home(ex)
    ex.add_argument("--dest", type=Path, default=None)

    dest = sub.add_parser("destroy", help="Destroy Citizen (export first by default)")
    add_home(dest)
    dest.add_argument("--no-export", action="store_true")

    lr = sub.add_parser("lab-report", help="Outside-LLM inventory evidence")
    add_home(lr)

    args = p.parse_args(argv)
    home = citizen_home(args.home)

    if args.cmd == "install":
        from .installer import install, BootstrapDisarmed

        try:
            result = install(home=home)
        except BootstrapDisarmed as e:
            print(
                json.dumps({"error": str(e), "hint": "use Sync / citizen-seed update"}, indent=2),
                file=sys.stderr,
            )
            return 2
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "boot":
        from .runtime import boot, BootError

        try:
            result = boot(home=home)
        except BootError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 0

    if args.cmd == "update":
        from .updater import one_click_update

        print(json.dumps(one_click_update(home=home, updates_dir=args.updates), indent=2))
        return 0

    if args.cmd == "status":
        from .updater import status

        print(json.dumps(status(home=home), indent=2))
        return 0

    if args.cmd == "project":
        from .crypto import load_publisher_secret
        from .assets import AssetLoader
        from .manifest import load_manifest
        from .paths import layout
        from .projection import ProjectionEngine

        paths = layout(home)
        secret = load_publisher_secret(paths["runtime"] / "publisher.secret")
        m = load_manifest(paths["manifest"] / "current.json")
        loader = AssetLoader(paths["assets"], secret)
        print(json.dumps(ProjectionEngine(loader, paths["projection"]).project(m), indent=2))
        return 0

    if args.cmd == "serve":
        from .ui_server import serve

        serve(home=home, host=args.host, port=args.port)
        return 0

    if args.cmd == "export-birth":
        from .birth_lab import export_birth_package

        print(json.dumps(export_birth_package(home=home, dest_dir=args.dest), indent=2))
        return 0

    if args.cmd == "destroy":
        from .birth_lab import destroy_citizen

        print(json.dumps(destroy_citizen(home=home, export_first=not args.no_export), indent=2))
        return 0

    if args.cmd == "lab-report":
        from .birth_lab import outside_llm_report

        print(json.dumps(outside_llm_report(home), indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
