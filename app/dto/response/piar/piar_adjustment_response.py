from typing import Optional
from app.dto.camel_model import CamelModel
from app.model import AdjustmentType


class PiarAdjustmentResponse(CamelModel):
    id: int
    piar_id: int
    course_subject_id: Optional[int]
    subject_name: Optional[str]
    tipo: AdjustmentType
    descripcion: str
