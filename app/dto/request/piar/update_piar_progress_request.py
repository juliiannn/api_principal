from typing import Optional
from app.dto.camel_model import CamelModel
from app.model import ProgressLevel


class UpdatePiarProgressRequest(CamelModel):
    nivel: ProgressLevel
    observaciones: Optional[str] = None
