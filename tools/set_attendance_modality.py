# tools/set_attendance_modality.py — SetAttendanceModality (pendingModalidad -> pendingApproval)
import json
import logging
from typing import Any, Dict

import azure.functions as func

from .acta_draft_store import ActaDraftStore
from .intro_paragraph_builder import build_intro_fields
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("actaId", "string", "Id del acta.", isRequired=True),
        ToolProperty("modalidadPorPersona", "object", "Diccionario nombre -> 'presencial'|'virtual'.", isRequired=True),
    ]
)


def register_set_attendance_modality_tool(app: func.FunctionApp):
    store = ActaDraftStore()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="SetAttendanceModality",
        description="Define la modalidad (presencial/virtual) de cada asistente antes de aprobar el acta.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def set_attendance_modality(context) -> str:
        try:
            args = get_arguments(context)
            acta_id = args.get("actaId")
            modalidad_map = args.get("modalidadPorPersona")
            if isinstance(modalidad_map, str):
                modalidad_map = json.loads(modalidad_map)
            if not acta_id or not modalidad_map:
                raise ValueError("Debe enviar 'actaId' y 'modalidadPorPersona'.")

            acta = store.get_acta(str(acta_id))
            if acta is None:
                raise ValueError(f"Acta no encontrada: {acta_id}")

            for persona in acta.get("asistentes", []):
                nombre = persona.get("nombre")
                if nombre in modalidad_map:
                    persona["modalidad"] = modalidad_map[nombre]

            acta.update(build_intro_fields(acta))
            acta["status"] = "pendingApproval"
            store.save_acta(str(acta_id), acta)

            return json.dumps({"status": "ok", "actaStatus": acta["status"]}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("SetAttendanceModality error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return set_attendance_modality