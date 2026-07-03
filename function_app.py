"""Servidor MCP para generación de actas bancarias."""

import logging

import azure.functions as func

from tools.acta_wizard import register_acta_wizard_tool
from tools.validate_acta import register_validate_acta_tool
from tools.generate_draft import register_generate_draft_tool
from tools.update_draft import register_update_draft_tool
from tools.approve_draft import register_approve_draft_tool
from tools.generate_docx import register_generate_docx_tool

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
logger = logging.getLogger(__name__)

register_acta_wizard_tool(app)
register_validate_acta_tool(app)
register_generate_draft_tool(app)
register_update_draft_tool(app)
register_approve_draft_tool(app)
register_generate_docx_tool(app)
