# tools/list_directorios_tool.py — ListDirectorios
import json
import logging

import azure.functions as func

from . import sharepoint_client, paths
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_TOOL_PROPERTIES = tool_properties_json(
    [ToolProperty("gestion", "string", "Año de gestión (ej. '2026').", isRequired=True)]
)


def register_list_directorios_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ListDirectorios",
        description="Lista los directorios (sesiones) disponibles dentro de una gestión.",
        tool_properties=_TOOL_PROPERTIES,
    )
    def list_directorios(context) -> str:
        try:
            args = get_arguments(context)
            gestion = args.get("gestion")
            if not gestion:
                raise ValueError("Debe enviar 'gestion'.")
            items = sharepoint_client.list_children(paths.list_directorios(gestion))
            directorios = [item["name"] for item in items if item["isFolder"]]
            return json.dumps({"status": "ok", "directorios": directorios}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("ListDirectorios error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return list_directorios