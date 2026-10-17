from typing import Optional
from pydantic import BaseModel


class PiarGoalResponse(BaseModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    descripcion: str
