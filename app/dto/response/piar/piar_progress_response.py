from typing import Optional
from app.dto.camel_model import CamelModel
from app.model import Period, ProgressLevel


class PiarProgressResponse(CamelModel):
    id: int
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str]
    registrado_por: int
    teacher_name: str
