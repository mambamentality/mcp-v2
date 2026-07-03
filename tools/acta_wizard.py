import json
import logging

import azure.functions as func

from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json
from .session_manager import ActaSessionManager

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty(
            "action",
            "string",
            "Acción a ejecutar: create_session | retrieve_session | save_responses. "
            "Por defecto create_session.",
            isRequired=False,
        ),
        ToolProperty(
            "sessionId",
            "string",
            "Id de la sesión existente. Requerido para retrieve_session y save_responses.",
            isRequired=False,
        ),
        ToolProperty(
            "responses",
            "object",
            "Diccionario campo -> valor con las respuestas capturadas (usado en save_responses).",
            isRequired=False,
        ),
    ]
)


def register_acta_wizard_tool(app: func.FunctionApp):
    manager = ActaSessionManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ActaWizard",
        description="Administra el flujo de captura de datos para crear un acta.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def acta_wizard(context) -> str:
        try:
            args = get_arguments(context)
            action = str(args.get("action", "create_session")).strip()

            if action == "create_session":
                session = manager.create_session()
                next_field = manager.determine_next_field(session)
                question = manager.build_next_question(session)
                return json.dumps(
                    {
                        "sessionId": session.session_id,
                        "status": session.status,
                        "nextField": next_field,
                        "question": question,
                    },
                    ensure_ascii=False,
                )

            session_id = args.get("sessionId")
            if not session_id:
                raise ValueError("Debe enviar 'sessionId'.")

            session = manager.get_session(str(session_id))
            if session is None:
                raise ValueError(f"Sesión no encontrada: {session_id}")

            if action == "retrieve_session":
                next_field = manager.determine_next_field(session)
                question = manager.build_next_question(session)
                payload = session.to_dict()
                payload.update({"nextField": next_field, "question": question})
                return json.dumps(payload, ensure_ascii=False)

            if action == "save_responses":
                responses = args.get("responses") or args.get("answers") or {}
                if not isinstance(responses, dict):
                    raise ValueError("'responses' debe ser un objeto JSON.")
                session = manager.save_responses(str(session_id), responses)
                if session is None:
                    raise ValueError(f"Sesión no encontrada: {session_id}")
                next_field = manager.determine_next_field(session)
                question = manager.build_next_question(session)
                return json.dumps(
                    {
                        "sessionId": session.session_id,
                        "status": session.status,
                        "nextField": next_field,
                        "question": question,
                    },
                    ensure_ascii=False,
                )

            raise ValueError(f"Acción inválida para ActaWizard: {action}")
        except Exception as exc:
            logger.exception("ActaWizard error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return acta_wizard
