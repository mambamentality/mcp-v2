# tools/list_gestiones_tool.py — ListGestiones
import json
import logging

import azure.functions as func

from . import sharepoint_client, paths
from .mcp_helpers import get_arguments

logger = logging.getLogger(__name__)


def register_list_gestiones_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="ListGestiones",
        description="Lista las gestiones (años) disponibles con actas en SharePoint.",
        tool_properties="[]",
    )
    def list_gestiones(context) -> str:
        try:
            items = sharepoint_client.list_children(paths.list_gestiones())
            gestiones = [item["name"] for item in items if item["isFolder"]]
            return json.dumps({"status": "ok", "gestiones": gestiones}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("ListGestiones error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return list_gestiones