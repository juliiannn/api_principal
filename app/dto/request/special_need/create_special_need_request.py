from typing import Optional
from pydantic import BaseModel


class CreateSpecialNeedRequest(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
