# Proyector — Plan de build

Proyecto de Jose: usar su proyector como (1) vista de la mañana que lo ayuda a despertar y le muestra el día, y (2) pizarra en la pared con webcam + IA que corrige lo que escribe.

## Hardware

| Pieza | Detalle |
|---|---|
| Proyector | **Formovie Xming Page One** (XMM2101). Google TV, Chromecast integrado, WiFi 2.4/5 GHz, BT 5.0, HDMI, 1080p, 320 ISO lm. Tiene "network standby" (<2 W) |
| PC | Windows. **Duerme de noche** (la luz le molesta) — hay que despertarla con Task Scheduler |
| Teléfono | Samsung S25 Ultra (S Pen) — posible superficie de dibujo en el futuro |
| Webcam | Por confirmar |
| Ubicación | Tempe, AZ (America/Phoenix, sin horario de verano) |

## Arquitectura

```
MODO MAÑANA (por Chromecast, no necesita HDMI)
05:55  Task Scheduler despierta la PC → morning/generate.py
       lee Google Calendar + Google Tasks + clima → genera morning.html
06:00  power/wake.py   → androidtvremote2 manda WAKEUP al proyector
       power/cast.py   → catt cast_site http://<ip-pc>:8000/morning.html

MODO PIZARRA (por HDMI, el proyector es una pantalla extendida de Windows)
board/calibrate.py → homografía cámara→proyector con 4 marcadores ArUco
board/capture.py   → foto de la pared (proyector en negro ~0.5 s para que no sature)
board/analyze.py   → Gemini (visión) revisa → feedback + cajas de dónde está el error
board/overlay.py   → dibuja marcas en la pared encima de lo escrito
```

## Restricciones

- **Gratis primero.** Gemini con API key gratis para visión/texto. Open-Meteo para el clima (no pide key). APIs de Google gratis. Nada de pago sin preguntarle a Jose.
- Rápido y simple. Python 3.11+ en Windows. Nada de modelos locales pesados.
- Secretos en `.env` (GEMINI_API_KEY, credenciales OAuth de Google) — en `.gitignore`.
- Configuración en `config.toml` (IP del proyector, nombre del Chromecast, hora de la alarma, ciudad, índice de la cámara, posición del monitor del proyector).
- Más adelante se integra con Pakito (`C:\Users\jdsn2\source\repos\pakito-jarvis`), así que cada modo tiene que tener una entrada CLI limpia que Pakito pueda llamar.

## Fases

Cada fase termina con una **prueba manual que Jose corre él mismo**. No pases a la siguiente fase hasta que Jose confirme que la prueba funcionó.

> **Orden cambiado el 2026-11-18 por decisión de Jose:** el modo mañana no es prioritario.
> El orden de trabajo es **0 → 3 → 4 → 1 → 2 → 5**. Los números de las fases se quedan
> como están para que las entradas viejas de PROGRESS.md sigan teniendo sentido.
> La pizarra (3 y 4) no depende de las fases 1 y 2: necesita HDMI + webcam, no el
> Chromecast ni el Task Scheduler.

### Fase 0 — Probar el hardware
- `power/wake.py`: emparejar con `androidtvremote2` (sale un PIN en la pared la primera vez), leer `is_on`, mandar `WAKEUP` (y probar `POWER` si no responde).
- `power/cast.py`: `catt scan` + `cast_site` de una URL.
- HDMI: confirmar que Windows lo detecta como pantalla extendida y anotar su offset x/y. Averiguar cómo cambiar el proyector a la entrada HDMI (keycode por el remote API o a mano).
- Webcam: listar cámaras y mostrar un preview.
- **Prueba de Jose:** pone el proyector en standby, espera ~30 min y corre `python -m power.wake` → ¿prende?
- Si no prende: documenta las opciones de respaldo (smart plug + encender al conectar, o un ESP32 que imite el control por BLE) y para.

### Fase 1 — Página de la mañana (manual)
- `morning/generate.py` → `morning/out/morning.html` (un solo archivo autocontenido).
- **Vista tranqui** (por defecto): fondo casi negro y cálido que sube de brillo durante ~10 min (efecto amanecer); hora grande; clima y salida del sol; línea de tiempo del día en bloques de color; "ahora → siguiente"; máximo 3 tareas. Poco texto, se lee a 3 m de distancia recién despierto.
- **Power view**: el día completo, todas las tareas, deadlines. Cambia después de N minutos o con una tecla/comando.
- `morning/serve.py` sirve la carpeta en la LAN.
- **Prueba de Jose:** `python -m morning.run --now` → la página aparece en la pared. Jose la usa a mano unos días y vamos iterando el diseño.

### Fase 2 — Automatización de las 6am
- Tarea en Task Scheduler con "Wake the computer to run this task" (exportar el XML + un script que la instale).
- Secuencia: generar → servir → despertar el proyector → reintentar si no responde → cast. Todo con log en `logs/`.
- Que el servidor se apague solo después de ~1 h.
- **Prueba de Jose:** programarlo 5 min adelante con la PC suspendida.

### Fase 3 — Pizarra v1
- `board/calibrate.py` (punto de partida: el script de ArUco + homografía de abajo). Guarda `cam2proj.npy`.
- Una tecla dispara la captura con el proyector en negro → `analyze.py` → un panel de texto con la corrección proyectado al lado del área de trabajo.
- **Prueba de Jose:** escribe un problema de física o matemáticas con un error a propósito → la corrección aparece en la pared en menos de ~5 s.

### Fase 4 — Pizarra v2 (marcas encima)
- Gemini devuelve cajas normalizadas → píxeles de cámara → homografía → píxeles del proyector → círculo/subrayado más una nota corta al lado.
- Opcional: detectar los trazos con OpenCV (diferencia contra una foto de referencia de la pared vacía) para afinar la posición de las marcas.
- **Prueba de Jose:** la marca cae encima del error con menos de ~2 cm de diferencia.

### Fase 5 — Integración con Pakito
- Comandos de voz: "modo pizarra", "revisa esto", "modo mañana". Las tareas de Pakito (Google Tasks) alimentan la vista de la mañana.

## Punto de partida para la calibración (Fase 3)

Script de prueba de ArUco + homografía: proyecta 4 marcadores, la webcam los detecta, calcula la homografía, y al hacer click en la vista de la cámara dibuja un círculo en ese mismo punto de la pared. Pásalo a `board/calibrate.py` y usa `config.toml` en vez de las constantes.

## Reglas de reporte — OBLIGATORIAS

Después de cada sesión o tarea, **agrega** (nunca sobrescribas) una entrada al final de `PROGRESS.md`:

```
## YYYY-MM-DD HH:MM — <fase / tarea>
**Hecho:** qué se construyó o cambió (archivos)
**Probar:** comandos exactos que Jose debe correr y qué debería ver
**Resultado:** pendiente de Jose | ✅ confirmado | ❌ falló (por qué)
**Bloqueado / decisiones para Jose:** …
**Siguiente:** …
```

Jose y su asistente de chat leen `PROGRESS.md` para seguir el avance, así que tiene que ser honesto: no marques ✅ algo que Jose no probó.
