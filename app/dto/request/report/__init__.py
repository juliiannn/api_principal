from datetime import date
from typing import List, Literal, Optional

from pydantic import Field

from app.dto.camel_model import CamelModel

ReportFormat = Literal["xlsx", "pdf"]
ReportType = Literal["consolidado", "notas", "asistencia", "estudiantes", "piar"]
PeriodCode = Literal["PERIOD_1", "PERIOD_2", "PERIOD_3", "PERIOD_4"]


class ReportFiltersRequest(CamelModel):
    """Criterios de consulta (todos opcionales)."""
    curso_id: Optional[int] = None
    materia_id: Optional[int] = None
    periodo: Optional[PeriodCode] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None


class ReportRequest(ReportFiltersRequest):
    tipo: ReportType
    formato: ReportFormat


class ReportEmailRequest(ReportFiltersRequest):
    tipo: ReportType
    formatos: List[ReportFormat] = Field(min_length=1, max_length=2)


__all__ = ["ReportEmailRequest", "ReportFiltersRequest", "ReportRequest"]
