"""Servidor MCP para generación de actas bancarias."""

import logging

import azure.functions as func

from tools.validate_acta import register_validate_acta_tool
from tools.generate_draft import register_generate_draft_tool
from tools.update_draft import register_update_draft_tool
from tools.approve_draft import register_approve_draft_tool
from tools.generate_docx import register_generate_docx_tool

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger(__name__)

register_validate_acta_tool(app)
register_generate_draft_tool(app)
register_update_draft_tool(app)
register_approve_draft_tool(app)
register_generate_docx_tool(app)


@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health(req: func.HttpRequest) -> func.HttpResponse:
	"""Ruta de healthcheck rápida para verificar que el worker/Python se cargó."""
	return func.HttpResponse("ok", status_code=200)
