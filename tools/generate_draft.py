import json
import logging

import azure.functions as func

from .draft_manager import DraftManager
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json
from .session_manager import ActaSessionManager

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("sessionId", "string", "Id de la sesión con los datos capturados.", isRequired=True),
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
    session_manager = ActaSessionManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="GenerateDraft",
        description="Genera un borrador de acta en Markdown a partir de los datos capturados.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def generate_draft(context) -> str:
        try:
            args = get_arguments(context)
            session_id = args.get("sessionId")
            extra_context = args.get("context")

            if not session_id:
                raise ValueError("Debe enviar 'sessionId'.")

            session = session_manager.get_session(str(session_id))
            if session is None:
                raise ValueError(f"Sesión no encontrada: {session_id}")

            draft = draft_manager.create_draft(session, extra_context)
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
