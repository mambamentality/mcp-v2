"""Tests de humo para los tools MCP.

Estos tests NO levantan el runtime de Azure Functions ni requieren Azurite:
llaman directamente a las funciones que registran los tools, pasándoles un
dict como si fuera el `context` ya parseado (ver tools/mcp_helpers.get_arguments,
que acepta tanto un JSON string real -como llega en producción- como un dict
-como se usa aquí-).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import azure.functions as func
import pytest

from tools.approve_draft import register_approve_draft_tool
from tools.ask_questions import register_ask_questions_tool
from tools.generate_docx import register_generate_docx_tool
from tools.generate_draft import register_generate_draft_tool
from tools.update_draft import register_update_draft_tool

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


def test_generate_draft_con_datos_directos(app):
    generate_draft = register_generate_draft_tool(app)
    result = _call(
        generate_draft,
        {
            "titulo": "Comité de Tecnología",
            "fecha": "2026-07-01",
            "participantes": ["Ana Perez", "Juan Gomez"],
            "objetivo": "Revisar avances del trimestre",
            "acuerdos": ["Escalar con proveedor", "Cerrar contrato"],
        },
    )

    assert "draftId" in result
    assert result["status"] == "pendingApproval"
    assert "Comité de Tecnología" in result["draftMarkdown"]


def test_ask_questions_devuelve_la_siguiente_pregunta(app):
    ask_questions = register_ask_questions_tool(app)

    result = _call(ask_questions, {"data": {"titulo": "Reunión de prueba"}})

    assert result["status"] == "question"
    assert result["field"] == "fecha"
    assert "fecha" in result["question"].lower()


def test_ask_questions_indica_cuando_termina(app):
    ask_questions = register_ask_questions_tool(app)

    result = _call(
        ask_questions,
        {
            "data": {
                "titulo": "Reunión de prueba",
                "fecha": "2026-07-06",
                "participantes": ["Ana"],
                "objetivo": "Revisar",
                "acuerdos": ["Acordado"],
            }
        },
    )

    assert result["status"] == "done"


def test_full_flow_hasta_generar_docx(app):
    generate_draft = register_generate_draft_tool(app)
    update_draft = register_update_draft_tool(app)
    approve_draft = register_approve_draft_tool(app)
    generate_docx = register_generate_docx_tool(app)

    draft = _call(
        generate_draft,
        {
            "titulo": "Comité de Tecnología",
            "fecha": "2026-07-01",
            "participantes": ["Ana Perez", "Juan Gomez"],
            "objetivo": "Revisar avances del trimestre",
            "acuerdos": ["Escalar con proveedor", "Cerrar contrato"],
        },
    )
    draft_id = draft["draftId"]

    updated = _call(update_draft, {"draftId": draft_id, "instruction": "agregar Nota final de prueba"})
    assert updated["draftUpdated"] is True
    assert "Nota final de prueba" in updated["draftMarkdown"]

    not_approved = _call(generate_docx, {"draftId": draft_id})
    assert not_approved["status"] == "error"

    approval = _call(approve_draft, {"draftId": draft_id})
    assert approval["approved"] is True

    docx_result = _call(generate_docx, {"draftId": draft_id})
    assert docx_result["status"] == "ok"
    assert docx_result["fileName"] == f"Acta_{draft_id}.docx"
    assert len(docx_result["fileBase64"]) > 0


def test_update_draft_borrador_aprobado_no_se_edita(app):
    generate_draft = register_generate_draft_tool(app)
    update_draft = register_update_draft_tool(app)
    approve_draft = register_approve_draft_tool(app)

    draft = _call(
        generate_draft,
        {
            "titulo": "Test",
            "fecha": "2026-01-01",
            "participantes": ["A", "B"],
            "objetivo": "Objetivo",
            "acuerdos": ["Acuerdo 1"],
        },
    )
    draft_id = draft["draftId"]

    _call(approve_draft, {"draftId": draft_id})
    result = _call(update_draft, {"draftId": draft_id, "instruction": "agregar algo"})

    assert result["draftUpdated"] is False


def test_tool_property_declarado_como_json_valido():
    """Los tools deben declarar tool_properties como JSON válido."""
    import tools.approve_draft as m4
    import tools.ask_questions as m6
    import tools.generate_docx as m5
    import tools.generate_draft as m2
    import tools.update_draft as m3

    for module in (m2, m3, m4, m5, m6):
        props = json.loads(module._TOOL_PROPERTIES)
        assert isinstance(props, list)
        assert len(props) > 0
        for prop in props:
            assert "propertyName" in prop
            assert "propertyType" in prop
