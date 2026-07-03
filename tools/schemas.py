from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ActaFormData(BaseModel):
    titulo: str = ""
    fecha: str = ""
    hora_inicio: str = ""
    hora_fin: str = ""
    lugar: str = ""
    participantes: List[str] = Field(default_factory=list)
    objetivo: str = ""
    antecedentes: str = ""
    temas_tratados: List[str] = Field(default_factory=list)
    acuerdos: List[str] = Field(default_factory=list)
    compromisos: List[str] = Field(default_factory=list)
    observaciones: str = ""


class ActaSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    data: ActaFormData = Field(default_factory=ActaFormData)
    status: str = "in_progress"

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def to_dict(self) -> Dict[str, Any]:
        # model_dump_json() serializa datetimes de forma consistente (ISO-8601);
        # volvemos a parsear a dict plano para poder guardarlo con json.dump.
        return json.loads(self.model_dump_json())


class Draft(BaseModel):
    draft_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: Optional[str] = None
    status: str = "pendingApproval"
    draft_markdown: str = ""
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    approved_at: Optional[datetime] = None

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def approve(self) -> None:
        self.status = "approved"
        self.approved_at = _utcnow()
        self.touch()

    def to_dict(self) -> Dict[str, Any]:
        return json.loads(self.model_dump_json())
