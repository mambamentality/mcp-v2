import json
from typing import Any, Dict, List, Optional

import azure.functions as func

from .extract_agreements import _extract_agreements_from_fragment, _normalize_fragments


def register_generate_meeting_minutes_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="req",
        tool_name="generate_meeting_minutes",
        description="Genera un borrador de acta en markdown a partir de fragmentos de actas en JSON.",
    )
    def generate_meeting_minutes(req: dict):
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

            metadata = _normalize_metadata(req)
            agreements: List[Dict[str, Any]] = []
            for idx, fragment in enumerate(fragments, start=1):
                agreements.extend(_extract_agreements_from_fragment(fragment, origen=f"fragmento_{idx}"))

            minutes_md = _render_meeting_minutes(metadata, fragments, agreements)
            return json.dumps(
                {
                    "status": "ok",
                    "meeting_minutes_md": minutes_md,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Error al generar las actas: {str(exc)}",
                },
                ensure_ascii=False,
            )

    return generate_meeting_minutes


def _normalize_metadata(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {}

    metadata: Dict[str, Any] = {}
    metadata["title"] = payload.get("title") or payload.get("titulo") or payload.get("titulo_acta") or "Acta de reunión"
    metadata["numero_acta"] = payload.get("numero_acta") or payload.get("numeroActa") or payload.get("numero")
    metadata["tipo_reunion"] = payload.get("tipo_reunion") or payload.get("tipoReunion") or payload.get("tipo")
    metadata["fecha"] = payload.get("fecha") or payload.get("date")
    participants = payload.get("participantes") or payload.get("participants")
    if isinstance(participants, str):
        metadata["participantes"] = [participant.strip() for participant in participants.split("\n") if participant.strip()]
    elif isinstance(participants, list):
        metadata["participantes"] = [str(item).strip() for item in participants if str(item).strip()]
    else:
        metadata["participantes"] = []
    return metadata


def _render_meeting_minutes(metadata: Dict[str, Any], fragments: List[str], agreements: List[Dict[str, Any]]) -> str:
    lines: List[str] = []

    title = metadata.get("title", "Acta de reunión")
    lines.append(f"# {title}")

    if metadata.get("numero_acta"):
        lines.append(f"**Número de acta:** {metadata['numero_acta']}")
    if metadata.get("tipo_reunion"):
        lines.append(f"**Tipo de reunión:** {metadata['tipo_reunion']}")
    if metadata.get("fecha"):
        lines.append(f"**Fecha:** {metadata['fecha']}")
    if metadata.get("participantes"):
        participants = metadata["participantes"]
        lines.append("**Participantes:**")
        for participant in participants:
            lines.append(f"- {participant}")

    lines.append("")
    lines.append("## Resumen de fragmentos recibidos")
    lines.append(
        "Se han agregado fragmentos de actas recibidos desde el agente. A continuación se conserva la información original y se extraen los acuerdos detectados."
    )
    lines.append("")

    for idx, fragment in enumerate(fragments, start=1):
        snippet = fragment.strip()
        if len(snippet) > 320:
            snippet = snippet[:320].rstrip() + "..."
        lines.append(f"### Fragmento {idx}")
        lines.append(snippet)
        lines.append("")

    if agreements:
        lines.append("## ACUERDOS")
        lines.append("| N° | Acuerdo | Responsable | Fecha |")
        lines.append("|---|---|---|---|")
        for idx, agreement in enumerate(agreements, start=1):
            texto = _escape_markdown_cell(str(agreement.get("texto", "")).strip())
            responsable = _escape_markdown_cell(str(agreement.get("responsable", "")).strip())
            fecha = _escape_markdown_cell(str(agreement.get("fecha", "")).strip())
            lines.append(f"| {idx} | {texto} | {responsable} | {fecha} |")
    else:
        lines.append("## ACUERDOS")
        lines.append("No se detectaron acuerdos explícitos en los fragmentos recibidos.")

    lines.append("")
    lines.append("## Texto consolidado")
    lines.extend(fragment for fragment in fragments)
    return "\n".join(lines).strip()


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")
