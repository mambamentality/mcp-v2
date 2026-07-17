# tools/paths.py
"""Construcción centralizada de rutas de SharePoint."""
from __future__ import annotations

_INSUMOS_ROOT = "Actas/Insumos"
_GENERADAS_ROOT = "Actas/Generadas"
_MAESTRO_PATH = "Actas/Acta Maestra.xlsx"


def insumos_folder(gestion: str, directorio: str) -> str:
    return f"{_INSUMOS_ROOT}/{gestion.strip()}/{directorio.strip()}"


def generadas_folder(gestion: str, directorio: str) -> str:
    return f"{_GENERADAS_ROOT}/{gestion.strip()}/{directorio.strip()}"


def maestro_path() -> str:
    return _MAESTRO_PATH


def list_gestiones() -> str:
    return _INSUMOS_ROOT


def list_directorios(gestion: str) -> str:
    return f"{_INSUMOS_ROOT}/{gestion.strip()}"


def generadas_root_for_gestion(gestion: str) -> str:
    return f"{_GENERADAS_ROOT}/{gestion.strip()}"