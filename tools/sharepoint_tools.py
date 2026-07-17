# tools/sharepoint_tools.py — SharePointListDirectory, SharePointFetchFile, SharePointUploadFile
import base64
import json
import logging

import azure.functions as func

from . import sharepoint_client
from .mcp_helpers import ToolProperty, get_arguments, tool_properties_json

logger = logging.getLogger(__name__)

_LIST_PROPS = tool_properties_json(
    [ToolProperty("folderPath", "string", "Ruta de la carpeta relativa a la raíz del sitio.", isRequired=True)]
)
_FETCH_PROPS = tool_properties_json(
    [ToolProperty("filePath", "string", "Ruta completa del archivo a descargar.", isRequired=True)]
)
_UPLOAD_PROPS = tool_properties_json(
    [
        ToolProperty("folderPath", "string", "Carpeta destino relativa a la raíz del sitio.", isRequired=True),
        ToolProperty("fileName", "string", "Nombre del archivo a crear.", isRequired=True),
        ToolProperty("fileBase64", "string", "Contenido del archivo codificado en base64.", isRequired=True),
    ]
)


def register_sharepoint_list_directory_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="SharePointListDirectory",
        description="Lista los archivos de una carpeta de gestión en SharePoint.",
        tool_properties=_LIST_PROPS,
    )
    def sharepoint_list_directory(context) -> str:
        try:
            args = get_arguments(context)
            folder_path = args.get("folderPath")
            if not folder_path:
                raise ValueError("Debe enviar 'folderPath'.")
            items = sharepoint_client.list_children(str(folder_path))
            return json.dumps({"status": "ok", "items": items}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("SharePointListDirectory error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return sharepoint_list_directory


def register_sharepoint_fetch_file_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="SharePointFetchFile",
        description="Descarga un archivo de SharePoint y lo devuelve en base64.",
        tool_properties=_FETCH_PROPS,
    )
    def sharepoint_fetch_file(context) -> str:
        try:
            args = get_arguments(context)
            file_path = args.get("filePath")
            if not file_path:
                raise ValueError("Debe enviar 'filePath'.")
            content = sharepoint_client.download_file(str(file_path))
            return json.dumps(
                {"status": "ok", "filePath": file_path, "fileBase64": base64.b64encode(content).decode("ascii")},
                ensure_ascii=False,
            )
        except Exception as exc:
            logger.exception("SharePointFetchFile error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return sharepoint_fetch_file


def register_sharepoint_upload_file_tool(app: func.FunctionApp):
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="SharePointUploadFile",
        description="Sube un archivo a una carpeta de SharePoint.",
        tool_properties=_UPLOAD_PROPS,
    )
    def sharepoint_upload_file(context) -> str:
        try:
            args = get_arguments(context)
            folder_path = args.get("folderPath")
            file_name = args.get("fileName")
            file_b64 = args.get("fileBase64")
            if not (folder_path and file_name and file_b64):
                raise ValueError("Debe enviar 'folderPath', 'fileName' y 'fileBase64'.")
            content = base64.b64decode(file_b64)
            result = sharepoint_client.upload_file(str(folder_path), str(file_name), content)
            return json.dumps({"status": "ok", "webUrl": result.get("webUrl"), "id": result.get("id")}, ensure_ascii=False)
        except Exception as exc:
            logger.exception("SharePointUploadFile error")
            return json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False)

    return sharepoint_upload_file