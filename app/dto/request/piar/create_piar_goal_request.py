from typing import Optional
from app.dto.camel_model import CamelModel


class CreatePiarGoalRequest(CamelModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    descripcion: str
