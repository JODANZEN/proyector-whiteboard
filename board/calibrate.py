"""Fase 3 - calibracion camara -> proyector con 4 marcadores ArUco.

Proyecta 4 marcadores, los detecta con la webcam, calcula la homografia que
convierte pixeles de camara en pixeles del proyector, y la guarda en cam2proj.npy.

    python -m board.calibrate                # calibrar y guardar
    python -m board.calibrate --test         # reusar cam2proj.npy y solo probar
    python -m board.calibrate --autotest     # validar la matematica sin hardware
    python -m board.calibrate --guardar      # ademas guarda las fotos en logs/

Prueba: en la ventana "camara" haz click sobre un punto de la pared; debe
aparecer un circulo rojo proyectado en ese mismo punto. ESC sale, c limpia.

Todo sale de config.toml ([board]), no de constantes.
"""
from __future__ import annotations

import argparse

import numpy as np

from common.config import DIR_LOGS, get, raiz

RUTA_H = raiz() / "cam2proj.npy"
VENTANA_PROY = "proyector"
VENTANA_CAM = "camara"


def _cv2():
    try:
        import cv2
    except ImportError:
        raise SystemExit("Falta OpenCV. Instala: pip install -r requirements.txt")
    return cv2


# --------------------------------------------------------------------------- #
# geometria de los marcadores
# --------------------------------------------------------------------------- #
def posiciones(ancho: int, alto: int, s: int, m: int) -> dict[int, tuple[int, int]]:
    """Esquina superior-izquierda de cada marcador, en px del proyector."""
    return {
        0: (m, m),
        1: (ancho - m - s, m),
        2: (ancho - m - s, alto - m - s),
        3: (m, alto - m - s),
    }


def esquinas_proyector(x: int, y: int, s: int) -> list[list[int]]:
    """En el mismo orden que devuelve detectMarkers: TL, TR, BR, BL."""
    return [[x, y], [x + s, y], [x + s, y + s], [x, y + s]]


def lienzo(cv2, ancho: int, alto: int, s: int, m: int) -> np.ndarray:
    aruco = cv2.aruco
    dic = diccionario(cv2)
    img = np.full((alto, ancho), 255, np.uint8)
    for i, (x, y) in posiciones(ancho, alto, s, m).items():
        img[y : y + s, x : x + s] = aruco.generateImageMarker(dic, i, s)
    return img


def diccionario(cv2):
    return cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)


# --------------------------------------------------------------------------- #
# homografia
# --------------------------------------------------------------------------- #
def homografia(cv2, detectados: dict[int, np.ndarray], ancho, alto, s, m):
    """detectados: {id: array (4,2) con las esquinas en px de camara}.

    Devuelve (H, error_medio, error_max), errores en px del proyector.
    """
    pos = posiciones(ancho, alto, s, m)
    src, dst = [], []
    for i in sorted(detectados):
        if i not in pos:
            continue
        src.extend(np.asarray(detectados[i], dtype=np.float32).tolist())
        x, y = pos[i]
        dst.extend(esquinas_proyector(x, y, s))
    if len(src) < 4:
        raise SystemExit(f"Solo tengo {len(src)} puntos; necesito al menos 4.")

    src_a = np.float32(src)
    dst_a = np.float32(dst)
    H, _ = cv2.findHomography(src_a, dst_a, cv2.RANSAC, 3.0)
    if H is None:
        raise SystemExit("findHomography fallo: los marcadores quedaron casi en linea.")
    proy = cv2.perspectiveTransform(src_a.reshape(-1, 1, 2), H).reshape(-1, 2)
    err = np.linalg.norm(proy - dst_a, axis=1)
    return H, float(err.mean()), float(err.max())


# --------------------------------------------------------------------------- #
# ventanas
# --------------------------------------------------------------------------- #
def offset_proyector(ancho: int, alto: int) -> tuple[int, int, str]:
    """Busca en Windows el monitor que mide ancho x alto y no es el primario.

    Vuelve al offset de config.toml si no lo encuentra. El offset guardado no es
    confiable: Windows reacomoda las coordenadas cuando el proyector se apaga.
    """
    try:
        from tools.displays import monitores

        for mon in monitores():
            if (mon["ancho"], mon["alto"]) == (ancho, alto) and not mon["primario"]:
                return mon["x"], mon["y"], f"detectado ({mon['device']})"
    except Exception as e:  # noqa: BLE001
        print(f"  (no pude leer los monitores: {type(e).__name__}: {e})")
    return int(get("board.offset_x", 0)), int(get("board.offset_y", 0)), "de config.toml"


def abrir_ventana_proyector(cv2, ancho: int, alto: int) -> None:
    x, y, origen = offset_proyector(ancho, alto)
    print(f"  ventana del proyector en x={x} y={y} ({origen})")
    if origen.startswith("de config"):
        print("  OJO: no encontre un monitor de "
              f"{ancho}x{alto}. Si no ves los marcadores en la pared,")
        print("       conecta el proyector por HDMI como pantalla extendida y corre:")
        print("       python -m tools.displays")
    cv2.namedWindow(VENTANA_PROY, cv2.WINDOW_NORMAL)
    cv2.moveWindow(VENTANA_PROY, x, y)
    cv2.setWindowProperty(VENTANA_PROY, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


def abrir_camara(cv2, indice: int):
    cam = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    if not cam.isOpened():
        cam.release()
        cam = cv2.VideoCapture(indice)
    if not cam.isOpened():
        raise SystemExit(
            f"No pude abrir la camara {indice}. Prueba: python -m board.camera list"
        )
    cw = int(get("board.cam_ancho", 0) or 0)
    ch = int(get("board.cam_alto", 0) or 0)
    if cw and ch:
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, cw)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, ch)
    real_w = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
    real_h = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"  camara {indice} a {real_w}x{real_h}")
    return cam


# --------------------------------------------------------------------------- #
# calibracion
# --------------------------------------------------------------------------- #
def capturar_marcadores(cv2, cam, frames: int, guardar: bool) -> dict[int, np.ndarray]:
    """Promedia las esquinas de cada marcador en varios frames."""
    det = cv2.aruco.ArucoDetector(diccionario(cv2))
    acum: dict[int, list[np.ndarray]] = {}
    ultimo = None
    for _ in range(frames):
        ok, frame = cam.read()
        if not ok:
            continue
        ultimo = frame
        esquinas, ids, _ = det.detectMarkers(frame)
        if ids is None:
            continue
        for c, i in zip(esquinas, ids.flatten()):
            acum.setdefault(int(i), []).append(c[0])
    if ultimo is None:
        raise SystemExit("La camara no dio ni un frame.")

    promedio = {
        i: np.mean(np.stack(lista), axis=0)
        for i, lista in acum.items()
        if len(lista) >= 2
    }
    print(f"  marcadores detectados: {sorted(promedio)} de [0, 1, 2, 3]")
    for i in sorted(acum):
        print(f"    id {i}: visto en {len(acum[i])}/{frames} frames")

    if guardar:
        DIR_LOGS.mkdir(exist_ok=True)
        anotado = ultimo.copy()
        esquinas, ids, _ = det.detectMarkers(ultimo)
        if ids is not None:
            cv2.aruco.drawDetectedMarkers(anotado, esquinas, ids)
        ruta = DIR_LOGS / "calib_camara.png"
        cv2.imwrite(str(ruta), anotado)
        print(f"  foto de la camara guardada en {ruta}")
    return promedio


def calibrar(cv2, args) -> np.ndarray:
    ancho = int(get("board.ancho", 1920))
    alto = int(get("board.alto", 1080))
    s = int(get("board.marcador_tam", 220))
    m = int(get("board.marcador_margen", 80))
    indice = int(get("board.camara", 0))

    print(f"Proyector {ancho}x{alto}, marcadores de {s}px con margen {m}px")
    abrir_ventana_proyector(cv2, ancho, alto)
    cv2.imshow(VENTANA_PROY, lienzo(cv2, ancho, alto, s, m))
    cv2.waitKey(args.espera_ms)

    cam = abrir_camara(cv2, indice)
    try:
        for _ in range(10):  # warm-up / auto-exposicion
            cam.read()
        det = capturar_marcadores(cv2, cam, args.frames, args.guardar)
        if len(det) < 2:
            raise SystemExit(
                f"Solo detecte {len(det)} marcador(es).\n"
                "- Se ven los 4 marcadores en la pared, y los 4 entran en el cuadro"
                " de la camara?\n"
                "- Baja la luz del cuarto o sube el brillo del proyector.\n"
                "- Corre con --guardar y mira logs/calib_camara.png para ver que"
                " esta viendo la camara."
            )
        H, err_medio, err_max = homografia(cv2, det, ancho, alto, s, m)
    finally:
        cam.release()

    np.save(RUTA_H, H)
    print(f"\nHomografia guardada en {RUTA_H}")
    print(f"  error de reproyeccion: medio {err_medio:.1f} px, maximo {err_max:.1f} px")
    if err_max > 15:
        print("  OJO: mas de 15 px de error. Revisa que la camara no se haya movido")
        print("       y que los 4 marcadores se vean completos y sin reflejos.")
    return H


# --------------------------------------------------------------------------- #
# prueba del click
# --------------------------------------------------------------------------- #
def prueba_click(cv2, H: np.ndarray) -> None:
    ancho = int(get("board.ancho", 1920))
    alto = int(get("board.alto", 1080))
    indice = int(get("board.camara", 0))
    marcas = np.zeros((alto, ancho, 3), np.uint8)

    def click(ev, x, y, *_):
        if ev != cv2.EVENT_LBUTTONDOWN:
            return
        px, py = cv2.perspectiveTransform(np.float32([[[x, y]]]), H)[0][0]
        print(f"  camara ({x},{y}) -> proyector ({px:.0f},{py:.0f})")
        if 0 <= px < ancho and 0 <= py < alto:
            cv2.circle(marcas, (int(px), int(py)), 25, (0, 0, 255), 4)
        else:
            print("    (cae fuera del proyector: le picaste afuera del area calibrada)")

    cam = abrir_camara(cv2, indice)
    cv2.namedWindow(VENTANA_CAM)
    cv2.setMouseCallback(VENTANA_CAM, click)
    print("\nClick en la ventana 'camara' -> circulo en la pared. ESC sale, c limpia.")
    try:
        while True:
            ok, frame = cam.read()
            if ok:
                cv2.imshow(VENTANA_CAM, frame)
            cv2.imshow(VENTANA_PROY, marcas)
            k = cv2.waitKey(1) & 0xFF
            if k == 27:
                break
            if k == ord("c"):
                marcas[:] = 0
    finally:
        cam.release()
        cv2.destroyAllWindows()


# --------------------------------------------------------------------------- #
# autotest: valida la matematica sin proyector ni camara
# --------------------------------------------------------------------------- #
def autotest(cv2) -> int:
    ancho = int(get("board.ancho", 1920))
    alto = int(get("board.alto", 1080))
    s = int(get("board.marcador_tam", 220))
    m = int(get("board.marcador_margen", 80))

    canvas = lienzo(cv2, ancho, alto, s, m)
    cam_w, cam_h = 1280, 720
    esq_proy = np.float32([[0, 0], [ancho, 0], [ancho, alto], [0, alto]])
    esq_cam = np.float32([[120, 80], [1180, 140], [1210, 660], [90, 610]])
    proy2cam = cv2.getPerspectiveTransform(esq_proy, esq_cam)
    falsa = cv2.warpPerspective(
        canvas, proy2cam, (cam_w, cam_h), borderValue=200, flags=cv2.INTER_LINEAR
    )

    det = cv2.aruco.ArucoDetector(diccionario(cv2))
    esquinas, ids, _ = det.detectMarkers(falsa)
    n = 0 if ids is None else len(ids)
    print(f"autotest: marcadores detectados en la imagen sintetica: {n}/4")
    if n < 4:
        print("FALLO: no detecte los 4 marcadores en una imagen perfecta.")
        return 1

    detectados = {int(i): c[0] for c, i in zip(esquinas, ids.flatten())}
    H, err_medio, err_max = homografia(cv2, detectados, ancho, alto, s, m)
    print(f"  error de reproyeccion: medio {err_medio:.2f} px, maximo {err_max:.2f} px")

    cam2proy_real = np.linalg.inv(proy2cam)
    rejilla = np.float32(
        [
            [[x, y]]
            for x in range(100, cam_w - 100, 120)
            for y in range(100, cam_h - 100, 120)
        ]
    )
    a = cv2.perspectiveTransform(rejilla, H).reshape(-1, 2)
    b = cv2.perspectiveTransform(rejilla, cam2proy_real).reshape(-1, 2)
    d = np.linalg.norm(a - b, axis=1)
    print(f"  contra la homografia real: medio {d.mean():.2f} px, maximo {d.max():.2f} px")

    ok = err_max < 5 and d.max() < 10
    print("autotest OK" if ok else "autotest FALLO")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--test", action="store_true", help="reusar cam2proj.npy, no recalibrar")
    ap.add_argument("--autotest", action="store_true", help="validar la matematica sin hardware")
    ap.add_argument("--guardar", action="store_true", help="guardar las fotos en logs/")
    ap.add_argument("--frames", type=int, default=15, help="frames a promediar (default 15)")
    ap.add_argument(
        "--espera-ms",
        type=int,
        default=1500,
        dest="espera_ms",
        help="ms de espera tras proyectar los marcadores (default 1500)",
    )
    ap.add_argument("--sin-prueba", action="store_true", help="calibrar y salir, sin el click")
    args = ap.parse_args()

    cv2 = _cv2()
    if args.autotest:
        return autotest(cv2)

    if args.test:
        if not RUTA_H.exists():
            raise SystemExit(
                f"No existe {RUTA_H}. Corre primero: python -m board.calibrate"
            )
        H = np.load(RUTA_H)
        print(f"Homografia cargada de {RUTA_H}")
        abrir_ventana_proyector(
            cv2, int(get("board.ancho", 1920)), int(get("board.alto", 1080))
        )
    else:
        H = calibrar(cv2, args)
        if args.sin_prueba:
            cv2.destroyAllWindows()
            return 0

    prueba_click(cv2, H)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
