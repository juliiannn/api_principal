from typing import Optional
from pydantic import BaseModel
from app.model import AdjustmentType


class CreatePiarAdjustmentRequest(BaseModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    tipo: AdjustmentType
    descripcion: str
