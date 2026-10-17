from typing import Optional
from pydantic import BaseModel


class CreatePiarGoalRequest(BaseModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    descripcion: str
