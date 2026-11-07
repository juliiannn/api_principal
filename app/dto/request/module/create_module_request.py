from typing import Optional
from app.dto.camel_model import CamelModel


class CreateModuleRequest(CamelModel):
    nombre: str
    ruta: str
    descripcion: Optional[str] = None
