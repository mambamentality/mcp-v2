# tools/update_acta_point.py — UpdateActaPoint
import json
import logging

import azure.functions as func

from .acta_draft_store import ActaDraftStore
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [
        ToolProperty("actaId", "string", "Id del acta a editar.", isRequired=True),
        ToolProperty("puntoNumero", "string", "Número del punto a modificar (ej. '4.2').", isRequired=False),
        ToolProperty("nuevaNarrativa", "string", "Nuevo texto narrativo para ese punto.", isRequired=False),
        ToolProperty("nuevaDeterminacion", "string", "Nuevo texto de determinación para ese punto.", isRequired=False),
        ToolProperty("nuevoNumeroActa", "string", "Corrige el número de acta sugerido.", isRequired=False),
    ]
)


def register_update_acta_point_tool(app: func.FunctionApp):
    store = ActaDraftStore()

    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="UpdateActaPoint",
        description="Modifica la narrativa/determinación de un punto, o el número de acta, antes de aprobar.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def update_acta_point(context) -> str:
        try:
            args = get_arguments(context)
            acta_id = args.get("actaId")
            if not acta_id:
                raise ValueError("Debe enviar 'actaId'.")

            acta = store.get_acta(str(acta_id))
            if acta is None:
                raise ValueError(f"Acta no encontrada: {acta_id}")
            if acta.get("status") == "approved":
                return json.dumps({"updated": False, "message": "El acta ya fue aprobada y no se puede editar."}, ensure_ascii=False)

            if args.get("nuevoNumeroActa"):
                acta["numeroActa"] = args["nuevoNumeroActa"]
                acta["numeroActaConfirmado"] = True
                store.save_acta(str(acta_id), acta)
                return json.dumps({"updated": True, "numeroActa": acta["numeroActa"]}, ensure_ascii=False)

            punto_numero = args.get("puntoNumero")
            if not punto_numero:
                raise ValueError("Debe enviar 'puntoNumero' (o 'nuevoNumeroActa').")

            point = _find_point(acta.get("ordenDelDia", []), str(punto_numero))
            if point is None:
                raise ValueError(f"Punto no encontrado: {punto_numero}")

            if args.get("nuevaNarrativa"):
                point["narrativa"] = args["nuevaNarrativa"]
            if args.get("nuevaDeterminacion"):
                point["determinacion"] = args["nuevaDeterminacion"]

            store.save_acta(str(acta_id), acta)
            return json.dumps({"updated": True, "punto": point}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("UpdateActaPoint error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return update_acta_point


def _find_point(points, numero: str):
    for point in points:
        if point.get("numero") == numero:
            return point
        found = _find_point(point.get("subpuntos", []), numero)
        if found:
            return found
    return None