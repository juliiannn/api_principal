from datetime import datetime
from typing import List, Optional

from app.dto.camel_model import CamelModel


class ReportCatalogItem(CamelModel):
    tipo: str
    titulo: str
    descripcion: str
    filtros: List[str]          # curso, materia, periodo, desde, hasta


class ReportFileResponse(CamelModel):
    id: int
    tipo: str
    titulo: str
    formato: str
    filtros: str
    nombre_archivo: str
    tamano_bytes: int
    filas: int
    creado: Optional[datetime] = None
    expira_en: datetime
    enviado_a: Optional[str] = None


class ReportOption(CamelModel):
    id: int
    nombre: str


class ReportOptionsResponse(CamelModel):
    """Valores que el usuario puede elegir en los filtros (ya limitados a su alcance)."""
    cursos: List[ReportOption]
    materias: List[ReportOption]


class ReportEmailResponse(CamelModel):
    estado: str                 # ENVIADO | FALLIDO | OMITIDO
    destinatario: str
    enviado_a: Optional[str] = None
    error: Optional[str] = None
    archivos: List[ReportFileResponse]


__all__ = ["ReportCatalogItem", "ReportEmailResponse", "ReportFileResponse", "ReportOption", "ReportOptionsResponse"]
