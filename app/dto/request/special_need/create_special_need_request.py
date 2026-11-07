from typing import Optional
from app.dto.camel_model import CamelModel


class CreateSpecialNeedRequest(CamelModel):
    nombre: str
    descripcion: Optional[str] = None
