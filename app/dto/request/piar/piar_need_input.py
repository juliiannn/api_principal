from typing import Optional
from pydantic import BaseModel


class PiarNeedInput(BaseModel):
    special_need_id: int
    diagnostico: Optional[str] = None
