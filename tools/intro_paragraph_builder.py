# tools/intro_paragraph_builder.py
"""Arma los párrafos fijos de apertura del acta (asistencia, presidencia,
modalidad) en Python, no con LLM."""
from __future__ import annotations

from typing import Any, Dict, List


def _agrupar_por_modalidad(personas: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    grupos = {"presencial": [], "virtual": []}
    for p in personas:
        if p.get("asistio") and p.get("modalidad") in grupos:
            grupos[p["modalidad"]].append(p["nombre"])
    return grupos


def _frase_grupo(nombres: List[str]) -> str:
    if not nombres:
        return ""
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + f" y {nombres[-1]}"


def build_intro_fields(acta_data: Dict[str, Any]) -> Dict[str, Any]:
    asistentes = acta_data.get("asistentes", [])

    def por_rol(rol: str) -> List[Dict[str, Any]]:
        return [a for a in asistentes if a.get("rol") == rol]

    directores = _agrupar_por_modalidad(por_rol("Directores/as"))
    fiscalizacion = _agrupar_por_modalidad(por_rol("Comisión Fiscalizadora"))
    gerencia = _agrupar_por_modalidad(por_rol("Alta Gerencia"))
    administracion = _agrupar_por_modalidad(por_rol("Administración"))

    partes_directores = []
    if directores["presencial"]:
        partes_directores.append(f"{_frase_grupo(directores['presencial'])}, quienes asistieron de manera presencial")
    if directores["virtual"]:
        conector = "mientras que" if partes_directores else ""
        partes_directores.append(f"{conector} {_frase_grupo(directores['virtual'])}, concurrieron mediante videoconferencia".strip())
    parrafo_directores = (
        "Participaron de la presente sesión los/as Directores/as: " + ", ".join(partes_directores) + "."
        if partes_directores else ""
    )

    parrafo_fiscalizacion = (
        f"De la misma manera, participó de la reunión la Comisión Fiscalizadora, compuesta por "
        f"{_frase_grupo(fiscalizacion['presencial'] + fiscalizacion['virtual'])}, quienes asistieron presencialmente."
        if (fiscalizacion["presencial"] or fiscalizacion["virtual"]) else ""
    )

    parrafo_gerencia = (
        f"Se convocó a esta reunión a los/as siguientes miembros de la Alta Gerencia, quienes "
        f"participaron presencialmente, con voz pero sin voto, {_frase_grupo(gerencia['presencial'])}."
        if gerencia["presencial"] else ""
    )

    parrafo_administracion = (
        f"Asimismo, por parte de la Administración asistieron presencialmente {_frase_grupo(administracion['presencial'])}."
        if administracion["presencial"] else ""
    )

    hay_virtuales = bool(directores["virtual"] or fiscalizacion["virtual"])
    presidenta_nombre = acta_data.get("presidenta", "")

    return {
        "parrafoDirectores": parrafo_directores,
        "parrafoFiscalizacion": parrafo_fiscalizacion,
        "parrafoAltaGerencia": parrafo_gerencia,
        "parrafoAdministracion": parrafo_administracion,
        "hayVirtuales": hay_virtuales,
        "modalidadSesionTexto": "de forma presencial y mediante videoconferencia" if hay_virtuales else "de forma presencial",
        "presidenciaTexto": f"de la señora {presidenta_nombre}" if presidenta_nombre else "",
        "presidentaModalidadTexto": "presencialmente",
    }