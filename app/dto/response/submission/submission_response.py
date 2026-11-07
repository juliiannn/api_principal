from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.dto.camel_model import CamelModel


class SubmissionResponse(CamelModel):
    id: int
    assignment_id: int
    assignment_title: str
    course_name: str
    subject_name: str
    due_date: date
    student_id: int
    student_name: str
    contenido: str
    fecha_entrega: Optional[datetime] = None
    actualizado: Optional[datetime] = None
    entrega_tardia: bool = False
    calificada: bool = False
    nota: Optional[Decimal] = None
    retroalimentacion: Optional[str] = None
    calificado_por_nombre: Optional[str] = None
    fecha_calificacion: Optional[datetime] = None
    estado: bool = True
