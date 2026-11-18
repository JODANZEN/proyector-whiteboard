# Progreso

## 2026-11-18 — Planeación (chat)
**Hecho:** se definió el plan (PLAN.md), las reglas (CLAUDE.md) y el prototipo de calibración (board/calibrate_prototype.py)
**Probar:** —
**Resultado:** —
**Bloqueado / decisiones para Jose:** confirmar si tiene webcam; confirmar la hora a la que se despierta de verdad
**Siguiente:** Fase 0 — pruebas de hardware

## 2026-11-18 14:17 — Fase 0: repo + scripts de hardware
**Hecho:** repo `proyector-whiteboard` creado en `Documents\GitHub` con los 4 archivos de arranque (CLAUDE.md, PLAN.md, PROGRESS.md, board/calibrate_prototype.py) + scaffolding: `config.toml`, `.env.example`, `.gitignore`, `requirements.txt`, `README.md`, `common/config.py` (carga config.toml y .env), `power/scan.py` (mDNS), `power/wake.py` (pair/status/wake/power/hdmi/key por androidtvremote2), `power/cast.py` (catt), `tools/displays.py` (monitores de Windows + offset), `board/camera.py` (list/preview de webcam). Venv en `C:\Users\jdsn2\.venvs\proyector` (fuera de OneDrive) con androidtvremote2 0.3.3, catt 0.13.3, zeroconf 0.154, opencv-contrib-python 5.1.0, numpy 2.5.5 — todo gratis.

**Verificado por Claude (sin hardware):** los 5 CLIs arrancan; `common/config.py` lee config.toml; la API de androidtvremote2 0.3.3 coincide con lo que usa `wake.py`; el ArUco de OpenCV 5.1 funciona (`generateImageMarker` + `ArucoDetector`) así que el prototipo de la Fase 3 sigue siendo válido con esta versión.

**Probar:** (el proyector tiene que estar prendido y en la misma red para los primeros)
```
C:\Users\jdsn2\.venvs\proyector\Scripts\Activate.ps1
cd C:\Users\jdsn2\OneDrive\Documents\GitHub\proyector-whiteboard
python -m power.scan                 # -> IP del proyector; cópiala a config.toml
python -m power.cast scan            # -> nombre del Chromecast; cópialo a config.toml
python -m power.wake pair            # -> PIN en la pared, escríbelo
python -m power.wake status          # -> "estado: PRENDIDO"
python -m board.camera preview --index 0   # ESC para salir
python -m board.camera preview --index 1
```
Prueba de la fase (la del PLAN): poner el proyector en standby, esperar ~30 min y correr `python -m power.wake wake` → ¿prende?

**Resultado:** pendiente de Jose.
- Webcam: ✅ hay dos cámaras — índice 0 a 640x480 e índice 1 a 1280x720 (detectadas por `board.camera list`, sin ver la imagen todavía). Para la pizarra conviene la de 720p, pero Jose tiene que ver el preview de las dos y decidir cuál apunta a la pared.
- HDMI: ❌ no se puede confirmar todavía. `tools.displays` ve 2 monitores de 2560x1440 (primario en x=0, el otro en x=-3840) y ninguno de 1920x1080, así que el proyector NO está conectado por HDMI ahora mismo. Ojo: el monitor extendido está a la **izquierda** (x negativo), así que el `offset_x = 1920` que trae el prototipo está mal para esta PC; hay que volver a correr `tools.displays` con el proyector conectado.
- Proyector en la red: ❌ `power.scan` (8 s de mDNS) y `catt scan` no encontraron nada.

**Bloqueado / decisiones para Jose:**
1. El proyector no apareció en la red. Antes de culpar al código: ¿estaba prendido? ¿el "network standby" está activado en los ajustes de Google TV? ¿la PC y el proyector están en la misma red (la PC parece estar por cable y el proyector por WiFi — algunos routers separan las bandas o tienen aislamiento de clientes)? Hasta que `power.scan` o `catt scan` lo vean, no se puede emparejar ni probar `wake`.
2. Falta decidir la cámara (índice 0 vs 1) después del preview.
3. Pendiente del plan original: a qué hora te despiertas de verdad (para la Fase 2).

**Siguiente:** Jose corre los comandos de arriba con el proyector prendido. Si aparece → emparejar y probar el `wake` desde standby. Si no aparece → documentar el respaldo (smart plug con "encender al conectar", o un ESP32 que imite el control por BLE) y parar, como dice el PLAN.

## 2026-11-18 14:26 — Repo en GitHub + hallazgo de monitores
**Hecho:** repo subido a https://github.com/JODANZEN/proyector-whiteboard (**privado**, rama `main`). Para hacerlo público: `gh repo edit --visibility public`.

**Hallazgo (pregunta de Jose: ¿aguanta 3 monitores?):** la PC tiene una **Radeon RX 7800 XT** (RDNA 3: hasta 4 pantallas simultáneas) *más* una iGPU "AMD Radeon(TM) Graphics", así que 2 monitores + el proyector no es problema de GPU, solo de puertos físicos. También aparece un "Meta Virtual Monitor" (driver de pantalla virtual, de Quest Link) instalado.

**Consecuencia para la Fase 3:** `offset_x` / `offset_y` en config.toml **no son estables**. Cuando el proyector se apaga o se desconecta, Windows reacomoda las coordenadas del escritorio, y con un monitor virtual de por medio el orden puede cambiar. Decisión a tomar en la Fase 3: que `board/calibrate.py` y `overlay.py` busquen el monitor del proyector en tiempo real por resolución (1920x1080) con `tools/displays.py` en vez de confiar en el offset guardado. Por eso `tools.displays` ya avisa cuando no puede distinguir cuál monitor es el proyector.

**Probar:** nada nuevo. Sigue pendiente la prueba de hardware de la entrada anterior.
**Resultado:** push ✅ (verificado: `git status -sb` dice `main...origin/main`). Lo demás, pendiente de Jose.
**Bloqueado / decisiones para Jose:** las mismas de la entrada anterior (proyector no aparece en la red; elegir índice de cámara; hora real de despertar) + confirmar que la tarjeta tiene un puerto libre para el proyector.
**Siguiente:** Fase 0, prueba de hardware de Jose.

## 2026-11-18 14:34 — Repo público
**Hecho:** el repo pasó a **público**: https://github.com/JODANZEN/proyector-whiteboard. Antes de cambiarlo revisé el historial completo: no hay `.env`, ni `secrets/`, ni certificados, ni `.npy`, ni API keys en ningún commit (solo `.env.example` vacío). También cambié las rutas del README a `$env:USERPROFILE` para que no lleven el nombre de usuario de Windows y para que el repo sirva en cualquier máquina.

**Datos personales que SÍ quedan públicos a propósito** (están en CLAUDE.md / PLAN.md / las entradas viejas de PROGRESS.md, y las entradas viejas no se reescriben por regla del proyecto): el nombre "Jose", la ciudad (Tempe, AZ) con lat/lon en config.toml, el modelo del teléfono, la hora de despertar, la ruta `C:\Users\jdsn2\...` y la existencia del proyecto `pakito-jarvis`. Nada de eso es un secreto, pero ahí está si Jose prefiere limpiarlo.

**Probar:** `gh repo view --json visibility` → `PUBLIC` (ya verificado).
**Resultado:** ✅ público. Para revertir: `gh repo edit --visibility private --accept-visibility-change-consequences`.
**Bloqueado / decisiones para Jose:** si quiere, limpiar los datos personales de los .md (requeriría reescribir el historial con `git filter-repo`, o simplemente editarlos de aquí en adelante).
**Siguiente:** Fase 0, prueba de hardware de Jose (sigue pendiente).

## 2026-11-18 15:02 — Fase 0: proyector encontrado en la red
**Hecho:** Jose llenó config.toml. Correcciones y verificaciones:
- `chromecast` tenía pegada la línea completa de `catt scan` (`"192.168.0.222 - Xming Google TV - Formovie Xming Google TV"`); el formato de catt es `IP - NOMBRE - MODELO`, así que lo dejé en `"Xming Google TV"`, que es lo único que entiende `catt -d`.
- `power/cast.py`: ahora imprime el comando con `subprocess.list2cmdline` para que se vea entre comillas y sea copiable (antes el nombre con espacios salía sin comillas; funcionaba, pero confundía).

**Verificado por Claude (con el proyector prendido):**
- `power.scan` ✅ lo encuentra por mDNS: **Xming Google TV, 192.168.0.222**, puerto 6466, BT `E8:51:9E:82:05:0E`.
- Puertos abiertos ✅: 6466 (API del remote), 6467 (emparejamiento), 8009 (Chromecast).
- `power.cast status` ✅ responde con el nombre corregido (volumen 0, no muteado).
- Cámara: Jose confirma que el **índice 0** es la buena (ya estaba como default en config.toml).

**Probar:** el emparejamiento es interactivo (hay que escribir el PIN), así que lo corre Jose:
```
python -m power.wake pair      # sale un PIN de 6 dígitos en la pared, escríbelo
python -m power.wake status    # -> "estado: PRENDIDO"
```
Después, la prueba de la fase: poner el proyector en standby, esperar ~30 min, y `python -m power.wake wake`.

**Resultado:** red y cast ✅ confirmados. Emparejamiento y wake-desde-standby: pendientes de Jose.
**Bloqueado / decisiones para Jose:** ninguna nueva. Sigue pendiente la hora real de despertar (Fase 2) y el offset HDMI (el proyector todavía no se ha conectado por HDMI, así que `offset_x = 1920` sigue sin verificar).
**Siguiente:** emparejar y probar el wake desde standby. Si prende, Fase 0 cerrada.

## 2026-11-18 15:14 — Fase 0: emparejamiento ✅
**Hecho:** Jose emparejó la PC con el proyector. Certificado en `secrets/cert.pem` + `key.pem` (confirmado que `.gitignore` los excluye, no están en el repo).

**Verificado por Claude (proyector prendido):**
- `power.wake status` ✅ → `estado: PRENDIDO`, dispositivo: **Formovie / Xming Google TV / sw 7.00.999235495**.
- `power.wake wake` ✅ → conecta, lee el estado, manda `WAKEUP` y lo vuelve a leer sin error. Con el proyector ya prendido el WAKEUP es un no-op, así que esto valida el camino completo del código (conexión + envío de teclas), pero **no** prueba el despertar desde standby.

**Probar (la prueba que cierra la Fase 0, solo Jose puede hacerla):**
1. Apaga el proyector con su control (que entre en standby, no lo desconectes de la corriente).
2. Espera ~30 min para que entre en standby profundo.
3. `python -m power.wake wake`
Si falla la conexión en el primer intento, córrelo una segunda vez antes de darlo por muerto: el reintento automático es de la Fase 2, todavía no está implementado.

**Resultado:** emparejamiento ✅ confirmado. Wake desde standby: pendiente.
**Bloqueado / decisiones para Jose:** falta conectar el proyector por HDMI para (a) anotar el offset real con `tools.displays` y (b) probar el cambio de entrada (`python -m power.wake hdmi 1`). No probé el cambio de entrada todavía a propósito: sin el HDMI conectado solo mostraría "sin señal" y habría que volver a cambiarlo a mano.
**Siguiente:** la prueba de standby de arriba. Si prende → Fase 0 cerrada y arranca la Fase 1 (página de la mañana).

## 2026-11-18 15:41 — Cambio de prioridad + Fase 3: calibrate.py
**Decisión de Jose:** el modo mañana no es prioritario. El orden de trabajo pasa a ser **0 → 3 → 4 → 1 → 2 → 5**. Anotado como nota en PLAN.md (los números de fase no se renumeraron, para que las entradas viejas sigan teniendo sentido). La pizarra no depende de las fases 1 y 2: necesita HDMI + webcam, no Chromecast ni Task Scheduler.

**Hecho:** `board/calibrate.py`, el paso del prototipo a algo usable:
- Todo sale de config.toml (resolución, offsets, cámara, tamaño y margen de los marcadores); ya no hay constantes en el código.
- **Busca el monitor del proyector en tiempo real** por resolución con `tools/displays.py`, y solo usa `offset_x`/`offset_y` de config.toml como respaldo (esto era la decisión pendiente de la entrada de las 14:26: el offset guardado no es confiable porque Windows reacomoda las coordenadas).
- Promedia las esquinas de los marcadores en varios frames (`--frames`, default 15) en vez de usar un solo frame como el prototipo.
- `findHomography` con RANSAC e **informe del error de reproyección** en px, con aviso si pasa de 15 px.
- Mensajes de error que dicen qué hacer (luz, encuadre, `--guardar` para ver lo que ve la cámara).
- `--test` reusa `cam2proj.npy` sin recalibrar; `--guardar` deja la foto con los marcadores detectados en `logs/calib_camara.png`.
- `--autotest` valida la matemática **sin proyector ni cámara**: deforma el lienzo con una homografía conocida, detecta los marcadores en esa imagen sintética, recupera la homografía y la compara con la real.
- Nuevas llaves en config.toml: `cam_ancho` / `cam_alto` (0 = dejar el default de la cámara).

**Verificado por Claude (sin hardware):** `python -m board.calibrate --autotest` → 4/4 marcadores detectados, error de reproyección medio 0.97 px / máximo 2.13 px, y contra la homografía real medio 0.90 px / máximo 1.40 px. O sea: la geometría y el orden de las esquinas están bien. Lo que esto NO prueba es nada óptico (brillo del proyector, enfoque, reflejos en la pared, encuadre de la webcam).

**Probar (Jose):**
```
1. Conecta el proyector por HDMI y ponlo en pantalla extendida (Win+P -> Extender).
2. python -m tools.displays        # confirma que sale un monitor de 1920x1080
3. python -m board.calibrate --guardar
```
Deberías ver 4 cuadros negros en las esquinas de la pared, y en la consola `marcadores detectados: [0, 1, 2, 3] de [0, 1, 2, 3]`. Luego aparece la ventana "camara": haz click sobre un punto de la pared y debe salir un círculo rojo proyectado justo ahí. ESC para salir, c para limpiar.

**Resultado:** autotest ✅. Calibración con hardware real: pendiente de Jose.
**Bloqueado / decisiones para Jose:**
1. Falta conectar el HDMI; sin eso la calibración no se puede probar.
2. Para `analyze.py` (el siguiente paso de la Fase 3) hace falta la `GEMINI_API_KEY` en `.env`. Jose tiene que sacarla de aistudio.google.com (gratis) y pegarla ahí.
3. Sigue pendiente la prueba de standby de la Fase 0 (Jose dijo que la haría). No bloquea la pizarra, solo el modo mañana.

**Siguiente:** que Jose corra la calibración con el HDMI conectado. Después, `board/capture.py` (foto con el proyector en negro) + `board/analyze.py` (Gemini) para cerrar la Fase 3.
