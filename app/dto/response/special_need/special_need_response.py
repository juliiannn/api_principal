from typing import Optional
from pydantic import ConfigDict
from app.dto.camel_model import CamelModel


class SpecialNeedResponse(CamelModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    estado: bool

    model_config = ConfigDict(from_attributes=True)
