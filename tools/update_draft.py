import json
import logging

import azure.functions as func

from .draft_manager import DraftManager
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("draftId", "string", "Id del borrador a modificar.", isRequired=True),
        ToolProperty(
            "instruction",
            "string",
            "Instrucción en texto libre sobre qué cambiar en el borrador "
            "(p. ej. \"reemplazar 'X' por 'Y'\", \"agregar ...\").",
            isRequired=True,
        ),
    ]
)


def register_update_draft_tool(app: func.FunctionApp):
    manager = DraftManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="UpdateDraft",
        description="Permite modificar el borrador generado del acta.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def update_draft(context) -> str:
        try:
            args = get_arguments(context)
            draft_id = args.get("draftId")
            instruction = args.get("instruction")

            if not draft_id:
                raise ValueError("Debe enviar 'draftId'.")
            if not instruction:
                raise ValueError("Debe enviar 'instruction'.")

            draft = manager.update_draft(str(draft_id), str(instruction))
            if draft is None:
                raise ValueError(f"Borrador no encontrado: {draft_id}")
            if draft.status == "approved":
                return json.dumps(
                    {
                        "draftUpdated": False,
                        "draftMarkdown": draft.draft_markdown,
                        "message": "El borrador ya fue aprobado y no se puede editar.",
                    },
                    ensure_ascii=False,
                )

            return json.dumps(
                {"draftUpdated": True, "draftMarkdown": draft.draft_markdown},
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("UpdateDraft error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return update_draft
