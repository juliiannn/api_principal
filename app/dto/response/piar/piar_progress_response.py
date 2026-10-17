from typing import Optional
from pydantic import BaseModel
from app.model import Period, ProgressLevel


class PiarProgressResponse(BaseModel):
    id: int
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str]
    registrado_por: int
    teacher_name: str
