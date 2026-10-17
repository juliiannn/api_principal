from typing import Optional
from pydantic import BaseModel
from app.model import Period, ProgressLevel


class CreatePiarProgressRequest(BaseModel):
    piar_goal_id: int
    period: Period
    nivel: ProgressLevel
    observaciones: Optional[str] = None
