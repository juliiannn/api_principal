from typing import Optional
from pydantic import BaseModel


class ModuleResponse(BaseModel):
    id: int
    nombre: str
    ruta: str
    descripcion: Optional[str]
    estado: bool

    class Config:
        from_attributes = True
