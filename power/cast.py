"""Cast al proyector por Chromecast, usando catt.

    python -m power.cast scan                       # lista dispositivos
    python -m power.cast site http://192.168.1.5:8000/morning.html
    python -m power.cast status
    python -m power.cast stop

El nombre del dispositivo sale de config.toml ([proyector] chromecast) o de --device.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys

from common.config import get


def _catt() -> list[str]:
    exe = shutil.which("catt")
    if exe:
        return [exe]
    return [sys.executable, "-m", "catt.cli"]


def _correr(argumentos: list[str]) -> int:
    cmd = _catt() + argumentos
    print("$ " + subprocess.list2cmdline(cmd), flush=True)
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        raise SystemExit("Falta catt. Instala: pip install -r requirements.txt")


def _device(args) -> list[str]:
    nombre = args.device or get("proyector.chromecast")
    if not nombre:
        raise SystemExit(
            "No sé el nombre del Chromecast.\n"
            "  1) python -m power.cast scan\n"
            '  2) ponlo en config.toml -> [proyector] chromecast = "..."'
        )
    return ["-d", str(nombre)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--device", help="nombre del Chromecast (default: config.toml)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")
    p_site = sub.add_parser("site")
    p_site.add_argument("url")
    sub.add_parser("status")
    sub.add_parser("stop")
    args = ap.parse_args()

    if args.cmd == "scan":
        rc = _correr(["scan"])
        print("\nCopia el nombre a config.toml -> [proyector] chromecast = \"...\"")
        return rc
    if args.cmd == "site":
        return _correr(_device(args) + ["cast_site", args.url])
    return _correr(_device(args) + [args.cmd])


if __name__ == "__main__":
    raise SystemExit(main())
