from typing import Optional
from app.dto.camel_model import CamelModel


class PiarGoalResponse(CamelModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    descripcion: str
