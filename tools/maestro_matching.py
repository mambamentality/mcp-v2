# tools/maestro_matching.py — lógica de fuzzy matching compartida
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List
from uuid import uuid4

_DATE_NUMBER_RE = re.compile(r"\bal\s+\d{1,2}[./]\d{1,2}[./]\d{2,4}\b|\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b", re.IGNORECASE)


def _normalize(titulo: str) -> str:
    text = titulo.lower().strip()
    text = _DATE_NUMBER_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio()


def match_to_maestro(
    puntos: List[Dict[str, Any]],
    maestro_rows: List[Dict[str, Any]],
    umbral_alto: float = 0.85,
    umbral_bajo: float = 0.6,
) -> List[Dict[str, Any]]:
    """Recorre recursivamente los puntos (incluye subpuntos) y les agrega
    maestroId/maestroEstado/tipo/plantillaFrase/narrativaAnterior/determinacionAnterior."""

    def match_node(node: Dict[str, Any]) -> Dict[str, Any]:
        best, best_score = None, 0.0
        for row in maestro_rows:
            score = _similarity(node["titulo"], row.get("titulo", ""))
            if score > best_score:
                best, best_score = row, score

        if best and best_score >= umbral_alto:
            node["maestroId"] = best["maestroId"]
            node["maestroEstado"] = "asignado_automatico"
        elif best and best_score >= umbral_bajo:
            node["maestroId"] = best["maestroId"]
            node["maestroEstado"] = "requiere_confirmacion"
        else:
            node["maestroId"] = str(uuid4())
            node["maestroEstado"] = "punto_nuevo"
            best = None

        if best:
            node["tipo"] = best.get("tipo", "complejo")
            node["plantillaFrase"] = best.get("plantillaFrase", "")
            node["narrativaAnterior"] = best.get("narrativaAnterior", "")
            node["determinacionAnterior"] = best.get("determinacionAnterior", "")
        else:
            node["tipo"] = "complejo"
            node["plantillaFrase"] = ""
            node["narrativaAnterior"] = ""
            node["determinacionAnterior"] = ""

        node["subpuntos"] = [match_node(dict(s)) for s in node.get("subpuntos", [])]
        return node

    return [match_node(dict(p)) for p in puntos]