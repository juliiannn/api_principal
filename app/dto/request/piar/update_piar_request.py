from datetime import date
from typing import Optional
from app.dto.camel_model import CamelModel


class UpdatePiarRequest(CamelModel):
    fecha_fin: Optional[date] = None
    observaciones: Optional[str] = None
    consentimiento_acudiente: bool
