"""Prueba de la webcam: listar cámaras y ver un preview.

    python -m board.camera list
    python -m board.camera preview            # usa config.toml [board] camara
    python -m board.camera preview --index 1

En el preview: ESC o q para salir, s para guardar un frame en logs/.
"""
from __future__ import annotations

import argparse

from common.config import DIR_LOGS, get


def _cv2():
    try:
        import cv2
    except ImportError:
        raise SystemExit(
            "Falta OpenCV. Instala: pip install opencv-contrib-python numpy"
        )
    return cv2


def _abrir(cv2, indice: int):
    """En Windows DSHOW abre más rápido y evita cámaras fantasma."""
    cam = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    if not cam.isOpened():
        cam.release()
        cam = cv2.VideoCapture(indice)
    return cam


def cmd_list(args) -> int:
    cv2 = _cv2()
    try:  # probar índices que no existen llena la consola de errores de OpenCV
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
    except Exception:
        pass
    encontradas = []
    for i in range(args.max):
        cam = _abrir(cv2, i)
        if cam.isOpened():
            ok, frame = cam.read()
            if ok and frame is not None:
                h, w = frame.shape[:2]
                encontradas.append((i, w, h))
                print(f"  [{i}] funciona — {w}x{h}")
            else:
                print(f"  [{i}] se abre pero no da imagen (¿en uso por otra app?)")
        cam.release()
    if not encontradas:
        print("No encontré ninguna cámara.")
        print("- ¿Está conectada? ¿Windows le dio permiso (Configuración > Privacidad > Cámara)?")
        return 1
    print(f"\nconfig.toml -> [board] camara = {encontradas[0][0]}")
    return 0


def cmd_preview(args) -> int:
    cv2 = _cv2()
    indice = args.index if args.index is not None else int(get("board.camara", 0))
    cam = _abrir(cv2, indice)
    if not cam.isOpened():
        raise SystemExit(f"No pude abrir la cámara {indice}. Prueba: python -m board.camera list")
    print(f"Cámara {indice} abierta. ESC o q para salir, s para guardar un frame.")
    ventana = f"camara {indice}"
    cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
    n = 0
    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("frame fallido")
                break
            cv2.imshow(ventana, frame)
            k = cv2.waitKey(1) & 0xFF
            if k in (27, ord("q")):
                break
            if k == ord("s"):
                DIR_LOGS.mkdir(exist_ok=True)
                ruta = DIR_LOGS / f"camara{indice}_{n:03d}.png"
                cv2.imwrite(str(ruta), frame)
                print(f"guardado {ruta}")
                n += 1
    finally:
        cam.release()
        cv2.destroyAllWindows()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_list = sub.add_parser("list")
    p_list.add_argument("--max", type=int, default=5, help="índices a probar (default 5)")
    p_list.set_defaults(fn=cmd_list)
    p_prev = sub.add_parser("preview")
    p_prev.add_argument("--index", type=int, default=None)
    p_prev.set_defaults(fn=cmd_preview)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
