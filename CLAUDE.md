# Proyector — reglas para Claude Code

- Lee `PLAN.md` antes de hacer cualquier cosa. Construye fase por fase, en orden.
- No empieces la siguiente fase hasta que Jose confirme que la prueba manual de la fase actual funcionó.
- Después de cada tarea, AGREGA una entrada a `PROGRESS.md` con el formato de `PLAN.md` → "Reglas de reporte". Nunca reescribas entradas viejas. Nunca marques ✅ algo que Jose no haya probado.
- Pasos pequeños que se puedan probar. Jose prefiere correr las pruebas él mismo: dale los comandos exactos y qué debería ver.
- Windows + Python 3.11+. Herramientas gratis primero; pregúntale a Jose antes de agregar cualquier cosa de pago.
- Los secretos van en `.env` (gitignored). La configuración en `config.toml`.
- Si algo del hardware no funciona como dice el plan, para, escribe el hallazgo en PROGRESS.md y pregunta. No improvises cambios grandes de arquitectura.
