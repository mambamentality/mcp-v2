import json
import re
from typing import Any, Dict, List, Optional

import azure.functions as func


def register_extract_agreements_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="req",
        tool_name="extract_agreements",
        description="Extrae acuerdos y responsabilidades de fragmentos de actas en JSON.",
    )
    def extract_agreements(req: dict):
        try:
            fragments = _normalize_fragments(req)
            if not fragments:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "No se encontraron fragmentos en el payload. Use 'fragments', 'fragmentos' o 'texto'.",
                    },
                    ensure_ascii=False,
                )

            agreements: List[Dict[str, str]] = []
            for idx, fragment in enumerate(fragments, start=1):
                agreements.extend(_extract_agreements_from_fragment(fragment, origen=f"fragmento_{idx}"))

            return json.dumps(
                {
                    "status": "ok",
                    "agreements": agreements,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error al extraer acuerdos: {str(exc)}",
                },
                ensure_ascii=False,
            )

    return extract_agreements


def _normalize_fragments(payload: Any) -> List[str]:
    fragments: List[str] = []
    if isinstance(payload, str):
        fragments.append(payload)
        return fragments

    if not isinstance(payload, dict):
        return fragments

    raw = payload.get("fragments") or payload.get("fragmentos") or payload.get("texto") or payload.get("text") or payload.get("data")
    if isinstance(raw, str):
        fragments.append(raw)
    elif isinstance(raw, dict):
        text = raw.get("text") or raw.get("texto") or raw.get("fragmento") or raw.get("raw")
        if isinstance(text, str):
            fragments.append(text)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                fragments.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("texto") or item.get("fragmento") or item.get("raw")
                if isinstance(text, str):
                    fragments.append(text)
    elif raw is not None:
        fragments.append(str(raw))

    clean_fragments = [fragment.strip() for fragment in fragments if isinstance(fragment, str) and fragment.strip()]
    return clean_fragments


def _extract_agreements_from_fragment(text: str, origen: Optional[str] = None) -> List[Dict[str, str]]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    sections = _find_agreement_sections(text)
    if not sections:
        sections = [text]

    agreements: List[Dict[str, str]] = []
    for section in sections:
        agreements.extend(_parse_agreement_section(section, origen))

    return agreements


def _find_agreement_sections(text: str) -> List[str]:
    sections: List[str] = []
    heading_pattern = re.compile(r"(?sm)^#{1,6}\s*ACUERDOS?\s*$\n?(.*?)(?=(?m)^#{1,6}\s|\Z)")
    for match in heading_pattern.finditer(text):
        section = match.group(1).strip()
        if section:
            sections.append(section)

    if sections:
        return sections

    fallback_pattern = re.compile(r"(?sm)^(?:ACUERDOS?|ACUERDO)\s*[:\-]?\s*$\n?(.*?)(?=(?m)^[A-Z \t]+:\s*$|\Z)")
    for match in fallback_pattern.finditer(text):
        section = match.group(1).strip()
        if section:
            sections.append(section)

    return sections


def _parse_agreement_section(section: str, origen: Optional[str]) -> List[Dict[str, str]]:
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if not lines:
        return []

    table_agreements = _parse_markdown_table(lines, origen)
    if table_agreements:
        return table_agreements

    agreements: List[Dict[str, str]] = []
    for line in lines:
        match = re.match(r"^\s*(?:[-*•]|\d+[\.)])\s+(.*)$", line)
        if match:
            item = match.group(1).strip()
            parsed = _parse_agreement_fields(item)
            if parsed:
                parsed["origen"] = origen or "fragmento"
                agreements.append(parsed)
            continue

        if "acuerdo" in line.lower() or "responsable" in line.lower() or "fecha" in line.lower():
            parsed = _parse_agreement_fields(line)
            if parsed:
                parsed["origen"] = origen or "fragmento"
                agreements.append(parsed)

    return agreements


def _parse_markdown_table(lines: List[str], origen: Optional[str]) -> List[Dict[str, str]]:
    rows: List[List[str]] = []
    for line in lines:
        if re.match(r"^\|.*\|$", line):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            rows.append(cells)

    if len(rows) < 2:
        return []

    header = [cell.lower() for cell in rows[0]]
    if not any("acuerdo" in cell or "compromiso" in cell for cell in header):
        return []

    agreements: List[Dict[str, str]] = []
    for row in rows[2:] if len(rows) > 2 and re.match(r"^\|?\s*[-:]+\s*\|", rows[1]) else rows[1:]:
        if len(row) < 2:
            continue
        agreement: Dict[str, str] = {}
        for index, cell in enumerate(row):
            title = header[index]
            if "acuerdo" in title or "compromiso" in title:
                agreement["texto"] = cell
            elif "responsable" in title or "responsable" in title:
                agreement["responsable"] = cell
            elif "fecha" in title:
                agreement["fecha"] = cell
            else:
                agreement[title] = cell
        if agreement:
            agreement["origen"] = origen or "fragmento"
            agreements.append(agreement)

    return agreements


def _parse_agreement_fields(text: str) -> Dict[str, str]:
    agreement: Dict[str, str] = {"texto": text}

    responsable_match = re.search(r"responsable\s*[:\-]\s*(.+?)(?:[\.;]|$)", text, re.IGNORECASE)
    if responsable_match:
        agreement["responsable"] = responsable_match.group(1).strip()

    fecha_match = re.search(r"fecha\s*[:\-]\s*(.+?)(?:[\.;]|$)", text, re.IGNORECASE)
    if fecha_match:
        agreement["fecha"] = fecha_match.group(1).strip()

    return agreement
