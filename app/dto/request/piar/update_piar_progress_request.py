from typing import Optional
from pydantic import BaseModel
from app.model import ProgressLevel


class UpdatePiarProgressRequest(BaseModel):
    nivel: ProgressLevel
    observaciones: Optional[str] = None
