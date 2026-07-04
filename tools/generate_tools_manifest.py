#!/usr/bin/env python3
"""Genera un manifiesto estático `tools/tools_manifest.json` a partir de los
módulos en `tools/` para que IDEs/analizadores (p. ej. Copilot) puedan
descubrir las tools sin ejecutar el runtime.

El script busca en cada archivo Python de `tools/`:
- el decorador `@app.mcp_tool_trigger(..., tool_name="...")` para obtener el
  nombre de la tool y la descripción del decorator si existe.
- la asignación `_TOOL_PROPERTIES = tool_properties_json([...])` y extrae las
  llamadas a `ToolProperty(...)` para construir la lista de propiedades.

Uso:
  python tools/generate_tools_manifest.py

Salida: `tools/tools_manifest.json` con array de objetos { module, toolName,
description, properties }.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict


TOOLS_DIR = Path(__file__).resolve().parent


def extract_tool_metadata(text: str) -> Dict:
    # tool_name from decorator
    m_tool = re.search(r"@app\.mcp_tool_trigger\s*\([^\)]*tool_name\s*=\s*[\"']([^\"']+)[\"']", text, re.S)
    tool_name = m_tool.group(1) if m_tool else None

    # description from decorator (optional)
    m_desc = re.search(r"@app\.mcp_tool_trigger\s*\([^\)]*description\s*=\s*[\"']([^\"']+)[\"']", text, re.S)
    description = m_desc.group(1) if m_desc else ""

    properties: List[Dict] = []

    # intento extraer la lista pasada a tool_properties_json([...])
    m_props = re.search(r"_TOOL_PROPERTIES\s*=\s*tool_properties_json\s*\(\s*(\[[\s\S]*?\])\s*\)", text, re.S)
    if m_props:
        list_text = m_props.group(1)
        # extraer llamadas a ToolProperty("name", "type", "desc", isRequired=True)
        for m in re.finditer(
            r"ToolProperty\s*\(\s*([\"'])([^\"']+)\1\s*,\s*([\"'])([^\"']+)\3\s*(?:,\s*([\"'])([^\"']*)\5)?(?:\s*,\s*isRequired\s*=\s*(True|False))?(?:\s*,\s*isArray\s*=\s*(True|False))?",
            list_text,
        ):
            name = m.group(2)
            ptype = m.group(4)
            desc = m.group(6) or ""
            isRequired = (m.group(7) == "True") if m.group(7) else False
            isArray = (m.group(8) == "True") if m.group(8) else False
            properties.append(
                {
                    "propertyName": name,
                    "propertyType": ptype,
                    "description": desc,
                    "isRequired": isRequired,
                    "isArray": isArray,
                }
            )
    else:
        # fallback: buscar un literal JSON asignado a _TOOL_PROPERTIES
        m_json = re.search(r"_TOOL_PROPERTIES\s*=\s*(r?[\"']\s*\[.+?\]\s*[\"'])", text, re.S)
        if m_json:
            try:
                js = eval(m_json.group(1))
                properties = json.loads(js)
            except Exception:
                properties = []

    return {"toolName": tool_name, "description": description, "properties": properties}


def main() -> None:
    manifest: List[Dict] = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        if "mcp_tool_trigger" not in text:
            continue
        meta = extract_tool_metadata(text)
        if not meta.get("toolName"):
            # usar nombre del módulo si no hay tool_name explícito
            meta["toolName"] = path.stem
        meta["module"] = path.name
        manifest.append(meta)

    out = TOOLS_DIR / "tools_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} ({len(manifest)} tools)")


if __name__ == "__main__":
    main()
