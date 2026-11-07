from typing import Optional
from app.dto.camel_model import CamelModel
from app.model import Period, ProgressLevel


class CreatePiarProgressRequest(CamelModel):
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str] = None
