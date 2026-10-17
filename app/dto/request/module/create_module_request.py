from typing import Optional
from pydantic import BaseModel


class CreateModuleRequest(BaseModel):
    nombre: str
    ruta: str
    descripcion: Optional[str] = None
