# tools/match_agenda_to_maestra.py — MatchAgendaToMaestra (standalone, para debug/uso manual)
import json
import logging
from typing import Any, Dict, List

import azure.functions as func

from . import maestro_store
from .maestro_matching import match_to_maestro
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("puntosConvocatoria", "object", "Lista de puntos extraídos por ExtractConvocatoria.", isRequired=True),
        ToolProperty("umbralAlto", "number", "Score mínimo (0-1) para asignar automático. Default 0.85.", isRequired=False),
        ToolProperty("umbralBajo", "number", "Score mínimo (0-1) para posible match. Default 0.6.", isRequired=False),
    ]
)


def register_match_agenda_to_maestra_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="MatchAgendaToMaestra",
        description="Identifica a qué punto de la Acta Maestra corresponde cada punto de la convocatoria actual.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def match_agenda_to_maestra(context) -> str:
        try:
            args = get_arguments(context)
            puntos = _as_list(args.get("puntosConvocatoria"))
            umbral_alto = float(args.get("umbralAlto", 0.85))
            umbral_bajo = float(args.get("umbralBajo", 0.6))

            maestro_rows = maestro_store.read_maestro()
            resultado = match_to_maestro(puntos, maestro_rows, umbral_alto, umbral_bajo)
            return json.dumps({"status": "ok", "matches": resultado}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("MatchAgendaToMaestra error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return match_agenda_to_maestra


def _as_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, str):
        return json.loads(value)
    return value or []