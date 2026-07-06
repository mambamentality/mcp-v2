import json
import logging
from typing import Any, Dict, List

import azure.functions as func

from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_FIELDS = [
    "titulo",
    "fecha",
    "hora_inicio",
    "hora_fin",
    "lugar",
    "participantes",
    "objetivo",
    "antecedentes",
    "temas_tratados",
    "acuerdos",
    "compromisos",
    "observaciones",
]

_REQUIRED_FIELDS = ["titulo", "fecha", "participantes", "objetivo", "acuerdos"]

_QUESTION_TEMPLATES = {
    "titulo": "¿Cuál es el título del acta?",
    "fecha": "¿Cuál es la fecha de la reunión?",
    "hora_inicio": "¿Cuál es la hora de inicio?",
    "hora_fin": "¿Cuál es la hora de fin?",
    "lugar": "¿Dónde se celebró la reunión?",
    "participantes": "¿Quiénes participaron?",
    "objetivo": "¿Cuál fue el objetivo de la reunión?",
    "antecedentes": "¿Qué antecedentes o contexto quieres incluir?",
    "temas_tratados": "¿Qué temas se trataron?",
    "acuerdos": "¿Qué acuerdos se alcanzaron?",
    "compromisos": "¿Qué compromisos quedaron?",
    "observaciones": "¿Hay alguna observación adicional?",
}

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("data", "string", "Datos ya recolectados del acta en formato JSON o dict.", isRequired=False),
    ]
)


def register_ask_questions_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="AskQuestions",
        description="Hace preguntas una por una para completar los datos del acta sin usar sesiones.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def ask_questions(context) -> str:
        try:
            args = get_arguments(context)
            data = args.get("data") or {}
            if isinstance(data, str):
                data = json.loads(data)
            if not isinstance(data, dict):
                data = {}

            next_field = _find_next_field(data)
            if next_field is None:
                return json.dumps({"status": "done", "data": data}, ensure_ascii=False)

            return json.dumps(
                {
                    "status": "question",
                    "field": next_field,
                    "question": _QUESTION_TEMPLATES[next_field],
                    "data": data,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("AskQuestions error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return ask_questions


def _find_next_field(data: Dict[str, Any]) -> str | None:
    for field in _REQUIRED_FIELDS:
        value = data.get(field)
        if value in (None, "", [], {}):
            return field
    return None

