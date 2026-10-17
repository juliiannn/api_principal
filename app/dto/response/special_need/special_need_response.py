from typing import Optional
from pydantic import BaseModel


class SpecialNeedResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: bool

    class Config:
        from_attributes = True
