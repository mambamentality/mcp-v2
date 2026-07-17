# tools/acta_data_schemas.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AgendaPoint(BaseModel):
    numero: str
    titulo: str
    maestroId: Optional[str] = None
    maestroEstado: Optional[str] = None  # asignado_automatico | requiere_confirmacion | punto_nuevo
    tipo: Optional[str] = None  # simple | complejo
    plantillaFrase: Optional[str] = None
    narrativaAnterior: Optional[str] = None
    determinacionAnterior: Optional[str] = None
    narrativa: str = ""
    determinacion: str = ""
    cite: Optional[str] = None
    expositor: str = ""
    expositorIntro: str = ""
    textoRespaldo: str = ""
    subpuntos: List["AgendaPoint"] = Field(default_factory=list)


AgendaPoint.model_rebuild()


class Attendee(BaseModel):
    nombre: str
    rol: str = ""
    modalidad: str = ""  # "presencial" | "virtual"
    asistio: bool = True
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None


class BackupDocument(BaseModel):
    fileName: str
    puntoNumero: str
    cite: Optional[str] = None
    tipoArchivo: str
    textoExtraido: str


class ActaData(BaseModel):
    actaId: str = ""
    numeroActa: str = ""
    numeroActaConfirmado: bool = False
    fecha: str = ""
    horaInicio: str = ""
    horaFin: str = ""
    lugar: str = ""
    modalidadSesion: str = ""
    ordenDelDia: List[AgendaPoint] = Field(default_factory=list)
    asistentes: List[Attendee] = Field(default_factory=list)
    roles: dict = Field(default_factory=dict)
    documentosRespaldo: List[BackupDocument] = Field(default_factory=list)
    presidenta: str = ""
    secretaria: str = ""
    status: str = "pendingModalidad"  # pendingModalidad -> pendingApproval -> approved
    sourceFolder: str = ""
    outputFolder: str = ""
    gestion: str = ""
    directorio: str = ""