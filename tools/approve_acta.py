# tools/approve_acta.py — ApproveActa
import json
import logging
from datetime import datetime, timezone

import azure.functions as func

from .acta_draft_store import ActaDraftStore
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [ToolProperty("actaId", "string", "Id del acta a aprobar.", isRequired=True)]
)


def register_approve_acta_tool(app: func.FunctionApp):
    store = ActaDraftStore()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ApproveActa",
        description="Registra la aprobación formal del acta antes de convertirla a Word.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def approve_acta(context) -> str:
        try:
            args = get_arguments(context)
            acta_id = args.get("actaId")
            if not acta_id:
                raise ValueError("Debe enviar 'actaId'.")

            acta = store.get_acta(str(acta_id))
            if acta is None:
                raise ValueError(f"Acta no encontrada: {acta_id}")
            if acta.get("status") == "pendingModalidad":
                raise ValueError("Falta definir la modalidad de asistencia (SetAttendanceModality) antes de aprobar.")

            acta["status"] = "approved"
            acta["approvedAt"] = datetime.now(timezone.utc).isoformat()
            store.save_acta(str(acta_id), acta)

            return json.dumps({"approved": True, "approvalTimestamp": acta["approvedAt"]}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("ApproveActa error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return approve_acta