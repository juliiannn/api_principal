from typing import Optional
from pydantic import BaseModel


class PiarNeedResponse(BaseModel):
    special_need_id: int
    nombre: str
    diagnostico: Optional[str]
