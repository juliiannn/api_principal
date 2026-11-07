from datetime import date, datetime
from typing import Optional
from app.dto.camel_model import CamelModel


class AssignmentResponse(CamelModel):
    id: int
    course_subject_id: int
    course_id: int
    course_name: str
    subject_id: int
    subject_name: str
    teacher_name: str
    title: str
    description: str
    due_date: date
    estado: bool = True
    creado: Optional[datetime] = None
