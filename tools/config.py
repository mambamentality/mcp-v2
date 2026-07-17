# tools/config.py
import os


def get_env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value or ""