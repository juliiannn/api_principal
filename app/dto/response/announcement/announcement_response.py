from datetime import datetime
from typing import Optional

from app.dto.camel_model import CamelModel


class AnnouncementResponse(CamelModel):
    id: int
    titulo: str
    contenido: str
    publicado_por_nombre: str
    publicado_por_rol: str
    creado: Optional[datetime] = None
    actualizado: Optional[datetime] = None
    estado: bool = True
