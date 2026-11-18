"""Lista los monitores de Windows con su posición en el escritorio virtual.

    python -m tools.displays

Sirve para llenar config.toml -> [board] offset_x / offset_y: ahí es donde
hay que mover la ventana del proyector para que caiga en la pantalla extendida.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
try:
    user32.SetProcessDPIAware()
except Exception:
    pass

MONITORINFOF_PRIMARY = 0x1


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", ctypes.c_wchar * 32),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


MONITORENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(RECT),
    wintypes.LPARAM,
)


def _nombre_amigable(device: str) -> str:
    dd = DISPLAY_DEVICEW()
    dd.cb = ctypes.sizeof(DISPLAY_DEVICEW)
    if user32.EnumDisplayDevicesW(device, 0, ctypes.byref(dd), 0):
        return dd.DeviceString
    return ""


def monitores() -> list[dict]:
    salida: list[dict] = []

    def cb(hmon, hdc, lprect, lparam):
        mi = MONITORINFOEXW()
        mi.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            r = mi.rcMonitor
            salida.append(
                {
                    "device": mi.szDevice,
                    "nombre": _nombre_amigable(mi.szDevice),
                    "x": r.left,
                    "y": r.top,
                    "ancho": r.right - r.left,
                    "alto": r.bottom - r.top,
                    "primario": bool(mi.dwFlags & MONITORINFOF_PRIMARY),
                }
            )
        return 1

    user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return salida


def main() -> int:
    mons = monitores()
    print(f"{len(mons)} monitor(es):\n")
    for i, m in enumerate(mons):
        etiqueta = "PRIMARIO" if m["primario"] else "extendido"
        print(f"  [{i}] {m['device']}  {etiqueta}")
        print(f"       {m['ancho']}x{m['alto']} en posición x={m['x']} y={m['y']}")
        if m["nombre"]:
            print(f"       {m['nombre']}")
    secundarios = [m for m in mons if not m["primario"]]
    print()
    if not secundarios:
        print("Solo veo el monitor primario: el proyector no está conectado por HDMI")
        print("(o Windows está en modo duplicado en vez de extendido).")
        print("Win+P -> Extender, y vuelve a correr esto.")
        return 1
    # El proyector es 1080p; si hay varios monitores extendidos, ese es el candidato.
    candidatos = [m for m in secundarios if (m["ancho"], m["alto"]) == (1920, 1080)]
    elegido = candidatos[0] if candidatos else secundarios[0]
    if len(secundarios) > 1 or not candidatos:
        print("OJO: hay más de un monitor no primario (o ninguno es 1920x1080),")
        print("así que no puedo adivinar cuál es el proyector. Conéctalo por HDMI,")
        print("vuelve a correr esto y usa el monitor que aparezca nuevo.\n")
    print(f"Para config.toml -> [board]  (monitor {elegido['device']}):")
    print(f"  offset_x = {elegido['x']}")
    print(f"  offset_y = {elegido['y']}")
    print(f"  ancho = {elegido['ancho']}")
    print(f"  alto = {elegido['alto']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
