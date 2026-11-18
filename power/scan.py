"""Busca el proyector (Android TV remote v2) en la LAN por mDNS.

    python -m power.scan
    python -m power.scan --segundos 10
"""
from __future__ import annotations

import argparse
import socket
import time

SERVICIO = "_androidtvremote2._tcp.local."


def buscar(segundos: float = 6.0, servicio: str = SERVICIO) -> list[dict]:
    try:
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    except ImportError:
        raise SystemExit("Falta zeroconf. Instala: pip install -r requirements.txt")

    encontrados: dict[str, dict] = {}

    class Oyente(ServiceListener):
        def _ver(self, zc, tipo, nombre):
            info = zc.get_service_info(tipo, nombre, timeout=3000)
            if info is None:
                return
            ips = [socket.inet_ntoa(a) for a in info.addresses if len(a) == 4]
            props = {}
            for k, v in (info.properties or {}).items():
                clave = k.decode(errors="replace") if isinstance(k, bytes) else str(k)
                valor = v.decode(errors="replace") if isinstance(v, bytes) else v
                props[clave] = valor
            encontrados[nombre] = {
                "nombre": nombre.removesuffix("." + tipo),
                "ips": ips,
                "puerto": info.port,
                "props": props,
            }

        add_service = _ver
        update_service = _ver

        def remove_service(self, zc, tipo, nombre):
            pass

    zc = Zeroconf()
    try:
        ServiceBrowser(zc, servicio, Oyente())
        time.sleep(segundos)
    finally:
        zc.close()
    return list(encontrados.values())


def main() -> int:
    ap = argparse.ArgumentParser(description="Busca dispositivos Android TV en la LAN")
    ap.add_argument("--segundos", type=float, default=6.0)
    ap.add_argument("--servicio", default=SERVICIO)
    args = ap.parse_args()

    print(f"Buscando {args.servicio} durante {args.segundos:g}s ...")
    disp = buscar(args.segundos, args.servicio)
    if not disp:
        print("\nNo encontré nada.")
        print("- El proyector tiene que estar prendido (o en network standby) y en la misma red/VLAN.")
        print("- El WiFi de 2.4 vs 5 GHz a veces separa los dispositivos; prueba igual con `python -m power.cast scan`.")
        return 1
    print()
    for d in disp:
        modelo = d["props"].get("bt") or d["props"].get("md") or ""
        print(f"  {d['nombre']}")
        print(f"    ip     : {', '.join(d['ips']) or '?'}")
        print(f"    puerto : {d['puerto']}")
        if modelo:
            print(f"    props  : {d['props']}")
    print("\nCopia la IP a config.toml -> [proyector] ip = \"...\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
