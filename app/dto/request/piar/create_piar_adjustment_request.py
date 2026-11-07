from typing import Optional
from app.dto.camel_model import CamelModel
from app.model import AdjustmentType


class CreatePiarAdjustmentRequest(CamelModel):
    piar_id: int
    course_subject_id: Optional[int] = None
    tipo: AdjustmentType
    descripcion: str
