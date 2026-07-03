"""Utilidades compartidas para los tools MCP.

La documentación oficial del `mcp_tool_trigger` de Azure Functions (Python v2)
indica que el argumento del trigger (normalmente llamado `context`) llega como
un JSON string con la forma:

    {"name": "<tool_name>", "arguments": {...}, "sessionId": "...", ...}

y que cada tool debe declarar explícitamente sus `tool_properties` (un JSON
con la lista de propiedades) para que el cliente MCP sepa qué argumentos
puede/debe enviar. Ver:
https://learn.microsoft.com/azure/azure-functions/functions-bindings-mcp-tool-trigger

Este módulo centraliza ambas cosas para no repetir boilerplate en cada tool.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolProperty:
    propertyName: str
    propertyType: str
    description: str = ""
    isRequired: bool = False
    isArray: bool = False


def tool_properties_json(properties: List[ToolProperty]) -> str:
    """Serializa una lista de ToolProperty al JSON que espera `tool_properties`."""
    return json.dumps([prop.__dict__ for prop in properties], ensure_ascii=False)


def get_arguments(context: Any) -> Dict[str, Any]:
    """Extrae el dict de argumentos desde el ToolInvocationContext.

    - En producción/local con `func start`, `context` llega como JSON string.
    - En tests unitarios (ver tests/test_tools.py) se invoca a los tools
      pasando directamente un dict, para no depender del runtime de Azure.
      Por eso este helper acepta ambos casos.
    """
    if context is None:
        return {}
    if isinstance(context, dict):
        # Ya es un dict de argumentos (tests) o ya es el objeto completo.
        return context.get("arguments", context)
    if isinstance(context, (bytes, bytearray)):
        context = context.decode("utf-8")
    parsed = json.loads(context)
    return parsed.get("arguments", parsed)
