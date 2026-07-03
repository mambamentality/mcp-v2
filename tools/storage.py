from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

from .schemas import ActaSession, Draft


class JsonStore:
    """Store simple basado en un archivo JSON local.

    NOTA para producción: en Azure Functions (especialmente en el plan
    Consumption) el filesystem local no está garantizado entre reinicios ni
    entre instancias cuando hay más de una. Esto es suficiente para correr
    `func start` localmente y para pruebas, pero antes de desplegar a Azure
    con más de una instancia conviene reemplazar este store por Azure Table
    Storage / Cosmos DB / Blob Storage.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def _load(self) -> Dict[str, Dict]:
        if not self.file_path.exists():
            return {}
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    def _save(self, data: Dict[str, Dict]) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def get(self, key: str) -> Optional[Dict]:
        # Releemos el archivo en cada get() en vez de cachear en memoria:
        # cada tool crea su propio manager/store (ver acta_wizard.py,
        # validate_acta.py, etc.), así que dos instancias distintas necesitan
        # ver los datos que la otra acaba de guardar. Es el fix a un bug real
        # detectado con los tests de tests/test_tools.py (sesión "no encontrada"
        # al validarla justo después de crearla desde otro tool).
        with self._lock:
            return self._load().get(key)

    def set(self, key: str, value: Dict) -> None:
        with self._lock:
            data = self._load()
            data[key] = value
            self._save(data)


class SessionStore(JsonStore):
    def __init__(self):
        root = Path(__file__).resolve().parent.parent
        super().__init__(root / ".data" / "sessions.json")

    def save_session(self, session: ActaSession) -> None:
        self.set(session.session_id, session.to_dict())

    def get_session(self, session_id: str) -> Optional[ActaSession]:
        raw = self.get(session_id)
        if raw is None:
            return None
        return ActaSession.model_validate(raw)


class DraftStore(JsonStore):
    def __init__(self):
        root = Path(__file__).resolve().parent.parent
        super().__init__(root / ".data" / "drafts.json")

    def save_draft(self, draft: Draft) -> None:
        self.set(draft.draft_id, draft.to_dict())

    def get_draft(self, draft_id: str) -> Optional[Draft]:
        raw = self.get(draft_id)
        if raw is None:
            return None
        return Draft.model_validate(raw)
