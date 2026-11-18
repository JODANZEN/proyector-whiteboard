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
