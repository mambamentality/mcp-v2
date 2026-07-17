# tools/narrative_filler.py — decide simple (plantilla, sin LLM) vs complejo (LLM)
from __future__ import annotations

from typing import Any, Dict, List

from .llm_narrative_service import generate_point_narrative, generate_point_determination
from .determination_templates import get_determination


def fill_narratives(points: List[Dict[str, Any]], fecha_corte: str = "", mes: str = "", periodo: str = "") -> None:
    for point in points:
        if not point.get("subpuntos"):
            if point.get("tipo") == "simple" and point.get("plantillaFrase"):
                point["narrativa"] = point["plantillaFrase"].format(
                    cite=point.get("cite") or "s/n",
                    fecha_corte=fecha_corte,
                    mes=mes,
                    periodo=periodo,
                )
                plantilla_det = point.get("determinacionAnterior") or ""
                point["determinacion"] = plantilla_det.format(
                    cite=point.get("cite") or "s/n",
                    fecha_corte=fecha_corte,
                    mes=mes,
                    periodo=periodo,
                ) if plantilla_det else get_determination(point.get("titulo", ""), point.get("cite"))
            else:
                point["narrativa"] = generate_point_narrative(
                    titulo_punto=point.get("titulo", ""),
                    expositor=point.get("expositor", ""),
                    cite=point.get("cite", ""),
                    texto_respaldo=point.get("textoRespaldo", ""),
                    narrativa_anterior=point.get("narrativaAnterior"),
                )
                point["determinacion"] = (
                    generate_point_determination(
                        titulo_punto=point.get("titulo", ""),
                        cite=point.get("cite", ""),
                        determinacion_anterior=point.get("determinacionAnterior"),
                    )
                    if point.get("determinacionAnterior")
                    else get_determination(point.get("titulo", ""), point.get("cite"))
                )
        else:
            fill_narratives(point["subpuntos"], fecha_corte, mes, periodo)