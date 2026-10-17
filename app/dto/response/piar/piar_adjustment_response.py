from typing import Optional
from pydantic import BaseModel
from app.model import AdjustmentType


class PiarAdjustmentResponse(BaseModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    tipo: AdjustmentType
    descripcion: str
