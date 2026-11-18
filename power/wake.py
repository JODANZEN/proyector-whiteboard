"""Control del proyector por el protocolo Android TV Remote v2.

    python -m power.wake pair            # emparejar (sale un PIN en la pared)
    python -m power.wake status          # ¿está prendido? + info del dispositivo
    python -m power.wake wake            # manda WAKEUP
    python -m power.wake power           # manda POWER (toggle) — respaldo
    python -m power.wake hdmi 1          # cambia a la entrada HDMI 1
    python -m power.wake key HOME        # cualquier keycode

La IP sale de config.toml ([proyector] ip) o de --ip.
El certificado del emparejamiento se guarda en secrets/ (gitignored).
"""
from __future__ import annotations

import argparse
import asyncio
import inspect

from common.config import DIR_SECRETS, get

TIMEOUT = 15.0


def _clases():
    try:
        from androidtvremote2 import (
            AndroidTVRemote,
            CannotConnect,
            ConnectionClosed,
            InvalidAuth,
        )
    except ImportError:
        raise SystemExit(
            "Falta androidtvremote2. Instala: pip install -r requirements.txt"
        )
    return AndroidTVRemote, CannotConnect, ConnectionClosed, InvalidAuth


def _ip(args) -> str:
    ip = args.ip or get("proyector.ip")
    if not ip:
        raise SystemExit(
            "No sé la IP del proyector.\n"
            "  1) python -m power.scan\n"
            '  2) ponla en config.toml -> [proyector] ip = "192.168.x.x"'
        )
    return str(ip)


def _remote(ip: str):
    AndroidTVRemote, *_ = _clases()
    DIR_SECRETS.mkdir(exist_ok=True)
    return AndroidTVRemote(
        client_name=str(get("proyector.nombre_cliente", "proyector-pc")),
        certfile=str(DIR_SECRETS / "cert.pem"),
        keyfile=str(DIR_SECRETS / "key.pem"),
        host=ip,
    )


async def _conectar(ip: str):
    """Conecta con un certificado ya emparejado. Devuelve el remote conectado."""
    _, CannotConnect, _, InvalidAuth = _clases()
    r = _remote(ip)
    if await r.async_generate_cert_if_missing():
        raise SystemExit(
            "No hay certificado todavía. Empareja primero:\n"
            "  python -m power.wake pair"
        )
    try:
        await asyncio.wait_for(r.async_connect(), TIMEOUT)
    except InvalidAuth:
        raise SystemExit(
            "El proyector rechazó el certificado.\n"
            "Borra la carpeta secrets/ y vuelve a correr: python -m power.wake pair"
        )
    except (CannotConnect, OSError, asyncio.TimeoutError) as e:
        raise SystemExit(
            f"No pude conectar con {ip} ({type(e).__name__}: {e}).\n"
            "- ¿El proyector está prendido o en network standby?\n"
            "- Verifica la IP: python -m power.scan"
        )
    return r


async def _enviar(r, tecla: str, direccion: str = "SHORT") -> None:
    fn = getattr(r, "send_key_command", None) or getattr(r, "async_send_key_command")
    res = fn(tecla, direccion)
    if inspect.isawaitable(res):
        await res


def _estado(r) -> str:
    on = getattr(r, "is_on", None)
    return {True: "PRENDIDO", False: "APAGADO/standby"}.get(on, f"desconocido ({on!r})")


async def cmd_pair(args) -> int:
    ip = _ip(args)
    r = _remote(ip)
    nuevo = await r.async_generate_cert_if_missing()
    if not nuevo:
        print("Ya había un certificado en secrets/ — intento emparejar de nuevo.")
    print(f"Emparejando con {ip} ... mira la pared, debe salir un PIN de 6 dígitos.")
    await r.async_start_pairing()
    pin = input("PIN: ").strip()
    await r.async_finish_pairing(pin)
    print("Emparejado. Certificado en secrets/cert.pem")
    print("Ahora prueba: python -m power.wake status")
    return 0


async def cmd_status(args) -> int:
    r = await _conectar(_ip(args))
    try:
        print(f"estado    : {_estado(r)}")
        info = getattr(r, "device_info", None)
        if info:
            print(f"dispositivo: {info}")
        app = getattr(r, "current_app", None)
        if app:
            print(f"app actual : {app}")
    finally:
        r.disconnect()
    return 0


async def _pulsar(args, tecla: str) -> int:
    r = await _conectar(_ip(args))
    try:
        antes = _estado(r)
        print(f"estado antes: {antes}")
        print(f"mandando {tecla} ...")
        await _enviar(r, tecla)
        await asyncio.sleep(args.espera)
        print(f"estado después: {_estado(r)}")
    finally:
        r.disconnect()
    return 0


async def cmd_wake(args) -> int:
    return await _pulsar(args, "WAKEUP")


async def cmd_power(args) -> int:
    return await _pulsar(args, "POWER")


async def cmd_hdmi(args) -> int:
    return await _pulsar(args, f"TV_INPUT_HDMI_{args.n}")


async def cmd_key(args) -> int:
    return await _pulsar(args, args.keycode.upper())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ip", help="IP del proyector (default: config.toml)")
    ap.add_argument(
        "--espera",
        type=float,
        default=4.0,
        help="segundos a esperar antes de releer el estado (default 4)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pair").set_defaults(fn=cmd_pair)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("wake").set_defaults(fn=cmd_wake)
    sub.add_parser("power").set_defaults(fn=cmd_power)
    p_hdmi = sub.add_parser("hdmi")
    p_hdmi.add_argument("n", nargs="?", default="1")
    p_hdmi.set_defaults(fn=cmd_hdmi)
    p_key = sub.add_parser("key")
    p_key.add_argument("keycode")
    p_key.set_defaults(fn=cmd_key)

    args = ap.parse_args()
    try:
        return asyncio.run(args.fn(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
