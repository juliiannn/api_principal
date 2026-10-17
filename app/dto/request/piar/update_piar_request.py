from datetime import date
from typing import Optional
from pydantic import BaseModel


class UpdatePiarRequest(BaseModel):
    fecha_fin: Optional[date] = None
    observaciones: Optional[str] = None
    consentimiento_acudiente: bool
