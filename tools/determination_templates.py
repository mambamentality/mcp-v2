# tools/determination_templates.py — fallback SOLO para puntos sin historial en la Maestra
from __future__ import annotations

import re
from typing import Optional

_TEMPLATES = [
    (r"informe", "El Directorio tomó conocimiento del informe presentado, cite {cite}."),
    (r"seguimiento", "El Directorio tomó conocimiento del seguimiento reportado, cite {cite}."),
    (r"aprob", "El Directorio aprobó el informe presentado, cite {cite}."),
    (r"reprogramaci", "El Directorio tomó conocimiento del informe y determinó se apliquen las medidas y acciones necesarias, cite {cite}."),
]
_DEFAULT = "El Directorio tomó conocimiento del informe presentado, cite {cite}."


def get_determination(titulo: str, cite: Optional[str]) -> str:
    cite_text = cite or "s/n"
    for pattern, template in _TEMPLATES:
        if re.search(pattern, titulo, re.IGNORECASE):
            return template.format(cite=cite_text)
    return _DEFAULT.format(cite=cite_text)