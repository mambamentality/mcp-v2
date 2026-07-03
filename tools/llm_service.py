from __future__ import annotations

from typing import List, Optional

from .schemas import ActaFormData


class LLMService:
    """Interfaz de servicio LLM.

    NOTA: pese al nombre, esta clase NO invoca ningún modelo externo. Genera
    el Markdown de forma determinista a partir de los datos capturados. Si en
    el futuro se conecta a un modelo real (Azure OpenAI, etc.), este es el
    único lugar que habría que tocar; el resto del código no depende de la
    implementación interna.
    """

    def generate_markdown_draft(self, data: ActaFormData, context: Optional[str] = None) -> str:
        parts: List[str] = []
        parts.append(f"# Acta de Reunión: {data.titulo or 'Sin título'}")

        if data.fecha:
            parts.append(f"**Fecha:** {data.fecha}")
        if data.hora_inicio or data.hora_fin:
            parts.append(f"**Hora:** {data.hora_inicio or 'n/a'} — {data.hora_fin or 'n/a'}")
        if data.lugar:
            parts.append(f"**Lugar:** {data.lugar}")
        parts.append("")

        parts.append("## Participantes")
        if data.participantes:
            for participant in data.participantes:
                parts.append(f"- {participant}")
        else:
            parts.append("- No se registraron participantes.")
        parts.append("")

        parts.append("## Objetivo")
        parts.append(data.objetivo or "No se especificó un objetivo.")
        parts.append("")

        parts.append("## Antecedentes")
        parts.append(data.antecedentes or "No se registraron antecedentes.")
        parts.append("")

        parts.append("## Temas tratados")
        if data.temas_tratados:
            for tema in data.temas_tratados:
                parts.append(f"- {tema}")
        else:
            parts.append("- No se registraron temas tratados.")
        parts.append("")

        parts.append("## Acuerdos")
        if data.acuerdos:
            for acuerdo in data.acuerdos:
                parts.append(f"- {acuerdo}")
        else:
            parts.append("- No se registraron acuerdos.")
        parts.append("")

        parts.append("## Compromisos")
        if data.compromisos:
            for compromiso in data.compromisos:
                parts.append(f"- {compromiso}")
        else:
            parts.append("- No se registraron compromisos.")
        parts.append("")

        parts.append("## Observaciones")
        parts.append(data.observaciones or "No hay observaciones adicionales.")
        parts.append("")

        if context:
            parts.append("## Contexto adicional")
            parts.append(context)
            parts.append("")

        parts.append("## Conclusiones")
        parts.append(
            "El acta se genera a partir de los datos capturados y debe revisarse antes de su aprobación."
        )
        return "\n".join(parts)
