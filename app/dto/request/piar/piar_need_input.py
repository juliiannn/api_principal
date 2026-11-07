from typing import Optional
from app.dto.camel_model import CamelModel


class PiarNeedInput(CamelModel):
    special_need_id: int
    diagnostico: Optional[str] = None
