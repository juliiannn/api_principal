from typing import Optional
from app.dto.camel_model import CamelModel


class PiarNeedResponse(CamelModel):
    special_need_id: int
    nombre: str
    diagnostico: Optional[str]
