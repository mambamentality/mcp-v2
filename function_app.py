# function_app.py — registro final completo
"""Servidor MCP para generación de actas bancarias."""
import logging

import azure.functions as func

# Tools originales (modo manual, se mantienen como fallback)
from tools.ask_questions import register_ask_questions_tool
from tools.generate_draft import register_generate_draft_tool
from tools.update_draft import register_update_draft_tool
from tools.approve_draft import register_approve_draft_tool
from tools.generate_docx import register_generate_docx_tool

# Pipeline nuevo (SharePoint + extracción + Acta Maestra)
from tools.sharepoint_tools import (
    register_sharepoint_list_directory_tool,
    register_sharepoint_fetch_file_tool,
    register_sharepoint_upload_file_tool,
)
from tools.list_gestiones_tool import register_list_gestiones_tool
from tools.list_directorios_tool import register_list_directorios_tool
from tools.extract_convocatoria import register_extract_convocatoria_tool
from tools.extract_attendance import register_extract_attendance_tool
from tools.extract_backup_content import register_extract_backup_content_tool
from tools.match_backup_to_agenda import register_match_backup_to_agenda_tool
from tools.match_agenda_to_maestra import register_match_agenda_to_maestra_tool
from tools.orchestrate_acta import register_process_gestion_directory_tool
from tools.set_attendance_modality import register_set_attendance_modality_tool
from tools.update_acta_point import register_update_acta_point_tool
from tools.approve_acta import register_approve_acta_tool
from tools.finalize_acta import register_finalize_acta_tool

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger(__name__)

register_ask_questions_tool(app)
register_generate_draft_tool(app)
register_update_draft_tool(app)
register_approve_draft_tool(app)
register_generate_docx_tool(app)

register_sharepoint_list_directory_tool(app)
register_sharepoint_fetch_file_tool(app)
register_sharepoint_upload_file_tool(app)
register_list_gestiones_tool(app)
register_list_directorios_tool(app)
register_extract_convocatoria_tool(app)
register_extract_attendance_tool(app)
register_extract_backup_content_tool(app)
register_match_backup_to_agenda_tool(app)
register_match_agenda_to_maestra_tool(app)
register_process_gestion_directory_tool(app)
register_set_attendance_modality_tool(app)
register_update_acta_point_tool(app)
register_approve_acta_tool(app)
register_finalize_acta_tool(app)


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse("ok", status_code=200)