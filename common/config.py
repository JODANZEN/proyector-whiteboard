"""Carga config.toml y .env desde la raíz del repo.

Uso:
    from common.config import get, raiz
    ip = get("proyector.ip")
"""
from __future__ import annotations

import os
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
RUTA_CONFIG = RAIZ / "config.toml"
RUTA_ENV = RAIZ / ".env"
DIR_SECRETS = RAIZ / "secrets"
DIR_LOGS = RAIZ / "logs"


def raiz() -> Path:
    return RAIZ


@lru_cache(maxsize=1)
def cargar() -> dict[str, Any]:
    if not RUTA_CONFIG.exists():
        raise SystemExit(f"No encuentro {RUTA_CONFIG}")
    with RUTA_CONFIG.open("rb") as f:
        return tomllib.load(f)


def get(ruta: str, default: Any = None) -> Any:
    """get("proyector.ip") -> valor, o `default` si no existe o está vacío."""
    actual: Any = cargar()
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return default
        actual = actual[parte]
    if actual == "" or actual is None:
        return default
    return actual


def requerido(ruta: str) -> Any:
    valor = get(ruta)
    if valor is None:
        raise SystemExit(f"Falta `{ruta}` en {RUTA_CONFIG}")
    return valor


def cargar_env() -> None:
    """Mete las variables de .env en os.environ (sin pisar las que ya existen)."""
    if not RUTA_ENV.exists():
        return
    for linea in RUTA_ENV.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def secreto(clave: str, default: Any = None) -> Any:
    cargar_env()
    return os.environ.get(clave, default)
