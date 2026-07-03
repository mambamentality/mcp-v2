import json
import logging

import azure.functions as func

from .draft_manager import DraftManager
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("draftId", "string", "Id del borrador a aprobar.", isRequired=True),
    ]
)


def register_approve_draft_tool(app: func.FunctionApp):
    manager = DraftManager()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ApproveDraft",
        description="Registra la aprobación formal del borrador de acta.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def approve_draft(context) -> str:
        try:
            args = get_arguments(context)
            draft_id = args.get("draftId")
            if not draft_id:
                raise ValueError("Debe enviar 'draftId'.")

            draft = manager.approve_draft(str(draft_id))
            if draft is None:
                raise ValueError(f"Borrador no encontrado: {draft_id}")

            return json.dumps(
                {
                    "approved": True,
                    "approvalTimestamp": draft.approved_at.isoformat() if draft.approved_at else None,
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("ApproveDraft error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return approve_draft
