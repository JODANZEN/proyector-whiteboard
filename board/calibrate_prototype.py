"""Prototipo de calibración: proyecta 4 marcadores ArUco, los detecta con la webcam,
calcula la homografía cámara->proyector y la guarda en cam2proj.npy.
Prueba: click en la ventana "cam" -> aparece un círculo en ese mismo punto de la pared. ESC para salir.
Requiere: pip install opencv-contrib-python numpy
"""
import cv2
import numpy as np

W, H = 1920, 1080        # resolución del proyector
PROJ_X = 1920            # offset x del proyector como pantalla extendida (revisa la configuración de pantalla de Windows)
CAM_INDEX = 0
S, M = 220, 80           # tamaño y margen de los marcadores, en px del proyector

aruco = cv2.aruco
d = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
pos = {0: (M, M), 1: (W - M - S, M), 2: (W - M - S, H - M - S), 3: (M, H - M - S)}

canvas = np.full((H, W), 255, np.uint8)
for i, (x, y) in pos.items():
    canvas[y:y + S, x:x + S] = aruco.generateImageMarker(d, i, S)

cv2.namedWindow("proj", cv2.WINDOW_NORMAL)
cv2.moveWindow("proj", PROJ_X, 0)
cv2.setWindowProperty("proj", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow("proj", canvas)
cv2.waitKey(1500)

cam = cv2.VideoCapture(CAM_INDEX)
for _ in range(10):  # warm-up de la cámara / auto-exposición
    ok, frame = cam.read()
corners, ids, _ = aruco.ArucoDetector(d).detectMarkers(frame)
n = 0 if ids is None else len(ids)
assert n >= 2, f"solo se detectaron {n} marcadores; ajusta la cámara o la luz"

src, dst = [], []
for c, i in zip(corners, ids.flatten()):
    x, y = pos[int(i)]
    src += c[0].tolist()
    dst += [[x, y], [x + S, y], [x + S, y + S], [x, y + S]]
Hm, _ = cv2.findHomography(np.float32(src), np.float32(dst))
np.save("cam2proj.npy", Hm)
print(f"Homografía guardada ({n} marcadores)")

blank = np.zeros((H, W, 3), np.uint8)

def click(ev, x, y, *_):
    if ev == cv2.EVENT_LBUTTONDOWN:
        px, py = cv2.perspectiveTransform(np.float32([[[x, y]]]), Hm)[0][0]
        cv2.circle(blank, (int(px), int(py)), 25, (0, 0, 255), 4)

cv2.namedWindow("cam")
cv2.setMouseCallback("cam", click)
while True:
    ok, f = cam.read()
    if ok:
        cv2.imshow("cam", f)
    cv2.imshow("proj", blank)
    if cv2.waitKey(1) == 27:
        break
cam.release()
cv2.destroyAllWindows()
