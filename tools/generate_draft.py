import json
import logging
from typing import Any, List

import azure.functions as func

from .draft_manager import DraftManager
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json
from .schemas import ActaFormData

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("titulo", "string", "Título del acta.", isRequired=True),
        ToolProperty("fecha", "string", "Fecha de la reunión.", isRequired=False),
        ToolProperty("hora_inicio", "string", "Hora de inicio.", isRequired=False),
        ToolProperty("hora_fin", "string", "Hora de fin.", isRequired=False),
        ToolProperty("lugar", "string", "Lugar de la reunión.", isRequired=False),
        ToolProperty("participantes", "string", "Participantes de la reunión.", isRequired=False, isArray=True),
        ToolProperty("objetivo", "string", "Objetivo de la reunión.", isRequired=False),
        ToolProperty("antecedentes", "string", "Antecedentes o contexto.", isRequired=False),
        ToolProperty("temas_tratados", "string", "Temas tratados.", isRequired=False, isArray=True),
        ToolProperty("acuerdos", "string", "Acuerdos alcanzados.", isRequired=False, isArray=True),
        ToolProperty("compromisos", "string", "Compromisos derivados.", isRequired=False, isArray=True),
        ToolProperty("observaciones", "string", "Observaciones adicionales.", isRequired=False),
        ToolProperty(
            "context",
            "string",
            "Contexto adicional en texto libre para incluir en el borrador (opcional).",
            isRequired=False,
        ),
    ]
)


def register_generate_draft_tool(app: func.FunctionApp):
    draft_manager = DraftManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="GenerateDraft",
        description="Genera un borrador de acta en Markdown a partir de los datos explícitos de la conversación.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def generate_draft(context) -> str:
        try:
            args = get_arguments(context)
            form_data = _build_form_data(args)
            extra_context = args.get("context")

            if not form_data.titulo:
                raise ValueError("Debe enviar 'titulo'.")

            draft = draft_manager.create_draft(form_data, extra_context)
            return json.dumps(
                {
                    "draftId": draft.draft_id,
                    "status": draft.status,
                    "draftMarkdown": draft.draft_markdown,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("GenerateDraft error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return generate_draft


def _build_form_data(args: dict[str, Any]) -> ActaFormData:
    return ActaFormData(
        titulo=_as_string(args.get("titulo") or args.get("title")),
        fecha=_as_string(args.get("fecha") or args.get("date")),
        hora_inicio=_as_string(args.get("hora_inicio") or args.get("startTime")),
        hora_fin=_as_string(args.get("hora_fin") or args.get("endTime")),
        lugar=_as_string(args.get("lugar") or args.get("place")),
        participantes=_coerce_list(args.get("participantes") or args.get("participants")),
        objetivo=_as_string(args.get("objetivo") or args.get("objective")),
        antecedentes=_as_string(args.get("antecedentes") or args.get("background")),
        temas_tratados=_coerce_list(args.get("temas_tratados") or args.get("topics")),
        acuerdos=_coerce_list(args.get("acuerdos") or args.get("agreements")),
        compromisos=_coerce_list(args.get("compromisos") or args.get("commitments")),
        observaciones=_as_string(args.get("observaciones") or args.get("observations")),
    )


def _coerce_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value)]


def _as_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
