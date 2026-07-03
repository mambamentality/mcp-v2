import json
import logging

import azure.functions as func

from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json
from .session_manager import ActaSessionManager

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("sessionId", "string", "Id de la sesión a validar.", isRequired=True),
    ]
)


def register_validate_acta_tool(app: func.FunctionApp):
    manager = ActaSessionManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ValidateActa",
        description="Valida que los campos obligatorios del acta estén completos.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def validate_acta(context) -> str:
        try:
            args = get_arguments(context)
            session_id = args.get("sessionId")
            if not session_id:
                raise ValueError("Debe enviar 'sessionId'.")

            session = manager.get_session(str(session_id))
            if session is None:
                raise ValueError(f"Sesión no encontrada: {session_id}")

            missing_fields = manager.get_missing_fields(session)
            return json.dumps(
                {
                    "complete": len(missing_fields) == 0,
                    "missingFields": missing_fields,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("ValidateActa error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return validate_acta
