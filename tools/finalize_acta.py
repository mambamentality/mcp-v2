# tools/finalize_acta.py — FinalizeActa (genera docx, sube a SharePoint, actualiza Maestra)
import base64
import io
import json
import logging
from pathlib import Path

import azure.functions as func
from docxtpl import DocxTemplate

from . import sharepoint_client, maestro_store
from .acta_draft_store import ActaDraftStore
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "acta_template.docx"

_TOOL_PROPERTIES = tool_properties_json(
    [ToolProperty("actaId", "string", "Id del acta aprobada.", isRequired=True)]
)


def register_finalize_acta_tool(app: func.FunctionApp):
    store = ActaDraftStore()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="FinalizeActa",
        description="Genera el .docx final, lo sube a SharePoint y actualiza el Acta Maestra. Requiere que el acta esté aprobada.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def finalize_acta(context) -> str:
        try:
            args = get_arguments(context)
            acta_id = args.get("actaId")
            if not acta_id:
                raise ValueError("Debe enviar 'actaId'.")

            acta = store.get_acta(str(acta_id))
            if acta is None:
                raise ValueError(f"Acta no encontrada: {acta_id}")
            if acta.get("status") != "approved":
                raise ValueError("El acta debe estar aprobada antes de finalizar.")

            doc = DocxTemplate(str(_TEMPLATE_PATH))
            doc.render(acta)
            buffer = io.BytesIO()
            doc.save(buffer)
            file_bytes = buffer.getvalue()
            file_name = f"Acta_Directorio_{acta.get('numeroActa', 's_n').replace('/', '-')}.docx"

            upload_folder = acta.get("outputFolder")
            if not upload_folder:
                raise ValueError("El acta no tiene 'outputFolder' calculado.")
            upload_result = sharepoint_client.upload_file(upload_folder, file_name, file_bytes)

            maestro_updates = _build_maestro_updates(acta.get("ordenDelDia", []))
            maestro_store.upsert_maestro_rows(maestro_updates)

            return json.dumps(
                {
                    "status": "ok",
                    "fileName": file_name,
                    "webUrl": upload_result.get("webUrl"),
                    "fileBase64": base64.b64encode(file_bytes).decode("ascii"),
                    "maestroActualizado": len(maestro_updates),
                },
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("FinalizeActa error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return finalize_acta


def _build_maestro_updates(points):
    updates = []

    def walk(node):
        if not node.get("subpuntos"):
            updates.append(
                {
                    "maestroId": node.get("maestroId"),
                    "titulo": node.get("titulo"),
                    "tipo": node.get("tipo", "complejo"),
                    "plantillaFrase": node.get("plantillaFrase", ""),
                    "narrativaAnterior": node.get("narrativa"),
                    "determinacionAnterior": node.get("determinacion"),
                    "ultimoCite": node.get("cite"),
                    "ultimaFecha": "",
                }
            )
        for sub in node.get("subpuntos", []):
            walk(sub)

    for p in points:
        walk(p)
    return updates