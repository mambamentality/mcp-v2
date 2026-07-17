# tools/extract_convocatoria.py
"""Extrae fecha, hora, lugar, modalidad, orden del día y roles desde el PDF
de convocatoria. Heurístico: ajustar los patrones si cambia el formato."""
from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List

import azure.functions as func
import fitz  # PyMuPDF

from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [ToolProperty("fileBase64", "string", "Contenido del PDF de convocatoria en base64.", isRequired=True)]
)

_ROLE_HEADERS = ["Directores/as", "Comisión Fiscalizadora", "Alta Gerencia", "Administración"]

_DATE_RE = re.compile(r"(?:tendrá lugar el|el día)?\s*(\w+\s+\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", re.IGNORECASE)
_TIME_RE = re.compile(r"a\s+horas\s+(\d{1,2}:\d{2})", re.IGNORECASE)
_PLACE_RE = re.compile(r"presencial\s+en\s+(.+?)\s+y\s+mediante", re.IGNORECASE | re.DOTALL)


def register_extract_convocatoria_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ExtractConvocatoria",
        description="Extrae fecha, hora, lugar, orden del día y roles desde la convocatoria (PDF).",
        tool_properties=_TOOL_PROPERTIES,
    )
    def extract_convocatoria(context) -> str:
        try:
            args = get_arguments(context)
            file_b64 = args.get("fileBase64")
            if not file_b64:
                raise ValueError("Debe enviar 'fileBase64'.")

            pdf_bytes = base64.b64decode(file_b64)
            text = _extract_text(pdf_bytes)

            result = {
                "fecha": _first_match(_DATE_RE, text),
                "hora": _first_match(_TIME_RE, text),
                "lugar": _first_match(_PLACE_RE, text),
                "modalidad": _detect_modalidad(text),
                "ordenDelDia": _parse_orden_del_dia(text),
                "roles": _parse_roles(text),
            }
            return json.dumps({"status": "ok", **result}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("ExtractConvocatoria error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return extract_convocatoria


def _first_match(pattern: re.Pattern, text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _detect_modalidad(text: str) -> str:
    presencial = bool(re.search(r"presencial", text, re.IGNORECASE))
    virtual = bool(re.search(r"videoconferencia|teams|virtual", text, re.IGNORECASE))
    if presencial and virtual:
        return "presencial y videoconferencia"
    if virtual:
        return "videoconferencia"
    return "presencial"



def _parse_roles(text: str) -> Dict[str, List[str]]:
    """Los nombres preceden al encabezado de su rol en la convocatoria real
    (ej. 'Andrés Urquidi... Directores/as'), por eso el bloque de nombres
    pendiente se asigna al header que se acaba de encontrar, no al anterior."""
    match = re.search(r"Señores?/as:\s*(.*?)(?:\n\s*Banco FIE|\Z)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return {}

    block = match.group(1)
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    roles: Dict[str, List[str]] = {header: [] for header in _ROLE_HEADERS}
    pending_names: List[str] = []

    for line in lines:
        header_hit = next((h for h in _ROLE_HEADERS if h.lower() in line.lower()), None)
        if header_hit:
            roles[header_hit].extend(pending_names)
            pending_names = []
        else:
            pending_names.append(line)

    # Nombres que quedaron sin un header después (no debería pasar en el
    # formato esperado) se descartan en vez de asignarse a algo incorrecto.
    return {role: names for role, names in roles.items() if names}


# tools/extract_convocatoria.py — reemplazar la función _extract_text

from .ocr_helper import extract_text_with_ocr_fallback


def _extract_text(pdf_bytes: bytes) -> str:
    return extract_text_with_ocr_fallback(pdf_bytes)    

# tools/extract_convocatoria.py — agregar esta función y modificar _parse_orden_del_dia

def _parse_orden_del_dia_llm(text: str) -> List[Dict[str, Any]]:
    """Usa un LLM para reconstruir el orden del día a partir de texto OCR
    con ruido (números perdidos en saltos de página, pies de página
    mezclados). Más robusto que regex para este tipo de error."""
    from openai import AzureOpenAI
    from .config import get_env

    match = re.search(r"ORDEN DEL D[ÍI]A\s*(.*?)(?:\nCon este motivo|\nSaludo|\Z)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    block = match.group(1)

    client = AzureOpenAI(
        azure_endpoint=get_env("AZURE_OPENAI_ENDPOINT"),
        api_key=get_env("AZURE_OPENAI_KEY"),
        api_version=get_env("AZURE_OPENAI_API_VERSION", default="2024-08-01-preview"),
    )

    system_prompt = """Recibes el texto OCR (con posibles errores) del bloque "ORDEN DEL DÍA"
de una convocatoria de Directorio. Reconstruye la lista completa de puntos, incluyendo los
que perdieron su número por errores de OCR (usa el contexto y la numeración de los puntos
vecinos para inferir el número correcto). Ignora cualquier texto de pie de página (teléfonos,
direcciones de oficinas, membretes) que se haya colado entre puntos.

Responde ÚNICAMENTE con JSON válido, sin texto adicional, con este formato exacto:
[{"numero": "1", "titulo": "...", "subpuntos": [{"numero": "3.1", "titulo": "...", "subpuntos": []}]}]"""

    response = client.chat.completions.create(
        model=get_env("AZURE_OPENAI_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": block},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def _parse_orden_del_dia(text: str) -> List[Dict[str, Any]]:
    """Intenta con LLM primero (más robusto ante ruido de OCR); si falla
    o no hay credenciales configuradas, cae al parser por regex."""
    try:
        result = _parse_orden_del_dia_llm(text)
        if result:
            return result
    except Exception:
        logger.warning("Fallback a regex para orden del día (LLM no disponible o falló).", exc_info=True)

    return _parse_orden_del_dia_regex(text)


def _parse_orden_del_dia_regex(text: str) -> List[Dict[str, Any]]:
    """Parser original por regex — se mantiene como respaldo."""
    text = _strip_page_footers(text)
    match = re.search(r"ORDEN DEL D[ÍI]A\s*(.*?)(?:\nCon este motivo|\nSaludo|\Z)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    block = match.group(1)
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    entry_re = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.+)$")
    raw_points: List[List[str]] = []
    leading_lines: List[str] = []

    for line in lines:
        m = entry_re.match(line)
        if m:
            raw_points.append([m.group(1), m.group(2)])
        elif raw_points:
            raw_points[-1][1] = f"{raw_points[-1][1]} {line}"
        else:
            leading_lines.append(line)

    implicit_points: List[List[str]] = []
    buffer = ""
    for line in leading_lines:
        buffer = f"{buffer} {line}".strip()
        if line.endswith("."):
            implicit_points.append(buffer)
            buffer = ""
    if buffer:
        implicit_points.append(buffer)

    numbered_raw = [[str(i + 1), titulo] for i, titulo in enumerate(implicit_points)] + raw_points

    top_level: List[Dict[str, Any]] = []
    lookup: Dict[str, Dict[str, Any]] = {}
    for numero, titulo in numbered_raw:
        node = {"numero": numero, "titulo": titulo.strip(), "subpuntos": []}
        lookup[numero] = node
        if "." in numero:
            parent_numero = numero.rsplit(".", 1)[0]
            parent = lookup.get(parent_numero)
            if parent:
                parent["subpuntos"].append(node)
                continue
        top_level.append(node)

    return top_level


# tools/extract_convocatoria.py — reemplazar _FOOTER_RE y _strip_page_footers

_FOOTER_RE = re.compile(
    r"(?:\[?\s*,?\s*zona Sopocachi.*?)?(?:Oficina Nacional.*?)?"
    r"(?:La Paz\s+El Alto|Telf[:.]?\s*\d).{0,400}?(?:BancoFie|Banco\s*Fie|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _strip_page_footers(text: str) -> str:
    """El membrete de pie de página (teléfonos de oficinas) se repite en
    cada página del PDF escaneado. Se detecta por la presencia de varios
    'Telf:' seguidos, más que por texto literal exacto, porque el OCR no
    siempre reconoce el encabezado 'Oficina Nacional' de forma consistente."""
    return _FOOTER_RE.sub(" ", text)