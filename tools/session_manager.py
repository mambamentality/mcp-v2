from __future__ import annotations

import re
from typing import Dict, List, Optional

from .schemas import ActaFormData, ActaSession
from .storage import SessionStore

FIELD_ORDER = [
    "titulo",
    "fecha",
    "hora_inicio",
    "hora_fin",
    "lugar",
    "participantes",
    "objetivo",
    "antecedentes",
    "temas_tratados",
    "acuerdos",
    "compromisos",
    "observaciones",
]

REQUIRED_FIELDS = ["titulo", "fecha", "participantes", "objetivo", "acuerdos"]

FIELD_QUESTIONS = {
    "titulo": "¿Cuál es el título del acta?",
    "fecha": "¿Cuál es la fecha de la reunión?",
    "hora_inicio": "¿A qué hora comenzó la reunión?",
    "hora_fin": "¿A qué hora finalizó la reunión?",
    "lugar": "¿Dónde se realizó la reunión?",
    "participantes": "¿Quiénes participaron en la reunión? Enumera los nombres separados por comas o líneas nuevas.",
    "objetivo": "¿Cuál fue el objetivo principal de la reunión?",
    "antecedentes": "¿Qué antecedentes se deben registrar?",
    "temas_tratados": "¿Qué temas se trataron durante la reunión? Indícalos como lista.",
    "acuerdos": "¿Qué acuerdos se alcanzaron? Enumera los acuerdos clave.",
    "compromisos": "¿Qué compromisos se asumieron? Enumera los compromisos clave.",
    "observaciones": "¿Hay observaciones adicionales que debamos registrar?",
}


class ActaSessionManager:
    def __init__(self):
        self.store = SessionStore()

    def create_session(self) -> ActaSession:
        session = ActaSession()
        self.store.save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ActaSession]:
        return self.store.get_session(session_id)

    def save_responses(self, session_id: str, responses: Dict[str, object]) -> Optional[ActaSession]:
        session = self.get_session(session_id)
        if session is None:
            return None

        for key, raw_value in responses.items():
            if not hasattr(session.data, key):
                continue
            normalized = self._normalize_field_value(key, raw_value)
            setattr(session.data, key, normalized)

        session.touch()
        self.store.save_session(session)
        return session

    def get_missing_fields(self, session: ActaSession) -> List[str]:
        missing = []
        for field in REQUIRED_FIELDS:
            value = getattr(session.data, field)
            if self._is_empty(value):
                missing.append(field)
        return missing

    def determine_next_field(self, session: ActaSession) -> str:
        for field in REQUIRED_FIELDS:
            if self._is_empty(getattr(session.data, field)):
                return field

        for field in FIELD_ORDER:
            if self._is_empty(getattr(session.data, field)):
                return field

        return "complete"

    def build_next_question(self, session: ActaSession) -> str:
        next_field = self.determine_next_field(session)
        if next_field == "complete":
            return (
                "Todos los campos han sido completados. Ahora puedes validar el acta con ValidateActa o generar el borrador con GenerateDraft."
            )
        return FIELD_QUESTIONS.get(next_field, "¿Cuál es la siguiente información?")

    @staticmethod
    def _normalize_field_value(field: str, raw_value: object) -> object:
        if field in {"participantes", "temas_tratados", "acuerdos", "compromisos"}:
            if isinstance(raw_value, str):
                items = re.split(r"[,\n;]+", raw_value)
                return [item.strip() for item in items if item.strip()]
            if isinstance(raw_value, list):
                return [str(item).strip() for item in raw_value if str(item).strip()]
            return [str(raw_value)]

        if isinstance(raw_value, str):
            return raw_value.strip()

        return raw_value

    @staticmethod
    def _is_empty(value: object) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ""
        if isinstance(value, list):
            return len(value) == 0
        return False
