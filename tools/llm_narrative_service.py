# tools/llm_narrative_service.py
from __future__ import annotations

from openai import AzureOpenAI

from .config import get_env

_SYSTEM_PROMPT_NUEVO = """Eres un asistente que redacta actas de Directorio de un banco boliviano,
en tono formal e institucional, en tercera persona. Redacta un párrafo (sin encabezados ni
Markdown) que resuma el contenido del documento de respaldo entregado, mencionando cifras
relevantes si existen. No incluyas la Determinación, esa se genera aparte."""

_SYSTEM_PROMPT_ACTUALIZAR = """Eres un asistente que actualiza actas de Directorio de un banco
boliviano. Se te da la redacción de un punto TAL COMO SE ESCRIBIÓ EN UNA SESIÓN ANTERIOR, y el
contenido de un documento de respaldo NUEVO sobre el mismo tema.

Reescribe el párrafo manteniendo EXACTAMENTE la misma estructura, tono y estilo del texto
anterior, reemplazando: el número de cite, las fechas de corte, las cifras/porcentajes por los
nuevos valores del documento de respaldo, y el nombre del expositor si cambió. No agregues
información nueva que no esté en el documento de respaldo. No incluyas la Determinación."""


def generate_point_narrative(
    titulo_punto: str,
    expositor: str,
    cite: str,
    texto_respaldo: str,
    narrativa_anterior: str | None = None,
) -> str:
    client = AzureOpenAI(
        azure_endpoint=get_env("AZURE_OPENAI_ENDPOINT"),
        api_key=get_env("AZURE_OPENAI_KEY"),
        api_version=get_env("AZURE_OPENAI_API_VERSION", default="2024-08-01-preview"),
    )

    if narrativa_anterior:
        system_prompt = _SYSTEM_PROMPT_ACTUALIZAR
        user_prompt = (
            f"Punto: {titulo_punto}\nExpositor actual: {expositor or 'no especificado'}\n"
            f"Cite nuevo: {cite or 's/n'}\n\n--- Redacción anterior ---\n{narrativa_anterior}\n\n"
            f"--- Documento de respaldo nuevo ---\n{texto_respaldo[:8000]}"
        )
    else:
        system_prompt = _SYSTEM_PROMPT_NUEVO
        user_prompt = (
            f"Punto: {titulo_punto}\nExpositor: {expositor or 'no especificado'}\n"
            f"Cite: {cite or 's/n'}\n\nContenido del documento de respaldo:\n{texto_respaldo[:8000]}"
        )

    response = client.chat.completions.create(
        model=get_env("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def generate_point_determination(titulo_punto: str, cite: str, determinacion_anterior: str | None = None) -> str:
    if not determinacion_anterior:
        return "Determinación pendiente de definir manualmente."

    client = AzureOpenAI(
        azure_endpoint=get_env("AZURE_OPENAI_ENDPOINT"),
        api_key=get_env("AZURE_OPENAI_KEY"),
        api_version=get_env("AZURE_OPENAI_API_VERSION", default="2024-08-01-preview"),
    )
    system_prompt = (
        "Actualiza este párrafo de Determinación de un acta de Directorio, manteniendo "
        "exactamente la misma redacción y decisión, solo reemplazando cite y fechas."
    )
    user_prompt = f"Punto: {titulo_punto}\nCite nuevo: {cite or 's/n'}\n\nDeterminación anterior:\n{determinacion_anterior}"

    response = client.chat.completions.create(
        model=get_env("AZURE_OPENAI_DEPLOYMENT"),
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()
