# proyector-whiteboard

El proyector de Jose como (1) vista de la mañana para despertar y (2) pizarra en la
pared con webcam + IA. El plan completo está en [PLAN.md](PLAN.md); el avance real,
en [PROGRESS.md](PROGRESS.md); las reglas de trabajo, en [CLAUDE.md](CLAUDE.md).

## Setup

El entorno virtual vive **fuera** de OneDrive para que no lo sincronice:

```powershell
& "$env:USERPROFILE\.venvs\proyector\Scripts\python.exe" -m pip install -r requirements.txt
```

Para no escribir la ruta completa cada vez:

```powershell
. "$env:USERPROFILE\.venvs\proyector\Scripts\Activate.ps1"
```

(Si PowerShell bloquea el script, usa la ruta completa de `python.exe` en todos los comandos.)

- Configuración: `config.toml` (IP del proyector, cámara, offset del monitor...).
- Secretos: `.env` (copia `.env.example`). Está en `.gitignore`.
- El certificado del emparejamiento con el proyector se guarda en `secrets/` (gitignored).

## Comandos (Fase 0 — hardware)

| Comando | Qué hace |
|---|---|
| `python -m power.scan` | busca el proyector en la LAN por mDNS → da la IP |
| `python -m power.wake pair` | empareja con el proyector (sale un PIN en la pared) |
| `python -m power.wake status` | ¿prendido o en standby? |
| `python -m power.wake wake` | manda `WAKEUP` |
| `python -m power.wake power` | manda `POWER` (toggle) — respaldo |
| `python -m power.wake hdmi 1` | cambia a la entrada HDMI 1 |
| `python -m power.cast scan` | lista dispositivos Chromecast |
| `python -m power.cast site <url>` | castea una página al proyector |
| `python -m tools.displays` | monitores de Windows y su offset x/y |
| `python -m board.camera list` | lista webcams |
| `python -m board.camera preview` | preview de la webcam (ESC sale, `s` guarda) |

## Estructura

```
power/    prender el proyector y castear       (Fases 0, 2)
morning/  generar y servir la vista de mañana  (Fase 1)
board/    calibración, captura, análisis       (Fases 3, 4)
tools/    utilidades de diagnóstico
common/   carga de config.toml y .env
logs/     logs y capturas (gitignored)
```
