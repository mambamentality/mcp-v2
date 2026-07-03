"""Tests de humo para los tools MCP.

Estos tests NO levantan el runtime de Azure Functions ni requieren Azurite:
llaman directamente a las funciones que registran los tools, pasándoles un
dict como si fuera el `context` ya parseado (ver tools/mcp_helpers.get_arguments,
que acepta tanto un JSON string real -como llega en producción- como un dict
-como se usa aquí-).

Correr con:
    cd actas-mcp
    pip install -r requirements.txt
    pytest -v
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import azure.functions as func
import pytest

from tools.acta_wizard import register_acta_wizard_tool
from tools.approve_draft import register_approve_draft_tool
from tools.generate_docx import register_generate_docx_tool
from tools.generate_draft import register_generate_draft_tool
from tools.update_draft import register_update_draft_tool
from tools.validate_acta import register_validate_acta_tool

DATA_DIR = Path(__file__).resolve().parent.parent / ".data"


@pytest.fixture(autouse=True)
def clean_data_dir():
    """Aísla cada test limpiando el store JSON local antes y después."""
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    yield
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)


@pytest.fixture()
def app() -> func.FunctionApp:
    return func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def _call(tool_fn, arguments: dict) -> dict:
    """Invoca un tool simulando el ToolInvocationContext ya parseado."""
    raw = tool_fn({"arguments": arguments})
    return json.loads(raw)


def test_acta_wizard_create_session(app):
    acta_wizard = register_acta_wizard_tool(app)
    result = _call(acta_wizard, {"action": "create_session"})

    assert "sessionId" in result
    assert result["status"] == "in_progress"
    assert result["nextField"] == "titulo"


def test_full_flow_hasta_generar_docx(app):
    acta_wizard = register_acta_wizard_tool(app)
    validate_acta = register_validate_acta_tool(app)
    generate_draft = register_generate_draft_tool(app)
    update_draft = register_update_draft_tool(app)
    approve_draft = register_approve_draft_tool(app)
    generate_docx = register_generate_docx_tool(app)

    # 1. Crear sesión
    session = _call(acta_wizard, {"action": "create_session"})
    session_id = session["sessionId"]

    # 2. Cargar los campos obligatorios
    responses = {
        "titulo": "Comité de Tecnología",
        "fecha": "2026-07-01",
        "participantes": "Ana Perez, Juan Gomez",
        "objetivo": "Revisar avances del trimestre",
        "acuerdos": "Escalar con proveedor, Cerrar contrato",
    }
    saved = _call(acta_wizard, {"action": "save_responses", "sessionId": session_id, "responses": responses})
    assert saved["sessionId"] == session_id

    # 3. Validar -> debe estar completo
    validation = _call(validate_acta, {"sessionId": session_id})
    assert validation["complete"] is True
    assert validation["missingFields"] == []

    # 4. Generar borrador
    draft = _call(generate_draft, {"sessionId": session_id})
    draft_id = draft["draftId"]
    assert "Comité de Tecnología" in draft["draftMarkdown"]

    # 5. Editar el borrador
    updated = _call(update_draft, {"draftId": draft_id, "instruction": "agregar Nota final de prueba"})
    assert updated["draftUpdated"] is True
    assert "Nota final de prueba" in updated["draftMarkdown"]

    # 6. GenerateDocx debe fallar si el borrador no está aprobado
    not_approved = _call(generate_docx, {"draftId": draft_id})
    assert not_approved["status"] == "error"

    # 7. Aprobar
    approval = _call(approve_draft, {"draftId": draft_id})
    assert approval["approved"] is True

    # 8. Ahora sí debe generar el docx y devolverlo en base64
    docx_result = _call(generate_docx, {"draftId": draft_id})
    assert docx_result["status"] == "ok"
    assert docx_result["fileName"] == f"Acta_{draft_id}.docx"
    assert len(docx_result["fileBase64"]) > 0


def test_validate_acta_con_campos_faltantes(app):
    acta_wizard = register_acta_wizard_tool(app)
    validate_acta = register_validate_acta_tool(app)

    session = _call(acta_wizard, {"action": "create_session"})
    result = _call(validate_acta, {"sessionId": session["sessionId"]})

    assert result["complete"] is False
    assert "titulo" in result["missingFields"]


def test_update_draft_borrador_aprobado_no_se_edita(app):
    acta_wizard = register_acta_wizard_tool(app)
    generate_draft = register_generate_draft_tool(app)
    update_draft = register_update_draft_tool(app)
    approve_draft = register_approve_draft_tool(app)

    session = _call(acta_wizard, {"action": "create_session"})
    session_id = session["sessionId"]
    _call(
        acta_wizard,
        {
            "action": "save_responses",
            "sessionId": session_id,
            "responses": {
                "titulo": "Test",
                "fecha": "2026-01-01",
                "participantes": "A, B",
                "objetivo": "Objetivo",
                "acuerdos": "Acuerdo 1",
            },
        },
    )
    draft = _call(generate_draft, {"sessionId": session_id})
    draft_id = draft["draftId"]

    _call(approve_draft, {"draftId": draft_id})
    result = _call(update_draft, {"draftId": draft_id, "instruction": "agregar algo"})

    assert result["draftUpdated"] is False


def test_tool_property_declarado_como_json_valido():
    """Los 6 tools deben declarar tool_properties como JSON válido (regresión del bug original)."""
    import tools.acta_wizard as m1
    import tools.approve_draft as m4
    import tools.generate_docx as m5
    import tools.generate_draft as m2
    import tools.update_draft as m3
    import tools.validate_acta as m6

    for module in (m1, m2, m3, m4, m5, m6):
        props = json.loads(module._TOOL_PROPERTIES)
        assert isinstance(props, list)
        assert len(props) > 0
        for prop in props:
            assert "propertyName" in prop
            assert "propertyType" in prop
