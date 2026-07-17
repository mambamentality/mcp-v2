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
_PLACE_RE = re.compile(r"en\s+(?:el|la)?\s*(.+?)(?:,\s*y mediante|\.\s|\.$)", re.IGNORECASE)


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


def _extract_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


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


def _parse_orden_del_dia(text: str) -> List[Dict[str, Any]]:
    match = re.search(r"ORDEN DEL D[ÍI]A\s*(.*?)(?:\nCon este motivo|\nSaludo|\Z)", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    block = match.group(1)
    line_re = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.+)$", re.MULTILINE)
    raw_points = [(m.group(1), m.group(2).strip()) for m in line_re.finditer(block)]

    top_level: List[Dict[str, Any]] = []
    lookup: Dict[str, Dict[str, Any]] = {}
    for numero, titulo in raw_points:
        node = {"numero": numero, "titulo": titulo, "subpuntos": []}
        lookup[numero] = node
        if "." in numero:
            parent_numero = numero.rsplit(".", 1)[0]
            parent = lookup.get(parent_numero)
            if parent:
                parent["subpuntos"].append(node)
                continue
        top_level.append(node)

    return top_level


def _parse_roles(text: str) -> Dict[str, List[str]]:
    """NOTA: validar con la convocatoria real si los nombres preceden o
    siguen al encabezado de rol — en la muestra real los nombres vienen
    ANTES del header ('Directores/as' aparece después de la lista)."""
    match = re.search(r"Señores?/as:\s*(.*?)ORDEN DEL D[ÍI]A", text, re.IGNORECASE | re.DOTALL)
    if not match:
        return {}

    block = match.group(1)
    lines = [line.strip() for line in block.splitlines() if line.strip()]

    roles: Dict[str, List[str]] = {header: [] for header in _ROLE_HEADERS}
    current_role = None
    pending_names: List[str] = []

    for line in lines:
        header_hit = next((h for h in _ROLE_HEADERS if h.lower() in line.lower()), None)
        if header_hit:
            if current_role:
                roles[current_role].extend(pending_names)
            current_role = header_hit
            pending_names = []
        else:
            pending_names.append(line)

    if current_role:
        roles[current_role].extend(pending_names)

    return {role: names for role, names in roles.items() if names}